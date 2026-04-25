# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Tests for FlowStudio solver artifact discovery without FreeCAD runtime."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from flow_studio.enterprise.services.process_executor import LocalProcessExecutor
from flow_studio.solver_deps import find_executable


class TestSolverArtifactResolution(unittest.TestCase):
    def test_find_executable_prefers_configured_artifact_root(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_root = Path(temp_dir) / "elmer-build"
            artifact_dir = artifact_root / "bin"
            artifact_dir.mkdir(parents=True)
            exe = artifact_dir / ("ElmerSolver.exe" if os.name == "nt" else "ElmerSolver")
            exe.write_text("", encoding="utf-8")

            with patch.dict(os.environ, {"FLOWSTUDIO_SOLVER_ARTIFACTS": str(artifact_root)}, clear=False), \
                    patch("flow_studio.solver_deps.shutil.which", return_value=None), \
                    patch("flow_studio.solver_deps._detect_version", return_value="test-version"):
                path, version = find_executable("ElmerSolver", backend_name="Elmer")

            self.assertEqual(path, str(exe.resolve()))
            self.assertEqual(version, "test-version")

    def test_local_process_executor_uses_solver_artifact_resolution(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_root = Path(temp_dir) / "fluidx3d"
            artifact_dir = artifact_root / "build" / "Release"
            artifact_dir.mkdir(parents=True)
            exe = artifact_dir / ("FluidX3D.exe" if os.name == "nt" else "FluidX3D")
            exe.write_text("", encoding="utf-8")

            with patch.dict(os.environ, {"FLOWSTUDIO_SOLVER_ARTIFACTS": str(artifact_root)}, clear=False), \
                    patch("flow_studio.enterprise.services.process_executor.shutil.which", return_value=None):
                resolved = LocalProcessExecutor._resolve_executable("FluidX3D")

            self.assertEqual(resolved, str(exe.resolve()))


if __name__ == "__main__":
    unittest.main()