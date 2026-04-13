# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""FlowStudio import/export for .foam, .vtk, .stl result files.

FreeCAD requires ``open(filename)`` and optionally ``insert(filename, docname)``
functions for registered import types.
"""

import os
import FreeCAD


# ---- FreeCAD import entry points ----

def open(filename):
    """Entry point called by FreeCAD when opening a .foam / .vtk file."""
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".foam":
        return open_foam_case(filename)
    elif ext in (".vtk", ".vtu", ".vtp"):
        return open_vtk_file(filename)
    else:
        FreeCAD.Console.PrintWarning(
            f"FlowStudio: Unsupported import format '{ext}'\n"
        )


def insert(filename, docname=None):
    """Insert results into an existing document."""
    if docname:
        doc = FreeCAD.getDocument(docname)
    else:
        doc = FreeCAD.ActiveDocument
    return open(filename)


def open_foam_case(filename):
    """Open an OpenFOAM .foam file – creates a PostPipeline."""
    doc = FreeCAD.ActiveDocument
    if doc is None:
        doc = FreeCAD.newDocument("CFDResult")

    from flow_studio.ObjectsFlowStudio import makePostPipeline
    obj = makePostPipeline(doc)
    obj.ResultFile = filename
    obj.ResultFormat = "OpenFOAM"
    doc.recompute()
    return obj


def open_vtk_file(filename):
    """Import a VTK result file."""
    doc = FreeCAD.ActiveDocument
    if doc is None:
        doc = FreeCAD.newDocument("CFDResult")

    from flow_studio.ObjectsFlowStudio import makePostPipeline
    obj = makePostPipeline(doc)
    obj.ResultFile = filename
    obj.ResultFormat = "VTK"
    doc.recompute()
    return obj


def export_stl(objects, filename):
    """Export FreeCAD shapes to binary STL for FluidX3D."""
    import Mesh
    meshes = []
    for obj in objects:
        if hasattr(obj, "Shape"):
            meshes.append(Mesh.Mesh(obj.Shape.tessellate(0.1)))
    if meshes:
        combined = meshes[0]
        for m in meshes[1:]:
            combined.addMesh(m)
        combined.write(filename)
        FreeCAD.Console.PrintMessage(
            f"FlowStudio: Exported STL -> {filename}\n"
        )
