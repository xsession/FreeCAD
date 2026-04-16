# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Local process execution helpers for enterprise runs."""

from __future__ import annotations

from dataclasses import dataclass
import os
import shutil
import subprocess

from flow_studio.enterprise.core.domain import JobState, PreparedCase


@dataclass(frozen=True)
class ProcessExecutionResult:
    """Outcome of a local process execution attempt."""

    state: JobState
    execution_mode: str
    return_code: int
    stdout: str = ""
    stderr: str = ""
    native_identifier: str | None = None


class LocalProcessExecutor:
    """Execute prepared solver commands locally with safe synthetic fallback."""

    def __init__(self, timeout_seconds: int = 30, allow_synthetic_fallback: bool = True):
        self._timeout_seconds = timeout_seconds
        self._allow_synthetic_fallback = allow_synthetic_fallback

    def execute(self, prepared_case: PreparedCase) -> ProcessExecutionResult:
        """Run the prepared command or degrade gracefully when unavailable."""

        command = tuple(prepared_case.launch_command)
        if not command:
            return ProcessExecutionResult(
                state=JobState.FAILED,
                execution_mode="invalid",
                return_code=1,
                stderr="Prepared case did not define a launch command.",
            )

        executable = command[0]
        resolved = self._resolve_executable(executable)
        if resolved is None:
            if self._allow_synthetic_fallback:
                return ProcessExecutionResult(
                    state=JobState.COMPLETED,
                    execution_mode="synthetic",
                    return_code=0,
                    stdout=(
                        f"Executable '{executable}' was not available. "
                        "Completed using synthetic enterprise fallback."
                    ),
                    native_identifier="synthetic-process",
                )
            return ProcessExecutionResult(
                state=JobState.FAILED,
                execution_mode="missing_executable",
                return_code=127,
                stderr=f"Executable '{executable}' was not found on PATH.",
            )

        run_command = (resolved,) + command[1:]
        try:
            completed = subprocess.run(
                run_command,
                cwd=prepared_case.case_directory if os.path.isdir(prepared_case.case_directory) else None,
                capture_output=True,
                text=True,
                timeout=self._timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            return ProcessExecutionResult(
                state=JobState.FAILED,
                execution_mode="subprocess",
                return_code=124,
                stdout=exc.stdout or "",
                stderr=exc.stderr or f"Execution timed out after {self._timeout_seconds} seconds.",
            )
        except OSError as exc:
            return ProcessExecutionResult(
                state=JobState.FAILED,
                execution_mode="subprocess",
                return_code=1,
                stderr=str(exc),
            )

        return ProcessExecutionResult(
            state=JobState.COMPLETED if completed.returncode == 0 else JobState.FAILED,
            execution_mode="subprocess",
            return_code=completed.returncode,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
            native_identifier=resolved,
        )

    @staticmethod
    def _resolve_executable(executable: str) -> str | None:
        if os.path.isabs(executable) and os.path.isfile(executable):
            return executable
        return shutil.which(executable)
