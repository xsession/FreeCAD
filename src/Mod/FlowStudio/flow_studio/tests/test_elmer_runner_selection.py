# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Tests for Elmer runner command selection without requiring FreeCAD runtime."""

import io
import os
import sys
import tempfile
import types
import unittest
from types import SimpleNamespace
from unittest.mock import patch


class _Console:
    def PrintMessage(self, *_args, **_kwargs):
        pass

    def PrintWarning(self, *_args, **_kwargs):
        pass

    def PrintError(self, *_args, **_kwargs):
        pass


if "FreeCAD" not in sys.modules:
    sys.modules["FreeCAD"] = types.SimpleNamespace(
        Console=_Console(),
        ActiveDocument=types.SimpleNamespace(TransientDir=tempfile.gettempdir()),
    )

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from flow_studio.solvers.elmer_runner import ElmerRunner


class _FakeProcess:
    def __init__(self):
        self.stdout = io.BytesIO(b"")
        self.returncode = 0

    def wait(self):
        return self.returncode


class TestElmerRunnerSelection(unittest.TestCase):
    def _make_runner(self, temp_dir, num_processors=1, solver_binary="ElmerSolver"):
        solver = SimpleNamespace(
            FlowType="FlowStudio::Solver",
            NumProcessors=num_processors,
            ElmerSolverBinary=solver_binary,
        )
        analysis = SimpleNamespace(
            Name="TestAnalysis",
            CaseDir=temp_dir,
            Group=[solver],
            PhysicsDomain="Thermal",
        )
        return ElmerRunner(analysis, solver)

    def test_prefers_serial_solver_by_default(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            runner = self._make_runner(temp_dir)
            with patch("flow_studio.solvers.elmer_runner.shutil.which") as mock_which, \
                    patch("flow_studio.solvers.elmer_runner.subprocess.Popen") as mock_popen:
                mock_which.side_effect = lambda name: f"/fake/{name}"
                mock_popen.return_value = _FakeProcess()

                runner.run()

            command = mock_popen.call_args.args[0]
            self.assertEqual(command, ["/fake/ElmerSolver"])

    def test_uses_explicit_mpi_solver_when_requested(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            runner = self._make_runner(temp_dir, num_processors=4, solver_binary="ElmerSolver_mpi")
            with patch.object(runner, "_partition_mesh", return_value=True), \
                    patch("flow_studio.solvers.elmer_runner.shutil.which") as mock_which, \
                    patch("flow_studio.solvers.elmer_runner.subprocess.Popen") as mock_popen:
                mapping = {
                    "ElmerSolver_mpi": "/fake/ElmerSolver_mpi",
                    "mpirun": "/fake/mpirun",
                    "mpiexec": None,
                    "ElmerSolver": "/fake/ElmerSolver",
                }
                mock_which.side_effect = lambda name: mapping.get(name)
                mock_popen.return_value = _FakeProcess()

                runner.run()

            command = mock_popen.call_args.args[0]
            self.assertEqual(
                command,
                ["/fake/mpirun", "-np", "4", "/fake/ElmerSolver_mpi"],
            )

    def test_falls_back_to_serial_when_mpi_binary_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            runner = self._make_runner(temp_dir, num_processors=3, solver_binary="ElmerSolver_mpi")
            with patch.object(runner, "_partition_mesh", return_value=True), \
                    patch("flow_studio.solvers.elmer_runner.shutil.which") as mock_which, \
                    patch("flow_studio.solvers.elmer_runner.subprocess.Popen") as mock_popen:
                mapping = {
                    "ElmerSolver_mpi": None,
                    "ElmerSolver": "/fake/ElmerSolver",
                }
                mock_which.side_effect = lambda name: mapping.get(name)
                mock_popen.return_value = _FakeProcess()

                runner.run()

            command = mock_popen.call_args.args[0]
            self.assertEqual(command, ["/fake/ElmerSolver"])


if __name__ == "__main__":
    unittest.main()