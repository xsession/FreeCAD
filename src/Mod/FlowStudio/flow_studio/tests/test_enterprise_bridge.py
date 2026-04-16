# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Tests for legacy Flow Studio to enterprise model bridging."""

from types import SimpleNamespace

from flow_studio.enterprise.core.serialization import to_json
from flow_studio.enterprise.integration.freecad_bridge import (
    LegacyAnalysisBridge,
    build_project_manifest,
)


def _make_child(flow_type: str, **kwargs):
    return SimpleNamespace(FlowType=flow_type, **kwargs)


def test_legacy_analysis_bridge_builds_openfoam_study():
    part = SimpleNamespace(Name="Body")
    analysis = SimpleNamespace(
        Name="CFDAnalysis",
        Label="Cooling Study",
        PhysicsDomain="CFD",
        AnalysisType="General",
        SolverBackend="OpenFOAM",
        NeedsMeshRewrite=True,
        NeedsCaseRewrite=False,
        Group=[
            _make_child(
                "FlowStudio::MeshGmsh",
                Part=part,
                CharacteristicLength=2.5,
            ),
            _make_child(
                "FlowStudio::PhysicsModel",
                FlowRegime="Turbulent",
                TurbulenceModel="kOmegaSST",
                Compressibility="Incompressible",
                TimeModel="Steady",
                HeatTransfer=True,
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
                MaxIterations=2000,
                ConvergenceTolerance=1e-4,
                WriteInterval=100,
                NumProcessors=4,
            ),
        ],
    )

    study = LegacyAnalysisBridge(analysis).to_study_definition()

    assert study.study_id == "CFDAnalysis"
    assert study.solver_family == "openfoam"
    assert study.geometry_ref == "Document/Body"
    assert study.mesh_recipe.generator_id == "gmsh.default"
    assert study.physics[0].family == "cht"
    assert study.adapter_extensions["openfoam.primary"]["solver_binary"] == "simpleFoam"


def test_project_manifest_serializes_to_json():
    analysis = SimpleNamespace(
        Name="A1",
        Label="A1",
        PhysicsDomain="CFD",
        AnalysisType="General",
        SolverBackend="Elmer",
        Group=[],
    )

    manifest = build_project_manifest("project-001", [analysis])
    serialized = to_json(manifest)

    assert '"project_id": "project-001"' in serialized
    assert '"solver_family": "elmer"' in serialized


def test_legacy_analysis_bridge_prefers_solver_object_backend():
    analysis = SimpleNamespace(
        Name="A2",
        Label="A2",
        PhysicsDomain="CFD",
        AnalysisType="General",
        SolverBackend="OpenFOAM",
        Group=[
            _make_child(
                "FlowStudio::Solver",
                SolverBackend="FluidX3D",
                FluidX3DPrecision="FP32/FP16S",
                FluidX3DResolution=512,
                FluidX3DMultiGPU=True,
            ),
        ],
    )

    study = LegacyAnalysisBridge(analysis).to_study_definition()

    assert study.solver_family == "fluidx3d"
    assert study.adapter_extensions["fluidx3d.optional"]["resolution"] == 512
