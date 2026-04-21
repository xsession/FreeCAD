# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""FlowStudio – Multi-Physics Simulation Workbench.

The package keeps the historical flat module surface for FreeCAD startup and
macro compatibility, while newer code can use grouped namespaces:

- ``flow_studio.api`` for object factories
- ``flow_studio.catalog`` for engineering database access
- ``flow_studio.core`` for workflow and domain helpers
- ``flow_studio.runtime`` for dependency and installer tooling
- ``flow_studio.tools`` for geometry-oriented helpers
- ``flow_studio.ui`` for workspace layout metadata
- ``flow_studio.workflows`` for guided workflow profiles
"""

__version__ = "0.2.0"

__all__ = [
	"__version__",
]
