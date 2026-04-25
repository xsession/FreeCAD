# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Presenter and view-state helpers for the FlowStudio solver task panel."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SolverSettings:
    solver_backend: str
    openfoam_solver: str
    max_iterations: int
    convergence_tolerance: float
    num_processors: int
    convection_scheme: str
    elmer_solver_binary: str
    fluidx3d_precision: str
    fluidx3d_resolution: int
    fluidx3d_time_steps: int
    fluidx3d_vram: int
    fluidx3d_multi_gpu: bool
    fluidx3d_num_gpus: int
    geant4_executable: str
    geant4_physics_list: str
    geant4_event_count: int
    geant4_threads: int
    geant4_macro_name: str
    geant4_enable_visualization: bool
    multi_solver_enabled: bool
    multi_solver_backends: tuple[str, ...]
    soft_runtime_warning_seconds: int
    max_runtime_seconds: int
    stall_timeout_seconds: int
    min_progress_percent: float
    abort_on_threshold: bool


class SolverPresenter:
    """Frontend-neutral presenter for solver validation and persistence."""

    BACKEND_PAGE_INDEX = {
        "OpenFOAM": 0,
        "Elmer": 1,
        "FluidX3D": 2,
        "SU2": 3,
        "Geant4": 4,
    }

    def __init__(self, service=None):
        if service is None:
            from flow_studio.app import FlowStudioSolverService

            service = FlowStudioSolverService()
        self._service = service

    @staticmethod
    def normalized_multi_solver_backends(value):
        if isinstance(value, str):
            candidates = [item.strip() for item in value.split(",")]
        else:
            candidates = [str(item).strip() for item in (value or ())]
        return tuple(dict.fromkeys(item for item in candidates if item))

    def read_settings(self, obj):
        return self._coerce_settings(self._service.read_settings(obj))

    def persist_settings(self, obj, settings):
        self._service.persist_settings(obj, self._to_payload(settings))

    def build_validation(self, settings):
        if settings.multi_solver_enabled:
            if len(settings.multi_solver_backends) < 2:
                return (
                    "incomplete",
                    "Select multiple solver backends",
                    "Enable at least two enterprise solver backends for simultaneous multi-solver execution.",
                )
            if settings.solver_backend not in settings.multi_solver_backends:
                return (
                    "incomplete",
                    "Primary backend missing from multi-solver selection",
                    "Include the currently selected backend in the multi-solver backend list.",
                )

        if settings.solver_backend == "Geant4" and not settings.geant4_executable.strip():
            return (
                "incomplete",
                "Geant4 executable required",
                "Set the compiled Geant4 application path before launching the solver.",
            )

        if (
            settings.soft_runtime_warning_seconds > 0
            and settings.max_runtime_seconds > 0
            and settings.soft_runtime_warning_seconds > settings.max_runtime_seconds
        ):
            return (
                "warning",
                "Runtime thresholds out of order",
                "The soft runtime warning must not exceed the hard runtime limit.",
            )

        if (
            settings.stall_timeout_seconds > 0
            and settings.max_runtime_seconds > 0
            and settings.stall_timeout_seconds > settings.max_runtime_seconds
        ):
            return (
                "warning",
                "Stall timeout exceeds hard runtime limit",
                "Reduce the stall timeout or increase the hard runtime limit so both thresholds can be applied consistently.",
            )

        if settings.min_progress_percent < 0.0 or settings.min_progress_percent > 100.0:
            return (
                "warning",
                "Minimum progress threshold invalid",
                "Use a minimum progress threshold between 0 and 100 percent.",
            )

        return ("", "", "")

    def backend_page_index(self, backend_name):
        return self.BACKEND_PAGE_INDEX.get(backend_name, 0)

    def _coerce_settings(self, payload):
        return SolverSettings(
            solver_backend=str(payload["SolverBackend"]),
            openfoam_solver=str(payload["OpenFOAMSolver"]),
            max_iterations=int(payload["MaxIterations"]),
            convergence_tolerance=float(payload["ConvergenceTolerance"]),
            num_processors=int(payload["NumProcessors"]),
            convection_scheme=str(payload["ConvectionScheme"]),
            elmer_solver_binary=str(payload["ElmerSolverBinary"]),
            fluidx3d_precision=str(payload["FluidX3DPrecision"]),
            fluidx3d_resolution=int(payload["FluidX3DResolution"]),
            fluidx3d_time_steps=int(payload["FluidX3DTimeSteps"]),
            fluidx3d_vram=int(payload["FluidX3DVRAM"]),
            fluidx3d_multi_gpu=bool(payload["FluidX3DMultiGPU"]),
            fluidx3d_num_gpus=int(payload["FluidX3DNumGPUs"]),
            geant4_executable=str(payload["Geant4Executable"]),
            geant4_physics_list=str(payload["Geant4PhysicsList"]),
            geant4_event_count=int(payload["Geant4EventCount"]),
            geant4_threads=int(payload["Geant4Threads"]),
            geant4_macro_name=str(payload["Geant4MacroName"]),
            geant4_enable_visualization=bool(payload["Geant4EnableVisualization"]),
            multi_solver_enabled=bool(payload["MultiSolverEnabled"]),
            multi_solver_backends=self.normalized_multi_solver_backends(payload["MultiSolverBackends"]),
            soft_runtime_warning_seconds=int(payload["SoftRuntimeWarningSeconds"]),
            max_runtime_seconds=int(payload["MaxRuntimeSeconds"]),
            stall_timeout_seconds=int(payload["StallTimeoutSeconds"]),
            min_progress_percent=float(payload["MinProgressPercent"]),
            abort_on_threshold=bool(payload["AbortOnThreshold"]),
        )

    def _to_payload(self, settings):
        return {
            "SolverBackend": settings.solver_backend,
            "OpenFOAMSolver": settings.openfoam_solver,
            "MaxIterations": settings.max_iterations,
            "ConvergenceTolerance": settings.convergence_tolerance,
            "NumProcessors": settings.num_processors,
            "ConvectionScheme": settings.convection_scheme,
            "ElmerSolverBinary": settings.elmer_solver_binary,
            "FluidX3DPrecision": settings.fluidx3d_precision,
            "FluidX3DResolution": settings.fluidx3d_resolution,
            "FluidX3DTimeSteps": settings.fluidx3d_time_steps,
            "FluidX3DVRAM": settings.fluidx3d_vram,
            "FluidX3DMultiGPU": settings.fluidx3d_multi_gpu,
            "FluidX3DNumGPUs": settings.fluidx3d_num_gpus,
            "Geant4Executable": settings.geant4_executable,
            "Geant4PhysicsList": settings.geant4_physics_list,
            "Geant4EventCount": settings.geant4_event_count,
            "Geant4Threads": settings.geant4_threads,
            "Geant4MacroName": settings.geant4_macro_name,
            "Geant4EnableVisualization": settings.geant4_enable_visualization,
            "MultiSolverEnabled": settings.multi_solver_enabled,
            "MultiSolverBackends": list(settings.multi_solver_backends),
            "SoftRuntimeWarningSeconds": settings.soft_runtime_warning_seconds,
            "MaxRuntimeSeconds": settings.max_runtime_seconds,
            "StallTimeoutSeconds": settings.stall_timeout_seconds,
            "MinProgressPercent": settings.min_progress_percent,
            "AbortOnThreshold": settings.abort_on_threshold,
        }