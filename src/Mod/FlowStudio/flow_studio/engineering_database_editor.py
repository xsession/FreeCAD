# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Engineering database editor dialog."""

from __future__ import annotations

import copy

import FreeCAD
from PySide import QtCore, QtGui

from flow_studio.engineering_database import (
    load_database,
    reset_user_database,
    save_database,
    user_database_path,
)


class EngineeringDatabaseDialog(QtGui.QDialog):
    """Tree/table editor for FlowStudio engineering database entries."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("FlowStudio Engineering Database")
        self.resize(1000, 720)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, False)
        self.setWindowModality(QtCore.Qt.NonModal)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Window)
        self.database = load_database()
        self.current_path: list[str] = []
        self._build_ui()
        self._populate_tree()

    def closeEvent(self, event):
        global _ENGINEERING_DATABASE_DIALOG
        _ENGINEERING_DATABASE_DIALOG = None
        super().closeEvent(event)

    def _build_ui(self):
        layout = QtGui.QVBoxLayout(self)

        toolbar = QtGui.QToolBar()
        self.act_save = toolbar.addAction("Save")
        self.act_new = toolbar.addAction("New Item")
        self.act_duplicate = toolbar.addAction("Duplicate")
        self.act_delete = toolbar.addAction("Delete")
        toolbar.addSeparator()
        self.act_reset = toolbar.addAction("Reset Defaults")
        self.act_save.triggered.connect(self._save)
        self.act_new.triggered.connect(self._new_item)
        self.act_duplicate.triggered.connect(self._duplicate_item)
        self.act_delete.triggered.connect(self._delete_item)
        self.act_reset.triggered.connect(self._reset_defaults)
        layout.addWidget(toolbar)

        splitter = QtGui.QSplitter()
        layout.addWidget(splitter, 1)

        left = QtGui.QWidget()
        left_layout = QtGui.QVBoxLayout(left)
        left_layout.addWidget(QtGui.QLabel("Database tree:"))
        self.tree = QtGui.QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.currentItemChanged.connect(self._on_tree_changed)
        left_layout.addWidget(self.tree)
        splitter.addWidget(left)

        right = QtGui.QWidget()
        right_layout = QtGui.QVBoxLayout(right)
        self.path_label = QtGui.QLabel("")
        right_layout.addWidget(self.path_label)
        self.tabs = QtGui.QTabWidget()
        right_layout.addWidget(self.tabs, 1)

        self.items_table = QtGui.QTableWidget(0, 2)
        self.items_table.setHorizontalHeaderLabels(["Items", "Comments"])
        self.items_table.itemSelectionChanged.connect(self._on_item_selected)
        self.items_table.horizontalHeader().setStretchLastSection(True)
        self.tabs.addTab(self.items_table, "Items")

        self.props_table = QtGui.QTableWidget(0, 2)
        self.props_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.props_table.horizontalHeader().setStretchLastSection(True)
        self.tabs.addTab(self.props_table, "Item Properties")

        self.curve_table = QtGui.QTableWidget(0, 2)
        self.curve_table.setHorizontalHeaderLabels(["Volume flow rate [m^3/s]", "Pressure difference [Pa]"])
        self.curve_table.horizontalHeader().setStretchLastSection(True)
        self.tabs.addTab(self.curve_table, "Tables and Curves")
        splitter.addWidget(right)
        splitter.setSizes([260, 740])

        buttons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self):
        self._store_current_tables()
        self._save()
        super().accept()

    def _populate_tree(self):
        self.tree.clear()
        for root_name in ("fans", "heat_sinks", "materials", "units"):
            root_value = self.database.get(root_name, {})
            root_item = QtGui.QTreeWidgetItem([self._display_name(root_name)])
            root_item.setData(0, QtCore.Qt.UserRole, [root_name])
            self.tree.addTopLevelItem(root_item)
            self._add_tree_children(root_item, root_value, [root_name])
            root_item.setExpanded(True)

    def _add_tree_children(self, parent, value, path):
        if not isinstance(value, dict):
            return
        for key, child in sorted(value.items()):
            if not isinstance(child, dict):
                continue
            item = QtGui.QTreeWidgetItem([key])
            item.setData(0, QtCore.Qt.UserRole, path + [key])
            parent.addChild(item)
            if not self._is_leaf(child):
                self._add_tree_children(item, child, path + [key])

    @staticmethod
    def _display_name(name):
        return name.replace("_", " ").title()

    @staticmethod
    def _is_leaf(value):
        return isinstance(value, dict) and (
            "curve" in value or any(not isinstance(v, dict) for v in value.values())
        )

    def _on_tree_changed(self, item, _previous):
        self._store_current_tables()
        self.current_path = item.data(0, QtCore.Qt.UserRole) if item else []
        self._load_path()

    def _node(self):
        node = self.database
        for part in self.current_path:
            node = node.setdefault(part, {})
        return node

    def _load_path(self):
        path = "/".join(self.current_path)
        self.path_label.setText(path or "(root)")
        node = self._node()
        self._load_items(node)
        if self._is_leaf(node):
            self._load_properties(node)
            self._load_curve(node.get("curve", []))
        else:
            self._load_properties({})
            self._load_curve([])

    def _load_items(self, node):
        self.items_table.setRowCount(0)
        if not isinstance(node, dict):
            return
        for key, value in sorted(node.items()):
            if key.startswith("_"):
                continue
            if not isinstance(value, dict):
                continue
            row = self.items_table.rowCount()
            self.items_table.insertRow(row)
            name_item = QtGui.QTableWidgetItem(key)
            comment = str(value.get("Comment", "")) if isinstance(value, dict) else ""
            comment_item = QtGui.QTableWidgetItem(comment)
            self.items_table.setItem(row, 0, name_item)
            self.items_table.setItem(row, 1, comment_item)

    def _on_item_selected(self):
        selected = self.items_table.selectedItems()
        if not selected:
            self._load_properties({})
            self._load_curve([])
            return
        row = selected[0].row()
        key_item = self.items_table.item(row, 0)
        if key_item is None:
            return
        entry = self._node().get(key_item.text(), {})
        if not isinstance(entry, dict):
            entry = {}
        self._load_properties(entry)
        self._load_curve(entry.get("curve", []))

    def _load_properties(self, entry):
        self.props_table.setRowCount(0)
        for key, value in sorted((entry or {}).items()):
            if key == "curve":
                continue
            row = self.props_table.rowCount()
            self.props_table.insertRow(row)
            self.props_table.setItem(row, 0, QtGui.QTableWidgetItem(str(key)))
            self.props_table.setItem(row, 1, QtGui.QTableWidgetItem(str(value)))

    def _load_curve(self, curve):
        self.curve_table.setRowCount(0)
        for pair in curve or []:
            row = self.curve_table.rowCount()
            self.curve_table.insertRow(row)
            x = pair[0] if len(pair) > 0 else 0.0
            y = pair[1] if len(pair) > 1 else 0.0
            self.curve_table.setItem(row, 0, QtGui.QTableWidgetItem(str(x)))
            self.curve_table.setItem(row, 1, QtGui.QTableWidgetItem(str(y)))

    def _store_current_tables(self):
        selected = self.items_table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        key_item = self.items_table.item(row, 0)
        if key_item is None:
            return
        key = key_item.text()
        node = self._node()
        entry = node.setdefault(key, {})
        if not isinstance(entry, dict):
            entry = {}
            node[key] = entry

        for r in range(self.props_table.rowCount()):
            prop = self._table_text(self.props_table, r, 0)
            value = self._table_text(self.props_table, r, 1)
            if prop:
                entry[prop] = self._coerce(value)

        curve = []
        for r in range(self.curve_table.rowCount()):
            x = self._coerce(self._table_text(self.curve_table, r, 0))
            y = self._coerce(self._table_text(self.curve_table, r, 1))
            if x != "" and y != "":
                curve.append([float(x), float(y)])
        if curve:
            entry["curve"] = curve

    @staticmethod
    def _table_text(table, row, col):
        item = table.item(row, col)
        return item.text() if item is not None else ""

    @staticmethod
    def _coerce(value):
        if value in ("True", "False"):
            return value == "True"
        try:
            return float(value)
        except (TypeError, ValueError):
            return value

    def _new_item(self):
        node = self._node()
        if not isinstance(node, dict):
            return
        base = "New Item"
        name = base
        index = 1
        while name in node:
            index += 1
            name = f"{base} {index}"
        node[name] = {"MaterialName": name, "Comment": "User-defined database item"}
        self._load_path()

    def _duplicate_item(self):
        selected = self.items_table.selectedItems()
        if not selected:
            return
        key = self.items_table.item(selected[0].row(), 0).text()
        node = self._node()
        if key not in node:
            return
        new_key = f"{key} Copy"
        index = 1
        while new_key in node:
            index += 1
            new_key = f"{key} Copy {index}"
        node[new_key] = copy.deepcopy(node[key])
        self._load_path()

    def _delete_item(self):
        selected = self.items_table.selectedItems()
        if not selected:
            return
        key = self.items_table.item(selected[0].row(), 0).text()
        node = self._node()
        if key in node:
            del node[key]
        self._load_path()

    def _save(self):
        self._store_current_tables()
        path = save_database(self.database)
        FreeCAD.Console.PrintMessage(f"FlowStudio: Engineering database saved to {path}\n")

    def _reset_defaults(self):
        answer = QtGui.QMessageBox.question(
            self,
            "Reset Engineering Database",
            "Reset the user engineering database to built-in defaults?",
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
            QtGui.QMessageBox.No,
        )
        if answer != QtGui.QMessageBox.Yes:
            return
        reset_user_database()
        self.database = load_database()
        self._populate_tree()
        FreeCAD.Console.PrintMessage(f"FlowStudio: Engineering database reset at {user_database_path()}\n")


_ENGINEERING_DATABASE_DIALOG = None


def _dialog_parent():
    try:
        import FreeCADGui

        main_window = FreeCADGui.getMainWindow()
        if main_window is not None:
            return main_window
    except Exception:
        pass

    app = QtGui.QApplication.instance()
    if app is None:
        return None

    for widget in app.topLevelWidgets():
        if isinstance(widget, QtGui.QMainWindow):
            return widget

    return app.activeWindow()


def show_engineering_database_editor():
    global _ENGINEERING_DATABASE_DIALOG

    try:
        dialog_valid = _ENGINEERING_DATABASE_DIALOG is not None and _ENGINEERING_DATABASE_DIALOG.isVisible() is not None
    except RuntimeError:
        dialog_valid = False

    if not dialog_valid:
        _ENGINEERING_DATABASE_DIALOG = EngineeringDatabaseDialog(parent=_dialog_parent())

    dialog = _ENGINEERING_DATABASE_DIALOG
    dialog.setParent(_dialog_parent())
    dialog.setWindowFlags(dialog.windowFlags() | QtCore.Qt.Window)
    dialog.setWindowModality(QtCore.Qt.NonModal)
    dialog.showNormal()
    dialog.show()
    try:
        dialog.raise_()
    except AttributeError:
        dialog.raise()
    dialog.activateWindow()
    FreeCAD.Console.PrintMessage("FlowStudio: Engineering database editor opened\n")
    return dialog
