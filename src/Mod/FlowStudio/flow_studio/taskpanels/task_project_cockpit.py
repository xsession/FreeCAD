# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""End-to-end FlowStudio project cockpit with forced workflow guidance."""

from __future__ import annotations

import os

import FreeCAD
import FreeCADGui
from PySide import QtCore, QtGui

from flow_studio.core.workflow import get_active_analysis
from flow_studio.physics_domains import example_command_groups
from flow_studio.runtime_monitor import get_run_snapshot, sync_post_pipeline, terminate_run
from flow_studio.workflow_guide import get_workflow_context, get_workflow_status


def _phase_color(level):
    palette = {
        "done": ("#e8f5e9", "#1b5e20"),
        "active": ("#e3f2fd", "#0d47a1"),
        "blocked": ("#f5f5f5", "#616161"),
        "warning": ("#fff8e1", "#8a6d3b"),
        "running": ("#e0f7fa", "#006064"),
        "failed": ("#ffebee", "#b71c1c"),
    }
    return palette.get(level, palette["blocked"])


def _style_banner(widget, level):
    bg, fg = _phase_color(level)
    widget.setStyleSheet(
        f"background:{bg}; color:{fg}; padding:8px; border-radius:6px; border:1px solid {fg};"
    )


class ProjectCockpitPanel:
    """Color-coded simulation cockpit that drives the whole project flow."""

    EXAMPLE_LABELS = {
        "FlowStudio_ElectronicsCoolingStudy": "EC Study",
        "FlowStudio_ExternalAeroStudy": "Aero Study",
        "FlowStudio_PipeFlowStudy": "Pipe Study",
        "FlowStudio_StaticMixerStudy": "Mixer Study",
        "FlowStudio_StructuralBracketExample": "Struct Ex",
        "FlowStudio_ElectrostaticCapacitorExample": "ES Ex",
        "FlowStudio_ElectromagneticCoilExample": "EM Ex",
        "FlowStudio_ThermalPlateExample": "Therm Ex",
        "FlowStudio_OpticalLensExample": "Opt Ex",
    }

    STARTER_COMMAND_GROUPS = tuple(
        (
            group_label,
            tuple(
                (command_name, EXAMPLE_LABELS.get(command_name, command_name.replace("FlowStudio_", "")))
                for command_name in commands
            ),
        )
        for _group_key, group_label, commands in example_command_groups()
    )

    COMMAND_LABELS = (
        ("FlowStudio_Analysis", "1. Analysis"),
        ("FlowStudio_ImportStep", "2. Import Model"),
        ("FlowStudio_CheckGeometry", "3. Check / Debug"),
        ("FlowStudio_MeshGmsh", "4. Mesh"),
        ("FlowStudio_InitialConditions", "5. Study Controls"),
        ("FlowStudio_RunSolver", "6. Run"),
        ("FlowStudio_PostPipeline", "7. Post"),
        ("FlowStudio_CheckWorkflow", "Validate"),
    )

    def __init__(self):
        self.form = QtGui.QWidget()
        self.form.setWindowTitle("FlowStudio Project Cockpit")
        self._command_buttons = {}
        self._build_form()
        self._timer = QtCore.QTimer(self.form)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(1500)
        self._refresh()

    def _build_form(self):
        layout = QtGui.QVBoxLayout(self.form)

        self.banner = QtGui.QLabel("")
        self.banner.setWordWrap(True)
        layout.addWidget(self.banner)

        self.progress = QtGui.QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        layout.addWidget(self.progress)

        self.summary = QtGui.QLabel("")
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)

        self.recipe_group = QtGui.QGroupBox("Study Recipe")
        recipe_layout = QtGui.QVBoxLayout(self.recipe_group)
        self.recipe_banner = QtGui.QLabel("")
        self.recipe_banner.setWordWrap(True)
        recipe_layout.addWidget(self.recipe_banner)
        self.recipe_details = QtGui.QLabel("")
        self.recipe_details.setWordWrap(True)
        recipe_layout.addWidget(self.recipe_details)
        self.recipe_group.setVisible(False)
        layout.addWidget(self.recipe_group)

        starter_group = QtGui.QGroupBox("Starter Examples")
        starter_layout = QtGui.QVBoxLayout(starter_group)
        for group_label, commands in self.STARTER_COMMAND_GROUPS:
            domain_group = QtGui.QGroupBox(group_label)
            domain_layout = QtGui.QGridLayout(domain_group)
            for index, (command_name, label) in enumerate(commands):
                button = QtGui.QPushButton(label)
                button.clicked.connect(lambda _checked=False, c=command_name: self._run_command(c))
                button.setMinimumHeight(32)
                row, col = divmod(index, 2)
                domain_layout.addWidget(button, row, col)
                self._command_buttons[command_name] = button
            starter_layout.addWidget(domain_group)
        layout.addWidget(starter_group)

        actions_group = QtGui.QGroupBox("Forced Workflow")
        actions_layout = QtGui.QGridLayout(actions_group)
        for index, (command_name, label) in enumerate(self.COMMAND_LABELS):
            button = QtGui.QPushButton(label)
            button.clicked.connect(lambda _checked=False, c=command_name: self._run_command(c))
            button.setMinimumHeight(34)
            row, col = divmod(index, 4)
            actions_layout.addWidget(button, row, col)
            self._command_buttons[command_name] = button

        control_row = (len(self.COMMAND_LABELS) + 3) // 4

        self.btn_stop = QtGui.QPushButton("Stop Run")
        self.btn_stop.clicked.connect(self._stop_run)
        actions_layout.addWidget(self.btn_stop, control_row, 0, 1, 2)

        self.btn_results = QtGui.QPushButton("Open Results")
        self.btn_results.clicked.connect(lambda: self._run_command("FlowStudio_PostPipeline"))
        actions_layout.addWidget(self.btn_results, control_row, 2, 1, 2)
        layout.addWidget(actions_group)

        self.steps_tree = QtGui.QTreeWidget()
        self.steps_tree.setHeaderLabels(["State", "Step", "Gate", "Hint"])
        self.steps_tree.setMinimumHeight(220)
        layout.addWidget(self.steps_tree)

        runtime_group = QtGui.QGroupBox("Live Runtime")
        runtime_layout = QtGui.QVBoxLayout(runtime_group)
        self.runtime_banner = QtGui.QLabel("")
        self.runtime_banner.setWordWrap(True)
        runtime_layout.addWidget(self.runtime_banner)

        self.runtime_progress = QtGui.QProgressBar()
        runtime_layout.addWidget(self.runtime_progress)

        self.runtime_details = QtGui.QLabel("")
        self.runtime_details.setWordWrap(True)
        runtime_layout.addWidget(self.runtime_details)

        self.runtime_log = QtGui.QPlainTextEdit()
        self.runtime_log.setReadOnly(True)
        self.runtime_log.setMinimumHeight(160)
        runtime_layout.addWidget(self.runtime_log)
        layout.addWidget(runtime_group)

    def _run_command(self, command_name):
        if not command_name:
            return
        try:
            FreeCADGui.runCommand(command_name)
        finally:
            QtCore.QTimer.singleShot(250, self._refresh)

    def _stop_run(self):
        analysis = get_active_analysis()
        if terminate_run(analysis):
            FreeCAD.Console.PrintWarning("FlowStudio: Solver termination requested.\n")
        self._refresh()

    def _refresh(self):
        context = get_workflow_context()
        steps = get_workflow_status()
        analysis = context["analysis"]
        profile = context["profile"]

        completed = sum(1 for step in steps if step.complete)
        total = max(1, len(steps))
        percent = int((completed / float(total)) * 100.0)
        self.progress.setValue(percent)

        next_step = next((step for step in steps if not step.complete and step.active), None)
        if completed == total:
            banner_level = "done"
            banner_title = "Project ready for result review"
            banner_detail = "All workflow phases are complete. Review results or refine the setup."
        elif next_step is not None:
            banner_level = "active"
            banner_title = f"Next forced step: {next_step.number}. {next_step.name}"
            banner_detail = next_step.hint or next_step.description
        else:
            banner_level = "warning"
            banner_title = "Workflow is blocked"
            banner_detail = "Resolve the blocked prerequisites shown below to continue."
        _style_banner(self.banner, banner_level)
        self.banner.setText(
            f"<b>{profile.label} Project Cockpit</b><br>{banner_title}<br>{banner_detail}"
        )

        self.summary.setText(
            f"Completed {completed}/{total} steps for "
            f"{getattr(analysis, 'Label', getattr(analysis, 'Name', 'No Analysis'))}. "
            f"Color coding is enforced: green = done, blue = ready now, grey = blocked."
        )

        self._refresh_study_recipe(context)
        self._refresh_step_tree(steps)
        self._refresh_action_buttons(steps)
        self._refresh_runtime(analysis)

    def _refresh_study_recipe(self, context):
        recipe = context.get("study_recipe")
        if recipe is None:
            self.recipe_group.setVisible(False)
            self.recipe_banner.clear()
            self.recipe_details.clear()
            return

        self.recipe_group.setVisible(True)
        self.recipe_banner.setText(
            f"<b>{recipe.label}</b><br>{recipe.summary}<br><a href='{recipe.reference_url}'>{recipe.reference_url}</a>"
        )
        milestone_lines = "".join(f"<li>{item}</li>" for item in recipe.milestones)
        parameter_lines = "".join(f"<li>{item}</li>" for item in recipe.key_parameters)
        self.recipe_details.setText(
            "<b>Workflow milestones</b><ul>"
            f"{milestone_lines}"
            "</ul><b>Reference values</b><ul>"
            f"{parameter_lines}"
            "</ul>"
        )
        self.recipe_banner.setOpenExternalLinks(True)

    def _refresh_step_tree(self, steps):
        self.steps_tree.clear()
        for step in steps:
            if step.complete:
                state = "Done"
                level = "done"
                gate = "Unlocked"
            elif step.active:
                state = "Ready"
                level = "active"
                gate = "Do this now"
            else:
                state = "Blocked"
                level = "blocked"
                gate = "Waiting for previous step"
            item = QtGui.QTreeWidgetItem([state, f"{step.number}. {step.name}", gate, step.hint or ""])
            bg, fg = _phase_color(level)
            for column in range(4):
                item.setBackground(column, QtGui.QBrush(QtGui.QColor(bg)))
                item.setForeground(column, QtGui.QBrush(QtGui.QColor(fg)))
            self.steps_tree.addTopLevelItem(item)
        self.steps_tree.expandAll()

    def _refresh_action_buttons(self, steps):
        step_by_command = {step.command_name: step for step in steps if step.command_name}
        for command_name, _label in self.COMMAND_LABELS:
            button = self._command_buttons[command_name]
            step = step_by_command.get(command_name)
            enabled = True
            level = "active"
            if step is not None:
                enabled = bool(step.active or step.complete)
                if step.complete:
                    level = "done"
                elif step.active:
                    level = "active"
                else:
                    level = "blocked"
            bg, fg = _phase_color(level)
            button.setEnabled(enabled)
            button.setStyleSheet(
                f"background:{bg}; color:{fg}; border:1px solid {fg}; border-radius:4px; padding:6px;"
            )

    def _refresh_runtime(self, analysis):
        snapshot = get_run_snapshot(analysis)
        if snapshot["result_path"]:
            try:
                sync_post_pipeline(analysis, snapshot=snapshot)
            except Exception:
                pass

        status = snapshot["status"]
        if status == "RUNNING":
            level = "running"
            title = "Simulation is running"
        elif status == "FINISHED":
            level = "done"
            title = "Simulation finished"
        elif status in {"FAILED", "TERMINATING"}:
            level = "failed" if status == "FAILED" else "warning"
            title = "Simulation needs attention"
        else:
            level = "blocked"
            title = "No active simulation"

        _style_banner(self.runtime_banner, level)
        self.runtime_banner.setText(
            f"<b>{title}</b><br>{snapshot['phase']}"
        )

        progress_percent = snapshot["progress_percent"]
        if progress_percent is None and status == "RUNNING":
            self.runtime_progress.setRange(0, 0)
        else:
            self.runtime_progress.setRange(0, 100)
            self.runtime_progress.setValue(int(progress_percent or 0))

        elapsed = snapshot["elapsed_seconds"]
        result_path = snapshot["result_path"]
        details = [
            f"Backend: {snapshot['backend'] or 'n/a'}",
            f"PID: {snapshot['pid'] or 'n/a'}",
            f"Elapsed: {elapsed:.1f}s",
        ]
        if snapshot["case_dir"]:
            details.append(f"Case: {snapshot['case_dir']}")
        if result_path:
            details.append(f"Results: {os.path.basename(result_path)}")
        if snapshot["last_error"]:
            details.append(f"Last issue: {snapshot['last_error']}")
        self.runtime_details.setText("<br>".join(details))

        log_tail = snapshot["log_tail"]
        self.runtime_log.setPlainText("\n".join(log_tail) if log_tail else "No live log output yet.")
        self.runtime_log.verticalScrollBar().setValue(self.runtime_log.verticalScrollBar().maximum())

        self.btn_stop.setEnabled(status == "RUNNING")
        self.btn_results.setEnabled(bool(result_path))

    def accept(self):
        self._timer.stop()
        FreeCADGui.Control.closeDialog()

    def reject(self):
        self._timer.stop()
        FreeCADGui.Control.closeDialog()
