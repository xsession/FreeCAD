# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Task panel for Solver settings – multi-solver configuration."""

import FreeCAD
from PySide import QtGui
from flow_studio.taskpanels.base_taskpanel import BaseTaskPanel


class TaskSolver(BaseTaskPanel):

    def _build_form(self):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)
        layout.addWidget(QtGui.QLabel("<b>Solver Configuration</b>"))

        # Backend
        self.cb_backend = self._combo(
            ["OpenFOAM", "Elmer", "FluidX3D", "SU2"], self.obj.SolverBackend
        )
        self._add_row(layout, "Solver Backend:", self.cb_backend)
        self.cb_backend.currentTextChanged.connect(self._on_backend_changed)

        # --- Stacked pages per solver ---
        self.stack = QtGui.QStackedWidget()

        # OpenFOAM page
        of_page = QtGui.QWidget()
        of_layout = QtGui.QVBoxLayout(of_page)
        self.cb_of_solver = self._combo(
            ["simpleFoam", "pimpleFoam", "pisoFoam", "icoFoam",
             "rhoSimpleFoam", "rhoPimpleFoam", "buoyantSimpleFoam",
             "buoyantPimpleFoam", "interFoam", "potentialFoam"],
            self.obj.OpenFOAMSolver,
        )
        self._add_row(of_layout, "Application:", self.cb_of_solver)
        self.sp_iter = self._spin_int(self.obj.MaxIterations, 1, 999999)
        self._add_row(of_layout, "Max Iterations:", self.sp_iter)
        self.sp_tol = self._spin_float(self.obj.ConvergenceTolerance, 1e-12, 1, 8, 1e-5)
        self._add_row(of_layout, "Convergence Tol:", self.sp_tol)
        self.sp_nproc = self._spin_int(self.obj.NumProcessors, 1, 1024)
        self._add_row(of_layout, "Num. Processors:", self.sp_nproc)
        self.cb_conv = self._combo(
            ["linearUpwind", "upwind", "linear", "limitedLinear", "LUST"],
            self.obj.ConvectionScheme,
        )
        self._add_row(of_layout, "Convection Scheme:", self.cb_conv)
        of_layout.addStretch()
        self.stack.addWidget(of_page)

        # Elmer page
        elmer_page = QtGui.QWidget()
        elmer_layout = QtGui.QVBoxLayout(elmer_page)
        self.cb_elmer_solver = self._combo(
            ["ElmerSolver", "ElmerSolver_mpi"],
            getattr(self.obj, "ElmerSolverBinary", "ElmerSolver"),
        )
        self._add_row(elmer_layout, "Executable:", self.cb_elmer_solver)
        self.sp_elmer_nproc = self._spin_int(self.obj.NumProcessors, 1, 1024)
        self._add_row(elmer_layout, "Num. Processors:", self.sp_elmer_nproc)
        elmer_layout.addWidget(
            QtGui.QLabel(
                "FlowStudio runs Elmer through the CLI solver binary only. "
                "ElmerGUI is not used for execution."
            )
        )
        elmer_layout.addStretch()
        self.stack.addWidget(elmer_page)

        # FluidX3D page
        fx_page = QtGui.QWidget()
        fx_layout = QtGui.QVBoxLayout(fx_page)
        self.cb_fx_prec = self._combo(
            ["FP32/FP32", "FP32/FP16S", "FP32/FP16C"], self.obj.FluidX3DPrecision
        )
        self._add_row(fx_layout, "Precision:", self.cb_fx_prec)
        self.sp_fx_res = self._spin_int(self.obj.FluidX3DResolution, 16, 4096)
        self._add_row(fx_layout, "Resolution:", self.sp_fx_res)
        self.sp_fx_steps = self._spin_int(self.obj.FluidX3DTimeSteps, 100, 99999999)
        self._add_row(fx_layout, "Time Steps:", self.sp_fx_steps)
        self.sp_fx_vram = self._spin_int(self.obj.FluidX3DVRAM, 100, 100000)
        self._add_row(fx_layout, "VRAM [MB]:", self.sp_fx_vram)
        self.chk_multigpu = self._checkbox(self.obj.FluidX3DMultiGPU)
        self._add_row(fx_layout, "Multi-GPU:", self.chk_multigpu)
        self.sp_ngpu = self._spin_int(self.obj.FluidX3DNumGPUs, 1, 16)
        self._add_row(fx_layout, "Num GPUs:", self.sp_ngpu)
        fx_layout.addStretch()
        self.stack.addWidget(fx_page)

        # SU2 placeholder
        su2_page = QtGui.QWidget()
        su2_layout = QtGui.QVBoxLayout(su2_page)
        su2_layout.addWidget(QtGui.QLabel("SU2 solver support – coming soon"))
        su2_layout.addStretch()
        self.stack.addWidget(su2_page)

        layout.addWidget(self.stack)
        self._on_backend_changed(self.cb_backend.currentText())

        layout.addStretch()
        return widget

    def _on_backend_changed(self, text):
        idx = {"OpenFOAM": 0, "Elmer": 1, "FluidX3D": 2, "SU2": 3}.get(text, 0)
        self.stack.setCurrentIndex(idx)

    def _store(self):
        self.obj.SolverBackend = self.cb_backend.currentText()
        # OpenFOAM
        self.obj.OpenFOAMSolver = self.cb_of_solver.currentText()
        self.obj.MaxIterations = self.sp_iter.value()
        self.obj.ConvergenceTolerance = self.sp_tol.value()
        self.obj.NumProcessors = self.sp_nproc.value()
        self.obj.ConvectionScheme = self.cb_conv.currentText()
        # Elmer
        self.obj.ElmerSolverBinary = self.cb_elmer_solver.currentText()
        if self.cb_backend.currentText() == "Elmer":
            self.obj.NumProcessors = self.sp_elmer_nproc.value()
        # FluidX3D
        self.obj.FluidX3DPrecision = self.cb_fx_prec.currentText()
        self.obj.FluidX3DResolution = self.sp_fx_res.value()
        self.obj.FluidX3DTimeSteps = self.sp_fx_steps.value()
        self.obj.FluidX3DVRAM = self.sp_fx_vram.value()
        self.obj.FluidX3DMultiGPU = self.chk_multigpu.isChecked()
        self.obj.FluidX3DNumGPUs = self.sp_ngpu.value()
