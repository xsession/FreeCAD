# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""FluidX3D solver backend – setup.cpp generation and execution.

FluidX3D uses the Lattice Boltzmann Method (LBM) on GPU via OpenCL.
This runner:
  1. Exports the geometry as binary .stl
  2. Generates a ``setup.cpp`` source file with the simulation parameters
  3. Compiles FluidX3D with the generated setup
  4. Runs the compiled binary
  5. Reads .vtk results

See: https://github.com/ProjectPhysX/FluidX3D
"""

import math
import os
import subprocess
import FreeCAD

from flow_studio.solvers.base_solver import BaseSolverRunner


class FluidX3DRunner(BaseSolverRunner):
    """Generate and run FluidX3D lattice Boltzmann simulations."""

    name = "FluidX3D"

    # ------------------------------------------------------------------
    def _find_objects(self, type_str):
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

    def _ic(self):
        objs = self._find_objects("FlowStudio::InitialConditions")
        return objs[0] if objs else None

    # ------------------------------------------------------------------
    def check(self):
        """Check FluidX3D repo / executable availability."""
        exe = getattr(self.solver_obj, "FluidX3DExecutable", "")
        if exe and os.path.isfile(exe):
            return True
        # Check if FluidX3D repo is cloned nearby
        return os.path.isdir(os.path.join(self.case_dir, "FluidX3D"))

    # ------------------------------------------------------------------
    def write_case(self):
        """Generate setup.cpp and export geometry as .stl."""
        FreeCAD.Console.PrintMessage("FlowStudio: Writing FluidX3D setup...\n")

        os.makedirs(self.case_dir, exist_ok=True)
        stl_dir = os.path.join(self.case_dir, "stl")
        os.makedirs(stl_dir, exist_ok=True)

        # Export geometry
        self._export_geometry(stl_dir)

        # Generate setup.cpp
        self._generate_setup_cpp()

        # Generate defines.hpp overrides
        self._generate_defines()

        FreeCAD.Console.PrintMessage(
            f"FlowStudio: FluidX3D case written to {self.case_dir}\n"
        )

    # ------------------------------------------------------------------
    def _export_geometry(self, stl_dir):
        """Export referenced shapes as binary STL for FluidX3D voxelization."""
        mesh_objs = self._find_objects("FlowStudio::MeshGmsh")
        if not mesh_objs:
            FreeCAD.Console.PrintWarning(
                "FlowStudio: No mesh object found - using shape from analysis.\n"
            )
            return

        mesh_obj = mesh_objs[0]
        part = mesh_obj.Part
        if part and hasattr(part, "Shape"):
            stl_path = os.path.join(stl_dir, "geometry.stl")
            part.Shape.exportStl(stl_path)
            self.stl_file = stl_path
            FreeCAD.Console.PrintMessage(
                f"FlowStudio: Exported STL -> {stl_path}\n"
            )
        else:
            self.stl_file = None

    # ------------------------------------------------------------------
    def _generate_setup_cpp(self):
        """Generate the FluidX3D main_setup() function."""
        physics = self._physics()
        material = self._material()
        ic = self._ic()
        solver = self.solver_obj

        # Simulation parameters
        vram = getattr(solver, "FluidX3DVRAM", 2000)
        resolution = getattr(solver, "FluidX3DResolution", 256)
        time_steps = getattr(solver, "FluidX3DTimeSteps", 10000)
        nu = material.KinematicViscosity if material else 1.48e-5
        rho = material.Density if material else 1.225

        # Multi-GPU settings
        multi_gpu = getattr(solver, "FluidX3DMultiGPU", False)
        num_gpus = max(1, getattr(solver, "FluidX3DNumGPUs", 1))

        # Compute LBM parameters
        # FloEFD-like automatic parameter mapping
        lbm_u = 0.075  # safe LBM velocity
        Re_target = 10000.0  # default Re
        lbm_nu = lbm_u * float(resolution) / Re_target

        # Velocity from initial conditions
        ux = ic.Ux if ic else 0.0
        uy = ic.Uy if ic else 0.0
        uz = ic.Uz if ic else 0.0
        u_mag = math.sqrt(ux**2 + uy**2 + uz**2)
        if u_mag > 0:
            Re_target = u_mag * 1.0 / nu  # approximate Re with L=1m
            lbm_nu = lbm_u * float(resolution) / Re_target

        # Gravity
        has_gravity = physics.Gravity if physics else False
        gx, gy, gz = 0.0, 0.0, 0.0
        if has_gravity:
            gz = -0.001  # LBM gravity magnitude

        # Boundary conditions
        bcs = [o for o in self.analysis.Group if hasattr(o, "BoundaryType")]

        # Determine extensions
        extensions = set()
        extensions.add("EQUILIBRIUM_BOUNDARIES")

        if physics:
            if physics.TurbulenceModel in ("LES-Smagorinsky", "LES-WALE"):
                extensions.add("SUBGRID")
            if physics.Gravity:
                extensions.add("VOLUME_FORCE")
            if physics.FreeSurface:
                extensions.add("SURFACE")
            if physics.HeatTransfer:
                extensions.add("TEMPERATURE")

        for bc in bcs:
            if getattr(bc, "WallType", "").startswith("Moving"):
                extensions.add("MOVING_BOUNDARIES")

        # Generate setup.cpp
        stl_rel = "../stl/geometry.stl"
        lines = [
            '#include "setup.hpp"',
            "",
            "void main_setup() {",
            f"    // FlowStudio auto-generated setup for FluidX3D",
            f"    // Re ~ {Re_target:.0f}, resolution = {resolution}",
            f"    // VRAM budget: {vram} MB",
        ]

        if multi_gpu and num_gpus > 1:
            lines.append(f"    // Multi-GPU: {num_gpus} devices")
        lines.append("")

        # Multi-GPU: domain decomposition along longest axis
        if multi_gpu and num_gpus > 1:
            # Split the domain along the Z axis by default
            lines += [
                f"    // Multi-GPU domain decomposition ({num_gpus} GPUs)",
                f"    const uint Dx={num_gpus}u, Dy=1u, Dz=1u;  // GPU grid topology",
                f"    const uint3 lbm_N = resolution(float3(1.0f, 1.0f, 1.0f), {vram}u*Dx*Dy*Dz);",
                f"    const float lbm_u = {lbm_u}f;",
                f"    const float lbm_nu = {lbm_nu:.8f}f;",
                f"    const ulong lbm_T = {time_steps}ull;",
                "",
            ]
        else:
            lines += [
                f"    const uint3 lbm_N = resolution(float3(1.0f, 1.0f, 1.0f), {vram}u);",
                f"    const float lbm_u = {lbm_u}f;",
                f"    const float lbm_nu = {lbm_nu:.8f}f;",
                f"    const ulong lbm_T = {time_steps}ull;",
                "",
            ]

        # LBM constructor
        if multi_gpu and num_gpus > 1:
            if has_gravity and "VOLUME_FORCE" in extensions:
                lines.append(
                    f"    LBM lbm(lbm_N, Dx, Dy, Dz, lbm_nu, {gx}f, {gy}f, {gz}f);"
                )
            else:
                lines.append(
                    f"    LBM lbm(lbm_N, Dx, Dy, Dz, lbm_nu);"
                )
        else:
            if has_gravity and "VOLUME_FORCE" in extensions:
                lines.append(
                    f"    LBM lbm(lbm_N, lbm_nu, {gx}f, {gy}f, {gz}f);"
                )
            else:
                lines.append("    LBM lbm(lbm_N, lbm_nu);")

        lines.append("")

        # Geometry loading
        if self.stl_file:
            lines += [
                f'    Mesh* mesh = read_stl(get_exe_path()+"{stl_rel}");',
                "    const float size = 0.8f*min(lbm.size().x, min(lbm.size().y, lbm.size().z));",
                "    mesh->scale(size/mesh->get_max_size());",
                "    mesh->translate(lbm.center()-mesh->get_bounding_box_center());",
                "    lbm.voxelize_mesh_on_device(mesh);",
                "",
            ]

        # Boundary setup
        lines += [
            "    const uint Nx=lbm.get_Nx(), Ny=lbm.get_Ny(), Nz=lbm.get_Nz();",
            "    parallel_for(lbm.get_N(), [&](ulong n) {",
            "        uint x=0u, y=0u, z=0u; lbm.coordinates(n, x, y, z);",
        ]

        # Initial velocity
        if u_mag > 0 and ux != 0:
            lines.append(f"        if(lbm.flags[n]!=TYPE_S) lbm.u.x[n] = lbm_u;")
        elif u_mag > 0 and uy != 0:
            lines.append(f"        if(lbm.flags[n]!=TYPE_S) lbm.u.y[n] = lbm_u;")
        elif u_mag > 0 and uz != 0:
            lines.append(f"        if(lbm.flags[n]!=TYPE_S) lbm.u.z[n] = lbm_u;")

        # Boundary flags
        lines += [
            "        if(x==0u||x==Nx-1u||y==0u||y==Ny-1u||z==0u||z==Nz-1u) lbm.flags[n] = TYPE_E;",
            "    });",
            "",
        ]

        # Visualization
        lines += [
            "    lbm.graphics.visualization_modes = VIS_FLAG_SURFACE|VIS_Q_CRITERION;",
            "",
            "    lbm.run(0u, lbm_T);  // initialize",
            "",
            "    while(lbm.get_t() <= lbm_T) {",
            "        lbm.run(1u, lbm_T);",
            "    }",
            "}",
        ]

        setup_path = os.path.join(self.case_dir, "setup.cpp")
        with open(setup_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    # ------------------------------------------------------------------
    def _generate_defines(self):
        """Generate a defines_override.hpp with required extensions."""
        physics = self._physics()
        extensions = set()
        extensions.add("EQUILIBRIUM_BOUNDARIES")

        if physics:
            if physics.TurbulenceModel in ("LES-Smagorinsky", "LES-WALE"):
                extensions.add("SUBGRID")
            if physics.Gravity:
                extensions.add("VOLUME_FORCE")
            if physics.FreeSurface:
                extensions.add("SURFACE")
            if physics.HeatTransfer:
                extensions.add("TEMPERATURE")

        # Multi-GPU support
        multi_gpu = getattr(self.solver_obj, "FluidX3DMultiGPU", False)
        num_gpus = max(1, getattr(self.solver_obj, "FluidX3DNumGPUs", 1))
        if multi_gpu and num_gpus > 1:
            extensions.add("MULTI_GPU")

        # Check for precision
        precision = getattr(self.solver_obj, "FluidX3DPrecision", "FP32/FP16S")
        if "FP16S" in precision:
            extensions.add("FP16S")
        elif "FP16C" in precision:
            extensions.add("FP16C")

        lines = [
            "// FlowStudio auto-generated defines for FluidX3D",
            "// Copy these #define lines into your FluidX3D defines.hpp",
            "",
        ]
        for ext in sorted(extensions):
            lines.append(f"#define {ext}")
        lines.append("")

        path = os.path.join(self.case_dir, "defines_override.hpp")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    # ------------------------------------------------------------------
    def run(self):
        """Compile and run FluidX3D (single or multi-GPU)."""
        exe = getattr(self.solver_obj, "FluidX3DExecutable", "")
        multi_gpu = getattr(self.solver_obj, "FluidX3DMultiGPU", False)
        num_gpus = max(1, getattr(self.solver_obj, "FluidX3DNumGPUs", 1))

        if exe and os.path.isfile(exe):
            if multi_gpu and num_gpus > 1:
                FreeCAD.Console.PrintMessage(
                    f"FlowStudio: Running FluidX3D on {num_gpus} GPUs: {exe}\n"
                )
            else:
                FreeCAD.Console.PrintMessage(
                    f"FlowStudio: Running FluidX3D: {exe}\n"
                )
            try:
                # FluidX3D handles multi-GPU internally via OpenCL.
                # We pass the number of GPUs via environment variable.
                env = os.environ.copy()
                if multi_gpu and num_gpus > 1:
                    env["FLUIDX3D_DEVICES"] = str(num_gpus)

                self.process = subprocess.Popen(
                    [exe],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=self.case_dir,
                    env=env,
                )
                return True
            except Exception as e:
                FreeCAD.Console.PrintError(f"FlowStudio: FluidX3D error: {e}\n")
                return False
        else:
            FreeCAD.Console.PrintWarning(
                "FlowStudio: FluidX3D executable not found. "
                "Please set the path in solver settings or compile from the "
                "generated setup.cpp. See: https://github.com/ProjectPhysX/FluidX3D\n"
            )
            FreeCAD.Console.PrintMessage(
                f"FlowStudio: Setup files generated at {self.case_dir}\n"
                "To compile:\n"
                "  1. Copy setup.cpp -> FluidX3D/src/setup.cpp\n"
                "  2. Apply defines from defines_override.hpp\n"
                "  3. Run: make -j\n"
            )
            return False

    # ------------------------------------------------------------------
    def read_results(self):
        """Look for exported .vtk files."""
        vtk_files = []
        for root, dirs, files in os.walk(self.case_dir):
            for f in files:
                if f.endswith(".vtk"):
                    vtk_files.append(os.path.join(root, f))
        if vtk_files:
            FreeCAD.Console.PrintMessage(
                f"FlowStudio: Found {len(vtk_files)} VTK result file(s)\n"
            )
            return vtk_files[-1]
        else:
            FreeCAD.Console.PrintWarning(
                "FlowStudio: No VTK result files found.\n"
            )
            return None
