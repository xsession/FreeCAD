# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Tests for application-facing enterprise actions."""

from pathlib import Path
from types import SimpleNamespace

from flow_studio.enterprise.app.legacy_actions import (
    build_manifest_for_analysis,
    export_fcstd_sidecar,
    export_analysis_manifest,
    prepare_runtime_submission,
    prepare_runtime_submissions,
    submit_analysis_to_runtime,
    submit_analysis_to_runtime_batch,
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
                SolverBackend="OpenFOAM",
                OpenFOAMSolver="simpleFoam",
                MaxIterations=200,
                ConvergenceTolerance=1e-4,
                WriteInterval=20,
                NumProcessors=2,
                MultiSolverEnabled=False,
                MultiSolverBackends=["OpenFOAM", "Elmer"],
                SoftRuntimeWarningSeconds=0,
                MaxRuntimeSeconds=0,
                StallTimeoutSeconds=0,
                MinProgressPercent=0.0,
                AbortOnThreshold=True,
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


def test_prepare_runtime_submissions_expands_multi_solver_plan(tmp_path: Path):
    analysis = _analysis_fixture()
    solver = analysis.Group[-1]
    solver.MultiSolverEnabled = True
    solver.MultiSolverBackends = ["OpenFOAM", "Elmer"]
    solver.MaxRuntimeSeconds = 120
    runtime = initialize_workbench()

    submissions = prepare_runtime_submissions(
        runtime=runtime,
        analysis_object=analysis,
        project_id="project-multi",
        run_id="run-multi-plan",
        working_directory=str(tmp_path / "multi-plan"),
    )

    assert [item[0] for item in submissions] == ["OpenFOAM", "Elmer"]
    assert submissions[0][2].runtime_thresholds.max_wall_time_seconds == 120
    assert submissions[0][2].run_id == "run-multi-plan-openfoam"
    assert submissions[1][2].run_id == "run-multi-plan-elmer"


def test_submit_analysis_to_runtime_batch_runs_multi_solver_configuration(tmp_path: Path):
    analysis = _analysis_fixture()
    solver = analysis.Group[-1]
    solver.MultiSolverEnabled = True
    solver.MultiSolverBackends = ["OpenFOAM", "Elmer"]
    solver.MaxRuntimeSeconds = 90
    runtime = initialize_workbench()

    submissions = submit_analysis_to_runtime_batch(
        runtime=runtime,
        analysis_object=analysis,
        project_id="project-multi-submit",
        run_id="run-multi-submit",
        working_directory=str(tmp_path / "multi-submit"),
    )

    assert len(submissions) == 2
    assert {record.adapter_id for _, record, _ in submissions} == {"openfoam.primary", "elmer.primary"}
    assert all(manifest_hash.startswith("sha256:") for _, _, manifest_hash in submissions)


def test_export_fcstd_sidecar_writes_canonical_payload(tmp_path: Path):
    analysis = _analysis_fixture()
    fcstd_path = tmp_path / "Demo.FCStd"
    fcstd_path.write_text("dummy", encoding="utf-8")

    sidecar_path = export_fcstd_sidecar(
        analysis_object=analysis,
        project_id="project-sidecar",
        fcstd_path=str(fcstd_path),
    )

    sidecar = Path(sidecar_path)
    assert sidecar.is_file()
    contents = sidecar.read_text(encoding="utf-8")
    assert '"artifact_type": "flowstudio.fcstd.sidecar"' in contents
    assert '"project_id": "project-sidecar"' in contents
    assert '"manifest_hash": "sha256:' in contents
