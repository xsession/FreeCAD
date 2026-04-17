# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""FCStd-linked sidecar serialization for canonical enterprise manifests."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any

from .serialization import to_primitive, to_sha256


def resolve_sidecar_path(
    *,
    project_id: str,
    fcstd_path: str | None,
    fallback_directory: str | None = None,
) -> str:
    """Return a deterministic sidecar path for a project manifest."""

    if fcstd_path:
        fcstd = Path(fcstd_path)
        return str(Path(f"{fcstd}.flowstudio.json"))

    base_dir = fallback_directory or os.getcwd()
    safe_project_id = project_id or "flowstudio-project"
    return str(Path(base_dir) / f"{safe_project_id}.flowstudio.json")


def build_sidecar_payload(
    *,
    manifest: Any,
    project_id: str,
    fcstd_path: str | None,
) -> dict[str, Any]:
    """Build canonical sidecar payload from a project manifest object."""

    return {
        "schema_version": "1.0.0",
        "artifact_type": "flowstudio.fcstd.sidecar",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_id": project_id,
        "fcstd_path": fcstd_path or "",
        "manifest_hash": to_sha256(manifest),
        "manifest": to_primitive(manifest),
    }


def write_sidecar_payload(payload: dict[str, Any], output_path: str) -> str:
    """Persist sidecar payload as stable UTF-8 JSON."""

    directory = os.path.dirname(output_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return output_path
