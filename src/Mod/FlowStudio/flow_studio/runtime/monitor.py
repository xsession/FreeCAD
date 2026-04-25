# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Live runtime monitor helpers for the FlowStudio project cockpit."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import os
import re
import threading
import time

try:
    import FreeCAD
except Exception:  # pragma: no cover - keeps pure-Python imports working
    class _FreeCADStub:
        ActiveDocument = None

    FreeCAD = _FreeCADStub()


_SESSIONS = {}
_SESSIONS_LOCK = threading.Lock()
_PERCENT_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*%")
_FLOAT_PATTERN = re.compile(r"(-?\d+(?:\.\d+)?)")


@dataclass
class RunSession:
    analysis_name: str
    backend: str
    case_dir: str
    process: object = None
    runner: object = None
    status: str = "IDLE"
    phase: str = "Idle"
    progress_percent: float | None = None
    started_at: float = 0.0
    ended_at: float = 0.0
    last_error: str = ""
    result_path: str = ""
    result_format: str = ""
    stdout_tail: deque = field(default_factory=lambda: deque(maxlen=200))
    total_iterations: int = 0
    completed_iterations: int = 0
    sync_attempted: bool = False


def _session_key(analysis):
    if analysis is None:
        return None
    return getattr(analysis, "Name", None)


def _guess_total_iterations(solver_obj):
    if solver_obj is None:
        return 0
    backend = str(getattr(solver_obj, "SolverBackend", "") or "")
    if backend == "FluidX3D":
        return int(getattr(solver_obj, "FluidX3DTimeSteps", 0) or 0)
    max_iterations = int(getattr(solver_obj, "MaxIterations", 0) or 0)
    if max_iterations > 0:
        return max_iterations
    end_time = float(getattr(solver_obj, "EndTime", 0.0) or 0.0)
    dt = float(getattr(solver_obj, "TimeStep", 0.0) or 0.0)
    if end_time > 0.0 and dt > 0.0:
        return max(1, int(end_time / dt))
    return 0


def register_run(analysis, solver_obj, runner):
    """Register a launched legacy solver run for live monitoring."""
    key = _session_key(analysis)
    process = getattr(runner, "process", None)
    if key is None or process is None:
        return None

    session = RunSession(
        analysis_name=key,
        backend=str(getattr(solver_obj, "SolverBackend", "") or ""),
        case_dir=str(getattr(runner, "case_dir", "") or ""),
        process=process,
        runner=runner,
        status="RUNNING",
        phase="Launching solver",
        started_at=time.time(),
        total_iterations=_guess_total_iterations(solver_obj),
    )

    with _SESSIONS_LOCK:
        _SESSIONS[key] = session

    thread = threading.Thread(target=_pump_run_output, args=(session,), daemon=True)
    thread.start()
    return session


def _append_log(session, line):
    text = str(line).rstrip()
    if text:
        session.stdout_tail.append(text)
        _update_progress_from_line(session, text)


def _update_progress_from_line(session, line):
    lower = line.lower()
    percent_match = _PERCENT_PATTERN.search(line)
    if percent_match:
        try:
            session.progress_percent = max(0.0, min(100.0, float(percent_match.group(1))))
        except Exception:
            pass

    if "time =" in lower or "iteration" in lower or "iter" in lower or "step" in lower:
        session.completed_iterations += 1
        if session.total_iterations > 0 and session.progress_percent is None:
            session.progress_percent = min(
                99.0,
                (session.completed_iterations / float(session.total_iterations)) * 100.0,
            )

    if "error" in lower or "fatal" in lower:
        session.last_error = line

    if "time =" in lower:
        session.phase = "Solving transient fields"
    elif "iteration" in lower or "iter" in lower:
        session.phase = "Iterating solver"
    elif "writing" in lower or "write" in lower:
        session.phase = "Writing results"
    elif "decomposepar" in lower:
        session.phase = "Preparing parallel decomposition"
    elif "mesh" in lower:
        session.phase = "Preparing mesh and case"


def _pump_run_output(session):
    process = session.process
    stream = getattr(process, "stdout", None)
    if stream is not None:
        try:
            for line in iter(stream.readline, ""):
                if line == "":
                    break
                _append_log(session, line)
        except Exception as exc:
            session.last_error = str(exc)

    return_code = None
    try:
        return_code = process.wait()
    except Exception as exc:
        session.last_error = str(exc)

    session.ended_at = time.time()
    if return_code == 0:
        session.status = "FINISHED"
        session.phase = "Solver finished"
        if session.progress_percent is None:
            session.progress_percent = 100.0
    elif return_code is None:
        session.status = "UNKNOWN"
        session.phase = "Run ended unexpectedly"
    else:
        session.status = "FAILED"
        session.phase = "Solver failed"

    try:
        result_path = session.runner.read_results()
    except Exception as exc:
        session.last_error = str(exc)
        result_path = None

    if result_path:
        session.result_path = str(result_path)
        session.result_format = _infer_result_format(result_path, session.backend)


