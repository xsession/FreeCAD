"""Static regression checks for GUI STEP import large-assembly optimizations."""

from __future__ import annotations

import pathlib
import unittest


class TestStepImportGuiPerfContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_path = pathlib.Path(__file__).resolve().parents[1] / "src" / "Mod" / "Import" / "Gui" / "AppImportGuiPy.cpp"
        cls.source = cls.source_path.read_text(encoding="utf-8")

    def test_gui_import_has_step_perf_profile(self):
        self.assertIn("struct StepImportPerfProfile", self.source)
        self.assertIn("getStepImportPerfProfile(const Base::FileInfo& file)", self.source)
        self.assertIn("profile.speedMode = isMedium;", self.source)

    def test_gui_import_batches_tessellation(self):
        self.assertIn("batchTessellateImportedShapes(file, perfProfile, importedObjs);", self.source)
        self.assertIn("ImportGui: Pre-tessellating %zu shapes before GUI refresh", self.source)
        self.assertIn("tracker.checkpoint(\"Batch tessellation\")", self.source)

    def test_gui_import_switches_flat_lines_to_shaded(self):
        self.assertIn("bool switchFlatLinesToShaded", self.source)
        self.assertIn('viewProvider->DisplayMode.setValue("Shaded");', self.source)
        self.assertIn("ImportGui: Switched %zu imported objects from Flat Lines to Shaded", self.source)


if __name__ == "__main__":
    unittest.main()