# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Unit tests for enterprise adapter matrix helper logic."""

from flow_studio.enterprise.ui.adapter_matrix import (
    ADAPTER_MATRIX_CSV_FIELDNAMES,
    collect_families,
    filter_rows,
    matrix_to_json,
    to_csv_row,
)


def _rows():
    return [
        {
            "adapter_id": "openfoam.primary",
            "display_name": "OpenFOAM",
            "family": "openfoam",
            "version": "0.1.0",
            "commercial_core_safe": True,
            "supports_gpu": False,
            "supports_remote": True,
            "supports_parallel": True,
            "supports_transient": True,
            "supported_physics": ("cfd.internal", "cht"),
            "supported_solver_versions": ("v2312",),
            "feature_flags": {"function_objects": True},
            "notes": "primary",
            "experimental": False,
        },
        {
            "adapter_id": "fluidx3d.optional",
            "display_name": "FluidX3D (Optional)",
            "family": "fluidx3d",
            "version": "0.1.0",
            "commercial_core_safe": False,
            "supports_gpu": True,
            "supports_remote": False,
            "supports_parallel": False,
            "supports_transient": True,
            "supported_physics": ("cfd.incompressible.exploratory",),
            "supported_solver_versions": ("2.x",),
            "feature_flags": {"optional_adapter": True},
            "notes": "optional",
            "experimental": True,
        },
    ]


def test_collect_families_returns_sorted_unique_non_empty():
    rows = _rows() + [{"family": "openfoam"}, {"family": ""}]
    assert collect_families(rows) == ["fluidx3d", "openfoam"]


def test_filter_rows_by_family_and_capability():
    rows = _rows()
    by_family = filter_rows(rows, family_filter="openfoam")
    assert len(by_family) == 1
    assert by_family[0]["adapter_id"] == "openfoam.primary"

    by_gpu = filter_rows(rows, capability_filter="supports_gpu")
    assert len(by_gpu) == 1
    assert by_gpu[0]["adapter_id"] == "fluidx3d.optional"


def test_filter_rows_by_text_matches_tokens_case_insensitive():
    rows = _rows()
    assert filter_rows(rows, text_filter="optional_adapter")[0]["adapter_id"] == "fluidx3d.optional"
    assert filter_rows(rows, text_filter="CHT")[0]["adapter_id"] == "openfoam.primary"


def test_matrix_to_json_stable_keys():
    payload = matrix_to_json(_rows())
    assert '"adapter_id": "openfoam.primary"' in payload
    assert '"adapter_id": "fluidx3d.optional"' in payload


def test_to_csv_row_normalizes_collections_to_json_strings():
    row = to_csv_row(_rows()[0])
    assert tuple(ADAPTER_MATRIX_CSV_FIELDNAMES) == tuple(row.keys())
    assert row["supported_solver_versions"].startswith("[")
    assert row["feature_flags"].startswith("{")
