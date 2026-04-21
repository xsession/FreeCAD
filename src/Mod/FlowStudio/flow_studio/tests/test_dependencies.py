# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Comprehensive tests for the solver dependency manager.

All tests run WITHOUT real executables by mocking shutil.which and
subprocess.run — so they pass on any CI/CD machine.
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestDependencyStatus(unittest.TestCase):
    """Test the DependencyStatus dataclass."""

    def test_ok_when_found(self):
        from flow_studio.solver_deps import DependencyStatus
        ds = DependencyStatus(
            name="simpleFoam", kind="executable", required=True,
            found=True, path="/usr/bin/simpleFoam", version="v2306",
        )
        self.assertTrue(ds.ok)
        self.assertTrue(ds.found)

    def test_ok_when_optional_missing(self):
        from flow_studio.solver_deps import DependencyStatus
        ds = DependencyStatus(
            name="paraFoam", kind="executable", required=False,
            found=False,
        )
        self.assertTrue(ds.ok)  # optional, so still ok

    def test_not_ok_when_required_missing(self):
        from flow_studio.solver_deps import DependencyStatus
        ds = DependencyStatus(
            name="ElmerSolver", kind="executable", required=True,
            found=False,
        )
        self.assertFalse(ds.ok)
        self.assertFalse(ds.found)

    def test_default_values(self):
        from flow_studio.solver_deps import DependencyStatus
        ds = DependencyStatus(
            name="test", kind="executable", required=True, found=False,
        )
        self.assertEqual(ds.path, "")
        self.assertEqual(ds.version, "")
        self.assertEqual(ds.hint, "")


class TestBackendReport(unittest.TestCase):
    """Test the BackendReport dataclass."""

    def test_available_when_all_required_met(self):
        from flow_studio.solver_deps import BackendReport, DependencyStatus
        deps = [
            DependencyStatus("a", "executable", True, True),
            DependencyStatus("b", "executable", False, False),
        ]
        report = BackendReport(backend="Test", available=True, deps=deps)
        self.assertTrue(report.available)
        self.assertEqual(len(report.missing_required), 0)
        self.assertEqual(len(report.missing_optional), 1)

    def test_unavailable_when_required_missing(self):
        from flow_studio.solver_deps import BackendReport, DependencyStatus
        deps = [
            DependencyStatus("a", "executable", True, False),
            DependencyStatus("b", "executable", True, True),
        ]
        report = BackendReport(backend="Test", available=False, deps=deps)
        self.assertFalse(report.available)
        self.assertEqual(len(report.missing_required), 1)
        self.assertEqual(report.missing_required[0].name, "a")

    def test_summary_output(self):
        from flow_studio.solver_deps import BackendReport, DependencyStatus
        deps = [
            DependencyStatus("ElmerSolver", "executable", True, True,
                             path="/usr/bin/ElmerSolver", version="9.0"),
            DependencyStatus("ElmerGrid", "executable", True, False,
                             hint="Install Elmer FEM"),
        ]
        report = BackendReport(backend="Elmer", available=False, deps=deps)
        summary = report.summary()
        self.assertIn("Elmer", summary)
        self.assertIn("UNAVAILABLE", summary)
        self.assertIn("+ ElmerSolver", summary)   # found dep
        self.assertIn("X ElmerGrid", summary)   # missing required dep

    def test_empty_deps(self):
        from flow_studio.solver_deps import BackendReport
        report = BackendReport(backend="Empty", available=True)
        self.assertEqual(len(report.deps), 0)
        self.assertEqual(len(report.missing_required), 0)
        self.assertEqual(len(report.missing_optional), 0)


