# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""File-backed persistence for enterprise run artifacts."""

from __future__ import annotations

import json
import os
import zipfile
from typing import Any

from flow_studio.enterprise.core.serialization import to_json


class FileRunStore:
    """Persist enterprise run metadata and artifacts to the filesystem."""

    def __init__(self, root_directory: str):
        self._root_directory = os.path.abspath(root_directory)
        os.makedirs(self._root_directory, exist_ok=True)

    @property
    def root_directory(self) -> str:
        """Return the run-store root directory."""

        return self._root_directory

    def run_directory(self, run_id: str) -> str:
        """Return the directory reserved for a run."""

        return os.path.join(self._root_directory, run_id)

    def record_path(self, run_id: str) -> str:
        """Return the canonical run-record path."""

        return os.path.join(self.run_directory(run_id), "run_record.json")

    def persist_run(
        self,
        *,
        run_id: str,
        request,
        prepared_case,
        run_record,
        result,
        events,
        execution_log: str | None = None,
    ) -> str:
        """Write the key submission artifacts for a run and return its directory."""

        run_directory = self.run_directory(run_id)
        os.makedirs(run_directory, exist_ok=True)
        self._write_json(os.path.join(run_directory, "request.json"), request)
        self._write_json(os.path.join(run_directory, "prepared_case.json"), prepared_case)
        self._write_json(self.record_path(run_id), run_record)
        self._write_json(os.path.join(run_directory, "result.json"), result)
        self._write_json(os.path.join(run_directory, "events.json"), tuple(events))
        if execution_log:
            self._write_text(os.path.join(run_directory, "execution.log"), execution_log)
        return run_directory

    def load_request(self, run_id: str) -> dict[str, Any]:
        """Load the persisted request payload for a run."""

        return self._read_json(os.path.join(self.run_directory(run_id), "request.json"))

    def load_prepared_case(self, run_id: str) -> dict[str, Any]:
        """Load the persisted prepared-case payload for a run."""

        return self._read_json(os.path.join(self.run_directory(run_id), "prepared_case.json"))

    def load_run_record(self, run_id: str) -> dict[str, Any]:
        """Load the persisted run-record payload for a run."""

        return self._read_json(self.record_path(run_id))

    def load_result(self, run_id: str) -> dict[str, Any]:
        """Load the persisted result payload for a run."""

        return self._read_json(os.path.join(self.run_directory(run_id), "result.json"))

    def load_execution_log(self, run_id: str) -> str:
        """Load the persisted execution log for a run."""

        path = os.path.join(self.run_directory(run_id), "execution.log")
        if not os.path.isfile(path):
            return ""
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()

    def load_events(self, run_id: str) -> list[dict[str, Any]]:
        """Load persisted stream events for a run."""

        data = self._read_json(os.path.join(self.run_directory(run_id), "events.json"))
        return list(data)

    def list_run_ids(self) -> tuple[str, ...]:
        """Return persisted run identifiers in sorted order."""

        if not os.path.isdir(self._root_directory):
            return ()
        run_ids: list[str] = []
        for entry in os.listdir(self._root_directory):
            if os.path.isdir(os.path.join(self._root_directory, entry)):
                run_ids.append(entry)
        return tuple(sorted(run_ids))

    def list_run_summaries(self) -> tuple[dict[str, Any], ...]:
        """Return lightweight summaries for every persisted run."""

        summaries: list[dict[str, Any]] = []
        for run_id in reversed(self.list_run_ids()):
            record = self.load_run_record(run_id)
            summaries.append(
                {
                    "run_id": run_id,
                    "study_id": record.get("study_id"),
                    "state": record.get("state"),
                    "adapter_id": record.get("adapter_id"),
                    "result_ref": record.get("result_ref"),
                    "manifest_hash": record.get("manifest_hash"),
                    "run_directory": self.run_directory(run_id),
                    "record_path": self.record_path(run_id),
                    "execution_mode": record.get("execution_mode"),
                    "return_code": record.get("return_code"),
                    "target": record.get("target"),
                    "target_ref": record.get("target_ref"),
                    "remote_run_id": record.get("remote_run_id"),
                }
            )
        return tuple(summaries)

    def create_support_bundle(self, run_id: str, output_path: str) -> str:
        """Create a zipped support bundle for a persisted run."""

        run_directory = self.run_directory(run_id)
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for root, _, filenames in os.walk(run_directory):
                for filename in filenames:
                    absolute_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(absolute_path, run_directory)
                    archive.write(absolute_path, arcname=os.path.join(run_id, relative_path))
        return output_path

    @staticmethod
    def _write_json(path: str, value) -> None:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(to_json(value))
            handle.write("\n")

    @staticmethod
    def _write_text(path: str, value: str) -> None:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(value)

    @staticmethod
    def _read_json(path: str) -> Any:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
