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


def build_manifest_for_analysis(analysis_object: object, project_id: str):
    """Return a portable project manifest for a single legacy analysis."""

    return build_project_manifest(project_id=project_id, analyses=[analysis_object])


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
):
    """Build the submission request and deterministic manifest hash."""

    manifest = build_manifest_for_analysis(analysis_object, project_id=project_id)
    manifest_hash = to_sha256(manifest)
    request = LegacyExecutionRequest(
        analysis_object=analysis_object,
        run_id=run_id,
        working_directory=working_directory,
        manifest_hash=manifest_hash,
        requested_by=requested_by,
        reason=reason,
        execution_profile=execution_profile or runtime.default_profile,
    )
    adapter_id, run_request = runtime.legacy_execution.build_run_request(request)
    return adapter_id, run_request, request, manifest_hash


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
