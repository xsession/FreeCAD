# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Jobs and run-history panel for Flow Studio Enterprise."""

from __future__ import annotations

import csv
import json

import FreeCAD
import FreeCADGui
from PySide import QtCore, QtGui

from flow_studio.enterprise.ui.adapter_matrix import (
    ADAPTER_MATRIX_CSV_FIELDNAMES,
    collect_families,
    filter_rows,
    matrix_to_json,
    to_csv_row,
)


class EnterpriseJobsPanel:
    """Task panel that displays persisted enterprise runs."""

    _COLUMNS = ("Run ID", "State", "Target", "Adapter", "Study", "Directory")
    _ADAPTER_COLUMNS = (
        "Adapter",
        "Family",
        "Version",
        "Commercial",
        "GPU",
        "Remote",
        "Parallel",
        "Transient",
    )

    def __init__(self, runtime):
        self.runtime = runtime
        self._adapter_rows = []
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

        adapter_label = QtGui.QLabel("<b>Adapter Capability Matrix</b>")
        layout.addWidget(adapter_label)

        adapter_filter_row = QtGui.QHBoxLayout()
        self.adapter_search = QtGui.QLineEdit()
        self.adapter_search.setPlaceholderText("Search adapter, family, capability...")
        self.adapter_search.textChanged.connect(self._apply_adapter_filters)
        adapter_filter_row.addWidget(self.adapter_search)

        self.adapter_family_filter = QtGui.QComboBox()
        self.adapter_family_filter.addItem("All families", "")
        self.adapter_family_filter.currentIndexChanged.connect(self._apply_adapter_filters)
        adapter_filter_row.addWidget(self.adapter_family_filter)

        self.adapter_capability_filter = QtGui.QComboBox()
        self.adapter_capability_filter.addItem("All capabilities", "")
        self.adapter_capability_filter.addItem("Supports GPU", "supports_gpu")
        self.adapter_capability_filter.addItem("Supports Remote", "supports_remote")
        self.adapter_capability_filter.addItem("Supports Parallel", "supports_parallel")
        self.adapter_capability_filter.addItem("Commercial-safe core", "commercial_core_safe")
        self.adapter_capability_filter.currentIndexChanged.connect(self._apply_adapter_filters)
        adapter_filter_row.addWidget(self.adapter_capability_filter)

        self.copy_adapter_json_button = QtGui.QPushButton("Copy Matrix JSON")
        self.copy_adapter_json_button.clicked.connect(self._copy_adapter_matrix_json)
        adapter_filter_row.addWidget(self.copy_adapter_json_button)

        self.export_adapter_csv_button = QtGui.QPushButton("Export Matrix CSV")
        self.export_adapter_csv_button.clicked.connect(self._export_adapter_matrix_csv)
        adapter_filter_row.addWidget(self.export_adapter_csv_button)
        layout.addLayout(adapter_filter_row)

        self.adapter_table = QtGui.QTableWidget(0, len(self._ADAPTER_COLUMNS))
        self.adapter_table.setHorizontalHeaderLabels(self._ADAPTER_COLUMNS)
        self.adapter_table.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.adapter_table.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.adapter_table.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.adapter_table.setAlternatingRowColors(True)
        self.adapter_table.horizontalHeader().setStretchLastSection(True)
        self.adapter_table.itemSelectionChanged.connect(self._update_adapter_details)
        self.adapter_table.setMaximumHeight(180)
        layout.addWidget(self.adapter_table)

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

        adapter_rows = self.runtime.job_service.adapter_capability_matrix()
        self._adapter_rows = list(adapter_rows)
        self._refresh_adapter_family_filter()
        self._apply_adapter_filters()

    def _refresh_adapter_family_filter(self):
        current_family = self.adapter_family_filter.currentData() or ""
        families = collect_families(self._adapter_rows)
        self.adapter_family_filter.blockSignals(True)
        self.adapter_family_filter.clear()
        self.adapter_family_filter.addItem("All families", "")
        for family in families:
            self.adapter_family_filter.addItem(family, family)
        index = self.adapter_family_filter.findData(current_family)
        self.adapter_family_filter.setCurrentIndex(index if index >= 0 else 0)
        self.adapter_family_filter.blockSignals(False)

    def _filtered_adapter_rows(self):
        text_filter = self.adapter_search.text()
        family_filter = str(self.adapter_family_filter.currentData() or "")
        capability_filter = str(self.adapter_capability_filter.currentData() or "")

        return filter_rows(
            self._adapter_rows,
            text_filter=text_filter,
            family_filter=family_filter,
            capability_filter=capability_filter,
        )

    def _apply_adapter_filters(self):
        adapter_rows = self._filtered_adapter_rows()
        self.adapter_table.setRowCount(len(adapter_rows))
        for row, adapter in enumerate(adapter_rows):
            values = (
                adapter.get("display_name", adapter.get("adapter_id", "")),
                adapter.get("family", ""),
                adapter.get("version", ""),
                "Yes" if adapter.get("commercial_core_safe", False) else "No",
                "Yes" if adapter.get("supports_gpu", False) else "No",
                "Yes" if adapter.get("supports_remote", False) else "No",
                "Yes" if adapter.get("supports_parallel", False) else "No",
                "Yes" if adapter.get("supports_transient", False) else "No",
            )
            for column, value in enumerate(values):
                item = QtGui.QTableWidgetItem(str(value))
                if column == 0:
                    item.setData(QtCore.Qt.UserRole, adapter)
                self.adapter_table.setItem(row, column, item)
        if adapter_rows:
            self.adapter_table.selectRow(0)
        else:
            self.details.setPlainText("No adapters match the current filter.")

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

    def _update_adapter_details(self):
        indexes = self.adapter_table.selectionModel().selectedRows()
        if not indexes:
            return
        item = self.adapter_table.item(indexes[0].row(), 0)
        if item is None:
            return
        adapter = item.data(QtCore.Qt.UserRole) or {}
        payload = {
            "adapter": {
                "adapter_id": adapter.get("adapter_id", ""),
                "display_name": adapter.get("display_name", ""),
                "family": adapter.get("family", ""),
                "version": adapter.get("version", ""),
                "commercial_core_safe": adapter.get("commercial_core_safe", False),
                "experimental": adapter.get("experimental", False),
                "supported_solver_versions": adapter.get("supported_solver_versions", ()),
            },
            "capabilities": {
                "supports_remote": adapter.get("supports_remote", False),
                "supports_parallel": adapter.get("supports_parallel", False),
                "supports_gpu": adapter.get("supports_gpu", False),
                "supports_transient": adapter.get("supports_transient", False),
                "supported_physics": adapter.get("supported_physics", ()),
                "feature_flags": adapter.get("feature_flags", {}),
            },
            "notes": adapter.get("notes", ""),
        }
        self.details.setPlainText(json.dumps(payload, indent=2, sort_keys=True))

    def _copy_adapter_matrix_json(self):
        payload = self._filtered_adapter_rows()
        QtGui.QApplication.clipboard().setText(matrix_to_json(payload))
        FreeCAD.Console.PrintMessage(
            f"FlowStudio: Copied adapter capability matrix ({len(payload)} rows) as JSON.\n"
        )

    def _export_adapter_matrix_csv(self):
        rows = self._filtered_adapter_rows()
        default_path = "flowstudio_adapter_matrix.csv"
        selected_path = default_path
        if FreeCAD.GuiUp:
            selected_path = QtGui.QFileDialog.getSaveFileName(
                None,
                "Export Adapter Capability Matrix",
                default_path,
                "CSV Files (*.csv)",
            )[0]
        if not selected_path:
            return

        with open(selected_path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=ADAPTER_MATRIX_CSV_FIELDNAMES)
            writer.writeheader()
            for adapter in rows:
                writer.writerow(to_csv_row(adapter))
        FreeCAD.Console.PrintMessage(
            f"FlowStudio: Exported adapter capability matrix CSV to {selected_path}\n"
        )

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
