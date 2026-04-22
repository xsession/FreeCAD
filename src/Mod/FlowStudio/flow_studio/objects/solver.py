# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Solver object – multi-solver settings container."""

from flow_studio.objects.base_object import BaseFlowObject


def recommended_parallel_defaults(backend="OpenFOAM"):
    """Return default parallel settings for a solver backend."""
    defaults = {
        "AutoParallel": False,
        "NumProcessors": 1,
        "ElmerSolverBinary": "ElmerSolver",
    }

    try:
        from flow_studio.runtime.dependencies import recommend_parallel_settings

        settings = recommend_parallel_settings()
        backend_key = backend if backend in ("OpenFOAM", "Elmer") else "OpenFOAM"
        backend_settings = settings.get(backend_key, {})
        num_processors = max(
            1,
            int(backend_settings.get("NumProcessors", settings.get("cpu_physical", 1) or 1)),
        )
        defaults["AutoParallel"] = True
        defaults["NumProcessors"] = num_processors
        defaults["ElmerSolverBinary"] = (
            "ElmerSolver_mpi"
            if settings.get("Elmer", {}).get("mpi_available") and num_processors > 1
            else "ElmerSolver"
        )
    except Exception:
        pass

    return defaults


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
            "Elmer",
            "FluidX3D",
            "SU2",
            "Geant4",
            "Raysect",
            "Meep",
            "openEMS",
            "Optiland",
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

        # --- Elmer-specific ---
        obj.addProperty(
            "App::PropertyEnumeration", "ElmerSolverBinary", "Elmer",
            "Elmer solver executable used for CLI execution"
        )
        obj.ElmerSolverBinary = [
            "ElmerSolver",
            "ElmerSolver_mpi",
        ]
        obj.ElmerSolverBinary = "ElmerSolver"

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

        obj.addProperty(
            "App::PropertyBool", "MultiSolverEnabled", "Parallel",
            "Submit the same model to multiple enterprise solver backends in parallel"
        )
        obj.MultiSolverEnabled = False

        obj.addProperty(
            "App::PropertyStringList", "MultiSolverBackends", "Parallel",
            "Selected enterprise backends for multi-solver submissions"
        )
        obj.MultiSolverBackends = ["OpenFOAM", "Elmer"]

        parallel_defaults = recommended_parallel_defaults(obj.SolverBackend)
        obj.NumProcessors = parallel_defaults["NumProcessors"]
        obj.ElmerSolverBinary = parallel_defaults["ElmerSolverBinary"]
        obj.AutoParallel = parallel_defaults["AutoParallel"]

        obj.addProperty(
            "App::PropertyInteger", "SoftRuntimeWarningSeconds", "Runtime Thresholds",
            "Emit a runtime warning after this many seconds (0 disables)"
        )
        obj.SoftRuntimeWarningSeconds = 0

        obj.addProperty(
            "App::PropertyInteger", "MaxRuntimeSeconds", "Runtime Thresholds",
            "Stop the solver after this many wall-clock seconds (0 disables)"
        )
        obj.MaxRuntimeSeconds = 0

        obj.addProperty(
            "App::PropertyInteger", "StallTimeoutSeconds", "Runtime Thresholds",
            "Stop the solver if no meaningful progress is observed within this many seconds (0 disables)"
        )
        obj.StallTimeoutSeconds = 0

        obj.addProperty(
            "App::PropertyFloat", "MinProgressPercent", "Runtime Thresholds",
            "Minimum expected progress percentage within a stall window"
        )
        obj.MinProgressPercent = 0.0

        obj.addProperty(
            "App::PropertyBool", "AbortOnThreshold", "Runtime Thresholds",
            "Abort the run when a runtime threshold is exceeded"
        )
        obj.AbortOnThreshold = True

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

        # --- Geant4-specific ---
        obj.addProperty(
            "App::PropertyString", "Geant4PhysicsList", "Geant4",
            "Reference physics list used by the generated Geant4 run scaffold"
        )
        obj.Geant4PhysicsList = "FTFP_BERT"

        obj.addProperty(
            "App::PropertyInteger", "Geant4EventCount", "Geant4",
            "Number of primary events to simulate"
        )
        obj.Geant4EventCount = 1000

        obj.addProperty(
            "App::PropertyInteger", "Geant4Threads", "Geant4",
            "Number of Geant4 worker threads for MT-enabled applications"
        )
        obj.Geant4Threads = 1

        obj.addProperty(
            "App::PropertyString", "Geant4MacroName", "Geant4",
            "Primary Geant4 macro file written into the case directory"
        )
        obj.Geant4MacroName = "run.mac"

        obj.addProperty(
            "App::PropertyBool", "Geant4EnableVisualization", "Geant4",
            "Emit visualization commands in the generated Geant4 macro"
        )
        obj.Geant4EnableVisualization = False

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
        obj.addProperty(
            "App::PropertyPath", "Geant4Executable", "Paths",
            "Path to the compiled Geant4 application executable"
        )

    def onChanged(self, obj, prop):
        """React to property changes."""
        if prop in ("AutoParallel", "SolverBackend") and hasattr(obj, "AutoParallel"):
            if obj.AutoParallel:
                self._auto_detect_parallel(obj)

    @staticmethod
    def _auto_detect_parallel(obj):
        """Auto-detect optimal parallel settings based on hardware."""
        try:
            backend = getattr(obj, "SolverBackend", "OpenFOAM")
            defaults = recommended_parallel_defaults(backend)

            if hasattr(obj, "NumProcessors"):
                obj.NumProcessors = defaults["NumProcessors"]

            if hasattr(obj, "ElmerSolverBinary"):
                obj.ElmerSolverBinary = defaults["ElmerSolverBinary"]

            if hasattr(obj, "FluidX3DMultiGPU"):
                from flow_studio.runtime.dependencies import recommend_parallel_settings

                settings = recommend_parallel_settings()
                fx3d = settings.get("FluidX3D", {})
                obj.FluidX3DMultiGPU = fx3d.get("MultiGPU", False)
                obj.FluidX3DNumGPUs = max(1, fx3d.get("NumGPUs", 1))
        except Exception:
            pass  # Silently fail if detection unavailable
