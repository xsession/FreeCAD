# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Pure-Python helpers shared by Geant4 legacy and enterprise paths."""

from __future__ import annotations

import csv
import json
import os


def macro_comment(text):
    return f"# {text}"


def reference_targets(obj):
    refs = getattr(obj, "References", ()) or ()
    targets = []
    for ref_obj, sub_elements in refs:
        ref_name = getattr(ref_obj, "Name", None) or getattr(ref_obj, "Label", None) or "LinkedObject"
        base = f"Document/{ref_name}"
        if isinstance(sub_elements, str):
            sub_names = (sub_elements,)
        else:
            sub_names = tuple(sub_elements or ())
        if sub_names:
            targets.extend(f"{base}/{name}" for name in sub_names)
        else:
            targets.append(base)
    return tuple(dict.fromkeys(targets))


def source_macro_lines(source, index):
    source_type = source.get("source_type", "Beam")
    particle = source.get("particle_type", "gamma")
    energy = source.get("energy_mev", 1.0)
    radius = source.get("beam_radius_mm", 1.0)
    direction = source.get("direction", (0.0, 0.0, 1.0))
    refs = source.get("reference_targets", ())
    event_count = int(source.get("events", 1000))

    lines = [
        macro_comment(f"FlowStudio source {index}: {source.get('label', source.get('name', 'Source'))}"),
        macro_comment(f"Selected geometry: {', '.join(refs) if refs else 'unassigned'}"),
        f"/gps/particle {particle}",
        "/gps/ene/type Mono",
        f"/gps/ene/mono {energy} MeV",
        f"/gps/direction {direction[0]} {direction[1]} {direction[2]}",
    ]

    if source_type == "Point Source":
        lines.extend([
            "/gps/pos/type Point",
            "/gps/pos/centre 0 0 0 mm",
        ])
    elif source_type == "Volume Source":
        lines.extend([
            "/gps/pos/type Volume",
            "/gps/pos/shape Sphere",
            f"/gps/pos/radius {radius} mm",
            "/gps/pos/centre 0 0 0 mm",
        ])
    else:
        lines.extend([
            "/gps/pos/type Plane",
            "/gps/pos/shape Circle",
            f"/gps/pos/radius {radius} mm",
            "/gps/pos/centre 0 0 0 mm",
        ])

    if source_type == "Beam":
        lines.append("/gps/ang/type beam2d")
    elif source_type == "Surface Source":
        lines.append(macro_comment("Surface source approximated as a planar circular source in the generated macro."))

    lines.append(f"/run/beamOn {event_count}")
    return lines


def scoring_macro_lines(scoring_entries):
    lines = []
    quantity_map = {
        "DoseDeposit": "doseDeposit",
        "EnergyDeposit": "eDep",
        "TrackLength": "trackLength",
        "Flux": "flatSurfaceFlux",
        "CellHits": "nOfStep",
    }

    for index, scoring in enumerate(scoring_entries, start=1):
        bins = scoring.get("bins", [16, 16, 16])
        quantity = quantity_map.get(scoring.get("score_quantity", "DoseDeposit"), "doseDeposit")
        refs = scoring.get("reference_targets", ())
        lines.extend([
            macro_comment(f"FlowStudio scoring {index}: {scoring.get('score_quantity', 'DoseDeposit')} on {', '.join(refs) if refs else 'unassigned geometry'}"),
            f"/score/create/boxMesh flowstudioScore{index}",
            f"/score/mesh/nBin {bins[0]} {bins[1]} {bins[2]}",
            f"/score/quantity/{quantity} score{index}",
            "/score/close",
        ])
        if scoring.get("normalize_per_event", True):
            lines.append(macro_comment("Requested normalization per event will be applied during FlowStudio-side post-processing."))
    return lines


def detector_macro_lines(detector_entries):
    lines = []
    for index, detector in enumerate(detector_entries, start=1):
        refs = detector.get("reference_targets", ())
        lines.extend([
            macro_comment(
                f"FlowStudio detector {index}: {detector.get('detector_type', 'Sensitive Detector')} "
                f"collection={detector.get('collection_name', 'detectorHits')} targets={', '.join(refs) if refs else 'unassigned'}"
            ),
            macro_comment("Detector sensitivity is application-defined; wire this collection name inside the compiled Geant4 app."),
        ])
    return lines


def build_macro_lines(manifest):
    lines = [
        "/control/verbose 1",
        "/run/verbose 1",
        "/event/verbose 0",
        macro_comment(f"FlowStudio generated Geant4 macro for analysis {manifest.get('analysis', 'Geant4Analysis')}."),
        macro_comment(f"Physics list: {manifest.get('physics_list', 'FTFP_BERT')}"),
        f"/run/numberOfThreads {manifest['threads']}",
    ]
    if manifest["visualization"]:
        lines = [
            "/vis/open OGL 1024x768-0+0",
            "/vis/viewer/set/autoRefresh true",
            "/vis/drawVolume",
            "/vis/scene/add/trajectories smooth",
        ] + lines

    lines.extend(detector_macro_lines(manifest.get("detectors", ())))
    lines.extend(scoring_macro_lines(manifest.get("scoring", ())))

    if manifest.get("sources"):
        for index, source in enumerate(manifest["sources"], start=1):
            lines.extend(source_macro_lines(source, index))
    else:
        lines.extend([
            macro_comment("No FlowStudio Geant4 sources were defined; using solver-level beamOn count only."),
            f"/run/beamOn {manifest['event_count']}",
        ])
    return lines