class TestFindExecutable(unittest.TestCase):
    """Test find_executable with mocked shutil.which."""

    @patch("flow_studio.solver_deps.shutil.which")
    def test_found_on_path(self, mock_which):
        from flow_studio.solver_deps import find_executable
        mock_which.return_value = "/usr/bin/ElmerSolver"
        with patch("flow_studio.solver_deps._detect_version", return_value="9.0"):
            path, ver = find_executable("ElmerSolver")
        self.assertIn("ElmerSolver", path)
        self.assertEqual(ver, "9.0")

    @patch("flow_studio.solver_deps.shutil.which")
    def test_not_found(self, mock_which):
        from flow_studio.solver_deps import find_executable
        mock_which.return_value = None
        path, ver = find_executable("nonexistent_binary_xyz")
        self.assertIsNone(path)
        self.assertEqual(ver, "")

    @patch("flow_studio.solver_deps.shutil.which")
    @patch("flow_studio.solver_deps.os.path.isdir")
    @patch("flow_studio.solver_deps.os.path.isfile")
    @patch("flow_studio.solver_deps.os.access")
    def test_found_in_extra_dir(self, mock_access, mock_isfile, mock_isdir, mock_which):
        from flow_studio.solver_deps import find_executable
        mock_which.return_value = None
        mock_isdir.return_value = True

        def isfile_side(p):
            return "ElmerSolver" in p and p.endswith(".exe")
        mock_isfile.side_effect = isfile_side
        mock_access.return_value = True

        with patch("flow_studio.solver_deps._detect_version", return_value=""):
            path, ver = find_executable("ElmerSolver",
                                        extra_paths=[r"C:\FakeElmer\bin"])
        self.assertIsNotNone(path)
        self.assertIn("ElmerSolver", path)


class TestFindPythonPackage(unittest.TestCase):
    """Test find_python_package."""

    def test_finds_existing_module(self):
        from flow_studio.solver_deps import find_python_package
        found, loc, ver = find_python_package("os")
        self.assertTrue(found)

    def test_missing_module(self):
        from flow_studio.solver_deps import find_python_package
        found, loc, ver = find_python_package("nonexistent_pkg_xyzzy_42")
        self.assertFalse(found)
        self.assertEqual(loc, "")

    def test_finds_unittest(self):
        from flow_studio.solver_deps import find_python_package
        found, loc, ver = find_python_package("unittest")
        self.assertTrue(found)


class TestCheckBackend(unittest.TestCase):
    """Test check_backend with mocked dependency detection."""

    @patch("flow_studio.solver_deps.find_executable")
    def test_openfoam_all_found(self, mock_find):
        from flow_studio.solver_deps import check_backend
        mock_find.return_value = ("/usr/bin/simpleFoam", "v2306")
        report = check_backend("OpenFOAM")
        self.assertTrue(report.available)
        self.assertEqual(report.backend, "OpenFOAM")
        # simpleFoam is the only required one
        req_deps = [d for d in report.deps if d.required]
        self.assertTrue(all(d.found for d in req_deps))

    @patch("flow_studio.solver_deps.find_executable")
    def test_openfoam_missing_simplefoam(self, mock_find):
        from flow_studio.solver_deps import check_backend
        mock_find.return_value = (None, "")
        report = check_backend("OpenFOAM")
        self.assertFalse(report.available)
        self.assertGreater(len(report.missing_required), 0)

    @patch("flow_studio.solver_deps.find_executable")
    def test_elmer_all_found(self, mock_find):
        from flow_studio.solver_deps import check_backend
        mock_find.return_value = ("/usr/bin/ElmerSolver", "9.0")
        report = check_backend("Elmer")
        self.assertTrue(report.available)
        req_names = {d.name for d in report.deps if d.required}
        self.assertIn("ElmerSolver", req_names)
        self.assertIn("ElmerGrid", req_names)

    def test_elmer_dependency_list_does_not_require_gui(self):
        from flow_studio.solver_deps import _BACKEND_DEPS
        dep_names = {name for name, _kind, _required, _hint in _BACKEND_DEPS["Elmer"]}
        self.assertNotIn("ElmerGUI", dep_names)

    @patch("flow_studio.solver_deps.find_executable")
    def test_elmer_missing_grid(self, mock_find):
        from flow_studio.solver_deps import check_backend

        def selective_find(name, extra_paths=None):
            if name == "ElmerSolver":
                return ("/usr/bin/ElmerSolver", "9.0")
            return (None, "")

        mock_find.side_effect = selective_find
        report = check_backend("Elmer")
        self.assertFalse(report.available)

    @patch("flow_studio.solver_deps.find_executable")
    def test_fluidx3d_not_found(self, mock_find):
        from flow_studio.solver_deps import check_backend
        mock_find.return_value = (None, "")
        report = check_backend("FluidX3D")
        self.assertFalse(report.available)

    def test_unknown_backend(self):
        from flow_studio.solver_deps import check_backend
        report = check_backend("NonExistentSolver")
        self.assertFalse(report.available)
        self.assertIn("Unknown", report.message)

    def test_meshing_backend(self):
        from flow_studio.solver_deps import check_backend
        report = check_backend("Meshing")
        # gmsh python package may or may not be present
        self.assertIsInstance(report.available, bool)
        dep_names = {d.name for d in report.deps}
        self.assertIn("gmsh", dep_names)

    def test_postprocessing_backend(self):
        from flow_studio.solver_deps import check_backend
        report = check_backend("PostProcessing")
        # All deps are optional
        dep_names = {d.name for d in report.deps}
        self.assertIn("numpy", dep_names)
        self.assertIn("vtk", dep_names)
        # No required deps → always available
        self.assertTrue(report.available)


