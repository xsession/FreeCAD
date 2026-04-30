"""GUI smoke test for opening a STEP file and activating FlowStudio.

Run with the repository launcher:

    $env:FLOWSTUDIO_STEP_FILE='E:\\path\\to\\model.stp'
    run_freecad.bat tests\test_flowstudio_step_open_smoke.py
"""

from __future__ import annotations

import os
import sys
import time
import traceback


try:
    import FreeCAD as App
    import FreeCADGui as Gui
    import ImportGui
    from PySide import QtCore, QtGui
except ImportError:
    print("ERROR: This script must run inside FreeCAD GUI.")
    sys.exit(1)


REPORT_LINES = []
REPORT_PATH = "E:/GIT/FreeCAD/build/debug/test_flowstudio_step_open_smoke_report.txt"


def report(line):
    REPORT_LINES.append(line)
    print(line)


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


def view_count(gui_doc):
    if gui_doc is None:
        return -1
    try:
        return len(gui_doc.mdiViewsOfType("Gui::View3DInventor"))
    except Exception:
        return -1


def document_stats(doc):
    object_count = len(doc.Objects)
    part_like_count = 0
    face_count = 0
    visible_count = 0

    for obj in doc.Objects:
        view_obj = getattr(obj, "ViewObject", None)
        if view_obj is not None and getattr(view_obj, "Visibility", False):
            visible_count += 1

        shape = getattr(obj, "Shape", None)
        if not shape:
            continue

        part_like_count += 1
        try:
            face_count += shape.countElement("Face")
        except Exception:
            pass

    return object_count, part_like_count, face_count, visible_count


def resolve_document(import_result):
    candidate_name = getattr(import_result, "Name", None)
    if candidate_name:
        documents = App.listDocuments()
        if candidate_name in documents:
            return documents[candidate_name]
    return getattr(App, "ActiveDocument", None)


def main():
    step_file = os.environ.get("FLOWSTUDIO_STEP_FILE", "").strip()
    if not step_file:
        report("FAIL: FLOWSTUDIO_STEP_FILE is not set")
        write_report()
        return 1

    if not os.path.isfile(step_file):
        report("FAIL: STEP file does not exist: " + step_file)
        write_report()
        return 1

    step_size_mb = os.path.getsize(step_file) / (1024.0 * 1024.0)
    report("step-file=" + step_file)
    report("step-size-mb=%.2f" % step_size_mb)

    doc = None
    try:
        main_window = None
        try:
            main_window = Gui.getMainWindow()
        except Exception:
            main_window = None

        if main_window is not None:
            main_window.show()
        process_events(0.1, rounds=10)

        start = time.perf_counter()
        import_result = ImportGui.open(step_file)
        process_events(0.1, rounds=30)
        import_seconds = time.perf_counter() - start

        doc = resolve_document(import_result)

        if doc is None:
            report("FAIL: ImportGui.open did not leave an active document")
            write_report()
            return 1

        gui_doc = Gui.getDocument(doc.Name)
        object_count, part_like_count, face_count, visible_count = document_stats(doc)

        report("import-seconds=%.2f" % import_seconds)
        report("document=" + doc.Name)
        report("objects=%d" % object_count)
        report("part-like-objects=%d" % part_like_count)
        report("faces=%d" % face_count)
        report("visible-objects=%d" % visible_count)
        report("view-count-after-open=%d" % view_count(gui_doc))
        report("active-view-after-open=" + active_view_signature())

        activated = bool(Gui.activateWorkbench("FlowStudioWorkbench"))
        process_events(0.1, rounds=20)

        gui_doc = Gui.getDocument(doc.Name)
        report("flowstudio-activated=" + str(activated))
        report("view-count-after-flowstudio=%d" % view_count(gui_doc))
        report("active-view-after-flowstudio=" + active_view_signature())

        if active_view_signature() == "none":
            report("FAIL: no active view after FlowStudio activation")
            write_report()
            return 1

        write_report()
        return 0
    except Exception as exc:
        report("exception=" + repr(exc))
        report(traceback.format_exc())
        write_report()
        print("FAIL: unhandled exception during STEP smoke: " + repr(exc))
        return 1
    finally:
        if doc is not None:
            try:
                App.closeDocument(doc.Name)
                process_events(0.05, rounds=4)
            except Exception:
                pass


if __name__ == "__main__":
    exit_with(main())