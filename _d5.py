import sys, traceback
f = open(r'C:\GIT\FreeCAD\_pyout4.txt', 'w')
try:
    import FreeCAD, Part
    
    # Test 1: Simple box
    box = Part.makeBox(10, 10, 10)
    f.write('=== Box ===\n')
    f.write('ShapeType: %s\n' % box.ShapeType)
    f.write('isNull: %s\n' % box.isNull())
    f.write('isValid: %s\n' % box.isValid())
    f.write('len(Faces): %d\n' % len(box.Faces))
    f.write('len(Edges): %d\n' % len(box.Edges))
    f.write('countElement("Face"): %d\n' % box.countElement('Face'))
    f.write('countElement("Edge"): %d\n' % box.countElement('Edge'))
    f.write('countElement("Vertex"): %d\n' % box.countElement('Vertex'))
    f.write('Tag: %d\n' % box.Tag)
    f.write('ElementMapSize: %d\n' % box.ElementMapSize)
    f.flush()
    
    # Test 2: hasSubShape
    for i in range(1, 7):
        try:
            f.write('hasSubShape("Face%d"): %s\n' % (i, box.hasSubShape('Face%d' % i)))
        except Exception as e:
            f.write('hasSubShape("Face%d"): ERR %s\n' % (i, e))
    f.flush()
    
    # Test 3: getSubShape (inherited from TopoShapeSolidPy or similar?)
    try:
        f.write('\ndir with "sub": %s\n' % [x for x in dir(box) if 'sub' in x.lower() or 'Sub' in x])
    except:
        pass
    f.flush()
    
    # Test 4: countSubShapes via internal method
    try:
        f.write('\ncountSubShapes("Face"): ')
        result = box.countSubShapes('Face')
        f.write('%d\n' % result)
    except Exception as e:
        f.write('ERR %s\n' % e)
    f.flush()
    
    # Test 5: Try Part.getShape on a Part.Feature
    f.write('\n=== Part.Feature test ===\n')
    doc = FreeCAD.newDocument('T')
    feat = doc.addObject('Part::Feature', 'Box')
    feat.Shape = box
    doc.recompute()
    f.write('Feature.Shape.ShapeType: %s\n' % feat.Shape.ShapeType)
    f.write('Feature.Shape.len(Faces): %d\n' % len(feat.Shape.Faces))
    f.write('Feature.Shape.countElement("Face"): %d\n' % feat.Shape.countElement('Face'))
    f.flush()
    
    for i in range(1, 7):
        try:
            sub = Part.getShape(feat, 'Face%d' % i, needSubElement=True)
            f.write('getShape Face%d: null=%s\n' % (i, sub.isNull()))
        except Exception as e:
            f.write('getShape Face%d: ERR %s\n' % (i, e))
    f.flush()
    
    # Test 6: getSubObject on the feature
    for i in range(1, 7):
        try:
            obj = feat.getSubObject('Face%d' % i)
            if obj is not None:
                f.write('getSubObject Face%d: type=%s\n' % (i, obj.ShapeType))
            else:
                f.write('getSubObject Face%d: None\n' % i)
        except Exception as e:
            f.write('getSubObject Face%d: ERR %s\n' % (i, e))
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
