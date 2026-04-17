"""Workbench registration and GUI layout for Electrical Harness."""

from __future__ import annotations

import os

import FreeCAD
import FreeCADGui
from PySide import QtCore

from App import project_store
from App.document_objects import register_default_objects
from App.reports import ReportService
from App.validation import ValidationEngine
from Commands.command_registry import register_commands
from Gui.panels import (
    LibraryBrowserPanel,
    ProjectBrowserPanel,
    ReportsPanel,
    ValidationPanel,
)
from Gui.selection_bridge import SelectionBridge


class ElectricalHarnessWorkbench(FreeCADGui.Workbench):
    MenuText = "Electrical Harness"
    ToolTip = "Enterprise harness and schematics engineering workbench"

    CORE_COMMANDS = [
        "ElectricalHarness_NewProject",
        "ElectricalHarness_CreateConnector",
        "ElectricalHarness_CreateWire",
        "ElectricalHarness_RenameNet",
        "ElectricalHarness_CreateRoutePath",
        "ElectricalHarness_Validate",
        "ElectricalHarness_FromToReport",
    ]

    DOC_COMMANDS = [
        "ElectricalHarness_OpenArchitecture",
    ]

    def __init__(self):
        module_dir = ""
        for mod_dir in FreeCAD.__ModDirs__:
            if os.path.basename(mod_dir) == "ElectricalHarness":
                module_dir = mod_dir
                break
        if not module_dir:
            module_dir = os.path.join(FreeCAD.getHomePath(), "Mod", "ElectricalHarness")
        self.__class__.Icon = os.path.join(
            module_dir,
            "Resources",
            "icons",
            "ElectricalHarnessWorkbench.svg",
        )

    def Initialize(self):
        register_default_objects()
        register_commands()

        self.appendToolbar("Electrical Harness Core", self.CORE_COMMANDS)
        self.appendToolbar("Electrical Harness Docs", self.DOC_COMMANDS)
        self.appendMenu("Electrical Harness", self.CORE_COMMANDS)
        self.appendMenu(["Electrical Harness", "Documentation"], self.DOC_COMMANDS)

    def Activated(self):
        self._selection_bridge = SelectionBridge()
        mw = FreeCADGui.getMainWindow()
        self._project_panel = ProjectBrowserPanel("EH Project Browser", mw)
        self._library_panel = LibraryBrowserPanel("EH Library Browser", mw)
        self._validation_panel = ValidationPanel("EH Validation", mw)
        self._reports_panel = ReportsPanel("EH Reports", mw)

        self._project_panel.set_provider(self._project_rows)
        self._library_panel.set_provider(project_store.sample_library_rows)
        self._validation_panel.set_provider(self._validation_rows)
        self._reports_panel.set_provider(self._report_rows)

        for panel in (
            self._project_panel,
            self._library_panel,
            self._validation_panel,
            self._reports_panel,
        ):
            mw.addDockWidget(QtCore.Qt.LeftDockWidgetArea, panel)
            panel.show()
            panel.refresh()

        self._project_panel.rowActivated.connect(lambda sid: self._selection_bridge.publish("project", sid))
        self._validation_panel.rowActivated.connect(lambda sid: self._selection_bridge.publish("validation", sid))
        self._reports_panel.rowActivated.connect(lambda sid: self._selection_bridge.publish("reports", sid))
        self._selection_bridge.subscribe("project", self._cross_probe_entity)
        self._selection_bridge.subscribe("validation", self._cross_probe_entity)
        self._selection_bridge.subscribe("reports", self._cross_probe_entity)

        project_store.register_observer(self._refresh_panels)

    def Deactivated(self):
        project_store.unregister_observer(self._refresh_panels)
        for attr in (
            "_project_panel",
            "_library_panel",
            "_validation_panel",
            "_reports_panel",
        ):
            panel = getattr(self, attr, None)
            if panel is not None:
                panel.hide()
        bridge = getattr(self, "_selection_bridge", None)
        if bridge is not None:
            bridge.clear()

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def _refresh_panels(self) -> None:
        for panel in (
            getattr(self, "_project_panel", None),
            getattr(self, "_library_panel", None),
            getattr(self, "_validation_panel", None),
            getattr(self, "_reports_panel", None),
        ):
            if panel is not None:
                panel.refresh()

    def _cross_probe_entity(self, entity_id: str) -> None:
        if not entity_id or entity_id == "-":
            return
        for panel in (
            getattr(self, "_project_panel", None),
            getattr(self, "_library_panel", None),
            getattr(self, "_validation_panel", None),
            getattr(self, "_reports_panel", None),
        ):
            if panel is not None:
                panel.focus_on_token(entity_id)

    @staticmethod
    def _project_rows():
        model = project_store.get_active_model()
        return [
            {
                "entity": "Project",
                "name": model.project.name,
                "id": model.project.project_id,
                "count": "-",
            },
            {"entity": "Connectors", "name": "Instances", "id": "connector", "count": len(model.connectors)},
            {"entity": "Pins", "name": "Cavities", "id": "pin", "count": len(model.pins)},
            {"entity": "Nets", "name": "Signals", "id": "net", "count": len(model.nets)},
            {"entity": "Wires", "name": "Conductor links", "id": "wire", "count": len(model.wires)},
            {"entity": "Splices", "name": "Inline joints", "id": "splice", "count": len(model.splices)},
            {"entity": "Bundle Segments", "name": "Route topology", "id": "bundle", "count": len(model.bundle_segments)},
        ]

    @staticmethod
    def _validation_rows():
        model = project_store.get_active_model()
        issues = ValidationEngine().run(model)
        rows = []
        for issue in issues:
            rows.append(
                {
                    "severity": issue.severity,
                    "code": issue.code,
                    "entity": issue.entity_id,
                    "message": issue.message,
                }
            )
        return rows

    @staticmethod
    def _report_rows():
        model = project_store.get_active_model()
        rows = ReportService().from_to_table(model)
        if rows:
            return rows
        return [{"wire_id": "-", "net_id": "-", "from_pin_id": "-", "to_pin_id": "-", "gauge": "-"}]
