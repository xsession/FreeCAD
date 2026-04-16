# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Integration helpers between FreeCAD document objects and enterprise core."""

from .freecad_bridge import LegacyAnalysisBridge, build_project_manifest

__all__ = [
    "LegacyAnalysisBridge",
    "build_project_manifest",
]
