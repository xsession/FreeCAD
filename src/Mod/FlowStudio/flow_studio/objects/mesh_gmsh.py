# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""MeshGmsh – GMSH-based CFD mesh generation (like FloEFD auto-mesher)."""

from flow_studio.objects.base_object import BaseFlowObject


class MeshGmsh(BaseFlowObject):
    """CFD mesh using GMSH for volume meshing."""

    Type = "FlowStudio::MeshGmsh"

    def __init__(self, obj):
        super().__init__(obj)

        # Geometry reference
        obj.addProperty(
            "App::PropertyLink", "Part", "Mesh",
            "Reference to the shape to mesh"
        )

        # Element size
        obj.addProperty(
            "App::PropertyFloat", "CharacteristicLength", "Mesh",
            "Base characteristic mesh element size [mm]"
        )
        obj.CharacteristicLength = 10.0
        obj.addProperty(
            "App::PropertyFloat", "MinElementSize", "Mesh",
            "Minimum element size [mm]"
        )
        obj.MinElementSize = 1.0
        obj.addProperty(
            "App::PropertyFloat", "MaxElementSize", "Mesh",
            "Maximum element size [mm]"
        )
        obj.MaxElementSize = 50.0

        # Mesh algorithm
        obj.addProperty(
            "App::PropertyEnumeration", "Algorithm3D", "Mesh",
            "3D meshing algorithm"
        )
        obj.Algorithm3D = ["Delaunay", "Frontal", "HXT", "MMG3D"]
        obj.Algorithm3D = "Delaunay"

        # Element order
        obj.addProperty(
            "App::PropertyEnumeration", "ElementOrder", "Mesh",
            "Mesh element order"
        )
        obj.ElementOrder = ["1st Order", "2nd Order"]
        obj.ElementOrder = "1st Order"

        # Element type
        obj.addProperty(
            "App::PropertyEnumeration", "ElementType", "Mesh",
            "Volume element type"
        )
        obj.ElementType = ["Tetrahedral", "Hexahedral (structured)", "Polyhedral"]
        obj.ElementType = "Tetrahedral"

        # Mesh quality
        obj.addProperty(
            "App::PropertyFloat", "GrowthRate", "Mesh",
            "Element size growth rate from surfaces"
        )
        obj.GrowthRate = 1.3

        # Number of cells in gaps (FloEFD-like)
        obj.addProperty(
            "App::PropertyInteger", "CellsInGap", "Mesh",
            "Minimum number of cells across narrow gaps"
        )
        obj.CellsInGap = 3

        # Export format
        obj.addProperty(
            "App::PropertyEnumeration", "MeshFormat", "Mesh",
            "Output mesh format"
        )
        obj.MeshFormat = ["SU2 (.su2)", "OpenFOAM (polyMesh)", "GMSH (.msh)", "VTK (.vtk)", "STL (.stl)"]
        obj.MeshFormat = "SU2 (.su2)"

        # Path to generated mesh
        obj.addProperty(
            "App::PropertyPath", "MeshPath", "Output",
            "Path to generated mesh files"
        )

        # Stats
        obj.addProperty(
            "App::PropertyInteger", "NumCells", "Statistics",
            "Total number of volume cells"
        )
        obj.NumCells = 0
        obj.addProperty(
            "App::PropertyInteger", "NumFaces", "Statistics",
            "Total number of faces"
        )
        obj.NumFaces = 0
        obj.addProperty(
            "App::PropertyInteger", "NumPoints", "Statistics",
            "Total number of points"
        )
        obj.NumPoints = 0
