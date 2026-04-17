import importlib
import sys
import types
import unittest


class _FakeDoc:
    def __init__(self, name):
        self.Name = name


class TestProjectStore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if "FreeCAD" not in sys.modules:
            sys.modules["FreeCAD"] = types.SimpleNamespace(ActiveDocument=None)

    def setUp(self):
        self.freecad = sys.modules["FreeCAD"]
        self.freecad.ActiveDocument = _FakeDoc("DocA")
        self.project_store = importlib.import_module("App.project_store")
        self.project_store._MODELS_BY_DOC.clear()
        self.project_store._OBSERVERS.clear()

    def tearDown(self):
        self.project_store._MODELS_BY_DOC.clear()
        self.project_store._OBSERVERS.clear()

    def test_get_active_model_creates_per_document(self):
        model_a = self.project_store.get_active_model()
        self.assertEqual(model_a.project.project_id, "DocA")

        self.freecad.ActiveDocument = _FakeDoc("DocB")
        model_b = self.project_store.get_active_model()
        self.assertEqual(model_b.project.project_id, "DocB")
        self.assertNotEqual(model_a.project.project_id, model_b.project.project_id)

    def test_observer_runtime_error_is_removed(self):
        calls = {"ok": 0, "bad": 0}

        def ok_callback():
            calls["ok"] += 1

        def bad_callback():
            calls["bad"] += 1
            raise RuntimeError("stale panel")

        self.project_store.register_observer(ok_callback)
        self.project_store.register_observer(bad_callback)

        self.project_store.notify_changed()
        self.project_store.notify_changed()

        self.assertEqual(calls["ok"], 2)
        self.assertEqual(calls["bad"], 1)

    def test_unregister_observer(self):
        calls = {"ok": 0}

        def ok_callback():
            calls["ok"] += 1

        self.project_store.register_observer(ok_callback)
        self.project_store.unregister_observer(ok_callback)
        self.project_store.notify_changed()

        self.assertEqual(calls["ok"], 0)


if __name__ == "__main__":
    unittest.main()
