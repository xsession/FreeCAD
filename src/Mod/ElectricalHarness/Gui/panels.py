"""Dockable panel placeholders for enterprise-style workflow."""

from __future__ import annotations

from typing import Callable, Dict, Iterable, List

from PySide import QtCore
from PySide import QtGui


class _BaseDockPanel(QtGui.QDockWidget):
    panel_name = "ElectricalHarness"
    rowActivated = QtCore.Signal(str)

    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        self.setObjectName(self.panel_name)
        self._provider: Callable[[], List[Dict[str, object]]] | None = None
        self._all_rows: List[Dict[str, object]] = []
        self._active_probe_token = ""
        self._suppress_row_activation = False

        container = QtGui.QWidget(self)
        layout = QtGui.QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)

        search_row = QtGui.QHBoxLayout()
        self._search = QtGui.QLineEdit(container)
        self._search.setPlaceholderText("Filter...")
        self._search.textChanged.connect(self._apply_filter)
        self._refresh_button = QtGui.QPushButton("Refresh", container)
        self._refresh_button.clicked.connect(self.refresh)
        search_row.addWidget(self._search)
        search_row.addWidget(self._refresh_button)
        layout.addLayout(search_row)

        self._table = QtGui.QTableWidget(0, 0, container)
        self._table.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.itemSelectionChanged.connect(self._emit_row_activation)
        layout.addWidget(self._table)

        self._status_label = QtGui.QLabel("Rows: 0", container)
        layout.addWidget(self._status_label)

        self.setWidget(container)

    def set_provider(self, provider: Callable[[], List[Dict[str, object]]]) -> None:
        self._provider = provider

    def refresh(self) -> None:
        if self._provider is None:
            return
        self._all_rows = self._provider()
        self._apply_filter()

    def set_rows(self, rows: Iterable[Dict[str, object]]) -> None:
        self._all_rows = list(rows)
        self._apply_filter()

    def focus_on_token(self, token: str) -> None:
        if not token:
            return
        self._active_probe_token = token
        self._search.setText(token)
        self._select_first_row()
        self.raise_()
        self.show()

    def _apply_filter(self) -> None:
        token = self._search.text().strip().lower()
        rows = self._all_rows
        if token:
            rows = [
                row
                for row in rows
                if token in " ".join(str(value).lower() for value in row.values())
            ]

        headers: List[str] = []
        if rows:
            headers = list(rows[0].keys())
        self._table.setColumnCount(len(headers))
        self._table.setHorizontalHeaderLabels(headers)
        self._table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for col_index, header in enumerate(headers):
                value = row.get(header, "")
                self._table.setItem(row_index, col_index, QtGui.QTableWidgetItem(str(value)))
        self._select_first_row()
        self._update_status(len(rows))

    def _emit_row_activation(self) -> None:
        if self._suppress_row_activation:
            return
        row = self._table.currentRow()
        if row < 0:
            return
        headers = []
        for idx in range(self._table.columnCount()):
            item = self._table.horizontalHeaderItem(idx)
            headers.append(item.text() if item else "")
        values: Dict[str, str] = {}
        for idx, header in enumerate(headers):
            cell = self._table.item(row, idx)
            values[header] = cell.text() if cell else ""

        for preferred_key in (
            "entity",
            "id",
            "entity_id",
            "net_id",
            "wire_id",
            "from_pin_id",
            "to_pin_id",
        ):
            stable_id = values.get(preferred_key, "").strip()
            if stable_id and stable_id != "-":
                self._active_probe_token = stable_id
                self._update_status(self._table.rowCount())
                self.rowActivated.emit(stable_id)
                return

    def _select_first_row(self) -> None:
        if self._table.rowCount() <= 0:
            return
        self._suppress_row_activation = True
        try:
            self._table.setCurrentCell(0, 0)
            self._table.selectRow(0)
            item = self._table.item(0, 0)
            if item is not None:
                self._table.scrollToItem(item)
        finally:
            self._suppress_row_activation = False

    def _update_status(self, filtered_count: int) -> None:
        if self._active_probe_token:
            if filtered_count <= 0:
                self._status_label.setText(
                    f"Selected: {self._active_probe_token} (no matches in this panel)"
                )
            else:
                self._status_label.setText(
                    f"Selected: {self._active_probe_token} ({filtered_count} match(es))"
                )
            return
        self._status_label.setText(f"Rows: {filtered_count}")


class ProjectBrowserPanel(_BaseDockPanel):
    panel_name = "ElectricalHarnessProjectBrowser"


class LibraryBrowserPanel(_BaseDockPanel):
    panel_name = "ElectricalHarnessLibraryBrowser"


class ValidationPanel(_BaseDockPanel):
    panel_name = "ElectricalHarnessValidation"


class ReportsPanel(_BaseDockPanel):
    panel_name = "ElectricalHarnessReports"
