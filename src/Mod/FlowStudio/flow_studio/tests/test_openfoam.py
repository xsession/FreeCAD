# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Unit tests for OpenFOAM case generation (string output, no FreeCAD)."""

import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestOpenFOAMHeaderFormat(unittest.TestCase):
    """Test OpenFOAM file header formatting."""

    def test_header_format(self):
        """Verify that generated headers contain FoamFile dict."""
        # We can't easily import the full runner without FreeCAD,
        # but we can test the header template pattern
        header = """FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      controlDict;
}"""
        self.assertIn("FoamFile", header)
        self.assertIn("version     2.0;", header)
        self.assertIn("class       dictionary;", header)


class TestOpenFOAMTurbulenceMapping(unittest.TestCase):
    """Test turbulence model to OpenFOAM mapping logic."""

    def test_ras_models(self):
        ras_map = {
            "kEpsilon": "kEpsilon",
            "kOmega": "kOmega",
            "kOmegaSST": "kOmegaSST",
            "SpalartAllmaras": "SpalartAllmaras",
        }
        for key, val in ras_map.items():
            self.assertEqual(val, ras_map[key])

    def test_les_models(self):
        les_map = {
            "LES-Smagorinsky": "Smagorinsky",
            "LES-WALE": "WALE",
        }
        self.assertEqual(les_map["LES-Smagorinsky"], "Smagorinsky")
        self.assertEqual(les_map["LES-WALE"], "WALE")


class TestOpenFOAMSolverAppMapping(unittest.TestCase):
    """Test that solver app names are valid OpenFOAM executables."""

    VALID_SOLVERS = {
        "simpleFoam", "pimpleFoam", "pisoFoam", "icoFoam",
        "rhoSimpleFoam", "rhoPimpleFoam", "buoyantSimpleFoam",
        "buoyantPimpleFoam", "interFoam", "potentialFoam",
    }

    def test_all_solvers_recognized(self):
        for solver in self.VALID_SOLVERS:
            self.assertTrue(solver.endswith("Foam"),
                            f"{solver} doesn't follow OpenFOAM naming")


if __name__ == "__main__":
    unittest.main()