def get_run_snapshot(analysis=None):
    """Return a JSON-like snapshot for the currently tracked run."""
    key = _session_key(analysis) if analysis is not None else None
    if key is None and analysis is None and FreeCAD.ActiveDocument is not None:
        try:
            from flow_studio.core.workflow import get_active_analysis

            key = _session_key(get_active_analysis())
        except Exception:
            key = None

    with _SESSIONS_LOCK:
        session = _SESSIONS.get(key)

    if session is None:
        return {
            "status": "IDLE",
            "phase": "No active run",
            "progress_percent": None,
            "elapsed_seconds": 0,
            "backend": "",
            "case_dir": "",
            "pid": None,
            "result_path": "",
            "result_format": "",
            "last_error": "",
            "log_tail": [],
        }

    now = time.time()
    end_time = session.ended_at or now
    return {
        "status": session.status,
        "phase": session.phase,
        "progress_percent": session.progress_percent,
        "elapsed_seconds": max(0.0, end_time - session.started_at) if session.started_at else 0.0,
        "backend": session.backend,
        "case_dir": session.case_dir,
        "pid": getattr(session.process, "pid", None),
        "result_path": session.result_path,
        "result_format": session.result_format,
        "last_error": session.last_error,
        "log_tail": list(session.stdout_tail)[-30:],
    }


def terminate_run(analysis=None):
    """Terminate a tracked legacy solver process."""
    key = _session_key(analysis) if analysis is not None else None
    if key is None and analysis is None:
        try:
            from flow_studio.core.workflow import get_active_analysis

            key = _session_key(get_active_analysis())
        except Exception:
            key = None
    with _SESSIONS_LOCK:
        session = _SESSIONS.get(key)
    if session is None or session.process is None:
        return False
    if session.process.poll() is not None:
        return False
    try:
        session.process.terminate()
        session.status = "TERMINATING"
        session.phase = "Termination requested"
        return True
    except Exception as exc:
        session.last_error = str(exc)
        return False


def _infer_result_format(result_path, backend):
    path = str(result_path or "")
    if os.path.isdir(path):
        return "OpenFOAM"
    lowered = path.lower()
    if lowered.endswith(".vtk") or lowered.endswith(".vtu") or lowered.endswith(".vtp"):
        if backend == "FluidX3D":
            return "FluidX3D-VTK"
        return "VTK"
    if lowered.endswith(".json"):
        return "Geant4-JSON"
    if backend == "OpenFOAM":
        return "OpenFOAM"
    return "VTK"


def _default_fields_for_format(result_format, backend):
    if result_format in ("OpenFOAM", "VTK", "FluidX3D-VTK"):
        if backend == "FluidX3D":
            return ["rho", "u", "flags"]
        return ["U", "p", "T", "k", "omega"]
    if result_format.startswith("Geant4"):
        return ["dose", "energy", "events", "hits"]
    if backend == "Elmer":
        return ["Temperature", "Displacement", "Potential"]
    return ["Result"]


def sync_post_pipeline(analysis, snapshot=None):
    """Create/update a PostPipeline object from a finished runtime snapshot."""
    if analysis is None:
        return None
    snapshot = snapshot or get_run_snapshot(analysis)
    result_path = str(snapshot.get("result_path", "") or "")
    if not result_path:
        return None

    from flow_studio.ObjectsFlowStudio import makePostPipeline

    pipeline = None
    for obj in getattr(analysis, "Group", []) or []:
        if getattr(obj, "FlowType", "") == "FlowStudio::PostPipeline":
            pipeline = obj
            break
    if pipeline is None:
        pipeline = makePostPipeline(getattr(analysis, "Document", None) or FreeCAD.ActiveDocument)
        analysis.addObject(pipeline)

    pipeline.Analysis = analysis
    pipeline.ResultFile = result_path
    result_format = str(snapshot.get("result_format", "") or _infer_result_format(result_path, snapshot.get("backend", "")))
    if result_format:
        pipeline.ResultFormat = result_format
    available_fields = _default_fields_for_format(result_format, snapshot.get("backend", ""))
    pipeline.AvailableFields = list(available_fields)
    if available_fields:
        pipeline.ActiveField = available_fields[0]
    return pipeline
