import FreeCAD, Part, Sketcher, PartDesign
doc=FreeCAD.newDocument('T')
body=doc.addObject('PartDesign::Body','Body')
sk=doc.addObject('Sketcher::SketchObject','Sketch')
body.addObject(sk)
sk.AttachmentSupport=[(doc.getObject('XY_Plane'),'')]
sk.MapMode='FlatFace'
sk.addGeometry(Part.LineSegment(FreeCAD.Vector(0,0,0),FreeCAD.Vector(10,0,0)),False)
sk.addGeometry(Part.LineSegment(FreeCAD.Vector(10,0,0),FreeCAD.Vector(10,10,0)),False)
sk.addGeometry(Part.LineSegment(FreeCAD.Vector(10,10,0),FreeCAD.Vector(0,10,0)),False)
sk.addGeometry(Part.LineSegment(FreeCAD.Vector(0,10,0),FreeCAD.Vector(0,0,0)),False)
doc.recompute()
pad=doc.addObject('PartDesign::Pad','Pad')
body.addObject(pad)
pad.Profile=sk
pad.Length=10.0
doc.recompute()
s=pad.Shape
print('TYPE:',s.ShapeType)
print('FACES:',len(s.Faces))
print('COUNT_FACE:',s.countElement('Face'))
print('COUNT_EDGE:',s.countElement('Edge'))
print('COUNT_VERT:',s.countElement('Vertex'))
print('MAPSIZE:',s.ElementMapSize)
print('TAG:',s.Tag)
print('VALID:',s.isValid())
for i in range(1,7):
    try:
        sub=s.getSubShape('Face%d'%i)
        print('GETSUB Face%d: type=%s area=%.1f'%(i,sub.ShapeType,sub.Area))
    except Exception as e:
        print('GETSUB Face%d: ERR %s'%(i,e))
for i in range(1,7):
    try:
        sub=Part.getShape(pad,'Face%d'%i,needSubElement=True)
        print('GETSHAPE Face%d: null=%s'%(i,sub.isNull()))
    except Exception as e:
        print('GETSHAPE Face%d: ERR %s'%(i,e))
for i in range(1,7):
    try:
        sub=Part.getShape(pad,'Face%d'%i,needSubElement=True,noElementMap=True)
        print('NOMAP Face%d: null=%s'%(i,sub.isNull()))
    except Exception as e:
        print('NOMAP Face%d: ERR %s'%(i,e))
box=Part.makeBox(10,10,10)
print('BOX_FACES:',len(box.Faces))
print('BOX_COUNT:',box.countElement('Face'))
try:
    sub=box.getSubShape('Face1')
    print('BOX_GETSUB: type=%s'%sub.ShapeType)
except Exception as e:
    print('BOX_GETSUB: ERR %s'%e)
FreeCAD.closeDocument('T')
exit()
