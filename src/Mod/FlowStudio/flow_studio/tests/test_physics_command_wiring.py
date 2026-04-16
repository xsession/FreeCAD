# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Regression tests for electrostatic/electromagnetic BC command wiring.

These tests are intentionally static (AST/source checks) to avoid requiring
FreeCAD GUI runtime while still catching accidental command/factory removals.
"""

import ast
import os
import unittest


class TestPhysicsBCWiring(unittest.TestCase):
    """Validate BC factories, command classes, and workbench command lists."""

    @classmethod
    def setUpClass(cls):
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        pkg_dir = os.path.join(root_dir, "flow_studio")

        cls.objects_path = os.path.join(pkg_dir, "ObjectsFlowStudio.py")
        cls.commands_path = os.path.join(pkg_dir, "commands.py")
        cls.initgui_path = os.path.join(root_dir, "InitGui.py")

        with open(cls.objects_path, "r", encoding="utf-8") as f:
            cls.objects_src = f.read()
        with open(cls.commands_path, "r", encoding="utf-8") as f:
            cls.commands_src = f.read()
        with open(cls.initgui_path, "r", encoding="utf-8") as f:
            cls.initgui_src = f.read()

        cls.objects_ast = ast.parse(cls.objects_src)
        cls.commands_ast = ast.parse(cls.commands_src)
        cls.initgui_ast = ast.parse(cls.initgui_src)

    def test_objects_factory_functions_exist(self):
        fn_names = {
            node.name
            for node in self.objects_ast.body
            if isinstance(node, ast.FunctionDef)
        }
        required = {
            "makeBCElectricFlux",
            "makeBCMagneticFluxDensity",
            "makeBCFarFieldEM",
        }
        self.assertTrue(required.issubset(fn_names),
                        f"Missing BC factories: {required - fn_names}")

    def test_command_classes_exist(self):
        class_names = {
            node.name
            for node in self.commands_ast.body
            if isinstance(node, ast.ClassDef)
        }
        required = {
            "_CmdBCElectricFlux",
            "_CmdBCMagneticFluxDensity",
            "_CmdBCFarFieldEM",
        }
        self.assertTrue(required.issubset(class_names),
                        f"Missing BC command classes: {required - class_names}")

    def test_addcommand_registrations_exist(self):
        self.assertIn('FlowStudio_BC_ElectricFlux', self.commands_src)
        self.assertIn('FlowStudio_BC_MagneticFluxDensity', self.commands_src)
        self.assertIn('FlowStudio_BC_FarFieldEM', self.commands_src)

    def test_physics_commands_have_registrations(self):
        registered = set()
        for node in ast.walk(self.commands_ast):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not isinstance(func, ast.Attribute):
                continue
            if func.attr != "addCommand":
                continue
            if not node.args:
                continue
            arg0 = node.args[0]
            if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
                registered.add(arg0.value)

        physics_entries = self._physics_commands_entries()
        missing = [
            cmd for cmd in physics_entries
            if cmd != "Separator" and cmd not in registered
        ]
        self.assertEqual(missing, [],
                         f"PHYSICS_COMMANDS entries missing addCommand: {missing}")

    def test_new_icons_exist(self):
        icons_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "Resources",
            "icons",
        )
        required = [
            "FlowStudioElectricFlux.svg",
            "FlowStudioMagneticFluxDensity.svg",
            "FlowStudioFarFieldEM.svg",
        ]
        missing = [name for name in required if not os.path.isfile(os.path.join(icons_dir, name))]
        self.assertEqual(missing, [], f"Missing icon files: {missing}")

    def test_physics_commands_contains_new_entries(self):
        physics_entries = self._physics_commands_entries()
        required = {
            "FlowStudio_BC_ElectricFlux",
            "FlowStudio_BC_MagneticFluxDensity",
            "FlowStudio_BC_FarFieldEM",
        }
        self.assertTrue(required.issubset(set(physics_entries)),
                        f"Missing PHYSICS_COMMANDS entries: {required - set(physics_entries)}")

    def _physics_commands_entries(self):
        physics_entries = []
        for node in self.initgui_ast.body:
            if not isinstance(node, ast.ClassDef):
                continue
            if node.name != "FlowStudioWorkbench":
                continue
            for stmt in node.body:
                if not isinstance(stmt, ast.Assign):
                    continue
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and target.id == "PHYSICS_COMMANDS":
                        if isinstance(stmt.value, ast.List):
                            for elt in stmt.value.elts:
                                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                    physics_entries.append(elt.value)
        return physics_entries


if __name__ == "__main__":
    unittest.main()
