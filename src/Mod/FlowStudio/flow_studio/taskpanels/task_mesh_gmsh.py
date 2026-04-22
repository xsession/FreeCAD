# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Task panel for GMSH mesh generation."""

import FreeCAD
from PySide import QtGui
from flow_studio.taskpanels.base_taskpanel import BaseTaskPanel


class TaskMeshGmsh(BaseTaskPanel):

    SUMMARY_TITLE = "Mesh Generation"
    SUMMARY_DETAIL = (
        "Define the mesh sizing, algorithm, and export format used to discretize {label}."
    )

    def _build_task_validation(self):
        min_size = float(getattr(self.obj, "MinElementSize", 0.0))
        max_size = float(getattr(self.obj, "MaxElementSize", 0.0))
        base_size = float(getattr(self.obj, "CharacteristicLength", 0.0))

        if base_size <= 0.0:
            return (
                "error",
                "Base mesh size must be positive",
                "Set a positive base size before generating the mesh.",
            )

        if min_size > max_size:
            return (
                "warning",
                "Minimum size exceeds maximum size",
                "Reduce the minimum element size or increase the maximum element size before meshing.",
            )

        return super()._build_task_validation()

    def _build_form(self):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)
        layout.addWidget(QtGui.QLabel("<b>CFD Mesh Settings (GMSH)</b>"))

        sizing = self._section(layout, "Sizing")
        self.sp_char = self._spin_float(self.obj.CharacteristicLength, 0.01, 10000, 2, 1)
        self._add_row(sizing, "Base Size [mm]:", self.sp_char)

        self.sp_min = self._spin_float(self.obj.MinElementSize, 0.001, 10000, 3, 0.1)
        self._add_row(sizing, "Min Size [mm]:", self.sp_min)

        self.sp_max = self._spin_float(self.obj.MaxElementSize, 0.01, 100000, 2, 10)
        self._add_row(sizing, "Max Size [mm]:", self.sp_max)

        controls = self._section(layout, "Mesh Controls")

        self.cb_algo = self._combo(
            ["Delaunay", "Frontal", "HXT", "MMG3D"], self.obj.Algorithm3D
        )
        self._add_row(controls, "Algorithm:", self.cb_algo)

        self.cb_order = self._combo(
            ["1st Order", "2nd Order"], self.obj.ElementOrder
        )
        self._add_row(controls, "Element Order:", self.cb_order)

        self.cb_type = self._combo(
            ["Tetrahedral", "Hexahedral (structured)", "Polyhedral"],
            self.obj.ElementType,
        )
        self._add_row(controls, "Element Type:", self.cb_type)

        self.sp_growth = self._spin_float(self.obj.GrowthRate, 1.0, 3.0, 2, 0.1)
        self._add_row(controls, "Growth Rate:", self.sp_growth)

        self.sp_gap = self._spin_int(self.obj.CellsInGap, 1, 20)
        self._add_row(controls, "Cells in Gap:", self.sp_gap)

        output = self._section(layout, "Output")

        self.cb_format = self._combo(
            ["SU2 (.su2)", "OpenFOAM (polyMesh)", "GMSH (.msh)", "VTK (.vtk)", "STL (.stl)"],
            self.obj.MeshFormat,
        )
        self._add_row(output, "Output Format:", self.cb_format)

        actions = self._section(layout, "Actions")
        btn_run = QtGui.QPushButton("Generate Mesh")
        btn_run.clicked.connect(self._run_mesh)
        actions.addWidget(btn_run)

        self.lbl_stats = QtGui.QLabel(f"Cells: {self.obj.NumCells}")
        actions.addWidget(self.lbl_stats)

        layout.addStretch()
        return widget

    def _run_mesh(self):
        """Trigger mesh generation (placeholder – actual GMSH call)."""
        FreeCAD.Console.PrintMessage(
            "FlowStudio: Mesh generation triggered (GMSH integration pending)\n"
        )

    def _store(self):
        self.obj.CharacteristicLength = self.sp_char.value()
        self.obj.MinElementSize = self.sp_min.value()
        self.obj.MaxElementSize = self.sp_max.value()
        self.obj.Algorithm3D = self.cb_algo.currentText()
        self.obj.ElementOrder = self.cb_order.currentText()
        self.obj.ElementType = self.cb_type.currentText()
        self.obj.GrowthRate = self.sp_growth.value()
        self.obj.CellsInGap = self.sp_gap.value()
        self.obj.MeshFormat = self.cb_format.currentText()
