"""Capture baseline shell artifacts from the current FreeCAD Qt runtime.

Run through the repo launcher, for example:

    $env:PARITY_BASELINE_ID='shell-empty-light'
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
    import Part
    import Sketcher
    from PySide import QtCore, QtGui
except ImportError:
    print("ERROR: This script must run inside FreeCAD GUI.")
    sys.exit(1)


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PARITY_ROOT = os.path.join(REPO_ROOT, "docs", "parity", "baselines")
SCREENSHOT_DIR = os.path.join(PARITY_ROOT, "screenshots")
METADATA_DIR = os.path.join(PARITY_ROOT, "metadata")
TECHDRAW_TEST_TEMPLATE = os.path.join(REPO_ROOT, "src", "Mod", "TechDraw", "TDTest", "TestTemplate.svg")
MAIN_WINDOW_PREF_PATH = "User parameter:BaseApp/Preferences/MainWindow"
BUILTIN_THEME_BY_LABEL = {
    "dark": "FreeCAD Dark",
    "light": "FreeCAD Light",
}


def add_rectangle_sketch(sketch, corner, lengths):
    hmin, hmax = corner[0], corner[0] + lengths[0]
    vmin, vmax = corner[1], corner[1] + lengths[1]
    start_index = int(sketch.GeometryCount)

    sketch.addGeometry(Part.LineSegment(App.Vector(hmin, vmax), App.Vector(hmax, vmax, 0)))
    sketch.addGeometry(Part.LineSegment(App.Vector(hmax, vmax, 0), App.Vector(hmax, vmin, 0)))
    sketch.addGeometry(Part.LineSegment(App.Vector(hmax, vmin, 0), App.Vector(hmin, vmin, 0)))
    sketch.addGeometry(Part.LineSegment(App.Vector(hmin, vmin, 0), App.Vector(hmin, vmax, 0)))

    sketch.addConstraint(Sketcher.Constraint("Coincident", start_index + 0, 2, start_index + 1, 1))
    sketch.addConstraint(Sketcher.Constraint("Coincident", start_index + 1, 2, start_index + 2, 1))
    sketch.addConstraint(Sketcher.Constraint("Coincident", start_index + 2, 2, start_index + 3, 1))
    sketch.addConstraint(Sketcher.Constraint("Coincident", start_index + 3, 2, start_index + 0, 1))
    sketch.addConstraint(Sketcher.Constraint("Horizontal", start_index + 0))
    sketch.addConstraint(Sketcher.Constraint("Horizontal", start_index + 2))
    sketch.addConstraint(Sketcher.Constraint("Vertical", start_index + 1))
    sketch.addConstraint(Sketcher.Constraint("Vertical", start_index + 3))
    sketch.addConstraint(Sketcher.Constraint("DistanceX", start_index + 2, 2, corner[0]))
    sketch.addConstraint(Sketcher.Constraint("DistanceY", start_index + 2, 2, corner[1]))
    sketch.addConstraint(Sketcher.Constraint("Distance", start_index + 1, vmax - vmin))
    sketch.addConstraint(Sketcher.Constraint("Distance", start_index + 0, hmax - hmin))


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


def apply_runtime_theme(theme_label):
    normalized = theme_label.lower()
    desired_theme = BUILTIN_THEME_BY_LABEL.get(normalized)
    if not desired_theme:
        return None

    prefs = App.ParamGet(MAIN_WINDOW_PREF_PATH)
    previous = {
        "Theme": prefs.GetString("Theme"),
        "StyleSheet": prefs.GetString("StyleSheet"),
        "ThemeStyleParametersFile": prefs.GetString("ThemeStyleParametersFile"),
    }

    changed = False
    if previous["Theme"] != desired_theme:
        prefs.SetString("Theme", desired_theme)
        changed = True
    if previous["StyleSheet"] != "FreeCAD.qss":
        prefs.SetString("StyleSheet", "FreeCAD.qss")
        changed = True
    if previous["ThemeStyleParametersFile"]:
        prefs.SetString("ThemeStyleParametersFile", "")
        changed = True

    if changed:
        try:
            Gui.runCommand("Std_ReloadStyleSheet", 0)
        except Exception:
            App.Console.PrintWarning("Failed to reload stylesheet after theme switch\n")
        process_events(0.1, rounds=16)

    return previous


def restore_runtime_theme(previous):
    if not previous:
        return

    prefs = App.ParamGet(MAIN_WINDOW_PREF_PATH)
    prefs.SetString("Theme", previous["Theme"])
    prefs.SetString("StyleSheet", previous["StyleSheet"])
    prefs.SetString("ThemeStyleParametersFile", previous["ThemeStyleParametersFile"])

    try:
        Gui.runCommand("Std_ReloadStyleSheet", 0)
    except Exception:
        App.Console.PrintWarning("Failed to restore stylesheet after parity capture\n")
    process_events(0.05, rounds=8)


def activate_workbench(workbench_name):
    if not workbench_name:
        return
    available = Gui.listWorkbenches()
    resolved_name = workbench_name
    if resolved_name not in available and resolved_name == "StartWorkbench" and "Start" in available:
        resolved_name = "Start"
    if resolved_name not in available and workbench_name == "StartWorkbench":
        App.Console.PrintLog("Skipping legacy StartWorkbench activation; Start is no longer an activatable workbench\n")
        process_events(0.1, rounds=12)
        return
    Gui.activateWorkbench(resolved_name)
    process_events(0.1, rounds=12)


def current_workbench_name():
    try:
        workbench = Gui.activeWorkbench()
    except Exception:
        workbench = None
    if workbench is None:
        return "unknown"
    return workbench.__class__.__name__


def prepare_fixture_document(fixture_id):
    if not fixture_id or fixture_id == "startup-shell":
        return getattr(App, "ActiveDocument", None)

    if fixture_id == "empty-document":
        doc = App.newDocument("ParityEmpty")
        process_events(0.1, rounds=12)
        return doc

    if fixture_id == "primitive-document":
        doc = App.newDocument("ParityPrimitive")
        part = doc.addObject("App::Part", "Part")
        box = part.newObject("Part::Box", "Box")
        box.Length = 16
        box.Width = 12
        box.Height = 10
        doc.recompute()
        process_events(0.1, rounds=16)
        return doc

    if fixture_id == "partdesign-pad-example":
        doc = App.newDocument("ParityPartDesign")
        body = doc.addObject("PartDesign::Body", "Body")
        sketch = body.newObject("Sketcher::SketchObject", "Sketch")
        sketch.AttachmentSupport = [(body.Origin.OriginFeatures[3], "")]
        sketch.MapMode = "FlatFace"

        points = [
            App.Vector(0, 0, 0),
            App.Vector(30, 0, 0),
            App.Vector(30, 20, 0),
            App.Vector(0, 20, 0),
        ]
        for start, end in zip(points, points[1:] + points[:1]):
            sketch.addGeometry(Part.LineSegment(start, end), False)

        sketch.addConstraint(
            [
                Sketcher.Constraint("Coincident", 0, 2, 1, 1),
                Sketcher.Constraint("Coincident", 1, 2, 2, 1),
                Sketcher.Constraint("Coincident", 2, 2, 3, 1),
                Sketcher.Constraint("Coincident", 3, 2, 0, 1),
                Sketcher.Constraint("Horizontal", 0),
                Sketcher.Constraint("Horizontal", 2),
                Sketcher.Constraint("Vertical", 1),
                Sketcher.Constraint("Vertical", 3),
            ]
        )

        pad = body.newObject("PartDesign::Pad", "Pad")
        pad.Profile = sketch
        pad.Length = 12
        doc.recompute()
        process_events(0.1, rounds=16)
        return doc

    if fixture_id == "sketcher-constraint-example":
        doc = App.newDocument("ParitySketcher")
        sketch = doc.addObject("Sketcher::SketchObject", "Sketch")
        add_rectangle_sketch(sketch, (0, 0), (30, 20))
        circle_index = sketch.addGeometry(Part.Circle(App.Vector(15, 10, 0), App.Vector(0, 0, 1), 6), False)
        sketch.addConstraint(Sketcher.Constraint("Radius", circle_index, 6))
        sketch.addConstraint(Sketcher.Constraint("DistanceX", circle_index, 3, 15))
        sketch.addConstraint(Sketcher.Constraint("DistanceY", circle_index, 3, 10))
        doc.recompute()
        process_events(0.1, rounds=16)
        return doc

    if fixture_id == "techdraw-example":
        doc = App.newDocument("ParityTechDraw")
        box = doc.addObject("Part::Box", "Box")
        box.Length = 30
        box.Width = 20
        box.Height = 15

        page = doc.addObject("TechDraw::DrawPage", "Page")
        template = doc.addObject("TechDraw::DrawSVGTemplate", "Template")
        template.Template = TECHDRAW_TEST_TEMPLATE
        page.Template = template

        view = doc.addObject("TechDraw::DrawViewPart", "View")
        page.addView(view)
        view.Source = [box]
        page.Scale = 5.0
        doc.recompute()

        gui_doc = getattr(Gui, "ActiveDocument", None)
        if gui_doc is not None:
            gui_page = gui_doc.getObject(page.Name)
            if gui_page is not None:
                gui_page.show()

        process_events(0.1, rounds=30)
        return doc

    if fixture_id == "multi-body-tree":
        doc = App.newDocument("ParityTree")
        assembly = doc.addObject("App::Part", "Assembly")

        sub_part_a = assembly.newObject("App::Part", "SubPartA")
        box_a = sub_part_a.newObject("Part::Box", "BoxA")
        box_a.Length = 12
        box_a.Width = 8
        box_a.Height = 6

        sub_part_b = assembly.newObject("App::Part", "SubPartB")
        box_b = sub_part_b.newObject("Part::Box", "BoxB")
        box_b.Length = 10
        box_b.Width = 7
        box_b.Height = 5

        loose_group = doc.addObject("App::DocumentObjectGroup", "LooseGroup")
        loose_box = doc.addObject("Part::Box", "LooseBox")
        loose_box.Length = 6
        loose_box.Width = 4
        loose_box.Height = 3
        loose_group.addObject(loose_box)

        doc.recompute()
        process_events(0.1, rounds=16)
        return doc

    if fixture_id == "partdesign-editable-feature":
        return prepare_fixture_document("partdesign-pad-example")

    if fixture_id == "partdesign-movefeature-example":
        doc = App.newDocument("ParityMoveFeature")
        body_source = doc.addObject("PartDesign::Body", "BodySource")
        sketch = doc.addObject("Sketcher::SketchObject", "Sketch")
        body_source.addObject(sketch)
        sketch.AttachmentSupport = (body_source.Origin.OriginFeatures[3], [""])
        sketch.MapMode = "FlatFace"
        add_rectangle_sketch(sketch, (-10, -10), (20, 20))

        pad = doc.addObject("PartDesign::Pad", "Pad")
        body_source.addObject(pad)
        pad.Profile = sketch
        pad.Length = 10

        body_target = doc.addObject("PartDesign::Body", "BodyTarget")
        doc.recompute()

        view = Gui.activeView()
        if view is not None:
            try:
                view.setActiveObject("pdbody", body_source)
            except Exception:
                pass

        process_events(0.1, rounds=16)
        return doc

    if fixture_id == "partdesign-taskpanel-example":
        doc = App.newDocument("ParityTaskPanel")
        body = doc.addObject("PartDesign::Body", "Body")
        body.Label = "Body"
        body.AllowCompound = True
        doc.recompute()

        view = Gui.activeView()
        if view is not None:
            try:
                view.setActiveObject("pdbody", body)
            except Exception:
                pass

        process_events(0.1, rounds=16)
        return doc

    return getattr(App, "ActiveDocument", None)


def resolve_input_path(path_value):
    if not path_value:
        return ""
    if os.path.isabs(path_value):
        return path_value
    return os.path.join(REPO_ROOT, path_value)


def open_step_if_requested(step_file):
    if not step_file:
        return getattr(App, "ActiveDocument", None)
    resolved_step_file = resolve_input_path(step_file)
    if not os.path.isfile(resolved_step_file):
        raise FileNotFoundError(resolved_step_file)
    import_result = ImportGui.open(resolved_step_file)
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

    target_dock = activate_dock_target(main_window)
    if target_dock is not None:
        output = screenshot_path(baseline_id, "tree-property")
        target_dock.grab().save(output)
        return output

    for dock in main_window.findChildren(QtGui.QDockWidget):
        title = dock.windowTitle().lower()
        if "tree" in title or "property" in title or "combo" in title or title == "model":
            output = screenshot_path(baseline_id, "tree-property")
            dock.grab().save(output)
            return output
    return None


def maybe_save_task_panel_crop(main_window, baseline_id):
    if not bool_env("PARITY_CAPTURE_TASK_PANEL"):
        return None

    for dock in main_window.findChildren(QtGui.QDockWidget):
        title = dock.windowTitle().lower()
        if "task" in title:
            output = screenshot_path(baseline_id, "task-panel")
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


def current_active_task():
    gui_doc = getattr(Gui, "ActiveDocument", None)
    if gui_doc is None:
        return None

    try:
        in_edit = gui_doc.getInEdit()
    except Exception:
        in_edit = None

    if in_edit is None:
        return None
    if hasattr(in_edit, "Object") and in_edit.Object is not None:
        return getattr(in_edit.Object, "Name", None) or getattr(in_edit.Object, "TypeId", None)
    return getattr(in_edit, "TypeId", None)


def find_dock_ancestor(widget):
    current = widget
    while current is not None:
        if isinstance(current, QtGui.QDockWidget):
            return current
        current = current.parentWidget()
    return None


def activate_dock_target(main_window):
    target = env("PARITY_CAPTURE_DOCK_TARGET").lower()
    if not target:
        return None

    for tab_widget in main_window.findChildren(QtGui.QTabWidget):
        for index in range(tab_widget.count()):
            label = tab_widget.tabText(index).lower()
            if target in label or (target == "model" and "tree" in label):
                tab_widget.setCurrentIndex(index)
                process_events(0.05, rounds=8)
                return find_dock_ancestor(tab_widget)

    for dock in main_window.findChildren(QtGui.QDockWidget):
        title = dock.windowTitle().lower()
        if target in title or (target == "model" and "tree" in title):
            return dock

    return None


def expand_tree_targets(main_window):
    if not bool_env("PARITY_EXPAND_TREE"):
        return

    dock = activate_dock_target(main_window)
    tree_views = []
    if dock is not None:
        tree_views = dock.findChildren(QtGui.QTreeView)
    if not tree_views:
        tree_views = main_window.findChildren(QtGui.QTreeView)

    for tree_view in tree_views:
        try:
            tree_view.expandAll()
        except Exception:
            pass
    process_events(0.1, rounds=12)


def activate_selection_target(target_name):
    if not target_name:
        return

    active_doc = getattr(App, "ActiveDocument", None)
    if active_doc is None:
        return

    target = active_doc.getObject(target_name)
    if target is None:
        return

    Gui.Selection.clearSelection()
    subelement = env("PARITY_SELECT_SUBELEMENT")
    if subelement:
        Gui.Selection.addSelection(active_doc.Name, target.Name, subelement)
    else:
        Gui.Selection.addSelection(target)
    process_events(0.05, rounds=8)


def apply_selection_emphasis(target_name):
    if not bool_env("PARITY_SELECTION_EMPHASIS") or not target_name:
        return

    active_doc = getattr(App, "ActiveDocument", None)
    if active_doc is None:
        return

    target = active_doc.getObject(target_name)
    if target is None or not hasattr(target, "ViewObject"):
        return

    view_object = target.ViewObject
    try:
        view_object.DisplayMode = "Flat Lines"
    except Exception:
        pass
    try:
        view_object.ShapeColor = (0.55, 0.72, 0.95)
    except Exception:
        pass
    try:
        view_object.LineColor = (0.10, 0.35, 0.80)
    except Exception:
        pass
    try:
        view_object.LineWidth = 3
    except Exception:
        pass
    try:
        view_object.Transparency = 12
    except Exception:
        pass
    process_events(0.05, rounds=8)


def activate_edit_target(target_name):
    if not target_name:
        return

    gui_doc = getattr(Gui, "ActiveDocument", None)
    if gui_doc is None:
        return

    gui_doc.setEdit(target_name)
    process_events(0.1, rounds=16)


def reset_edit_target():
    gui_doc = getattr(Gui, "ActiveDocument", None)
    if gui_doc is None:
        return

    try:
        if gui_doc.getInEdit():
            gui_doc.resetEdit()
            process_events(0.05, rounds=6)
    except Exception:
        pass


def accept_active_modal():
    dialog = QtGui.QApplication.activeModalWidget()
    if dialog is not None:
        QtCore.QTimer.singleShot(0, dialog, QtCore.SLOT("accept()"))


def run_capture_command(command_name):
    if not command_name:
        return

    if bool_env("PARITY_AUTO_ACCEPT_MODAL"):
        delay_ms = 200
        try:
            delay_ms = int(env("PARITY_MODAL_DELAY_MS", "200"))
        except ValueError:
            delay_ms = 200
        QtCore.QTimer.singleShot(delay_ms, accept_active_modal)

    Gui.runCommand(command_name, 0)
    process_events(0.1, rounds=16)


def build_metadata(baseline_id, full_window, viewport_crop, tree_property_crop, task_panel_crop):
    active_doc = getattr(App, "ActiveDocument", None)
    return {
        "$schema": "./metadata-schema.json",
        "baseline_id": baseline_id,
        "theme": env("PARITY_THEME", "unspecified"),
        "workbench": current_workbench_name(),
        "fixture_document": env("PARITY_FIXTURE_DOCUMENT", active_doc.Name if active_doc else "none"),
        "visible_toolbars": collect_visible_toolbars(Gui.getMainWindow()),
        "visible_panels": collect_visible_panels(Gui.getMainWindow()),
        "active_task": current_active_task(),
        "artifacts": {
            "full_window": relative_from_repo(full_window),
            "viewport_crop": relative_from_repo(viewport_crop),
            "tree_property_crop": relative_from_repo(tree_property_crop),
            "task_panel_crop": relative_from_repo(task_panel_crop),
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
    previous_theme = None
    try:
        main_window = Gui.getMainWindow()
        main_window.show()
        main_window.raise_()
        process_events(0.1, rounds=12)

        previous_theme = apply_runtime_theme(env("PARITY_THEME"))

        doc = prepare_fixture_document(env("PARITY_FIXTURE_DOCUMENT"))
        activate_workbench(env("PARITY_WORKBENCH"))
        step_doc = open_step_if_requested(env("PARITY_STEP_FILE"))
        if step_doc is not None:
            doc = step_doc
        activate_selection_target(env("PARITY_SELECT_OBJECT"))
        apply_selection_emphasis(env("PARITY_SELECT_OBJECT"))
        activate_edit_target(env("PARITY_EDIT_OBJECT"))
        run_capture_command(env("PARITY_RUN_COMMAND"))
        expand_tree_targets(main_window)
        process_events(0.1, rounds=16)

        full_window = save_main_window_capture(main_window, baseline_id)
        viewport_crop = maybe_save_viewport_capture(baseline_id)
        tree_property_crop = maybe_save_dock_crop(main_window, baseline_id)
        task_panel_crop = maybe_save_task_panel_crop(main_window, baseline_id)
        metadata = build_metadata(baseline_id, full_window, viewport_crop, tree_property_crop, task_panel_crop)
        metadata_output = write_metadata(baseline_id, metadata)

        print("baseline-id=" + baseline_id)
        print("full-window=" + full_window)
        print("viewport=" + str(viewport_crop))
        print("tree-property=" + str(tree_property_crop))
        print("task-panel=" + str(task_panel_crop))
        print("metadata=" + metadata_output)
        return 0
    except Exception as exc:
        print("FAIL: parity capture failed: " + repr(exc))
        print(traceback.format_exc())
        return 1
    finally:
        reset_edit_target()
        if doc is not None:
            try:
                App.closeDocument(doc.Name)
                process_events(0.05, rounds=4)
            except Exception:
                pass
        restore_runtime_theme(previous_theme)


if __name__ == "__main__":
    exit_with(main())