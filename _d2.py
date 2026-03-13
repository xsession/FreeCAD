import sys, traceback
f = open(r'C:\GIT\FreeCAD\_pyout.txt', 'w')
try:
    f.write('STEP1: imports\n')
    f.flush()
    import FreeCAD, Part
    f.write('STEP2: FreeCAD+Part imported OK\n')
    f.flush()
    
    f.write('STEP3: makeBox\n')
    f.flush()
    try:
        b = Part.makeBox(10, 10, 10)
        f.write('BOX OK: type=%s faces=%d\n' % (b.ShapeType, len(b.Faces)))
    except Exception as e:
        f.write('BOX ERR: %s\n' % e)
        traceback.print_exc(file=f)
    f.flush()
    
    f.write('STEP4: newDocument\n')
    f.flush()
    try:
        doc = FreeCAD.newDocument('T')
        f.write('DOC OK\n')
    except Exception as e:
        f.write('DOC ERR: %s\n' % e)
        traceback.print_exc(file=f)
    f.flush()
    
    f.write('STEP5: create body+sketch\n')
    f.flush()
    try:
        import Sketcher, PartDesign
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
        f.write('SKETCH OK\n')
    except Exception as e:
        f.write('SKETCH ERR: %s\n' % e)
        traceback.print_exc(file=f)
    f.flush()
    
    f.write('STEP6: create pad\n')
    f.flush()
    try:
        pad = doc.addObject('PartDesign::Pad', 'Pad')
        body.addObject(pad)
        pad.Profile = sk
        pad.Length = 10.0
        doc.recompute()
        f.write('PAD OK, valid=%s\n' % pad.Shape.isValid())
    except Exception as e:
        f.write('PAD ERR: %s\n' % e)
        traceback.print_exc(file=f)
    f.flush()
    
    f.write('STEP7: shape info\n')
    f.flush()
    try:
        s = pad.Shape
        f.write('ShapeType=%s\n' % s.ShapeType)
        f.write('Faces=%d\n' % len(s.Faces))
        f.write('countElement(Face)=%d\n' % s.countElement('Face'))
        f.write('ElementMapSize=%d\n' % s.ElementMapSize)
        f.write('Tag=%d\n' % s.Tag)
    except Exception as e:
        f.write('SHAPE ERR: %s\n' % e)
        traceback.print_exc(file=f)
    f.flush()
    
    f.write('STEP8: getSubShape\n')
    f.flush()
    for i in range(1, 7):
        try:
            sub = s.getSubShape('Face%d' % i)
            f.write('getSubShape Face%d: type=%s area=%.1f\n' % (i, sub.ShapeType, sub.Area))
        except Exception as e:
            f.write('getSubShape Face%d: ERR %s\n' % (i, e))
    f.flush()
    
    f.write('STEP9: Part.getShape needSubElement\n')
    f.flush()
    for i in range(1, 7):
        try:
            sub = Part.getShape(pad, 'Face%d' % i, needSubElement=True)
            f.write('getShape Face%d: null=%s type=%s\n' % (i, sub.isNull(), sub.ShapeType if not sub.isNull() else 'N/A'))
        except Exception as e:
            f.write('getShape Face%d: ERR %s\n' % (i, e))
    f.flush()
    
    f.write('STEP10: Part.getShape noElementMap\n')
    f.flush()
    for i in range(1, 7):
        try:
            sub = Part.getShape(pad, 'Face%d' % i, needSubElement=True, noElementMap=True)
            f.write('noMap Face%d: null=%s type=%s\n' % (i, sub.isNull(), sub.ShapeType if not sub.isNull() else 'N/A'))
        except Exception as e:
            f.write('noMap Face%d: ERR %s\n' % (i, e))
    f.flush()
    
    f.write('STEP11: getSubObject\n')
    f.flush()
    for i in range(1, 7):
        try:
            obj = pad.getSubObject('Face%d' % i)
            if obj is not None:
                f.write('getSubObject Face%d: type=%s\n' % (i, obj.ShapeType))
            else:
                f.write('getSubObject Face%d: None\n' % i)
        except Exception as e:
            f.write('getSubObject Face%d: ERR %s\n' % (i, e))
    f.flush()
    
    f.write('STEP12: getMappedName\n')
    f.flush()
    try:
        for i in range(1, 7):
            mn = s.getElementMappedName('Face%d' % i)
            f.write('MappedName Face%d: %s\n' % (i, repr(mn)))
    except Exception as e:
        f.write('MAPPED ERR: %s\n' % e)
        traceback.print_exc(file=f)
    f.flush()
    
    f.write('STEP13: ElementMap entries\n')
    f.flush()
    try:
        emap = s.ElementMap
        f.write('ElementMap len=%d\n' % len(emap))
        for k, v in list(emap.items())[:10]:
            f.write('  %s -> %s\n' % (repr(k), repr(v)))
    except Exception as e:
        f.write('EMAP ERR: %s\n' % e)
        traceback.print_exc(file=f)
    f.flush()
    
    f.write('STEP14: cleanup\n')
    FreeCAD.closeDocument('T')
    f.write('DONE\n')
except Exception as e:
    f.write('FATAL: %s\n' % e)
    traceback.print_exc(file=f)
finally:
    f.flush()
    f.close()

sys.exit(0)
