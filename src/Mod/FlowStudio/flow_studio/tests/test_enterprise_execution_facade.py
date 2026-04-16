# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Tests for legacy-analysis submission through enterprise services."""

from pathlib import Path
from types import SimpleNamespace

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
