"""Minimal GUI smoke test for ribbon/classic toolbar toggling.

Run with the repository launcher:

    run_freecad.bat tests\test_ribbon_toolbar_toggle_smoke.py
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


def process_events(delay=0.05, rounds=4):
    app = QtGui.QApplication.instance()
    if app is None:
        return
    for _ in range(rounds):
        app.processEvents()
        if delay:
            time.sleep(delay)


def visible_workbench_toolbars(main_window):
    result = []
    for toolbar in main_window.findChildren(QtGui.QToolBar):
        action = toolbar.toggleViewAction()
        if action and action.isVisible() and toolbar.isVisible():
            result.append(toolbar.objectName())
    return sorted(name for name in result if name)


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


def main():
    prefs = App.ParamGet("User parameter:BaseApp/Preferences/MainWindow")
    original = bool(prefs.GetBool("UseRibbonBar", False))

    Gui.showMainWindow()
    process_events(0.1, rounds=8)
    Gui.activateWorkbench("PartDesignWorkbench")
    process_events(0.1, rounds=8)
    main_window = Gui.getMainWindow()

    try:
        if not original:
            Gui.runCommand("Std_ToggleRibbonBar", 0)
            process_events(0.1, rounds=10)

        Gui.runCommand("Std_ToggleRibbonBar", 0)
        process_events(0.1, rounds=10)

        visible = visible_workbench_toolbars(main_window)
        print("VISIBLE_TOOLBARS=" + ",".join(visible))

        if not visible:
            print("FAIL: no visible classic workbench toolbars after disabling ribbon")
            return 1

        return 0
    finally:
        current = bool(prefs.GetBool("UseRibbonBar", False))
        if current != original:
            Gui.runCommand("Std_ToggleRibbonBar", 0)
            process_events(0.1, rounds=8)


if __name__ == "__main__":
    exit_with(main())
