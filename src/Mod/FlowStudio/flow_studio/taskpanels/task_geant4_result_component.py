# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Task panel for typed Geant4 result child objects."""

from PySide import QtGui

from flow_studio.taskpanels.base_taskpanel import BaseTaskPanel


class TaskGeant4ResultComponent(BaseTaskPanel):
    SUMMARY_TITLE = "Geant4 Result Component"
    SUMMARY_DETAIL = "Inspect imported Geant4 component metadata for {label}."

    def _build_task_validation(self):
        parent_result = getattr(self.obj, "ParentResult", None)
        flow_type = getattr(self.obj, "FlowType", "")
        available_fields = list(getattr(self.obj, "AvailableFields", []) or [])
        active_field = str(getattr(self.obj, "ActiveField", "") or "").strip()

        if parent_result is None:
            return (
                "info",
                "Parent Geant4 result missing",
                "Link this component back to a Geant4 result so its source context is clear.",
            )

        if flow_type == "FlowStudio::Geant4ScoringResult":
            if available_fields and active_field not in available_fields:
                return (
                    "warning",
                    "Selected field is unavailable",
                    "Choose an active field that exists in this scoring result.",
                )
            if not available_fields:
                return (
                    "info",
                    "No scoring fields available",
                    "The scoring result is linked, but no imported fields are available yet.",
                )

        if not list(getattr(self.obj, "ArtifactFiles", []) or []):
            return (
                "info",
                "No component artifacts recorded",
                "This result component has metadata, but no exported artifact files are attached yet.",
            )

        return (
            "success",
            "Geant4 component ready",
            "Imported metadata and artifacts are available for this Geant4 result component.",
        )

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

    def _store(self):
        if self.cb_field is not None:
            self.obj.ActiveField = self.cb_field.currentText()