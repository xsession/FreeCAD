# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Canonical enterprise domain model and contracts."""

from .adapter_policy import (
    COMPATIBILITY_MATRIX,
    PLUGIN_API_POLICY,
    PLUGIN_API_STABILITY,
    PLUGIN_API_VERSION,
    AdapterCompatibility,
    validate_plugin_metadata,
)
from .contracts import MeshGenerator, MonitorStream, PostProcessor, ReportGenerator, SolverAdapter
from .domain import (
    AdapterMetadata,
    CapabilitySet,
    ExecutionProfile,
    JobEvent,
    JobEventType,
    JobHandle,
    JobState,
    MaterialAssignment,
    MeshRecipe,
    PhysicsDefinition,
    PreparedCase,
    PreparedStudyContext,
    ProjectManifest,
    ResultSet,
    RunRecord,
    RunRequest,
    StudyDefinition,
    ValidationIssue,
)
from .serialization import to_json, to_primitive, to_sha256

__all__ = [
    "AdapterCompatibility",
    "AdapterMetadata",
    "CapabilitySet",
    "COMPATIBILITY_MATRIX",
    "ExecutionProfile",
    "JobEvent",
    "JobEventType",
    "JobHandle",
    "JobState",
    "MaterialAssignment",
    "MeshGenerator",
    "MeshRecipe",
    "MonitorStream",
    "PhysicsDefinition",
    "PostProcessor",
    "PreparedCase",
    "PreparedStudyContext",
    "ProjectManifest",
    "ReportGenerator",
    "ResultSet",
    "RunRecord",
    "RunRequest",
    "SolverAdapter",
    "StudyDefinition",
    "PLUGIN_API_POLICY",
    "PLUGIN_API_STABILITY",
    "PLUGIN_API_VERSION",
    "ValidationIssue",
    "validate_plugin_metadata",
    "to_json",
    "to_primitive",
    "to_sha256",
]
