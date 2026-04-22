# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Source-level regression checks for viewport selection defaults.

These tests stay headless and verify that selection rendering defaults remain
consistent across legacy selection, unified selection, and the preference UI.
"""

from __future__ import annotations

import os
import unittest


class TestViewportSelectionContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.dirname(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            )
        )

    def _read(self, rel_path):
        abs_path = os.path.join(self.repo_root, rel_path)
        with open(abs_path, "r", encoding="utf-8") as handle:
            return abs_path, handle.read()

    def test_selection_defaults_are_consistent_across_render_paths(self):
        unified_path, unified_source = self._read("src/Gui/Selection/SoFCUnifiedSelection.cpp")
        legacy_path, legacy_source = self._read("src/Gui/Selection/SoFCSelection.cpp")

        self.assertIn("SbColor(1.0f, 0.69f, 0.13f)", unified_source, unified_path)
        self.assertIn("SbColor(0.12f, 0.44f, 0.92f)", unified_source, unified_path)
        self.assertIn("SbColor(1.0f, 0.69f, 0.13f)", legacy_source, legacy_path)
        self.assertIn("SbColor(0.12f, 0.44f, 0.92f)", legacy_source, legacy_path)

    def test_selection_preferences_match_runtime_defaults(self):
        ui_path, ui_source = self._read("src/Gui/PreferencePages/DlgSettingsSelection.ui")

        self.assertIn("<red>31</red>", ui_source, ui_path)
        self.assertIn("<green>111</green>", ui_source, ui_path)
        self.assertIn("<blue>235</blue>", ui_source, ui_path)
        self.assertIn("<red>255</red>", ui_source, ui_path)
        self.assertIn("<green>176</green>", ui_source, ui_path)
        self.assertIn("<blue>32</blue>", ui_source, ui_path)

    def test_selection_bounding_box_uses_stronger_line_width(self):
        path, source = self._read("src/Gui/Selection/SoFCUnifiedSelection.cpp")

        self.assertIn("SoLineWidthElement::set(state, node, 2.0f);", source, path)

    def test_viewer_exposes_document_state_badge_wiring(self):
        header_path, header_source = self._read("src/Gui/View3DInventorViewer.h")
        impl_path, impl_source = self._read("src/Gui/View3DInventorViewer.cpp")

        self.assertIn("void connectDocumentStateSignals();", header_source, header_path)
        self.assertIn("void updateViewportStateBadge();", header_source, header_path)
        self.assertIn("QLabel* viewportStateBadge = nullptr;", header_source, header_path)
        self.assertIn("signalTouchedObject.connect", impl_source, impl_path)
        self.assertIn("signalBeforeRecompute.connect", impl_source, impl_path)
        self.assertIn("signalRecomputed.connect", impl_source, impl_path)
        self.assertIn("signalSkipRecompute.connect", impl_source, impl_path)
        self.assertIn('tr("Recompute Pending")', impl_source, impl_path)
        self.assertIn('tr("Recomputing")', impl_source, impl_path)
        self.assertIn('tr("Skip Recompute")', impl_source, impl_path)


if __name__ == "__main__":
    unittest.main()