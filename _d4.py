import sys, traceback
f = open(r'C:\GIT\FreeCAD\_pyout3.txt', 'w')
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
    
    f.write('Sketch valid: %s\n' % sk.Shape.isValid())
    f.write('Sketch ShapeType: %s\n' % sk.Shape.ShapeType)
    f.write('Sketch state: %s\n' % str(sk.State))
    f.flush()
    
    pad = doc.addObject('PartDesign::Pad', 'Pad')
    body.addObject(pad)
    pad.Profile = sk
    pad.Length = 10.0
    
    f.write('\nBefore recompute:\n')
    f.write('Pad state: %s\n' % str(pad.State))
    f.flush()
    
    rc = doc.recompute()
    f.write('\nAfter recompute (rc=%s):\n' % str(rc))
    f.write('Pad state: %s\n' % str(pad.State))
    f.write('Pad isValid: %s\n' % pad.isValid())
    f.flush()
    
    # Check if Shape property is null
    try:
        shape_prop = pad.getPropertyByName('Shape')
        f.write('Shape property type: %s\n' % type(shape_prop))
        f.write('Shape isNull: %s\n' % shape_prop.isNull())
        if not shape_prop.isNull():
            f.write('Shape ShapeType: %s\n' % shape_prop.ShapeType)
            f.write('Shape len(Faces): %d\n' % len(shape_prop.Faces))
    except Exception as e:
        f.write('Shape property ERR: %s\n' % e)
        traceback.print_exc(file=f)
    f.flush()
    
    # Check Pad properties
    f.write('\nPad properties:\n')
    for prop in pad.PropertiesList:
        try:
            val = pad.getPropertyByName(prop)
            f.write('  %s = %s\n' % (prop, repr(val)[:100]))
        except Exception as e:
            f.write('  %s = ERR: %s\n' % (prop, e))
    f.flush()
    
    # Try direct Part operations
    f.write('\n=== Direct Part.makeBox test ===\n')
    box = Part.makeBox(10, 10, 10)
    f.write('Box ShapeType: %s\n' % box.ShapeType)
    f.write('Box Faces: %d\n' % len(box.Faces))
    f.write('Box countElement(Face): %d\n' % box.countElement('Face'))
    f.write('Box isValid: %s\n' % box.isValid())
    f.flush()
    
    # Try extrusion manually
    f.write('\n=== Manual extrusion ===\n')
    try:
        wire = Part.makePolygon([FreeCAD.Vector(0,0,0), FreeCAD.Vector(10,0,0),
                                  FreeCAD.Vector(10,10,0), FreeCAD.Vector(0,10,0),
                                  FreeCAD.Vector(0,0,0)])
        face = Part.Face(wire)
        solid = face.extrude(FreeCAD.Vector(0,0,10))
        f.write('Manual solid ShapeType: %s\n' % solid.ShapeType)
        f.write('Manual solid Faces: %d\n' % len(solid.Faces))
        f.write('Manual solid countElement(Face): %d\n' % solid.countElement('Face'))
        f.write('Manual solid isValid: %s\n' % solid.isValid())
    except Exception as e:
        f.write('Manual extrusion ERR: %s\n' % e)
        traceback.print_exc(file=f)
    f.flush()
    
    FreeCAD.closeDocument('T')
    f.write('\nDONE\n')
except Exception as e:
    f.write('FATAL: %s\n' % e)
    traceback.print_exc(file=f)
finally:
    f.flush()
    f.close()

sys.exit(0)
