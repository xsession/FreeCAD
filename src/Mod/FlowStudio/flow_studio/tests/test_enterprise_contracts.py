# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Contract tests for the enterprise architecture scaffolding."""

from pathlib import Path
import sys

from flow_studio.enterprise.adapters.elmer import ElmerSolverAdapter
from flow_studio.enterprise.adapters.openfoam import OpenFOAMSolverAdapter
from flow_studio.enterprise.core.domain import JobState, PreparedCase
from flow_studio.enterprise.services import FileRunStore
from flow_studio.enterprise.services.jobs import InMemoryJobService
from flow_studio.enterprise.services.process_executor import LocalProcessExecutor
from flow_studio.enterprise.testing.harness import AdapterContractHarness, make_demo_request


def test_openfoam_adapter_contract_smoke():
    result_ref, fields = AdapterContractHarness(OpenFOAMSolverAdapter()).smoke_test("run-of")
    assert result_ref.startswith("results://openfoam/")
    assert "U" in fields


def test_elmer_adapter_contract_smoke():
    result_ref, fields = AdapterContractHarness(ElmerSolverAdapter()).smoke_test("run-elmer")
    assert result_ref.startswith("results://elmer/")
    assert "Temperature" in fields


def test_openfoam_adapter_uses_extension_selected_solver_binary(tmp_path: Path):
    adapter = OpenFOAMSolverAdapter()
    request = make_demo_request("run-of-binary", solver_family=adapter.metadata().family)
    study = request.study
    request = request.__class__(
        run_id=request.run_id,
        study=study.__class__(
            study_id=study.study_id,
            name=study.name,
            solver_family=study.solver_family,
            geometry_ref=study.geometry_ref,
            mesh_recipe=study.mesh_recipe,
            materials=study.materials,
            physics=study.physics,
            parameters=study.parameters,
            adapter_extensions={"openfoam.primary": {"solver_binary": "pimpleFoam"}},
        ),
        execution_profile=request.execution_profile,
        requested_by=request.requested_by,
        reason=request.reason,
    )
    from flow_studio.enterprise.core.domain import PreparedStudyContext

    prepared = adapter.prepare_case(
        PreparedStudyContext(
            request=request,
            working_directory=str(tmp_path / "of-binary"),
            manifest_hash="sha256:of-binary",
        )
    )

    assert prepared.launch_command[0] == "pimpleFoam"


def test_elmer_adapter_uses_extension_selected_solver_binary(tmp_path: Path):
    adapter = ElmerSolverAdapter()
    request = make_demo_request("run-elmer-binary", solver_family=adapter.metadata().family)
    study = request.study
    request = request.__class__(
        run_id=request.run_id,
        study=study.__class__(
            study_id=study.study_id,
            name=study.name,
            solver_family=study.solver_family,
            geometry_ref=study.geometry_ref,
            mesh_recipe=study.mesh_recipe,
            materials=study.materials,
            physics=study.physics,
            parameters=study.parameters,
            adapter_extensions={"elmer.primary": {"solver_binary": "ElmerSolver_mpi"}},
        ),
        execution_profile=request.execution_profile,
        requested_by=request.requested_by,
        reason=request.reason,
    )
    from flow_studio.enterprise.core.domain import PreparedStudyContext

    prepared = adapter.prepare_case(
        PreparedStudyContext(
            request=request,
            working_directory=str(tmp_path / "elmer-binary"),
            manifest_hash="sha256:elmer-binary",
        )
    )

    assert prepared.launch_command[0] == "ElmerSolver_mpi"


def test_in_memory_job_service_submits_openfoam_run(tmp_path: Path):
    adapter = OpenFOAMSolverAdapter()
    request = make_demo_request("run-job-service", solver_family=adapter.metadata().family)
    service = InMemoryJobService({adapter.adapter_id: adapter})

    record = service.submit(
        request=request,
        adapter_id=adapter.adapter_id,
        working_directory=str(tmp_path / "job-service"),
        manifest_hash="sha256:test-job",
    )

    assert record.run_id == "run-job-service"
    assert service.result("run-job-service").result_ref.startswith("results://openfoam/")


