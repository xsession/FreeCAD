# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""High-level execution helpers that bridge legacy Flow Studio objects."""

from __future__ import annotations

from dataclasses import dataclass

from flow_studio.enterprise.core.domain import ExecutionProfile, RunRecord, RunRequest
from flow_studio.enterprise.integration.freecad_bridge import LegacyAnalysisBridge
from flow_studio.enterprise.services.jobs import InMemoryJobService


def _default_adapter_id(study_solver_family: str) -> str:
    mapping = {
        "openfoam": "openfoam.primary",
        "elmer": "elmer.primary",
        "fluidx3d": "fluidx3d.optional",
    }
    return mapping.get(study_solver_family, study_solver_family)


@dataclass(frozen=True)
class LegacyExecutionRequest:
    """Input required to submit a legacy analysis through enterprise services."""

    analysis_object: object
    run_id: str
    working_directory: str
    manifest_hash: str
    requested_by: str = "local-user"
    reason: str = "interactive"
    execution_profile: ExecutionProfile | None = None


class LegacyExecutionFacade:
    """Translate and submit existing Flow Studio analyses to the job service."""

    def __init__(self, job_service: InMemoryJobService):
        self._job_service = job_service

    def build_run_request(self, request: LegacyExecutionRequest) -> tuple[str, RunRequest]:
        """Build an adapter id and canonical run request from a legacy analysis."""

        study = LegacyAnalysisBridge(request.analysis_object).to_study_definition()
        profile = request.execution_profile or ExecutionProfile(name="local-interactive", target="local")
        run_request = RunRequest(
            run_id=request.run_id,
            study=study,
            execution_profile=profile,
            requested_by=request.requested_by,
            reason=request.reason,
        )
        return _default_adapter_id(study.solver_family), run_request

    def submit(self, request: LegacyExecutionRequest) -> RunRecord:
        """Submit a translated legacy analysis to the underlying job service."""

        adapter_id, run_request = self.build_run_request(request)
        return self._job_service.submit(
            request=run_request,
            adapter_id=adapter_id,
            working_directory=request.working_directory,
            manifest_hash=request.manifest_hash,
        )


def submit_legacy_analysis(
    analysis_object: object,
    run_id: str,
    working_directory: str,
    manifest_hash: str,
    *,
    requested_by: str = "local-user",
    reason: str = "interactive",
    execution_profile: ExecutionProfile | None = None,
    job_service: InMemoryJobService | None = None,
) -> RunRecord:
    """Compatibility helper mirroring the pre-facade submission entry point."""

    facade = LegacyExecutionFacade(job_service or InMemoryJobService())
    request = LegacyExecutionRequest(
        analysis_object=analysis_object,
        run_id=run_id,
        working_directory=working_directory,
        manifest_hash=manifest_hash,
        requested_by=requested_by,
        reason=reason,
        execution_profile=execution_profile,
    )
    return facade.submit(request)
