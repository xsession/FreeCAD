"""FlowStudio solver artifact discovery helpers.

This module lets FlowStudio prefer locally built solver artifacts from the
vendored ``solver_repos`` trees, explicit environment overrides, and common
build/install output folders before falling back to plain PATH lookup.
"""

from __future__ import annotations

import os
from pathlib import Path


_BACKEND_REPO_NAMES = {
    "OpenFOAM": "openfoam",
    "Elmer": "elmerfem",
    "FluidX3D": "fluidx3d",
    "Geant4": "geant4",
}

_DEFAULT_SUBDIRS = (
    "",
    "bin",
    os.path.join("build", "bin"),
    os.path.join("build", "Release"),
    os.path.join("build", "RelWithDebInfo"),
    os.path.join("build", "release"),
    os.path.join("install", "bin"),
    os.path.join("dist", "bin"),
)

_BACKEND_SUBDIRS = {
    "OpenFOAM": (
        os.path.join("platforms", "windows", "bin"),
        os.path.join("platforms", "linux64GccDPInt32Opt", "bin"),
        os.path.join("platforms", "linux64GccDPInt64Opt", "bin"),
    ),
    "Elmer": (
        os.path.join("build", "fem", "src"),
        os.path.join("build", "fem", "src", "Release"),
    ),
    "FluidX3D": (
        os.path.join("out", "build", "x64-Release"),
        os.path.join("out", "build", "x64-RelWithDebInfo"),
        os.path.join("out", "build", "Release"),
    ),
}


def _flowstudio_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _solver_repos_root() -> Path:
    return _flowstudio_root() / "solver_repos"


def _configured_artifact_roots() -> list[Path]:
    raw = os.environ.get("FLOWSTUDIO_SOLVER_ARTIFACTS", "")
    if not raw:
        return []

    roots = []
    for item in raw.split(os.pathsep):
        item = item.strip()
        if item:
            roots.append(Path(item))
    return roots


def _candidate_filenames(name: str) -> tuple[str, ...]:
    if not name:
        return ()
    if os.path.splitext(name)[1]:
        return (name,)

    names = [name]
    if os.name == "nt":
        names.extend((name + ".exe", name + ".bat", name + ".cmd"))
    return tuple(dict.fromkeys(names))


def _iter_backend_globs(repo_root: Path, backend_name: str | None):
    if backend_name == "OpenFOAM":
        yield from repo_root.glob(os.path.join("platforms", "*", "bin"))
        yield from repo_root.glob(os.path.join("platforms", "*", "*", "bin"))
    elif backend_name == "Elmer":
        yield from repo_root.glob(os.path.join("build", "*", "bin"))
        yield from repo_root.glob(os.path.join("build", "*", "*", "bin"))
    elif backend_name == "FluidX3D":
        yield from repo_root.glob(os.path.join("out", "build", "*", "Release"))
        yield from repo_root.glob(os.path.join("out", "build", "*", "RelWithDebInfo"))


def artifact_search_dirs(
    backend_name: str | None = None,
    extra_paths: list[str] | tuple[str, ...] | None = None,
) -> list[str]:
    """Return candidate directories that may contain built solver artifacts."""

    roots = []
    if extra_paths:
        roots.extend(Path(item) for item in extra_paths if item)
    roots.extend(_configured_artifact_roots())

    repo_name = _BACKEND_REPO_NAMES.get(backend_name or "")
    if repo_name:
        roots.append(_solver_repos_root() / repo_name)

    directories = []
    seen = set()
    for root in roots:
        for rel_path in _DEFAULT_SUBDIRS:
            candidate = root / rel_path if rel_path else root
            candidate_key = os.path.normcase(str(candidate))
            if candidate.is_dir() and candidate_key not in seen:
                seen.add(candidate_key)
                directories.append(str(candidate))

        for rel_path in _BACKEND_SUBDIRS.get(backend_name or "", ()):  # fixed backend output dirs
            candidate = root / rel_path
            candidate_key = os.path.normcase(str(candidate))
            if candidate.is_dir() and candidate_key not in seen:
                seen.add(candidate_key)
                directories.append(str(candidate))

        for candidate in _iter_backend_globs(root, backend_name):
            candidate_key = os.path.normcase(str(candidate))
            if candidate.is_dir() and candidate_key not in seen:
                seen.add(candidate_key)
                directories.append(str(candidate))

    return directories


def resolve_solver_artifact(
    name: str,
    backend_name: str | None = None,
    extra_paths: list[str] | tuple[str, ...] | None = None,
) -> str | None:
    """Resolve an executable from FlowStudio-managed solver artifacts."""

    if not name:
        return None

    path = Path(name)
    if path.is_absolute() or any(sep in name for sep in (os.sep, "/")):
        return str(path) if path.is_file() else None

    for directory in artifact_search_dirs(backend_name=backend_name, extra_paths=extra_paths):
        base = Path(directory)
        for candidate_name in _candidate_filenames(name):
            candidate = base / candidate_name
            if candidate.is_file():
                return str(candidate.resolve())

    return None