def test_job_service_persists_run_artifacts(tmp_path: Path):
    adapter = OpenFOAMSolverAdapter()
    request = make_demo_request("run-persisted", solver_family=adapter.metadata().family)
    service = InMemoryJobService(
        {adapter.adapter_id: adapter},
        run_store=FileRunStore(str(tmp_path / "run-store")),
    )

    record = service.submit(
        request=request,
        adapter_id=adapter.adapter_id,
        working_directory=str(tmp_path / "working"),
        manifest_hash="sha256:persisted",
    )

    run_directory = Path(service.run_directory(record.run_id))
    assert run_directory.is_dir()
    assert (run_directory / "request.json").is_file()
    assert (run_directory / "prepared_case.json").is_file()
    assert (run_directory / "run_record.json").is_file()
    assert (run_directory / "result.json").is_file()
    assert (run_directory / "events.json").is_file()
    assert record.run_id in service.list_persisted_run_ids()


def test_job_service_exposes_persisted_run_summaries(tmp_path: Path):
    adapter = OpenFOAMSolverAdapter()
    request = make_demo_request("run-summary", solver_family=adapter.metadata().family)
    service = InMemoryJobService(
        {adapter.adapter_id: adapter},
        run_store=FileRunStore(str(tmp_path / "run-store")),
    )

    record = service.submit(
        request=request,
        adapter_id=adapter.adapter_id,
        working_directory=str(tmp_path / "working"),
        manifest_hash="sha256:summary",
    )

    summaries = service.persisted_run_summaries()
    assert len(summaries) == 1
    assert summaries[0]["run_id"] == record.run_id
    assert summaries[0]["state"] == record.state.value
    assert summaries[0]["adapter_id"] == record.adapter_id

    persisted_record = service.persisted_run_record(record.run_id)
    persisted_result = service.persisted_run_result(record.run_id)
    persisted_events = service.persisted_run_events(record.run_id)
    persisted_log = service.persisted_execution_log(record.run_id)
    assert persisted_record["run_id"] == record.run_id
    assert persisted_result["result_ref"].startswith("results://openfoam/")
    assert len(persisted_events) >= 1
    assert "execution_mode=" in persisted_log


def test_job_service_creates_support_bundle(tmp_path: Path):
    adapter = OpenFOAMSolverAdapter()
    request = make_demo_request("run-bundle", solver_family=adapter.metadata().family)
    service = InMemoryJobService(
        {adapter.adapter_id: adapter},
        run_store=FileRunStore(str(tmp_path / "run-store")),
    )

    record = service.submit(
        request=request,
        adapter_id=adapter.adapter_id,
        working_directory=str(tmp_path / "working"),
        manifest_hash="sha256:bundle",
    )

    bundle_path = tmp_path / "support" / "run-bundle.zip"
    created = service.create_support_bundle(record.run_id, str(bundle_path))

    assert created == str(bundle_path)
    assert bundle_path.is_file()


def test_local_process_executor_runs_real_subprocess(tmp_path: Path):
    executor = LocalProcessExecutor(timeout_seconds=10, allow_synthetic_fallback=False)
    prepared_case = PreparedCase(
        adapter_id="test.adapter",
        run_id="run-real-process",
        case_directory=str(tmp_path),
        launch_command=(sys.executable, "-c", "print('flowstudio-process-ok')"),
        artifact_manifest={},
    )

    result = executor.execute(prepared_case)

    assert result.state == JobState.COMPLETED
    assert result.execution_mode == "subprocess"
    assert result.return_code == 0
    assert "flowstudio-process-ok" in result.stdout


def test_local_process_executor_uses_synthetic_fallback(tmp_path: Path):
    executor = LocalProcessExecutor(timeout_seconds=10, allow_synthetic_fallback=True)
    prepared_case = PreparedCase(
        adapter_id="test.adapter",
        run_id="run-synthetic-process",
        case_directory=str(tmp_path),
        launch_command=("definitely-not-a-real-solver-exe", "--flag"),
        artifact_manifest={},
    )

    result = executor.execute(prepared_case)

    assert result.state == JobState.COMPLETED
    assert result.execution_mode == "synthetic"
    assert result.return_code == 0


def test_local_process_executor_uses_case_runtime_threshold_override(tmp_path: Path):
    executor = LocalProcessExecutor(timeout_seconds=30, allow_synthetic_fallback=False)
    prepared_case = PreparedCase(
        adapter_id="test.adapter",
        run_id="run-timeout-override",
        case_directory=str(tmp_path),
        launch_command=(sys.executable, "-c", "import time; time.sleep(2)"),
        artifact_manifest={},
        max_runtime_seconds=1,
    )

    result = executor.execute(prepared_case)

    assert result.state == JobState.FAILED
    assert result.return_code == 124
    assert "1 seconds" in result.stderr
