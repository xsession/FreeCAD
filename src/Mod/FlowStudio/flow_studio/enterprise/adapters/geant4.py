# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Geant4 enterprise adapter scaffold."""

from __future__ import annotations

import json
import os

from flow_studio.enterprise.adapters.base import BaseSolverAdapter
from flow_studio.enterprise.core.domain import (
    AdapterMetadata,
    CapabilitySet,
    JobHandle,
    JobState,
    PreparedCase,
    PreparedStudyContext,
    ResultSet,
)


class Geant4SolverAdapter(BaseSolverAdapter):
    """Manifest-first Geant4 adapter for particle transport studies."""

    adapter_id = "geant4.primary"
    display_name = "Geant4"
    family = "geant4"

    def __init__(self) -> None:
        self._prepared_case_directories: dict[str, str] = {}
        self._prepared_artifact_manifests: dict[str, dict[str, str]] = {}

    @staticmethod
    def _extension_options(context: PreparedStudyContext) -> dict[str, str | float | bool]:
        options = context.request.study.adapter_extensions.get("geant4.primary", {})
        return dict(options)

    def metadata(self) -> AdapterMetadata:
        return AdapterMetadata(
            adapter_id=self.adapter_id,
            display_name=self.display_name,
            version="0.1.0",
            family=self.family,
            commercial_core_safe=True,
            supported_solver_versions=("11.4", "11.4.1"),
            notes=(
                "Generates Geant4 run scaffolding and can dispatch a compiled "
                "application executable when provided by the user."
            ),
        )

    def capabilities(self) -> CapabilitySet:
        return CapabilitySet(
            supports_remote=True,
            supports_parallel=True,
            supports_gpu=False,
            supports_transient=False,
            supported_physics=("particle_transport", "radiation", "dosimetry"),
            feature_flags={
                "macro_generation": True,
                "user_application_required": True,
                "manifest_first": True,
            },
        )

    @staticmethod
    def _macro_lines(options: dict[str, str | float | bool]) -> list[str]:
        from flow_studio.solvers.geant4_support import build_macro_lines

        manifest = {
            "analysis": options.get("run_id", "Geant4Analysis"),
            "physics_list": options.get("physics_list", "FTFP_BERT"),
            "threads": int(options.get("threads", 1)),
            "event_count": int(options.get("event_count", 1000)),
            "visualization": bool(options.get("visualization", False)),
            "sources": options.get("sources", []),
            "detectors": options.get("detectors", []),
            "scoring": options.get("scoring", []),
        }
        return build_macro_lines(manifest)

    @staticmethod
    def _write_result_summary(case_directory: str, payload: dict[str, object]):
        summary_path = os.path.join(case_directory, "flowstudio_geant4_result_summary.json")
        with open(summary_path, "w", encoding="utf-8") as handle_out:
            json.dump(payload, handle_out, indent=2, sort_keys=True)
            handle_out.write("\n")
        return summary_path

    def prepare_case(self, context: PreparedStudyContext) -> PreparedCase:
        case_directory = os.path.join(context.working_directory, "geant4_case")
        os.makedirs(case_directory, exist_ok=True)
        options = self._extension_options(context)
        macro_name = str(options.get("macro_name", "run.mac"))
        artifact_manifest = {
            "geant4_case.json": os.path.join(case_directory, "geant4_case.json"),
            macro_name: os.path.join(case_directory, macro_name),
        }
        with open(artifact_manifest["geant4_case.json"], "w", encoding="utf-8") as handle:
            json.dump(options, handle, indent=2, sort_keys=True)
            handle.write("\n")
        with open(artifact_manifest[macro_name], "w", encoding="utf-8") as handle:
            handle.write("\n".join(self._macro_lines(options)) + "\n")

        self._prepared_case_directories[context.request.run_id] = case_directory
        self._prepared_artifact_manifests[context.request.run_id] = dict(artifact_manifest)

        executable = str(options.get("application_executable", "geant4-app"))
        return PreparedCase(
            adapter_id=self.adapter_id,
            run_id=context.request.run_id,
            case_directory=case_directory,
            launch_command=(executable, macro_name),
            artifact_manifest=artifact_manifest,
            max_runtime_seconds=context.request.runtime_thresholds.max_wall_time_seconds,
        )

    def collect_results(self, handle: JobHandle) -> ResultSet:
        artifact_manifest = dict(self._prepared_artifact_manifests.get(handle.run_id, {}))
        fields = ("dose", "energy_deposition", "track_length")
        monitors = ("events", "steps", "hits")
        case_directory = self._prepared_case_directories.get(handle.run_id)
        artifact_summaries = []

        if case_directory and os.path.isdir(case_directory):
            from flow_studio.solvers.geant4_support import result_component_summaries, summarize_result_artifacts

            scoring_fields = ()
            case_payload = {}
            case_manifest_path = os.path.join(case_directory, "geant4_case.json")
            if os.path.isfile(case_manifest_path):
                try:
                    with open(case_manifest_path, "r", encoding="utf-8") as handle_in:
                        case_payload = json.load(handle_in)
                except Exception:
                    case_payload = {}
                if isinstance(case_payload, dict):
                    scoring = case_payload.get("scoring", [])
                    if isinstance(scoring, list):
                        scoring_fields = tuple(
                            str(item.get("score_quantity", "")).strip()
                            for item in scoring
                            if isinstance(item, dict) and str(item.get("score_quantity", "")).strip()
                        )

            result_paths = []
            excluded_names = {
                "geant4_case.json",
                "README.geant4.txt",
                "flowstudio_geant4_result_summary.json",
            }
            macro_name = os.path.basename(next(
                (path for key, path in artifact_manifest.items() if key != "geant4_case.json"),
                "run.mac",
            ))
            excluded_names.add(macro_name)
            for root, _dirs, files in os.walk(case_directory):
                for filename in files:
                    if filename in excluded_names:
                        continue
                    if filename.lower().endswith((".json", ".csv", ".txt", ".dat")):
                        result_paths.append(os.path.join(root, filename))
            result_paths.sort()

            if result_paths:
                fields, artifact_summaries, monitors = summarize_result_artifacts(
                    result_paths,
                    scoring_fields=scoring_fields,
                )
                for index, result_path in enumerate(result_paths, start=1):
                    artifact_manifest[f"result_artifact_{index}"] = result_path
            else:
                fields, artifact_summaries, monitors = summarize_result_artifacts(
                    (),
                    scoring_fields=scoring_fields,
                )

            preferred_path = next(
                (path for path in result_paths if path.lower().endswith(".json")),
                next((path for path in result_paths if path.lower().endswith(".csv")), ""),
            )
            result_format = "Geant4-JSON" if preferred_path.lower().endswith(".json") else (
                "Geant4-CSV" if preferred_path.lower().endswith(".csv") else "Geant4-TXT"
            )
            scoring_summaries, detector_summaries = result_component_summaries(
                case_payload if isinstance(case_payload, dict) else {},
                artifact_summaries,
                monitors,
            )
            primary_quantity = next(
                (field for field in scoring_fields if field),
                next((field for field in fields if field), ""),
            )
            summary_payload = {
                "run_id": handle.run_id,
                "result_file": preferred_path,
                "result_format": result_format,
                "fields": list(fields),
                "available_fields": list(fields),
                "monitors": list(monitors),
                "artifact_summaries": list(artifact_summaries),
                "scoring_summaries": scoring_summaries,
                "detector_summaries": detector_summaries,
                "primary_quantity": primary_quantity,
            }

            summary_path = self._write_result_summary(
                case_directory,
                summary_payload,
            )
            artifact_manifest["result_summary"] = summary_path

        return ResultSet(
            run_id=handle.run_id,
            result_ref=f"results://geant4/{handle.run_id}",
            fields=fields,
            monitors=monitors,
            artifact_manifest=artifact_manifest or {
                "geant4_case": f"artifacts/{handle.run_id}/geant4_case",
            },
        )

    def launch(self, prepared_case: PreparedCase) -> JobHandle:
        return JobHandle(
            run_id=prepared_case.run_id,
            adapter_id=prepared_case.adapter_id,
            state=JobState.RUNNING,
            native_identifier="geant4-skeleton",
        )