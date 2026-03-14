"""
Automated GUI workflow tester for FreeCAD PartDesign sketch-on-face.

Emulates what a human would do step-by-step:
  1. Create a new document
  2. Create a Body with a Sketch on XY_Plane  
  3. Draw a rectangle in the Sketch
  4. Pad the Sketch to create a 3D solid
  5. Select a face on the Pad
  6. Click "New Sketch" 
  7. Verify a new sketch was created on that face

Run inside FreeCAD:
  - Open FreeCAD GUI
  - In the Python console:  exec(open(r"C:\GIT\FreeCAD\tests\test_sketcher_on_face.py").read())
  
  OR from command line (headless diagnostics only):
  - FreeCADCmd.exe test_sketcher_on_face.py
"""

import sys
import time
import traceback

# ── Detect environment ───────────────────────────────────────────────
try:
    import FreeCAD as App
    import Part
    import Sketcher
except ImportError:
    print("ERROR: This script must be run inside FreeCAD (GUI or FreeCADCmd).")
    sys.exit(1)

HAS_GUI = False
try:
    import FreeCADGui as Gui
    if Gui.activeDocument() is not None or Gui.ActiveDocument is not None:
        HAS_GUI = True
except Exception:
    pass

# Also try to detect if Gui module is available even without active doc
if not HAS_GUI:
    try:
        import FreeCADGui as Gui
        # If we can import Gui, the GUI might be available
        HAS_GUI = hasattr(Gui, 'Selection')
    except Exception:
        pass


# ── Utility helpers ──────────────────────────────────────────────────
class Logger:
    """Color-coded test output."""
    PASS = 0
    FAIL = 1
    WARN = 2
    INFO = 3
    
    _counts = {"pass": 0, "fail": 0, "warn": 0, "skip": 0}
    
    @staticmethod
    def _print(prefix, msg):
        full = f"[{prefix}] {msg}"
        print(full)
        try:
            App.Console.PrintMessage(full + "\n")
        except Exception:
            pass
    
    @classmethod
    def ok(cls, msg):
        cls._counts["pass"] += 1
        cls._print("  OK  ", msg)
    
    @classmethod
    def fail(cls, msg):
        cls._counts["fail"] += 1
        cls._print(" FAIL ", msg)
    
    @classmethod
    def warn(cls, msg):
        cls._counts["warn"] += 1
        cls._print(" WARN ", msg)
    
    @classmethod
    def skip(cls, msg):
        cls._counts["skip"] += 1
        cls._print(" SKIP ", msg)
    
    @classmethod
    def info(cls, msg):
        cls._print(" INFO ", msg)
    
    @classmethod
    def section(cls, msg):
        cls._print("======", msg)
    
    @classmethod
    def summary(cls):
        p, f, w, s = cls._counts["pass"], cls._counts["fail"], cls._counts["warn"], cls._counts["skip"]
        total = p + f + s
        cls.section(f"RESULTS: {p} passed, {f} failed, {w} warnings, {s} skipped / {total} total")
        return f == 0


def process_events(delay=0.1):
    """Process Qt events (if GUI) and wait — emulates human pause."""
    try:
        from PySide.QtGui import QApplication
        QApplication.processEvents()
    except Exception:
        pass
    if delay > 0:
        time.sleep(delay)


# ── Step 1: Create document and body ────────────────────────────────
def test_create_document():
    """Human action: File → New Document."""
    Logger.section("Step 1: Create new document")
    doc = App.newDocument("TestSketchOnFace")
    process_events(0.2)
    
    if doc is None:
        Logger.fail("Could not create document")
        return None
    Logger.ok(f"Created document '{doc.Name}'")
    return doc


def test_create_body(doc):
    """Human action: PartDesign → Create Body."""
    Logger.section("Step 2: Create Body")
    body = doc.addObject("PartDesign::Body", "Body")
    process_events(0.1)
    
    if body is None:
        Logger.fail("Could not create Body")
        return None
    Logger.ok(f"Created Body '{body.Name}'")
    
    # Activate the body (like double-clicking it in model tree)
    if HAS_GUI:
        try:
            Gui.activateView("Gui::View3DInventor", True)
            Gui.activeView().setActiveObject("pdbody", body)
            Logger.ok("Body activated in GUI view")
        except Exception as e:
            Logger.warn(f"Could not activate body in view: {e}")
    
    return body