class TestCheckAll(unittest.TestCase):
    """Test check_all aggregation."""

    @patch("flow_studio.solver_deps.find_executable", return_value=(None, ""))
    def test_check_all_returns_all_backends(self, mock_find):
        from flow_studio.solver_deps import check_all
        reports = check_all()
        self.assertIn("OpenFOAM", reports)
        self.assertIn("FluidX3D", reports)
        self.assertIn("Elmer", reports)
        self.assertIn("Meshing", reports)
        self.assertIn("PostProcessing", reports)

    @patch("flow_studio.solver_deps.find_executable", return_value=(None, ""))
    def test_check_all_returns_backend_reports(self, mock_find):
        from flow_studio.solver_deps import check_all, BackendReport
        reports = check_all()
        for name, report in reports.items():
            self.assertIsInstance(report, BackendReport)
            self.assertEqual(report.backend, name)


class TestInstallHint(unittest.TestCase):
    """Test install_hint generation."""

    @patch("flow_studio.solver_deps.find_executable", return_value=(None, ""))
    def test_elmer_install_hint(self, mock_find):
        from flow_studio.solver_deps import install_hint
        text = install_hint("Elmer")
        self.assertIn("Elmer", text)
        self.assertIn("REQUIRED", text)
        self.assertIn("ElmerSolver", text)

    @patch("flow_studio.solver_deps.find_executable",
           return_value=("/usr/bin/simpleFoam", "v2306"))
    def test_satisfied_returns_short_message(self, mock_find):
        from flow_studio.solver_deps import install_hint
        text = install_hint("OpenFOAM")
        self.assertIn("satisfied", text.lower())


class TestStatusDict(unittest.TestCase):
    """Test JSON-serializable status dict."""

    @patch("flow_studio.solver_deps.find_executable", return_value=(None, ""))
    def test_status_dict_structure(self, mock_find):
        from flow_studio.solver_deps import status_dict
        d = status_dict()
        self.assertIsInstance(d, dict)
        for backend_name, info in d.items():
            self.assertIn("available", info)
            self.assertIn("deps", info)
            self.assertIsInstance(info["deps"], list)
            for dep in info["deps"]:
                self.assertIn("name", dep)
                self.assertIn("kind", dep)
                self.assertIn("required", dep)
                self.assertIn("found", dep)


class TestExtraDirs(unittest.TestCase):
    """Test that _extra_dirs respects environment variables."""

    @patch.dict(os.environ, {"ELMER_HOME": "/opt/elmer"})
    def test_elmer_home(self):
        from flow_studio.solver_deps import _extra_dirs
        dirs = _extra_dirs()
        self.assertTrue(any("elmer" in d for d in dirs))

    @patch.dict(os.environ, {"FOAM_APPBIN": "/opt/openfoam/bin"})
    def test_foam_appbin(self):
        from flow_studio.solver_deps import _extra_dirs
        dirs = _extra_dirs()
        self.assertTrue(any("openfoam" in d for d in dirs))

    @patch.dict(os.environ, {}, clear=False)
    def test_returns_list(self):
        from flow_studio.solver_deps import _extra_dirs
        dirs = _extra_dirs()
        self.assertIsInstance(dirs, list)


