# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Tests for application-facing enterprise actions."""

from pathlib import Path
from types import SimpleNamespace

from flow_studio.enterprise.app.legacy_actions import (
    build_manifest_for_analysis,
    export_analysis_manifest,
    prepare_runtime_submission,
    submit_analysis_to_runtime,
)
from flow_studio.enterprise.bootstrap import initialize_workbench


def _analysis_fixture():
    return SimpleNamespace(
        Name="CoolingStudy",
        Label="Cooling Study",
        PhysicsDomain="CFD",
        AnalysisType="General",
        SolverBackend="OpenFOAM",
        NeedsMeshRewrite=False,
        NeedsCaseRewrite=False,
        Group=[
            SimpleNamespace(
                FlowType="FlowStudio::MeshGmsh",
                CharacteristicLength=3.0,
                Part=SimpleNamespace(Name="Body"),
            ),
            SimpleNamespace(
                FlowType="FlowStudio::PhysicsModel",
                FlowRegime="Turbulent",
                TurbulenceModel="kOmegaSST",
                Compressibility="Incompressible",
                TimeModel="Steady",
                HeatTransfer=False,
                Gravity=False,
                Buoyancy=False,
            ),
            SimpleNamespace(
                FlowType="FlowStudio::FluidMaterial",
                MaterialName="Air",
                Density=1.225,
                DynamicViscosity=1.81e-5,
                SpecificHeat=1005.0,
                ThermalConductivity=0.0257,
            ),
            SimpleNamespace(
                FlowType="FlowStudio::Solver",
                OpenFOAMSolver="simpleFoam",
                MaxIterations=200,
                ConvergenceTolerance=1e-4,
                WriteInterval=20,
                NumProcessors=2,
            ),
        ],
    )


def test_export_analysis_manifest_writes_json(tmp_path: Path):
    analysis = _analysis_fixture()
    output_path = tmp_path / "study.enterprise.json"

    path = export_analysis_manifest(analysis, project_id="project-123", output_path=str(output_path))

    assert path == str(output_path)
    contents = output_path.read_text(encoding="utf-8")
    assert '"project_id": "project-123"' in contents
    assert '"study_id": "CoolingStudy"' in contents


def test_submit_analysis_to_runtime_returns_deterministic_manifest_hash(tmp_path: Path):
    analysis = _analysis_fixture()
    runtime = initialize_workbench()

    record_a, manifest_hash_a = submit_analysis_to_runtime(
        runtime=runtime,
        analysis_object=analysis,
        project_id="project-123",
        run_id="run-a",
        working_directory=str(tmp_path / "submit-a"),
    )
    record_b, manifest_hash_b = submit_analysis_to_runtime(
        runtime=runtime,
        analysis_object=analysis,
        project_id="project-123",
        run_id="run-b",
        working_directory=str(tmp_path / "submit-b"),
    )

    assert record_a.adapter_id == "openfoam.primary"
    assert manifest_hash_a == manifest_hash_b
    assert manifest_hash_a.startswith("sha256:")
    assert runtime.job_service.run_directory(record_a.run_id) is not None
    assert record_a.execution_mode == "synthetic"

    events = runtime.job_service.persisted_run_events(record_a.run_id)
    assert any(event.get("event_type") == "state_changed" for event in events)
    assert any(event.get("state") == "Completed" for event in events)


def test_build_manifest_for_analysis_contains_single_study():
    manifest = build_manifest_for_analysis(_analysis_fixture(), project_id="project-xyz")
    assert manifest.project_id == "project-xyz"
    assert len(manifest.studies) == 1


def test_prepare_runtime_submission_uses_solver_object_backend(tmp_path: Path):
    analysis = _analysis_fixture()
    analysis.SolverBackend = "OpenFOAM"
    analysis.Group[-1].SolverBackend = "Elmer"
    runtime = initialize_workbench()

    adapter_id, run_request, _, manifest_hash = prepare_runtime_submission(
        runtime=runtime,
        analysis_object=analysis,
        project_id="project-elmer",
        run_id="run-elmer-selection",
        working_directory=str(tmp_path / "elmer-selection"),
    )

    assert adapter_id == "elmer.primary"
    assert run_request.study.solver_family == "elmer"
    assert manifest_hash.startswith("sha256:")


def test_submit_analysis_to_runtime_supports_remote_execution_profile(tmp_path: Path):
    analysis = _analysis_fixture()
    runtime = initialize_workbench()

    record, manifest_hash = submit_analysis_to_runtime(
        runtime=runtime,
        analysis_object=analysis,
        project_id="project-remote",
        run_id="run-remote-actions",
        working_directory=str(tmp_path / "remote-actions"),
        execution_profile=runtime.profiles["remote-loopback"],
    )

    assert record.target == "remote"
    assert record.target_ref == "loopback.default"
    assert record.remote_run_id == "run-remote-actions"
    assert manifest_hash.startswith("sha256:")
