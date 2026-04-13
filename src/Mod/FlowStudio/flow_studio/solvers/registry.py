# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Solver registry – maps backend names to runner classes.

Imports are lazy so this module can be used outside FreeCAD for testing.
Supports both CFD-era flat lookup and multi-physics domain-aware lookup.
"""

# Flat registry: backend_name → (module_path, class_name)
_REGISTRY_PATHS = {
    "OpenFOAM": ("flow_studio.solvers.openfoam_runner", "OpenFOAMRunner"),
    "FluidX3D": ("flow_studio.solvers.fluidx3d_runner", "FluidX3DRunner"),
    "Elmer": ("flow_studio.solvers.elmer_runner", "ElmerRunner"),
}

# Domain → list of available solver backend names
_DOMAIN_SOLVERS = {
    "CFD": ["OpenFOAM", "FluidX3D", "Elmer"],
    "Structural": ["Elmer"],
    "Electrostatic": ["Elmer"],
    "Electromagnetic": ["Elmer"],
    "Thermal": ["Elmer"],
}


def _resolve(backend_name):
    """Lazily import and return the runner *class* for *backend_name*."""
    entry = _REGISTRY_PATHS.get(backend_name)
    if entry is None:
        return None
    mod_path, cls_name = entry
    import importlib
    mod = importlib.import_module(mod_path)
    return getattr(mod, cls_name)


def get_runner(backend_name):
    """Return the runner *class* for *backend_name*, or None.

    Parameters
    ----------
    backend_name : str
        One of "OpenFOAM", "FluidX3D", "Elmer", etc.

    Returns
    -------
    BaseSolverRunner subclass or None
    """
    return _resolve(backend_name)


def available_backends():
    """Return a list of all registered solver backend names."""
    return list(_REGISTRY_PATHS.keys())


def available_backends_installed(extra_paths=None):
    """Return backends whose required dependencies are satisfied.

    Lazily imports :mod:`flow_studio.solver_deps` so this module stays
    lightweight when dependency checking isn't needed.

    Parameters
    ----------
    extra_paths : list[str] or None
        Extra directories to search for executables.

    Returns
    -------
    list[str]
        Backend names (e.g. ``["Elmer"]``) that are actually installed.
    """
    try:
        from flow_studio.solver_deps import check_backend as _check
    except ImportError:
        # Fallback: return all registered (can't verify)
        return available_backends()

    _SOLVER_BACKEND_NAMES = {
        "OpenFOAM": "OpenFOAM",
        "FluidX3D": "FluidX3D",
        "Elmer":    "Elmer",
    }
    installed = []
    for name in _REGISTRY_PATHS:
        dep_key = _SOLVER_BACKEND_NAMES.get(name, name)
        report = _check(dep_key, extra_paths)
        if report.available:
            installed.append(name)
    return installed


def backends_for_domain(domain_key):
    """Return solver backend names available for *domain_key*.

    Parameters
    ----------
    domain_key : str
        One of "CFD", "Structural", "Electrostatic", "Electromagnetic", "Thermal".

    Returns
    -------
    list[str]
    """
    return list(_DOMAIN_SOLVERS.get(domain_key, []))


def backends_for_domain_installed(domain_key, extra_paths=None):
    """Return installed solver backends for *domain_key*.

    Combines :func:`backends_for_domain` with dependency checks from
    :mod:`flow_studio.solver_deps` to filter out solvers that are
    registered but not actually installed on this machine.

    Parameters
    ----------
    domain_key : str
    extra_paths : list[str] or None

    Returns
    -------
    list[str]
    """
    all_for_domain = backends_for_domain(domain_key)
    installed = set(available_backends_installed(extra_paths))
    return [b for b in all_for_domain if b in installed]


def register_backend(name, module_path, class_name, domains=None):
    """Register a new solver backend dynamically.

    Parameters
    ----------
    name : str
        Backend name (e.g. "MyCustomSolver").
    module_path : str
        Python module path (e.g. "my_plugin.solvers.custom_runner").
    class_name : str
        Class name inside the module.
    domains : list[str] or None
        Physics domains this solver supports. If None, added to no domain.
    """
    _REGISTRY_PATHS[name] = (module_path, class_name)
    if domains:
        for d in domains:
            if d not in _DOMAIN_SOLVERS:
                _DOMAIN_SOLVERS[d] = []
            if name not in _DOMAIN_SOLVERS[d]:
                _DOMAIN_SOLVERS[d].append(name)
