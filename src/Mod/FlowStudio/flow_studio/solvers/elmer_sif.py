# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Elmer SIF (Solver Input File) generator.

Provides a builder API for constructing Elmer SIF files programmatically.
Each SIF block (Header, Simulation, Constants, Body, Material, Solver,
Equation, Boundary Condition, Initial Condition, Body Force) is represented
as an ordered dictionary of key-value pairs.

The SIF format reference:
  Header            – mesh path, results directory
  Simulation        – coordinate system, simulation type, time stepping
  Constants         – physical constants (permittivity of vacuum, etc.)
  Body N            – links to equation, material, body force, initial cond.
  Material N        – material properties
  Solver N          – equation procedure, linear/nonlinear solver settings
  Equation N        – list of active solvers for a body set
  Boundary Cond. N  – boundary constraints
  Initial Cond. N   – initial field values
  Body Force N      – volumetric sources
"""

from collections import OrderedDict


def _normalize_key(key):
    return str(key).replace("_", " ")


def _infer_procedure(equation_name):
    return SifProcedure(str(equation_name), str(equation_name))


class SifSection:
    """One named section of a SIF file (e.g., 'Body 1').

    Stores key-value pairs preserving insertion order.
    Values can be: str, int, float, bool, list, or SifProcedure.
    """

    def __init__(self, block_type, index=None, name=None):
        self.block_type = block_type  # e.g. "Body", "Material"
        self.index = index            # e.g. 1, 2, ...
        self.name = name              # e.g. "Copper"
        self.data = OrderedDict()

    def __setitem__(self, key, value):
        self.data[key] = value

    def __getitem__(self, key):
        return self.data[key]

    def __contains__(self, key):
        return key in self.data

    def get(self, key, default=None):
        return self.data.get(key, default)

    def header_line(self):
        """Return the block header line, e.g. 'Body 1'."""
        if self.index is not None:
            return f"{self.block_type} {self.index}"
        return self.block_type

    def to_sif(self):
        """Format this section as SIF text."""
        lines = [self.header_line()]
        for key, val in self.data.items():
            lines.append(f"  {_format_kv(key, val)}")
        lines.append("End\n")
        return "\n".join(lines)


class SifProcedure:
    """Represents an Elmer solver procedure reference.

    Usage:  SifProcedure("HeatSolve", "HeatSolver")
    Output: Procedure = "HeatSolve" "HeatSolver"
    """

    def __init__(self, library, routine):
        self.library = library
        self.routine = routine

    def __repr__(self):
        return f'"{self.library}" "{self.routine}"'


class SifBuilder:
    """Fluent builder for complete Elmer SIF files.

    Example
    -------
    >>> b = SifBuilder()
    >>> b.set_header(mesh_db=".", mesh_dir="mesh")
    >>> b.set_simulation(coord_system="Cartesian 3D", sim_type="Steady State")
    >>> b.set_constant("Permittivity Of Vacuum", 8.8542e-12)
    >>> mat = b.add_material("Air")
    >>> mat["Density"] = 1.225
    >>> solver = b.add_solver("Heat Equation", SifProcedure("HeatSolve", "HeatSolver"))
    >>> eq = b.add_equation("Heat", [1])
    >>> body = b.add_body("Solid", equation=1, material=1)
    >>> bc = b.add_boundary_condition("Hot Wall")
    >>> bc["Temperature"] = 373.15
    >>> bc["Target Boundaries(1)"] = 1
    >>> print(b.generate())
    """

    def __init__(self):
        self.header = SifSection("Header")
        self.simulation = SifSection("Simulation")
        self.constants = SifSection("Constants")
        self.bodies = []
        self.materials = []
        self.solvers = []
        self.equations = []
        self.boundary_conditions = []
        self.initial_conditions = []
        self.body_forces = []

    # ---- Header ----
    def set_header(self, mesh_db=".", mesh_dir="mesh", results_dir="", result_dir=None):
        if result_dir is not None:
            results_dir = result_dir
        self.header["Mesh DB"] = f'"{mesh_db}" "{mesh_dir}"'
        self.header["Include Path"] = '""'
        self.header["Results Directory"] = f'"{results_dir}"'
        return self

    # ---- Simulation ----
    def set_simulation(self, coord_system="Cartesian 3D",
                       sim_type="Steady State",
                       steady_max_iter=1,
                       output_level=5, **kwargs):
        steady_state = kwargs.pop("steady_state", None)
        time_steps = kwargs.pop("time_steps", None)
        dt = kwargs.pop("dt", None)

        if steady_state is False:
            sim_type = "Transient"
        elif steady_state is True:
            sim_type = "Steady State"

        self.simulation["Coordinate System"] = coord_system
        self.simulation["Simulation Type"] = sim_type
        self.simulation["Steady State Max Iterations"] = steady_max_iter
        self.simulation["Max Output Level"] = output_level
        if time_steps is not None:
            self.simulation["Timestep Intervals"] = time_steps
        if dt is not None:
            self.simulation["Timestep Sizes"] = dt
        for k, v in kwargs.items():
            self.simulation[_normalize_key(k)] = v
        return self

    # ---- Constants ----
    def set_constant(self, key=None, value=None, **kwargs):
        if key is not None:
            self.constants[_normalize_key(key)] = value
        for extra_key, extra_value in kwargs.items():
            self.constants[_normalize_key(extra_key)] = extra_value
        return self

    # ---- Bodies ----
    def add_body(self, name, equation=None, material=None,
                 body_force=None, initial_condition=None):
        idx = len(self.bodies) + 1
        sec = SifSection("Body", idx, name)
        sec["Name"] = f'"{name}"'
        if equation is not None:
            sec["Equation"] = equation
        if material is not None:
            sec["Material"] = material
        if body_force is not None:
            sec["Body Force"] = body_force
        if initial_condition is not None:
            sec["Initial Condition"] = initial_condition
        self.bodies.append(sec)
        return sec

    # ---- Materials ----
    def add_material(self, name, **properties):
        idx = len(self.materials) + 1
        sec = SifSection("Material", idx, name)
        sec["Name"] = f'"{name}"'
        for key, value in properties.items():
            sec[_normalize_key(key)] = value
        self.materials.append(sec)
        return sec

    # ---- Solvers ----
    def add_solver(self, equation_name, procedure=None, variable=None,
                   variable_dofs=1, **settings):
        """Add a Solver block.

        Parameters
        ----------
        equation_name : str
            E.g. "Heat Equation", "Stat Elec Solver"
        procedure : SifProcedure
            E.g. SifProcedure("HeatSolve", "HeatSolver")
        variable : str or None
            Primary variable name (e.g. "Temperature")
        variable_dofs : int
            Degrees of freedom per node
        **settings
            Additional solver keywords
        """
        idx = len(self.solvers) + 1
        sec = SifSection("Solver", idx)
        if procedure is None:
            procedure = _infer_procedure(equation_name)
        sec["Equation"] = f'"{equation_name}"'
        sec["Procedure"] = procedure
        if variable:
            sec["Variable"] = f'"{variable}"'
        sec["Variable DOFs"] = variable_dofs
        for k, v in settings.items():
            sec[_normalize_key(k)] = v
        self.solvers.append(sec)
        return sec

    # ---- Equations ----
    def add_equation(self, name, active_solvers):
        """Add an Equation block.

        Parameters
        ----------
        name : str
        active_solvers : list[int]
            Solver indices (1-based) to activate.
        """
        idx = len(self.equations) + 1
        sec = SifSection("Equation", idx)
        sec["Name"] = f'"{name}"'
        n = len(active_solvers)
        ids_str = " ".join(str(s) for s in active_solvers)
        sec[f"Active Solvers({n})"] = ids_str
        self.equations.append(sec)
        return sec

    # ---- Boundary Conditions ----
    def add_boundary_condition(self, name, **values):
        idx = len(self.boundary_conditions) + 1
        sec = SifSection("Boundary Condition", idx, name)
        sec["Name"] = f'"{name}"'
        for key, value in values.items():
            sec[_normalize_key(key)] = value
        self.boundary_conditions.append(sec)
        return sec

    def add_bc(self, name, **values):
        return self.add_boundary_condition(name, **values)

    # ---- Initial Conditions ----
    def add_initial_condition(self, name=None, **values):
        idx = len(self.initial_conditions) + 1
        if name is None:
            name = f"Initial Condition {idx}"
        sec = SifSection("Initial Condition", idx, name)
        sec["Name"] = f'"{name}"'
        for key, value in values.items():
            sec[_normalize_key(key)] = value
        self.initial_conditions.append(sec)
        return sec

    # ---- Body Forces ----
    def add_body_force(self, name, **values):
        idx = len(self.body_forces) + 1
        sec = SifSection("Body Force", idx, name)
        sec["Name"] = f'"{name}"'
        for key, value in values.items():
            sec[_normalize_key(key)] = value
        self.body_forces.append(sec)
        return sec

    # ---- Output ----
    def generate(self):
        """Generate the complete SIF file content as a string."""
        parts = ['Check Keywords "Warn"\n']
        parts.append(self.header.to_sif())
        parts.append(self.simulation.to_sif())
        if self.constants.data:
            parts.append(self.constants.to_sif())
        for sec_list in (self.bodies, self.materials, self.solvers,
                         self.equations, self.boundary_conditions,
                         self.initial_conditions, self.body_forces):
            for sec in sec_list:
                parts.append(sec.to_sif())
        return "\n".join(parts)


# ======================================================================
# Formatting helpers
# ======================================================================

def _format_kv(key, value):
    """Format a single key = value line for SIF."""
    if isinstance(value, SifProcedure):
        return f'{key} = {value!r}'
    elif isinstance(value, bool):
        return f'{key} = {"True" if value else "False"}'
    elif isinstance(value, int):
        return f'{key} = {value}'
    elif isinstance(value, float):
        return f'{key} = {_format_float(value)}'
    elif isinstance(value, (list, tuple)):
        vals = " ".join(_format_single(v) for v in value)
        return f'{key} = {vals}'
    else:
        # String – check if already quoted
        s = str(value)
        if key == "Variable" and len(s) >= 2 and s[0] == '"' and s[-1] == '"':
            s = s[1:-1]
        return f'{key} = {s}'


def _format_single(value):
    """Format a single value for SIF (in arrays, etc.)."""
    if isinstance(value, bool):
        return "True" if value else "False"
    elif isinstance(value, int):
        return str(value)
    elif isinstance(value, float):
        return _format_float(value)
    else:
        return str(value)


def _format_float(value):
    """Format float – use scientific notation for very small/large numbers."""
    if abs(value) < 1e-4 or abs(value) > 1e9:
        return f"{value:.6e}"
    if float(value).is_integer():
        return str(int(value))
    return f"{value:g}"
