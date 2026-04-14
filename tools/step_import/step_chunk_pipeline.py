"""
STEP chunking and import pipeline for FreeCAD / FreeCADCmd.

Modes:
- chunk: import one large STEP file, optionally defeature it, then export chunk STEP files.
- import-chunk: import one chunk STEP file and save it as FCStd.

Examples:
    FreeCADCmd.exe tools\\step_import\\step_chunk_pipeline.py --mode chunk --input big.step --output-dir out
    FreeCADCmd.exe tools\\step_import\\step_chunk_pipeline.py --mode import-chunk --input out\\chunk_000.step --output-file out\\chunk_000.FCStd
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import traceback
from pathlib import Path

import FreeCAD
import Import
import Part


def _console(message: str) -> None:
    FreeCAD.Console.PrintMessage(f"{message}\n")


def _warn(message: str) -> None:
    FreeCAD.Console.PrintWarning(f"{message}\n")


def _error(message: str) -> None:
    FreeCAD.Console.PrintError(f"{message}\n")


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _shape_objects(doc):
    objects = []
    for obj in doc.Objects:
        try:
            if hasattr(obj, "Shape") and obj.Shape and not obj.Shape.isNull():
                objects.append(obj)
        except Exception:
            continue
    return objects


def _bbox_diag(shape) -> float:
    try:
        bb = shape.BoundBox
        dx = bb.XMax - bb.XMin
        dy = bb.YMax - bb.YMin
        dz = bb.ZMax - bb.ZMin
        return math.sqrt(dx * dx + dy * dy + dz * dz)
    except Exception:
        return 0.0


def _count_faces(shape) -> int:
    try:
        return len(shape.Faces)
    except Exception:
        return 0


def _shape_volume(shape) -> float:
    try:
        return abs(float(shape.Volume))
    except Exception:
        return 0.0


def _looks_like_fastener(label: str) -> bool:
    label = (label or "").lower()
    return bool(re.search(
        r'\b(bolt|screw|nut|washer|stud|pin|fastener|shim|rivet)\b',
        label,
    ))


def _configure_export_schema(schema: str) -> None:
    if not schema:
        return
    Part.setStaticValue("write.step.schema", schema)
    _console(f"STEP export schema set to {schema}")


def _import_step(input_path: Path, doc_name: str):
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    doc = FreeCAD.newDocument(doc_name)
    _console(f"Importing STEP: {input_path}")
    Import.insert(str(input_path), doc.Name, False, False, True, 0)
    doc.recompute()
    return doc


def _candidate_small_blend_faces(shape, fillet_threshold_mm: float, max_face_area: float):
    removable = []
    for face in getattr(shape, "Faces", []):
        try:
            if face.Area > max_face_area:
                continue
            surface = face.Surface
            radius = getattr(surface, "Radius", None)
            if radius is None:
                continue
            radius = abs(float(radius))
            if 0.0 < radius <= fillet_threshold_mm:
                removable.append(face)
        except Exception:
            continue
    return removable


def _try_defeature_object(obj, fillet_threshold_mm: float, max_face_area: float) -> bool:
    shape = getattr(obj, "Shape", None)
    if shape is None or shape.isNull():
        return False

    removable_faces = _candidate_small_blend_faces(shape, fillet_threshold_mm, max_face_area)
    if not removable_faces:
        return False

    try:
        new_shape = shape.defeaturing(removable_faces)
    except Exception as exc:
        _warn(f"Defeaturing failed for {obj.Label}: {exc}")
        return False

    if new_shape.isNull():
        return False

    obj.Shape = new_shape
    return True


def _remove_small_bodies(doc, volume_threshold: float, diagonal_threshold: float):
    removed = []
    for obj in list(_shape_objects(doc)):
        shape = obj.Shape
        vol = _shape_volume(shape)
        diag = _bbox_diag(shape)
        faces = _count_faces(shape)
        is_small = vol > 0.0 and vol <= volume_threshold and diag <= diagonal_threshold and faces <= 64
        if _looks_like_fastener(getattr(obj, "Label", "")) and is_small:
            removed.append(obj)
            continue
        if is_small:
            removed.append(obj)

    for obj in removed:
        try:
            doc.removeObject(obj.Name)
        except Exception:
            pass

    if removed:
        _console(f"Removed {len(removed)} small/fastener-like bodies")
    return len(removed)


def _defeature_doc(doc, fillet_threshold_mm: float, max_face_area: float):
    changed = 0
    for obj in _shape_objects(doc):
        if _try_defeature_object(obj, fillet_threshold_mm, max_face_area):
            changed += 1
    if changed:
        _console(f"Defeatured {changed} objects")
    return changed


def _chunk_groups(objects, target_faces: int, target_objects: int):
    ranked = []
    for obj in objects:
        shape = obj.Shape
        ranked.append(
            {
                "obj": obj,
                "faces": max(1, _count_faces(shape)),
                "volume": _shape_volume(shape),
            }
        )

    ranked.sort(key=lambda item: (item["faces"], item["volume"]), reverse=True)

    groups = []
    current = []
    current_faces = 0
    for item in ranked:
        would_exceed_faces = current and current_faces + item["faces"] > target_faces
        would_exceed_count = current and len(current) >= target_objects
        if would_exceed_faces or would_exceed_count:
            groups.append(current)
            current = []
            current_faces = 0
        current.append(item["obj"])
        current_faces += item["faces"]

    if current:
        groups.append(current)
    return groups


def _clone_objects_to_doc(src_objects, out_doc):
    created = []
    for src in src_objects:
        try:
            dst = out_doc.addObject("Part::Feature", src.Name)
            dst.Label = src.Label
            dst.Shape = src.Shape.copy()
            created.append(dst)
        except Exception as exc:
            _warn(f"Failed to clone {src.Label}: {exc}")
    out_doc.recompute()
    return created


def _export_chunk_step(src_objects, output_path: Path, schema: str):
    _configure_export_schema(schema)
    Import.export(list(src_objects), str(output_path))


def _save_chunk_fcstd(src_objects, output_path: Path):
    out_doc = FreeCAD.newDocument(output_path.stem)
    try:
        created = _clone_objects_to_doc(src_objects, out_doc)
        if not created:
            raise RuntimeError("No objects cloned into chunk document")
        out_doc.saveAs(str(output_path))
    finally:
        FreeCAD.closeDocument(out_doc.Name)


def run_chunk_mode(args) -> int:
    input_path = Path(args.input).resolve()
    output_dir = _ensure_dir(Path(args.output_dir).resolve())
    manifest_path = output_dir / "manifest.json"

    doc = _import_step(input_path, "StepChunkSource")
    try:
        if args.remove_small_bodies:
            _remove_small_bodies(
                doc,
                volume_threshold=args.small_body_volume_mm3,
                diagonal_threshold=args.small_body_diag_mm,
            )

        if args.defeature:
            _defeature_doc(
                doc,
                fillet_threshold_mm=args.fillet_threshold_mm,
                max_face_area=args.max_blend_face_area_mm2,
            )

        doc.recompute()
        objects = _shape_objects(doc)
        if not objects:
            raise RuntimeError("No shape objects found after import")

        groups = _chunk_groups(
            objects,
            target_faces=args.target_faces,
            target_objects=args.target_objects,
        )

        manifest = {
            "source": str(input_path),
            "chunk_count": len(groups),
            "chunks": [],
        }

        for index, group in enumerate(groups):
            stem = f"chunk_{index:03d}"
            step_path = output_dir / f"{stem}.step"
            _export_chunk_step(group, step_path, args.ap_schema)

            chunk_info = {
                "name": stem,
                "step": str(step_path),
                "object_count": len(group),
                "face_count": sum(_count_faces(obj.Shape) for obj in group),
                "labels": [obj.Label for obj in group],
            }

            if args.save_fcstd:
                fcstd_path = output_dir / f"{stem}.FCStd"
                _save_chunk_fcstd(group, fcstd_path)
                chunk_info["fcstd"] = str(fcstd_path)

            manifest["chunks"].append(chunk_info)
            _console(
                f"Exported {stem}: {chunk_info['object_count']} objects, "
                f"{chunk_info['face_count']} faces")

        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        _console(f"Wrote manifest: {manifest_path}")
        return 0
    finally:
        FreeCAD.closeDocument(doc.Name)


def run_import_chunk_mode(args) -> int:
    input_path = Path(args.input).resolve()
    output_file = Path(args.output_file).resolve()
    _ensure_dir(output_file.parent)

    doc = _import_step(input_path, output_file.stem)
    try:
        if args.remove_small_bodies:
            _remove_small_bodies(
                doc,
                volume_threshold=args.small_body_volume_mm3,
                diagonal_threshold=args.small_body_diag_mm,
            )
        if args.defeature:
            _defeature_doc(
                doc,
                fillet_threshold_mm=args.fillet_threshold_mm,
                max_face_area=args.max_blend_face_area_mm2,
            )
        doc.recompute()
        doc.saveAs(str(output_file))
        _console(f"Saved chunk document: {output_file}")
        return 0
    finally:
        FreeCAD.closeDocument(doc.Name)


def build_parser():
    parser = argparse.ArgumentParser(description="STEP chunking/import pipeline for FreeCAD")
    parser.add_argument("--mode", choices=("chunk", "import-chunk"), required=True)
    parser.add_argument("--input", required=True, help="Input STEP file")
    parser.add_argument("--defeature", action="store_true", help="Try conservative blend removal")
    parser.add_argument(
        "--remove-small-bodies", action="store_true", help="Remove likely fasteners/tiny bodies"
    )
    parser.add_argument(
        "--fillet-threshold-mm",
        type=float,
        default=2.0,
        help="Blend radius threshold used for defeaturing",
    )
    parser.add_argument(
        "--max-blend-face-area-mm2",
        type=float,
        default=200.0,
        help="Maximum analytic face area eligible for defeaturing",
    )
    parser.add_argument(
        "--small-body-volume-mm3",
        type=float,
        default=250.0,
        help="Delete bodies below this volume when tiny-body removal is enabled",
    )
    parser.add_argument(
        "--small-body-diag-mm",
        type=float,
        default=25.0,
        help="Delete bodies below this bounding-box diagonal when tiny-body removal is enabled",
    )
    parser.add_argument(
        "--ap-schema",
        default="AP203",
        choices=("AP203", "AP214CD", "AP214DIS", "AP214IS", "AP242DIS"),
        help="STEP schema used when exporting chunk STEP files",
    )

    parser.add_argument("--output-dir", help="Output directory for chunk mode")
    parser.add_argument("--target-faces", type=int, default=15000)
    parser.add_argument("--target-objects", type=int, default=64)
    parser.add_argument("--save-fcstd", action="store_true", help="Also save FCStd for each chunk")

    parser.add_argument("--output-file", help="Output FCStd path for import-chunk mode")
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.mode == "chunk":
            if not args.output_dir:
                parser.error("--output-dir is required for --mode chunk")
            return run_chunk_mode(args)
        if args.mode == "import-chunk":
            if not args.output_file:
                parser.error("--output-file is required for --mode import-chunk")
            return run_import_chunk_mode(args)
        parser.error(f"Unsupported mode: {args.mode}")
    except SystemExit:
        raise
    except Exception as exc:
        _error(str(exc))
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
