# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Qt-facing enterprise UI helpers."""

from .adapter_matrix import (
    ADAPTER_MATRIX_CSV_FIELDNAMES,
    collect_families,
    filter_rows,
    matrix_to_json,
    to_csv_row,
)

try:
    from .jobs_panel import EnterpriseJobsPanel
except Exception:  # pragma: no cover - optional in headless contexts
    EnterpriseJobsPanel = None

__all__ = [
    "ADAPTER_MATRIX_CSV_FIELDNAMES",
    "EnterpriseJobsPanel",
    "collect_families",
    "filter_rows",
    "matrix_to_json",
    "to_csv_row",
]
