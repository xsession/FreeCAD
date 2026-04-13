# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Base task panel for FlowStudio dialogs."""

import FreeCAD
import FreeCADGui
from PySide import QtGui, QtCore


class BaseTaskPanel:
    """Common task panel base with accept/reject."""

    def __init__(self, obj):
        self.obj = obj
        self.form = self._build_form()

    def _build_form(self):
        """Override to build the Qt widget. Return a QWidget."""
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)
        layout.addWidget(QtGui.QLabel("(no settings)"))
        return widget

    def accept(self):
        self._store()
        FreeCADGui.ActiveDocument.resetEdit()
        FreeCAD.ActiveDocument.recompute()
        return True

    def reject(self):
        FreeCADGui.ActiveDocument.resetEdit()
        return True

    def _store(self):
        """Override to write widget values back to the document object."""
        pass

    # Convenience helpers -----------------------------------------------
    @staticmethod
    def _add_row(layout, label_text, widget):
        row = QtGui.QHBoxLayout()
        row.addWidget(QtGui.QLabel(label_text))
        row.addWidget(widget)
        layout.addLayout(row)
        return widget

    @staticmethod
    def _spin_float(value, minimum=-1e9, maximum=1e9, decimals=6, step=0.1):
        sb = QtGui.QDoubleSpinBox()
        sb.setRange(minimum, maximum)
        sb.setDecimals(decimals)
        sb.setSingleStep(step)
        sb.setValue(value)
        return sb

    @staticmethod
    def _spin_int(value, minimum=0, maximum=999999999):
        sb = QtGui.QSpinBox()
        sb.setRange(minimum, maximum)
        sb.setValue(value)
        return sb

    @staticmethod
    def _combo(items, current):
        cb = QtGui.QComboBox()
        cb.addItems(items)
        idx = cb.findText(current)
        if idx >= 0:
            cb.setCurrentIndex(idx)
        return cb

    @staticmethod
    def _checkbox(checked):
        cb = QtGui.QCheckBox()
        cb.setChecked(checked)
        return cb
