# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Static contract checks for the canonical FlowStudio catalog namespace."""

from __future__ import annotations

import os
import unittest


class TestCatalogNamespaceContract(unittest.TestCase):
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

    def test_catalog_database_is_canonical(self):
        path, source = self._read("src/Mod/FlowStudio/flow_studio/catalog/database.py")

        self.assertIn("DEFAULT_DATABASE", source, path)
        self.assertIn("def load_database()", source, path)
        self.assertIn("def material_presets(*categories: str)", source, path)
        self.assertIn("def fan_presets()", source, path)

    def test_catalog_editor_is_canonical(self):
        path, source = self._read("src/Mod/FlowStudio/flow_studio/catalog/editor.py")

        self.assertIn("class EngineeringDatabaseDialog", source, path)
        self.assertIn("from flow_studio.catalog.database import", source, path)
        self.assertIn("def show_engineering_database_editor()", source, path)

    def test_flat_catalog_modules_are_compatibility_wrappers(self):
        database_path, database_source = self._read("src/Mod/FlowStudio/flow_studio/engineering_database.py")
        editor_path, editor_source = self._read("src/Mod/FlowStudio/flow_studio/engineering_database_editor.py")

        self.assertIn("Compatibility wrapper", database_source, database_path)
        self.assertIn("from flow_studio.catalog.database import *", database_source, database_path)
        self.assertIn("Compatibility wrapper", editor_source, editor_path)
        self.assertIn("from flow_studio.catalog.editor import", editor_source, editor_path)


if __name__ == "__main__":
    unittest.main()