# ── Step 2: Create sketch with rectangle ────────────────────────────
def test_create_sketch(doc, body):
    """Human action: Select XY_Plane → New Sketch → Draw rectangle → Close."""
    Logger.section("Step 3: Create Sketch on XY_Plane")
    
    sketch = doc.addObject("Sketcher::SketchObject", "Sketch")
    if sketch is None:
        Logger.fail("Could not create SketchObject")
        return None
    
    # Attach to XY_Plane (like human selecting XY_Plane and clicking New Sketch)
    xy_plane = body.Origin.OriginFeatures[3]  # XY_Plane
    sketch.AttachmentSupport = (xy_plane, [""])
    sketch.MapMode = "FlatFace"
    body.addObject(sketch)
    Logger.ok(f"Sketch '{sketch.Name}' attached to {xy_plane.Label}")
    
    # Draw a 20x20mm rectangle centered at origin (like human drawing)
    Logger.info("Drawing 20x20mm rectangle...")
    geo = []
    geo.append(Part.LineSegment(App.Vector(-10, -10, 0), App.Vector(10, -10, 0)))
    geo.append(Part.LineSegment(App.Vector(10, -10, 0), App.Vector(10, 10, 0)))
    geo.append(Part.LineSegment(App.Vector(10, 10, 0), App.Vector(-10, 10, 0)))
    geo.append(Part.LineSegment(App.Vector(-10, 10, 0), App.Vector(-10, -10, 0)))
    sketch.addGeometry(geo, False)
    
    # Add constraints (like human would constrain the sketch)
    constraints = []
    constraints.append(Sketcher.Constraint("Coincident", 0, 2, 1, 1))
    constraints.append(Sketcher.Constraint("Coincident", 1, 2, 2, 1))
    constraints.append(Sketcher.Constraint("Coincident", 2, 2, 3, 1))
    constraints.append(Sketcher.Constraint("Coincident", 3, 2, 0, 1))
    constraints.append(Sketcher.Constraint("Horizontal", 0))
    constraints.append(Sketcher.Constraint("Horizontal", 2))
    constraints.append(Sketcher.Constraint("Vertical", 1))
    constraints.append(Sketcher.Constraint("Vertical", 3))
    sketch.addConstraint(constraints)
    
    doc.recompute()
    process_events(0.2)
    
    if sketch.Shape.isNull():
        Logger.fail("Sketch shape is null after recompute")
        return None
    
    Logger.ok(f"Sketch fully constrained, {len(sketch.Shape.Edges)} edges")
    return sketch


# ── Step 3: Pad the sketch ──────────────────────────────────────────
def test_create_pad(doc, body, sketch):
    """Human action: Select Sketch → PartDesign Pad → Set length 10mm → OK."""
    Logger.section("Step 4: Pad the Sketch (10mm)")
    
    pad = doc.addObject("PartDesign::Pad", "Pad")
    pad.Profile = sketch
    pad.Length = 10.0
    pad.Type = 0  # Dimension
    pad.Reversed = False
    body.addObject(pad)
    
    doc.recompute()
    process_events(0.3)
    
    if pad.Shape.isNull():
        Logger.fail("Pad shape is null — Pad failed to compute!")
        return None
    
    face_count = len(pad.Shape.Faces)
    edge_count = len(pad.Shape.Edges)
    vertex_count = len(pad.Shape.Vertexes)
    
    Logger.ok(f"Pad computed: {face_count} faces, {edge_count} edges, {vertex_count} vertices")
    
    if face_count != 6:
        Logger.warn(f"Expected 6 faces on a box pad, got {face_count}")
    
    return pad


