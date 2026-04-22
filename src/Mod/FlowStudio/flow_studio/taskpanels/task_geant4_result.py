# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Task panel for native Geant4 result objects."""

from PySide import QtGui

from flow_studio.taskpanels.base_taskpanel import BaseTaskPanel


class TaskGeant4Result(BaseTaskPanel):
    SUMMARY_TITLE = "Geant4 Result"
    SUMMARY_DETAIL = (
        "Inspect imported Geant4 artifacts, parsed fields, and monitors for {label}."
    )

    def _build_task_validation(self):
        result_file = str(getattr(self.obj, "ResultFile", "") or "").strip()
        artifact_files = list(getattr(self.obj, "ArtifactFiles", []) or [])
        available_fields = list(getattr(self.obj, "AvailableFields", []) or [])
        active_field = str(getattr(self.obj, "ActiveField", "") or "").strip()

        if not result_file and not artifact_files:
            return (
                "info",
                "Import a Geant4 result",
                "Load a Geant4 summary or artifact set before inspecting fields and monitor data.",
            )

        if available_fields and active_field not in available_fields:
            return (
                "warning",
                "Selected field is unavailable",
                "Choose an active field that exists in the imported Geant4 result set.",
            )

        if not available_fields:
            return (
                "info",
                "No parsed fields available yet",
                "The result object is present, but no parsed Geant4 fields are available for inspection yet.",
            )

        return (
            "success",
            "Geant4 result ready",
            "Imported artifacts and parsed fields are available for inspection.",
        )

    def _build_form(self):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)
        layout.addWidget(QtGui.QLabel("<b>Geant4 Result</b>"))

        summary = self._section(layout, "Summary")
        self.lbl_result = QtGui.QLabel(getattr(self.obj, "ResultFile", ""))
        self._add_row(summary, "Primary Artifact:", self.lbl_result)
        self.lbl_summary = QtGui.QLabel(getattr(self.obj, "SummaryFile", ""))
        self._add_row(summary, "Summary File:", self.lbl_summary)
        self.lbl_primary = QtGui.QLabel(getattr(self.obj, "PrimaryQuantity", ""))
        self._add_row(summary, "Primary Quantity:", self.lbl_primary)
        scoring_count = len(getattr(self.obj, "ScoringResults", []) or [])
        detector_count = len(getattr(self.obj, "DetectorResults", []) or [])
        self._add_row(summary, "Scoring Outputs:", QtGui.QLabel(str(scoring_count)))
        self._add_row(summary, "Detector Outputs:", QtGui.QLabel(str(detector_count)))

        fields_section = self._section(layout, "Fields")
        fields = list(getattr(self.obj, "AvailableFields", []) or [getattr(self.obj, "ActiveField", "dose")])
        self.cb_field = self._combo(fields, getattr(self.obj, "ActiveField", ""))
        self._add_row(fields_section, "Active Field:", self.cb_field)
        self.lbl_monitors = QtGui.QLabel(", ".join(getattr(self.obj, "MonitorNames", []) or []))
        self._add_row(fields_section, "Monitors:", self.lbl_monitors)

        artifacts_section = self._section(layout, "Artifacts")
        artifacts = "\n".join(getattr(self.obj, "ArtifactFiles", []) or [])
        self.txt_artifacts = QtGui.QPlainTextEdit(artifacts)
        self.txt_artifacts.setReadOnly(True)
        artifacts_section.addWidget(self.txt_artifacts)

        notes_section = self._section(layout, "Notes")
        self.txt_notes = QtGui.QPlainTextEdit(getattr(self.obj, "ImportNotes", ""))
        self.txt_notes.setReadOnly(True)
        notes_section.addWidget(self.txt_notes)

        layout.addStretch()
        return widget

    def _store(self):
        self.obj.ActiveField = self.cb_field.currentText()