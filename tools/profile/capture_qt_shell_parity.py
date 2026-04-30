"""Capture baseline shell artifacts from the current FreeCAD Qt runtime.

Run through the repo launcher, for example:

    $env:PARITY_BASELINE_ID='shell-empty-light'
    $env:PARITY_WORKBENCH='StartWorkbench'
    .\run_freecad.bat tools\profile\capture_qt_shell_parity.py
"""

from __future__ import annotations

import json
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


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PARITY_ROOT = os.path.join(REPO_ROOT, "docs", "parity", "baselines")
SCREENSHOT_DIR = os.path.join(PARITY_ROOT, "screenshots")
METADATA_DIR = os.path.join(PARITY_ROOT, "metadata")


def env(name, default=""):
    return os.environ.get(name, default).strip()


def bool_env(name):
    return env(name).lower() in {"1", "true", "yes", "on"}


def process_events(delay=0.05, rounds=8):
    app = QtGui.QApplication.instance()
    if app is None:
        return
    for _ in range(rounds):
        app.processEvents()
        if delay:
            time.sleep(delay)


def ensure_dirs():
    for path in (SCREENSHOT_DIR, METADATA_DIR):
        os.makedirs(path, exist_ok=True)


def activate_workbench(workbench_name):
    if not workbench_name:
        return
    Gui.activateWorkbench(workbench_name)
    process_events(0.1, rounds=12)


def open_step_if_requested(step_file):
    if not step_file:
        return getattr(App, "ActiveDocument", None)
    if not os.path.isfile(step_file):
        raise FileNotFoundError(step_file)
    import_result = ImportGui.open(step_file)
    process_events(0.1, rounds=30)
    candidate_name = getattr(import_result, "Name", None)
    if candidate_name:
        documents = App.listDocuments()
        if candidate_name in documents:
            return documents[candidate_name]
    return getattr(App, "ActiveDocument", None)


def sanitize_baseline_id(value):
    return value.replace(" ", "-").replace("/", "-").replace("\\", "-")


def screenshot_path(baseline_id, suffix=""):
    suffix_part = f"-{suffix}" if suffix else ""
    return os.path.join(SCREENSHOT_DIR, f"{baseline_id}{suffix_part}.png")


def metadata_path(baseline_id):
    return os.path.join(METADATA_DIR, f"{baseline_id}.json")


def save_main_window_capture(main_window, baseline_id):
    output = screenshot_path(baseline_id)
    pixmap = main_window.grab()
    pixmap.save(output)
    return output


def maybe_save_viewport_capture(baseline_id):
    if not bool_env("PARITY_CAPTURE_VIEWPORT"):
        return None
    view = Gui.activeView()
    if view is None:
        return None
    output = screenshot_path(baseline_id, "viewport")
    try:
        view.viewIsometric()
    except Exception:
        pass
    try:
        view.fitAll()
    except Exception:
        pass
    process_events(0.1, rounds=10)
    try:
        view.saveImage(output, 1440, 900, "White")
    except Exception:
        return None
    return output


def maybe_save_dock_crop(main_window, baseline_id):
    if not bool_env("PARITY_CAPTURE_TREE_PROPERTY"):
        return None

    for dock in main_window.findChildren(QtGui.QDockWidget):
        title = dock.windowTitle().lower()
        if "tree" in title or "property" in title or "combo" in title:
            output = screenshot_path(baseline_id, "tree-property")
            dock.grab().save(output)
            return output
    return None


def collect_visible_toolbars(main_window):
    labels = []
    for toolbar in main_window.findChildren(QtGui.QToolBar):
        if toolbar.isVisible():
            labels.append(toolbar.windowTitle() or toolbar.objectName() or "unnamed-toolbar")
    return sorted(set(labels))


def collect_visible_panels(main_window):
    labels = []
    for dock in main_window.findChildren(QtGui.QDockWidget):
        if dock.isVisible():
            labels.append(dock.windowTitle() or dock.objectName() or "unnamed-panel")
    return sorted(set(labels))


def relative_from_repo(path):
    if not path:
        return None
    return os.path.relpath(path, REPO_ROOT).replace("\\", "/")


def build_metadata(baseline_id, full_window, viewport_crop, tree_property_crop):
    active_doc = getattr(App, "ActiveDocument", None)
    return {
        "$schema": "./metadata-schema.json",
        "baseline_id": baseline_id,
        "theme": env("PARITY_THEME", "unspecified"),
        "workbench": env("PARITY_WORKBENCH", Gui.activeWorkbench().__class__.__name__ if Gui.activeWorkbench() else "unknown"),
        "fixture_document": env("PARITY_FIXTURE_DOCUMENT", active_doc.Name if active_doc else "none"),
        "visible_toolbars": collect_visible_toolbars(Gui.getMainWindow()),
        "visible_panels": collect_visible_panels(Gui.getMainWindow()),
        "active_task": None,
        "artifacts": {
            "full_window": relative_from_repo(full_window),
            "viewport_crop": relative_from_repo(viewport_crop),
            "tree_property_crop": relative_from_repo(tree_property_crop),
            "recording": None,
        },
        "notes": env("PARITY_NOTES", "Captured from Qt shell baseline helper."),
    }


def write_metadata(baseline_id, metadata):
    output = metadata_path(baseline_id)
    with open(output, "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)
        handle.write("\n")
    return output


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
    baseline_id = sanitize_baseline_id(env("PARITY_BASELINE_ID"))
    if not baseline_id:
        print("FAIL: PARITY_BASELINE_ID is required")
        return 1

    ensure_dirs()

    doc = None
    try:
        main_window = Gui.getMainWindow()
        main_window.show()
        main_window.raise_()
        process_events(0.1, rounds=12)

        activate_workbench(env("PARITY_WORKBENCH"))
        doc = open_step_if_requested(env("PARITY_STEP_FILE"))
        process_events(0.1, rounds=16)

        full_window = save_main_window_capture(main_window, baseline_id)
        viewport_crop = maybe_save_viewport_capture(baseline_id)
        tree_property_crop = maybe_save_dock_crop(main_window, baseline_id)
        metadata = build_metadata(baseline_id, full_window, viewport_crop, tree_property_crop)
        metadata_output = write_metadata(baseline_id, metadata)

        print("baseline-id=" + baseline_id)
        print("full-window=" + full_window)
        print("viewport=" + str(viewport_crop))
        print("tree-property=" + str(tree_property_crop))
        print("metadata=" + metadata_output)
        return 0
    except Exception as exc:
        print("FAIL: parity capture failed: " + repr(exc))
        print(traceback.format_exc())
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