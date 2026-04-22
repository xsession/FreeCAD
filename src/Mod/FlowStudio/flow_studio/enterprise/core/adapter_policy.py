# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Adapter policy, plugin stability, and compatibility tables.

This module centralizes policy so UI, orchestration, and CI can enforce:
- API stability guarantees for external adapter plugins
- Commercial-safety boundaries
- Version compatibility constraints
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from flow_studio.enterprise.core.domain import AdapterMetadata


PLUGIN_API_VERSION = "1.0"
PLUGIN_API_STABILITY = "stable"
PLUGIN_API_POLICY = (
    "Semantic versioning: minor versions are backward-compatible; major "
    "versions may introduce breaking changes with migration guides."
)


@dataclass(frozen=True)
class AdapterCompatibility:
    """Compatibility matrix row for one solver adapter."""

    adapter_id: str
    flow_studio_min: str
    flow_studio_max: str
    host_freecad_min: str
    host_freecad_max: str
    solver_versions: Sequence[str]
    notes: str = ""


COMPATIBILITY_MATRIX: Mapping[str, AdapterCompatibility] = {
    "openfoam.primary": AdapterCompatibility(
        adapter_id="openfoam.primary",
        flow_studio_min="1.0.0",
        flow_studio_max="1.x",
        host_freecad_min="0.21",
        host_freecad_max="1.99",
        solver_versions=("v2212", "v2306", "v2312"),
        notes="Primary production CFD backend.",
    ),
    "elmer.primary": AdapterCompatibility(
        adapter_id="elmer.primary",
        flow_studio_min="1.0.0",
        flow_studio_max="1.x",
        host_freecad_min="0.21",
        host_freecad_max="1.99",
        solver_versions=("9.0", "9.1"),
        notes="Primary multiphysics backend.",
    ),
    "geant4.primary": AdapterCompatibility(
        adapter_id="geant4.primary",
        flow_studio_min="1.0.0",
        flow_studio_max="1.x",
        host_freecad_min="0.21",
        host_freecad_max="1.99",
        solver_versions=("11.4", "11.4.1"),
        notes="Primary particle transport and radiation backend.",
    ),
    "fluidx3d.optional": AdapterCompatibility(
        adapter_id="fluidx3d.optional",
        flow_studio_min="1.0.0",
        flow_studio_max="1.x",
        host_freecad_min="0.21",
        host_freecad_max="1.99",
        solver_versions=("2.x",),
        notes=(
            "Optional and experimental. Non-commercial unless explicit commercial "
            "licensing is confirmed."
        ),
    ),
}


def validate_plugin_metadata(metadata: AdapterMetadata) -> tuple[str, ...]:
    """Validate adapter metadata against enterprise platform policy.

    Returns:
        Tuple of policy violations. Empty tuple means metadata passes baseline
        policy checks.
    """

    violations: list[str] = []

    if not metadata.adapter_id or "." not in metadata.adapter_id:
        violations.append("adapter_id must be namespaced (e.g. family.variant)")

    if not metadata.display_name:
        violations.append("display_name is required")

    if not metadata.version:
        violations.append("adapter version is required")

    if metadata.adapter_id == "fluidx3d.optional" and metadata.commercial_core_safe:
        violations.append(
            "fluidx3d.optional must not be marked commercial_core_safe=True"
        )

    if metadata.adapter_id in COMPATIBILITY_MATRIX:
        row = COMPATIBILITY_MATRIX[metadata.adapter_id]
        if tuple(metadata.supported_solver_versions) != tuple(row.solver_versions):
            violations.append(
                "supported_solver_versions does not match compatibility matrix"
            )

    return tuple(violations)
