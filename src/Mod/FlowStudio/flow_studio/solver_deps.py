# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Solver dependency manager – automatic detection, validation, and
installation guidance for external solver toolchains.

Each solver backend (OpenFOAM, FluidX3D, Elmer, GMSH) has a set of
required executables, optional executables, and Python packages.  This
module provides:

- :func:`check_all`       – scan every registered solver
- :func:`check_backend`   – scan one backend
- :func:`find_executable`  – robust PATH + common-location search
- :func:`install_hint`     – human-readable install instructions
- :class:`DependencyStatus` – per-dependency result
- :class:`BackendReport`    – aggregated report for one backend
"""

import os
import platform
import shutil
import importlib
from functools import lru_cache
from dataclasses import dataclass, field

from flow_studio.runtime.artifacts import artifact_search_dirs, resolve_solver_artifact


# ======================================================================
# Data structures
# ======================================================================

@dataclass
class DependencyStatus:
    """Status of a single dependency (executable or Python package)."""
    name: str
    kind: str          # "executable" | "python_package" | "python_optional"
    required: bool
    found: bool
    path: str = ""     # resolved path (for executables) or module location
    version: str = ""  # version string if detectable
    hint: str = ""     # install hint if missing

    @property
    def ok(self):
        return self.found or not self.required


@dataclass
class BackendReport:
    """Aggregated dependency report for one solver backend."""
    backend: str
    available: bool
    deps: list = field(default_factory=list)   # list[DependencyStatus]
    message: str = ""

    @property
    def missing_required(self):
        return [d for d in self.deps if d.required and not d.found]

    @property
    def missing_optional(self):
        return [d for d in self.deps if not d.required and not d.found]

    def summary(self):
        lines = [f"Backend: {self.backend}  -  "
                 f"{'AVAILABLE' if self.available else 'UNAVAILABLE'}"]
        for d in self.deps:
            mark = "+" if d.found else ("X" if d.required else "o")
            loc = f"  ({d.path})" if d.path else ""
            ver = f"  [{d.version}]" if d.version else ""
            lines.append(f"  {mark} {d.name} ({d.kind}){loc}{ver}")
            if not d.found and d.hint:
                lines.append(f"      hint: {d.hint}")
        return "\n".join(lines)


# ======================================================================
# Executable search
# ======================================================================

_VERSION_FLAGS = {
    "gmsh": ("--version",),
    "paraview": ("--version",),
}

_VERSION_DETECT_TIMEOUT = 1.0

# Common installation locations beyond PATH
_COMMON_DIRS = {
    "Windows": [
        r"C:\Program Files\ElmerFEM",
        r"C:\Program Files (x86)\ElmerFEM",
        r"C:\Program Files\ElmerFEM\bin",
        r"C:\OpenFOAM",
        r"C:\Program Files\GMSH",
        r"C:\Program Files\gmsh",
    ],
    "Linux": [
        "/usr/bin",
        "/usr/local/bin",
        "/opt/openfoam/bin",
        "/opt/elmer/bin",
        "/snap/bin",
    ],
    "Darwin": [
        "/usr/local/bin",
        "/opt/homebrew/bin",
        "/opt/elmer/bin",
        "/Applications/Elmer.app/Contents/bin",
    ],
}


def _extra_dirs():
    """Return platform-specific extra search directories."""
    system = platform.system()
    dirs = list(_COMMON_DIRS.get(system, []))
    # Respect env vars
    for env in ("ELMER_HOME", "FOAM_APPBIN", "OPENFOAM_DIR",
                "GMSH_BIN", "FLUIDX3D_DIR"):
        val = os.environ.get(env, "")
        if val:
            dirs.append(val)
            dirs.append(os.path.join(val, "bin"))
    # Also search inside pixi/conda environments
    for env in ("CONDA_PREFIX", "PIXI_PROJECT_MANIFEST"):
        val = os.environ.get(env, "")
        if val:
            base = val if os.path.isdir(val) else os.path.dirname(val)
            dirs.append(os.path.join(base, "bin"))
            dirs.append(os.path.join(base, "Library", "bin"))  # Windows conda
    return dirs


def find_executable(name, extra_paths=None, backend_name=None):
    """Find an executable on PATH or in common locations.

    Returns (path, version_string) or (None, "").
    """
    # 1. shutil.which (respects PATH)
    path = shutil.which(name)
    if path:
        return os.path.abspath(path), _detect_version(path, name)

    # 2. FlowStudio-managed build/install artifacts
    artifact_path = resolve_solver_artifact(
        name,
        backend_name=backend_name,
        extra_paths=extra_paths,
    )
    if artifact_path:
        return os.path.abspath(artifact_path), _detect_version(artifact_path, name)

    # 3. Extra dirs
    search_dirs = _extra_dirs() + artifact_search_dirs(
        backend_name=backend_name,
        extra_paths=extra_paths,
    )
    for d in search_dirs:
        if not os.path.isdir(d):
            continue
        for ext in ("", ".exe", ".bat", ".cmd"):
            candidate = os.path.join(d, name + ext)
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return os.path.abspath(candidate), _detect_version(candidate, name)

    return None, ""


@lru_cache(maxsize=128)
def _detect_version(exe_path, name):
    """Try to detect version by running ``<exe> --version`` etc."""
    import subprocess

    flags = _VERSION_FLAGS.get(name.lower(), ("--version", "-v", "-version"))
    for flag in flags:
        try:
            result = subprocess.run(
                [exe_path, flag],
                capture_output=True,
                text=True,
                timeout=_VERSION_DETECT_TIMEOUT,
            )
            output = (result.stdout + result.stderr).strip()
            if output:
                # Return first line (usually contains version)
                return output.splitlines()[0][:120]
        except (OSError, subprocess.SubprocessError, Exception):
            continue
    return ""


def find_python_package(module_name):
    """Check if a Python package is importable.

    Returns (found: bool, location: str, version: str).
    """
    try:
        mod = importlib.import_module(module_name)
        loc = getattr(mod, "__file__", "") or ""
        ver = getattr(mod, "__version__", "")
        if not ver:
            # Try pkg_resources / importlib.metadata
            try:
                from importlib.metadata import version as _meta_ver
                ver = _meta_ver(module_name)
            except Exception:
                pass
        return True, loc, ver
    except ImportError:
        return False, "", ""


# ======================================================================
# Backend dependency definitions
# ======================================================================

# Each backend maps to a list of (name, kind, required, hint) tuples.
# kind: "executable" | "python_package" | "python_optional"

_BACKEND_DEPS = {
    "OpenFOAM": [
        ("simpleFoam", "executable", True,
         "Install OpenFOAM: https://openfoam.org/download/ "
         "or via WSL on Windows"),
        ("pimpleFoam", "executable", False,
         "Part of standard OpenFOAM installation"),
        ("decomposePar", "executable", False,
         "Part of OpenFOAM – needed for parallel runs"),
        ("reconstructPar", "executable", False,
         "Part of OpenFOAM – needed to merge parallel results"),
        ("mpirun", "executable", False,
         "Install OpenMPI: apt install openmpi-bin (Linux) "
         "or via MS-MPI (Windows)"),
        ("gmshToFoam", "executable", False,
         "Included with OpenFOAM; converts GMSH meshes to polyMesh"),
        ("paraFoam", "executable", False,
         "ParaView with OpenFOAM plugin for post-processing"),
    ],
    "FluidX3D": [
        ("FluidX3D", "executable", True,
         "Clone and build: https://github.com/ProjectPhysX/FluidX3D"),
        ("make", "executable", False,
         "Required to compile FluidX3D from source"),
    ],
    "Elmer": [
        ("ElmerSolver", "executable", True,
         "Install Elmer FEM: https://www.elmerfem.org/blog/binaries/ "
         "or: apt install elmer / choco install elmer"),
        ("ElmerGrid", "executable", True,
         "Part of Elmer FEM installation (mesh format conversion)"),
        ("ElmerSolver_mpi", "executable", False,
         "Parallel Elmer solver (requires MPI)"),
    ],
    "Geant4": [
        ("geant4-config", "executable", False,
         "Install Geant4 from https://geant4.web.cern.ch/download/ and source its environment setup script."),
        ("cmake", "executable", False,
         "CMake is typically required when building Geant4 applications from source."),
    ],
    "SU2": [
        ("SU2_CFD", "executable", True,
         "Install SU2: https://su2code.github.io/ or pip install SU2"),
        ("SU2_DEF", "executable", False,
         "SU2 mesh deformation tool"),
        ("SU2_SOL", "executable", False,
         "SU2 solution output tool"),
        ("mpirun", "executable", False,
         "MPI launcher for parallel SU2 runs"),
    ],
    "ParaView": [
        ("paraview", "executable", True,
         "Download ParaView: https://www.paraview.org/download/"),
        ("pvpython", "executable", False,
         "ParaView Python scripting interface"),
        ("pvbatch", "executable", False,
         "ParaView batch processing (headless)"),
    ],
    "Meshing": [
        ("gmsh", "python_package", True,
         "Install GMSH Python API: pip install gmsh"),
        ("gmsh", "executable", False,
         "GMSH standalone: https://gmsh.info/#Download"),
    ],
    "PostProcessing": [
        ("vtk", "python_package", False,
         "Install VTK: pip install vtk (for result visualization)"),
        ("numpy", "python_package", False,
         "Install NumPy: pip install numpy"),
        ("matplotlib", "python_optional", False,
         "Install matplotlib: pip install matplotlib (for plots)"),
    ],
    "Raysect": [
        ("raysect", "python_package", True,
         "Install Raysect: pip install raysect"),
        ("numpy", "python_optional", False,
         "Install NumPy: pip install numpy"),
    ],
    "Meep": [
        ("meep", "python_package", True,
         "Install Meep from Conda Forge, usually: conda install -c conda-forge pymeep"),
        ("h5py", "python_optional", False,
         "Install h5py for field/result output: pip install h5py"),
    ],
    "openEMS": [
        ("openEMS", "python_package", False,
         "Install openEMS Python bindings if available for your platform"),
        ("openEMS", "executable", False,
         "Install openEMS: https://openems.de/start/"),
    ],
    "Optiland": [
        ("optiland", "python_package", True,
         "Install Optiland from its project package/source distribution"),
        ("torch", "python_optional", False,
         "Install PyTorch for differentiable/GPU tracing workflows"),
    ],
}


# ======================================================================
# Check functions
# ======================================================================

def check_backend(backend_name, extra_paths=None):
    """Check all dependencies for a single backend.

    Parameters
    ----------
    backend_name : str
        One of "OpenFOAM", "FluidX3D", "Elmer", "Meshing", "PostProcessing".
    extra_paths : list[str] or None
        Additional directories to search for executables.

    Returns
    -------
    BackendReport
    """
    if backend_name == "Geant4":
        return _check_geant4_backend(extra_paths)

    dep_defs = _BACKEND_DEPS.get(backend_name)
    if dep_defs is None:
        return BackendReport(
            backend=backend_name,
            available=False,
            message=f"Unknown backend: {backend_name}",
        )

    deps = []
    for name, kind, required, hint in dep_defs:
        if kind == "executable":
            path, ver = find_executable(name, extra_paths, backend_name=backend_name)
            deps.append(DependencyStatus(
                name=name, kind=kind, required=required,
                found=path is not None,
                path=path or "", version=ver, hint=hint,
            ))
        elif kind in ("python_package", "python_optional"):
            found, loc, ver = find_python_package(name)
            deps.append(DependencyStatus(
                name=name, kind=kind, required=required,
                found=found, path=loc, version=ver, hint=hint,
            ))

    all_required_met = all(d.ok for d in deps)
    return BackendReport(
        backend=backend_name,
        available=all_required_met,
        deps=deps,
    )


def _check_geant4_backend(extra_paths=None):
    """Detect Geant4 using its common environment markers and tooling."""

    deps = []
    config_path, config_ver = find_executable("geant4-config", extra_paths)
    deps.append(DependencyStatus(
        name="geant4-config",
        kind="executable",
        required=False,
        found=config_path is not None,
        path=config_path or "",
        version=config_ver,
        hint=(
            "Install Geant4 from https://geant4.web.cern.ch/download/ and source the "
            "provided environment setup script before launching FlowStudio."
        ),
    ))

    env_markers = []
    for env_name in ("GEANT4_INSTALL", "Geant4_DIR", "GEANT4_DATA_DIR"):
        env_value = os.environ.get(env_name, "")
        found = bool(env_value)
        env_markers.append(found)
        deps.append(DependencyStatus(
            name=env_name,
            kind="executable",
            required=False,
            found=found,
            path=env_value,
            version="",
            hint=(
                f"Set {env_name} by sourcing the Geant4 environment or configuring your build/install tree."
            ),
        ))

    cmake_path, cmake_ver = find_executable("cmake", extra_paths)
    deps.append(DependencyStatus(
        name="cmake",
        kind="executable",
        required=False,
        found=cmake_path is not None,
        path=cmake_path or "",
        version=cmake_ver,
        hint="Install CMake if you need to build or rebuild Geant4 applications.",
    ))

    available = config_path is not None or any(env_markers)
    message = "" if available else "Geant4 environment was not detected."
    return BackendReport(
        backend="Geant4",
        available=available,
        deps=deps,
        message=message,
    )


def check_all(extra_paths=None):
    """Check dependencies for every registered backend.

    Returns
    -------
    dict[str, BackendReport]
    """
    reports = {}
    for backend_name in _BACKEND_DEPS:
        reports[backend_name] = check_backend(backend_name, extra_paths)
    return reports


def install_hint(backend_name):
    """Return a human-readable installation guide for a backend.

    Returns
    -------
    str
    """
    report = check_backend(backend_name)
    if report.available:
        return f"{backend_name}: All dependencies satisfied."

    lines = [f"=== {backend_name} Installation Guide ===\n"]
    system = platform.system()

    for dep in report.missing_required:
        lines.append(f"REQUIRED: {dep.name}")
        lines.append(f"  {dep.hint}")
        lines.append(_platform_specific_hint(dep.name, system))
        lines.append("")

    for dep in report.missing_optional:
        lines.append(f"OPTIONAL: {dep.name}")
        lines.append(f"  {dep.hint}")
        lines.append("")

    return "\n".join(lines)


def _platform_specific_hint(dep_name, system):
    """Return platform-specific installation command."""
    hints = {
        ("ElmerSolver", "Windows"): "  > choco install elmer\n  or download from: https://www.elmerfem.org/blog/binaries/",
        ("ElmerSolver", "Linux"):   "  $ sudo apt install elmer  (Ubuntu/Debian)\n  $ sudo dnf install elmer  (Fedora)",
        ("ElmerSolver", "Darwin"):  "  $ brew install elmer  (Homebrew)",
        ("ElmerGrid", "Windows"):   "  Installed with ElmerFEM package",
        ("ElmerGrid", "Linux"):     "  Installed with elmer package",
        ("ElmerGrid", "Darwin"):    "  Installed with elmer package",
        ("simpleFoam", "Windows"):  "  Use WSL2: wsl --install && sudo apt install openfoam\n  or: https://www.bluecfd.com/",
        ("simpleFoam", "Linux"):    "  $ sudo apt install openfoam  (Ubuntu)\n  or: https://openfoam.org/download/",
        ("simpleFoam", "Darwin"):   "  $ brew install open-mpi && brew install openfoam",
        ("gmsh", "Windows"):        "  > pip install gmsh\n  or download: https://gmsh.info/",
        ("gmsh", "Linux"):          "  $ pip install gmsh\n  $ sudo apt install gmsh",
        ("gmsh", "Darwin"):         "  $ pip install gmsh\n  $ brew install gmsh",
        ("FluidX3D", "Windows"):    "  Clone: git clone https://github.com/ProjectPhysX/FluidX3D\n  Build with Visual Studio (requires OpenCL SDK)",
        ("FluidX3D", "Linux"):      "  Clone: git clone https://github.com/ProjectPhysX/FluidX3D\n  $ cd FluidX3D && make",
        ("FluidX3D", "Darwin"):     "  Clone: git clone https://github.com/ProjectPhysX/FluidX3D\n  $ cd FluidX3D && make",
        ("geant4-config", "Windows"): "  Install Geant4 from https://geant4.web.cern.ch/download/ and launch FlowStudio from a developer shell where the Geant4 environment is loaded.",
        ("geant4-config", "Linux"):   "  Build or install Geant4, then source geant4.sh from the installation prefix before launching FlowStudio.",
        ("geant4-config", "Darwin"):  "  Build or install Geant4, then source geant4.sh from the installation prefix before launching FlowStudio.",
        ("SU2_CFD", "Windows"):     "  Download from https://su2code.github.io/download.html\n  or: pip install SU2",
        ("SU2_CFD", "Linux"):       "  $ sudo apt install su2  (Ubuntu)\n  or: pip install SU2",
        ("SU2_CFD", "Darwin"):      "  $ brew install su2\n  or: pip install SU2",
        ("paraview", "Windows"):    "  Download from https://www.paraview.org/download/\n  or: choco install paraview",
        ("paraview", "Linux"):      "  $ sudo apt install paraview\n  or download from https://www.paraview.org/download/",
        ("paraview", "Darwin"):     "  $ brew install paraview\n  or download from https://www.paraview.org/download/",
    }
    return hints.get((dep_name, system), "")


# ======================================================================
# Convenience: status dict for UI consumption
# ======================================================================

def status_dict():
    """Return a JSON-serializable dict of all backend statuses.

    Suitable for task-panel display or FreeCAD console reporting.
    """
    reports = check_all()
    result = {}
    for name, report in reports.items():
        result[name] = {
            "available": report.available,
            "deps": [
                {
                    "name": d.name,
                    "kind": d.kind,
                    "required": d.required,
                    "found": d.found,
                    "path": d.path,
                    "version": d.version,
                    "hint": d.hint,
                }
                for d in report.deps
            ],
        }
    return result


def print_report():
    """Print a human-readable dependency report to stdout."""
    reports = check_all()
    lines = ["", "=" * 60, "FlowStudio Solver Dependency Report", "=" * 60, ""]
    for name, report in reports.items():
        lines.append(report.summary())
        lines.append("")
    print("\n".join(lines))


# ======================================================================
# Parallelism helpers
# ======================================================================

def detect_cpu_cores():
    """Detect number of physical CPU cores available.

    Returns (physical_cores, logical_cores).
    """
    import multiprocessing
    logical = multiprocessing.cpu_count()
    try:
        # Try psutil for physical core count
        import psutil
        physical = psutil.cpu_count(logical=False) or logical
    except ImportError:
        # Heuristic: assume hyper-threading (2 threads/core)
        physical = max(1, logical // 2)
    return physical, logical


def detect_gpu_count():
    """Detect number of OpenCL/CUDA capable GPUs.

    Returns the number of GPUs found, or 0.
    """
    # Try OpenCL first
    try:
        import pyopencl as cl
        platforms = cl.get_platforms()
        gpu_count = 0
        for p in platforms:
            devs = p.get_devices(device_type=cl.device_type.GPU)
            gpu_count += len(devs)
        return gpu_count
    except (ImportError, Exception):
        pass

    # Try nvidia-smi
    try:
        import subprocess
        result = subprocess.run(
            ["nvidia-smi", "--list-gpus"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return len(result.stdout.strip().splitlines())
    except Exception:
        pass

    return 0


def recommend_parallel_settings():
    """Recommend optimal parallelism settings for each solver backend.

    Returns a dict with recommended settings.
    """
    phys_cores, logical_cores = detect_cpu_cores()
    gpu_count = detect_gpu_count()

    # Production defaults should use all detected physical cores.
    of_procs = max(1, phys_cores)
    elmer_procs = max(1, phys_cores)

    return {
        "cpu_physical": phys_cores,
        "cpu_logical": logical_cores,
        "gpu_count": gpu_count,
        "OpenFOAM": {
            "NumProcessors": of_procs,
            "mpi_available": find_executable("mpirun")[0] is not None
                             or find_executable("mpiexec")[0] is not None,
        },
        "Elmer": {
            "NumProcessors": elmer_procs,
            "mpi_available": find_executable("ElmerSolver_mpi", backend_name="Elmer")[0] is not None,
        },
        "FluidX3D": {
            "NumGPUs": max(1, gpu_count),
            "MultiGPU": gpu_count > 1,
        },
    }
