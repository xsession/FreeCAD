# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""FlowStudio – Multi-Physics Simulation Workbench.

The grouped namespaces below are the canonical architecture surface for new
code. Historical flat modules remain as compatibility shims for FreeCAD startup
and macro compatibility:

- ``flow_studio.api`` for object factories
- ``flow_studio.app`` for application services and frontend-neutral use cases
- ``flow_studio.catalog`` for engineering database access
- ``flow_studio.core`` for workflow and domain helpers
- ``flow_studio.runtime`` for dependency and installer tooling
- ``flow_studio.tools`` for geometry-oriented helpers
- ``flow_studio.ui`` for presenters, view-state helpers, and workspace layout metadata
- ``flow_studio.workflows`` for guided workflow profiles
"""

__version__ = "0.2.0"

__all__ = [
	"__version__",
]