# ── Step 4: Verify shape sub-elements ───────────────────────────────
def test_shape_subelements(pad):
    """Diagnostic: Verify we can access Face1..Face6 on the Pad (App level)."""
    Logger.section("Step 5: Verify Pad sub-element access (App level)")
    
    shape = pad.Shape
    if shape.isNull():
        Logger.fail("Pad.Shape is null!")
        return False
    
    all_ok = True
    
    # Test each face
    for i in range(1, len(shape.Faces) + 1):
        face_name = f"Face{i}"
        try:
            sub = shape.getElement(face_name)
            if sub is None or sub.isNull():
                Logger.fail(f"  {face_name}: getElement returned null")
                all_ok = False
            else:
                Logger.ok(f"  {face_name}: {sub.ShapeType}, Area={sub.Area:.2f}")
        except Exception as e:
            Logger.fail(f"  {face_name}: Exception — {e}")
            all_ok = False
    
    # Test Part.getShape with needSubElement
    Logger.info("Testing Part.getShape() with needSubElement=True...")
    for i in range(1, min(len(shape.Faces) + 1, 7)):
        face_name = f"Face{i}"
        try:
            sub = Part.getShape(pad, face_name, needSubElement=True)
            if sub is None or sub.isNull():
                Logger.fail(f"  Part.getShape(pad, '{face_name}', needSubElement=True) = null")
                all_ok = False
            else:
                Logger.ok(f"  Part.getShape(pad, '{face_name}') → {sub.ShapeType}")
        except Exception as e:
            Logger.fail(f"  Part.getShape(pad, '{face_name}') → Exception: {e}")
            all_ok = False
    
    # Test TopoShape element name mapping
    Logger.info("Testing TopoShape element names...")
    try:
        ts = pad.Shape
        types = ts.ElementTypes
        Logger.ok(f"  ElementTypes = {types}")
        for t in types:
            count = ts.countSubElements(t)
            Logger.ok(f"  count({t}) = {count}")
    except Exception as e:
        Logger.warn(f"  ElementTypes test: {e}")
    
    return all_ok


# ── Step 5: Test GUI selection of face ──────────────────────────────
def test_gui_face_selection(doc, pad):
    """Human action: Click on Face1 of the Pad in 3D view.
    We emulate this via Gui.Selection.addSelection()."""
    Logger.section("Step 6: GUI — Select Face1 on Pad")
    
    if not HAS_GUI:
        Logger.skip("No GUI available — skipping selection test")
        return False
    
    # Clear any existing selection (like clicking empty space first)
    Gui.Selection.clearSelection()
    process_events(0.1)
    
    sel_before = Gui.Selection.getSelection()
    Logger.info(f"Selection before: {len(sel_before)} items")
    
    # Emulate clicking Face1 on the Pad
    doc_name = doc.Name
    pad_name = pad.Name
    
    Logger.info(f"Adding selection: {doc_name}.{pad_name}.Face1")
    Gui.Selection.addSelection(doc_name, pad_name, "Face1")
    process_events(0.2)
    
    # Verify selection was added
    sel_after = Gui.Selection.getSelection()
    sel_ex = Gui.Selection.getSelectionEx()
    
    Logger.info(f"Selection after addSelection: {len(sel_after)} items, {len(sel_ex)} selectionEx")
    
    if len(sel_after) == 0:
        Logger.fail("Selection is EMPTY after addSelection — face selection is broken!")
        
        # Additional diagnostics
        Logger.info("Trying to select the Pad object without sub-element...")
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(doc_name, pad_name)
        process_events(0.1)
        sel2 = Gui.Selection.getSelection()
        if len(sel2) > 0:
            Logger.warn(f"Object-level selection works ({len(sel2)} items) but sub-element (Face1) does not")
        else:
            Logger.fail("Even object-level selection fails — Selection system is broken")
        return False
    
    # Check sub-element names
    if len(sel_ex) > 0:
        sub_names = sel_ex[0].SubElementNames
        Logger.info(f"SubElementNames = {sub_names}")
        if "Face1" in sub_names:
            Logger.ok("Face1 is correctly in SubElementNames")
        else:
            Logger.fail(f"Face1 not found in SubElementNames: {sub_names}")
            return False
    else:
        Logger.fail("getSelectionEx() returned empty even though getSelection() has items")
        return False
    
    return True


