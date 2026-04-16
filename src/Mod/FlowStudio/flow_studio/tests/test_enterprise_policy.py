# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Policy and compatibility tests for enterprise adapter governance."""

from flow_studio.enterprise.adapters.fluidx3d import FluidX3DOptionalAdapter
from flow_studio.enterprise.core.adapter_policy import (
    COMPATIBILITY_MATRIX,
    PLUGIN_API_STABILITY,
    PLUGIN_API_VERSION,
    validate_plugin_metadata,
)


def test_plugin_api_version_is_declared():
    assert PLUGIN_API_VERSION
    assert PLUGIN_API_STABILITY in {"stable", "experimental"}


def test_compatibility_matrix_contains_core_adapters():
    assert "openfoam.primary" in COMPATIBILITY_MATRIX
    assert "elmer.primary" in COMPATIBILITY_MATRIX


def test_fluidx3d_policy_enforces_non_commercial_flag():
    metadata = FluidX3DOptionalAdapter().metadata()
    assert metadata.commercial_core_safe is False

    violations = validate_plugin_metadata(metadata)
    assert not violations
