# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Task panel for native Geant4 result objects."""

from PySide import QtGui

from flow_studio.taskpanels.base_taskpanel import BaseTaskPanel
from flow_studio.ui.geant4_result_presenter import Geant4ResultPresenter, Geant4ResultSettings


class TaskGeant4Result(BaseTaskPanel):
    SUMMARY_TITLE = "Geant4 Result"
    SUMMARY_DETAIL = (
        "Inspect imported Geant4 artifacts, parsed fields, and monitors for {label}."
    )

    def __init__(self, obj):
        self._presenter = Geant4ResultPresenter()
        super().__init__(obj)

    def _build_task_validation(self):
        return self._presenter.build_validation(self._current_settings())

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

    def _current_settings(self):
        if not hasattr(self, "cb_field"):
            return self._presenter.read_settings(self.obj)
        return Geant4ResultSettings(
            result_file=str(getattr(self.obj, "ResultFile", "") or "").strip(),
            artifact_files=tuple(getattr(self.obj, "ArtifactFiles", []) or []),
            available_fields=tuple(getattr(self.obj, "AvailableFields", []) or []),
            active_field=self.cb_field.currentText().strip(),
        )

    def _store(self):
        self._presenter.persist_settings(self.obj, self._current_settings())