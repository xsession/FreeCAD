# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Elmer enterprise adapter skeleton."""

from __future__ import annotations

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


class ElmerSolverAdapter(BaseSolverAdapter):
    """Elmer backend for multiphysics-oriented studies."""

    adapter_id = "elmer.primary"
    display_name = "Elmer"
    family = "elmer"

    @staticmethod
    def _extension_options(context: PreparedStudyContext) -> dict[str, str | float | bool]:
        options = context.request.study.adapter_extensions.get("elmer.primary", {})
        return dict(options)

    def metadata(self) -> AdapterMetadata:
        return AdapterMetadata(
            adapter_id=self.adapter_id,
            display_name=self.display_name,
            version="0.1.0",
            family=self.family,
            commercial_core_safe=True,
            supported_solver_versions=("9.0", "9.1"),
            notes="Primary multiphysics-capable backend for Flow Studio Enterprise.",
        )

    def capabilities(self) -> CapabilitySet:
        return CapabilitySet(
            supports_remote=True,
            supports_parallel=True,
            supports_gpu=False,
            supports_transient=True,
            supported_physics=("thermal", "structural", "electrostatic", "cht"),
            feature_flags={
                "mpi_launch_profiles": True,
                "sif_generation": True,
                "multiphysics_coupling": True,
            },
        )

    def prepare_case(self, context: PreparedStudyContext) -> PreparedCase:
        case_directory = os.path.join(context.working_directory, "elmer_case")
        os.makedirs(os.path.join(case_directory, "mesh"), exist_ok=True)
        options = self._extension_options(context)
        artifact_manifest = {
            "case.sif": os.path.join(case_directory, "case.sif"),
            "mesh/mesh.header": os.path.join(case_directory, "mesh", "mesh.header"),
        }
        for relative_path, absolute_path in artifact_manifest.items():
            with open(absolute_path, "w", encoding="utf-8") as handle:
                handle.write(f"! Flow Studio Enterprise placeholder for {relative_path}\n")
                for key, value in sorted(options.items()):
                    handle.write(f"! {key}={value}\n")
        solver_binary = str(options.get("solver_binary", "ElmerSolver"))
        return PreparedCase(
            adapter_id=self.adapter_id,
            run_id=context.request.run_id,
            case_directory=case_directory,
            launch_command=(solver_binary, "case.sif"),
            artifact_manifest=artifact_manifest,
        )

    def collect_results(self, handle: JobHandle) -> ResultSet:
        return ResultSet(
            run_id=handle.run_id,
            result_ref=f"results://elmer/{handle.run_id}",
            fields=("Temperature", "Displacement", "Potential"),
            monitors=("nonlinear_iterations", "probe_points"),
            artifact_manifest={
                "elmer_case": f"artifacts/{handle.run_id}/elmer_case",
            },
        )

    def launch(self, prepared_case: PreparedCase) -> JobHandle:
        return JobHandle(
            run_id=prepared_case.run_id,
            adapter_id=prepared_case.adapter_id,
            state=JobState.RUNNING,
            native_identifier="elmer-skeleton",
        )
