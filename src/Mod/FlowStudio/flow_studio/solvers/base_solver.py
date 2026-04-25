# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Base solver interface – defines the contract every solver backend must satisfy."""

import os
import FreeCAD

from flow_studio.solver_deps import find_executable


class BaseSolverRunner:
    """Abstract base class for CFD solver backends.

    Every solver backend must implement:
    - ``check()``      – validate that the solver is available
    - ``write_case()`` – generate all input files
    - ``run()``        – launch the solver process
    - ``read_results()`` – parse results back into FreeCAD
    """

    name = "BaseSolver"

    def __init__(self, analysis, solver_obj):
        self.analysis = analysis
        self.solver_obj = solver_obj
        self.case_dir = self._get_case_dir()
        self.process = None

    def _get_case_dir(self):
        """Return or create the solver working directory."""
        if self.analysis.CaseDir:
            d = self.analysis.CaseDir
        else:
            d = os.path.join(
                FreeCAD.ActiveDocument.TransientDir,
                "FlowStudio",
                self.analysis.Name,
            )
        os.makedirs(d, exist_ok=True)
        return d

    def check(self):
        """Check that the solver executable is available."""
        raise NotImplementedError

    def _resolve_executable(self, name, backend_name=None, extra_paths=None):
        """Resolve an executable from PATH or FlowStudio-managed solver artifacts."""
        path, _version = find_executable(
            name,
            extra_paths=extra_paths,
            backend_name=backend_name,
        )
        return path

    def write_case(self):
        """Write all input / case files for the solver."""
        raise NotImplementedError

    def run(self):
        """Execute the solver (blocking or threaded)."""
        raise NotImplementedError

    def read_results(self):
        """Read solver results and attach them to the analysis."""
        raise NotImplementedError

    def stop(self):
        """Terminate a running solver process."""
        if self.process and self.process.poll() is None:
            self.process.terminate()
