# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

from __future__ import annotations

import importlib
import os
import sys
import time
import types
import unittest
from unittest import mock


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class _FakeStdout:
    def __init__(self, lines):
        self._lines = list(lines)

    def readline(self):
        if self._lines:
            return self._lines.pop(0)
        return ""


class _FakeProcess:
    def __init__(self, lines, return_code=0, pid=1234):
        self.stdout = _FakeStdout(lines)
        self._return_code = return_code
        self.pid = pid
        self._terminated = False

    def wait(self):
        return self._return_code

    def poll(self):
        return None if not self._terminated and self._return_code == 0 else self._return_code

    def terminate(self):
        self._terminated = True


class TestRuntimeMonitor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._freecad_stub = types.SimpleNamespace(ActiveDocument=None)
        cls._patcher = mock.patch.dict(sys.modules, {"FreeCAD": cls._freecad_stub})
        cls._patcher.start()
        cls.runtime_monitor = importlib.import_module("flow_studio.runtime.monitor")

    @classmethod
    def tearDownClass(cls):
        cls._patcher.stop()
        sys.modules.pop("flow_studio.runtime.monitor", None)

    def test_register_run_captures_progress_and_results(self):
        analysis = types.SimpleNamespace(Name="Analysis001")
        solver = types.SimpleNamespace(SolverBackend="OpenFOAM", MaxIterations=10)
        runner = types.SimpleNamespace(
            process=_FakeProcess(["Time = 0.1\n", "Time = 0.2\n", "Writing fields\n"]),
            case_dir="C:/tmp/case",
            read_results=lambda: "C:/tmp/case/100",
        )

        self.runtime_monitor.register_run(analysis, solver, runner)
        time.sleep(0.05)
        snapshot = self.runtime_monitor.get_run_snapshot(analysis)

        self.assertEqual(snapshot["status"], "FINISHED")
        self.assertEqual(snapshot["backend"], "OpenFOAM")
        self.assertEqual(snapshot["result_path"], "C:/tmp/case/100")
        self.assertTrue(any("Time =" in line for line in snapshot["log_tail"]))

    def test_sync_post_pipeline_populates_result_object(self):
        created = []

        class _FakePipeline:
            FlowType = "FlowStudio::PostPipeline"

            def __init__(self):
                self.Analysis = None
                self.ResultFile = ""
                self.ResultFormat = ""
                self.AvailableFields = []
                self.ActiveField = ""

        class _FakeAnalysis:
            def __init__(self):
                self.Name = "AnalysisSync"
                self.Group = []
                self.Document = object()

            def addObject(self, obj):
                self.Group.append(obj)

        analysis = _FakeAnalysis()

        def _make_post_pipeline(_doc):
            pipeline = _FakePipeline()
            created.append(pipeline)
            return pipeline

        snapshot = {
            "result_path": "C:/tmp/result.vtk",
            "result_format": "VTK",
            "backend": "OpenFOAM",
        }

        with mock.patch.dict(
            sys.modules,
            {"flow_studio.ObjectsFlowStudio": types.SimpleNamespace(makePostPipeline=_make_post_pipeline)},
        ):
            pipeline = self.runtime_monitor.sync_post_pipeline(analysis, snapshot=snapshot)

        self.assertIsNotNone(pipeline)
        self.assertEqual(pipeline.ResultFile, "C:/tmp/result.vtk")
        self.assertEqual(pipeline.ResultFormat, "VTK")
        self.assertIn("U", list(pipeline.AvailableFields))
        self.assertEqual(len(created), 1)


if __name__ == "__main__":
    unittest.main()
