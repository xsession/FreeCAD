"""
Parallel wrapper around FreeCADCmd for chunk STEP imports.

This script runs outside FreeCAD using normal Python.
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import subprocess
import sys
from pathlib import Path


def _discover_inputs(input_dir: Path):
    manifest = input_dir / "manifest.json"
    if manifest.exists():
        data = json.loads(manifest.read_text(encoding="utf-8"))
        return [Path(item["step"]) for item in data.get("chunks", [])]
    return sorted(input_dir.glob("chunk_*.step"))


def _run_one(job):
    freecadcmd, pipeline_script, step_path, output_dir, flags, timeout = job
    output_file = output_dir / f"{step_path.stem}.FCStd"
    cmd = [
        str(freecadcmd),
        str(pipeline_script),
        "--mode",
        "import-chunk",
        "--input",
        str(step_path),
        "--output-file",
        str(output_file),
    ]
    cmd.extend(flags)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout or None)
        return {
            "input": str(step_path),
            "output": str(output_file),
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    except subprocess.TimeoutExpired:
        return {
            "input": str(step_path),
            "output": str(output_file),
            "returncode": -1,
            "stdout": "",
            "stderr": f"Timed out after {timeout}s",
        }


def build_parser():
    parser = argparse.ArgumentParser(description="Parallel STEP chunk importer")
    parser.add_argument("--freecadcmd", required=True, help="Path to FreeCADCmd.exe")
    parser.add_argument("--pipeline-script", required=True, help="Path to step_chunk_pipeline.py")
    parser.add_argument("--input-dir", required=True, help="Directory containing chunk STEP files")
    parser.add_argument("--output-dir", required=True, help="Directory for FCStd outputs")
    parser.add_argument("--workers", type=int, default=max(1, mp.cpu_count() // 2))
    parser.add_argument("--defeature", action="store_true")
    parser.add_argument("--remove-small-bodies", action="store_true")
    parser.add_argument("--fillet-threshold-mm", type=float, default=2.0)
    parser.add_argument("--max-blend-face-area-mm2", type=float, default=200.0)
    parser.add_argument("--small-body-volume-mm3", type=float, default=250.0)
    parser.add_argument("--small-body-diag-mm", type=float, default=25.0)
    parser.add_argument("--timeout", type=int, default=3600,
                        help="Timeout in seconds per worker process (0=no timeout)")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    freecadcmd = Path(args.freecadcmd).resolve()
    if not freecadcmd.exists():
        print(f"FreeCADCmd not found: {freecadcmd}", file=sys.stderr)
        return 1
    pipeline_script = Path(args.pipeline_script).resolve()
    input_dir = Path(args.input_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    flags = [
        "--fillet-threshold-mm",
        str(args.fillet_threshold_mm),
        "--max-blend-face-area-mm2",
        str(args.max_blend_face_area_mm2),
        "--small-body-volume-mm3",
        str(args.small_body_volume_mm3),
        "--small-body-diag-mm",
        str(args.small_body_diag_mm),
    ]
    if args.defeature:
        flags.append("--defeature")
    if args.remove_small_bodies:
        flags.append("--remove-small-bodies")

    step_files = _discover_inputs(input_dir)
    if not step_files:
        print(f"No chunk STEP files found in {input_dir}", file=sys.stderr)
        return 1

    jobs = [
        (freecadcmd, pipeline_script, step_file, output_dir, list(flags), args.timeout)
        for step_file in step_files
    ]

    failures = 0
    with mp.Pool(processes=args.workers) as pool:
        for result in pool.imap_unordered(_run_one, jobs):
            status = "OK" if result["returncode"] == 0 else "FAIL"
            print(f"[{status}] {result['input']} -> {result['output']}")
            if result["stdout"].strip():
                print(result["stdout"].strip())
            if result["stderr"].strip():
                print(result["stderr"].strip(), file=sys.stderr)
            if result["returncode"] != 0:
                failures += 1

    print(f"Completed {len(jobs)} jobs with {failures} failures")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
