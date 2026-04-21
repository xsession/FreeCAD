# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Pure helper utilities for adapter capability matrix UI logic.

This module intentionally has no FreeCAD/Qt dependencies so behavior can be
unit tested in regular Python test runs.
"""

from __future__ import annotations

import json
from typing import Any, Iterable

from flow_studio.enterprise.adapters import ElmerSolverAdapter, OpenFOAMSolverAdapter

try:
    from flow_studio.enterprise.adapters import FluidX3DOptionalAdapter
except Exception:  # pragma: no cover - optional adapter may be unavailable
    FluidX3DOptionalAdapter = None


ADAPTER_MATRIX_CSV_FIELDNAMES = (
    "adapter_id",
    "display_name",
    "family",
    "version",
    "commercial_core_safe",
    "experimental",
    "supports_gpu",
    "supports_remote",
    "supports_parallel",
    "supports_transient",
    "supported_solver_versions",
    "supported_physics",
    "feature_flags",
    "notes",
)


def collect_families(rows: Iterable[dict[str, Any]]) -> list[str]:
    """Return sorted, unique non-empty families from adapter rows."""

    return sorted(
        {
            str(adapter.get("family", ""))
            for adapter in rows
            if str(adapter.get("family", ""))
        }
    )


def filter_rows(
    rows: Iterable[dict[str, Any]],
    *,
    text_filter: str = "",
    family_filter: str = "",
    capability_filter: str = "",
) -> list[dict[str, Any]]:
    """Filter matrix rows using text/family/capability constraints."""

    text_filter = text_filter.strip().lower()
    family_filter = family_filter.strip()
    capability_filter = capability_filter.strip()

    filtered: list[dict[str, Any]] = []
    for adapter in rows:
        if family_filter and str(adapter.get("family", "")) != family_filter:
            continue
        if capability_filter and not bool(adapter.get(capability_filter, False)):
            continue

        if text_filter:
            tokens = [
                str(adapter.get("adapter_id", "")),
                str(adapter.get("display_name", "")),
                str(adapter.get("family", "")),
                json.dumps(adapter.get("feature_flags", {}), sort_keys=True),
                json.dumps(adapter.get("supported_physics", ())),
            ]
            if text_filter not in " ".join(tokens).lower():
                continue

        filtered.append(adapter)
    return filtered


def matrix_to_json(rows: Iterable[dict[str, Any]]) -> str:
    """Serialize matrix rows to deterministic JSON for clipboard/export use."""

    return json.dumps(list(rows), indent=2, sort_keys=True)


def to_csv_row(adapter: dict[str, Any]) -> dict[str, Any]:
    """Normalize one adapter row into CSV-friendly scalar values."""

    return {
        "adapter_id": adapter.get("adapter_id", ""),
        "display_name": adapter.get("display_name", ""),
        "family": adapter.get("family", ""),
        "version": adapter.get("version", ""),
        "commercial_core_safe": adapter.get("commercial_core_safe", False),
        "experimental": adapter.get("experimental", False),
        "supports_gpu": adapter.get("supports_gpu", False),
        "supports_remote": adapter.get("supports_remote", False),
        "supports_parallel": adapter.get("supports_parallel", False),
        "supports_transient": adapter.get("supports_transient", False),
        "supported_solver_versions": json.dumps(adapter.get("supported_solver_versions", ())),
        "supported_physics": json.dumps(adapter.get("supported_physics", ())),
        "feature_flags": json.dumps(adapter.get("feature_flags", {}), sort_keys=True),
        "notes": adapter.get("notes", ""),
    }


def build_capability_rows() -> list[dict[str, Any]]:
    """Build normalized adapter rows for UI display and compatibility tests."""

    adapter_types = [OpenFOAMSolverAdapter, ElmerSolverAdapter]
    if FluidX3DOptionalAdapter is not None:
        adapter_types.append(FluidX3DOptionalAdapter)

    rows: list[dict[str, Any]] = []
    for adapter_type in adapter_types:
        adapter = adapter_type()
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
                "supports_gpu": capabilities.supports_gpu,
                "supports_remote": capabilities.supports_remote,
                "supports_parallel": capabilities.supports_parallel,
                "supports_transient": capabilities.supports_transient,
                "supported_solver_versions": tuple(metadata.supported_solver_versions),
                "supported_physics": tuple(capabilities.supported_physics),
                "feature_flags": dict(capabilities.feature_flags),
                "notes": metadata.notes,
            }
        )
    return rows
