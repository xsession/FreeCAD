"""Runtime ribbon-context validation for FreeCAD GUI.

Run with the repository launcher so the full GUI environment is available:

    run_freecad.bat tests\test_ribbon_contextual_tabs.py

This script enables ribbon mode, drives representative Sketch, Assembly, and
FlowStudio objects into edit mode, and verifies that the matching contextual
tab appears and disappears again when edit mode is cleared.
"""

from __future__ import annotations

import sys
import time
import traceback
from pathlib import Path


try:
    import FreeCAD as App
    import FreeCADGui as Gui
    from PySide import QtCore, QtGui
except ImportError:
    print("ERROR: This script must run inside FreeCAD GUI.")
    sys.exit(1)


class Logger:
    counts = {"pass": 0, "fail": 0, "warn": 0}
    lines = []

    @classmethod
    def _print(cls, prefix, message):
        line = f"[{prefix}] {message}"
        cls.lines.append(line)
        print(line)
        try:
            App.Console.PrintMessage(line + "\n")
        except Exception:
            pass

    @classmethod
    def ok(cls, message):
        cls.counts["pass"] += 1
        cls._print(" OK ", message)

    @classmethod
    def fail(cls, message):
        cls.counts["fail"] += 1
        cls._print("FAIL", message)

    @classmethod
    def warn(cls, message):
        cls.counts["warn"] += 1
        cls._print("WARN", message)

    @classmethod
    def info(cls, message):
        cls._print("INFO", message)


def report_path():
    custom = App.ConfigGet("RibbonContextReport") or ""
    if custom:
        return Path(custom)

    env_path = ""
    try:
        import os

        env_path = os.environ.get("FREECAD_RIBBON_CONTEXT_REPORT", "")
    except Exception:
        env_path = ""

    if env_path:
        return Path(env_path)

    return Path(App.getHomePath()) / "ribbon_context_report.txt"


def write_report():
    destination = report_path()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(Logger.lines) + "\n", encoding="utf-8")
    Logger.info(f"Wrote report to {destination}")


def process_events(delay=0.05, rounds=3):
    app = QtGui.QApplication.instance()
    if app is None:
        return
    for _ in range(rounds):
        app.processEvents()
        if delay:
            time.sleep(delay)


def wait_for(predicate, timeout=3.0, description="condition"):
    deadline = time.time() + timeout
    while time.time() < deadline:
        process_events()
        if predicate():
            return True
    Logger.fail(f"Timed out waiting for {description}")
    return False


def main_window():
    Gui.showMainWindow()
    process_events(0.1, rounds=6)
    return Gui.getMainWindow()


def find_ribbon_tab_widget():
    window = main_window()
    candidates = window.findChildren(QtGui.QTabWidget)
    for candidate in candidates:
        labels = [candidate.tabText(index) for index in range(candidate.count())]
        if "File" in labels or "Home" in labels:
            return candidate
    raise RuntimeError("Could not find ribbon tab widget in the main window")


def tab_labels(tab_widget):
    return [tab_widget.tabText(index) for index in range(tab_widget.count())]


def ensure_ribbon_enabled():
    prefs = App.ParamGet("User parameter:BaseApp/Preferences/MainWindow")
    originally_enabled = bool(prefs.GetBool("UseRibbonBar", False))
    if not originally_enabled:
        Logger.info("Enabling ribbon mode")
        Gui.runCommand("Std_ToggleRibbonBar", 0)
        if not wait_for(lambda: "File" in tab_labels(find_ribbon_tab_widget()), description="ribbon mode"):
            raise RuntimeError("Ribbon mode did not activate")
    else:
        find_ribbon_tab_widget()
    return originally_enabled


