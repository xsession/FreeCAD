# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Task panel for Solver settings – multi-solver configuration."""

from PySide import QtGui
from flow_studio.taskpanels.base_taskpanel import BaseTaskPanel
from flow_studio.ui.solver_presenter import SolverPresenter


class TaskSolver(BaseTaskPanel):

    SUMMARY_TITLE = "Solver Configuration"
    SUMMARY_DETAIL = (
        "Choose the backend, numerical controls, and execution settings for {label}."
    )

    def __init__(self, obj):
        self._presenter = SolverPresenter()
        super().__init__(obj)

    def _build_task_validation(self):
        level, title, detail = self._presenter.build_validation(self._current_settings())
        if level or title or detail:
            return level, title, detail
        return super()._build_task_validation()

    def _build_form(self):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)
        layout.addWidget(QtGui.QLabel("<b>Solver Configuration</b>"))

        # Backend
        self.cb_backend = self._combo(
            ["OpenFOAM", "Elmer", "FluidX3D", "SU2", "Geant4"], self.obj.SolverBackend
        )
        self._add_row(layout, "Solver Backend:", self.cb_backend)
        self.cb_backend.currentTextChanged.connect(self._on_backend_changed)

        self.chk_multi_solver = self._checkbox(getattr(self.obj, "MultiSolverEnabled", False))
        self.chk_multi_solver.setText("Enable simultaneous multi-solver enterprise submission")
        layout.addWidget(self.chk_multi_solver)

        multi_solver_group = QtGui.QGroupBox("Parallel Multi-Solver Backends")
        multi_solver_layout = QtGui.QVBoxLayout(multi_solver_group)
        selected_multi_backends = set(
            self._presenter.normalized_multi_solver_backends(getattr(self.obj, "MultiSolverBackends", ()))
        )
        self.chk_multi_openfoam = QtGui.QCheckBox("OpenFOAM")
        self.chk_multi_openfoam.setChecked("OpenFOAM" in selected_multi_backends)
        multi_solver_layout.addWidget(self.chk_multi_openfoam)
        self.chk_multi_elmer = QtGui.QCheckBox("Elmer")
        self.chk_multi_elmer.setChecked("Elmer" in selected_multi_backends)
        multi_solver_layout.addWidget(self.chk_multi_elmer)
        self.chk_multi_fluidx3d = QtGui.QCheckBox("FluidX3D")
        self.chk_multi_fluidx3d.setChecked("FluidX3D" in selected_multi_backends)
        multi_solver_layout.addWidget(self.chk_multi_fluidx3d)
        self.chk_multi_geant4 = QtGui.QCheckBox("Geant4")
        self.chk_multi_geant4.setChecked("Geant4" in selected_multi_backends)
        multi_solver_layout.addWidget(self.chk_multi_geant4)
        multi_solver_group.setEnabled(self.chk_multi_solver.isChecked())
        self.chk_multi_solver.toggled.connect(multi_solver_group.setEnabled)
        layout.addWidget(multi_solver_group)

        runtime_group = QtGui.QGroupBox("Runtime Thresholds")
        runtime_layout = QtGui.QVBoxLayout(runtime_group)
        self.sp_runtime_soft = self._spin_int(
            int(getattr(self.obj, "SoftRuntimeWarningSeconds", 0) or 0), 0, 604800
        )
        self._add_row(runtime_layout, "Soft Warning [s]:", self.sp_runtime_soft)
        self.sp_runtime_max = self._spin_int(
            int(getattr(self.obj, "MaxRuntimeSeconds", 0) or 0), 0, 604800
        )
        self._add_row(runtime_layout, "Hard Limit [s]:", self.sp_runtime_max)
        self.sp_runtime_stall = self._spin_int(
            int(getattr(self.obj, "StallTimeoutSeconds", 0) or 0), 0, 604800
        )
        self._add_row(runtime_layout, "Stall Timeout [s]:", self.sp_runtime_stall)
        self.sp_runtime_progress = self._spin_float(
            float(getattr(self.obj, "MinProgressPercent", 0.0) or 0.0), 0.0, 100.0, 2, 0.5
        )
        self._add_row(runtime_layout, "Min Progress [%]:", self.sp_runtime_progress)
        self.chk_abort_threshold = self._checkbox(getattr(self.obj, "AbortOnThreshold", True))
        self._add_row(runtime_layout, "Abort On Threshold:", self.chk_abort_threshold)
        layout.addWidget(runtime_group)

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

        # Geant4 page
        geant4_page = QtGui.QWidget()
        geant4_layout = QtGui.QVBoxLayout(geant4_page)
        self.le_g4_exe = QtGui.QLineEdit(getattr(self.obj, "Geant4Executable", ""))
        self._add_row(geant4_layout, "Executable:", self.le_g4_exe)
        self.le_g4_physics = QtGui.QLineEdit(getattr(self.obj, "Geant4PhysicsList", "FTFP_BERT"))
        self._add_row(geant4_layout, "Physics List:", self.le_g4_physics)
        self.sp_g4_events = self._spin_int(getattr(self.obj, "Geant4EventCount", 1000), 1, 1000000000)
        self._add_row(geant4_layout, "Event Count:", self.sp_g4_events)
        self.sp_g4_threads = self._spin_int(getattr(self.obj, "Geant4Threads", 1), 1, 1024)
        self._add_row(geant4_layout, "Threads:", self.sp_g4_threads)
        self.le_g4_macro = QtGui.QLineEdit(getattr(self.obj, "Geant4MacroName", "run.mac"))
        self._add_row(geant4_layout, "Macro File:", self.le_g4_macro)
        self.chk_g4_vis = self._checkbox(getattr(self.obj, "Geant4EnableVisualization", False))
        self._add_row(geant4_layout, "Visualization:", self.chk_g4_vis)
        geant4_layout.addWidget(
            QtGui.QLabel(
                "FlowStudio generates a Geant4 case scaffold and macro, then launches "
                "your compiled Geant4 application if an executable path is configured."
            )
        )
        geant4_layout.addStretch()
        self.stack.addWidget(geant4_page)

        layout.addWidget(self.stack)
        self._on_backend_changed(self.cb_backend.currentText())

        layout.addStretch()
        return widget

    def _on_backend_changed(self, text):
        self.stack.setCurrentIndex(self._presenter.backend_page_index(text))

    def _selected_multi_solver_backends(self):
        selected = []
        if self.chk_multi_openfoam.isChecked():
            selected.append("OpenFOAM")
        if self.chk_multi_elmer.isChecked():
            selected.append("Elmer")
        if self.chk_multi_fluidx3d.isChecked():
            selected.append("FluidX3D")
        if self.chk_multi_geant4.isChecked():
            selected.append("Geant4")
        return selected

    def _store(self):
        self._presenter.persist_settings(self.obj, self._current_settings())

    def _current_settings(self):
        if not hasattr(self, "cb_backend"):
            return self._presenter.read_settings(self.obj)

        num_processors = self.sp_elmer_nproc.value() if self.cb_backend.currentText() == "Elmer" else self.sp_nproc.value()
        return self._presenter._coerce_settings({
            "SolverBackend": self.cb_backend.currentText(),
            "OpenFOAMSolver": self.cb_of_solver.currentText(),
            "MaxIterations": self.sp_iter.value(),
            "ConvergenceTolerance": self.sp_tol.value(),
            "NumProcessors": num_processors,
            "ConvectionScheme": self.cb_conv.currentText(),
            "ElmerSolverBinary": self.cb_elmer_solver.currentText(),
            "FluidX3DPrecision": self.cb_fx_prec.currentText(),
            "FluidX3DResolution": self.sp_fx_res.value(),
            "FluidX3DTimeSteps": self.sp_fx_steps.value(),
            "FluidX3DVRAM": self.sp_fx_vram.value(),
            "FluidX3DMultiGPU": self.chk_multigpu.isChecked(),
            "FluidX3DNumGPUs": self.sp_ngpu.value(),
            "Geant4Executable": self.le_g4_exe.text().strip(),
            "Geant4PhysicsList": self.le_g4_physics.text().strip() or "FTFP_BERT",
            "Geant4EventCount": self.sp_g4_events.value(),
            "Geant4Threads": self.sp_g4_threads.value(),
            "Geant4MacroName": self.le_g4_macro.text().strip() or "run.mac",
            "Geant4EnableVisualization": self.chk_g4_vis.isChecked(),
            "MultiSolverEnabled": self.chk_multi_solver.isChecked(),
            "MultiSolverBackends": self._selected_multi_solver_backends(),
            "SoftRuntimeWarningSeconds": self.sp_runtime_soft.value(),
            "MaxRuntimeSeconds": self.sp_runtime_max.value(),
            "StallTimeoutSeconds": self.sp_runtime_stall.value(),
            "MinProgressPercent": self.sp_runtime_progress.value(),
            "AbortOnThreshold": self.chk_abort_threshold.isChecked(),
        })
