# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Enterprise platform layer for the Flow Studio workbench."""

from .bootstrap import initialize_workbench, on_workbench_activated

__all__ = [
    "initialize_workbench",
    "on_workbench_activated",
]
