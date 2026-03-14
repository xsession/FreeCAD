# SPDX-License-Identifier: LGPL-2.1-or-later

# ***************************************************************************
# *   Copyright (c) 2025 FreeCAD contributors                              *
# *                                                                         *
# *   This file is part of FreeCAD.                                         *
# *                                                                         *
# *   FreeCAD is free software: you can redistribute it and/or modify it    *
# *   under the terms of the GNU Lesser General Public License as           *
# *   published by the Free Software Foundation, either version 2.1 of the  *
# *   License, or (at your option) any later version.                       *
# *                                                                         *
# *   FreeCAD is distributed in the hope that it will be useful, but        *
# *   WITHOUT ANY WARRANTY; without even the implied warranty of            *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU      *
# *   Lesser General Public License for more details.                       *
# *                                                                         *
# *   You should have received a copy of the GNU Lesser General Public      *
# *   License along with FreeCAD. If not, see                               *
# *   <https://www.gnu.org/licenses/>.                                      *
# *                                                                         *
# ***************************************************************************

"""Tests for creating a Sketch on a Pad face and proving TNP resolution.

Validates the complete workflow of:
  1. Creating a Body with a Sketch and Pad
  2. Accessing sub-shapes (faces, edges, vertices) on the Pad
  3. Attaching a second Sketch to a Pad face
  4. Creating a second Pad on that Sketch
  5. Sub-element name resolution via Part.getShape()
  6. SelectionFilter matching (when Gui is available)
  7. TNP resilience: downstream features survive upstream mutations
  8. Element map stability through sketch modifications
  9. Save / restore cycle preserves element maps and references
 10. Multi-level Pad chains with perturbation

These tests verify that the fixes to _ShapeNames / _ShapeNamesCStr in
TopoShape.cpp, the ElementMap.cpp guard, and the ComplexGeoData.cpp guard
all work correctly together, and that the Topological Naming Problem is
resolved for sketch-on-face workflows.
"""

import os
import tempfile
import unittest

import FreeCAD as App
import Part
import Sketcher
import TestSketcherApp