class TestDetectVersion(unittest.TestCase):
    """Test _detect_version with mocked subprocess."""

    def test_version_from_stdout(self):
        import subprocess as _sp
        from flow_studio.solver_deps import _detect_version
        mock_result = MagicMock()
        mock_result.stdout = "ElmerSolver v9.0 (Build 123)\n"
        mock_result.stderr = ""
        with patch.object(_sp, "run", return_value=mock_result):
            ver = _detect_version("/usr/bin/ElmerSolver", "ElmerSolver")
        self.assertIn("ElmerSolver", ver)

    def test_version_from_stderr(self):
        import subprocess as _sp
        from flow_studio.solver_deps import _detect_version
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = "gmsh 4.11.1\n"
        with patch.object(_sp, "run", return_value=mock_result):
            ver = _detect_version("/usr/bin/gmsh", "gmsh")
        self.assertIn("gmsh", ver)

    def test_version_detection_failure(self):
        import subprocess as _sp
        from flow_studio.solver_deps import _detect_version
        with patch.object(_sp, "run", side_effect=Exception("boom")):
            ver = _detect_version("/fake/path", "fake")
        self.assertEqual(ver, "")


class TestBackendDepsDefinitions(unittest.TestCase):
    """Test that _BACKEND_DEPS is well-formed."""

    def test_all_backends_have_deps(self):
        from flow_studio.solver_deps import _BACKEND_DEPS
        for name, defs in _BACKEND_DEPS.items():
            self.assertIsInstance(defs, list, f"{name} should have a list of deps")
            self.assertGreater(len(defs), 0, f"{name} should have at least one dep")

    def test_dep_tuples_have_four_elements(self):
        from flow_studio.solver_deps import _BACKEND_DEPS
        for name, defs in _BACKEND_DEPS.items():
            for dep_def in defs:
                self.assertEqual(len(dep_def), 4,
                                 f"{name}: dep {dep_def} should be (name, kind, required, hint)")

    def test_dep_kinds_valid(self):
        from flow_studio.solver_deps import _BACKEND_DEPS
        valid_kinds = {"executable", "python_package", "python_optional"}
        for name, defs in _BACKEND_DEPS.items():
            for dep_name, kind, req, hint in defs:
                self.assertIn(kind, valid_kinds,
                              f"{name}/{dep_name}: invalid kind '{kind}'")

    def test_required_is_bool(self):
        from flow_studio.solver_deps import _BACKEND_DEPS
        for name, defs in _BACKEND_DEPS.items():
            for dep_name, kind, req, hint in defs:
                self.assertIsInstance(req, bool,
                                     f"{name}/{dep_name}: required should be bool")

    def test_hints_are_strings(self):
        from flow_studio.solver_deps import _BACKEND_DEPS
        for name, defs in _BACKEND_DEPS.items():
            for dep_name, kind, req, hint in defs:
                self.assertIsInstance(hint, str,
                                     f"{name}/{dep_name}: hint should be str")
                if req:
                    self.assertGreater(len(hint), 0,
                                       f"{name}/{dep_name}: required deps must have hints")


class TestPrintReport(unittest.TestCase):
    """Test print_report doesn't crash."""

    @patch("flow_studio.solver_deps.find_executable", return_value=(None, ""))
    def test_print_report_runs(self, mock_find):
        from flow_studio.solver_deps import print_report
        from io import StringIO
        import contextlib
        f = StringIO()
        with contextlib.redirect_stdout(f):
            print_report()
        output = f.getvalue()
        self.assertIn("FlowStudio Solver Dependency Report", output)
        self.assertIn("OpenFOAM", output)
        self.assertIn("Elmer", output)


if __name__ == "__main__":
    unittest.main()