# ── Step 6: Test SelectionFilter matching ───────────────────────────
def test_selection_filter(doc, pad):
    """Test that the PartDesign face filter matches the selection.
    This is the filter used by SketchWorkflow::getFilters()."""
    Logger.section("Step 7: Test SelectionFilter with Face selection")
    
    if not HAS_GUI:
        Logger.skip("No GUI — skipping SelectionFilter test")
        return False
    
    # Ensure Face1 is selected
    Gui.Selection.clearSelection()
    Gui.Selection.addSelection(doc.Name, pad.Name, "Face1")
    process_events(0.1)
    
    # Test the exact filter string used by SketchWorkflow::getFilters()
    try:
        from Gui.Selection import SelectionFilter
    except ImportError:
        try:
            # Alternative import path
            sf_class = Gui.Selection.Filter
        except Exception:
            Logger.warn("Cannot import SelectionFilter — testing via string")
            sf_class = None
    
    # Use the filter string from SketchWorkflow.cpp line ~896
    filter_str = "SELECT Part::Feature SUBELEMENT Face COUNT 1"
    try:
        sf = Gui.Selection.Filter(filter_str)
        result = sf.match()
        if result:
            Logger.ok(f"SelectionFilter('{filter_str}').match() = True")
        else:
            Logger.fail(f"SelectionFilter('{filter_str}').match() = False — THIS IS THE BUG")
            
            # Extra diagnostics
            for test_filter in [
                "SELECT Part::Feature SUBELEMENT Face COUNT 1",
                "SELECT Part::Feature SUBELEMENT Edge COUNT 1",
                "SELECT Part::Feature COUNT 1",
                "SELECT PartDesign::Pad COUNT 1",
                "SELECT App::DocumentObject COUNT 1",
            ]:
                try:
                    sf2 = Gui.Selection.Filter(test_filter)
                    r2 = sf2.match()
                    Logger.info(f"  Filter('{test_filter}').match() = {r2}")
                except Exception as e2:
                    Logger.info(f"  Filter('{test_filter}') ERROR: {e2}")
            return False
    except Exception as e:
        Logger.fail(f"SelectionFilter test exception: {e}")
        traceback.print_exc()
        return False
    
    return True


# ── Step 7: Test New Sketch command ─────────────────────────────────
def test_new_sketch_command(doc, body, pad):
    """Human action: Select Face1 on Pad → Click 'New Sketch' toolbar button.
    This tests the full SketchWorkflow pipeline."""
    Logger.section("Step 8: Test 'New Sketch' command with face selected")
    
    if not HAS_GUI:
        Logger.skip("No GUI — skipping New Sketch command test")
        return False
    
    initial_obj_count = len(doc.Objects)
    
    # Select Face1 on Pad (like human clicking the face)
    Gui.Selection.clearSelection()
    process_events(0.1)
    Gui.Selection.addSelection(doc.Name, pad.Name, "Face1")
    process_events(0.3)
    
    sel_ex = Gui.Selection.getSelectionEx()
    Logger.info(f"Selection before command: {len(sel_ex)} items")
    if len(sel_ex) > 0:
        Logger.info(f"  Object: {sel_ex[0].ObjectName}, SubNames: {sel_ex[0].SubElementNames}")
    
    # Run the New Sketch command (like clicking toolbar button)
    # We use a timer to auto-accept any dialog that pops up
    try:
        from PySide.QtCore import QTimer
        
        def auto_accept_dialog():
            """If a plane selection dialog appears, auto-close it (this means the bug exists)."""
            try:
                from PySide.QtGui import QApplication
                dialog = QApplication.activeModalWidget()
                if dialog is not None:
                    Logger.warn(f"Modal dialog appeared: '{dialog.windowTitle()}' — face selection was NOT used")
                    dialog.reject()  # Cancel the dialog
            except Exception:
                pass
        
        # Set up timer to catch modal dialogs
        QTimer.singleShot(1000, auto_accept_dialog)
        QTimer.singleShot(2000, auto_accept_dialog)
        
        Logger.info("Running Gui.runCommand('PartDesign_NewSketch')...")
        Gui.runCommand("PartDesign_NewSketch")
        process_events(0.5)
        
    except Exception as e:
        Logger.fail(f"New Sketch command exception: {e}")
        traceback.print_exc()
        return False
    
    # Check if a new sketch was created
    new_obj_count = len(doc.Objects)
    new_objects = new_obj_count - initial_obj_count
    
    if new_objects > 0:
        # Find the new sketch
        new_sketch = None
        for obj in doc.Objects:
            if obj.isDerivedFrom("Sketcher::SketchObject") and obj.Name != "Sketch":
                new_sketch = obj
        
        if new_sketch:
            support = new_sketch.AttachmentSupport
            Logger.ok(f"New sketch '{new_sketch.Name}' created!")
            Logger.info(f"  AttachmentSupport = {support}")
            Logger.info(f"  MapMode = {new_sketch.MapMode}")
            
            # Verify it's on the Pad face
            if support and len(support) > 0:
                support_obj = support[0][0] if isinstance(support[0], tuple) else support[0]
                if hasattr(support_obj, 'Name') and support_obj.Name == pad.Name:
                    Logger.ok("Sketch is correctly attached to the Pad face!")
                    return True
                else:
                    Logger.warn(f"Sketch attached to '{support_obj}' instead of Pad")
            else:
                Logger.warn("Sketch has no AttachmentSupport — may be on a base plane")
        else:
            Logger.warn(f"{new_objects} new objects created but no new SketchObject found")
    else:
        Logger.fail("No new objects created — New Sketch command did not create a sketch")
        Logger.info("This confirms the bug: face selection is not being passed to the command")
    
    return False


