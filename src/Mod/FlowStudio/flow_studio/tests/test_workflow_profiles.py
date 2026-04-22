# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Static tests for CST-inspired workflow profiles and workspace layouts."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestWorkflowProfiles(unittest.TestCase):
    """Ensure each supported domain exposes profile and workspace metadata."""

    def test_optical_profile_exists(self):
        from flow_studio.workflows.profiles import get_workflow_profile

        profile = get_workflow_profile("Optical")
        self.assertEqual(profile.label, "Optical / Photonics")
        self.assertEqual(len(profile.steps), 9)
        self.assertEqual(profile.steps[4].name, "Define Sources, Detectors, and Boundaries")
        self.assertIn("Radiation transport", profile.workflows)

    def test_cfd_layout_exists(self):
        from flow_studio.ui.layouts import get_workspace_layout

        layout = get_workspace_layout("CFD")
        self.assertIn("Project Tree", layout.left_panes)
        self.assertIn("Results", layout.bottom_panes)

    def test_default_profile_falls_back_to_cfd(self):
        from flow_studio.workflows.profiles import get_workflow_profile

        self.assertEqual(get_workflow_profile(None).domain_key, "CFD")
        self.assertEqual(get_workflow_profile("Unknown").domain_key, "CFD")


class TestOpticalPresetCatalog(unittest.TestCase):
    """Validate the richer optical preset catalog used by the optics workflow."""

    def test_bk7_has_dispersion_coefficients(self):
        from flow_studio.catalog.optics import get_optical_material_preset

        bk7 = get_optical_material_preset("BK7")
        self.assertGreater(bk7["SellmeierB1"], 1.0)
        self.assertGreater(bk7["WavelengthMax"], bk7["WavelengthMin"])
        self.assertEqual(bk7["DispersionModel"], "Sellmeier")

    def test_custom_entry_not_in_catalog(self):
        from flow_studio.catalog.optics import OPTICAL_MATERIAL_PRESETS, get_optical_material_preset_names

        self.assertNotIn("Custom", OPTICAL_MATERIAL_PRESETS)
        self.assertEqual(get_optical_material_preset_names()[0], "Custom")


if __name__ == "__main__":
    unittest.main()