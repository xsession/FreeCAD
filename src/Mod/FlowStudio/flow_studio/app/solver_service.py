# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Application service for the FlowStudio solver task panel."""

from __future__ import annotations


class FlowStudioSolverService:
    """Backend-facing service for solver settings persistence."""

    FIELD_NAMES = (
        "SolverBackend",
        "OpenFOAMSolver",
        "MaxIterations",
        "ConvergenceTolerance",
        "NumProcessors",
        "ConvectionScheme",
        "ElmerSolverBinary",
        "FluidX3DPrecision",
        "FluidX3DResolution",
        "FluidX3DTimeSteps",
        "FluidX3DVRAM",
        "FluidX3DMultiGPU",
        "FluidX3DNumGPUs",
        "Geant4Executable",
        "Geant4PhysicsList",
        "Geant4EventCount",
        "Geant4Threads",
        "Geant4MacroName",
        "Geant4EnableVisualization",
        "MultiSolverEnabled",
        "MultiSolverBackends",
        "SoftRuntimeWarningSeconds",
        "MaxRuntimeSeconds",
        "StallTimeoutSeconds",
        "MinProgressPercent",
        "AbortOnThreshold",
    )

    def read_settings(self, obj):
        return {name: getattr(obj, name) for name in self.FIELD_NAMES}

    def persist_settings(self, obj, settings):
        for name in self.FIELD_NAMES:
            setattr(obj, name, settings[name])