# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Enterprise platform layer for the Flow Studio workbench."""

from .bootstrap import (
    adapter_capability_matrix,
    initialize_workbench,
    is_enterprise_enabled,
    on_workbench_activated,
)

__all__ = [
    "adapter_capability_matrix",
    "initialize_workbench",
    "is_enterprise_enabled",
    "on_workbench_activated",
]
