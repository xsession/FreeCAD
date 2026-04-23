"""GUI smoke test for Sketcher edit-mode ribbon/classic toggle behavior.

Run with the repository launcher:

    run_freecad.bat tests\test_sketcher_edit_toolbar_smoke.py
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


def report(line):
    REPORT_LINES.append(line)


def write_report():
    with open("C:/GIT/FreeCAD/build/debug/test_sketcher_edit_toolbar_smoke_report.txt", "w", encoding="utf-8") as handle:
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


def set_ribbon(enabled):
    prefs = App.ParamGet("User parameter:BaseApp/Preferences/MainWindow")
    current = bool(prefs.GetBool("UseRibbonBar", False))
    if current != enabled:
        Gui.runCommand("Std_ToggleRibbonBar", 0)
        process_events(0.1, rounds=10)


def visible_sketch_toolbars(main_window):
    wanted = {
        "Edit Mode",
        "Geometries",
        "Constraints",
        "Sketcher Tools",
        "B-Spline Tools",
        "Visual Helpers",
    }
    visible = []
    for toolbar in main_window.findChildren(QtGui.QToolBar):
        if toolbar.objectName() in wanted and toolbar.toggleViewAction().isVisible() and toolbar.isVisible():
            visible.append(toolbar.objectName())
    return sorted(visible)


def ribbon_tab_labels(main_window):
    for tab_widget in main_window.findChildren(QtGui.QTabWidget):
        labels = [tab_widget.tabText(index) for index in range(tab_widget.count())]
        if "Home" in labels or "Sketch" in labels:
            return labels
    return []


def sketch_ribbon_button_count(main_window):
    for tab_widget in main_window.findChildren(QtGui.QTabWidget):
        labels = [tab_widget.tabText(index) for index in range(tab_widget.count())]
        if "Sketch" not in labels:
            continue

        index = labels.index("Sketch")
        page = tab_widget.widget(index)
        if page is None:
            return 0

        buttons = []
        for button in page.findChildren(QtGui.QToolButton):
            if not button.isVisible():
                continue
            if button.defaultAction() is None and not button.text():
                continue
            buttons.append(button)

        return len(buttons)

    return 0


def main():
    prefs = App.ParamGet("User parameter:BaseApp/Preferences/MainWindow")
    original_ribbon = bool(prefs.GetBool("UseRibbonBar", False))

    Gui.showMainWindow()
    process_events(0.1, rounds=8)
    Gui.activateWorkbench("PartDesignWorkbench")
    process_events(0.1, rounds=8)

    doc = App.newDocument("SketcherEditToolbarSmoke")
    process_events(0.1, rounds=6)
    sketch = doc.addObject("Sketcher::SketchObject", "SmokeSketch")
    doc.recompute()
    process_events(0.1, rounds=8)
    gui_doc = Gui.getDocument(doc.Name)

    try:
        gui_doc.setEdit(sketch.Name)
        process_events(0.1, rounds=12)

        main_window = Gui.getMainWindow()

        set_ribbon(True)
        process_events(0.1, rounds=12)
        labels = ribbon_tab_labels(main_window)
        report("enable-1 tabs=" + ",".join(labels))
        if labels.count("Sketch") > 1:
            write_report()
            print("FAIL: duplicate Sketch ribbon tabs in edit mode: " + ",".join(labels))
            return 1
        if "Sketch" not in labels:
            write_report()
            print("FAIL: Sketch ribbon tab missing after enabling ribbon: " + ",".join(labels))
            return 1
        button_count = sketch_ribbon_button_count(main_window)
        report("enable-1 sketch-buttons=" + str(button_count))
        if button_count <= 0:
            write_report()
            print("FAIL: Sketch ribbon tab is empty after enabling ribbon")
            return 1

        set_ribbon(False)
        process_events(0.1, rounds=12)
        visible = visible_sketch_toolbars(main_window)
        report("disable classic-toolbars=" + ",".join(visible))
        if not visible:
            write_report()
            print("FAIL: no visible Sketcher edit-mode toolbars in classic mode")
            return 1

        set_ribbon(True)
        process_events(0.1, rounds=12)
        labels = ribbon_tab_labels(main_window)
        report("enable-2 tabs=" + ",".join(labels))
        if labels.count("Sketch") > 1:
            write_report()
            print("FAIL: duplicate Sketch ribbon tabs after re-enabling ribbon: " + ",".join(labels))
            return 1
        if "Sketch" not in labels:
            write_report()
            print("FAIL: Sketch ribbon tab missing after re-enabling ribbon: " + ",".join(labels))
            return 1
        button_count = sketch_ribbon_button_count(main_window)
        report("enable-2 sketch-buttons=" + str(button_count))
        if button_count <= 0:
            write_report()
            print("FAIL: Sketch ribbon tab is empty after re-enabling ribbon")
            return 1

        write_report()
        print("VISIBLE_SKETCH_TOOLBARS=" + ",".join(visible))
        print("RIBBON_TABS=" + ",".join(labels))
        print("SKETCH_RIBBON_BUTTONS=" + str(button_count))
        return 0
    finally:
        try:
            gui_doc.resetEdit()
            process_events(0.05, rounds=4)
        except Exception:
            pass
        App.closeDocument(doc.Name)
        process_events(0.05, rounds=4)
        set_ribbon(original_ribbon)
        process_events(0.05, rounds=4)


if __name__ == "__main__":
    exit_with(main())
