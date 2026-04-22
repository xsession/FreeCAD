# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Focused tests for enterprise Geant4 adapter result collection."""

from __future__ import annotations

import json
import sys
import types
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from flow_studio.enterprise.adapters.geant4 import Geant4SolverAdapter
from flow_studio.enterprise.core.domain import JobHandle, JobState, PreparedStudyContext
from flow_studio.enterprise.testing.harness import make_demo_request


def test_geant4_adapter_collects_structured_result_metadata(tmp_path: Path):
    adapter = Geant4SolverAdapter()
    request = make_demo_request("run-geant4-enterprise", solver_family="geant4")
    request = replace(
        request,
        study=replace(
            request.study,
            adapter_extensions={
                "geant4.primary": {
                    "macro_name": "run.mac",
                    "threads": 2,
                    "event_count": 100,
                    "detectors": [
                        {
                            "name": "DosePlaneDetector",
                            "label": "Dose Plane",
                            "detector_type": "Dose Plane",
                            "collection_name": "dosePlaneHits",
                            "threshold_kev": 5.0,
                            "reference_targets": ["Document/Target/Face1"],
                        }
                    ],
                    "scoring": [
                        {
                            "name": "DoseMesh",
                            "label": "Dose Mesh",
                            "score_quantity": "DoseDeposit",
                            "scoring_type": "Mesh",
                            "bins": [8, 6, 4],
                            "reference_targets": ["Document/Target/Solid1"],
                        },
                    ],
                }
            },
        ),
    )
    context = PreparedStudyContext(
        request=request,
        working_directory=str(tmp_path),
        manifest_hash="sha256:geant4-enterprise",
    )
    freecad_stub = types.SimpleNamespace(
        Console=types.SimpleNamespace(),
        ActiveDocument=types.SimpleNamespace(Name="EnterpriseDoc"),
    )

    with patch.dict(sys.modules, {"FreeCAD": freecad_stub}):
        prepared = adapter.prepare_case(context)

    case_dir = Path(prepared.case_directory)
    (case_dir / "dose.csv").write_text("DoseDeposit,TrackLength\n1.2,3.4\n", encoding="utf-8")
    (case_dir / "summary.json").write_text(
        json.dumps(
            {
                "summary": {"dose": 1.2, "event_count": 100},
                "detectors": [{"cellHits": 7}],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    with patch.dict(sys.modules, {"FreeCAD": freecad_stub}):
        result = adapter.collect_results(
            JobHandle(
                run_id=request.run_id,
                adapter_id=adapter.adapter_id,
                state=JobState.COMPLETED,
                native_identifier="geant4-skeleton",
            )
        )

    assert result.run_id == request.run_id
    assert "dose" in result.fields
    assert "track_length" in result.fields
    assert "hits" in result.fields
    assert "events" in result.monitors
    assert "hits" in result.monitors
    assert "result_summary" in result.artifact_manifest
    summary_path = Path(result.artifact_manifest["result_summary"])
    assert summary_path.is_file()
    summary_payload = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary_payload["result_file"].endswith("summary.json")
    assert summary_payload["result_format"] == "Geant4-JSON"
    assert summary_payload["primary_quantity"] == "DoseDeposit"
    assert summary_payload["available_fields"] == summary_payload["fields"]
    assert any(item["format"] == "Geant4-JSON" for item in summary_payload["artifact_summaries"])
    assert any(item["format"] == "Geant4-CSV" for item in summary_payload["artifact_summaries"])
    assert summary_payload["scoring_summaries"][0]["score_quantity"] == "DoseDeposit"
    assert summary_payload["scoring_summaries"][0]["artifact_files"]
    assert summary_payload["detector_summaries"][0]["collection_name"] == "dosePlaneHits"
    assert "events" in summary_payload["detector_summaries"][0]["monitor_names"]
