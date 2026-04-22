# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""High-level actions for working with legacy Flow Studio analyses."""

from __future__ import annotations

import os
from typing import Any

from flow_studio.enterprise.core.sidecar import (
    build_sidecar_payload,
    resolve_sidecar_path,
    write_sidecar_payload,
)
from flow_studio.enterprise.core.serialization import to_json, to_sha256
from flow_studio.enterprise.integration.freecad_bridge import build_project_manifest
from flow_studio.enterprise.services.execution_facade import LegacyExecutionRequest


def _solver_object(analysis_object: object):
    for child in tuple(getattr(analysis_object, "Group", ()) or ()):
        if getattr(child, "FlowType", "") == "FlowStudio::Solver":
            return child
    return None


def _primary_solver_backend(analysis_object: object) -> str:
    solver_object = _solver_object(analysis_object)
    if solver_object is not None:
        backend = str(getattr(solver_object, "SolverBackend", "") or "").strip()
        if backend:
            return backend
    return str(getattr(analysis_object, "SolverBackend", "OpenFOAM") or "OpenFOAM")


def _selected_multi_solver_backends(analysis_object: object) -> tuple[str, ...]:
    solver_object = _solver_object(analysis_object)
    primary_backend = _primary_solver_backend(analysis_object)
    if solver_object is None or not bool(getattr(solver_object, "MultiSolverEnabled", False)):
        return (primary_backend,)

    raw_backends = getattr(solver_object, "MultiSolverBackends", ()) or ()
    if isinstance(raw_backends, str):
        candidates = [item.strip() for item in raw_backends.split(",")]
    else:
        candidates = [str(item).strip() for item in raw_backends]
    backends = tuple(dict.fromkeys(item for item in candidates if item))
    if len(backends) < 2:
        raise ValueError("Multi-solver mode requires at least two selected backends.")
    if primary_backend not in backends:
        raise ValueError("The primary solver backend must also be selected for multi-solver execution.")
    return backends


def _backend_slug(backend: str) -> str:
    return backend.strip().lower().replace(" ", "-")


def build_manifest_for_analysis(
    analysis_object: object,
    project_id: str,
    solver_backend_override: str | None = None,
):
    """Return a portable project manifest for a single legacy analysis."""

    return build_project_manifest(
        project_id=project_id,
        analyses=[analysis_object],
        solver_backend_overrides=[solver_backend_override],
    )


def export_analysis_manifest(analysis_object: object, project_id: str, output_path: str) -> str:
    """Serialize and write a single-analysis manifest to disk."""

    manifest = build_manifest_for_analysis(analysis_object, project_id=project_id)
    directory = os.path.dirname(output_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(to_json(manifest))
        handle.write("\n")
    return output_path


def export_fcstd_sidecar(
    *,
    analysis_object: object,
    project_id: str,
    fcstd_path: str | None,
    fallback_directory: str | None = None,
    output_path: str | None = None,
) -> str:
    """Export canonical sidecar JSON linked to an FCStd document path."""

    manifest = build_manifest_for_analysis(analysis_object, project_id=project_id)
    payload = build_sidecar_payload(
        manifest=manifest,
        project_id=project_id,
        fcstd_path=fcstd_path,
    )
    sidecar_path = output_path or resolve_sidecar_path(
        project_id=project_id,
        fcstd_path=fcstd_path,
        fallback_directory=fallback_directory,
    )
    return write_sidecar_payload(payload, sidecar_path)


def prepare_runtime_submission(
    *,
    runtime: Any,
    analysis_object: object,
    project_id: str,
    run_id: str,
    working_directory: str,
    requested_by: str = "freecad-ui",
    reason: str = "interactive-submit",
    execution_profile: Any | None = None,
    solver_backend_override: str | None = None,
):
    """Build the submission request and deterministic manifest hash."""

    manifest = build_manifest_for_analysis(
        analysis_object,
        project_id=project_id,
        solver_backend_override=solver_backend_override,
    )
    manifest_hash = to_sha256(manifest)
    request = LegacyExecutionRequest(
        analysis_object=analysis_object,
        run_id=run_id,
        working_directory=working_directory,
        manifest_hash=manifest_hash,
        requested_by=requested_by,
        reason=reason,
        execution_profile=execution_profile or runtime.default_profile,
        solver_backend_override=solver_backend_override,
    )
    adapter_id, run_request = runtime.legacy_execution.build_run_request(request)
    return adapter_id, run_request, request, manifest_hash


def prepare_runtime_submissions(
    *,
    runtime: Any,
    analysis_object: object,
    project_id: str,
    run_id: str,
    working_directory: str,
    requested_by: str = "freecad-ui",
    reason: str = "interactive-submit",
    execution_profile: Any | None = None,
):
    """Build one or more enterprise submission requests for the selected solver plan."""

    backends = _selected_multi_solver_backends(analysis_object)
    submissions = []
    multi_solver = len(backends) > 1
    for backend in backends:
        backend_slug = _backend_slug(backend)
        submission_run_id = run_id if not multi_solver else f"{run_id}-{backend_slug}"
        submission_directory = (
            working_directory if not multi_solver else os.path.join(working_directory, backend_slug)
        )
        adapter_id, run_request, request, manifest_hash = prepare_runtime_submission(
            runtime=runtime,
            analysis_object=analysis_object,
            project_id=project_id,
            run_id=submission_run_id,
            working_directory=submission_directory,
            requested_by=requested_by,
            reason=reason,
            execution_profile=execution_profile,
            solver_backend_override=backend,
        )
        submissions.append((backend, adapter_id, run_request, request, manifest_hash))
    return tuple(submissions)


def submit_analysis_to_runtime(
    *,
    runtime: Any,
    analysis_object: object,
    project_id: str,
    run_id: str,
    working_directory: str,
    requested_by: str = "freecad-ui",
    reason: str = "interactive-submit",
    execution_profile: Any | None = None,
):
    """Build a deterministic manifest hash and submit a legacy analysis."""

    _, _, request, manifest_hash = prepare_runtime_submission(
        runtime=runtime,
        analysis_object=analysis_object,
        project_id=project_id,
        run_id=run_id,
        working_directory=working_directory,
        requested_by=requested_by,
        reason=reason,
        execution_profile=execution_profile,
    )
    record = runtime.legacy_execution.submit(request)
    return record, manifest_hash


def submit_analysis_to_runtime_batch(
    *,
    runtime: Any,
    analysis_object: object,
    project_id: str,
    run_id: str,
    working_directory: str,
    requested_by: str = "freecad-ui",
    reason: str = "interactive-submit",
    execution_profile: Any | None = None,
):
    """Submit one or more runtime requests, concurrently when multi-solver mode is enabled."""

    submissions = prepare_runtime_submissions(
        runtime=runtime,
        analysis_object=analysis_object,
        project_id=project_id,
        run_id=run_id,
        working_directory=working_directory,
        requested_by=requested_by,
        reason=reason,
        execution_profile=execution_profile,
    )
    records = runtime.legacy_execution.submit_many(tuple(item[3] for item in submissions))
    return tuple(
        (submissions[index][0], record, submissions[index][4])
        for index, record in enumerate(records)
    )
