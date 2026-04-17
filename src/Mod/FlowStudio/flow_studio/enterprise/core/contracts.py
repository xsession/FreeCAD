# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Typed contracts for enterprise services and adapters."""

from __future__ import annotations

from typing import Mapping
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


class GeometryProvider(Protocol):
    """Contract for CAD geometry access from FreeCAD documents."""

    def export_geometry(self, geometry_ref: str, output_dir: str) -> Mapping[str, str]:
        """Export geometry payloads (STEP/STL/etc.) for downstream workflows."""

    def geometry_fingerprint(self, geometry_ref: str) -> str:
        """Return deterministic geometry hash for provenance and cache keys."""


class TopologyDomainDetector(Protocol):
    """Contract for body/region/domain classification and fluid volume detection."""

    def detect_domains(self, geometry_ref: str) -> Sequence[Mapping[str, str | float | bool]]:
        """Return normalized domain descriptors from source geometry."""

    def detect_interfaces(self, geometry_ref: str) -> Sequence[Mapping[str, str | float | bool]]:
        """Return interface/contact descriptors used by BC and coupling setup."""


class MaterialLibrary(Protocol):
    """Contract for material catalog and property resolution."""

    def list_materials(self, family: str) -> Sequence[str]:
        """List material ids for a given material family/category."""

    def resolve_material(self, material_id: str) -> Mapping[str, str | float | bool]:
        """Resolve one material id to normalized properties."""


class BoundaryConditionModel(Protocol):
    """Contract for BC schema, validation and solver-neutral normalization."""

    def normalize(
        self, bc_payload: Mapping[str, str | float | bool]
    ) -> Mapping[str, str | float | bool]:
        """Normalize a boundary payload to canonical BC schema."""

    def validate(self, request: RunRequest) -> Sequence[ValidationIssue]:
        """Validate BC graph consistency for a run request."""


class PhysicsModelCompiler(Protocol):
    """Contract for compiling high-level physics intent to canonical model flags."""

    def compile(self, request: RunRequest) -> Mapping[str, str | float | bool]:
        """Compile physics node graph into canonical runtime physics config."""


class StudyDefinitionCompiler(Protocol):
    """Contract for assembling immutable study definitions before execution."""

    def compile(self, request: RunRequest) -> RunRequest:
        """Return normalized/expanded run request for execution."""


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
