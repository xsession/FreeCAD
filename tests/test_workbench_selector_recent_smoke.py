"""GUI smoke test for recent-workbench entries in the workbench selector.

Run with the repository launcher:

    run_freecad.bat tests\test_workbench_selector_recent_smoke.py
"""

from __future__ import annotations

import sys
import time


try:
    import FreeCAD as App
    import FreeCADGui as Gui
    from PySide import QtCore, QtGui
except ImportError:
    print("ERROR: This script must run inside FreeCAD GUI.")
    sys.exit(1)


REPORT_LINES = []


def log(line):
    try:
        App.Console.PrintMessage(line + "\n")
    except Exception:
        pass


def report(line):
    REPORT_LINES.append(line)
    log("RECENT_SMOKE: " + line)
    write_report()


def write_report():
    with open(
        "C:/GIT/FreeCAD/build/debug/test_workbench_selector_recent_smoke_report.txt",
        "w",
        encoding="utf-8",
    ) as handle:
        handle.write("\n".join(REPORT_LINES) + "\n")


def process_events(delay=0.05, rounds=6):
    app = QtGui.QApplication.instance()
    if app is None:
        return
    for _ in range(rounds):
        app.processEvents()
        if delay:
            time.sleep(delay)


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


def find_overflow_button(main_window):
    for object_name in ("WbTabBarMore", "WbComboMore"):
        button = main_window.findChild(QtGui.QToolButton, object_name)
        if button is not None:
            return button
    return None


def menu_actions_for_section(menu, section_name):
    inside_section = False
    section_actions = []

    for action in menu.actions():
        text = action.text().strip()
        if text == section_name:
            inside_section = True
            continue

        if not inside_section:
            continue

        if action.isSeparator() and not text:
            break

        section_actions.append(action)

    return section_actions


def main():
    prefs = App.ParamGet("User parameter:BaseApp/Preferences/Workbenches")
    original_favorites = prefs.GetString("FavoriteWorkbenchList", "")
    original_recents = prefs.GetString("RecentWorkbenchList", "")
    original_selector_type = prefs.GetInt("WorkbenchSelectorType", 0)

    available_workbenches = sorted(Gui.listWorkbenches().keys())
    blocked_recent_candidates = {
        "FlowStudioWorkbench",
        "FemWorkbench",
        "CAMWorkbench",
        "ElectricalHarnessWorkbench",
    }
    primary_candidates = [
        "StartWorkbench",
        "PartDesignWorkbench",
        "SketcherWorkbench",
        "PartWorkbench",
        "DraftWorkbench",
        "AssemblyWorkbench",
    ]
    recent_candidates = [
        "TechDrawWorkbench",
        "SpreadsheetWorkbench",
        "MeshWorkbench",
        "MeshWorkbench",
        "SurfaceWorkbench",
        "PointsWorkbench",
        "ReverseEngineeringWorkbench",
        "OpenSCADWorkbench",
    ]

    primary_names = [name for name in primary_candidates if name in available_workbenches]
    if len(primary_names) < 3:
        primary_names = available_workbenches[:6]

    recent_targets = [
        name
        for name in recent_candidates
        if name in available_workbenches
        and name not in primary_names
        and name not in blocked_recent_candidates
    ]
    if len(recent_targets) < 2:
        recent_targets = [
            name
            for name in available_workbenches
            if name not in primary_names and name not in blocked_recent_candidates
        ][:2]

    if len(recent_targets) < 2:
        log("RECENT_SMOKE: not enough non-primary workbenches available")
        print("FAIL: not enough non-primary workbenches available for recent-workbench smoke test")
        return 1

    prefs.SetString("FavoriteWorkbenchList", "|".join(primary_names))
    prefs.SetString("RecentWorkbenchList", "")
    prefs.SetInt("WorkbenchSelectorType", 0)

    Gui.showMainWindow()
    process_events(0.1, rounds=8)
    main_window = Gui.getMainWindow()

    try:
        for workbench_name in recent_targets:
            Gui.activateWorkbench(workbench_name)
            process_events(0.1, rounds=10)
            report("activated=" + workbench_name)
            print("ACTIVATED=" + workbench_name)

        overflow_button = find_overflow_button(main_window)
        if overflow_button is None or overflow_button.menu() is None:
            write_report()
            log("RECENT_SMOKE: missing overflow button")
            print("FAIL: could not find workbench selector overflow button")
            return 1

        menu = overflow_button.menu()
        process_events(0.1, rounds=6)

        top_level_texts = [action.text().strip() for action in menu.actions() if action.text().strip()]
        report("menu-sections=" + "|".join(top_level_texts))

        recent_actions = menu_actions_for_section(menu, "Recent Workbenches")
        recent_names = [str(action.property("workbenchName") or "") for action in recent_actions]
        report("recent-workbenches=" + ",".join(recent_names))

        if not recent_actions:
            write_report()
            log("RECENT_SMOKE: Recent Workbenches section missing or empty")
            print("FAIL: Recent Workbenches section missing or empty")
            return 1

        missing = [name for name in recent_targets if name not in recent_names]
        if missing:
            write_report()
            log("RECENT_SMOKE: missing recent entries " + ",".join(missing))
            print("FAIL: recent workbench entries missing from selector: " + ",".join(missing))
            return 1

        log("RECENT_SMOKE: PASS " + ",".join(recent_names))
        print("RECENT_WORKBENCHES=" + ",".join(recent_names))
        return 0
    finally:
        prefs.SetString("FavoriteWorkbenchList", original_favorites)
        prefs.SetString("RecentWorkbenchList", original_recents)
        prefs.SetInt("WorkbenchSelectorType", original_selector_type)
        process_events(0.05, rounds=4)
        write_report()


if __name__ == "__main__":
    exit_with(main())