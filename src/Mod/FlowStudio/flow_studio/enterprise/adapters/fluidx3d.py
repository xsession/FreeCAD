# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""FluidX3D optional enterprise adapter.

Licensing boundary:
- This adapter is optional and not required by the core platform.
- It is marked commercial_core_safe=False because FluidX3D licensing for
  commercial embedding must be validated independently.
- The platform remains fully viable with OpenFOAM + Elmer only.
"""

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


class FluidX3DOptionalAdapter(BaseSolverAdapter):
    """Non-core, optional adapter for exploratory GPU LBM runs."""

    adapter_id = "fluidx3d.optional"
    display_name = "FluidX3D (Optional)"
    family = "fluidx3d"

    @staticmethod
    def _extension_options(context: PreparedStudyContext) -> dict[str, str | float | bool]:
        options = context.request.study.adapter_extensions.get("fluidx3d.optional", {})
        return dict(options)

    def metadata(self) -> AdapterMetadata:
        return AdapterMetadata(
            adapter_id=self.adapter_id,
            display_name=self.display_name,
            version="0.1.0",
            family=self.family,
            commercial_core_safe=False,
            experimental=True,
            supported_solver_versions=("2.x",),
            notes=(
                "Optional adapter only. Treat as non-commercial unless a separate "
                "commercial license path is confirmed."
            ),
        )

    def capabilities(self) -> CapabilitySet:
        return CapabilitySet(
            supports_remote=False,
            supports_parallel=False,
            supports_gpu=True,
            supports_transient=True,
            supported_physics=("cfd.incompressible.exploratory",),
            feature_flags={
                "non_commercial_only": True,
                "gpu_required": True,
                "interactive_preview": True,
                "optional_adapter": True,
            },
        )

    def prepare_case(self, context: PreparedStudyContext) -> PreparedCase:
        case_directory = os.path.join(context.working_directory, "fluidx3d_case")
        os.makedirs(case_directory, exist_ok=True)
        options = self._extension_options(context)
        setup_path = os.path.join(case_directory, "setup.cpp")
        with open(setup_path, "w", encoding="utf-8") as handle:
            handle.write("// Flow Studio enterprise optional FluidX3D scaffold\n")
            handle.write("// This file is a generated placeholder for adapter integration.\n")
            for key, value in sorted(options.items()):
                handle.write(f"// {key}={value}\n")
        launch_executable = str(options.get("solver_binary", "FluidX3D"))
        return PreparedCase(
            adapter_id=self.adapter_id,
            run_id=context.request.run_id,
            case_directory=case_directory,
            launch_command=(launch_executable,),
            artifact_manifest={
                "setup.cpp": setup_path,
            },
            max_runtime_seconds=context.request.runtime_thresholds.max_wall_time_seconds,
        )

    def collect_results(self, handle: JobHandle) -> ResultSet:
        return ResultSet(
            run_id=handle.run_id,
            result_ref=f"results://fluidx3d/{handle.run_id}",
            fields=("rho", "u"),
            monitors=("mlups", "frame_time"),
            artifact_manifest={
                "fluidx3d_case": f"artifacts/{handle.run_id}/fluidx3d_case",
            },
        )

    def launch(self, prepared_case: PreparedCase) -> JobHandle:
        return JobHandle(
            run_id=prepared_case.run_id,
            adapter_id=prepared_case.adapter_id,
            state=JobState.RUNNING,
            native_identifier="fluidx3d-skeleton",
        )
