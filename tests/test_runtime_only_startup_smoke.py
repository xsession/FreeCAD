"""Smoke test for GUI runtime-only startup.

Run with the repository launcher:

    set FREECAD_SHELL_MODE=runtime-only
    run_freecad.bat tests\test_runtime_only_startup_smoke.py
"""

from __future__ import annotations

import os
import json
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


def exit_with(code):
    app = QtGui.QApplication.instance()
    if app is not None:
        QtCore.QTimer.singleShot(0, lambda: app.exit(code))
        process_events(0.05, rounds=4)
    raise SystemExit(code)


def sentinel_path():
    return os.path.join(os.environ.get("TEMP", os.getcwd()), "FreeCAD", "runtime-only-smoke.json")


def write_sentinel(payload):
    path = sentinel_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def main():
    shell_mode = os.environ.get("FREECAD_SHELL_MODE", "<unset>")
    print("FREECAD_SHELL_MODE=" + shell_mode)

    app = QtGui.QApplication.instance()
    if app is None:
        write_sentinel({"status": "no-qapplication", "shell_mode": shell_mode})
        print("FAIL: QApplication instance was not created")
        return 1

    if not App.GuiUp:
        write_sentinel({"status": "gui-not-up", "shell_mode": shell_mode})
        print("FAIL: FreeCAD GUI runtime is not marked active")
        return 1

    process_events(0.1, rounds=8)

    main_window = None
    main_window_error = None
    try:
        main_window = Gui.getMainWindow()
    except Exception as exc:
        main_window_error = exc

    if main_window is not None:
        title = ""
        try:
            title = main_window.windowTitle()
        except Exception:
            title = "<unavailable>"
        write_sentinel({
            "status": "main-window-present",
            "shell_mode": shell_mode,
            "window_title": title,
        })
        print("FAIL: runtime-only startup exposed a Qt main window: " + title)
        return 1

    top_level_widgets = [
        widget.metaObject().className()
        for widget in app.topLevelWidgets()
        if widget is not None
    ]
    write_sentinel({
        "status": "ok",
        "shell_mode": shell_mode,
        "top_level_widgets": sorted(top_level_widgets),
        "workbench_count": len(Gui.listWorkbenches()),
    })
    print("TOP_LEVEL_WIDGETS=" + ",".join(sorted(top_level_widgets)))
    if main_window_error is not None:
        print("GET_MAIN_WINDOW_ERROR=" + str(main_window_error))
    print("WORKBENCH_COUNT=" + str(len(Gui.listWorkbenches())))
    return 0


if __name__ == "__main__":
    exit_with(main())