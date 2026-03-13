import sys, os
sys.stdout = open(r'C:\GIT\FreeCAD\_pyout5.txt', 'w')
sys.stderr = sys.stdout

import FreeCAD as App
import Part

print("=== Test 1: countElement on makeBox ===")
s = Part.makeBox(10, 10, 10)
print(f"ShapeType: {s.ShapeType}, isNull: {s.isNull()}, isValid: {s.isValid()}")
print(f"len(Faces): {len(s.Faces)}")
print(f"countElement('Face'): {s.countElement('Face')}")
print(f"countElement('Edge'): {s.countElement('Edge')}")
print(f"countElement('Vertex'): {s.countElement('Vertex')}")

print("\n=== Test 2: Part.Feature with box shape ===")
doc = App.newDocument("Test")
feat = doc.addObject("Part::Feature", "Box")
feat.Shape = s
doc.recompute()
shape = feat.Shape
print(f"feat.Shape.countElement('Face'): {shape.countElement('Face')}")

print("\n=== Test 3: Part.getShape ===")
for i in range(1, 7):
    sub = Part.getShape(feat, f"Face{i}", needSubElement=True)
    print(f"Face{i}: null={sub.isNull()}, type={sub.ShapeType if not sub.isNull() else 'N/A'}")

print("\n=== Test 4: Pad + sketch on face ===")
import Sketcher, PartDesign
doc2 = App.newDocument("PadTest")
body = doc2.addObject('PartDesign::Body', 'Body')
sk = doc2.addObject('Sketcher::SketchObject', 'Sketch')
body.addObject(sk)
sk.AttachmentSupport = [(doc2.getObject('XY_Plane'), '')]
sk.MapMode = 'FlatFace'
sk.addGeometry(Part.LineSegment(App.Vector(0,0,0), App.Vector(10,0,0)), False)
sk.addGeometry(Part.LineSegment(App.Vector(10,0,0), App.Vector(10,10,0)), False)
sk.addGeometry(Part.LineSegment(App.Vector(10,10,0), App.Vector(0,10,0)), False)
sk.addGeometry(Part.LineSegment(App.Vector(0,10,0), App.Vector(0,0,0)), False)
doc2.recompute()
pad = doc2.addObject('PartDesign::Pad', 'Pad')
body.addObject(pad)
pad.Profile = sk
pad.Length = 10.0
doc2.recompute()
ps = pad.Shape
print(f"Pad ShapeType: {ps.ShapeType}, Faces: {len(ps.Faces)}, countElement('Face'): {ps.countElement('Face')}")
print(f"Pad ElementMapSize: {ps.ElementMapSize}")

# Test getSubObject on pad faces (this is what sketch-on-face needs)
for i in range(1, 7):
    sub = pad.getSubObject(f"Face{i}")
    print(f"pad.getSubObject('Face{i}'): type={type(sub).__name__}, null={sub.isNull() if hasattr(sub, 'isNull') else 'N/A'}")

# Test Part.getShape on pad
for i in range(1, 7):
    sub = Part.getShape(pad, f"Face{i}", needSubElement=True)
    print(f"Part.getShape(pad, 'Face{i}'): null={sub.isNull()}")

App.closeDocument("Test")
App.closeDocument("PadTest")
print("\nALL TESTS PASSED")
sys.stdout.flush()
sys.stdout.close()
