# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Local and remote orchestration services for enterprise study execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from flow_studio.enterprise.core.contracts import SolverAdapter
from flow_studio.enterprise.core.domain import (
    JobEvent,
    JobEventType,
    JobHandle,
    JobState,
    PreparedCase,
    PreparedStudyContext,
    ResultSet,
    RunRecord,
    RunRequest,
    ValidationIssue,
)
from flow_studio.enterprise.services.process_executor import LocalProcessExecutor
from flow_studio.enterprise.services.remote_api import JobSubmissionRequest, RemoteJobClient
from flow_studio.enterprise.services.run_store import FileRunStore


@dataclass
class JobSubmission:
    """Internal stored execution record."""

    request: RunRequest
    handle: JobHandle | None = None
    result: ResultSet | None = None
    events: list[JobEvent] = field(default_factory=list)


class InMemoryJobService:
    """Small orchestration skeleton for local testing and bootstrap wiring."""

    def __init__(
        self,
        adapter_registry: Mapping[str, SolverAdapter],
        run_store: FileRunStore | None = None,
        process_executor: LocalProcessExecutor | None = None,
        remote_clients: Mapping[str, RemoteJobClient] | None = None,
    ):
        self._adapter_registry = dict(adapter_registry)
        self._submissions: dict[str, JobSubmission] = {}
        self._run_store = run_store
        self._process_executor = process_executor
        self._remote_clients = dict(remote_clients or {})

    def validate(self, request: RunRequest, adapter_id: str) -> tuple[ValidationIssue, ...]:
        """Validate a request through the selected adapter."""

        adapter = self._adapter_registry[adapter_id]
        return tuple(adapter.validate(request))

    def adapter_ids(self) -> tuple[str, ...]:
        """Return registered adapter identifiers."""

        return tuple(sorted(self._adapter_registry.keys()))

    def adapter_capability_matrix(self) -> tuple[dict[str, Any], ...]:
        """Return a UI-ready capability matrix for registered adapters."""

        rows: list[dict[str, Any]] = []
        for adapter_id in sorted(self._adapter_registry.keys()):
            adapter = self._adapter_registry[adapter_id]
            metadata = adapter.metadata()
            capabilities = adapter.capabilities()
            rows.append(
                {
                    "adapter_id": metadata.adapter_id,
                    "display_name": metadata.display_name,
                    "family": metadata.family,
                    "version": metadata.version,
                    "commercial_core_safe": metadata.commercial_core_safe,
                    "experimental": metadata.experimental,
                    "supported_solver_versions": tuple(metadata.supported_solver_versions),
                    "supports_remote": capabilities.supports_remote,
                    "supports_parallel": capabilities.supports_parallel,
                    "supports_gpu": capabilities.supports_gpu,
                    "supports_transient": capabilities.supports_transient,
                    "supported_physics": tuple(capabilities.supported_physics),
                    "feature_flags": dict(capabilities.feature_flags),
                    "notes": metadata.notes,
                }
            )
        return tuple(rows)

    def remote_target_ids(self) -> tuple[str, ...]:
        """Return configured remote-target identifiers."""

        return tuple(sorted(self._remote_clients.keys()))

    def submit(
        self, request: RunRequest, adapter_id: str, working_directory: str, manifest_hash: str
    ) -> RunRecord:
        """Prepare and launch a study using the selected adapter."""

        if request.execution_profile.target == "remote":
            return self._submit_remote(
                request=request,
                adapter_id=adapter_id,
                working_directory=working_directory,
                manifest_hash=manifest_hash,
            )
        return self._submit_local(
            request=request,
            adapter_id=adapter_id,
            working_directory=working_directory,
            manifest_hash=manifest_hash,
        )

    def _submit_local(
        self, request: RunRequest, adapter_id: str, working_directory: str, manifest_hash: str
    ) -> RunRecord:
        """Prepare and launch a study on the local workstation."""

        adapter = self._adapter_registry[adapter_id]
        events: list[JobEvent] = []
        events.append(self._state_event(request.run_id, JobState.VALIDATING, "Validating run request."))
        issues = adapter.validate(request)
        if issues:
            for issue in issues:
                events.append(
                    JobEvent(
                        run_id=request.run_id,
                        event_type=JobEventType.LOG,
                        message=issue.message,
                        state=JobState.FAILED,
                        payload={
                            "code": issue.code,
                            "severity": issue.severity,
                            "remediation": issue.remediation or "",
                        },
                    )
                )
            raise ValueError(f"Run request failed validation: {issues}")

        context = PreparedStudyContext(
            request=request,
            working_directory=working_directory,
            manifest_hash=manifest_hash,
        )
        prepared = adapter.prepare_case(context)
        events.append(self._state_event(request.run_id, JobState.PREPARED, "Prepared solver case."))

        execution_log = ""
        if self._process_executor is not None:
            events.append(
                self._state_event(request.run_id, JobState.RUNNING, "Launching local process execution.")
            )
            execution = self._process_executor.execute(prepared)
            handle = JobHandle(
                run_id=request.run_id,
                adapter_id=adapter_id,
                state=execution.state,
                native_identifier=execution.native_identifier,
            )
            execution_log = self._compose_execution_log(execution)
            if execution.stdout:
                events.append(
                    JobEvent(
                        run_id=request.run_id,
                        event_type=JobEventType.LOG,
                        message=execution.stdout.strip(),
                        state=execution.state,
                        payload={"execution_mode": execution.execution_mode},
                    )
                )
            if execution.stderr:
                events.append(
                    JobEvent(
                        run_id=request.run_id,
                        event_type=JobEventType.LOG,
                        message=execution.stderr.strip(),
                        state=execution.state,
                        payload={"execution_mode": execution.execution_mode},
                    )
                )
        else:
            handle = adapter.launch(prepared)
            execution = None
            execution_log = "execution_mode=adapter-launch\nreturn_code=0\n"

        events.append(
            self._state_event(
                request.run_id,
                handle.state,
                f"Execution finished with state '{handle.state.value}'.",
            )
        )
        events.extend(list(adapter.stream(handle)))
        result = adapter.collect_results(handle) if handle.state != JobState.FAILED else None

        submission = JobSubmission(request=request, handle=handle, result=result, events=events)
        self._submissions[request.run_id] = submission
        record = RunRecord(
            run_id=request.run_id,
            study_id=request.study.study_id,
            state=handle.state,
            manifest_hash=manifest_hash,
            adapter_id=adapter_id,
            result_ref=result.result_ref if result is not None else None,
            working_directory=prepared.case_directory,
            execution_mode=execution.execution_mode if execution is not None else "adapter-launch",
            return_code=execution.return_code if execution is not None else 0,
            target=request.execution_profile.target,
            target_ref=request.execution_profile.target_ref,
        )
        if self._run_store is not None:
            self._run_store.persist_run(
                run_id=request.run_id,
                request=request,
                prepared_case=prepared,
                run_record=record,
                result=result,
                events=events,
                execution_log=execution_log,
            )
        return record

    def _submit_remote(
        self, request: RunRequest, adapter_id: str, working_directory: str, manifest_hash: str
    ) -> RunRecord:
        """Submit a study to a configured remote target."""

        adapter = self._adapter_registry[adapter_id]
        issues = tuple(adapter.validate(request))
        if issues:
            raise ValueError(f"Run request failed validation: {issues}")

        target_ref = request.execution_profile.target_ref or "default"
        remote_client = self._remote_clients[target_ref]
        events: list[JobEvent] = [
            self._state_event(request.run_id, JobState.VALIDATING, "Validating remote run request."),
            self._state_event(
                request.run_id,
                JobState.PREPARED,
                f"Submitting run to remote target '{target_ref}'.",
            ),
        ]
        response = remote_client.submit(
            JobSubmissionRequest(
                adapter_id=adapter_id,
                profile_name=request.execution_profile.name,
                target_ref=target_ref,
                working_directory=working_directory,
                manifest_hash=manifest_hash,
                run_request=request,
            )
        )
        remote_run_id = response.remote_run_id or response.run_id
        remote_record = remote_client.run_record(remote_run_id)
        events.append(
            JobEvent(
                run_id=request.run_id,
                event_type=JobEventType.LOG,
                message=response.message or f"Remote job accepted by '{target_ref}'.",
                payload={"target_ref": target_ref, "remote_run_id": remote_run_id},
            )
        )
        events.extend(self._normalize_remote_events(remote_client.events(remote_run_id), request.run_id, remote_run_id))

        result = remote_client.result(remote_run_id)
        state = self._resolve_remote_state(response.state, remote_record)
        execution_mode = "remote-gateway"
        return_code = None
        remote_working_directory = working_directory
        if remote_record is not None:
            execution_mode = remote_record.execution_mode or execution_mode
            return_code = remote_record.return_code
            remote_working_directory = remote_record.working_directory or remote_working_directory

        prepared = PreparedCase(
            adapter_id=adapter_id,
            run_id=request.run_id,
            case_directory=working_directory,
            launch_command=(),
            artifact_manifest={"submission_transport": "remote", "target_ref": target_ref},
        )
        handle = JobHandle(
            run_id=request.run_id,
            adapter_id=adapter_id,
            state=state,
            native_identifier=remote_run_id,
        )
        submission = JobSubmission(request=request, handle=handle, result=result, events=events)
        self._submissions[request.run_id] = submission
        record = RunRecord(
            run_id=request.run_id,
            study_id=request.study.study_id,
            state=state,
            manifest_hash=manifest_hash,
            adapter_id=adapter_id,
            result_ref=result.result_ref if result is not None else response.result_ref,
            working_directory=remote_working_directory,
            execution_mode=execution_mode,
            return_code=return_code,
            target=request.execution_profile.target,
            target_ref=target_ref,
            remote_run_id=remote_run_id,
        )
        if self._run_store is not None:
            self._run_store.persist_run(
                run_id=request.run_id,
                request=request,
                prepared_case=prepared,
                run_record=record,
                result=result,
                events=events,
                execution_log=self._compose_remote_execution_log(
                    target_ref=target_ref,
                    remote_run_id=remote_run_id,
                    response=response,
                    remote_record=remote_record,
                ),
            )
        return record

    def events(self, run_id: str) -> tuple[JobEvent, ...]:
        """Return buffered events for a submitted run."""

        submission = self._submissions[run_id]
        return tuple(submission.events)

    def result(self, run_id: str) -> ResultSet:
        """Return the normalized result set for a submitted run."""

        submission = self._submissions[run_id]
        if submission.result is None:
            raise KeyError(f"No result recorded for run '{run_id}'.")
        return submission.result

    def state(self, run_id: str) -> JobState:
        """Return the current job state."""

        submission = self._submissions[run_id]
        if submission.handle is None:
            return JobState.DRAFT
        return submission.handle.state

    def run_directory(self, run_id: str) -> str | None:
        """Return the persisted directory for a run when file-backed storage is enabled."""

        if self._run_store is None:
            return None
        return self._run_store.run_directory(run_id)

    def record_path(self, run_id: str) -> str | None:
        """Return the persisted run-record path when file-backed storage is enabled."""

        if self._run_store is None:
            return None
        return self._run_store.record_path(run_id)

    def list_persisted_run_ids(self) -> tuple[str, ...]:
        """Return persisted run ids when file-backed storage is enabled."""

        if self._run_store is None:
            return ()
        return self._run_store.list_run_ids()

    def persisted_run_summaries(self) -> tuple[dict[str, object], ...]:
        """Return lightweight summaries for persisted runs."""

        if self._run_store is None:
            return ()
        return self._run_store.list_run_summaries()

    def persisted_run_record(self, run_id: str) -> dict[str, object] | None:
        """Return a persisted run record when file-backed storage is enabled."""

        if self._run_store is None:
            return None
        return self._run_store.load_run_record(run_id)

    def persisted_run_result(self, run_id: str) -> dict[str, object] | None:
        """Return a persisted run result when file-backed storage is enabled."""

        if self._run_store is None:
            return None
        return self._run_store.load_result(run_id)

    def persisted_run_events(self, run_id: str) -> list[dict[str, object]]:
        """Return persisted run events when file-backed storage is enabled."""

        if self._run_store is None:
            return []
        return self._run_store.load_events(run_id)

    def persisted_execution_log(self, run_id: str) -> str:
        """Return the persisted execution log when file-backed storage is enabled."""

        if self._run_store is None:
            return ""
        return self._run_store.load_execution_log(run_id)

    def create_support_bundle(self, run_id: str, output_path: str) -> str | None:
        """Create a support bundle for a persisted run when file-backed storage is enabled."""

        if self._run_store is None:
            return None
        return self._run_store.create_support_bundle(run_id, output_path)

    @staticmethod
    def _state_event(run_id: str, state: JobState, message: str) -> JobEvent:
        return JobEvent(
            run_id=run_id,
            event_type=JobEventType.STATE_CHANGED,
            message=message,
            state=state,
        )

    @staticmethod
    def _compose_execution_log(execution) -> str:
        sections = [f"execution_mode={execution.execution_mode}", f"return_code={execution.return_code}"]
        if execution.stdout:
            sections.append("stdout:")
            sections.append(execution.stdout.rstrip())
        if execution.stderr:
            sections.append("stderr:")
            sections.append(execution.stderr.rstrip())
        return "\n".join(sections) + "\n"

    @staticmethod
    def _compose_remote_execution_log(
        *,
        target_ref: str,
        remote_run_id: str,
        response,
        remote_record: RunRecord | None,
    ) -> str:
        sections = [
            "execution_mode=remote-gateway",
            f"target_ref={target_ref}",
            f"remote_run_id={remote_run_id}",
            f"accepted={response.accepted}",
            f"remote_state={response.state}",
        ]
        if remote_record is not None:
            sections.append(f"remote_execution_mode={remote_record.execution_mode or ''}")
            sections.append(f"remote_return_code={remote_record.return_code}")
            sections.append(f"remote_result_ref={remote_record.result_ref or ''}")
        if response.message:
            sections.append("message:")
            sections.append(response.message.rstrip())
        return "\n".join(sections) + "\n"

    @staticmethod
    def _normalize_remote_events(
        events: Sequence[JobEvent], local_run_id: str, remote_run_id: str
    ) -> tuple[JobEvent, ...]:
        normalized: list[JobEvent] = []
        for event in events:
            payload = dict(event.payload)
            payload.setdefault("remote_run_id", remote_run_id)
            normalized.append(
                JobEvent(
                    run_id=local_run_id,
                    event_type=event.event_type,
                    message=event.message,
                    state=event.state,
                    progress=event.progress,
                    payload=payload,
                )
            )
        return tuple(normalized)

    @staticmethod
    def _resolve_remote_state(state_value: str, remote_record: RunRecord | None) -> JobState:
        if remote_record is not None:
            return JobState(remote_record.state)
        return JobState(state_value)