def restore_ribbon_mode(originally_enabled):
    prefs = App.ParamGet("User parameter:BaseApp/Preferences/MainWindow")
    current_enabled = bool(prefs.GetBool("UseRibbonBar", False))
    if current_enabled != originally_enabled:
        Logger.info("Restoring original ribbon preference")
        Gui.runCommand("Std_ToggleRibbonBar", 0)
        process_events(0.1, rounds=6)


def activate_workbench(name):
    Logger.info(f"Activating {name}")
    if not Gui.activateWorkbench(name):
        raise RuntimeError(f"Failed to activate workbench {name}")
    process_events(0.1, rounds=8)


def gui_document(doc):
    return Gui.getDocument(doc)


def clear_edit(doc):
    gui_doc = gui_document(doc.Name)
    if gui_doc and gui_doc.getInEdit():
        gui_doc.resetEdit()
        process_events(0.1, rounds=8)


def validate_contextual_tab(case_name, workbench_name, tab_name, create_object):
    Logger.info(f"Validating {case_name} contextual tab")
    doc = App.newDocument(f"RibbonContext_{case_name.replace(' ', '_')}")
    process_events(0.1, rounds=6)

    try:
        activate_workbench(workbench_name)
        obj = create_object(doc)
        doc.recompute()
        process_events(0.1, rounds=8)

        gui_doc = gui_document(doc.Name)
        gui_doc.setEdit(obj.Name)

        tab_widget = find_ribbon_tab_widget()
        if wait_for(lambda: tab_name in tab_labels(tab_widget), description=f"{case_name} contextual tab"): 
            Logger.ok(f"{case_name}: contextual tab '{tab_name}' is visible during edit mode")

        clear_edit(doc)
        if wait_for(lambda: tab_name not in tab_labels(tab_widget), description=f"{case_name} contextual tab reset"):
            Logger.ok(f"{case_name}: contextual tab '{tab_name}' is removed after edit mode reset")
    finally:
        try:
            clear_edit(doc)
        except Exception:
            pass
        App.closeDocument(doc.Name)
        process_events(0.1, rounds=6)


def create_sketch(doc):
    sketch = doc.addObject("Sketcher::SketchObject", "ValidationSketch")
    return sketch


def create_assembly(doc):
    return doc.addObject("Assembly::AssemblyObject", "ValidationAssembly")


def create_flow_analysis(doc):
    from flow_studio.ObjectsFlowStudio import makeAnalysis

    return makeAnalysis(doc=doc, name="ValidationAnalysis")


def run_validation():
    original_ribbon = ensure_ribbon_enabled()
    try:
        validate_contextual_tab(
            case_name="Sketch",
            workbench_name="SketcherWorkbench",
            tab_name="Sketch",
            create_object=create_sketch,
        )
        validate_contextual_tab(
            case_name="Assembly",
            workbench_name="AssemblyWorkbench",
            tab_name="Assembly",
            create_object=create_assembly,
        )
        validate_contextual_tab(
            case_name="FlowStudio",
            workbench_name="FlowStudioWorkbench",
            tab_name="Simulation",
            create_object=create_flow_analysis,
        )
    finally:
        restore_ribbon_mode(original_ribbon)


def exit_with(code):
    app = QtGui.QApplication.instance()
    if app is not None:
        window = None
        try:
            window = Gui.getMainWindow()
        except Exception:
            window = None

        if window is not None:
            QtCore.QTimer.singleShot(0, window.close)
        QtCore.QTimer.singleShot(0, lambda: app.exit(code))
        process_events(0.05, rounds=4)
    raise SystemExit(code)


if __name__ == "__main__":
    try:
        run_validation()
    except Exception as exc:
        Logger.fail(str(exc))
        traceback.print_exc()
    finally:
        Logger.info(
            "Results: {pass_count} passed, {fail_count} failed, {warn_count} warnings".format(
                pass_count=Logger.counts["pass"],
                fail_count=Logger.counts["fail"],
                warn_count=Logger.counts["warn"],
            )
        )
        write_report()

    exit_with(1 if Logger.counts["fail"] else 0)