"""Minimal GUI smoke test for the FlowStudio project cockpit panel.

Run with the repository launcher:

    run_freecad.bat tests\test_project_cockpit_panel_smoke.py
"""

from __future__ import annotations

import sys
import time
import traceback


try:
    import FreeCADGui as Gui
    from PySide import QtCore, QtGui
except ImportError:
    print("ERROR: This script must run inside FreeCAD GUI.")
    sys.exit(1)


REPORT_LINES = []
REPORT_PATH = "C:/GIT/FreeCAD/build/debug/test_project_cockpit_panel_smoke_report.txt"


def report(line):
    REPORT_LINES.append(line)


def write_report():
    with open(REPORT_PATH, "w", encoding="utf-8") as handle:
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


def main():
    panel = None
    try:
        from flow_studio.taskpanels.task_project_cockpit import ProjectCockpitPanel

        panel = ProjectCockpitPanel()
        process_events(0.1, rounds=6)
        panel._refresh()
        process_events(0.1, rounds=6)

        report("title=" + panel.form.windowTitle())
        report("has_presenter=" + str(hasattr(panel, "_presenter")))
        report("summary=" + panel.summary.text())

        if not hasattr(panel, "_presenter"):
            write_report()
            print("FAIL: project cockpit panel did not initialize its presenter")
            return 1

        if panel.form.windowTitle() != "FlowStudio Project Cockpit":
            write_report()
            print("FAIL: project cockpit panel window title was not initialized")
            return 1

        write_report()
        print("PANEL_TITLE=" + panel.form.windowTitle())
        return 0
    except Exception as exc:
        report("exception=" + repr(exc))
        report(traceback.format_exc())
        write_report()
        print("FAIL: unhandled exception in project cockpit panel smoke: " + repr(exc))
        return 1
    finally:
        if panel is not None:
            try:
                panel._timer.stop()
                panel.form.close()
                process_events(0.05, rounds=4)
            except Exception:
                pass


if __name__ == "__main__":
    exit_with(main())