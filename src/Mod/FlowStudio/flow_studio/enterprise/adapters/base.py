# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Shared base classes for solver adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from flow_studio.enterprise.core.domain import (
    AdapterMetadata,
    CapabilitySet,
    JobEvent,
    JobEventType,
    JobHandle,
    JobState,
    PreparedCase,
    PreparedStudyContext,
    ResultSet,
    RunRequest,
    ValidationIssue,
)


from flow_studio.enterprise.core.contracts import SolverAdapter as SolverAdapter


class BaseSolverAdapter(ABC):
    """Base class for enterprise solver adapters."""

    adapter_id = "base.unspecified"
    display_name = "Base Solver"
    family = "generic"

    @abstractmethod
    def metadata(self) -> AdapterMetadata:
        """Return static metadata."""

    @abstractmethod
    def capabilities(self) -> CapabilitySet:
        """Return the adapter capability set."""

    def validate(self, request: RunRequest) -> Sequence[ValidationIssue]:
        """Return adapter-specific validation issues."""

        if request.study.solver_family != self.family:
            return [
                ValidationIssue(
                    code="solver.family_mismatch",
                    message=(
                        f"Study family '{request.study.solver_family}' does not match "
                        f"adapter family '{self.family}'."
                    ),
                    remediation="Select a compatible solver adapter.",
                )
            ]
        return []

    @abstractmethod
    def prepare_case(self, context: PreparedStudyContext) -> PreparedCase:
        """Create or materialize the backend-specific case."""

    def launch(self, prepared_case: PreparedCase) -> JobHandle:
        """Return a synthetic ready-to-run handle."""

        return JobHandle(
            run_id=prepared_case.run_id,
            adapter_id=prepared_case.adapter_id,
            state=JobState.READY_TO_RUN,
            native_identifier="synthetic",
        )

    def stream(self, handle: JobHandle) -> Sequence[JobEvent]:
        """Return a minimal default event stream."""

        return [
            JobEvent(
                run_id=handle.run_id,
                event_type=JobEventType.STATE_CHANGED,
                message="Synthetic adapter stream initialized.",
                state=handle.state,
            )
        ]

    @abstractmethod
    def collect_results(self, handle: JobHandle) -> ResultSet:
        """Collect normalized results from the backend."""
