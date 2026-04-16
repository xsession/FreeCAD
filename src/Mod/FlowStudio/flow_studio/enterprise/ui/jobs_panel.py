# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Jobs and run-history panel for Flow Studio Enterprise."""

from __future__ import annotations

import json

import FreeCAD
import FreeCADGui
from PySide import QtCore, QtGui


class EnterpriseJobsPanel:
    """Task panel that displays persisted enterprise runs."""

    _COLUMNS = ("Run ID", "State", "Target", "Adapter", "Study", "Directory")

    def __init__(self, runtime):
        self.runtime = runtime
        self.form = self._build_form()
        self.refresh()

    def _build_form(self):
        widget = QtGui.QWidget()
        widget.setWindowTitle("Flow Studio Enterprise Jobs")
        layout = QtGui.QVBoxLayout(widget)

        header = QtGui.QLabel(
            "<h3>Enterprise Jobs</h3>"
            "<p>Review persisted enterprise runs, states, and artifact locations.</p>"
        )
        header.setWordWrap(True)
        layout.addWidget(header)

        self.table = QtGui.QTableWidget(0, len(self._COLUMNS))
        self.table.setHorizontalHeaderLabels(self._COLUMNS)
        self.table.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemSelectionChanged.connect(self._update_details)
        layout.addWidget(self.table)

        button_row = QtGui.QHBoxLayout()
        self.refresh_button = QtGui.QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh)
        button_row.addWidget(self.refresh_button)

        self.copy_path_button = QtGui.QPushButton("Copy Run Path")
        self.copy_path_button.clicked.connect(self._copy_selected_path)
        button_row.addWidget(self.copy_path_button)

        self.bundle_button = QtGui.QPushButton("Export Bundle")
        self.bundle_button.clicked.connect(self._export_selected_bundle)
        button_row.addWidget(self.bundle_button)

        self.print_button = QtGui.QPushButton("Print Summary")
        self.print_button.clicked.connect(self._print_selected_summary)
        button_row.addWidget(self.print_button)
        button_row.addStretch()
        layout.addLayout(button_row)

        self.details = QtGui.QPlainTextEdit()
        self.details.setReadOnly(True)
        self.details.setPlaceholderText("Select a run to inspect its persisted details.")
        layout.addWidget(self.details)

        return widget

    def refresh(self):
        """Reload summaries from the persisted run store."""

        summaries = self.runtime.job_service.persisted_run_summaries()
        self.table.setRowCount(len(summaries))
        for row, summary in enumerate(summaries):
            values = (
                summary.get("run_id", ""),
                summary.get("state", ""),
                summary.get("target_ref", "") or summary.get("target", ""),
                summary.get("adapter_id", ""),
                summary.get("study_id", ""),
                summary.get("run_directory", ""),
            )
            for column, value in enumerate(values):
                item = QtGui.QTableWidgetItem(str(value))
                if column == 0:
                    item.setData(QtCore.Qt.UserRole, summary.get("run_id", ""))
                self.table.setItem(row, column, item)
        if summaries:
            self.table.selectRow(0)
        else:
            self.details.setPlainText("No persisted enterprise runs were found yet.")

    def _selected_run_id(self):
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        item = self.table.item(indexes[0].row(), 0)
        if item is None:
            return None
        return item.data(QtCore.Qt.UserRole)

    def _update_details(self):
        run_id = self._selected_run_id()
        if not run_id:
            self.details.setPlainText("No run selected.")
            return

        record = self.runtime.job_service.persisted_run_record(run_id) or {}
        result = self.runtime.job_service.persisted_run_result(run_id) or {}
        events = self.runtime.job_service.persisted_run_events(run_id)
        payload = {
            "run_record": record,
            "result": result,
            "event_count": len(events),
            "events_preview": events[:5],
            "execution_log": self.runtime.job_service.persisted_execution_log(run_id),
        }
        self.details.setPlainText(json.dumps(payload, indent=2, sort_keys=True))

    def _copy_selected_path(self):
        run_id = self._selected_run_id()
        if not run_id:
            return
        path = self.runtime.job_service.run_directory(run_id)
        if not path:
            return
        QtGui.QApplication.clipboard().setText(path)
        FreeCAD.Console.PrintMessage(f"FlowStudio: Copied enterprise run path: {path}\n")

    def _print_selected_summary(self):
        run_id = self._selected_run_id()
        if not run_id:
            return
        record = self.runtime.job_service.persisted_run_record(run_id) or {}
        result = self.runtime.job_service.persisted_run_result(run_id) or {}
        FreeCAD.Console.PrintMessage(
            "FlowStudio: Enterprise run summary\n"
            f"  Run ID: {run_id}\n"
            f"  State: {record.get('state', '')}\n"
            f"  Target: {record.get('target_ref', '') or record.get('target', '')}\n"
            f"  Adapter: {record.get('adapter_id', '')}\n"
            f"  Result: {result.get('result_ref', '')}\n"
            f"  Directory: {self.runtime.job_service.run_directory(run_id) or ''}\n"
        )

    def _export_selected_bundle(self):
        run_id = self._selected_run_id()
        if not run_id:
            return

        run_directory = self.runtime.job_service.run_directory(run_id) or ""
        default_path = f"{run_directory}.support.zip" if run_directory else f"{run_id}.support.zip"

        selected_path = default_path
        if FreeCAD.GuiUp:
            selected_path = QtGui.QFileDialog.getSaveFileName(
                None,
                "Export Support Bundle",
                default_path,
                "Zip Archives (*.zip)",
            )[0]
        if not selected_path:
            return

        bundle_path = self.runtime.job_service.create_support_bundle(run_id, selected_path)
        if bundle_path:
            FreeCAD.Console.PrintMessage(
                f"FlowStudio: Support bundle exported to {bundle_path}\n"
            )

    def accept(self):
        FreeCADGui.Control.closeDialog()
        return True

    def reject(self):
        FreeCADGui.Control.closeDialog()
        return True