# ── Step 8: Diagnostic — Test complete sub-shape lookup chain ───────
def test_subshape_lookup_chain(pad):
    """Deep diagnostic: test every layer of the sub-shape lookup."""
    Logger.section("Step 9: Deep diagnostic — sub-shape lookup chain")
    
    shape = pad.Shape
    
    # Layer 1: Direct OCC access
    Logger.info("Layer 1: Direct TopoDS_Shape face access")
    try:
        import Part
        faces = shape.Faces
        Logger.ok(f"  shape.Faces: {len(faces)} faces")
        for i, f in enumerate(faces):
            Logger.ok(f"    Face[{i}]: Area={f.Area:.4f}, Type={f.Surface}")
    except Exception as e:
        Logger.fail(f"  shape.Faces failed: {e}")
    
    # Layer 2: getElement (string-based lookup)
    Logger.info("Layer 2: shape.getElement('FaceN')")
    for i in range(1, 7):
        try:
            elem = shape.getElement(f"Face{i}")
            Logger.ok(f"  getElement('Face{i}'): {elem.ShapeType if elem else 'null'}")
        except Exception as e:
            Logger.fail(f"  getElement('Face{i}'): {e}")
    
    # Layer 3: Part.getShape with resolve
    Logger.info("Layer 3: Part.getShape(pad, 'FaceN', needSubElement=True)")
    for i in range(1, 7):
        try:
            s = Part.getShape(pad, f"Face{i}", needSubElement=True)
            if s and not s.isNull():
                Logger.ok(f"  Face{i}: {s.ShapeType}, Area={s.Area:.4f}")
            else:
                Logger.fail(f"  Face{i}: null shape returned")
        except Exception as e:
            Logger.fail(f"  Face{i}: {e}")
    
    # Layer 4: Element map / topology naming
    Logger.info("Layer 4: Element map inspection")
    try:
        ts = pad.Shape
        Logger.info(f"  Tag = {ts.Tag}")
        Logger.info(f"  ElementTypes = {ts.ElementTypes}")
        Logger.info(f"  Hashcode = {ts.Hashcode}")
        
        # Try mapped element names
        for face_type in ["Face"]:
            count = ts.countSubElements(face_type)
            Logger.ok(f"  countSubElements('{face_type}') = {count}")
            for i in range(1, count + 1):
                try:
                    mapped = ts.getElementName(f"{face_type}{i}")
                    Logger.ok(f"    {face_type}{i} → mapped: '{mapped}'")
                except Exception as e:
                    Logger.warn(f"    {face_type}{i} → {e}")
    except Exception as e:
        Logger.warn(f"  Element map inspection: {e}")


