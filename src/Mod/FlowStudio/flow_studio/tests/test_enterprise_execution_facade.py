# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Tests for legacy-analysis submission through enterprise services."""

from pathlib import Path
from types import SimpleNamespace

from flow_studio.enterprise.adapters.elmer import ElmerSolverAdapter
from flow_studio.enterprise.adapters.openfoam import OpenFOAMSolverAdapter
from flow_studio.enterprise.services.execution_facade import (
    LegacyExecutionFacade,
    LegacyExecutionRequest,
)
from flow_studio.enterprise.services.jobs import InMemoryJobService


def _make_child(flow_type: str, **kwargs):
    return SimpleNamespace(FlowType=flow_type, **kwargs)


def test_legacy_execution_facade_submits_translated_analysis(tmp_path: Path):
    analysis = SimpleNamespace(
        Name="A1",
        Label="A1",
        PhysicsDomain="CFD",
        AnalysisType="General",
        SolverBackend="OpenFOAM",
        Group=[
            _make_child("FlowStudio::MeshGmsh", CharacteristicLength=5.0, Part=None),
            _make_child(
                "FlowStudio::PhysicsModel",
                FlowRegime="Turbulent",
                TurbulenceModel="kOmegaSST",
                Compressibility="Incompressible",
                TimeModel="Steady",
                HeatTransfer=False,
                Gravity=False,
                Buoyancy=False,
            ),
            _make_child(
                "FlowStudio::FluidMaterial",
                MaterialName="Air",
                Density=1.225,
                DynamicViscosity=1.81e-5,
                SpecificHeat=1005.0,
                ThermalConductivity=0.0257,
            ),
            _make_child(
                "FlowStudio::Solver",
                OpenFOAMSolver="simpleFoam",
                MaxIterations=500,
                ConvergenceTolerance=1e-4,
                WriteInterval=50,
                NumProcessors=2,
            ),
        ],
    )

    facade = LegacyExecutionFacade(
        InMemoryJobService({"openfoam.primary": OpenFOAMSolverAdapter()})
    )
    record = facade.submit(
        LegacyExecutionRequest(
            analysis_object=analysis,
            run_id="run-legacy-001",
            working_directory=str(tmp_path / "legacy-run"),
            manifest_hash="sha256:legacy-run",
        )
    )

    assert record.run_id == "run-legacy-001"
    assert record.adapter_id == "openfoam.primary"
    assert record.result_ref is not None


def test_legacy_execution_facade_builds_runtime_thresholds_and_backend_override(tmp_path: Path):
    analysis = SimpleNamespace(
        Name="A2",
        Label="A2",
        PhysicsDomain="CFD",
        AnalysisType="General",
        SolverBackend="OpenFOAM",
        Group=[
            _make_child(
                "FlowStudio::Solver",
                SolverBackend="OpenFOAM",
                OpenFOAMSolver="simpleFoam",
                ElmerSolverBinary="ElmerSolver_mpi",
                NumProcessors=4,
                SoftRuntimeWarningSeconds=15,
                MaxRuntimeSeconds=45,
                StallTimeoutSeconds=20,
                MinProgressPercent=7.5,
                AbortOnThreshold=False,
            ),
        ],
    )

    facade = LegacyExecutionFacade(
        InMemoryJobService({"elmer.primary": ElmerSolverAdapter()})
    )
    adapter_id, run_request = facade.build_run_request(
        LegacyExecutionRequest(
            analysis_object=analysis,
            run_id="run-legacy-override",
            working_directory=str(tmp_path / "legacy-override"),
            manifest_hash="sha256:legacy-override",
            solver_backend_override="Elmer",
        )
    )

    assert adapter_id == "elmer.primary"
    assert run_request.study.solver_family == "elmer"
    assert run_request.runtime_thresholds.max_wall_time_seconds == 45
    assert run_request.runtime_thresholds.soft_wall_time_seconds == 15
    assert run_request.runtime_thresholds.stall_time_seconds == 20
    assert run_request.runtime_thresholds.min_progress_percent == 7.5
    assert run_request.runtime_thresholds.abort_on_threshold is False
