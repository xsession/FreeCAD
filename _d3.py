import sys, traceback
f = open(r'C:\GIT\FreeCAD\_pyout2.txt', 'w')
try:
    import FreeCAD, Part, Sketcher, PartDesign
    
    doc = FreeCAD.newDocument('T')
    body = doc.addObject('PartDesign::Body', 'Body')
    sk = doc.addObject('Sketcher::SketchObject', 'Sketch')
    body.addObject(sk)
    sk.AttachmentSupport = [(doc.getObject('XY_Plane'), '')]
    sk.MapMode = 'FlatFace'
    sk.addGeometry(Part.LineSegment(FreeCAD.Vector(0,0,0), FreeCAD.Vector(10,0,0)), False)
    sk.addGeometry(Part.LineSegment(FreeCAD.Vector(10,0,0), FreeCAD.Vector(10,10,0)), False)
    sk.addGeometry(Part.LineSegment(FreeCAD.Vector(10,10,0), FreeCAD.Vector(0,10,0)), False)
    sk.addGeometry(Part.LineSegment(FreeCAD.Vector(0,10,0), FreeCAD.Vector(0,0,0)), False)
    doc.recompute()
    pad = doc.addObject('PartDesign::Pad', 'Pad')
    body.addObject(pad)
    pad.Profile = sk
    pad.Length = 10.0
    doc.recompute()
    
    s = pad.Shape
    f.write('=== Pad Shape ===\n')
    f.write('ShapeType: %s\n' % s.ShapeType)
    f.write('isNull: %s\n' % s.isNull())
    f.write('isValid: %s\n' % s.isValid())
    f.write('len(Faces): %d\n' % len(s.Faces))
    f.write('len(Edges): %d\n' % len(s.Edges))
    f.write('len(Vertexes): %d\n' % len(s.Vertexes))
    f.write('countElement(Face): %d\n' % s.countElement('Face'))
    f.write('countElement(Edge): %d\n' % s.countElement('Edge'))
    f.write('countElement(Vertex): %d\n' % s.countElement('Vertex'))
    f.write('ElementMapSize: %d\n' % s.ElementMapSize)
    f.write('Tag: %d\n' % s.Tag)
    f.flush()
    
    # Try creating a new Part.Shape from the OCC shape
    f.write('\n=== Copy via Part.Shape ===\n')
    try:
        s2 = Part.Shape(s)
        f.write('Copy ShapeType: %s\n' % s2.ShapeType)
        f.write('Copy len(Faces): %d\n' % len(s2.Faces))
        f.write('Copy countElement(Face): %d\n' % s2.countElement('Face'))
        f.write('Copy Tag: %d\n' % s2.Tag)
        f.write('Copy ElementMapSize: %d\n' % s2.ElementMapSize)
    except Exception as e:
        f.write('Copy ERR: %s\n' % e)
        traceback.print_exc(file=f)
    f.flush()
    
    # Try accessing faces through Solid methods
    f.write('\n=== Solid Shell Faces ===\n')
    try:
        shells = s.Shells
        f.write('Shells: %d\n' % len(shells))
        if len(shells) > 0:
            sh = shells[0]
            f.write('Shell ShapeType: %s\n' % sh.ShapeType)
            f.write('Shell Faces: %d\n' % len(sh.Faces))
            f.write('Shell countElement(Face): %d\n' % sh.countElement('Face'))
    except Exception as e:
        f.write('Shell ERR: %s\n' % e)
    f.flush()
    
    # Test hasSubShape
    f.write('\n=== hasSubShape ===\n')
    try:
        for i in range(1, 7):
            f.write('hasSubShape Face%d: %s\n' % (i, s.hasSubShape('Face%d' % i)))
    except Exception as e:
        f.write('hasSubShape ERR: %s\n' % e)
    f.flush()
    
    # Try a simple box for comparison
    f.write('\n=== Box comparison ===\n')
    try:
        box = Part.makeBox(10, 10, 10)
        f.write('Box ShapeType: %s\n' % box.ShapeType)
        f.write('Box len(Faces): %d\n' % len(box.Faces))
        f.write('Box countElement(Face): %d\n' % box.countElement('Face'))
        f.write('Box Tag: %d\n' % box.Tag)
        f.write('Box ElementMapSize: %d\n' % box.ElementMapSize)
        f.write('Box hasSubShape Face1: %s\n' % box.hasSubShape('Face1'))
    except Exception as e:
        f.write('Box ERR: %s\n' % e)
    f.flush()
    
    # Try to get element names
    f.write('\n=== Element Names ===\n')
    try:
        enames = s.ElementReverseMap
        f.write('ElementReverseMap type: %s\n' % type(enames))
        f.write('ElementReverseMap: %s\n' % repr(enames)[:500])
    except Exception as e:
        f.write('ElementReverseMap ERR: %s\n' % e)
    try:
        for t in ['Face', 'Edge', 'Vertex']:
            names = s.getElementTypes()
            f.write('ElementTypes: %s\n' % names)
            break
    except Exception as e:
        f.write('ElementTypes ERR: %s\n' % e)
    f.flush()
    
    # Check if it's the element map that's broken 
    # by trying to get a sub-shape with explicit index
    f.write('\n=== Direct face access ===\n')
    try:
        faces = s.Faces
        for i, face in enumerate(faces):
            f.write('  Face[%d]: type=%s area=%.2f\n' % (i, face.ShapeType, face.Area))
    except Exception as e:
        f.write('Direct face ERR: %s\n' % e)
    f.flush()
    
    # Check if getSubObject works on body instead of pad
    f.write('\n=== getSubObject on body ===\n')
    try:
        for i in range(1, 7):
            obj = body.getSubObject('Pad.Face%d.' % i)
            if obj is not None:
                f.write('body.getSubObject Pad.Face%d.: type=%s\n' % (i, obj.ShapeType))
            else:
                f.write('body.getSubObject Pad.Face%d.: None\n' % i)
    except Exception as e:
        f.write('body getSubObject ERR: %s\n' % e)
    f.flush()
    
    # Check what shapeType returns for "Face"
    f.write('\n=== shapeType parsing ===\n')
    try:
        # countSubShapes("Face") internally calls shapeType("Face", true)
        # If it returns TopAbs_SHAPE that would explain countElement=0
        # Let's also try with lowercase
        f.write('countElement("Face"): %d\n' % s.countElement('Face'))
        f.write('countElement("Edge"): %d\n' % s.countElement('Edge'))
        f.write('countElement("Vertex"): %d\n' % s.countElement('Vertex'))
        f.write('countElement("SubShape"): %d\n' % s.countElement('SubShape'))
    except Exception as e:
        f.write('countElement ERR: %s\n' % e)
    f.flush()
    
    FreeCAD.closeDocument('T')
    f.write('DONE\n')
except Exception as e:
    f.write('FATAL: %s\n' % e)
    traceback.print_exc(file=f)
finally:
    f.flush()
    f.close()

sys.exit(0)
