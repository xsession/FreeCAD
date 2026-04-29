# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Engineering database editor dialog."""

from __future__ import annotations

import copy

import FreeCAD
from PySide import QtCore, QtGui

from flow_studio.catalog.database import (
    MATERIAL_CATEGORY_FIELDS,
    default_material_entry,
    load_database,
    reset_user_database,
    save_database,
    user_database_path,
)


class EngineeringDatabaseDialog(QtGui.QDialog):
    """Tree/table editor for FlowStudio engineering database entries."""

    def __init__(
        self,
        parent=None,
        pick_mode: str | None = None,
        material_categories: tuple[str, ...] = (),
        initial_preset: str | None = None,
    ):
        super().__init__(parent)
        self.pick_mode = pick_mode
        self.material_categories = tuple(material_categories or ())
        self.initial_preset = initial_preset
        self.database = load_database()
        self.current_path: list[str] = []
        self._selected_material: tuple[str, dict] | None = None
        self.setWindowTitle("FlowStudio Engineering Database")
        self.resize(1120, 760)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, False)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Window)
        self._build_ui()
        self._populate_tree()
        self._focus_initial_item()

    def closeEvent(self, event):
        global _ENGINEERING_DATABASE_DIALOG
        if self.pick_mode is None:
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
        self.act_new_property = toolbar.addAction("Add Property")
        self.act_delete_property = toolbar.addAction("Remove Property")
        self.act_add_curve_row = toolbar.addAction("Add Curve Row")
        self.act_delete_curve_row = toolbar.addAction("Remove Curve Row")
        toolbar.addSeparator()
        self.act_reset = toolbar.addAction("Reset Defaults")
        self.act_save.triggered.connect(self._save)
        self.act_new.triggered.connect(self._new_item)
        self.act_duplicate.triggered.connect(self._duplicate_item)
        self.act_delete.triggered.connect(self._delete_item)
        self.act_new_property.triggered.connect(self._add_property_row)
        self.act_delete_property.triggered.connect(self._remove_property_row)
        self.act_add_curve_row.triggered.connect(self._add_curve_row)
        self.act_delete_curve_row.triggered.connect(self._remove_curve_row)
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
        self.items_table.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.items_table.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
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

        self.unit_matrix_table = QtGui.QTableWidget(0, 0)
        self.unit_matrix_table.horizontalHeader().setStretchLastSection(True)
        self.tabs.addTab(self.unit_matrix_table, "Unit Matrix")
        splitter.addWidget(right)
        splitter.setSizes([300, 820])

        buttons = QtGui.QDialogButtonBox()
        if self.pick_mode == "material":
            self.btn_use_selected = buttons.addButton("Use Selected Material", QtGui.QDialogButtonBox.AcceptRole)
            self.btn_cancel = buttons.addButton(QtGui.QDialogButtonBox.Cancel)
        else:
            self.btn_ok = buttons.addButton(QtGui.QDialogButtonBox.Ok)
            self.btn_cancel = buttons.addButton(QtGui.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self):
        self._store_current_tables()
        self._store_unit_matrix()
        if self.pick_mode == "material":
            selected = self._selected_material_entry()
            if selected is None:
                QtGui.QMessageBox.warning(
                    self,
                    "Select Material",
                    "Select a material entry before using it in the task panel.",
                )
                return
            self._selected_material = selected
        self._save()
        super().accept()

    def selected_material(self):
        return copy.deepcopy(self._selected_material)

    def _populate_tree(self):
        self.tree.clear()
        for root_name in ("materials", "optics", "fans", "heat_sinks", "units"):
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
            if path == ["materials"] and self.material_categories and key not in self.material_categories:
                continue
            if not isinstance(child, dict):
                continue
            item = QtGui.QTreeWidgetItem([key])
            item.setData(0, QtCore.Qt.UserRole, path + [key])
            parent.addChild(item)
            if not self._is_leaf(child):
                self._add_tree_children(item, child, path + [key])

    def _focus_initial_item(self):
        target_path = ["materials"]
        if self.material_categories:
            target_path.append(self.material_categories[0])
        item = self._find_item_by_path(target_path)
        if item is None:
            item = self.tree.topLevelItem(0)
        if item is not None:
            self.tree.setCurrentItem(item)
        if self.initial_preset:
            self._select_item_row(self.initial_preset)

    def _find_item_by_path(self, path):
        if not path:
            return None

        def walk(item):
            if item.data(0, QtCore.Qt.UserRole) == path:
                return item
            for index in range(item.childCount()):
                found = walk(item.child(index))
                if found is not None:
                    return found
            return None

        for index in range(self.tree.topLevelItemCount()):
            found = walk(self.tree.topLevelItem(index))
            if found is not None:
                return found
        return None

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

    def _parent_node(self):
        node = self.database
        for part in self.current_path[:-1]:
            node = node.setdefault(part, {})
        return node

    def _load_path(self):
        self.path_label.setText("/".join(self.current_path) or "(root)")
        node = self._node()
        self._load_items(node)
        if self._is_leaf(node):
            self._load_properties(node)
            self._load_curve(node.get("curve", []))
        else:
            self._load_properties({})
            self._load_curve([])
        self._load_unit_matrix()

    def _load_items(self, node):
        self.items_table.setRowCount(0)
        if not isinstance(node, dict) or self._is_leaf(node):
            return
        for key, value in sorted(node.items()):
            if key.startswith("_") or not isinstance(value, dict):
                continue
            row = self.items_table.rowCount()
            self.items_table.insertRow(row)
            self.items_table.setItem(row, 0, QtGui.QTableWidgetItem(key))
            self.items_table.setItem(row, 1, QtGui.QTableWidgetItem(str(value.get("Comment", ""))))

    def _on_item_selected(self):
        entry = self._selected_table_entry()
        if entry is None:
            if not self._is_leaf(self._node()):
                self._load_properties({})
                self._load_curve([])
            return
        self._load_properties(entry)
        self._load_curve(entry.get("curve", []))

    def _selected_table_key(self):
        current_row = self.items_table.currentRow()
        if current_row < 0:
            return None
        key_item = self.items_table.item(current_row, 0)
        return key_item.text() if key_item is not None else None

    def _selected_table_entry(self):
        key = self._selected_table_key()
        node = self._node()
        if key and isinstance(node, dict):
            entry = node.get(key)
            if isinstance(entry, dict):
                return entry
        return None

    def _selected_entry_location(self):
        node = self._node()
        if self._is_leaf(node) and self.current_path:
            return self._parent_node(), self.current_path[-1]
        key = self._selected_table_key()
        if key:
            return node, key
        return None, None

    def _selected_material_entry(self):
        node, key = self._selected_entry_location()
        if node is None or key is None:
            return None
        entry = node.get(key)
        if not isinstance(entry, dict) or not self._is_leaf(entry):
            return None
        if self.current_path and self.current_path[0] == "materials":
            category = self.current_path[1] if len(self.current_path) > 1 else ""
        else:
            category = ""
        if self.material_categories and category not in self.material_categories:
            return None
        return key, copy.deepcopy(entry)

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

    def _load_unit_matrix(self):
        unit_systems = sorted((self.database.get("units", {}) or {}).keys())
        matrix = self.database.get("unit_matrix", {}) or {}
        self.unit_matrix_table.setColumnCount(1 + len(unit_systems))
        self.unit_matrix_table.setHorizontalHeaderLabels(["Property"] + unit_systems)
        self.unit_matrix_table.setRowCount(0)
        for field in sorted(matrix):
            row = self.unit_matrix_table.rowCount()
            self.unit_matrix_table.insertRow(row)
            self.unit_matrix_table.setItem(row, 0, QtGui.QTableWidgetItem(field))
            for column, unit_system in enumerate(unit_systems, start=1):
                self.unit_matrix_table.setItem(
                    row,
                    column,
                    QtGui.QTableWidgetItem(str(matrix.get(field, {}).get(unit_system, ""))),
                )

    def _store_current_tables(self):
        node, key = self._selected_entry_location()
        if node is None or key is None:
            return
        entry = node.setdefault(key, {})
        if not isinstance(entry, dict):
            entry = {}
            node[key] = entry

        comment_row = self.items_table.currentRow()
        if comment_row >= 0 and not self._is_leaf(self._node()):
            comment_item = self.items_table.item(comment_row, 1)
            if comment_item is not None:
                entry["Comment"] = comment_item.text()

        entry.clear()
        for row in range(self.props_table.rowCount()):
            prop = self._table_text(self.props_table, row, 0)
            value = self._table_text(self.props_table, row, 1)
            if prop:
                entry[prop] = self._coerce(value)

        curve = []
        for row in range(self.curve_table.rowCount()):
            x = self._coerce(self._table_text(self.curve_table, row, 0))
            y = self._coerce(self._table_text(self.curve_table, row, 1))
            if x != "" and y != "":
                curve.append([float(x), float(y)])
        if curve:
            entry["curve"] = curve

    def _store_unit_matrix(self):
        unit_systems = sorted((self.database.get("units", {}) or {}).keys())
        matrix = {}
        for row in range(self.unit_matrix_table.rowCount()):
            field = self._table_text(self.unit_matrix_table, row, 0)
            if not field:
                continue
            matrix[field] = {}
            for column, unit_system in enumerate(unit_systems, start=1):
                matrix[field][unit_system] = self._table_text(self.unit_matrix_table, row, column)
        if matrix:
            self.database["unit_matrix"] = matrix

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
        target = node
        category = None
        if self._is_leaf(node):
            target = self._parent_node()
        if self.current_path and self.current_path[0] == "materials" and len(self.current_path) > 1:
            category = self.current_path[1]
        base = "New Item"
        name = base
        index = 1
        while name in target:
            index += 1
            name = f"{base} {index}"
        if category in MATERIAL_CATEGORY_FIELDS:
            target[name] = default_material_entry(category, name)
        else:
            target[name] = {"MaterialName": name, "Comment": "User-defined database item"}
        self._load_path()
        self._select_item_row(name)

    def _duplicate_item(self):
        node, key = self._selected_entry_location()
        if node is None or key is None or key not in node:
            return
        new_key = f"{key} Copy"
        index = 1
        while new_key in node:
            index += 1
            new_key = f"{key} Copy {index}"
        duplicated = copy.deepcopy(node[key])
        duplicated["MaterialName"] = new_key
        node[new_key] = duplicated
        self._load_path()
        self._select_item_row(new_key)

    def _delete_item(self):
        node, key = self._selected_entry_location()
        if node is not None and key is not None and key in node:
            del node[key]
        self._load_path()

    def _add_property_row(self):
        row = self.props_table.rowCount()
        self.props_table.insertRow(row)
        self.props_table.setItem(row, 0, QtGui.QTableWidgetItem("Property"))
        self.props_table.setItem(row, 1, QtGui.QTableWidgetItem(""))

    def _remove_property_row(self):
        row = self.props_table.currentRow()
        if row >= 0:
            self.props_table.removeRow(row)

    def _add_curve_row(self):
        row = self.curve_table.rowCount()
        self.curve_table.insertRow(row)
        self.curve_table.setItem(row, 0, QtGui.QTableWidgetItem("0.0"))
        self.curve_table.setItem(row, 1, QtGui.QTableWidgetItem("0.0"))

    def _remove_curve_row(self):
        row = self.curve_table.currentRow()
        if row >= 0:
            self.curve_table.removeRow(row)

    def _select_item_row(self, key):
        for row in range(self.items_table.rowCount()):
            item = self.items_table.item(row, 0)
            if item is not None and item.text() == key:
                self.items_table.setCurrentCell(row, 0)
                return True
        return False

    def _save(self):
        self._store_current_tables()
        self._store_unit_matrix()
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
        self._focus_initial_item()
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


def show_engineering_database_editor(
    pick_mode: str | None = None,
    material_categories: tuple[str, ...] = (),
    initial_preset: str | None = None,
):
    global _ENGINEERING_DATABASE_DIALOG

    if pick_mode == "material":
        dialog = EngineeringDatabaseDialog(
            parent=_dialog_parent(),
            pick_mode=pick_mode,
            material_categories=tuple(material_categories or ()),
            initial_preset=initial_preset,
        )
        if dialog.exec_() == QtGui.QDialog.Accepted:
            selected = dialog.selected_material()
            if selected is not None:
                FreeCAD.Console.PrintMessage(
                    f"FlowStudio: Selected material preset '{selected[0]}' from engineering database.\n"
                )
            return selected
        return None

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
        raise_method = getattr(dialog, "raise", None)
        if callable(raise_method):
            raise_method()
    dialog.activateWindow()
    FreeCAD.Console.PrintMessage("FlowStudio: Engineering database editor opened\n")
    return dialog
