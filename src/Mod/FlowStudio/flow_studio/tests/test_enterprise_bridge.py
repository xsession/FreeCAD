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
                References=[(part, "Solid1")],
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
    assert study.materials[0].target_ref == "Document/Body/Solid1"
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


def test_legacy_analysis_bridge_includes_elmer_solver_binary_extension():
    analysis = SimpleNamespace(
        Name="A3",
        Label="A3",
        PhysicsDomain="Thermal",
        AnalysisType="Transient Heat Transfer",
        SolverBackend="Elmer",
        Group=[
            _make_child(
                "FlowStudio::Solver",
                SolverBackend="Elmer",
                ElmerSolverBinary="ElmerSolver",
                NumProcessors=3,
                TimeStep=0.01,
                EndTime=2.0,
                MultiSolverEnabled=True,
                MultiSolverBackends=["Elmer", "OpenFOAM"],
                SoftRuntimeWarningSeconds=20,
                MaxRuntimeSeconds=60,
                StallTimeoutSeconds=30,
                MinProgressPercent=5.0,
                AbortOnThreshold=True,
            ),
        ],
    )

    study = LegacyAnalysisBridge(analysis).to_study_definition()

    assert study.solver_family == "elmer"
    assert study.adapter_extensions["elmer.primary"]["solver_binary"] == "ElmerSolver"
    assert study.parameters["multi_solver_enabled"] is True
    assert study.parameters["multi_solver_backends"] == "Elmer,OpenFOAM"
    assert study.parameters["max_runtime_seconds"] == 60


def test_legacy_analysis_bridge_honors_solver_backend_override():
    analysis = SimpleNamespace(
        Name="A5",
        Label="A5",
        PhysicsDomain="CFD",
        AnalysisType="General",
        SolverBackend="OpenFOAM",
        Group=[
            _make_child(
                "FlowStudio::Solver",
                SolverBackend="OpenFOAM",
                OpenFOAMSolver="simpleFoam",
                ElmerSolverBinary="ElmerSolver_mpi",
                NumProcessors=8,
            ),
        ],
    )

    study = LegacyAnalysisBridge(analysis, solver_backend_override="Elmer").to_study_definition()

    assert study.solver_family == "elmer"
    assert study.parameters["selected_solver_backend"] == "Elmer"
    assert study.adapter_extensions["elmer.primary"]["solver_binary"] == "ElmerSolver_mpi"


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


def test_legacy_analysis_bridge_maps_geant4_extensions():
    source_part = SimpleNamespace(Name="BeamBody")
    analysis = SimpleNamespace(
        Name="A4",
        Label="A4",
        PhysicsDomain="Optical",
        AnalysisType="Non-Sequential Ray Trace",
        SolverBackend="Geant4",
        Group=[
            _make_child(
                "FlowStudio::Solver",
                SolverBackend="Geant4",
                Geant4Executable="/opt/geant4/bin/exampleB1",
                Geant4PhysicsList="QGSP_BERT",
                Geant4EventCount=2500,
                Geant4Threads=6,
                Geant4MacroName="beam.mac",
                Geant4EnableVisualization=True,
            ),
            _make_child(
                "FlowStudio::BCGeant4Source",
                Name="BeamSource",
                Label="Beam Source",
                SourceType="Beam",
                ParticleType="proton",
                EnergyMeV=5.0,
                BeamRadius=2.0,
                DirectionX=0.0,
                DirectionY=0.0,
                DirectionZ=1.0,
                Events=2500,
                References=[(source_part, "Face1")],
            ),
        ],
    )

    study = LegacyAnalysisBridge(analysis).to_study_definition()

    assert study.solver_family == "geant4"
    assert study.adapter_extensions["geant4.primary"]["physics_list"] == "QGSP_BERT"
    assert study.adapter_extensions["geant4.primary"]["event_count"] == 2500
    assert study.adapter_extensions["geant4.primary"]["sources"][0]["particle_type"] == "proton"
