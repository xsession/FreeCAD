# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Geant4 solver adapter.

This backend currently follows the same manifest-first pattern as the optical
integration: FlowStudio exports a portable run scaffold and a Geant4 macro,
then launches a user-supplied Geant4 application executable when configured.
"""

from __future__ import annotations

import json
import os
import subprocess

import FreeCAD

from flow_studio.solvers.base_solver import BaseSolverRunner
from flow_studio.solvers.geant4_support import (
    build_macro_lines,
    classify_result,
    reference_targets,
    result_component_summaries,
    summarize_result_artifacts,
)


class Geant4Runner(BaseSolverRunner):
    """Generate and launch Geant4 case scaffolding."""

    name = "Geant4"

    def _analysis_children(self):
        try:
            return list(self.analysis.Group)
        except Exception:
            return []

    def _geometry_ref(self):
        for child in self._analysis_children():
            part = getattr(child, "Part", None)
            if part is None:
                continue
            ref = getattr(part, "Name", None) or getattr(part, "Label", None)
            if ref:
                return f"Document/{ref}"
        return "Document/UnassignedGeometry"

    def _result_candidates(self):
        candidates = []
        for root, _dirs, files in os.walk(self.case_dir):
            for filename in files:
                lower_name = filename.lower()
                if lower_name.endswith((".json", ".csv", ".txt", ".dat")):
                    candidates.append(os.path.join(root, filename))
        candidates.sort()
        return candidates

    def _collect_available_fields(self, result_paths):
        scoring_fields = [
            str(scoring.get("score_quantity", "")).strip()
            for scoring in self._case_manifest().get("scoring", ())
            if str(scoring.get("score_quantity", "")).strip()
        ]
        return summarize_result_artifacts(result_paths, scoring_fields)

    def _find_or_create_geant4_result(self, payload):
        doc = getattr(FreeCAD, "ActiveDocument", None)
        if doc is None:
            return None

        result_obj = None
        for obj in getattr(self.analysis, "Group", ()):
            if getattr(obj, "FlowType", "") == "FlowStudio::Geant4Result":
                result_obj = obj
                break

        if result_obj is None:
            try:
                from flow_studio.ObjectsFlowStudio import makeGeant4Result

                result_obj = makeGeant4Result(doc, name=f"{self.analysis.Name}_Geant4Result")
                add_object = getattr(self.analysis, "addObject", None)
                if callable(add_object):
                    add_object(result_obj)
            except Exception:
                return None

        from flow_studio.feminout.importFlowStudio import populate_geant4_result_object

        return populate_geant4_result_object(result_obj, payload, doc=doc, analysis=self.analysis)

    def _find_or_create_post_pipeline(self, result_path, result_format, available_fields):
        doc = getattr(FreeCAD, "ActiveDocument", None)
        if doc is None:
            return None

        pipeline = None
        for obj in getattr(self.analysis, "Group", ()):
            if getattr(obj, "FlowType", "") == "FlowStudio::PostPipeline":
                pipeline = obj
                break

        if pipeline is None:
            try:
                from flow_studio.ObjectsFlowStudio import makePostPipeline

                pipeline = makePostPipeline(doc, name=f"{self.analysis.Name}_Results")
                add_object = getattr(self.analysis, "addObject", None)
                if callable(add_object):
                    add_object(pipeline)
            except Exception:
                return None

        pipeline.Analysis = self.analysis
        pipeline.ResultFile = result_path
        pipeline.ResultFormat = result_format
        pipeline.AvailableFields = list(available_fields)
        if available_fields:
            pipeline.ActiveField = available_fields[0]

        recompute = getattr(doc, "recompute", None)
        if callable(recompute):
            recompute()
        return pipeline

    def _case_manifest(self):
        project_name = getattr(getattr(FreeCAD, "ActiveDocument", None), "Name", None)
        if not isinstance(project_name, str) or not project_name.strip():
            project_name = "FlowStudio"

        sources = []
        detectors = []
        scoring = []
        children = []
        for obj in self._analysis_children():
            flow_type = getattr(obj, "FlowType", "")
            item = {
                "flow_type": flow_type,
                "name": getattr(obj, "Name", ""),
                "label": getattr(obj, "Label", ""),
            }
            if flow_type == "FlowStudio::BCGeant4Source":
                item.update({
                    "source_type": getattr(obj, "SourceType", "Beam"),
                    "particle_type": getattr(obj, "ParticleType", "gamma"),
                    "energy_mev": float(getattr(obj, "EnergyMeV", 1.0)),
                    "beam_radius_mm": float(getattr(obj, "BeamRadius", 1.0)),
                    "direction": [
                        float(getattr(obj, "DirectionX", 0.0)),
                        float(getattr(obj, "DirectionY", 0.0)),
                        float(getattr(obj, "DirectionZ", 1.0)),
                    ],
                    "events": int(getattr(obj, "Events", 1000)),
                    "reference_targets": reference_targets(obj),
                })
                sources.append(item)
            elif flow_type == "FlowStudio::BCGeant4Detector":
                item.update({
                    "detector_type": getattr(obj, "DetectorType", "Sensitive Detector"),
                    "collection_name": getattr(obj, "CollectionName", "detectorHits"),
                    "threshold_kev": float(getattr(obj, "ThresholdKeV", 0.0)),
                    "reference_targets": reference_targets(obj),
                })
                detectors.append(item)
            elif flow_type == "FlowStudio::BCGeant4Scoring":
                item.update({
                    "score_quantity": getattr(obj, "ScoreQuantity", "DoseDeposit"),
                    "scoring_type": getattr(obj, "ScoringType", "Mesh"),
                    "bins": [
                        int(getattr(obj, "BinsX", 16)),
                        int(getattr(obj, "BinsY", 16)),
                        int(getattr(obj, "BinsZ", 16)),
                    ],
                    "normalize_per_event": bool(getattr(obj, "NormalizePerEvent", True)),
                    "reference_targets": reference_targets(obj),
                })
                scoring.append(item)
            children.append(item)

        return {
            "project": project_name,
            "analysis": getattr(self.analysis, "Name", "Geant4Analysis"),
            "domain": getattr(self.analysis, "PhysicsDomain", "Generic"),
            "backend": "Geant4",
            "geometry_ref": self._geometry_ref(),
            "physics_list": getattr(self.solver_obj, "Geant4PhysicsList", "FTFP_BERT"),
            "event_count": int(getattr(self.solver_obj, "Geant4EventCount", 1000)),
            "threads": int(getattr(self.solver_obj, "Geant4Threads", 1)),
            "macro": getattr(self.solver_obj, "Geant4MacroName", "run.mac"),
            "visualization": bool(
                getattr(self.solver_obj, "Geant4EnableVisualization", False)
            ),
            "sources": sources,
            "detectors": detectors,
            "scoring": scoring,
            "children": children,
        }

    def check(self):
        executable = getattr(self.solver_obj, "Geant4Executable", "")
        if executable and not os.path.isfile(executable):
            return [f"Configured Geant4 executable does not exist: {executable}"]
        return []

    def write_case(self):
        os.makedirs(self.case_dir, exist_ok=True)
        manifest = self._case_manifest()
        manifest_path = os.path.join(self.case_dir, "geant4_case.json")
        with open(manifest_path, "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=2, sort_keys=True)

        macro_name = manifest["macro"] or "run.mac"
        macro_path = os.path.join(self.case_dir, macro_name)
        macro_lines = build_macro_lines(manifest)

        with open(macro_path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(macro_lines) + "\n")

        readme_path = os.path.join(self.case_dir, "README.geant4.txt")
        with open(readme_path, "w", encoding="utf-8") as handle:
            handle.write(
                "FlowStudio Geant4 integration generated this scaffold.\n"
                "Provide a compiled Geant4 application executable in the solver object\n"
                "and ensure the Geant4 runtime environment is loaded before launching.\n"
                "Sensitive detectors remain application-defined; the generated macro carries source and scoring requests, while detector collection names are emitted as comments for app-side wiring.\n"
                "Artifacts:\n"
                "  - geant4_case.json: solver-neutral study manifest\n"
                f"  - {macro_name}: generated Geant4 macro\n"
            )

        FreeCAD.Console.PrintMessage(
            f"FlowStudio [Geant4]: wrote scaffold to {self.case_dir}\n"
        )
        return manifest_path

    def run(self):
        self.write_case()
        executable = getattr(self.solver_obj, "Geant4Executable", "")
        macro_name = getattr(self.solver_obj, "Geant4MacroName", "run.mac") or "run.mac"
        if not executable:
            FreeCAD.Console.PrintMessage(
                "FlowStudio [Geant4]: scaffold generated. Set Geant4Executable to launch a compiled Geant4 application.\n"
            )
            return 0

        cmd = [executable, macro_name]
        FreeCAD.Console.PrintMessage(
            f"FlowStudio [Geant4]: Command: {' '.join(cmd)}\n"
        )

        self.process = subprocess.Popen(
            cmd,
            cwd=self.case_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        for line in self.process.stdout:
            decoded = line.decode("utf-8", errors="replace").rstrip()
            FreeCAD.Console.PrintMessage(f"  [Geant4] {decoded}\n")
        self.process.wait()

        if self.process.returncode == 0:
            FreeCAD.Console.PrintMessage(
                "FlowStudio [Geant4]: application finished successfully.\n"
            )
        else:
            FreeCAD.Console.PrintError(
                f"FlowStudio [Geant4]: application exited with code {self.process.returncode}.\n"
            )
        return self.process.returncode

    def read_results(self):
        result_paths = [
            path for path in self._result_candidates()
            if os.path.basename(path) not in {"geant4_case.json", getattr(self.solver_obj, "Geant4MacroName", "run.mac") or "run.mac", "README.geant4.txt"}
        ]
        if not result_paths:
            FreeCAD.Console.PrintWarning(
                "FlowStudio [Geant4]: no importable result artifacts found. Expected JSON, CSV, TXT, or DAT outputs in the case directory.\n"
            )
            return None

        preferred_path = next(
            (path for path in result_paths if path.lower().endswith(".json")),
            next((path for path in result_paths if path.lower().endswith(".csv")), result_paths[0]),
        )
        result_format = classify_result(preferred_path)
        available_fields, artifact_summaries, monitors = self._collect_available_fields(result_paths)
        manifest = self._case_manifest()
        scoring_summaries, detector_summaries = result_component_summaries(
            manifest,
            artifact_summaries,
            monitors,
        )
        summary_path = os.path.join(self.case_dir, "flowstudio_geant4_result_summary.json")
        primary_quantity = next(
            (
                str(scoring.get("score_quantity", "")).strip()
                for scoring in manifest.get("scoring", ())
                if str(scoring.get("score_quantity", "")).strip()
            ),
            available_fields[0] if available_fields else "",
        )
        summary_payload = {
            "analysis": getattr(self.analysis, "Name", "Geant4Analysis"),
            "result_file": preferred_path,
            "result_format": result_format,
            "available_fields": list(available_fields),
            "monitors": list(monitors),
            "artifact_summaries": artifact_summaries,
            "scoring_summaries": scoring_summaries,
            "detector_summaries": detector_summaries,
            "primary_quantity": primary_quantity,
            "summary_file": summary_path,
        }
        with open(summary_path, "w", encoding="utf-8") as handle:
            json.dump(summary_payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        pipeline = self._find_or_create_post_pipeline(preferred_path, result_format, available_fields)
        geant4_result = self._find_or_create_geant4_result(summary_payload)
        summary = {
            "result_file": preferred_path,
            "result_format": result_format,
            "available_fields": list(available_fields),
            "artifacts": result_paths,
            "artifact_summaries": artifact_summaries,
            "monitors": list(monitors),
            "scoring_summaries": scoring_summaries,
            "detector_summaries": detector_summaries,
            "summary_file": summary_path,
            "post_pipeline": getattr(pipeline, "Name", None),
            "geant4_result": getattr(geant4_result, "Name", None),
        }
        FreeCAD.Console.PrintMessage(
            f"FlowStudio [Geant4]: imported result artifact {preferred_path}\n"
        )
        return summary