# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""OpenFOAM solver backend – case file generation and execution.

Supports simpleFoam, pimpleFoam, pisoFoam, icoFoam, interFoam,
buoyantSimpleFoam, and more.
"""

import os
import shutil
import subprocess
import FreeCAD

from flow_studio.solvers.base_solver import BaseSolverRunner


def _openfoam_patch_names(obj):
    """Return patch names from a FlowStudio References property."""

    refs = getattr(obj, "References", None) or ()
    names = []
    for ref_obj, sub_elements in refs:
        if isinstance(sub_elements, str):
            sub_names = (sub_elements,)
        else:
            sub_names = tuple(sub_elements or ())
        if sub_names:
            names.extend(sub_names)
            continue
        names.append(getattr(ref_obj, "Name", getattr(ref_obj, "Label", "patch")))
    return tuple(dict.fromkeys(name for name in names if name)) or (obj.Name,)


class OpenFOAMRunner(BaseSolverRunner):
    """Generate and run OpenFOAM cases."""

    name = "OpenFOAM"

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _find_objects(self, type_str):
        """Return all child objects in the analysis with given FlowType."""
        results = []
        for obj in self.analysis.Group:
            if hasattr(obj, "FlowType") and obj.FlowType == type_str:
                results.append(obj)
        return results

    def _physics(self):
        objs = self._find_objects("FlowStudio::PhysicsModel")
        return objs[0] if objs else None

    def _material(self):
        objs = self._find_objects("FlowStudio::FluidMaterial")
        return objs[0] if objs else None

    def _initial_conditions(self):
        objs = self._find_objects("FlowStudio::InitialConditions")
        return objs[0] if objs else None

    # ------------------------------------------------------------------
    # check
    # ------------------------------------------------------------------
    def check(self):
        """Check that OpenFOAM commands are on PATH or configured."""
        of_dir = getattr(self.solver_obj, "OpenFOAMDir", "")
        if of_dir and os.path.isdir(of_dir):
            return True
        # Try to find on PATH (Linux/WSL)
        result = shutil.which("simpleFoam")
        return result is not None

    # ------------------------------------------------------------------
    # write_case
    # ------------------------------------------------------------------
    def write_case(self):
        """Write a complete OpenFOAM case directory.

        Structure:
            case_dir/
                system/
                    controlDict
                    fvSchemes
                    fvSolution
                    decomposeParDict  (if parallel)
                constant/
                    transportProperties
                    turbulenceProperties
                    polyMesh/  (symlink or mesh files)
                0/
                    p
                    U
                    k, epsilon, omega, nuTilda  (turbulence)
                    T  (if heat transfer)
        """
        FreeCAD.Console.PrintMessage("FlowStudio: Writing OpenFOAM case...\n")

        physics = self._physics()
        material = self._material()
        ic = self._initial_conditions()

        # Create directories
        for sub in ["system", "constant", "0"]:
            os.makedirs(os.path.join(self.case_dir, sub), exist_ok=True)

        self._write_controlDict(physics)
        self._write_fvSchemes(physics)
        self._write_fvSolution(physics)
        self._write_transport_properties(material)
        self._write_turbulence_properties(physics)
        self._write_boundary_fields(ic, physics)

        if self.solver_obj.NumProcessors > 1:
            self._write_decompose_par_dict()

        FreeCAD.Console.PrintMessage(
            f"FlowStudio: OpenFOAM case written to {self.case_dir}\n"
        )

    # ------------------------------------------------------------------
    # controlDict
    # ------------------------------------------------------------------
    def _write_controlDict(self, physics):
        solver_app = self.solver_obj.OpenFOAMSolver
        is_transient = physics and physics.TimeModel == "Transient"

        lines = [
            "FoamFile",
            "{",
            "    version     2.0;",
            "    format      ascii;",
            "    class       dictionary;",
            "    object      controlDict;",
            "}",
            "",
            f"application     {solver_app};",
            "",
        ]
        if is_transient:
            lines += [
                "startFrom       startTime;",
                "startTime       0;",
                "",
                f"stopAt          endTime;",
                f"endTime         {self.solver_obj.EndTime};",
                "",
                f"deltaT          {self.solver_obj.TimeStep if self.solver_obj.TimeStep > 0 else 1e-4};",
                "",
                f"writeControl    timeStep;",
                f"writeInterval   {self.solver_obj.WriteInterval};",
            ]
        else:
            lines += [
                "startFrom       startTime;",
                "startTime       0;",
                "",
                "stopAt          endTime;",
                f"endTime         {self.solver_obj.MaxIterations};",
                "",
                "deltaT          1;",
                "",
                "writeControl    timeStep;",
                f"writeInterval   {self.solver_obj.WriteInterval};",
            ]

        lines += [
            "",
            "purgeWrite      0;",
            "",
            "writeFormat     ascii;",
            "writePrecision  8;",
            "writeCompression off;",
            "",
            "timeFormat      general;",
            "timePrecision   6;",
            "",
            "runTimeModifiable true;",
            "",
            "functions",
            "{",
            "    fieldAverage1",
            "    {",
            '        type            fieldAverage;',
            '        libs            ("libfieldFunctionObjects.so");',
            "        writeControl    writeTime;",
            "        fields",
            "        (",
            "            U",
            "            {",
            "                mean        on;",
            "                prime2Mean  on;",
            "                base        time;",
            "            }",
            "            p",
            "            {",
            "                mean        on;",
            "                prime2Mean  on;",
            "                base        time;",
            "            }",
            "        );",
            "    }",
            "",
            "    forceCoeffs1",
            "    {",
            '        type            forceCoeffs;',
            '        libs            ("libforces.so");',
            "        writeControl    timeStep;",
            "        writeInterval   1;",
            '        patches         ("wall.*");',
            "        rho             rhoInf;",
            "        rhoInf          1.225;",
            "        liftDir         (0 0 1);",
            "        dragDir         (0 1 0);",
            "        CofR            (0 0 0);",
            "        pitchAxis       (1 0 0);",
            "        magUInf         1;",
            "        lRef            1;",
            "        Aref            1;",
            "    }",
            "}",
        ]
        self._write_file("system/controlDict", "\n".join(lines))

    # ------------------------------------------------------------------
    # fvSchemes
    # ------------------------------------------------------------------
    def _write_fvSchemes(self, physics):
        conv_scheme = getattr(self.solver_obj, "ConvectionScheme", "linearUpwind")
        lines = [
            "FoamFile",
            "{",
            "    version     2.0;",
            "    format      ascii;",
            "    class       dictionary;",
            "    object      fvSchemes;",
            "}",
            "",
            "ddtSchemes",
            "{",
        ]
        if physics and physics.TimeModel == "Transient":
            lines.append("    default         Euler;")
        else:
            lines.append("    default         steadyState;")
        lines += [
            "}",
            "",
            "gradSchemes",
            "{",
            "    default         Gauss linear;",
            "    grad(p)         Gauss linear;",
            "    grad(U)         cellLimited Gauss linear 1;",
            "}",
            "",
            "divSchemes",
            "{",
            "    default         none;",
            f"    div(phi,U)      bounded Gauss {conv_scheme} grad(U);",
            f"    div(phi,k)      bounded Gauss {conv_scheme} grad(k);",
            f"    div(phi,epsilon) bounded Gauss {conv_scheme} grad(epsilon);",
            f"    div(phi,omega)  bounded Gauss {conv_scheme} grad(omega);",
            f"    div(phi,nuTilda) bounded Gauss {conv_scheme} grad(nuTilda);",
            "    div((nuEff*dev2(T(grad(U))))) Gauss linear;",
            "}",
            "",
            "laplacianSchemes",
            "{",
            "    default         Gauss linear corrected;",
            "}",
            "",
            "interpolationSchemes",
            "{",
            "    default         linear;",
            "}",
            "",
            "snGradSchemes",
            "{",
            "    default         corrected;",
            "}",
        ]
        self._write_file("system/fvSchemes", "\n".join(lines))

    # ------------------------------------------------------------------
    # fvSolution
    # ------------------------------------------------------------------
    def _write_fvSolution(self, physics):
        p_solver = getattr(self.solver_obj, "PressureSolver", "GAMG")
        u_solver = getattr(self.solver_obj, "VelocitySolver", "smoothSolver")
        relax_u = getattr(self.solver_obj, "RelaxationFactorU", 0.7)
        relax_p = getattr(self.solver_obj, "RelaxationFactorP", 0.3)
        tol = getattr(self.solver_obj, "ConvergenceTolerance", 1e-4)

        lines = [
            "FoamFile",
            "{",
            "    version     2.0;",
            "    format      ascii;",
            "    class       dictionary;",
            "    object      fvSolution;",
            "}",
            "",
            "solvers",
            "{",
            "    p",
            "    {",
            f"        solver          {p_solver};",
            "        smoother        GaussSeidel;",
            f"        tolerance       {tol};",
            f"        relTol          0.01;",
            "    }",
            "",
            "    U",
            "    {",
            f"        solver          {u_solver};",
            "        smoother        symGaussSeidel;",
            f"        tolerance       {tol};",
            "        relTol          0.1;",
            "    }",
            "",
            '    "(k|epsilon|omega|nuTilda)"',
            "    {",
            f"        solver          {u_solver};",
            "        smoother        symGaussSeidel;",
            f"        tolerance       {tol};",
            "        relTol          0.1;",
            "    }",
            "}",
            "",
            "SIMPLE",
            "{",
            f"    nNonOrthogonalCorrectors 1;",
            f"    consistent      yes;",
            "",
            "    residualControl",
            "    {",
            f'        p               {tol};',
            f'        U               {tol};',
            f'        "(k|epsilon|omega|nuTilda)" {tol};',
            "    }",
            "}",
            "",
            "relaxationFactors",
            "{",
            "    fields",
            "    {",
            f"        p               {relax_p};",
            "    }",
            "    equations",
            "    {",
            f"        U               {relax_u};",
            f"        k               {relax_u};",
            f"        epsilon         {relax_u};",
            f"        omega           {relax_u};",
            f"        nuTilda         {relax_u};",
            "    }",
            "}",
        ]
        self._write_file("system/fvSolution", "\n".join(lines))

    # ------------------------------------------------------------------
    # transportProperties
    # ------------------------------------------------------------------
    def _write_transport_properties(self, material):
        nu = material.KinematicViscosity if material else 1.48e-5
        lines = [
            "FoamFile",
            "{",
            "    version     2.0;",
            "    format      ascii;",
            "    class       dictionary;",
            "    object      transportProperties;",
            "}",
            "",
            "transportModel  Newtonian;",
            "",
            f"nu              [0 2 -1 0 0 0 0] {nu};",
        ]
        self._write_file("constant/transportProperties", "\n".join(lines))

    # ------------------------------------------------------------------
    # turbulenceProperties
    # ------------------------------------------------------------------
    def _write_turbulence_properties(self, physics):
        if not physics or physics.FlowRegime == "Laminar":
            sim_type = "laminar"
            model = "none"
        else:
            sim_type = "RAS"
            turb_map = {
                "kEpsilon": "kEpsilon",
                "kOmega": "kOmega",
                "kOmegaSST": "kOmegaSST",
                "SpalartAllmaras": "SpalartAllmaras",
                "LES-Smagorinsky": "Smagorinsky",
                "LES-WALE": "WALE",
            }
            model = turb_map.get(physics.TurbulenceModel, "kOmegaSST")
            if physics.TurbulenceModel.startswith("LES"):
                sim_type = "LES"

        lines = [
            "FoamFile",
            "{",
            "    version     2.0;",
            "    format      ascii;",
            "    class       dictionary;",
            "    object      turbulenceProperties;",
            "}",
            "",
            f"simulationType  {sim_type};",
            "",
        ]
        if sim_type == "RAS":
            lines += [
                "RAS",
                "{",
                f"    RASModel     {model};",
                "    turbulence  on;",
                "    printCoeffs on;",
                "}",
            ]
        elif sim_type == "LES":
            lines += [
                "LES",
                "{",
                f"    LESModel     {model};",
                "    turbulence  on;",
                "    printCoeffs on;",
                "    delta       cubeRootVol;",
                "}",
            ]
        self._write_file("constant/turbulenceProperties", "\n".join(lines))

    # ------------------------------------------------------------------
    # Boundary fields (0/ directory)
    # ------------------------------------------------------------------
    def _write_boundary_fields(self, ic, physics):
        """Write 0/p, 0/U and turbulence fields."""
        # Collect boundary conditions from analysis
        bcs = []
        for obj in self.analysis.Group:
            if hasattr(obj, "BoundaryType"):
                bcs.append(obj)

        # Write p
        self._write_p_field(ic, bcs)
        # Write U
        self._write_U_field(ic, bcs)
        # Write turbulence fields
        if physics and physics.FlowRegime == "Turbulent":
            self._write_turbulence_fields(ic, bcs, physics)

    def _write_p_field(self, ic, bcs):
        p0 = ic.Pressure if ic else 0.0
        bc_entries = []
        for bc in bcs:
            for patch_name in _openfoam_patch_names(bc):
                if bc.BoundaryType == "wall":
                    bc_entries.append(f"    {patch_name}\n    {{\n        type            zeroGradient;\n    }}")
                elif bc.BoundaryType == "inlet":
                    bc_entries.append(f"    {patch_name}\n    {{\n        type            zeroGradient;\n    }}")
                elif bc.BoundaryType == "outlet":
                    p_val = getattr(bc, "StaticPressure", 0.0)
                    bc_entries.append(
                        f"    {patch_name}\n    {{\n        type            fixedValue;\n        value           uniform {p_val};\n    }}"
                    )
                elif bc.BoundaryType == "symmetry":
                    bc_entries.append(f"    {patch_name}\n    {{\n        type            symmetry;\n    }}")
                elif bc.BoundaryType == "open":
                    p_val = getattr(bc, "FarFieldPressure", 101325.0)
                    bc_entries.append(
                        f"    {patch_name}\n    {{\n        type            totalPressure;\n        p0              uniform {p_val};\n        value           uniform {p_val};\n    }}"
                    )

        lines = [
            "FoamFile",
            "{",
            "    version     2.0;",
            "    format      ascii;",
            "    class       volScalarField;",
            "    object      p;",
            "}",
            "",
            "dimensions      [0 2 -2 0 0 0 0];",
            "",
            f"internalField   uniform {p0};",
            "",
            "boundaryField",
            "{",
        ]
        for entry in bc_entries:
            lines.append(entry)
        lines += ["}", ""]
        self._write_file("0/p", "\n".join(lines))

    def _write_U_field(self, ic, bcs):
        ux = ic.Ux if ic else 0.0
        uy = ic.Uy if ic else 0.0
        uz = ic.Uz if ic else 0.0

        bc_entries = []
        for bc in bcs:
            for patch_name in _openfoam_patch_names(bc):
                if bc.BoundaryType == "wall":
                    if getattr(bc, "WallType", "No-Slip") == "No-Slip":
                        bc_entries.append(
                            f"    {patch_name}\n    {{\n        type            noSlip;\n    }}"
                        )
                    elif bc.WallType == "Slip":
                        bc_entries.append(
                            f"    {patch_name}\n    {{\n        type            slip;\n    }}"
                        )
                    elif bc.WallType.startswith("Moving"):
                        vx = getattr(bc, "WallVelocityX", 0.0)
                        vy = getattr(bc, "WallVelocityY", 0.0)
                        vz = getattr(bc, "WallVelocityZ", 0.0)
                        bc_entries.append(
                            f"    {patch_name}\n    {{\n        type            fixedValue;\n"
                            f"        value           uniform ({vx} {vy} {vz});\n    }}"
                        )
                    else:
                        bc_entries.append(
                            f"    {patch_name}\n    {{\n        type            noSlip;\n    }}"
                        )
                elif bc.BoundaryType == "inlet":
                    vx = getattr(bc, "Ux", 0.0)
                    vy = getattr(bc, "Uy", 0.0)
                    vz = getattr(bc, "Uz", 1.0)
                    bc_entries.append(
                        f"    {patch_name}\n    {{\n        type            fixedValue;\n"
                        f"        value           uniform ({vx} {vy} {vz});\n    }}"
                    )
                elif bc.BoundaryType == "outlet":
                    bc_entries.append(
                        f"    {patch_name}\n    {{\n        type            zeroGradient;\n    }}"
                    )
                elif bc.BoundaryType == "symmetry":
                    bc_entries.append(f"    {patch_name}\n    {{\n        type            symmetry;\n    }}")
                elif bc.BoundaryType == "open":
                    vx = getattr(bc, "FarFieldVelocityX", 0.0)
                    vy = getattr(bc, "FarFieldVelocityY", 0.0)
                    vz = getattr(bc, "FarFieldVelocityZ", 0.0)
                    bc_entries.append(
                        f"    {patch_name}\n    {{\n        type            pressureInletOutletVelocity;\n"
                        f"        value           uniform ({vx} {vy} {vz});\n    }}"
                    )

        lines = [
            "FoamFile",
            "{",
            "    version     2.0;",
            "    format      ascii;",
            "    class       volVectorField;",
            "    object      U;",
            "}",
            "",
            "dimensions      [0 1 -1 0 0 0 0];",
            "",
            f"internalField   uniform ({ux} {uy} {uz});",
            "",
            "boundaryField",
            "{",
        ]
        for entry in bc_entries:
            lines.append(entry)
        lines += ["}", ""]
        self._write_file("0/U", "\n".join(lines))

    def _write_turbulence_fields(self, ic, bcs, physics):
        """Write k, epsilon/omega/nuTilda fields based on turbulence model."""
        model = physics.TurbulenceModel

        if model in ("kEpsilon",):
            self._write_k_field(ic, bcs)
            self._write_epsilon_field(ic, bcs)
        elif model in ("kOmega", "kOmegaSST"):
            self._write_k_field(ic, bcs)
            self._write_omega_field(ic, bcs)
        elif model == "SpalartAllmaras":
            self._write_nuTilda_field(ic, bcs)

    def _write_k_field(self, ic, bcs):
        k0 = ic.TurbulentKineticEnergy if ic else 0.001
        lines = self._scalar_field_header("k", "[0 2 -2 0 0 0 0]", k0)
        for bc in bcs:
            for patch_name in _openfoam_patch_names(bc):
                if bc.BoundaryType == "wall":
                    lines.append(f"    {patch_name}\n    {{\n        type            kqRWallFunction;\n        value           uniform {k0};\n    }}")
                elif bc.BoundaryType in ("inlet", "open"):
                    lines.append(f"    {patch_name}\n    {{\n        type            fixedValue;\n        value           uniform {k0};\n    }}")
                elif bc.BoundaryType == "outlet":
                    lines.append(f"    {patch_name}\n    {{\n        type            zeroGradient;\n    }}")
                elif bc.BoundaryType == "symmetry":
                    lines.append(f"    {patch_name}\n    {{\n        type            symmetry;\n    }}")
        lines += ["}", ""]
        self._write_file("0/k", "\n".join(lines))

    def _write_epsilon_field(self, ic, bcs):
        e0 = ic.TurbulentDissipationRate if ic else 0.001
        lines = self._scalar_field_header("epsilon", "[0 2 -3 0 0 0 0]", e0)
        for bc in bcs:
            for patch_name in _openfoam_patch_names(bc):
                if bc.BoundaryType == "wall":
                    lines.append(f"    {patch_name}\n    {{\n        type            epsilonWallFunction;\n        value           uniform {e0};\n    }}")
                elif bc.BoundaryType in ("inlet", "open"):
                    lines.append(f"    {patch_name}\n    {{\n        type            fixedValue;\n        value           uniform {e0};\n    }}")
                elif bc.BoundaryType == "outlet":
                    lines.append(f"    {patch_name}\n    {{\n        type            zeroGradient;\n    }}")
                elif bc.BoundaryType == "symmetry":
                    lines.append(f"    {patch_name}\n    {{\n        type            symmetry;\n    }}")
        lines += ["}", ""]
        self._write_file("0/epsilon", "\n".join(lines))

    def _write_omega_field(self, ic, bcs):
        w0 = ic.SpecificDissipationRate if ic else 1.0
        lines = self._scalar_field_header("omega", "[0 0 -1 0 0 0 0]", w0)
        for bc in bcs:
            for patch_name in _openfoam_patch_names(bc):
                if bc.BoundaryType == "wall":
                    lines.append(f"    {patch_name}\n    {{\n        type            omegaWallFunction;\n        value           uniform {w0};\n    }}")
                elif bc.BoundaryType in ("inlet", "open"):
                    lines.append(f"    {patch_name}\n    {{\n        type            fixedValue;\n        value           uniform {w0};\n    }}")
                elif bc.BoundaryType == "outlet":
                    lines.append(f"    {patch_name}\n    {{\n        type            zeroGradient;\n    }}")
                elif bc.BoundaryType == "symmetry":
                    lines.append(f"    {patch_name}\n    {{\n        type            symmetry;\n    }}")
        lines += ["}", ""]
        self._write_file("0/omega", "\n".join(lines))

    def _write_nuTilda_field(self, ic, bcs):
        nt0 = ic.NuTilda if ic else 1.5e-4
        lines = self._scalar_field_header("nuTilda", "[0 2 -1 0 0 0 0]", nt0)
        for bc in bcs:
            for patch_name in _openfoam_patch_names(bc):
                if bc.BoundaryType == "wall":
                    lines.append(f"    {patch_name}\n    {{\n        type            fixedValue;\n        value           uniform 0;\n    }}")
                elif bc.BoundaryType in ("inlet", "open"):
                    lines.append(f"    {patch_name}\n    {{\n        type            fixedValue;\n        value           uniform {nt0};\n    }}")
                elif bc.BoundaryType == "outlet":
                    lines.append(f"    {patch_name}\n    {{\n        type            zeroGradient;\n    }}")
                elif bc.BoundaryType == "symmetry":
                    lines.append(f"    {patch_name}\n    {{\n        type            symmetry;\n    }}")
        lines += ["}", ""]
        self._write_file("0/nuTilda", "\n".join(lines))

    def _scalar_field_header(self, name, dims, value):
        return [
            "FoamFile",
            "{",
            "    version     2.0;",
            "    format      ascii;",
            "    class       volScalarField;",
            f"    object      {name};",
            "}",
            "",
            f"dimensions      {dims};",
            "",
            f"internalField   uniform {value};",
            "",
            "boundaryField",
            "{",
        ]

    # ------------------------------------------------------------------
    # decomposePar
    # ------------------------------------------------------------------
    def _write_decompose_par_dict(self):
        n = self.solver_obj.NumProcessors
        lines = [
            "FoamFile",
            "{",
            "    version     2.0;",
            "    format      ascii;",
            "    class       dictionary;",
            "    object      decomposeParDict;",
            "}",
            "",
            f"numberOfSubdomains  {n};",
            "",
            "method          scotch;",
        ]
        self._write_file("system/decomposeParDict", "\n".join(lines))

    # ------------------------------------------------------------------
    # run
    # ------------------------------------------------------------------
    def run(self):
        """Execute the OpenFOAM solver (serial or parallel with MPI)."""
        solver_app = self.solver_obj.OpenFOAMSolver
        np = self.solver_obj.NumProcessors

        FreeCAD.Console.PrintMessage(
            f"FlowStudio: Running {solver_app} in {self.case_dir}...\n"
        )

        # ---- Parallel decomposition ----
        if np > 1:
            FreeCAD.Console.PrintMessage(
                f"FlowStudio: Decomposing case for {np} processors...\n"
            )
            decompose_ok = self._run_decompose_par()
            if not decompose_ok:
                FreeCAD.Console.PrintError(
                    "FlowStudio: decomposePar failed, falling back to serial.\n"
                )
                np = 1

        # ---- Build command ----
        of_dir = getattr(self.solver_obj, "OpenFOAMDir", "")
        solver_path = solver_app
        if of_dir:
            candidate = os.path.join(of_dir, "bin", solver_app)
            if os.path.isfile(candidate):
                solver_path = candidate

        if np > 1:
            # Find MPI launcher
            mpi_exe = self._find_mpi_executable()
            if mpi_exe is None:
                FreeCAD.Console.PrintWarning(
                    "FlowStudio: mpirun/mpiexec not found, running serial.\n"
                )
                cmd = [solver_path, "-case", self.case_dir]
            else:
                cmd = [
                    mpi_exe, "-np", str(np),
                    solver_path, "-parallel", "-case", self.case_dir,
                ]
        else:
            cmd = [solver_path, "-case", self.case_dir]

        FreeCAD.Console.PrintMessage(
            f"FlowStudio: Command: {' '.join(cmd)}\n"
        )

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=self.case_dir,
            )
        except FileNotFoundError:
            FreeCAD.Console.PrintError(
                f"FlowStudio: Could not find '{solver_app}'. "
                "Make sure OpenFOAM is installed and on PATH.\n"
            )
            return False

        return True

    def _find_mpi_executable(self):
        """Find mpirun or mpiexec on PATH or in OpenFOAM dir."""
        of_dir = getattr(self.solver_obj, "OpenFOAMDir", "")
        for name in ("mpirun", "mpiexec"):
            path = shutil.which(name)
            if path:
                return path
            if of_dir:
                candidate = os.path.join(of_dir, "bin", name)
                if os.path.isfile(candidate):
                    return candidate
        return None

    def _run_decompose_par(self):
        """Run decomposePar to split the domain for parallel execution."""
        exe = "decomposePar"
        of_dir = getattr(self.solver_obj, "OpenFOAMDir", "")
        if of_dir:
            candidate = os.path.join(of_dir, "bin", exe)
            if os.path.isfile(candidate):
                exe = candidate

        try:
            result = subprocess.run(
                [exe, "-case", self.case_dir, "-force"],
                capture_output=True, text=True,
                cwd=self.case_dir,
                timeout=120,
            )
            if result.returncode == 0:
                FreeCAD.Console.PrintMessage(
                    "FlowStudio: decomposePar completed successfully.\n"
                )
                return True
            else:
                FreeCAD.Console.PrintError(
                    f"FlowStudio: decomposePar failed:\n{result.stderr}\n"
                )
                return False
        except FileNotFoundError:
            FreeCAD.Console.PrintError(
                "FlowStudio: decomposePar not found.\n"
            )
            return False
        except subprocess.TimeoutExpired:
            FreeCAD.Console.PrintError(
                "FlowStudio: decomposePar timed out.\n"
            )
            return False

    def reconstruct_par(self):
        """Run reconstructPar to merge parallel results back together."""
        np = self.solver_obj.NumProcessors
        if np <= 1:
            return True

        FreeCAD.Console.PrintMessage(
            "FlowStudio: Reconstructing parallel results...\n"
        )
        exe = "reconstructPar"
        of_dir = getattr(self.solver_obj, "OpenFOAMDir", "")
        if of_dir:
            candidate = os.path.join(of_dir, "bin", exe)
            if os.path.isfile(candidate):
                exe = candidate

        try:
            result = subprocess.run(
                [exe, "-case", self.case_dir, "-latestTime"],
                capture_output=True, text=True,
                cwd=self.case_dir,
                timeout=120,
            )
            if result.returncode == 0:
                FreeCAD.Console.PrintMessage(
                    "FlowStudio: reconstructPar completed successfully.\n"
                )
                return True
            else:
                FreeCAD.Console.PrintError(
                    f"FlowStudio: reconstructPar failed:\n{result.stderr}\n"
                )
                return False
        except Exception as e:
            FreeCAD.Console.PrintError(
                f"FlowStudio: reconstructPar error: {e}\n"
            )
            return False

    # ------------------------------------------------------------------
    # read_results
    # ------------------------------------------------------------------
    def read_results(self):
        """Find the latest time directory and return its path."""
        time_dirs = []
        for entry in os.listdir(self.case_dir):
            try:
                t = float(entry)
                time_dirs.append((t, entry))
            except ValueError:
                continue
        if time_dirs:
            time_dirs.sort()
            latest = time_dirs[-1][1]
            result_dir = os.path.join(self.case_dir, latest)
            FreeCAD.Console.PrintMessage(
                f"FlowStudio: Results found at t={latest}\n"
            )
            return result_dir
        else:
            FreeCAD.Console.PrintWarning("FlowStudio: No result time directories found.\n")
            return None

    # ------------------------------------------------------------------
    # file I/O
    # ------------------------------------------------------------------
    def _write_file(self, rel_path, content):
        path = os.path.join(self.case_dir, rel_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content + "\n")
