# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""OpenFOAM enterprise adapter skeleton."""

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
    RunRequest,
    ValidationIssue,
)


class OpenFOAMSolverAdapter(BaseSolverAdapter):
    """Canonical OpenFOAM adapter boundary."""

    adapter_id = "openfoam.primary"
    display_name = "OpenFOAM"
    family = "openfoam"

    @staticmethod
    def _extension_options(context: PreparedStudyContext) -> dict[str, str | float | bool]:
        options = context.request.study.adapter_extensions.get("openfoam.primary", {})
        return dict(options)

    def metadata(self) -> AdapterMetadata:
        return AdapterMetadata(
            adapter_id=self.adapter_id,
            display_name=self.display_name,
            version="0.1.0",
            family=self.family,
            commercial_core_safe=True,
            supported_solver_versions=("v2212", "v2306", "v2312"),
            notes="Primary open CFD backend for Flow Studio Enterprise.",
        )

    def capabilities(self) -> CapabilitySet:
        return CapabilitySet(
            supports_remote=True,
            supports_parallel=True,
            supports_gpu=False,
            supports_transient=True,
            supported_physics=("cfd.internal", "cfd.external", "cht"),
            feature_flags={
                "region_support": True,
                "function_objects": True,
                "custom_solver_binary": True,
            },
        )

    def validate(self, request: RunRequest) -> tuple[ValidationIssue, ...]:
        issues = list(super().validate(request))
        if not request.study.mesh_recipe.generator_id:
            issues.append(
                ValidationIssue(
                    code="openfoam.mesh_recipe_missing",
                    message="OpenFOAM studies require a mesh recipe generator id.",
                    remediation="Select a supported mesh generator.",
                )
            )
        return tuple(issues)

    def prepare_case(self, context: PreparedStudyContext) -> PreparedCase:
        case_directory = os.path.join(context.working_directory, "openfoam_case")
        os.makedirs(os.path.join(case_directory, "system"), exist_ok=True)
        os.makedirs(os.path.join(case_directory, "constant"), exist_ok=True)
        os.makedirs(os.path.join(case_directory, "0"), exist_ok=True)
        options = self._extension_options(context)
        artifact_manifest = {
            "system/controlDict": os.path.join(case_directory, "system", "controlDict"),
            "system/fvSchemes": os.path.join(case_directory, "system", "fvSchemes"),
            "system/fvSolution": os.path.join(case_directory, "system", "fvSolution"),
            "constant/transportProperties": os.path.join(
                case_directory, "constant", "transportProperties"
            ),
        }
        for relative_path, absolute_path in artifact_manifest.items():
            with open(absolute_path, "w", encoding="utf-8") as handle:
                handle.write(f"# Flow Studio Enterprise placeholder for {relative_path}\n")
                for key, value in sorted(options.items()):
                    handle.write(f"# {key}={value}\n")
        solver_binary = str(options.get("solver_binary", "simpleFoam"))
        return PreparedCase(
            adapter_id=self.adapter_id,
            run_id=context.request.run_id,
            case_directory=case_directory,
            launch_command=(solver_binary, "-case", case_directory),
            artifact_manifest=artifact_manifest,
        )

    def collect_results(self, handle: JobHandle) -> ResultSet:
        return ResultSet(
            run_id=handle.run_id,
            result_ref=f"results://openfoam/{handle.run_id}",
            fields=("p", "U", "T"),
            monitors=("residuals", "forces", "probes"),
            artifact_manifest={
                "foam_case": f"artifacts/{handle.run_id}/openfoam_case",
            },
        )

    def launch(self, prepared_case: PreparedCase) -> JobHandle:
        return JobHandle(
            run_id=prepared_case.run_id,
            adapter_id=prepared_case.adapter_id,
            state=JobState.RUNNING,
            native_identifier="openfoam-skeleton",
        )
