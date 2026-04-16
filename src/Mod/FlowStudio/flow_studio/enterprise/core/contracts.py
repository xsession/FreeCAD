# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Typed contracts for enterprise services and adapters."""

from __future__ import annotations

from typing import Protocol, Sequence

from .domain import (
    AdapterMetadata,
    CapabilitySet,
    JobEvent,
    JobHandle,
    PreparedCase,
    PreparedStudyContext,
    ResultSet,
    RunRequest,
    ValidationIssue,
)


class MeshGenerator(Protocol):
    """Contract for meshing adapters."""

    def metadata(self) -> AdapterMetadata:
        """Return static adapter metadata."""

    def capabilities(self) -> CapabilitySet:
        """Return discovered adapter capabilities."""

    def validate(self, request: RunRequest) -> Sequence[ValidationIssue]:
        """Validate the study for this mesher."""


class SolverAdapter(Protocol):
    """Contract for solver runners exposed to orchestration."""

    def metadata(self) -> AdapterMetadata:
        """Return static adapter metadata."""

    def capabilities(self) -> CapabilitySet:
        """Return discovered adapter capabilities."""

    def validate(self, request: RunRequest) -> Sequence[ValidationIssue]:
        """Validate a run request for this solver."""

    def prepare_case(self, context: PreparedStudyContext) -> PreparedCase:
        """Create the deterministic case directory or bundle."""

    def launch(self, prepared_case: PreparedCase) -> JobHandle:
        """Start execution and return a handle."""

    def stream(self, handle: JobHandle) -> Sequence[JobEvent]:
        """Return available stream events for the handle."""

    def collect_results(self, handle: JobHandle) -> ResultSet:
        """Collect and normalize results."""


class MonitorStream(Protocol):
    """Contract for live monitor and progress channels."""

    def events(self, handle: JobHandle) -> Sequence[JobEvent]:
        """Return the latest buffered events."""


class PostProcessor(Protocol):
    """Contract for post-processing services."""

    def import_results(self, handle: JobHandle) -> ResultSet:
        """Normalize backend-specific outputs."""


class ReportGenerator(Protocol):
    """Contract for report generation services."""

    def build_report(self, result: ResultSet) -> str:
        """Return a generated report reference."""
