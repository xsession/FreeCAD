"""GUI viewport profiling for large STEP files.

Run with the repository launcher:

    $env:FLOWSTUDIO_STEP_FILE='E:\\path\\to\\model.stp'
    run_freecad.bat tests\test_flowstudio_step_viewport_profile.py
"""

from __future__ import annotations

import collections
import os
import sys
import tempfile
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
REPORT_PATH = "E:/GIT/FreeCAD/build/debug/test_flowstudio_step_viewport_profile_report.txt"


def report(line):
    REPORT_LINES.append(line)
    print(line)


def write_report():
    with open(REPORT_PATH, "w", encoding="utf-8") as handle:
        handle.write("\n".join(REPORT_LINES) + "\n")


def process_events(delay=0.05, rounds=8):
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


def open_step_document(step_file):
    import_result = ImportGui.open(step_file)
    process_events(0.1, rounds=30)
    candidate_name = getattr(import_result, "Name", None)
    if candidate_name:
        documents = App.listDocuments()
        if candidate_name in documents:
            return documents[candidate_name]
    return getattr(App, "ActiveDocument", None)


def collect_objects(doc):
    part_objects = []
    visible_part_objects = []
    total_faces = 0
    total_edges = 0

    for obj in doc.Objects:
        shape = getattr(obj, "Shape", None)
        if not shape:
            continue

        part_objects.append(obj)

        try:
            total_faces += shape.countElement("Face")
        except Exception:
            pass

        try:
            total_edges += shape.countElement("Edge")
        except Exception:
            pass

        view_obj = getattr(obj, "ViewObject", None)
        if view_obj is not None and getattr(view_obj, "Visibility", False):
            visible_part_objects.append(obj)

    return part_objects, visible_part_objects, total_faces, total_edges


def display_mode_counts(objects):
    counts = collections.Counter()
    for obj in objects:
        view_obj = getattr(obj, "ViewObject", None)
        if view_obj is None:
            continue
        mode = getattr(view_obj, "DisplayMode", None)
        if not mode:
            mode = "<none>"
        counts[str(mode)] += 1
    return counts


def format_counts(counter):
    if not counter:
        return "<empty>"
    return ", ".join(f"{key}:{counter[key]}" for key in sorted(counter))


def save_image_benchmark(view, label):
    image_path = os.path.join(tempfile.gettempdir(), f"flowstudio_{label}.png")
    start = time.perf_counter()
    view.redraw()
    process_events(0.05, rounds=6)
    view.saveImage(image_path, 1280, 720, "White")
    process_events(0.05, rounds=4)
    seconds = time.perf_counter() - start
    size_kb = os.path.getsize(image_path) / 1024.0 if os.path.exists(image_path) else -1.0
    return seconds, image_path, size_kb


def set_display_mode(objects, mode_name):
    changed = 0
    unsupported = 0
    for obj in objects:
        view_obj = getattr(obj, "ViewObject", None)
        if view_obj is None or not hasattr(view_obj, "DisplayMode"):
            unsupported += 1
            continue
        try:
            if str(view_obj.DisplayMode) != mode_name:
                view_obj.DisplayMode = mode_name
                changed += 1
        except Exception:
            unsupported += 1
    process_events(0.1, rounds=20)
    return changed, unsupported


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

    doc = None
    try:
        main_window = None
        try:
            main_window = Gui.getMainWindow()
        except Exception:
            main_window = None
        if main_window is not None:
            main_window.show()
        process_events(0.1, rounds=8)

        step_size_mb = os.path.getsize(step_file) / (1024.0 * 1024.0)
        report("step-file=" + step_file)
        report("step-size-mb=%.2f" % step_size_mb)

        import_start = time.perf_counter()
        doc = open_step_document(step_file)
        import_seconds = time.perf_counter() - import_start

        if doc is None:
            report("FAIL: STEP open did not leave an active document")
            write_report()
            return 1

        process_events(0.1, rounds=8)
        Gui.activateWorkbench("FlowStudioWorkbench")
        process_events(0.1, rounds=12)

        view = Gui.activeView()
        if view is None:
            report("FAIL: no active 3D view available")
            write_report()
            return 1

        part_objects, visible_part_objects, total_faces, total_edges = collect_objects(doc)
        initial_modes = display_mode_counts(visible_part_objects)

        report("document=" + doc.Name)
        report("import-seconds=%.2f" % import_seconds)
        report("objects=%d" % len(doc.Objects))
        report("part-like-objects=%d" % len(part_objects))
        report("visible-part-objects=%d" % len(visible_part_objects))
        report("faces=%d" % total_faces)
        report("edges=%d" % total_edges)
        report("display-modes-initial=" + format_counts(initial_modes))

        fit_start = time.perf_counter()
        view.viewIsometric()
        view.fitAll()
        process_events(0.1, rounds=10)
        fit_seconds = time.perf_counter() - fit_start
        report("view-fit-seconds=%.2f" % fit_seconds)

        current_render_seconds, current_image, current_size_kb = save_image_benchmark(view, "current")
        report("render-current-seconds=%.2f" % current_render_seconds)
        report("render-current-image-kb=%.1f" % current_size_kb)
        report("render-current-image=" + current_image)

        shaded_change_start = time.perf_counter()
        changed, unsupported = set_display_mode(visible_part_objects, "Shaded")
        shaded_apply_seconds = time.perf_counter() - shaded_change_start
        shaded_modes = display_mode_counts(visible_part_objects)
        report("display-modes-shaded=" + format_counts(shaded_modes))
        report("display-mode-shaded-changed=%d" % changed)
        report("display-mode-shaded-unsupported=%d" % unsupported)
        report("display-mode-shaded-apply-seconds=%.2f" % shaded_apply_seconds)

        shaded_render_seconds, shaded_image, shaded_size_kb = save_image_benchmark(view, "shaded")
        report("render-shaded-seconds=%.2f" % shaded_render_seconds)
        report("render-shaded-image-kb=%.1f" % shaded_size_kb)
        report("render-shaded-image=" + shaded_image)

        if current_render_seconds > 0:
            report("render-shaded-speedup=%.2fx" % (current_render_seconds / shaded_render_seconds if shaded_render_seconds > 0 else 0.0))

        write_report()
        return 0
    except Exception as exc:
        report("exception=" + repr(exc))
        report(traceback.format_exc())
        write_report()
        print("FAIL: unhandled exception during viewport profile: " + repr(exc))
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