def classify_result(path):
    lower_path = path.lower()
    if lower_path.endswith(".json"):
        return "Geant4-JSON"
    if lower_path.endswith(".csv"):
        return "Geant4-CSV"
    return "Geant4-TXT"


def normalize_field_name(name):
    text = str(name or "").strip()
    if not text:
        return ""
    compact = text.replace("-", "_").replace(" ", "_").strip("_")
    lowered = compact.lower()
    aliases = {
        "dosedeposit": "dose",
        "dose_deposit": "dose",
        "dose": "dose",
        "edep": "energy_deposition",
        "energydeposit": "energy_deposition",
        "energy_deposit": "energy_deposition",
        "energy_deposition": "energy_deposition",
        "tracklength": "track_length",
        "track_length": "track_length",
        "flux": "flux",
        "cellhits": "hits",
        "cell_hits": "hits",
        "hits": "hits",
        "events": "events",
        "event_count": "events",
        "steps": "steps",
        "step_count": "steps",
    }
    return aliases.get(lowered, compact)


def json_fields(payload):
    fields = []

    def visit(value, key_hint=None):
        if key_hint:
            normalized = normalize_field_name(key_hint)
            if normalized:
                fields.append(normalized)
        if isinstance(value, dict):
            for nested_key, nested_value in value.items():
                visit(nested_value, nested_key)
        elif isinstance(value, list):
            for item in value[:5]:
                if isinstance(item, dict):
                    for nested_key, nested_value in item.items():
                        visit(nested_value, nested_key)

    visit(payload)
    return tuple(dict.fromkeys(field for field in fields if field))


def csv_fields(path):
    try:
        with open(path, "r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader, [])
    except Exception:
        return ()
    fields = [normalize_field_name(column) for column in header]
    return tuple(dict.fromkeys(field for field in fields if field))


def filename_fields(path):
    stem = os.path.splitext(os.path.basename(path))[0]
    tokens = []
    for part in stem.replace("-", "_").split("_"):
        normalized = normalize_field_name(part)
        if normalized and normalized not in {"summary", "results", "result", "geant4", "score", "scoring", "output", "data"}:
            tokens.append(normalized)
    return tuple(dict.fromkeys(tokens))


def artifact_summary(path):
    result_format = classify_result(path)
    fields = list(filename_fields(path))
    if result_format == "Geant4-JSON":
        try:
            with open(path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except Exception:
            payload = None
        if payload is not None:
            fields.extend(json_fields(payload))
    elif result_format == "Geant4-CSV":
        fields.extend(csv_fields(path))

    return {
        "path": path,
        "format": result_format,
        "fields": list(dict.fromkeys(field for field in fields if field)),
    }


def summarize_result_artifacts(result_paths, scoring_fields=()):
    fields = []
    for quantity in scoring_fields:
        quantity_text = str(quantity).strip()
        if quantity_text:
            fields.append(quantity_text)
            normalized = normalize_field_name(quantity_text)
            if normalized and normalized != quantity_text:
                fields.append(normalized)
    artifact_summaries = [artifact_summary(path) for path in result_paths]
    for artifact in artifact_summaries:
        fields.extend(artifact["fields"])
    deduped_fields = tuple(dict.fromkeys(field for field in fields if field))
    monitors = tuple(
        field for field in ("events", "steps", "hits")
        if field in deduped_fields
    )
    return deduped_fields, artifact_summaries, monitors


def result_component_summaries(manifest, artifact_summaries, monitors):
    scoring_summaries = []
    detector_summaries = []

    for index, scoring in enumerate(manifest.get("scoring", ()), start=1):
        quantity = str(scoring.get("score_quantity", "DoseDeposit")).strip() or "DoseDeposit"
        normalized_quantity = normalize_field_name(quantity)
        matching_artifacts = []
        matching_fields = []
        for artifact in artifact_summaries:
            artifact_fields = list(artifact.get("fields", ()) or ())
            if quantity in artifact_fields or normalized_quantity in artifact_fields:
                matching_artifacts.append(artifact.get("path", ""))
                matching_fields.extend(artifact_fields)
        scoring_summaries.append({
            "name": scoring.get("name", f"Geant4Scoring{index}"),
            "label": scoring.get("label", scoring.get("name", f"Scoring {index}")),
            "score_quantity": quantity,
            "scoring_type": scoring.get("scoring_type", "Mesh"),
            "bins": list(scoring.get("bins", [16, 16, 16])),
            "reference_targets": list(scoring.get("reference_targets", ())),
            "artifact_files": [path for path in matching_artifacts if path],
            "available_fields": list(dict.fromkeys(field for field in matching_fields if field)),
        })

    for index, detector in enumerate(manifest.get("detectors", ()), start=1):
        detector_summaries.append({
            "name": detector.get("name", f"Geant4Detector{index}"),
            "label": detector.get("label", detector.get("name", f"Detector {index}")),
            "collection_name": detector.get("collection_name", f"detectorHits{index}"),
            "detector_type": detector.get("detector_type", "Hits Collection"),
            "threshold_kev": float(detector.get("threshold_kev", 0.0) or 0.0),
            "reference_targets": list(detector.get("reference_targets", ())),
            "monitor_names": list(monitors),
            "artifact_files": [artifact.get("path", "") for artifact in artifact_summaries if artifact.get("path")],
        })

    return scoring_summaries, detector_summaries
