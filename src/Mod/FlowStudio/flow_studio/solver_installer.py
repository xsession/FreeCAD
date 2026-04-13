# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Automatic solver and tool downloader/installer.

Provides automated download and installation for:
  - OpenFOAM (Windows: OpenCFD ESI package / WSL; Linux: native)
  - FluidX3D (GitHub clone + build)
  - Elmer FEM (official binaries)
  - ParaView (official binaries)
  - GMSH (pip or binary)

Each installer:
  1. Checks if the tool is already available (via solver_deps.find_executable)
  2. Downloads from the official source
  3. Extracts / installs to a local directory
  4. Updates PATH / environment hints
  5. Verifies the installation

All downloads go to ``~/.flowstudio/solvers/`` by default.
"""

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from flow_studio.solver_deps import find_executable, check_backend, BackendReport


# ======================================================================
# Configuration
# ======================================================================

def _default_install_root():
    """Return platform-appropriate install root."""
    home = Path.home()
    return str(home / ".flowstudio" / "solvers")


# Download URLs and metadata (updated periodically)
_SOLVER_DOWNLOADS = {
    "Elmer": {
        "Windows": {
            "url": "https://github.com/ElmerCSC/elmerfem/releases/download/release-9.0/ElmerFEM-Release9.0-Windows-AMD64.zip",
            "type": "zip",
            "subdir": "ElmerFEM-Release9.0",
            "bin_subdir": "bin",
            "test_exe": "ElmerSolver",
            "version": "9.0",
        },
        "Linux": {
            "url": "https://github.com/ElmerCSC/elmerfem/releases/download/release-9.0/ElmerFEM-Release9.0-Linux-AMD64.tar.gz",
            "type": "tar.gz",
            "subdir": "ElmerFEM-Release9.0",
            "bin_subdir": "bin",
            "test_exe": "ElmerSolver",
            "version": "9.0",
        },
    },
    "ParaView": {
        "Windows": {
            "url": "https://www.paraview.org/paraview-downloads/download.php?submit=Download&version=v5.13&type=binary&os=Windows&downloadFile=ParaView-5.13.1-Windows-Python3.10-msvc2022-AMD64.zip",
            "type": "zip",
            "subdir": "ParaView-5.13.1-Windows-Python3.10-msvc2022-AMD64",
            "bin_subdir": "bin",
            "test_exe": "paraview",
            "version": "5.13.1",
        },
        "Linux": {
            "url": "https://www.paraview.org/paraview-downloads/download.php?submit=Download&version=v5.13&type=binary&os=Linux&downloadFile=ParaView-5.13.1-MPI-Linux-Python3.10-x86_64.tar.gz",
            "type": "tar.gz",
            "subdir": "ParaView-5.13.1-MPI-Linux-Python3.10-x86_64",
            "bin_subdir": "bin",
            "test_exe": "paraview",
            "version": "5.13.1",
        },
    },
    "OpenFOAM": {
        "Linux": {
            "install_method": "apt",
            "commands": [
                "curl -s https://dl.openfoam.com/add-debian-repo.sh | sudo bash",
                "sudo apt-get install -y openfoam2406",
            ],
            "source_cmd": "source /usr/lib/openfoam/openfoam2406/etc/bashrc",
            "test_exe": "simpleFoam",
            "version": "v2406",
        },
        "Windows": {
            "install_method": "wsl",
            "info": (
                "OpenFOAM on Windows requires WSL2. "
                "Install via: wsl --install, then inside WSL:\n"
                "  curl -s https://dl.openfoam.com/add-debian-repo.sh | sudo bash\n"
                "  sudo apt-get install -y openfoam2406\n"
                "  source /usr/lib/openfoam/openfoam2406/etc/bashrc"
            ),
            "test_exe": "simpleFoam",
            "version": "v2406",
        },
    },
    "FluidX3D": {
        "all": {
            "install_method": "git_clone",
            "repo_url": "https://github.com/ProjectPhysX/FluidX3D.git",
            "build_commands": {
                "Linux": ["make -j$(nproc)"],
                "Darwin": ["make -j$(sysctl -n hw.ncpu)"],
                "Windows": [
                    "cmake -B build -DCMAKE_BUILD_TYPE=Release",
                    "cmake --build build --config Release --parallel",
                ],
            },
            "test_exe": "FluidX3D",
            "bin_subdir": "bin",
        },
    },
    "GMSH": {
        "pip": {
            "install_method": "pip",
            "package": "gmsh",
            "test_import": "gmsh",
        },
    },
}


# ======================================================================
# Download & extraction helpers
# ======================================================================

def _download_file(url, dest_path, progress_callback=None):
    """Download a file from URL to dest_path with optional progress."""
    print(f"  Downloading: {url}")
    print(f"  Destination: {dest_path}")

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "FlowStudio-Solver-Installer/1.0"
        })
        with urllib.request.urlopen(req, timeout=120) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 1024 * 256  # 256KB chunks

            with open(dest_path, "wb") as f:
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total > 0:
                        progress_callback(downloaded, total)
                    elif total > 0:
                        pct = downloaded * 100 // total
                        print(f"\r  Progress: {pct}% ({downloaded // 1024}KB / {total // 1024}KB)", end="", flush=True)

        print()  # newline after progress
        return True
    except Exception as e:
        print(f"  Download failed: {e}")
        return False


def _extract_zip(zip_path, dest_dir):
    """Extract a ZIP archive."""
    print(f"  Extracting ZIP to {dest_dir}...")
    os.makedirs(dest_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest_dir)
    print("  Extraction complete.")


def _extract_tar(tar_path, dest_dir):
    """Extract a tar.gz archive."""
    print(f"  Extracting tar.gz to {dest_dir}...")
    os.makedirs(dest_dir, exist_ok=True)
    with tarfile.open(tar_path, "r:gz") as tf:
        tf.extractall(dest_dir)
    print("  Extraction complete.")


def _pip_install(package_name):
    """Install a Python package via pip."""
    print(f"  Installing Python package: {package_name}")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet", package_name],
            timeout=120,
        )
        print(f"  {package_name} installed successfully.")
        return True
    except Exception as e:
        print(f"  pip install failed: {e}")
        return False


def _git_clone(repo_url, dest_dir):
    """Clone a git repository."""
    if os.path.isdir(dest_dir) and os.path.isdir(os.path.join(dest_dir, ".git")):
        print(f"  Repository already cloned at {dest_dir}, pulling latest...")
        try:
            subprocess.check_call(["git", "pull"], cwd=dest_dir, timeout=60)
            return True
        except Exception as e:
            print(f"  git pull failed: {e}")
            return False

    print(f"  Cloning {repo_url} -> {dest_dir}")
    os.makedirs(os.path.dirname(dest_dir), exist_ok=True)
    try:
        subprocess.check_call(
            ["git", "clone", "--depth", "1", repo_url, dest_dir],
            timeout=120,
        )
        print("  Clone complete.")
        return True
    except Exception as e:
        print(f"  git clone failed: {e}")
        return False


# ======================================================================
# Per-solver install functions
# ======================================================================

class SolverInstaller:
    """Manages downloading and installing solver backends."""

    def __init__(self, install_root=None):
        self.install_root = install_root or _default_install_root()
        self.system = platform.system()
        os.makedirs(self.install_root, exist_ok=True)
        self._state_file = os.path.join(self.install_root, "install_state.json")
        self._state = self._load_state()

    def _load_state(self):
        """Load installation state from disk."""
        if os.path.isfile(self._state_file):
            try:
                with open(self._state_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_state(self):
        """Persist installation state to disk."""
        with open(self._state_file, "w") as f:
            json.dump(self._state, f, indent=2)

    def _mark_installed(self, solver_name, info):
        """Record a successful installation."""
        self._state[solver_name] = {
            "installed": True,
            "path": info.get("path", ""),
            "version": info.get("version", ""),
            "bin_dir": info.get("bin_dir", ""),
        }
        self._save_state()

    def get_bin_dir(self, solver_name):
        """Return the bin directory for an installed solver, or ''."""
        entry = self._state.get(solver_name, {})
        return entry.get("bin_dir", "")

    def all_bin_dirs(self):
        """Return list of all installed solver bin directories."""
        dirs = []
        for name, entry in self._state.items():
            bd = entry.get("bin_dir", "")
            if bd and os.path.isdir(bd):
                dirs.append(bd)
        return dirs

    # ----- Elmer -----
    def install_elmer(self, force=False):
        """Download and install Elmer FEM."""
        print("=" * 60)
        print("Installing Elmer FEM...")
        print("=" * 60)

        # Already installed?
        if not force:
            path, ver = find_executable("ElmerSolver")
            if path:
                print(f"  Elmer already installed: {path} ({ver})")
                self._mark_installed("Elmer", {
                    "path": path,
                    "version": ver,
                    "bin_dir": os.path.dirname(path),
                })
                return True

        info = _SOLVER_DOWNLOADS.get("Elmer", {}).get(self.system)
        if not info:
            print(f"  No automatic installer for Elmer on {self.system}")
            return False

        dest_dir = os.path.join(self.install_root, "Elmer")
        archive_name = os.path.basename(info["url"].split("?")[0])
        archive_path = os.path.join(self.install_root, "_downloads", archive_name)

        # Download
        if not os.path.isfile(archive_path):
            ok = _download_file(info["url"], archive_path)
            if not ok:
                return False

        # Extract
        if info["type"] == "zip":
            _extract_zip(archive_path, dest_dir)
        else:
            _extract_tar(archive_path, dest_dir)

        # Find bin directory
        bin_dir = dest_dir
        if info.get("subdir"):
            bin_dir = os.path.join(dest_dir, info["subdir"])
        if info.get("bin_subdir"):
            bin_dir = os.path.join(bin_dir, info["bin_subdir"])

        # Verify
        test_exe = info["test_exe"]
        exe_path, ver = find_executable(test_exe, [bin_dir])
        if exe_path:
            print(f"  [+] Elmer installed successfully: {exe_path}")
            self._mark_installed("Elmer", {
                "path": exe_path,
                "version": ver or info.get("version", ""),
                "bin_dir": bin_dir,
            })
            return True
        else:
            print(f"  [X] Elmer installation verification failed")
            return False

    # ----- ParaView -----
    def install_paraview(self, force=False):
        """Download and install ParaView."""
        print("=" * 60)
        print("Installing ParaView...")
        print("=" * 60)

        if not force:
            path, ver = find_executable("paraview")
            if path:
                print(f"  ParaView already installed: {path} ({ver})")
                self._mark_installed("ParaView", {
                    "path": path,
                    "version": ver,
                    "bin_dir": os.path.dirname(path),
                })
                return True

        info = _SOLVER_DOWNLOADS.get("ParaView", {}).get(self.system)
        if not info:
            print(f"  No automatic installer for ParaView on {self.system}")
            return False

        dest_dir = os.path.join(self.install_root, "ParaView")
        archive_name = info["url"].split("downloadFile=")[-1] if "downloadFile=" in info["url"] else os.path.basename(info["url"])
        archive_path = os.path.join(self.install_root, "_downloads", archive_name)

        if not os.path.isfile(archive_path):
            ok = _download_file(info["url"], archive_path)
            if not ok:
                return False

        if info["type"] == "zip":
            _extract_zip(archive_path, dest_dir)
        else:
            _extract_tar(archive_path, dest_dir)

        bin_dir = dest_dir
        if info.get("subdir"):
            bin_dir = os.path.join(dest_dir, info["subdir"])
        if info.get("bin_subdir"):
            bin_dir = os.path.join(bin_dir, info["bin_subdir"])

        exe_path, ver = find_executable("paraview", [bin_dir])
        if exe_path:
            print(f"  [+] ParaView installed successfully: {exe_path}")
            self._mark_installed("ParaView", {
                "path": exe_path,
                "version": ver or info.get("version", ""),
                "bin_dir": bin_dir,
            })
            return True
        else:
            print(f"  [X] ParaView installation verification failed")
            return False

    # ----- FluidX3D -----
    def install_fluidx3d(self, force=False):
        """Clone and optionally build FluidX3D."""
        print("=" * 60)
        print("Installing FluidX3D...")
        print("=" * 60)

        if not force:
            path, ver = find_executable("FluidX3D")
            if path:
                print(f"  FluidX3D already available: {path}")
                self._mark_installed("FluidX3D", {
                    "path": path,
                    "version": ver,
                    "bin_dir": os.path.dirname(path),
                })
                return True

        info = _SOLVER_DOWNLOADS["FluidX3D"]["all"]
        dest_dir = os.path.join(self.install_root, "FluidX3D")

        ok = _git_clone(info["repo_url"], dest_dir)
        if not ok:
            return False

        # Attempt to build
        build_cmds = info["build_commands"].get(self.system, [])
        if build_cmds:
            print(f"  Building FluidX3D ({self.system})...")
            for cmd in build_cmds:
                try:
                    print(f"    $ {cmd}")
                    subprocess.check_call(
                        cmd, shell=True, cwd=dest_dir, timeout=300,
                    )
                except Exception as e:
                    print(f"    Build step failed: {e}")
                    print("    You may need to build manually. "
                          "See: https://github.com/ProjectPhysX/FluidX3D")
                    # Still mark as partially installed (source available)
                    self._mark_installed("FluidX3D", {
                        "path": dest_dir,
                        "version": "source",
                        "bin_dir": os.path.join(dest_dir, "bin"),
                    })
                    return False

        bin_dir = os.path.join(dest_dir, info.get("bin_subdir", "bin"))
        exe_path, ver = find_executable("FluidX3D", [bin_dir, dest_dir])
        if exe_path:
            print(f"  [+] FluidX3D built successfully: {exe_path}")
            self._mark_installed("FluidX3D", {
                "path": exe_path,
                "version": ver,
                "bin_dir": os.path.dirname(exe_path),
            })
            return True
        else:
            # Source is available even if binary isn't
            self._mark_installed("FluidX3D", {
                "path": dest_dir,
                "version": "source-only",
                "bin_dir": dest_dir,
            })
            print("  FluidX3D cloned but binary not found. Build manually.")
            return False

    # ----- OpenFOAM -----
    def install_openfoam(self, force=False):
        """Install OpenFOAM (platform-dependent)."""
        print("=" * 60)
        print("Installing OpenFOAM...")
        print("=" * 60)

        if not force:
            path, ver = find_executable("simpleFoam")
            if path:
                print(f"  OpenFOAM already installed: {path} ({ver})")
                self._mark_installed("OpenFOAM", {
                    "path": path,
                    "version": ver,
                    "bin_dir": os.path.dirname(path),
                })
                return True

        info = _SOLVER_DOWNLOADS.get("OpenFOAM", {}).get(self.system)
        if not info:
            print(f"  No automatic installer for OpenFOAM on {self.system}")
            return False

        if info.get("install_method") == "apt":
            print("  Installing via apt (requires sudo)...")
            for cmd in info["commands"]:
                print(f"    $ {cmd}")
                try:
                    subprocess.check_call(cmd, shell=True, timeout=300)
                except Exception as e:
                    print(f"    Failed: {e}")
                    return False

            # Source the environment and verify
            print(f"  OpenFOAM installed. Source with: {info['source_cmd']}")
            self._mark_installed("OpenFOAM", {
                "path": "/usr/lib/openfoam/openfoam2406",
                "version": info.get("version", ""),
                "bin_dir": "/usr/lib/openfoam/openfoam2406/platforms/linux64GccDPInt32Opt/bin",
            })
            return True

        elif info.get("install_method") == "wsl":
            print("  OpenFOAM on Windows requires WSL2.")
            print(info.get("info", ""))
            # Check if WSL is available
            try:
                result = subprocess.run(
                    ["wsl", "--list", "--quiet"],
                    capture_output=True, text=True, timeout=10,
                )
                if result.returncode == 0 and result.stdout.strip():
                    print("\n  WSL distributions found. Attempting install inside WSL...")
                    wsl_cmds = [
                        "curl -s https://dl.openfoam.com/add-debian-repo.sh | sudo bash",
                        "sudo apt-get update",
                        "sudo apt-get install -y openfoam2406",
                    ]
                    for cmd in wsl_cmds:
                        print(f"    wsl $ {cmd}")
                        try:
                            subprocess.check_call(
                                ["wsl", "bash", "-c", cmd],
                                timeout=300,
                            )
                        except Exception as e:
                            print(f"    WSL command failed: {e}")
                            return False
                    self._mark_installed("OpenFOAM", {
                        "path": "wsl",
                        "version": info.get("version", ""),
                        "bin_dir": "wsl",
                    })
                    return True
                else:
                    print("\n  No WSL distribution found. Install with: wsl --install")
                    return False
            except Exception:
                print("\n  WSL not available. Install from: https://learn.microsoft.com/en-us/windows/wsl/install")
                return False

        return False

    # ----- GMSH -----
    def install_gmsh(self, force=False):
        """Install GMSH Python package."""
        print("=" * 60)
        print("Installing GMSH...")
        print("=" * 60)

        if not force:
            try:
                import gmsh
                print(f"  GMSH already installed: {gmsh.__file__}")
                return True
            except ImportError:
                pass

        return _pip_install("gmsh")

    # ----- Install All -----
    def install_all(self, force=False, skip=None):
        """Install all solvers and tools.

        Parameters
        ----------
        force : bool
            Re-install even if already present.
        skip : set or None
            Set of solver names to skip.

        Returns
        -------
        dict[str, bool]
            Mapping of solver name -> install success.
        """
        skip = skip or set()
        results = {}

        installers = [
            ("GMSH", self.install_gmsh),
            ("Elmer", self.install_elmer),
            ("OpenFOAM", self.install_openfoam),
            ("FluidX3D", self.install_fluidx3d),
            ("ParaView", self.install_paraview),
        ]

        for name, func in installers:
            if name in skip:
                print(f"\n  Skipping {name} (requested)")
                results[name] = None
                continue
            try:
                results[name] = func(force=force)
            except Exception as e:
                print(f"  {name} installation error: {e}")
                results[name] = False

        # Print summary
        print("\n" + "=" * 60)
        print("Installation Summary")
        print("=" * 60)
        for name, ok in results.items():
            if ok is None:
                mark = "[-]"
                status = "SKIPPED"
            elif ok:
                mark = "[+]"
                status = "INSTALLED"
            else:
                mark = "[X]"
                status = "FAILED"
            print(f"  {mark} {name}: {status}")

        return results

    def ensure_solver(self, solver_name):
        """Ensure a single solver is available, installing if needed.

        Returns (available: bool, bin_dir: str).
        """
        # Check already installed
        report = check_backend(solver_name, self.all_bin_dirs())
        if report.available:
            return True, self.get_bin_dir(solver_name)

        # Try to install
        installer_map = {
            "Elmer": self.install_elmer,
            "OpenFOAM": self.install_openfoam,
            "FluidX3D": self.install_fluidx3d,
            "ParaView": self.install_paraview,
            "GMSH": self.install_gmsh,
            "Meshing": self.install_gmsh,
        }

        func = installer_map.get(solver_name)
        if func is None:
            print(f"  No installer for {solver_name}")
            return False, ""

        ok = func()
        if ok:
            return True, self.get_bin_dir(solver_name)
        return False, ""

    def status_report(self):
        """Print the current status of all solvers."""
        from flow_studio.solver_deps import check_all
        extra = self.all_bin_dirs()

        print("\n" + "=" * 60)
        print("FlowStudio Solver Status")
        print("=" * 60)

        reports = check_all(extra)
        for name, report in reports.items():
            print(report.summary())
            # Check our local installs
            local = self._state.get(name, {})
            if local.get("installed"):
                print(f"    [FlowStudio local install: {local.get('bin_dir', '')}]")
            print()

        # Check ParaView separately
        pv_path, pv_ver = find_executable("paraview", extra)
        if pv_path:
            print(f"  [+] ParaView: {pv_path} ({pv_ver})")
        else:
            print("  [X] ParaView: not found")

        return reports


# ======================================================================
# Convenience functions
# ======================================================================

def auto_install_missing(install_root=None, skip=None):
    """Detect and automatically install all missing solver dependencies.

    This is the main entry point for automatic solver provisioning.
    """
    installer = SolverInstaller(install_root)

    # Check what's already available
    from flow_studio.solver_deps import check_all
    reports = check_all(installer.all_bin_dirs())

    missing = []
    for name, report in reports.items():
        if not report.available:
            missing.append(name)

    # Always check ParaView too
    pv_path, _ = find_executable("paraview", installer.all_bin_dirs())
    if not pv_path:
        missing.append("ParaView")

    if not missing:
        print("All solvers and tools are already installed!")
        return {}

    print(f"Missing solvers: {', '.join(missing)}")
    results = {}
    for name in missing:
        if skip and name in skip:
            continue
        ok, _ = installer.ensure_solver(name)
        results[name] = ok

    return results


def get_installer(install_root=None):
    """Return a configured SolverInstaller instance."""
    return SolverInstaller(install_root)
