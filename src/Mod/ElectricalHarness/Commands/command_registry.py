"""FreeCAD command objects for the Electrical Harness workbench."""

from __future__ import annotations

import os

import FreeCAD
import FreeCADGui
from PySide import QtGui

from App.entities import Project
from App import project_store
from App.model import ElectricalProjectModel
from App.reports import ReportService
from App.validation import ValidationEngine
from Commands import object_factory


def _icon_path(name: str) -> str:
    module_dir = ""
    for mod_dir in FreeCAD.__ModDirs__:
        if os.path.basename(mod_dir) == "ElectricalHarness":
            module_dir = mod_dir
            break
    if not module_dir:
        module_dir = os.path.join(FreeCAD.getHomePath(), "Mod", "ElectricalHarness")
    return os.path.join(module_dir, "Resources", "icons", name)


class _BaseCommand:
    cmd_name = ""
    tooltip = ""

    def GetResources(self):
        return {
            "MenuText": self.cmd_name,
            "ToolTip": self.tooltip,
            "Pixmap": _icon_path("ElectricalHarnessGeneric.svg"),
        }

    def IsActive(self):
        return True


class CmdNewHarnessProject(_BaseCommand):
    cmd_name = "EH New Project"
    tooltip = "Create a new Electrical Harness project object"

    def Activated(self):
        object_factory.create_harness_project()
        doc_name = FreeCAD.ActiveDocument.Name if FreeCAD.ActiveDocument else "Harness"
        project_store.set_active_model(
            ElectricalProjectModel(Project(project_id=doc_name, name=doc_name))
        )


class CmdCreateConnector(_BaseCommand):
    cmd_name = "EH Connector"
    tooltip = "Create a connector instance"

    def Activated(self):
        object_factory.create_connector_instance()
        model = project_store.get_active_model()
        reference, ok = QtGui.QInputDialog.getText(
            None,
            "Connector Reference",
            "Connector reference:",
            QtGui.QLineEdit.Normal,
            f"J{len(model.connectors) + 1}",
        )
        if not ok or not reference.strip():
            return
        pin_count, ok = QtGui.QInputDialog.getInt(
            None,
            "Connector Pins",
            "Pin count:",
            2,
            1,
            128,
        )
        if not ok:
            return
        model.add_connector_with_pins(reference.strip(), pin_count)
        project_store.notify_changed()


class CmdCreateRoute(_BaseCommand):
    cmd_name = "EH Route Path"
    tooltip = "Create a route path placeholder"

    def Activated(self):
        object_factory.create_route_path()
        project_store.notify_changed()


class CmdCreateWire(_BaseCommand):
    cmd_name = "EH Wire"
    tooltip = "Connect two pins with a wire and assign a net"

    def Activated(self):
        model = project_store.get_active_model()
        pin_ids = sorted(model.pins.keys())
        if len(pin_ids) < 2:
            FreeCAD.Console.PrintWarning("ElectricalHarness: create connectors/pins first\n")
            return

        from_pin, ok = QtGui.QInputDialog.getItem(
            None,
            "Wire Start Pin",
            "From pin:",
            pin_ids,
            0,
            False,
        )
        if not ok:
            return
        to_pin, ok = QtGui.QInputDialog.getItem(
            None,
            "Wire End Pin",
            "To pin:",
            pin_ids,
            min(1, len(pin_ids) - 1),
            False,
        )
        if not ok or to_pin == from_pin:
            return
        net_name, ok = QtGui.QInputDialog.getText(
            None,
            "Net Name",
            "Net name:",
            QtGui.QLineEdit.Normal,
            "NET_SIGNAL",
        )
        if not ok or not net_name.strip():
            return

        model.connect_pins(
            from_pin_id=str(from_pin),
            to_pin_id=str(to_pin),
            net_name=net_name.strip(),
            gauge="22AWG",
            color="RD",
        )
        project_store.notify_changed()


class CmdRenameNet(_BaseCommand):
    cmd_name = "EH Rename Net"
    tooltip = "Search/replace net names across active project"

    def Activated(self):
        model = project_store.get_active_model()
        net_names = sorted({net.name for net in model.nets.values()})
        if not net_names:
            FreeCAD.Console.PrintWarning("ElectricalHarness: no nets available\n")
            return
        current_name, ok = QtGui.QInputDialog.getItem(
            None,
            "Select Net",
            "Current net name:",
            net_names,
            0,
            False,
        )
        if not ok:
            return
        new_name, ok = QtGui.QInputDialog.getText(
            None,
            "Rename Net",
            "New net name:",
            QtGui.QLineEdit.Normal,
            str(current_name),
        )
        if not ok or not new_name.strip():
            return
        updated = model.rename_net(str(current_name), new_name.strip())
        FreeCAD.Console.PrintMessage(f"ElectricalHarness: renamed {updated} net(s)\n")
        project_store.notify_changed()


class CmdValidateProject(_BaseCommand):
    cmd_name = "EH Validate"
    tooltip = "Run electrical harness design validation"

    def Activated(self):
        model = project_store.get_active_model()
        issues = ValidationEngine().run(model)
        FreeCAD.Console.PrintMessage(
            f"ElectricalHarness validation: {len(issues)} issue(s)\n"
        )
        project_store.notify_changed()


class CmdGenerateFromTo(_BaseCommand):
    cmd_name = "EH From-To Report"
    tooltip = "Generate from-to table report"

    def Activated(self):
        model = project_store.get_active_model()
        rows = ReportService().from_to_table(model)
        FreeCAD.Console.PrintMessage(
            f"ElectricalHarness from-to rows: {len(rows)}\n"
        )
        project_store.notify_changed()


class CmdOpenArchitectureDoc(_BaseCommand):
    cmd_name = "EH Architecture"
    tooltip = "Open architecture documentation"

    def Activated(self):
        module_dir = ""
        for mod_dir in FreeCAD.__ModDirs__:
            if os.path.basename(mod_dir) == "ElectricalHarness":
                module_dir = mod_dir
                break
        if not module_dir:
            module_dir = os.path.join(FreeCAD.getHomePath(), "Mod", "ElectricalHarness")
        FreeCADGui.open(os.path.join(module_dir, "docs", "ARCHITECTURE.md"))


def _has_command(command_name: str) -> bool:
    command_api = getattr(FreeCADGui, "Command", None)
    if command_api is not None:
        get_command = getattr(command_api, "get", None)
        if callable(get_command):
            return bool(get_command(command_name))

    list_commands = getattr(FreeCADGui, "listCommands", None)
    if callable(list_commands):
        return command_name in list_commands()

    return False


def register_commands() -> None:
    command_specs = {
        "ElectricalHarness_NewProject": CmdNewHarnessProject(),
        "ElectricalHarness_CreateConnector": CmdCreateConnector(),
        "ElectricalHarness_CreateWire": CmdCreateWire(),
        "ElectricalHarness_RenameNet": CmdRenameNet(),
        "ElectricalHarness_CreateRoutePath": CmdCreateRoute(),
        "ElectricalHarness_Validate": CmdValidateProject(),
        "ElectricalHarness_FromToReport": CmdGenerateFromTo(),
        "ElectricalHarness_OpenArchitecture": CmdOpenArchitectureDoc(),
    }
    for command_name, command in command_specs.items():
        if not _has_command(command_name):
            FreeCADGui.addCommand(command_name, command)
