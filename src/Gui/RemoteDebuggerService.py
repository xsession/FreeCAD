import importlib


def read_preferences(prefs):
    return {
        "tab_index": prefs.GetInt("TabIndex", 0),
        "address": prefs.GetString("VSCodeAddress", "localhost"),
        "port": prefs.GetInt("VSCodePort", 5678),
    }


def attach_debugger(settings, prefs, *, rpdb2_module=None, debugpy_module=None, python_exe_getter=None):
    index = settings.get("tab_index", 0)
    prefs.SetInt("TabIndex", index)

    if index == 0:
        if rpdb2_module is None:
            rpdb2_module = importlib.import_module("rpdb2")

        rpdb2_module.start_embedded_debugger(settings.get("password", ""), timeout=30)
        return

    if index == 1:
        address = settings.get("address", "localhost")
        port = settings.get("port", 5678)
        prefs.SetString("VSCodeAddress", address)
        prefs.SetInt("VSCodePort", port)

        if debugpy_module is None:
            debugpy_module = importlib.import_module("debugpy")

        if python_exe_getter is None:
            from freecad.utils import get_python_exe as python_exe_getter

        debugpy_module.configure(python=python_exe_getter())
        debugpy_module.listen((address, port))
        debugpy_module.wait_for_client()