# ── Step 9: GUI Selection system diagnostic ─────────────────────────
def test_selection_system_diagnostic(doc, pad):
    """Test that the Selection system itself works for various object types."""
    Logger.section("Step 10: Selection system diagnostic")
    
    if not HAS_GUI:
        Logger.skip("No GUI — skipping selection diagnostic")
        return
    
    tests = [
        ("Object only",     doc.Name, pad.Name, ""),
        ("Face1",           doc.Name, pad.Name, "Face1"),
        ("Face2",           doc.Name, pad.Name, "Face2"),
        ("Edge1",           doc.Name, pad.Name, "Edge1"),
        ("Vertex1",         doc.Name, pad.Name, "Vertex1"),
    ]
    
    for label, dname, oname, sub in tests:
        Gui.Selection.clearSelection()
        process_events(0.05)
        
        if sub:
            Gui.Selection.addSelection(dname, oname, sub)
        else:
            Gui.Selection.addSelection(dname, oname)
        process_events(0.05)
        
        sel = Gui.Selection.getSelection()
        sel_ex = Gui.Selection.getSelectionEx()
        
        if len(sel) > 0:
            sub_names = sel_ex[0].SubElementNames if len(sel_ex) > 0 else []
            Logger.ok(f"  Select '{label}': sel={len(sel)}, selEx={len(sel_ex)}, subs={sub_names}")
        else:
            Logger.fail(f"  Select '{label}': EMPTY — selection failed!")
    
    Gui.Selection.clearSelection()


# ══════════════════════════════════════════════════════════════════════
#  MAIN TEST RUNNER
# ══════════════════════════════════════════════════════════════════════
def run_all_tests():
    Logger.section("FreeCAD Sketch-on-Face Automated Test Suite")
    Logger.info(f"FreeCAD version: {App.Version()[0]}.{App.Version()[1]}.{App.Version()[2]}")
    Logger.info(f"GUI available: {HAS_GUI}")
    Logger.info(f"Platform: {sys.platform}")
    Logger.info("")
    
    # Step 1: Create document
    doc = test_create_document()
    if doc is None:
        Logger.fail("Cannot continue without document")
        Logger.summary()
        return
    
    # Step 2: Create body
    body = test_create_body(doc)
    if body is None:
        Logger.fail("Cannot continue without body")
        Logger.summary()
        return
    
    # Step 3: Create sketch
    sketch = test_create_sketch(doc, body)
    if sketch is None:
        Logger.fail("Cannot continue without sketch")
        Logger.summary()
        return
    
    # Step 4: Pad the sketch
    pad = test_create_pad(doc, body, sketch)
    if pad is None:
        Logger.fail("Cannot continue without pad")
        Logger.summary()
        return
    
    # Step 5: Verify sub-elements at App level
    test_shape_subelements(pad)
    
    # Step 6: GUI selection test
    if HAS_GUI:
        test_gui_face_selection(doc, pad)
    
    # Step 7: SelectionFilter test
    if HAS_GUI:
        test_selection_filter(doc, pad)
    
    # Step 8: Full New Sketch command test
    if HAS_GUI:
        test_new_sketch_command(doc, body, pad)
    
    # Step 9: Deep sub-shape diagnostic
    test_subshape_lookup_chain(pad)
    
    # Step 10: Selection system diagnostic
    if HAS_GUI:
        test_selection_system_diagnostic(doc, pad)
    
    # Summary
    Logger.info("")
    all_passed = Logger.summary()
    
    # Cleanup
    try:
        App.closeDocument(doc.Name)
    except Exception:
        pass
    
    return all_passed


# ── Entry point ──────────────────────────────────────────────────────
if __name__ == "__main__":
    run_all_tests()
else:
    # Running via exec() in FreeCAD console
    run_all_tests()
