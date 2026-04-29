# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Task panel for typed Geant4 result child objects."""

from PySide import QtGui

from flow_studio.taskpanels.base_taskpanel import BaseTaskPanel
from flow_studio.ui.geant4_result_presenter import (
    Geant4ResultComponentPresenter,
    Geant4ResultComponentSettings,
)


class TaskGeant4ResultComponent(BaseTaskPanel):
    SUMMARY_TITLE = "Geant4 Result Component"
    SUMMARY_DETAIL = "Inspect imported Geant4 component metadata for {label}."

    def __init__(self, obj):
        self._presenter = Geant4ResultComponentPresenter()
        super().__init__(obj)

    def _build_task_validation(self):
        return self._presenter.build_validation(self._current_settings())

    def _build_form(self):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)

        flow_type = getattr(self.obj, "FlowType", "")
        is_scoring = flow_type == "FlowStudio::Geant4ScoringResult"
        title = "Geant4 Scoring Result" if is_scoring else "Geant4 Detector Result"
        layout.addWidget(QtGui.QLabel(f"<b>{title}</b>"))

        summary = self._section(layout, "Summary")
        parent_name = getattr(getattr(self.obj, "ParentResult", None), "Label", "")
        self._add_row(summary, "Parent Result:", QtGui.QLabel(parent_name))

        if is_scoring:
            self._add_row(summary, "Score Quantity:", QtGui.QLabel(getattr(self.obj, "ScoreQuantity", "")))
            self._add_row(summary, "Scoring Type:", QtGui.QLabel(getattr(self.obj, "ScoringType", "")))
            self._add_row(summary, "Bins:", QtGui.QLabel(getattr(self.obj, "BinShape", "")))
            fields = list(getattr(self.obj, "AvailableFields", []) or [getattr(self.obj, "ActiveField", "")])
            self.cb_field = self._combo(fields, getattr(self.obj, "ActiveField", ""))
            self._add_row(summary, "Active Field:", self.cb_field)
        else:
            self._add_row(summary, "Collection:", QtGui.QLabel(getattr(self.obj, "CollectionName", "")))
            self._add_row(summary, "Detector Type:", QtGui.QLabel(getattr(self.obj, "DetectorType", "")))
            self._add_row(summary, "Threshold [keV]:", QtGui.QLabel(str(getattr(self.obj, "ThresholdKeV", 0.0))))
            self.cb_field = None

        refs_section = self._section(layout, "References")
        refs = "\n".join(getattr(self.obj, "ReferenceTargets", []) or [])
        txt_refs = QtGui.QPlainTextEdit(refs)
        txt_refs.setReadOnly(True)
        refs_section.addWidget(txt_refs)

        if not is_scoring:
            monitor_section = self._section(layout, "Monitors")
            txt_monitors = QtGui.QPlainTextEdit("\n".join(getattr(self.obj, "MonitorNames", []) or []))
            txt_monitors.setReadOnly(True)
            monitor_section.addWidget(txt_monitors)

        artifacts_section = self._section(layout, "Artifacts")
        txt_artifacts = QtGui.QPlainTextEdit("\n".join(getattr(self.obj, "ArtifactFiles", []) or []))
        txt_artifacts.setReadOnly(True)
        artifacts_section.addWidget(txt_artifacts)

        notes_section = self._section(layout, "Notes")
        txt_notes = QtGui.QPlainTextEdit(getattr(self.obj, "ImportNotes", ""))
        txt_notes.setReadOnly(True)
        notes_section.addWidget(txt_notes)

        layout.addStretch()
        return widget

    def _current_settings(self):
        if not hasattr(self, "cb_field"):
            return self._presenter.read_settings(self.obj)
        return Geant4ResultComponentSettings(
            parent_result=getattr(self.obj, "ParentResult", None),
            flow_type=getattr(self.obj, "FlowType", ""),
            available_fields=tuple(getattr(self.obj, "AvailableFields", []) or []),
            active_field=(self.cb_field.currentText().strip() if self.cb_field is not None else str(getattr(self.obj, "ActiveField", "") or "").strip()),
            artifact_files=tuple(getattr(self.obj, "ArtifactFiles", []) or []),
        )

    def _store(self):
        if self.cb_field is not None:
            self._presenter.persist_settings(self.obj, self._current_settings())