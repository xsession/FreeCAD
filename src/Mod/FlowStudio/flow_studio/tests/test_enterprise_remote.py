# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Tests for remote-target enterprise execution routing."""

from dataclasses import replace
import json
from pathlib import Path

from flow_studio.enterprise.adapters.geant4 import Geant4SolverAdapter
from flow_studio.enterprise.adapters.openfoam import OpenFOAMSolverAdapter
from flow_studio.enterprise.core.domain import ExecutionProfile
from flow_studio.enterprise.services.jobs import InMemoryJobService
from flow_studio.enterprise.services.process_executor import LocalProcessExecutor
from flow_studio.enterprise.services.remote_api import (
    LoopbackRemoteJobClient,
    RemoteEndpointDescriptor,
    RemoteJobGateway,
)
from flow_studio.enterprise.services.run_store import FileRunStore
from flow_studio.enterprise.testing.harness import make_demo_request


def test_job_service_submits_remote_run_via_loopback_gateway(tmp_path: Path):
    adapter = OpenFOAMSolverAdapter()
    remote_backend = InMemoryJobService(
        {adapter.adapter_id: adapter},
        run_store=FileRunStore(str(tmp_path / "remote-store")),
        process_executor=LocalProcessExecutor(),
    )
    remote_client = LoopbackRemoteJobClient(
        RemoteJobGateway(
            remote_backend,
            endpoint=RemoteEndpointDescriptor(
                endpoint_id="loopback.default",
                display_name="Loopback Remote Gateway",
            ),
        )
    )
    desktop_service = InMemoryJobService(
        {adapter.adapter_id: adapter},
        run_store=FileRunStore(str(tmp_path / "desktop-store")),
        remote_clients={"loopback.default": remote_client},
    )
    request = make_demo_request("run-remote", solver_family=adapter.metadata().family)
    request = request.__class__(
        run_id=request.run_id,
        study=request.study,
        execution_profile=ExecutionProfile(
            name="remote-loopback",
            target="remote",
            target_ref="loopback.default",
            queue="interactive",
        ),
        requested_by=request.requested_by,
        reason=request.reason,
    )

    record = desktop_service.submit(
        request=request,
        adapter_id=adapter.adapter_id,
        working_directory=str(tmp_path / "desktop-working"),
        manifest_hash="sha256:remote-submit",
    )

    assert record.state.value == "Completed"
    assert record.target == "remote"
    assert record.target_ref == "loopback.default"
    assert record.remote_run_id == "run-remote"
    assert record.execution_mode in {"synthetic", "subprocess", "adapter-launch"}

    result = desktop_service.result("run-remote")
    assert result.result_ref.startswith("results://openfoam/")

    summaries = desktop_service.persisted_run_summaries()
    assert summaries[0]["target_ref"] == "loopback.default"

    events = desktop_service.persisted_run_events("run-remote")
    assert any(event.get("payload", {}).get("remote_run_id") == "run-remote" for event in events)

    execution_log = desktop_service.persisted_execution_log("run-remote")
    assert "execution_mode=remote-gateway" in execution_log
    assert "target_ref=loopback.default" in execution_log


def test_job_service_requires_configured_remote_target(tmp_path: Path):
    adapter = OpenFOAMSolverAdapter()
    desktop_service = InMemoryJobService(
        {adapter.adapter_id: adapter},
        run_store=FileRunStore(str(tmp_path / "desktop-store")),
    )
    request = make_demo_request("run-remote-missing", solver_family=adapter.metadata().family)
    request = request.__class__(
        run_id=request.run_id,
        study=request.study,
        execution_profile=ExecutionProfile(
            name="remote-missing",
            target="remote",
            target_ref="missing.endpoint",
        ),
        requested_by=request.requested_by,
        reason=request.reason,
    )

    try:
        desktop_service.submit(
            request=request,
            adapter_id=adapter.adapter_id,
            working_directory=str(tmp_path / "desktop-working"),
            manifest_hash="sha256:remote-missing",
        )
    except KeyError as exc:
        assert "missing.endpoint" in str(exc)
    else:
        raise AssertionError("Expected remote submission to fail for an unknown remote target.")


def test_geant4_remote_run_persists_result_summary(tmp_path: Path):
    adapter = Geant4SolverAdapter()
    remote_backend = InMemoryJobService(
        {adapter.adapter_id: adapter},
        run_store=FileRunStore(str(tmp_path / "remote-store")),
        process_executor=LocalProcessExecutor(),
    )
    remote_client = LoopbackRemoteJobClient(
        RemoteJobGateway(
            remote_backend,
            endpoint=RemoteEndpointDescriptor(
                endpoint_id="loopback.default",
                display_name="Loopback Remote Gateway",
            ),
        )
    )
    desktop_service = InMemoryJobService(
        {adapter.adapter_id: adapter},
        run_store=FileRunStore(str(tmp_path / "desktop-store")),
        remote_clients={"loopback.default": remote_client},
    )
    request = make_demo_request("run-geant4-remote", solver_family=adapter.metadata().family)
    request = replace(
        request,
        study=replace(
            request.study,
            adapter_extensions={
                "geant4.primary": {
                    "macro_name": "run.mac",
                    "threads": 2,
                    "event_count": 100,
                    "scoring": [{"score_quantity": "DoseDeposit"}],
                }
            },
        ),
        execution_profile=ExecutionProfile(
            name="remote-loopback",
            target="remote",
            target_ref="loopback.default",
            queue="interactive",
        ),
    )

    record = desktop_service.submit(
        request=request,
        adapter_id=adapter.adapter_id,
        working_directory=str(tmp_path / "desktop-working"),
        manifest_hash="sha256:geant4-remote",
    )

    assert record.state.value == "Completed"
    result = desktop_service.result("run-geant4-remote")
    assert result is not None
    assert "result_summary" in result.artifact_manifest
    summary_path = Path(result.artifact_manifest["result_summary"])
    assert summary_path.is_file()
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    assert "DoseDeposit" in payload["fields"]
    assert "dose" in payload["fields"]
    assert "scoring_summaries" in payload
    assert payload["primary_quantity"] == "DoseDeposit"
    persisted = desktop_service.persisted_run_result("run-geant4-remote")
    assert persisted["artifact_manifest"]["result_summary"] == str(summary_path)
