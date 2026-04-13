# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Solver object – multi-solver settings container."""

from flow_studio.objects.base_object import BaseFlowObject


class Solver(BaseFlowObject):
    """CFD Solver configuration – supports multiple backends."""

    Type = "FlowStudio::Solver"

    def __init__(self, obj):
        super().__init__(obj)

        # Solver backend selection
        obj.addProperty(
            "App::PropertyEnumeration", "SolverBackend", "Solver",
            "CFD solver to use"
        )
        obj.SolverBackend = [
            "OpenFOAM",
            "FluidX3D",
            "SU2",
        ]
        obj.SolverBackend = "OpenFOAM"

        # --- OpenFOAM-specific ---
        obj.addProperty(
            "App::PropertyEnumeration", "OpenFOAMSolver", "OpenFOAM",
            "OpenFOAM application solver"
        )
        obj.OpenFOAMSolver = [
            "simpleFoam",
            "pimpleFoam",
            "pisoFoam",
            "icoFoam",
            "rhoSimpleFoam",
            "rhoPimpleFoam",
            "buoyantSimpleFoam",
            "buoyantPimpleFoam",
            "interFoam",
            "potentialFoam",
        ]
        obj.OpenFOAMSolver = "simpleFoam"

        obj.addProperty(
            "App::PropertyInteger", "MaxIterations", "OpenFOAM",
            "Maximum number of iterations (steady) or time steps (transient)"
        )
        obj.MaxIterations = 2000

        obj.addProperty(
            "App::PropertyFloat", "ConvergenceTolerance", "OpenFOAM",
            "Residual convergence criterion"
        )
        obj.ConvergenceTolerance = 1e-4

        obj.addProperty(
            "App::PropertyFloat", "RelaxationFactorU", "OpenFOAM",
            "Under-relaxation factor for velocity"
        )
        obj.RelaxationFactorU = 0.7

        obj.addProperty(
            "App::PropertyFloat", "RelaxationFactorP", "OpenFOAM",
            "Under-relaxation factor for pressure"
        )
        obj.RelaxationFactorP = 0.3

        obj.addProperty(
            "App::PropertyEnumeration", "PressureSolver", "OpenFOAM",
            "Linear solver for pressure equation"
        )
        obj.PressureSolver = ["GAMG", "PCG", "DIC"]
        obj.PressureSolver = "GAMG"

        obj.addProperty(
            "App::PropertyEnumeration", "VelocitySolver", "OpenFOAM",
            "Linear solver for velocity equation"
        )
        obj.VelocitySolver = ["smoothSolver", "PBiCGStab", "DILU"]
        obj.VelocitySolver = "smoothSolver"

        obj.addProperty(
            "App::PropertyEnumeration", "ConvectionScheme", "OpenFOAM",
            "Convection discretisation scheme"
        )
        obj.ConvectionScheme = [
            "linearUpwind",
            "upwind",
            "linear",
            "limitedLinear",
            "LUST",
        ]
        obj.ConvectionScheme = "linearUpwind"

        obj.addProperty(
            "App::PropertyInteger", "NumProcessors", "Parallel",
            "Number of MPI processes for parallel run (OpenFOAM / Elmer)"
        )
        obj.NumProcessors = 1

        obj.addProperty(
            "App::PropertyBool", "AutoParallel", "Parallel",
            "Automatically detect optimal number of processors"
        )
        obj.AutoParallel = False

        # --- FluidX3D-specific ---
        obj.addProperty(
            "App::PropertyEnumeration", "FluidX3DPrecision", "FluidX3D",
            "Floating-point precision for FluidX3D"
        )
        obj.FluidX3DPrecision = ["FP32/FP32", "FP32/FP16S", "FP32/FP16C"]
        obj.FluidX3DPrecision = "FP32/FP16S"

        obj.addProperty(
            "App::PropertyInteger", "FluidX3DResolution", "FluidX3D",
            "Grid resolution along longest axis"
        )
        obj.FluidX3DResolution = 256

        obj.addProperty(
            "App::PropertyInteger", "FluidX3DTimeSteps", "FluidX3D",
            "Number of LBM time steps to run"
        )
        obj.FluidX3DTimeSteps = 10000

        obj.addProperty(
            "App::PropertyInteger", "FluidX3DVRAM", "FluidX3D",
            "GPU VRAM budget [MB]"
        )
        obj.FluidX3DVRAM = 2000

        obj.addProperty(
            "App::PropertyEnumeration", "FluidX3DExtensions", "FluidX3D",
            "FluidX3D extensions to enable"
        )
        obj.FluidX3DExtensions = [
            "None",
            "VOLUME_FORCE",
            "EQUILIBRIUM_BOUNDARIES",
            "MOVING_BOUNDARIES",
            "SUBGRID",
            "SURFACE",
            "TEMPERATURE",
            "FORCE_FIELD",
        ]
        obj.FluidX3DExtensions = "EQUILIBRIUM_BOUNDARIES"

        obj.addProperty(
            "App::PropertyBool", "FluidX3DMultiGPU", "FluidX3D",
            "Enable multi-GPU domain decomposition"
        )
        obj.FluidX3DMultiGPU = False

        obj.addProperty(
            "App::PropertyInteger", "FluidX3DNumGPUs", "FluidX3D",
            "Number of GPUs to use"
        )
        obj.FluidX3DNumGPUs = 1

        # Transient settings
        obj.addProperty(
            "App::PropertyFloat", "TimeStep", "Transient",
            "Time step size [s] (0 = auto CFL-based)"
        )
        obj.TimeStep = 0.0

        obj.addProperty(
            "App::PropertyFloat", "EndTime", "Transient",
            "End time [s]"
        )
        obj.EndTime = 1.0

        obj.addProperty(
            "App::PropertyFloat", "MaxCourantNumber", "Transient",
            "Maximum Courant number for adaptive time stepping"
        )
        obj.MaxCourantNumber = 1.0

        obj.addProperty(
            "App::PropertyInteger", "WriteInterval", "Output",
            "Write result every N iterations/steps"
        )
        obj.WriteInterval = 100

        # Executable paths
        obj.addProperty(
            "App::PropertyPath", "OpenFOAMDir", "Paths",
            "Path to OpenFOAM installation (e.g. /opt/openfoam11)"
        )
        obj.addProperty(
            "App::PropertyPath", "FluidX3DExecutable", "Paths",
            "Path to FluidX3D executable"
        )
        obj.addProperty(
            "App::PropertyPath", "SU2Executable", "Paths",
            "Path to SU2_CFD executable"
        )

    def onChanged(self, obj, prop):
        """React to property changes."""
        if prop == "AutoParallel" and hasattr(obj, "AutoParallel"):
            if obj.AutoParallel:
                self._auto_detect_parallel(obj)

    @staticmethod
    def _auto_detect_parallel(obj):
        """Auto-detect optimal parallel settings based on hardware."""
        try:
            from flow_studio.solver_deps import recommend_parallel_settings
            settings = recommend_parallel_settings()

            if hasattr(obj, "NumProcessors"):
                backend = getattr(obj, "SolverBackend", "OpenFOAM")
                if backend == "OpenFOAM":
                    obj.NumProcessors = settings["OpenFOAM"]["NumProcessors"]
                elif backend in ("Elmer",):
                    obj.NumProcessors = settings["Elmer"]["NumProcessors"]

            if hasattr(obj, "FluidX3DMultiGPU"):
                fx3d = settings.get("FluidX3D", {})
                obj.FluidX3DMultiGPU = fx3d.get("MultiGPU", False)
                obj.FluidX3DNumGPUs = max(1, fx3d.get("NumGPUs", 1))
        except Exception:
            pass  # Silently fail if detection unavailable
