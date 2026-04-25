"""Minimal GUI smoke test for the PartDesign new-sketch viewport path.

Run with the repository launcher:

    run_freecad.bat tests\test_partdesign_new_sketch_viewport_smoke.py
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
REPORT_PATH = "C:/GIT/FreeCAD/build/debug/test_partdesign_new_sketch_viewport_smoke_report.txt"


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


def active_view_signature():
    try:
        view = Gui.activeView()
    except Exception:
        return "error"

    if view is None:
        return "none"

    view_type = type(view).__name__
    if hasattr(view, "getViewer"):
        return view_type + ":viewer"
    return view_type


def active_dialog_signature():
    try:
        dialog = Gui.Control.activeDialog()
    except Exception:
        return "error"

    if not dialog:
        return "none"

    return type(dialog).__name__


def object_names(doc, type_id):
    return sorted(obj.Name for obj in doc.Objects if getattr(obj, "TypeId", "") == type_id)


def main():
    part_design_prefs = App.ParamGet("User parameter:BaseApp/Preferences/Mod/PartDesign")
    original_attachment_pref = bool(
        part_design_prefs.GetBool("NewSketchUseAttachmentDialog", False)
    )

    doc = None
    try:
        part_design_prefs.SetBool("NewSketchUseAttachmentDialog", True)

        Gui.showMainWindow()
        process_events(0.1, rounds=8)
        Gui.activateWorkbench("PartDesignWorkbench")
        process_events(0.1, rounds=8)

        doc = App.newDocument("PartDesignNewSketchViewportSmoke")
        process_events(0.1, rounds=10)
        Gui.activateWorkbench("PartDesignWorkbench")
        process_events(0.1, rounds=8)

        report("before active-view=" + active_view_signature())
        report("before active-dialog=" + active_dialog_signature())

        Gui.runCommand("PartDesign_NewSketch", 0)
        process_events(0.1, rounds=18)

        body_names = object_names(doc, "PartDesign::Body")
        sketch_names = object_names(doc, "Sketcher::SketchObject")
        active_view = active_view_signature()
        active_dialog = active_dialog_signature()

        report("after bodies=" + ",".join(body_names))
        report("after sketches=" + ",".join(sketch_names))
        report("after active-view=" + active_view)
        report("after active-dialog=" + active_dialog)

        if not body_names:
            write_report()
            print("FAIL: PartDesign_NewSketch did not create or activate a body")
            return 1

        if not sketch_names:
            write_report()
            print("FAIL: PartDesign_NewSketch did not create a sketch")
            return 1

        if active_view == "none":
            write_report()
            print("FAIL: PartDesign_NewSketch left the GUI without an active view")
            return 1

        if active_dialog in {"none", "error"}:
            write_report()
            print("FAIL: PartDesign_NewSketch did not open the attachment dialog")
            return 1

        write_report()
        print("BODY_NAMES=" + ",".join(body_names))
        print("SKETCH_NAMES=" + ",".join(sketch_names))
        print("ACTIVE_VIEW=" + active_view)
        print("ACTIVE_DIALOG=" + active_dialog)
        return 0
    except Exception as exc:
        report("exception=" + repr(exc))
        report(traceback.format_exc())
        write_report()
        print("FAIL: unhandled exception in viewport smoke: " + repr(exc))
        return 1
    finally:
        try:
            Gui.Control.closeDialog()
            process_events(0.05, rounds=4)
        except Exception:
            pass

        if doc is not None:
            try:
                App.closeDocument(doc.Name)
                process_events(0.05, rounds=4)
            except Exception:
                pass

        part_design_prefs.SetBool(
            "NewSketchUseAttachmentDialog",
            original_attachment_pref,
        )
        process_events(0.05, rounds=4)


if __name__ == "__main__":
    exit_with(main())
