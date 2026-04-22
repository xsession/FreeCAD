# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Tests for enterprise bootstrap helpers and UI-facing endpoints."""

from flow_studio.enterprise.bootstrap import adapter_capability_matrix, is_enterprise_enabled


def test_is_enterprise_enabled_default_true():
    assert is_enterprise_enabled({}) is True


def test_is_enterprise_enabled_false_variants():
    for value in ("0", "false", "off", "no"):
        assert is_enterprise_enabled({"FLOWSTUDIO_ENTERPRISE_ENABLED": value}) is False


def test_adapter_capability_matrix_contains_core_adapters():
    matrix = adapter_capability_matrix()
    adapter_ids = {row["adapter_id"] for row in matrix}

    assert "openfoam.primary" in adapter_ids
    assert "elmer.primary" in adapter_ids
    assert "geant4.primary" in adapter_ids

    openfoam_row = next(row for row in matrix if row["adapter_id"] == "openfoam.primary")
    assert openfoam_row["commercial_core_safe"] is True
    assert openfoam_row["supports_parallel"] is True
    assert isinstance(openfoam_row["feature_flags"], dict)

    geant4_row = next(row for row in matrix if row["adapter_id"] == "geant4.primary")
    assert geant4_row["commercial_core_safe"] is True
    assert geant4_row["feature_flags"]["macro_generation"] is True
