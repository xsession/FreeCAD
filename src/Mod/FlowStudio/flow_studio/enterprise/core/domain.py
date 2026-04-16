# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Canonical entities for the Flow Studio Enterprise platform."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Sequence


class JobState(str, Enum):
    """Lifecycle states shared by local and remote executions."""

    DRAFT = "Draft"
    VALIDATING = "Validating"
    PREPARED = "Prepared"
    MESHING = "Meshing"
    READY_TO_RUN = "ReadyToRun"
    RUNNING = "Running"
    POST_PROCESSING = "PostProcessing"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"
    ARCHIVED = "Archived"


class JobEventType(str, Enum):
    """Typed event categories used for monitor and log streaming."""

    STATE_CHANGED = "state_changed"
    LOG = "log"
    PROGRESS = "progress"
    MONITOR = "monitor"
    ARTIFACT_READY = "artifact_ready"


@dataclass(frozen=True)
class ValidationIssue:
    """A validation issue produced by core or adapter-level checks."""

    code: str
    message: str
    severity: str = "error"
    object_ref: str | None = None
    remediation: str | None = None


@dataclass(frozen=True)
class CapabilitySet:
    """Capabilities discovered for a solver or mesher adapter."""

    supports_remote: bool = False
    supports_parallel: bool = True
    supports_gpu: bool = False
    supports_transient: bool = True
    supported_physics: Sequence[str] = field(default_factory=tuple)
    feature_flags: Mapping[str, bool] = field(default_factory=dict)


@dataclass(frozen=True)
class AdapterMetadata:
    """Metadata and compatibility facts for a backend adapter."""

    adapter_id: str
    display_name: str
    version: str
    family: str
    commercial_core_safe: bool
    experimental: bool = False
    supported_solver_versions: Sequence[str] = field(default_factory=tuple)
    notes: str = ""


@dataclass(frozen=True)
class MaterialAssignment:
    """Material assignment in the canonical study model."""

    target_ref: str
    material_id: str
    properties: Mapping[str, float | str | bool] = field(default_factory=dict)


@dataclass(frozen=True)
class PhysicsDefinition:
    """Physics intent attached to a study."""

    physics_id: str
    family: str
    options: Mapping[str, str | float | bool] = field(default_factory=dict)
    adapter_extensions: Mapping[str, Mapping[str, str | float | bool]] = field(
        default_factory=dict
    )


@dataclass(frozen=True)
class MeshRecipe:
    """Meshing intent that can be compiled by multiple mesh backends."""

    generator_id: str
    global_size: float
    boundary_layers_enabled: bool = False
    local_controls: Sequence[Mapping[str, str | float | bool]] = field(
        default_factory=tuple
    )


@dataclass(frozen=True)
class StudyDefinition:
    """Solver-neutral study description used by orchestration and adapters."""

    study_id: str
    name: str
    solver_family: str
    geometry_ref: str
    mesh_recipe: MeshRecipe
    materials: Sequence[MaterialAssignment] = field(default_factory=tuple)
    physics: Sequence[PhysicsDefinition] = field(default_factory=tuple)
    parameters: Mapping[str, str | float | bool] = field(default_factory=dict)
    adapter_extensions: Mapping[str, Mapping[str, str | float | bool]] = field(
        default_factory=dict
    )


@dataclass(frozen=True)
class ExecutionProfile:
    """Execution profile for local or remote runs."""

    name: str
    target: str
    target_ref: str | None = None
    cpu_cores: int | None = None
    mpi_ranks: int | None = None
    gpu_devices: Sequence[str] = field(default_factory=tuple)
    memory_limit_mb: int | None = None
    queue: str | None = None


@dataclass(frozen=True)
class RunRequest:
    """A request to execute a study with a selected profile."""

    run_id: str
    study: StudyDefinition
    execution_profile: ExecutionProfile
    requested_by: str = "local-user"
    reason: str = "interactive"


@dataclass(frozen=True)
class PreparedStudyContext:
    """Fully validated context handed to adapters before launch."""

    request: RunRequest
    working_directory: str
    manifest_hash: str
    schema_version: str = "1.0.0"


@dataclass(frozen=True)
class PreparedCase:
    """Prepared case emitted by a solver adapter."""

    adapter_id: str
    run_id: str
    case_directory: str
    launch_command: Sequence[str]
    artifact_manifest: Mapping[str, str]


@dataclass(frozen=True)
class JobHandle:
    """Opaque handle returned by adapter launches."""

    run_id: str
    adapter_id: str
    state: JobState
    native_identifier: str | None = None


@dataclass(frozen=True)
class JobEvent:
    """A structured event streamed during study execution."""

    run_id: str
    event_type: JobEventType
    message: str
    state: JobState | None = None
    progress: float | None = None
    payload: Mapping[str, str | float | bool] = field(default_factory=dict)


@dataclass(frozen=True)
class ResultSet:
    """Canonical result metadata."""

    run_id: str
    result_ref: str
    fields: Sequence[str] = field(default_factory=tuple)
    monitors: Sequence[str] = field(default_factory=tuple)
    artifact_manifest: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RunRecord:
    """Persisted record of a finished or active run."""

    run_id: str
    study_id: str
    state: JobState
    manifest_hash: str
    adapter_id: str
    result_ref: str | None = None
    working_directory: str | None = None
    execution_mode: str | None = None
    return_code: int | None = None
    target: str | None = None
    target_ref: str | None = None
    remote_run_id: str | None = None


@dataclass(frozen=True)
class ProjectManifest:
    """Portable project manifest."""

    schema_version: str
    project_id: str
    studies: Sequence[StudyDefinition] = field(default_factory=tuple)
