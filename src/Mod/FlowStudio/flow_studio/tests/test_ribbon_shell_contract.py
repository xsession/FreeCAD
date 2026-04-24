# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Static regression tests for the shared ribbon shell contract.

These checks intentionally inspect source files instead of importing FreeCAD GUI
runtime so they can run in headless CI while still catching regressions in the
cross-workbench ribbon metadata and contextual panel registry.
"""

from __future__ import annotations

import os
import unittest


class TestRibbonShellContract(unittest.TestCase):
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

    def test_ribbon_metadata_helper_exposes_registry_helpers(self):
        path, source = self._read("src/Gui/RibbonMetadata.py")

        self.assertIn("def build_ribbon_toolbar_name(", source, path)
        self.assertIn("home_priority=None", source, path)
        self.assertIn('parts.append("HomePrimary")', source, path)
        self.assertIn('parts.append("HomeSecondary")', source, path)
        self.assertIn("def build_contextual_ribbon_toolbar_name(", source, path)
        self.assertIn("def register_contextual_ribbon_panel(", source, path)
        self.assertIn("def unregister_contextual_ribbon_panel(", source, path)
        self.assertIn("FreeCADGui.registerContextualRibbonPanel", source, path)
        self.assertIn("FreeCADGui.unregisterContextualRibbonPanel", source, path)

    def test_application_py_exposes_contextual_registry(self):
        header_path, header_source = self._read("src/Gui/ApplicationPy.h")
        impl_path, impl_source = self._read("src/Gui/ApplicationPy.cpp")

        self.assertIn("sRegisterContextualRibbonPanel", header_source, header_path)
        self.assertIn("sUnregisterContextualRibbonPanel", header_source, header_path)
        self.assertIn('"registerContextualRibbonPanel"', impl_source, impl_path)
        self.assertIn('"unregisterContextualRibbonPanel"', impl_source, impl_path)
        self.assertIn("RibbonBar::registerContextualRibbonPanel", impl_source, impl_path)
        self.assertIn("RibbonBar::unregisterContextualRibbonPanel", impl_source, impl_path)

    def test_flowstudio_uses_contextual_registry(self):
        path, source = self._read("src/Mod/FlowStudio/InitGui.py")

        self.assertIn("register_contextual_ribbon_panel", source, path)
        self.assertEqual(source.count("register_contextual_ribbon_panel("), 7)
        self.assertIn("build_contextual_ribbon_toolbar_name(", source, path)
        self.assertIn('"Setup", "Analysis", "Home"', source, path)
        self.assertIn('"Setup", "Setup", "Home"', source, path)
        self.assertIn('"Solve", "Solve", "Home"', source, path)
        self.assertIn('build_ribbon_toolbar_name("Results", "Post-Processing"', source, path)
        self.assertIn('build_ribbon_toolbar_name("Inspect", "Geometry"', source, path)
        self.assertIn('"Electrostatic Setup"', source, path)
        self.assertIn('"Electromagnetic Setup"', source, path)
        self.assertIn('"Optical & Geant4"', source, path)
        self.assertIn("self.ELECTROSTATIC_COMMANDS", source, path)
        self.assertIn("self.ELECTROMAGNETIC_COMMANDS", source, path)
        self.assertIn("self.OPTICAL_COMMANDS", source, path)
        self.assertIn('"Simulation"', source, path)
        self.assertIn('home_priority="primary"', source, path)
        self.assertIn('home_priority="secondary"', source, path)
        self.assertNotIn("self.appendToolbar(\n                build_contextual_ribbon_toolbar_name(", source)

    def test_assembly_uses_contextual_registry(self):
        path, source = self._read("src/Mod/Assembly/InitGui.py")

        self.assertIn("register_contextual_ribbon_panel", source, path)
        self.assertEqual(source.count("register_contextual_ribbon_panel("), 4)
        self.assertIn('"Joint Presets"', source, path)
        self.assertIn("build_contextual_ribbon_toolbar_name(", source, path)

    def test_cam_keeps_stable_ribbon_metadata_contract(self):
        path, source = self._read("src/Mod/CAM/InitGui.py")

        self.assertIn("from RibbonMetadata import build_ribbon_toolbar_name", source, path)
        self.assertIn("build_ribbon_toolbar_name(", source, path)
        self.assertIn('"Job Setup"', source, path)
        self.assertIn('"Operations"', source, path)

    def test_sketcher_registers_context_from_workbench(self):
        path, source = self._read("src/Mod/Sketcher/Gui/Workbench.cpp")

        self.assertIn("#include <Gui/RibbonBar.h>", source, path)
        self.assertIn("registerSketchContextualPanel", source, path)
        self.assertIn("RibbonBar::registerContextualRibbonPanel", source, path)
        for panel_name in ["Sketch", "Geometry", "Constraints", "Tools", "B-Spline", "Visual"]:
            self.assertIn(f'QStringLiteral("{panel_name}")', source, path)

    def test_ribbon_bar_no_longer_contains_sketch_special_case(self):
        path, source = self._read("src/Gui/RibbonBar.cpp")

        self.assertIn("g_registeredContextualRibbonPanels", source, path)
        self.assertIn("registeredContextualPanels", source, path)
        self.assertIn("HomePrimary", source, path)
        self.assertIn("HomeSecondary", source, path)
        self.assertIn("toolbarHomePriorityForMetadata", source, path)
        self.assertIn("adaptiveHomePriorityForToolbar", source, path)
        self.assertIn("adaptiveHomePriorityForContextPanel", source, path)
        self.assertIn("homePage->clearPanels()", source, path)
        self.assertIn("selectionContainsObjectType", source, path)
        self.assertIn('QStringLiteral("Sketcher::SketchObject")', source, path)
        self.assertIn('tr("Most common actions for the active workflow context")', source, path)
        self.assertIn('QStringLiteral("PartDesignWorkbench")', source, path)
        self.assertIn('QStringLiteral("SketcherWorkbench")', source, path)
        self.assertIn('QStringLiteral("AssemblyWorkbench")', source, path)
        self.assertIn('QStringLiteral("FlowStudioWorkbench")', source, path)
        self.assertIn('QStringLiteral("TechDrawWorkbench")', source, path)
        self.assertIn('QStringLiteral("Simulation")', source, path)
        self.assertIn('tabName == QObject::tr("Setup")', source, path)
        self.assertIn('tabName == QObject::tr("Solve")', source, path)
        self.assertNotIn("populateSketchContextualTab", source, path)
        self.assertNotIn("shouldShowSketchContext", source, path)
        self.assertNotIn("Sketcher_NewSketch", source, path)

    def test_workbench_selector_exposes_searchable_overflow(self):
        path, source = self._read("src/Gui/WorkbenchSelector.cpp")

        self.assertIn("QLineEdit", source, path)
        self.assertIn("QWidgetAction", source, path)
        self.assertIn('setPlaceholderText(QObject::tr("Find workbench"))', source, path)
        self.assertIn("applyWorkbenchMenuFilter", source, path)
        self.assertIn('action->property("workbenchPurpose")', source, path)
        self.assertIn("buildWorkbenchOverflowMenu", source, path)
        self.assertIn("WorkbenchComboWidget::WorkbenchComboWidget", source, path)
        self.assertIn('QObject::tr("Pinned Workbenches (Primary Tabs)")', source, path)
        self.assertIn('QObject::tr("Pinned workbenches stay visible for one-click switching.")', source, path)
        self.assertIn('QObject::tr(" (Pinned)")', source, path)
        self.assertIn('QObject::tr("Pinned workbench: stays visible as a primary switching mode.")', source, path)

    def test_workbench_selector_groups_overflow_by_category(self):
        path, source = self._read("src/Gui/WorkbenchSelector.cpp")

        self.assertIn("createWorkbenchOverflowAction", source, path)
        self.assertIn("addWorkbenchCategorySection", source, path)
        self.assertIn('action->setProperty("workbenchCategory"', source, path)
        self.assertIn('QObject::tr("Getting Started")', source, path)
        self.assertIn('QObject::tr("Modeling")', source, path)
        self.assertIn('QObject::tr("Assembly")', source, path)
        self.assertIn('QObject::tr("Simulation")', source, path)
        self.assertIn('QObject::tr("Documentation")', source, path)
        self.assertIn('QObject::tr("Manufacturing")', source, path)
        self.assertIn('QObject::tr("Data and Utility")', source, path)

    def test_action_cpp_enriches_workbench_tooltips_with_purpose(self):
        path, source = self._read("src/Gui/Action.cpp")

        self.assertIn("QString workbenchPurpose(", source, path)
        self.assertIn("composeWorkbenchToolTip", source, path)
        self.assertIn('action->setProperty("workbenchPurpose"', source, path)
        self.assertIn("QString workbenchCategory(", source, path)
        self.assertIn('action->setProperty("workbenchCategory"', source, path)
        self.assertIn('QStringLiteral("AssemblyWorkbench")', source, path)
        self.assertIn('QStringLiteral("FlowStudioWorkbench")', source, path)

    def test_task_dialog_python_forwards_validation_metadata(self):
        path, source = self._read("src/Gui/TaskView/TaskDialogPython.cpp")

        self.assertIn('"taskview_context_mode"', source, path)
        self.assertIn('"taskview_context_title"', source, path)
        self.assertIn('"taskview_context_detail"', source, path)
        self.assertIn('"taskview_validation_level"', source, path)
        self.assertIn('"taskview_validation_title"', source, path)
        self.assertIn('"taskview_validation_detail"', source, path)
        self.assertIn("forwardedProperties", source, path)

    def test_task_dialog_python_mirrors_dynamic_property_updates(self):
        path, source = self._read("src/Gui/TaskView/TaskDialogPython.cpp")

        self.assertIn("QDynamicPropertyChangeEvent", source, path)
        self.assertIn("QEvent::DynamicPropertyChange", source, path)
        self.assertIn("isTaskViewMetadataProperty", source, path)
        self.assertIn("watched->property(propertyName.constData())", source, path)

    def test_base_task_panel_publishes_live_taskview_metadata(self):
        path, source = self._read("src/Mod/FlowStudio/flow_studio/taskpanels/base_taskpanel.py")

        self.assertIn("self._refresh_taskview_metadata()", source, path)
        self.assertIn("self._connect_taskview_metadata_signals()", source, path)
        self.assertIn('self._publish_taskview_property("taskview_context_mode", mode)', source, path)
        self.assertIn('self._publish_taskview_property("taskview_context_title", title)', source, path)
        self.assertIn('self._publish_taskview_property("taskview_context_detail", detail)', source, path)
        self.assertIn('self._publish_taskview_property("taskview_validation_level", level)', source, path)
        self.assertIn("def _publish_taskview_property", source, path)
        self.assertIn("def _apply_task_context", source, path)
        self.assertIn("def _build_task_context", source, path)
        self.assertIn("def _connect_widget_metadata_signal", source, path)

    def test_task_view_reads_context_metadata(self):
        path, source = self._read("src/Gui/TaskView/TaskView.cpp")

        self.assertIn('dlg->property("taskview_context_mode")', source, path)
        self.assertIn('dlg->property("taskview_context_title")', source, path)
        self.assertIn('dlg->property("taskview_context_detail")', source, path)
        self.assertIn("outInfo.taskPanel->setContext", source, path)
        self.assertIn('contextMode = tr("Edit")', source, path)


if __name__ == "__main__":
    unittest.main()