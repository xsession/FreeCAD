"""GUI smoke test for split-view overlay visibility and preference refresh.

Run with the repository launcher:

    run_freecad.bat tests\test_split_view_overlay_smoke.py
"""

from __future__ import annotations

import sys
import time
import traceback


try:
    import FreeCAD as App
    import FreeCADGui as Gui
    from PySide import QtCore, QtGui
except ImportError:
    print("ERROR: This script must run inside FreeCAD GUI.")
    sys.exit(1)


REPORT_LINES = []
REPORT_PATH = "C:/GIT/FreeCAD/build/debug/test_split_view_overlay_smoke_report.txt"


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


def viewer_signature(viewer, index):
    return "viewer{0}:navi={1}:corner={2}".format(
        index,
        bool(viewer.isEnabledNaviCube()),
        bool(viewer.isCornerCrossVisible()),
    )


def collect_signatures(split_view):
    return [viewer_signature(split_view.getViewer(index), index) for index in range(2)]


def set_overlay_preferences(*, show_navi_cube, show_corner_cross):
    view_prefs = App.ParamGet("User parameter:BaseApp/Preferences/View")
    view_prefs.SetBool("ShowNaviCube", show_navi_cube)
    view_prefs.SetBool("CornerCoordSystem", show_corner_cross)


def main():
    view_prefs = App.ParamGet("User parameter:BaseApp/Preferences/View")
    original_show_navi_cube = bool(view_prefs.GetBool("ShowNaviCube", True))
    original_corner_cross = bool(view_prefs.GetBool("CornerCoordSystem", True))
    split_view = None

    try:
        main_window = Gui.getMainWindow()
        if main_window is not None:
            main_window.show()
        process_events(0.1, rounds=8)

        set_overlay_preferences(show_navi_cube=True, show_corner_cross=True)
        process_events(0.1, rounds=8)

        split_view = Gui.createViewer(2, "SplitViewOverlaySmoke")
        process_events(0.1, rounds=12)

        initial_signatures = collect_signatures(split_view)
        for line in initial_signatures:
            report("initial " + line)

        if any("navi=False" in line or "corner=False" in line for line in initial_signatures):
            write_report()
            print("FAIL: split viewer did not initialize navicube and corner cross on every child viewer")
            return 1

        set_overlay_preferences(show_navi_cube=False, show_corner_cross=False)
        process_events(0.1, rounds=12)
        disabled_signatures = collect_signatures(split_view)
        for line in disabled_signatures:
            report("disabled " + line)

        if any("navi=True" in line or "corner=True" in line for line in disabled_signatures):
            write_report()
            print("FAIL: split viewer did not refresh overlays when preferences were disabled")
            return 1

        set_overlay_preferences(show_navi_cube=True, show_corner_cross=True)
        process_events(0.1, rounds=12)
        restored_signatures = collect_signatures(split_view)
        for line in restored_signatures:
            report("restored " + line)

        if any("navi=False" in line or "corner=False" in line for line in restored_signatures):
            write_report()
            print("FAIL: split viewer did not restore overlays when preferences were re-enabled")
            return 1

        write_report()
        print("INITIAL=" + ";".join(initial_signatures))
        print("DISABLED=" + ";".join(disabled_signatures))
        print("RESTORED=" + ";".join(restored_signatures))
        return 0
    except Exception as exc:
        report("exception=" + repr(exc))
        report(traceback.format_exc())
        write_report()
        print("FAIL: unhandled exception in split-view overlay smoke: " + repr(exc))
        return 1
    finally:
        if split_view is not None:
            try:
                split_view.close()
                process_events(0.05, rounds=6)
            except Exception:
                pass

        set_overlay_preferences(
            show_navi_cube=original_show_navi_cube,
            show_corner_cross=original_corner_cross,
        )
        process_events(0.05, rounds=6)


if __name__ == "__main__":
    exit_with(main())