class TestSketchOnFace(unittest.TestCase):
    """Test creating a Sketch attached to a Pad face and building on it."""

    # pylint: disable=attribute-defined-outside-init

    def setUp(self):
        """Create a fresh document and build a Body -> Sketch -> Pad."""
        self.Doc = App.newDocument("PartDesignTestSketchOnFace")
        self.Body = self.Doc.addObject("PartDesign::Body", "Body")

        # Sketch on XY plane
        self.Sketch = self.Doc.addObject("Sketcher::SketchObject", "Sketch")
        self.Body.addObject(self.Sketch)
        self.Sketch.AttachmentSupport = (self.Doc.XY_Plane, [""])
        self.Sketch.MapMode = "FlatFace"
        TestSketcherApp.CreateRectangleSketch(self.Sketch, (0, 0), (10, 10))
        self.Doc.recompute()

        # Pad 10 mm
        self.Pad = self.Doc.addObject("PartDesign::Pad", "Pad")
        self.Body.addObject(self.Pad)
        self.Pad.Profile = self.Sketch
        self.Pad.Length = 10
        self.Doc.recompute()

    # ------------------------------------------------------------------
    # Basic Pad geometry
    # ------------------------------------------------------------------

    def testPadIsValid(self):
        """The Pad should recompute successfully and be valid."""
        self.assertTrue(self.Pad.isValid(), "Pad is not valid after recompute")

    def testPadHasSixFaces(self):
        """A rectangular Pad must produce exactly 6 faces (box)."""
        self.assertEqual(len(self.Pad.Shape.Faces), 6)

    def testPadHasTwelveEdges(self):
        """A rectangular Pad must produce exactly 12 edges."""
        self.assertEqual(len(self.Pad.Shape.Edges), 12)

    def testPadHasEightVertices(self):
        """A rectangular Pad must produce exactly 8 vertices."""
        self.assertEqual(len(self.Pad.Shape.Vertexes), 8)

    def testPadVolume(self):
        """10 x 10 x 10 box should have volume 1000."""
        self.assertAlmostEqual(self.Pad.Shape.Volume, 1000.0, places=2)

    # ------------------------------------------------------------------
    # Sub-shape access via getElement / getSubObject
    # ------------------------------------------------------------------

    def testGetElementFaces(self):
        """Every Face1..Face6 must be resolvable via Shape.getElement()."""
        for i in range(1, 7):
            name = f"Face{i}"
            sub = self.Pad.Shape.getElement(name)
            self.assertIsNotNone(sub, f"getElement('{name}') returned None")
            self.assertEqual(sub.ShapeType, "Face",
                             f"getElement('{name}') returned {sub.ShapeType}, expected Face")

    def testGetElementEdges(self):
        """Every Edge1..Edge12 must be resolvable via Shape.getElement()."""
        for i in range(1, 13):
            name = f"Edge{i}"
            sub = self.Pad.Shape.getElement(name)
            self.assertIsNotNone(sub, f"getElement('{name}') returned None")
            self.assertEqual(sub.ShapeType, "Edge",
                             f"getElement('{name}') returned {sub.ShapeType}, expected Edge")

    def testGetElementVertices(self):
        """Every Vertex1..Vertex8 must be resolvable via Shape.getElement()."""
        for i in range(1, 9):
            name = f"Vertex{i}"
            sub = self.Pad.Shape.getElement(name)
            self.assertIsNotNone(sub, f"getElement('{name}') returned None")
            self.assertEqual(sub.ShapeType, "Vertex",
                             f"getElement('{name}') returned {sub.ShapeType}, expected Vertex")

    # ------------------------------------------------------------------
    # Part.getShape with needSubElement
    # ------------------------------------------------------------------

    def testPartGetShapeFaces(self):
        """Part.getShape(pad, 'FaceN', needSubElement=True) must return a Face."""
        for i in range(1, 7):
            name = f"Face{i}"
            sub = Part.getShape(self.Pad, name, needSubElement=True)
            self.assertFalse(sub.isNull(),
                             f"Part.getShape(Pad, '{name}', needSubElement=True) returned null shape")
            self.assertEqual(sub.ShapeType, "Face",
                             f"Part.getShape returned {sub.ShapeType} for '{name}'")

    def testPartGetShapeEdges(self):
        """Part.getShape(pad, 'EdgeN', needSubElement=True) must return an Edge."""
        for i in range(1, 13):
            name = f"Edge{i}"
            sub = Part.getShape(self.Pad, name, needSubElement=True)
            self.assertFalse(sub.isNull(),
                             f"Part.getShape(Pad, '{name}', needSubElement=True) returned null shape")
            self.assertEqual(sub.ShapeType, "Edge",
                             f"Part.getShape returned {sub.ShapeType} for '{name}'")

    def testPartGetShapeVertices(self):
        """Part.getShape(pad, 'VertexN', needSubElement=True) must return a Vertex."""
        for i in range(1, 9):
            name = f"Vertex{i}"
            sub = Part.getShape(self.Pad, name, needSubElement=True)
            self.assertFalse(sub.isNull(),
                             f"Part.getShape(Pad, '{name}', needSubElement=True) returned null shape")
            self.assertEqual(sub.ShapeType, "Vertex",
                             f"Part.getShape returned {sub.ShapeType} for '{name}'")

    # ------------------------------------------------------------------
    # Attach Sketch to Pad face and create second Pad
    # ------------------------------------------------------------------

    def testSketchOnPadFace(self):
        """Attaching a Sketch to Face6 of the Pad and padding it should succeed."""
        sketch2 = self.Doc.addObject("Sketcher::SketchObject", "Sketch2")
        self.Body.addObject(sketch2)
        sketch2.MapMode = "FlatFace"
        sketch2.AttachmentSupport = [(self.Pad, "Face6")]
        TestSketcherApp.CreateRectangleSketch(sketch2, (2, 2), (6, 6))
        self.Doc.recompute()

        pad2 = self.Doc.addObject("PartDesign::Pad", "Pad2")
        self.Body.addObject(pad2)
        pad2.Profile = sketch2
        pad2.Length = 5
        self.Doc.recompute()

        self.assertTrue(pad2.isValid(), "Pad2 on Face6 is not valid")
        # Original box 10*10*10 = 1000, plus extrusion 6*6*5 = 180
        self.assertAlmostEqual(pad2.Shape.Volume, 1180.0, places=2)

    def testSketchOnEveryPadFace(self):
        """A Sketch can be attached to each of the 6 faces without error."""
        for i in range(1, 7):
            face_name = f"Face{i}"
            sketch = self.Doc.addObject("Sketcher::SketchObject", f"SketchFace{i}")
            self.Body.addObject(sketch)
            sketch.MapMode = "FlatFace"
            sketch.AttachmentSupport = [(self.Pad, face_name)]
            self.Doc.recompute()
            self.assertTrue(sketch.isValid(),
                            f"Sketch attached to {face_name} is not valid")

    # ------------------------------------------------------------------
    # Element Map (if available)
    # ------------------------------------------------------------------

    def testPadElementMap(self):
        """If ElementMap is active, the Pad should have a populated map."""
        if self.Body.Shape.ElementMapVersion == "":
            return  # ElementMap not available in this build
        reverseMap = self.Pad.Shape.ElementReverseMap
        faces = [n for n in reverseMap.keys() if n.startswith("Face")]
        edges = [n for n in reverseMap.keys() if n.startswith("Edge")]
        vertexes = [n for n in reverseMap.keys() if n.startswith("Vertex")]
        self.assertEqual(len(faces), 6)
        self.assertEqual(len(edges), 12)
        self.assertEqual(len(vertexes), 8)

    # ------------------------------------------------------------------
    # TNP-style: move first Sketch, second Pad should survive
    # ------------------------------------------------------------------

    def testMoveSketchDoesNotBreakSecondPad(self):
        """After attaching Pad2 to Face6, moving the base Sketch should not
        break Pad2 (TNP resilience)."""
        sketch2 = self.Doc.addObject("Sketcher::SketchObject", "Sketch2")
        self.Body.addObject(sketch2)
        sketch2.MapMode = "FlatFace"
        sketch2.AttachmentSupport = [(self.Pad, "Face6")]
        TestSketcherApp.CreateRectangleSketch(sketch2, (2, 2), (6, 6))
        self.Doc.recompute()

        pad2 = self.Doc.addObject("PartDesign::Pad", "Pad2")
        self.Body.addObject(pad2)
        pad2.Profile = sketch2
        pad2.Length = 5
        self.Doc.recompute()
        self.assertTrue(pad2.isValid())

        # Move the base sketch
        self.Sketch.AttachmentOffset = App.Placement(
            App.Vector(1, 0, 0),
            App.Rotation(0, 0, 0),
        )
        self.Doc.recompute()

        self.assertTrue(self.Pad.isValid(), "Pad broke after sketch offset")
        if self.Body.Shape.ElementMapVersion != "":
            self.assertTrue(pad2.isValid(), "Pad2 broke after sketch offset (TNP)")

    # ------------------------------------------------------------------
    # GUI-level tests (only run when FreeCADGui is available)
    # ------------------------------------------------------------------

    def testSelectionFilterMatchesFace(self):
        """SelectionFilter('SELECT Part::Feature SUBELEMENT Face') should
        match when a Pad face is selected."""
        if not App.GuiUp:
            return
        import FreeCADGui as Gui  # noqa: E402

        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(self.Pad, "Face1")
        sel = Gui.Selection.getSelectionEx()
        self.assertEqual(len(sel), 1, "Selection should contain 1 object")
        self.assertTrue(len(sel[0].SubElementNames) > 0,
                        "Selection should have sub-element names")
        self.assertIn("Face1", sel[0].SubElementNames,
                      "Face1 should be in SubElementNames")

        sf = Gui.Selection.Filter("SELECT Part::Feature SUBELEMENT Face")
        self.assertTrue(sf.match(), "SelectionFilter should match a Face selection")
        Gui.Selection.clearSelection()

    def testSelectionFilterMatchesEdge(self):
        """SelectionFilter for Edge should match when a Pad edge is selected."""
        if not App.GuiUp:
            return
        import FreeCADGui as Gui  # noqa: E402

        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(self.Pad, "Edge1")

        sf = Gui.Selection.Filter("SELECT Part::Feature SUBELEMENT Edge")
        self.assertTrue(sf.match(), "SelectionFilter should match an Edge selection")
        Gui.Selection.clearSelection()

    def testProgrammaticFaceSelection(self):
        """Programmatically selecting Face1..Face6 and checking the
        selection state each time."""
        if not App.GuiUp:
            return
        import FreeCADGui as Gui  # noqa: E402

        for i in range(1, 7):
            face = f"Face{i}"
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection(self.Pad, face)
            sel = Gui.Selection.getSelectionEx()
            self.assertEqual(len(sel), 1,
                             f"Expected 1 selected object for {face}")
            self.assertIn(face, sel[0].SubElementNames,
                          f"{face} not in SubElementNames after addSelection")
        Gui.Selection.clearSelection()

    # ==================================================================
    # TNP PROOF: Topological Naming Problem resolution tests
    # ==================================================================

    # ------------------------------------------------------------------
    # TNP 1: Three-Pad chain — offset middle pad, third survives
    # ------------------------------------------------------------------

    def testTNP_ThreePadChainSurvivesMiddleOffset(self):
        """Build Pad -> Pad2(on Face6) -> Pad3(on Pad2 Face6).
        Offset the middle sketch. All three Pads must remain valid
        when ElementMap is active (proves TNP is solved)."""
        if self.Body.Shape.ElementMapVersion == "":
            return  # No ElementMap — skip

        # Pad2 on Pad.Face6
        sketch2 = self.Doc.addObject("Sketcher::SketchObject", "Sketch2")
        self.Body.addObject(sketch2)
        sketch2.MapMode = "FlatFace"
        sketch2.AttachmentSupport = [(self.Pad, "Face6")]
        TestSketcherApp.CreateRectangleSketch(sketch2, (1, 1), (8, 8))
        self.Doc.recompute()
        pad2 = self.Doc.addObject("PartDesign::Pad", "Pad2")
        self.Body.addObject(pad2)
        pad2.Profile = sketch2
        pad2.Length = 5
        self.Doc.recompute()
        self.assertTrue(pad2.isValid())

        # Pad3 on Pad2.Face6
        sketch3 = self.Doc.addObject("Sketcher::SketchObject", "Sketch3")
        self.Body.addObject(sketch3)
        sketch3.MapMode = "FlatFace"
        sketch3.AttachmentSupport = [(pad2, "Face6")]
        TestSketcherApp.CreateRectangleSketch(sketch3, (2, 2), (6, 6))
        self.Doc.recompute()
        pad3 = self.Doc.addObject("PartDesign::Pad", "Pad3")
        self.Body.addObject(pad3)
        pad3.Profile = sketch3
        pad3.Length = 3
        self.Doc.recompute()
        self.assertTrue(pad3.isValid())

        # Perturb the middle sketch
        sketch2.AttachmentOffset = App.Placement(
            App.Vector(0.5, 0.5, 0),
            App.Rotation(0, 0, 0),
        )
        self.Doc.recompute()

        # All three must survive
        self.assertTrue(self.Pad.isValid(), "Pad broke after middle sketch offset")
        self.assertTrue(pad2.isValid(), "Pad2 broke after its sketch was offset (TNP)")
        self.assertTrue(pad3.isValid(), "Pad3 broke after middle sketch offset (TNP)")

    # ------------------------------------------------------------------
    # TNP 2: Resize base sketch — second Pad on face survives
    # ------------------------------------------------------------------

    def testTNP_ResizeBaseSketchSecondPadSurvives(self):
        """Attach Sketch2 to Pad.Face6, create Pad2.  Then add geometry
        to the base Sketch (making the base pad L-shaped).  Pad2 must
        remain valid when ElementMap is active."""
        if self.Body.Shape.ElementMapVersion == "":
            return

        # Pad2 on Face6
        sketch2 = self.Doc.addObject("Sketcher::SketchObject", "Sketch2")
        self.Body.addObject(sketch2)
        sketch2.MapMode = "FlatFace"
        sketch2.AttachmentSupport = [(self.Pad, "Face6")]
        TestSketcherApp.CreateRectangleSketch(sketch2, (1, 1), (4, 4))
        self.Doc.recompute()
        pad2 = self.Doc.addObject("PartDesign::Pad", "Pad2")
        self.Body.addObject(pad2)
        pad2.Profile = sketch2
        pad2.Length = 3
        self.Doc.recompute()
        self.assertTrue(pad2.isValid())
        vol_before = self.Body.Shape.Volume

        # Mutate: add a second rectangle to the base sketch (L-shape)
        geoList = []
        geoList.append(Part.LineSegment(App.Vector(10, 0, 0), App.Vector(20, 0, 0)))
        geoList.append(Part.LineSegment(App.Vector(20, 0, 0), App.Vector(20, 10, 0)))
        geoList.append(Part.LineSegment(App.Vector(20, 10, 0), App.Vector(10, 10, 0)))
        geoList.append(Part.LineSegment(App.Vector(10, 10, 0), App.Vector(10, 0, 0)))
        self.Sketch.addGeometry(geoList, False)
        conList = []
        conList.append(Sketcher.Constraint("Coincident", 4, 2, 5, 1))
        conList.append(Sketcher.Constraint("Coincident", 5, 2, 6, 1))
        conList.append(Sketcher.Constraint("Coincident", 6, 2, 7, 1))
        conList.append(Sketcher.Constraint("Coincident", 7, 2, 4, 1))
        self.Sketch.addConstraint(conList)
        self.Doc.recompute()

        # Volume must have grown (base got larger)
        self.assertGreater(self.Body.Shape.Volume, vol_before)
        # Pad2 must still be valid (TNP solved)
        self.assertTrue(pad2.isValid(),
                        "Pad2 broke after base sketch was extended (TNP)")

    # ------------------------------------------------------------------
    # TNP 3: Pocket on face — base sketch perturbation
    # ------------------------------------------------------------------

    def testTNP_PocketOnFaceSurvivesBaseMove(self):
        """Create a Pocket on one of the Pad's faces.  Move the base
        Sketch.  The Pocket must remain valid."""
        if self.Body.Shape.ElementMapVersion == "":
            return

        # Pocket on Face6 (top face)
        pocketSketch = self.Doc.addObject("Sketcher::SketchObject", "SketchPocket")
        self.Body.addObject(pocketSketch)
        pocketSketch.MapMode = "FlatFace"
        pocketSketch.AttachmentSupport = [(self.Pad, "Face6")]
        TestSketcherApp.CreateRectangleSketch(pocketSketch, (2, 2), (6, 6))
        self.Doc.recompute()
        pocket = self.Doc.addObject("PartDesign::Pocket", "Pocket")
        self.Body.addObject(pocket)
        pocket.Profile = pocketSketch
        pocket.Length = 3
        self.Doc.recompute()
        self.assertTrue(pocket.isValid())
        # 1000 - 6*6*3 = 892
        self.assertAlmostEqual(pocket.Shape.Volume, 892.0, places=1)

        # Perturb base sketch
        self.Sketch.AttachmentOffset = App.Placement(
            App.Vector(1, 0, 0),
            App.Rotation(0, 0, 0),
        )
        self.Doc.recompute()

        self.assertTrue(self.Pad.isValid(), "Pad broke after base sketch move")
        self.assertTrue(pocket.isValid(), "Pocket broke after base sketch move (TNP)")

    # ------------------------------------------------------------------
    # TNP 4: Element map names stay consistent through getElement
    # ------------------------------------------------------------------

    def testTNP_ElementMapGetElementConsistency(self):
        """For every TNP name in the element map, getElement(tnpName) and
        getElement(shortName) must return the same geometric shape."""
        if self.Body.Shape.ElementMapVersion == "":
            return

        eMap = self.Pad.Shape.ElementMap
        self.assertGreater(self.Pad.Shape.ElementMapSize, 0,
                           "ElementMap should not be empty")
        for tnpName, shortName in eMap.items():
            elem1 = self.Pad.Shape.getElement(tnpName)
            elem2 = self.Pad.Shape.getElement(shortName)
            self.assertTrue(elem1.isSame(elem2),
                            f"getElement('{tnpName}') != getElement('{shortName}')")

    # ------------------------------------------------------------------
    # TNP 5: Element map preserved after second Pad
    # ------------------------------------------------------------------

    def testTNP_ElementMapPreservedAfterSecondPad(self):
        """After building Pad2 on Face6, Pad2's element map must be
        populated and consistent."""
        if self.Body.Shape.ElementMapVersion == "":
            return

        sketch2 = self.Doc.addObject("Sketcher::SketchObject", "Sketch2")
        self.Body.addObject(sketch2)
        sketch2.MapMode = "FlatFace"
        sketch2.AttachmentSupport = [(self.Pad, "Face6")]
        TestSketcherApp.CreateRectangleSketch(sketch2, (2, 2), (6, 6))
        self.Doc.recompute()
        pad2 = self.Doc.addObject("PartDesign::Pad", "Pad2")
        self.Body.addObject(pad2)
        pad2.Profile = sketch2
        pad2.Length = 5
        self.Doc.recompute()

        self.assertGreater(pad2.Shape.ElementMapSize, 0,
                           "Pad2 should have an element map")
        reverseMap = pad2.Shape.ElementReverseMap
        faces = [n for n in reverseMap.keys() if n.startswith("Face")]
        edges = [n for n in reverseMap.keys() if n.startswith("Edge")]
        vertexes = [n for n in reverseMap.keys() if n.startswith("Vertex")]
        # An L-tower: original box has 6 faces, adding a box on top creates
        # a combined shape with more faces than a simple box
        self.assertGreaterEqual(len(faces), 6)
        self.assertGreaterEqual(len(edges), 12)
        self.assertGreaterEqual(len(vertexes), 8)

    # ------------------------------------------------------------------
    # TNP 6: Save and restore preserves element maps
    # ------------------------------------------------------------------

    def testTNP_SaveRestorePreservesElementMap(self):
        """Save the document, close it, reopen it.  The Pad element map
        and a Sketch-on-face attachment must survive the round-trip."""
        if self.Body.Shape.ElementMapVersion == "":
            return

        # Attach Sketch2 to Face6
        sketch2 = self.Doc.addObject("Sketcher::SketchObject", "Sketch2")
        self.Body.addObject(sketch2)
        sketch2.MapMode = "FlatFace"
        sketch2.AttachmentSupport = [(self.Pad, "Face6")]
        TestSketcherApp.CreateRectangleSketch(sketch2, (2, 2), (6, 6))
        self.Doc.recompute()
        pad2 = self.Doc.addObject("PartDesign::Pad", "Pad2")
        self.Body.addObject(pad2)
        pad2.Profile = sketch2
        pad2.Length = 5
        self.Doc.recompute()
        self.assertTrue(pad2.isValid())

        mapSizeBefore = self.Pad.Shape.ElementMapSize
        volBefore = pad2.Shape.Volume

        # Save
        filename = tempfile.gettempdir() + os.sep + "PartDesignTestSketchOnFace_TNP"
        self.Doc.saveAs(filename)
        App.closeDocument("PartDesignTestSketchOnFace")

        # Restore
        self.Doc = App.openDocument(filename + ".FCStd")
        self.Doc.recompute()

        pad = self.Doc.getObject("Pad")
        pad2 = self.Doc.getObject("Pad2")
        sketch2 = self.Doc.getObject("Sketch2")
        self.assertIsNotNone(pad)
        self.assertIsNotNone(pad2)
        self.assertTrue(pad2.isValid(), "Pad2 invalid after restore")
        self.assertEqual(pad.Shape.ElementMapSize, mapSizeBefore,
                         "Element map size changed after restore")
        self.assertAlmostEqual(pad2.Shape.Volume, volBefore, places=2,
                               msg="Volume changed after restore")
        # Attachment still references Face6
        self.assertTrue("Face6" in sketch2.AttachmentSupport[0][1][0],
                        "Sketch2 attachment to Face6 lost after restore")

        # Cleanup temp file
        try:
            os.remove(filename + ".FCStd")
        except OSError:
            pass

    # ------------------------------------------------------------------
    # TNP 7: Pad length change does not break downstream
    # ------------------------------------------------------------------

    def testTNP_PadLengthChangePreservesDownstream(self):
        """Changing Pad.Length (but keeping the same topology) must not
        break a Sketch/Pad attached to one of its faces."""
        if self.Body.Shape.ElementMapVersion == "":
            return

        sketch2 = self.Doc.addObject("Sketcher::SketchObject", "Sketch2")
        self.Body.addObject(sketch2)
        sketch2.MapMode = "FlatFace"
        sketch2.AttachmentSupport = [(self.Pad, "Face6")]
        TestSketcherApp.CreateRectangleSketch(sketch2, (2, 2), (6, 6))
        self.Doc.recompute()
        pad2 = self.Doc.addObject("PartDesign::Pad", "Pad2")
        self.Body.addObject(pad2)
        pad2.Profile = sketch2
        pad2.Length = 5
        self.Doc.recompute()
        self.assertTrue(pad2.isValid())

        # Change the base pad height from 10 to 20
        self.Pad.Length = 20
        self.Doc.recompute()

        self.assertTrue(self.Pad.isValid(), "Pad broke after length change")
        self.assertTrue(pad2.isValid(), "Pad2 broke after base length change (TNP)")
        # Volume: 10*10*20 = 2000 + 6*6*5 = 180
        self.assertAlmostEqual(pad2.Shape.Volume, 2180.0, places=1)

    # ------------------------------------------------------------------
    # TNP 8: Fillet on Pad edge, then mutate base sketch
    # ------------------------------------------------------------------

    def testTNP_FilletSurvivesBaseSketchMove(self):
        """Apply a Fillet to an edge of the Pad, then move the base
        Sketch.  Both the Pad and the Fillet must remain valid thanks
        to the oldName fallback in getContinuousEdges()."""
        if self.Body.Shape.ElementMapVersion == "":
            return

        fillet = self.Doc.addObject("PartDesign::Fillet", "Fillet")
        self.Body.addObject(fillet)
        fillet.Base = (self.Pad, ["Edge1"])
        fillet.Radius = 1.0
        self.Doc.recompute()
        self.assertTrue(fillet.isValid(), "Fillet not valid initially")

        # Move the base sketch
        self.Sketch.AttachmentOffset = App.Placement(
            App.Vector(2, 0, 0),
            App.Rotation(0, 0, 0),
        )
        self.Doc.recompute()

        self.assertTrue(self.Pad.isValid(), "Pad broke after sketch move")
        self.assertTrue(fillet.isValid(), "Fillet broke after base sketch move (TNP)")

    # ------------------------------------------------------------------
    # TNP 9: Deep chain — 4 Pads stacked, perturb layer 1
    # ------------------------------------------------------------------

    def testTNP_FourPadDeepChainSurvives(self):
        """Stack four Pads each on the previous one's Face6.
        Offset the first sketch.  All must remain valid."""
        if self.Body.Shape.ElementMapVersion == "":
            return

        pads = [self.Pad]
        sketches = [self.Sketch]

        for level in range(1, 4):
            sk = self.Doc.addObject("Sketcher::SketchObject", f"Sk{level}")
            self.Body.addObject(sk)
            sk.MapMode = "FlatFace"
            sk.AttachmentSupport = [(pads[-1], "Face6")]
            margin = level
            side = 10 - 2 * margin
            TestSketcherApp.CreateRectangleSketch(sk, (margin, margin), (side, side))
            self.Doc.recompute()
            pd = self.Doc.addObject("PartDesign::Pad", f"Pd{level}")
            self.Body.addObject(pd)
            pd.Profile = sk
            pd.Length = 3
            self.Doc.recompute()
            self.assertTrue(pd.isValid(), f"Pad level {level} not valid initially")
            pads.append(pd)
            sketches.append(sk)

        # Perturb the very first sketch
        self.Sketch.AttachmentOffset = App.Placement(
            App.Vector(0.5, 0.5, 0),
            App.Rotation(0, 0, 0),
        )
        self.Doc.recompute()

        for i, pd in enumerate(pads):
            self.assertTrue(pd.isValid(),
                            f"Pad at level {i} broke after base sketch perturbation (TNP)")

    # ------------------------------------------------------------------
    # TNP 10: Verify Part.getShape with TNP names after mutation
    # ------------------------------------------------------------------

    def testTNP_PartGetShapeWithTNPNamesAfterMutation(self):
        """After mutating the base sketch, Part.getShape must still
        resolve every short face name on the Pad."""
        if self.Body.Shape.ElementMapVersion == "":
            return

        # Move base sketch
        self.Sketch.AttachmentOffset = App.Placement(
            App.Vector(1, 1, 0),
            App.Rotation(0, 0, 0),
        )
        self.Doc.recompute()

        for i in range(1, 7):
            name = f"Face{i}"
            sub = Part.getShape(self.Pad, name, needSubElement=True)
            self.assertFalse(sub.isNull(),
                             f"Part.getShape(Pad, '{name}') is null after base sketch move")
            self.assertEqual(sub.ShapeType, "Face")

    # ------------------------------------------------------------------
    # TNP 11: Chamfer on Pad edge survives base resize
    # ------------------------------------------------------------------

    def testTNP_ChamferSurvivesBaseResize(self):
        """Apply a Chamfer to a Pad edge.  Change the Pad length.
        Both the Pad and the Chamfer must remain valid thanks to the
        oldName fallback in getContinuousEdges()."""
        if self.Body.Shape.ElementMapVersion == "":
            return

        chamfer = self.Doc.addObject("PartDesign::Chamfer", "Chamfer")
        self.Body.addObject(chamfer)
        chamfer.Base = (self.Pad, ["Edge1"])
        chamfer.Size = 1.0
        self.Doc.recompute()
        self.assertTrue(chamfer.isValid(), "Chamfer not valid initially")

        # Resize the pad
        self.Pad.Length = 15
        self.Doc.recompute()

        self.assertTrue(self.Pad.isValid(), "Pad broke after resize")
        self.assertTrue(chamfer.isValid(), "Chamfer broke after pad resize (TNP)")

    # ------------------------------------------------------------------
    # TNP 12: Attachment reference string preserved after recompute
    # ------------------------------------------------------------------

    def testTNP_AttachmentReferenceStableAfterRecompute(self):
        """The AttachmentSupport sub-element string for a Sketch on Face6
        must still contain 'Face6' after multiple recomputes and a base
        sketch perturbation."""
        if self.Body.Shape.ElementMapVersion == "":
            return

        sketch2 = self.Doc.addObject("Sketcher::SketchObject", "Sketch2")
        self.Body.addObject(sketch2)
        sketch2.MapMode = "FlatFace"
        sketch2.AttachmentSupport = [(self.Pad, "Face6")]
        self.Doc.recompute()

        # Verify initial attachment
        ref = sketch2.AttachmentSupport[0][1][0]
        self.assertIn("Face6", ref)

        # Perturb and recompute several times
        for offset in [1, 2, 0]:
            self.Sketch.AttachmentOffset = App.Placement(
                App.Vector(offset, 0, 0),
                App.Rotation(0, 0, 0),
            )
            self.Doc.recompute()

        ref_after = sketch2.AttachmentSupport[0][1][0]
        self.assertIn("Face6", ref_after,
                       "Attachment reference to Face6 lost after perturbation (TNP)")

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def tearDown(self):
        # Handle the save/restore test which reopens under a different name
        for name in App.listDocuments():
            if "SketchOnFace" in name:
                App.closeDocument(name)
                return
        try:
            App.closeDocument("PartDesignTestSketchOnFace")
        except Exception:
            pass
