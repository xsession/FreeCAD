# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""End-to-end FlowStudio project cockpit with forced workflow guidance."""

from __future__ import annotations

import FreeCAD
import FreeCADGui
from PySide import QtCore, QtGui

from flow_studio.physics_domains import example_command_groups
from flow_studio.taskpanels.project_cockpit_desktop_actions import FreeCADProjectCockpitActions
from flow_studio.ui.project_cockpit_presenter import ProjectCockpitPresenter


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


def _build_starter_command_groups(
    command_groups_resolver=example_command_groups,
    example_labels=None,
):
    labels = example_labels or {}
    return tuple(
        (
            group_label,
            tuple(
                (command_name, labels.get(command_name, command_name.replace("FlowStudio_", "")))
                for command_name in commands
            ),
        )
        for _group_key, group_label, commands in command_groups_resolver()
    )


class ProjectCockpitPanel:
    """Color-coded simulation cockpit that drives the whole project flow."""

    EXAMPLE_LABELS = {
        "FlowStudio_ElectronicsCoolingStudy": "EC Study",
        "FlowStudio_CoolingChannelStudy": "Cool Ch",
        "FlowStudio_ExternalAeroStudy": "Aero Study",
        "FlowStudio_BuildingsStudy": "Bldg Study",
        "FlowStudio_AirfoilStudy": "Airfoil",
        "FlowStudio_TeslaValveStudy": "Tesla",
        "FlowStudio_VonKarmanStudy": "V-Karman",
        "FlowStudio_PipeFlowStudy": "Pipe Study",
        "FlowStudio_StaticMixerStudy": "Mixer Study",
        "FlowStudio_StructuralBracketExample": "Struct Ex",
        "FlowStudio_ElectrostaticCapacitorExample": "ES Ex",
        "FlowStudio_ElectromagneticCoilExample": "EM Ex",
        "FlowStudio_ThermalPlateExample": "Therm Ex",
        "FlowStudio_OpticalLensExample": "Opt Ex",
    }

    STARTER_COMMAND_GROUPS = ()

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
        self._actions = FreeCADProjectCockpitActions()
        self._presenter = ProjectCockpitPresenter(self.COMMAND_LABELS, actions=self._actions)
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
        self.btn_results.clicked.connect(self._open_results)
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
        try:
            self._presenter.handle_command(command_name)
        finally:
            QtCore.QTimer.singleShot(250, self._refresh)

    def _open_results(self):
        try:
            self._presenter.handle_open_results()
        finally:
            QtCore.QTimer.singleShot(250, self._refresh)

    def _stop_run(self):
        if self._presenter.stop_run():
            FreeCAD.Console.PrintWarning("FlowStudio: Solver termination requested.\n")
        self._refresh()

    def _refresh(self):
        state = self._presenter.build_view_state()
        self.progress.setValue(state.progress_percent)
        _style_banner(self.banner, state.banner.level)
        self.banner.setText(
            f"<b>{state.profile_label} Project Cockpit</b><br>{state.banner.title}<br>{state.banner.detail}"
        )
        self.summary.setText(state.summary_text)

        self._refresh_study_recipe(state.recipe)
        self._refresh_step_tree(state.steps)
        self._refresh_action_buttons(state.actions)
        self._refresh_runtime(state.runtime)

    def _refresh_study_recipe(self, recipe):
        if not recipe.visible:
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
            item = QtGui.QTreeWidgetItem([step.state_label, step.title, step.gate, step.hint])
            bg, fg = _phase_color(step.level)
            for column in range(4):
                item.setBackground(column, QtGui.QBrush(QtGui.QColor(bg)))
                item.setForeground(column, QtGui.QBrush(QtGui.QColor(fg)))
            self.steps_tree.addTopLevelItem(item)
        self.steps_tree.expandAll()

    def _refresh_action_buttons(self, actions):
        for action in actions:
            button = self._command_buttons[action.command_name]
            bg, fg = _phase_color(action.level)
            button.setEnabled(action.enabled)
            button.setStyleSheet(
                f"background:{bg}; color:{fg}; border:1px solid {fg}; border-radius:4px; padding:6px;"
            )

    def _refresh_runtime(self, runtime):
        _style_banner(self.runtime_banner, runtime.level)
        self.runtime_banner.setText(
            f"<b>{runtime.title}</b><br>{runtime.phase}"
        )

        if runtime.progress_indeterminate:
            self.runtime_progress.setRange(0, 0)
        else:
            self.runtime_progress.setRange(0, 100)
            self.runtime_progress.setValue(runtime.progress_percent)

        self.runtime_details.setText("<br>".join(runtime.details))
        self.runtime_log.setPlainText("\n".join(runtime.log_tail) if runtime.log_tail else "No live log output yet.")
        self.runtime_log.verticalScrollBar().setValue(self.runtime_log.verticalScrollBar().maximum())

        self.btn_stop.setEnabled(runtime.stop_enabled)
        self.btn_results.setEnabled(runtime.results_enabled)
        self.btn_results.setText(runtime.results_label)

    def accept(self):
        self._timer.stop()
        FreeCADGui.Control.closeDialog()

    def reject(self):
        self._timer.stop()
        FreeCADGui.Control.closeDialog()


ProjectCockpitPanel.STARTER_COMMAND_GROUPS = _build_starter_command_groups(
    example_labels=ProjectCockpitPanel.EXAMPLE_LABELS
)
