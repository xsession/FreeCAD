# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Transport-neutral remote job gateway contracts for Flow Studio Enterprise."""

from __future__ import annotations

from dataclasses import replace
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, Sequence

from flow_studio.enterprise.core.domain import (
    JobEvent,
    JobEventType,
    JobState,
    ResultSet,
    RunRecord,
    RunRequest,
)

if TYPE_CHECKING:
    from flow_studio.enterprise.services.jobs import InMemoryJobService


@dataclass(frozen=True)
class RemoteEndpointDescriptor:
    """Describes a remote execution endpoint exposed to the desktop client."""

    endpoint_id: str
    display_name: str
    transport: str = "loopback"
    supports_streaming: bool = False
    supports_partial_results: bool = False


@dataclass(frozen=True)
class JobSubmissionRequest:
    """Transport-safe request for remote study submission."""

    adapter_id: str
    profile_name: str
    target_ref: str | None
    working_directory: str
    manifest_hash: str
    run_request: RunRequest


@dataclass(frozen=True)
class JobSubmissionResponse:
    """Transport-safe response for remote study submission."""

    run_id: str
    accepted: bool
    state: str
    remote_run_id: str | None = None
    result_ref: str | None = None
    message: str = ""


class RemoteJobClient(Protocol):
    """Client contract used by the desktop orchestrator for remote targets."""

    def endpoint(self) -> RemoteEndpointDescriptor:
        """Return metadata about the remote endpoint."""

    def submit(self, request: JobSubmissionRequest) -> JobSubmissionResponse:
        """Submit a run to the remote endpoint."""

    def run_record(self, run_id: str) -> RunRecord | None:
        """Return the latest remote run record when available."""

    def events(self, run_id: str) -> Sequence[JobEvent]:
        """Return buffered remote events for a run."""

    def result(self, run_id: str) -> ResultSet | None:
        """Return the remote result set when available."""


class RemoteJobGateway:
    """Service facade that can back a REST or gRPC transport layer."""

    def __init__(
        self,
        job_service: "InMemoryJobService",
        endpoint: RemoteEndpointDescriptor | None = None,
    ):
        self._job_service = job_service
        self._endpoint = endpoint or RemoteEndpointDescriptor(
            endpoint_id="loopback.default",
            display_name="Loopback Remote Gateway",
        )

    def endpoint(self) -> RemoteEndpointDescriptor:
        """Return metadata about the gateway endpoint."""

        return self._endpoint

    def adapter_ids(self) -> tuple[str, ...]:
        """Return the adapter ids registered behind the gateway."""

        return self._job_service.adapter_ids()

    def submit(self, request: JobSubmissionRequest) -> JobSubmissionResponse:
        """Submit a job to the underlying orchestration service."""

        backend_request = replace(
            request.run_request,
            execution_profile=replace(
                request.run_request.execution_profile,
                target="local",
                target_ref=self._endpoint.endpoint_id,
            ),
        )
        record = self._job_service.submit(
            request=backend_request,
            adapter_id=request.adapter_id,
            working_directory=request.working_directory,
            manifest_hash=request.manifest_hash,
        )
        return JobSubmissionResponse(
            run_id=record.run_id,
            accepted=True,
            state=record.state.value,
            remote_run_id=record.run_id,
            result_ref=record.result_ref,
            message=f"Submitted to {self._endpoint.display_name}",
        )

    def run_record(self, run_id: str) -> RunRecord | None:
        """Return a normalized run record for a previously submitted job."""

        payload = self._job_service.persisted_run_record(run_id)
        if payload is None:
            return None
        return RunRecord(
            run_id=payload["run_id"],
            study_id=payload["study_id"],
            state=JobState(payload["state"]),
            manifest_hash=payload["manifest_hash"],
            adapter_id=payload["adapter_id"],
            result_ref=payload.get("result_ref"),
            working_directory=payload.get("working_directory"),
            execution_mode=payload.get("execution_mode"),
            return_code=payload.get("return_code"),
            target=payload.get("target"),
            target_ref=payload.get("target_ref"),
            remote_run_id=payload.get("remote_run_id"),
        )

    def events(self, run_id: str) -> Sequence[JobEvent]:
        """Return persisted events for a previously submitted job."""

        payloads = self._job_service.persisted_run_events(run_id)
        events: list[JobEvent] = []
        for payload in payloads:
            events.append(
                JobEvent(
                    run_id=payload["run_id"],
                    event_type=JobEventType(payload["event_type"]),
                    message=payload["message"],
                    state=JobState(payload["state"]) if payload.get("state") else None,
                    progress=payload.get("progress"),
                    payload=payload.get("payload", {}),
                )
            )
        return tuple(events)

    def result(self, run_id: str) -> ResultSet | None:
        """Return a normalized result set for a previously submitted job."""

        payload = self._job_service.persisted_run_result(run_id)
        if not payload:
            return None
        return ResultSet(
            run_id=payload["run_id"],
            result_ref=payload["result_ref"],
            fields=tuple(payload.get("fields", ())),
            monitors=tuple(payload.get("monitors", ())),
            artifact_manifest=payload.get("artifact_manifest", {}),
        )


class LoopbackRemoteJobClient:
    """Remote client that talks to an in-process gateway for integration tests."""

    def __init__(self, gateway: RemoteJobGateway):
        self._gateway = gateway

    def endpoint(self) -> RemoteEndpointDescriptor:
        return self._gateway.endpoint()

    def submit(self, request: JobSubmissionRequest) -> JobSubmissionResponse:
        return self._gateway.submit(request)

    def run_record(self, run_id: str) -> RunRecord | None:
        return self._gateway.run_record(run_id)

    def events(self, run_id: str) -> Sequence[JobEvent]:
        return self._gateway.events(run_id)

    def result(self, run_id: str) -> ResultSet | None:
        return self._gateway.result(run_id)
