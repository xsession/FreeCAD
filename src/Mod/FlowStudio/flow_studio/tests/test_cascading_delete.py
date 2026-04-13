# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Unit tests for analysis cascading delete behaviour."""

import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Add parent directory to path for standalone testing
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Mock FreeCAD and FreeCADGui before importing viewproviders
_fc_mock = MagicMock()
_fc_mock.Console.PrintMessage = MagicMock()
sys.modules.setdefault("FreeCAD", _fc_mock)
sys.modules.setdefault("FreeCADGui", MagicMock())


class TestAnalysisCascadingDelete(unittest.TestCase):
    """Verify that deleting an analysis removes all child objects."""

    def _make_mock_obj(self, name, group=None):
        """Create a mock FreeCAD document object."""
        obj = MagicMock(spec=[])  # empty spec so hasattr is controlled
        obj.Name = name
        obj.Label = name
        if group is not None:
            obj.Group = group
        return obj

    def _make_mock_doc(self):
        """Create a mock Document that tracks removeObject calls."""
        doc = MagicMock()
        doc.removed = []

        def _remove(name):
            doc.removed.append(name)

        doc.removeObject = _remove
        return doc

    def test_delete_analysis_removes_children(self):
        """Deleting an analysis should remove all its children."""
        from flow_studio.viewproviders.vp_analysis import VPCFDAnalysis

        doc = self._make_mock_doc()

        # Create child objects (no sub-groups)
        physics = self._make_mock_obj("PhysicsModel")
        material = self._make_mock_obj("FluidMaterial")
        inlet = self._make_mock_obj("BCInlet")
        solver = self._make_mock_obj("Solver")

        # Create analysis with children
        analysis = self._make_mock_obj(
            "CFDAnalysis", group=[physics, material, inlet, solver]
        )
        analysis.Document = doc

        # Create viewprovider
        vobj = MagicMock()
        vobj.Object = analysis
        vp = VPCFDAnalysis.__new__(VPCFDAnalysis)

        # Execute onDelete
        result = vp.onDelete(vobj, [])

        # Should allow deletion
        self.assertTrue(result)
        # All 4 children should have been removed
        self.assertEqual(len(doc.removed), 4)
        self.assertIn("PhysicsModel", doc.removed)
        self.assertIn("FluidMaterial", doc.removed)
        self.assertIn("BCInlet", doc.removed)
        self.assertIn("Solver", doc.removed)

    def test_delete_analysis_handles_nested_groups(self):
        """Children with sub-groups (e.g. mesh with mesh regions) are handled."""
        from flow_studio.viewproviders.vp_analysis import VPCFDAnalysis

        doc = self._make_mock_doc()

        # Mesh region is a child of the mesh object
        region = self._make_mock_obj("MeshRegion")
        bl = self._make_mock_obj("BoundaryLayer")
        mesh = self._make_mock_obj("MeshGmsh", group=[region, bl])
        mesh.Document = doc

        solver = self._make_mock_obj("Solver")

        analysis = self._make_mock_obj("Analysis", group=[mesh, solver])
        analysis.Document = doc

        vobj = MagicMock()
        vobj.Object = analysis
        vp = VPCFDAnalysis.__new__(VPCFDAnalysis)

        result = vp.onDelete(vobj, [])
        self.assertTrue(result)

        # Sub-children (region, bl) + children (mesh, solver) = 4 removed
        self.assertEqual(len(doc.removed), 4)
        self.assertIn("MeshRegion", doc.removed)
        self.assertIn("BoundaryLayer", doc.removed)
        self.assertIn("MeshGmsh", doc.removed)
        self.assertIn("Solver", doc.removed)

    def test_delete_empty_analysis(self):
        """An analysis with no children should delete cleanly."""
        from flow_studio.viewproviders.vp_analysis import VPCFDAnalysis

        doc = self._make_mock_doc()
        analysis = self._make_mock_obj("EmptyAnalysis", group=[])
        analysis.Document = doc

        vobj = MagicMock()
        vobj.Object = analysis
        vp = VPCFDAnalysis.__new__(VPCFDAnalysis)

        result = vp.onDelete(vobj, [])
        self.assertTrue(result)
        self.assertEqual(len(doc.removed), 0)

    def test_delete_with_none_object(self):
        """If vobj.Object is None, onDelete should still return True."""
        from flow_studio.viewproviders.vp_analysis import VPCFDAnalysis

        vobj = MagicMock()
        vobj.Object = None
        vp = VPCFDAnalysis.__new__(VPCFDAnalysis)

        result = vp.onDelete(vobj, [])
        self.assertTrue(result)

    def test_delete_all_domain_analysis_types(self):
        """Cascading delete works regardless of the physics domain."""
        from flow_studio.viewproviders.vp_analysis import VPCFDAnalysis

        for domain in ("CFD", "Structural", "Electrostatic",
                        "Electromagnetic", "Thermal"):
            doc = self._make_mock_doc()
            child1 = self._make_mock_obj(f"{domain}Physics")
            child2 = self._make_mock_obj(f"{domain}Material")
            analysis = self._make_mock_obj(
                f"{domain}Analysis", group=[child1, child2]
            )
            analysis.Document = doc

            vobj = MagicMock()
            vobj.Object = analysis
            vp = VPCFDAnalysis.__new__(VPCFDAnalysis)

            result = vp.onDelete(vobj, [])
            self.assertTrue(result, f"Failed for domain {domain}")
            self.assertEqual(
                len(doc.removed), 2,
                f"Expected 2 children removed for {domain}, got {doc.removed}"
            )


if __name__ == "__main__":
    unittest.main()
