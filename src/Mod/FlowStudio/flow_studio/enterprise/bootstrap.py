# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Workbench bootstrap helpers for Flow Studio Enterprise."""

from __future__ import annotations

from dataclasses import dataclass
import os
import tempfile
from typing import Any, Mapping, Optional

from flow_studio.enterprise.adapters.elmer import ElmerSolverAdapter
from flow_studio.enterprise.adapters.fluidx3d import FluidX3DOptionalAdapter
from flow_studio.enterprise.adapters.geant4 import Geant4SolverAdapter
from flow_studio.enterprise.adapters.openfoam import OpenFOAMSolverAdapter
from flow_studio.enterprise.core.domain import ExecutionProfile
from flow_studio.enterprise.observability.logging import configure_logging, get_logger
from flow_studio.enterprise.services.execution_facade import LegacyExecutionFacade
from flow_studio.enterprise.services.jobs import InMemoryJobService
from flow_studio.enterprise.services.process_executor import LocalProcessExecutor
from flow_studio.enterprise.services.remote_api import (
    LoopbackRemoteJobClient,
    RemoteEndpointDescriptor,
    RemoteJobGateway,
)
from flow_studio.enterprise.services.run_store import FileRunStore


@dataclass(frozen=True)
class EnterpriseRuntime:
    """Lightweight runtime container shared by workbench entry points."""

    job_service: InMemoryJobService
    default_profile: ExecutionProfile
    legacy_execution: LegacyExecutionFacade
    run_store: FileRunStore
    profiles: Mapping[str, ExecutionProfile]


_RUNTIME: Optional[EnterpriseRuntime] = None


def is_enterprise_enabled(env: Mapping[str, str] | None = None) -> bool:
    """Return whether enterprise UI/runtime features are enabled.

    Defaults to enabled to preserve existing behavior.
    Set FLOWSTUDIO_ENTERPRISE_ENABLED=0/false/off/no to disable.
    """

    source = env or os.environ
    raw = str(source.get("FLOWSTUDIO_ENTERPRISE_ENABLED", "1")).strip().lower()
    return raw not in {"0", "false", "off", "no"}


def initialize_workbench() -> EnterpriseRuntime:
    """Initialize platform-wide services."""

    global _RUNTIME
    if _RUNTIME is not None:
        return _RUNTIME

    configure_logging()
    logger = get_logger("flow_studio.enterprise.bootstrap")

    adapters = {
        OpenFOAMSolverAdapter.adapter_id: OpenFOAMSolverAdapter(),
        ElmerSolverAdapter.adapter_id: ElmerSolverAdapter(),
        Geant4SolverAdapter.adapter_id: Geant4SolverAdapter(),
    }
    enable_fluidx3d = os.getenv("FLOWSTUDIO_ENABLE_FLUIDX3D", "0") == "1"
    if enable_fluidx3d:
        adapters[FluidX3DOptionalAdapter.adapter_id] = FluidX3DOptionalAdapter()
        logger.info(
            "enterprise_optional_adapter_enabled",
            extra={
                "adapter_id": FluidX3DOptionalAdapter.adapter_id,
                "reason": "FLOWSTUDIO_ENABLE_FLUIDX3D=1",
            },
        )
    profile = ExecutionProfile(name="local-interactive", target="local")
    remote_profile = ExecutionProfile(
        name="remote-loopback",
        target="remote",
        target_ref="loopback.default",
        queue="interactive",
    )
    run_store = FileRunStore(
        os.path.join(tempfile.gettempdir(), "FlowStudioEnterprise", "runs")
    )
    remote_run_store = FileRunStore(
        os.path.join(tempfile.gettempdir(), "FlowStudioEnterprise", "remote-runs")
    )
    remote_backend = InMemoryJobService(
        adapter_registry=adapters,
        run_store=remote_run_store,
        process_executor=LocalProcessExecutor(),
    )
    remote_gateway = RemoteJobGateway(
        remote_backend,
        endpoint=RemoteEndpointDescriptor(
            endpoint_id="loopback.default",
            display_name="Loopback Remote Gateway",
            transport="loopback",
        ),
    )
    job_service = InMemoryJobService(
        adapter_registry=adapters,
        run_store=run_store,
        process_executor=LocalProcessExecutor(),
        remote_clients={"loopback.default": LoopbackRemoteJobClient(remote_gateway)},
    )
    _RUNTIME = EnterpriseRuntime(
        job_service=job_service,
        default_profile=profile,
        legacy_execution=LegacyExecutionFacade(job_service),
        run_store=run_store,
        profiles={
            profile.name: profile,
            remote_profile.name: remote_profile,
        },
    )

    logger.info(
        "enterprise_runtime_initialized",
        extra={
            "adapter_ids": sorted(adapters.keys()),
            "default_profile": profile.name,
            "remote_profiles": sorted(_RUNTIME.profiles.keys()),
            "run_store_root": run_store.root_directory,
        },
    )
    return _RUNTIME


def on_workbench_activated() -> EnterpriseRuntime:
    """Return the initialized runtime when the workbench is activated."""

    runtime = initialize_workbench()
    get_logger("flow_studio.enterprise.bootstrap").info(
        "enterprise_workbench_activated",
        extra={"default_profile": runtime.default_profile.name},
    )
    return runtime


def adapter_capability_matrix() -> tuple[dict[str, Any], ...]:
    """Return an adapter capability matrix consumable by UI components."""

    runtime = initialize_workbench()
    return runtime.job_service.adapter_capability_matrix()
