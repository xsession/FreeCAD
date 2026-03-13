// SPDX-License-Identifier: LGPL-2.1-or-later
// ImpExpDxfWrite.cpp — DXF export (ImpExpDxfWrite) and ImpExpDxfRead::getStatsAsPyObject.
// Split from ImpExpDxf.cpp to work around MSVC 2019 internal compiler error (ICE)
// in the code generator (p2/main.c line 213) which crashes on large translation units.

#include <Standard_Version.hxx>
#if OCC_VERSION_HEX < 0x070600
# include <BRepAdaptor_HCurve.hxx>
#endif
#include <Approx_Curve3d.hxx>
#include <BRepAdaptor_Curve.hxx>
#include <BRep_Tool.hxx>
#include <GCPnts_UniformAbscissa.hxx>
#include <GeomAPI_PointsToBSpline.hxx>
#include <Geom_BSplineCurve.hxx>
#include <Geom_Circle.hxx>
#include <Geom_Ellipse.hxx>
#include <TColgp_Array1OfPnt.hxx>
#include <TColStd_Array1OfInteger.hxx>
#include <TColStd_Array1OfReal.hxx>
#include <TopExp.hxx>
#include <TopExp_Explorer.hxx>
#include <TopoDS.hxx>
#include <TopoDS_Edge.hxx>
#include <TopoDS_Vertex.hxx>
#include <Precision.hxx>
#include <gp_Circ.hxx>
#include <gp_Dir.hxx>
#include <gp_Elips.hxx>
#include <gp_Pnt.hxx>
#include <gp_Vec.hxx>

#ifndef _USE_MATH_DEFINES
#define _USE_MATH_DEFINES
#endif
#include <cmath>

#include <App/Application.h>
#include <App/Document.h>
#include <Base/Console.h>
#include <Base/Parameter.h>
#include <Base/Vector3D.h>

#include "ImpExpDxf.h"


using namespace Import;

#if OCC_VERSION_HEX >= 0x070600
using BRepAdaptor_HCurve = BRepAdaptor_Curve;
#endif


//******************************************************************************
// writing

void gPntToTuple(double result[3], gp_Pnt& p)
{
    result[0] = p.X();
    result[1] = p.Y();
    result[2] = p.Z();
}

point3D gPntTopoint3D(gp_Pnt& p)
{
    point3D result = {p.X(), p.Y(), p.Z()};
    return result;
}

ImpExpDxfWrite::ImpExpDxfWrite(std::string filepath)
    : CDxfWrite(filepath.c_str())
{
    setOptionSource("User parameter:BaseApp/Preferences/Mod/Draft");
    setOptions();
}

ImpExpDxfWrite::~ImpExpDxfWrite() = default;

void ImpExpDxfWrite::setOptions()
{
    ParameterGrp::handle hGrp = App::GetApplication().GetParameterGroupByPath(
        getOptionSource().c_str()
    );
    optionMaxLength = hGrp->GetFloat("maxsegmentlength", 5.0);
    optionExpPoints = hGrp->GetBool("ExportPoints", false);
    m_version = hGrp->GetInt("DxfVersionOut", 14);
    optionPolyLine = hGrp->GetBool("DiscretizeEllipses", false);
    m_polyOverride = hGrp->GetBool("DiscretizeEllipses", false);
    setDataDir(App::Application::getResourceDir() + "Mod/Import/DxfPlate/");
}

void ImpExpDxfWrite::exportShape(const TopoDS_Shape input)
{
    // export Edges
    TopExp_Explorer edges(input, TopAbs_EDGE);
    for (int i = 1; edges.More(); edges.Next(), i++) {
        const TopoDS_Edge& edge = TopoDS::Edge(edges.Current());
        BRepAdaptor_Curve adapt(edge);
        if (adapt.GetType() == GeomAbs_Circle) {
            double f = adapt.FirstParameter();
            double l = adapt.LastParameter();
            gp_Pnt start = adapt.Value(f);
            gp_Pnt e = adapt.Value(l);
            if (fabs(l - f) > 1.0 && start.SquareDistance(e) < 0.001) {
                exportCircle(adapt);
            }
            else {
                exportArc(adapt);
            }
        }
        else if (adapt.GetType() == GeomAbs_Ellipse) {
            double f = adapt.FirstParameter();
            double l = adapt.LastParameter();
            gp_Pnt start = adapt.Value(f);
            gp_Pnt e = adapt.Value(l);
            if (fabs(l - f) > 1.0 && start.SquareDistance(e) < 0.001) {
                if (m_polyOverride) {
                    if (m_version >= 14) {
                        exportLWPoly(adapt);
                    }
                    else {  // m_version < 14
                        exportPolyline(adapt);
                    }
                }
                else if (optionPolyLine) {
                    if (m_version >= 14) {
                        exportLWPoly(adapt);
                    }
                    else {  // m_version < 14
                        exportPolyline(adapt);
                    }
                }
                else {  // no overrides, do what's right!
                    if (m_version < 14) {
                        exportPolyline(adapt);
                    }
                    else {
                        exportEllipse(adapt);
                    }
                }
            }
            else {  // it's an arc
                if (m_polyOverride) {
                    if (m_version >= 14) {
                        exportLWPoly(adapt);
                    }
                    else {  // m_version < 14
                        exportPolyline(adapt);
                    }
                }
                else if (optionPolyLine) {
                    if (m_version >= 14) {
                        exportLWPoly(adapt);
                    }
                    else {  // m_version < 14
                        exportPolyline(adapt);
                    }
                }
                else {  // no overrides, do what's right!
                    if (m_version < 14) {
                        exportPolyline(adapt);
                    }
                    else {
                        exportEllipseArc(adapt);
                    }
                }
            }
        }
        else if (adapt.GetType() == GeomAbs_BSplineCurve) {
            if (m_polyOverride) {
                if (m_version >= 14) {
                    exportLWPoly(adapt);
                }
                else {  // m_version < 14
                    exportPolyline(adapt);
                }
            }
            else if (optionPolyLine) {
                if (m_version >= 14) {
                    exportLWPoly(adapt);
                }
                else {  // m_version < 14
                    exportPolyline(adapt);
                }
            }
            else {  // no overrides, do what's right!
                if (m_version < 14) {
                    exportPolyline(adapt);
                }
                else {
                    exportBSpline(adapt);
                }
            }
        }
        else if (adapt.GetType() == GeomAbs_BezierCurve) {
            exportBCurve(adapt);
        }
        else if (adapt.GetType() == GeomAbs_Line) {
            exportLine(adapt);
        }
        else {
            Base::Console().warning(
                "ImpExpDxf - unknown curve type: %d\n",
                static_cast<int>(adapt.GetType())
            );
        }
    }

    if (optionExpPoints) {
        TopExp_Explorer verts(input, TopAbs_VERTEX);
        std::vector<gp_Pnt> duplicates;
        for (int i = 1; verts.More(); verts.Next(), i++) {
            const TopoDS_Vertex& v = TopoDS::Vertex(verts.Current());
            gp_Pnt p = BRep_Tool::Pnt(v);
            duplicates.push_back(p);
        }

        std::sort(duplicates.begin(), duplicates.end(), ImpExpDxfWrite::gp_PntCompare);
        auto newEnd = std::unique(duplicates.begin(), duplicates.end(), ImpExpDxfWrite::gp_PntEqual);
        std::vector<gp_Pnt> uniquePts(duplicates.begin(), newEnd);
        for (auto& p : uniquePts) {
            double point[3] = {0, 0, 0};
            gPntToTuple(point, p);
            writePoint(point);
        }
    }
}

bool ImpExpDxfWrite::gp_PntEqual(gp_Pnt p1, gp_Pnt p2)
{
    bool result = false;
    if (p1.IsEqual(p2, Precision::Confusion())) {
        result = true;
    }
    return result;
}

// is p1 "less than" p2?
bool ImpExpDxfWrite::gp_PntCompare(gp_Pnt p1, gp_Pnt p2)
{
    bool result = false;
    if (!(p1.IsEqual(p2, Precision::Confusion()))) {              // ie v1 != v2
        if (!(fabs(p1.X() - p2.X()) < Precision::Confusion())) {  // x1 != x2
            result = p1.X() < p2.X();
        }
        else if (!(fabs(p1.Y() - p2.Y()) < Precision::Confusion())) {  // y1 != y2
            result = p1.Y() < p2.Y();
        }
        else {
            result = p1.Z() < p2.Z();
        }
    }
    return result;
}


void ImpExpDxfWrite::exportCircle(BRepAdaptor_Curve& c)
{
    gp_Circ circ = c.Circle();
    gp_Pnt p = circ.Location();
    double center[3] = {0, 0, 0};
    gPntToTuple(center, p);

    double radius = circ.Radius();

    writeCircle(center, radius);
}

void ImpExpDxfWrite::exportEllipse(BRepAdaptor_Curve& c)
{
    gp_Elips ellp = c.Ellipse();
    gp_Pnt p = ellp.Location();
    double center[3] = {0, 0, 0};
    gPntToTuple(center, p);

    double major = ellp.MajorRadius();
    double minor = ellp.MinorRadius();

    gp_Dir xaxis = ellp.XAxis().Direction();  // direction of major axis
    // rotation appears to be the clockwise(?) angle between major & +Y??
    double rotation = xaxis.AngleWithRef(gp_Dir(0, 1, 0), gp_Dir(0, 0, 1));

    // 2*pi = 6.28319 is invalid(doesn't display in LibreCAD), but 2PI = 6.28318 is valid!
    // writeEllipse(center, major, minor, rotation, 0.0, 2 * std::numbers::pi, true );
    writeEllipse(center, major, minor, rotation, 0.0, 6.28318, true);
}

void ImpExpDxfWrite::exportArc(BRepAdaptor_Curve& c)
{
    gp_Circ circ = c.Circle();
    gp_Pnt p = circ.Location();
    double center[3] = {0, 0, 0};
    gPntToTuple(center, p);

    double f = c.FirstParameter();
    double l = c.LastParameter();
    gp_Pnt s = c.Value(f);
    double start[3];
    gPntToTuple(start, s);
    gp_Pnt m = c.Value((l + f) / 2.0);
    gp_Pnt e = c.Value(l);
    double end[3] = {0, 0, 0};
    gPntToTuple(end, e);

    gp_Vec v1(m, s);
    gp_Vec v2(m, e);
    gp_Vec v3(0, 0, 1);
    double a = v3.DotCross(v1, v2);

    bool dir = (a < 0) ? true : false;
    writeArc(start, end, center, dir);
}

void ImpExpDxfWrite::exportEllipseArc(BRepAdaptor_Curve& c)
{
    gp_Elips ellp = c.Ellipse();
    gp_Pnt p = ellp.Location();
    double center[3] = {0, 0, 0};
    gPntToTuple(center, p);

    double major = ellp.MajorRadius();
    double minor = ellp.MinorRadius();

    gp_Dir xaxis = ellp.XAxis().Direction();  // direction of major axis
    // rotation appears to be the clockwise angle between major & +Y??
    double rotation = xaxis.AngleWithRef(gp_Dir(0, 1, 0), gp_Dir(0, 0, 1));

    double f = c.FirstParameter();
    double l = c.LastParameter();
    gp_Pnt s = c.Value(f);
    gp_Pnt m = c.Value((l + f) / 2.0);
    gp_Pnt e = c.Value(l);

    gp_Vec v1(m, s);
    gp_Vec v2(m, e);
    gp_Vec v3(0, 0, 1);
    double a = v3.DotCross(v1, v2);  // a = v3 dot (v1 cross v2)
                                     // relates to "handedness" of 3 vectors
                                     // a > 0 ==> v2 is CCW from v1 (righthanded)?
                                     // a < 0 ==> v2 is CW from v1 (lefthanded)?

    double startAngle = fmod(f, 2.0 * M_PI);  // revolutions
    double endAngle = fmod(l, 2.0 * M_PI);
    bool endIsCW = (a < 0) ? true : false;  // if !endIsCW swap(start,end)
    // not sure if this is a hack or not. seems to make valid arcs.
    if (!endIsCW) {
        startAngle = -startAngle;
        endAngle = -endAngle;
    }

    writeEllipse(center, major, minor, rotation, startAngle, endAngle, endIsCW);
}

void ImpExpDxfWrite::exportBSpline(BRepAdaptor_Curve& c)
{
    SplineDataOut sd;
    Handle(Geom_BSplineCurve) spline;
    double f, l;
    gp_Pnt s, ePt;

    Standard_Real tol3D = 0.001;
    Standard_Integer maxDegree = 3, maxSegment = 200;
    Handle(BRepAdaptor_HCurve) hCurve = new BRepAdaptor_HCurve(c);
    Approx_Curve3d approx(hCurve, tol3D, GeomAbs_C0, maxSegment, maxDegree);
    if (approx.IsDone() && approx.HasResult()) {
        spline = approx.Curve();
    }
    else {
        if (approx.HasResult()) {  // result, but not within tolerance
            spline = approx.Curve();
            Base::Console().message("DxfWrite::exportBSpline - result not within tolerance\n");
        }
        else {
            f = c.FirstParameter();
            l = c.LastParameter();
            s = c.Value(f);
            ePt = c.Value(l);
            Base::Console().message(
                "DxfWrite::exportBSpline - no result- from:(%.3f,%.3f) to:(%.3f,%.3f)\n",
                s.X(),
                s.Y(),
                ePt.X(),
                ePt.Y()
            );
            TColgp_Array1OfPnt controlPoints(0, 1);
            controlPoints.SetValue(0, s);
            controlPoints.SetValue(1, ePt);
            spline = GeomAPI_PointsToBSpline(controlPoints, 1).Curve();
        }
    }
    // WF? norm of surface containing curve??
    sd.norm.x = 0.0;
    sd.norm.y = 0.0;
    sd.norm.z = 1.0;

    sd.flag = spline->IsClosed();
    sd.flag += spline->IsPeriodic() * 2;
    sd.flag += spline->IsRational() * 4;
    sd.flag += 8;  // planar spline

    sd.degree = spline->Degree();
    sd.control_points = spline->NbPoles();
    sd.knots = spline->NbKnots();
    gp_Pnt pt;
    spline->D0(spline->FirstParameter(), pt);
    sd.starttan = gPntTopoint3D(pt);
    spline->D0(spline->LastParameter(), pt);
    sd.endtan = gPntTopoint3D(pt);

    // next bit is from DrawingExport.cpp (Dan Falk?).
    Standard_Integer m = 0;
    if (spline->IsPeriodic()) {
        m = spline->NbPoles() + 2 * spline->Degree() - spline->Multiplicity(1) + 2;
    }
    else {
        for (int i = 1; i <= spline->NbKnots(); i++) {
            m += spline->Multiplicity(i);
        }
    }
    TColStd_Array1OfReal knotsequence(1, m);
    spline->KnotSequence(knotsequence);
    for (int i = knotsequence.Lower(); i <= knotsequence.Upper(); i++) {
        sd.knot.push_back(knotsequence(i));
    }
    sd.knots = knotsequence.Length();

    TColgp_Array1OfPnt poles(1, spline->NbPoles());
    spline->Poles(poles);
    for (int i = poles.Lower(); i <= poles.Upper(); i++) {
        sd.control.push_back(gPntTopoint3D(poles(i)));
    }
    // OCC doesn't have separate lists for control points and fit points.

    writeSpline(sd);
}

void ImpExpDxfWrite::exportBCurve(BRepAdaptor_Curve& c)
{
    (void)c;
    Base::Console().message("BCurve dxf export not yet supported\n");
}

void ImpExpDxfWrite::exportLine(BRepAdaptor_Curve& c)
{
    double f = c.FirstParameter();
    double l = c.LastParameter();
    gp_Pnt s = c.Value(f);
    double start[3] = {0, 0, 0};
    gPntToTuple(start, s);
    gp_Pnt e = c.Value(l);
    double end[3] = {0, 0, 0};
    gPntToTuple(end, e);
    writeLine(start, end);
}

// Helper function to discretize a curve into polyline vertices
// Returns true if discretization was successful and pd was populated
bool ImpExpDxfWrite::discretizeCurveToPolyline(BRepAdaptor_Curve& c, LWPolyDataOut& pd) const
{
    pd.Flag = c.IsClosed();
    pd.Elev = 0.0;
    pd.Thick = 0.0;
    pd.Extr.x = 0.0;
    pd.Extr.y = 0.0;
    pd.Extr.z = 1.0;
    pd.nVert = 0;

    GCPnts_UniformAbscissa discretizer;
    discretizer.Initialize(c, optionMaxLength);

    if (!discretizer.IsDone() || discretizer.NbPoints() <= 0) {
        return false;
    }

    int nbPoints = discretizer.NbPoints();
    // for closed curves, don't include the last point if it duplicates the first
    int endIndex = nbPoints;
    if (pd.Flag && nbPoints > 1) {
        gp_Pnt pFirst = c.Value(discretizer.Parameter(1));
        gp_Pnt pLast = c.Value(discretizer.Parameter(nbPoints));
        if (pFirst.Distance(pLast) < Precision::Confusion()) {
            endIndex = nbPoints - 1;
        }
    }

    for (int i = 1; i <= endIndex; i++) {
        gp_Pnt p = c.Value(discretizer.Parameter(i));
        pd.Verts.push_back(gPntTopoint3D(p));
    }
    pd.nVert = static_cast<int>(pd.Verts.size());

    return true;
}

void ImpExpDxfWrite::exportLWPoly(BRepAdaptor_Curve& c)
{
    LWPolyDataOut pd;
    if (discretizeCurveToPolyline(c, pd)) {
        writeLWPolyLine(pd);
    }
}

void ImpExpDxfWrite::exportPolyline(BRepAdaptor_Curve& c)
{
    LWPolyDataOut pd;
    if (discretizeCurveToPolyline(c, pd)) {
        writePolyline(pd);
    }
}

void ImpExpDxfWrite::exportText(
    const char* text,
    Base::Vector3d position1,
    Base::Vector3d position2,
    double size,
    int just
)
{
    double location1[3] = {0, 0, 0};
    location1[0] = position1.x;
    location1[1] = position1.y;
    location1[2] = position1.z;
    double location2[3] = {0, 0, 0};
    location2[0] = position2.x;
    location2[1] = position2.y;
    location2[2] = position2.z;

    writeText(text, location1, location2, size, just);
}

void ImpExpDxfWrite::exportLinearDim(
    Base::Vector3d textLocn,
    Base::Vector3d lineLocn,
    Base::Vector3d extLine1Start,
    Base::Vector3d extLine2Start,
    char* dimText,
    int type
)
{
    double text[3] = {0, 0, 0};
    text[0] = textLocn.x;
    text[1] = textLocn.y;
    text[2] = textLocn.z;
    double line[3] = {0, 0, 0};
    line[0] = lineLocn.x;
    line[1] = lineLocn.y;
    line[2] = lineLocn.z;
    double ext1[3] = {0, 0, 0};
    ext1[0] = extLine1Start.x;
    ext1[1] = extLine1Start.y;
    ext1[2] = extLine1Start.z;
    double ext2[3] = {0, 0, 0};
    ext2[0] = extLine2Start.x;
    ext2[1] = extLine2Start.y;
    ext2[2] = extLine2Start.z;
    writeLinearDim(text, line, ext1, ext2, dimText, type);
}

void ImpExpDxfWrite::exportAngularDim(
    Base::Vector3d textLocn,
    Base::Vector3d lineLocn,
    Base::Vector3d extLine1End,
    Base::Vector3d extLine2End,
    Base::Vector3d apexPoint,
    char* dimText
)
{
    double text[3] = {0, 0, 0};
    text[0] = textLocn.x;
    text[1] = textLocn.y;
    text[2] = textLocn.z;
    double line[3] = {0, 0, 0};
    line[0] = lineLocn.x;
    line[1] = lineLocn.y;
    line[2] = lineLocn.z;
    double ext1[3] = {0, 0, 0};
    ext1[0] = extLine1End.x;
    ext1[1] = extLine1End.y;
    ext1[2] = extLine1End.z;
    double ext2[3] = {0, 0, 0};
    ext2[0] = extLine2End.x;
    ext2[1] = extLine2End.y;
    ext2[2] = extLine2End.z;
    double apex[3] = {0, 0, 0};
    apex[0] = apexPoint.x;
    apex[1] = apexPoint.y;
    apex[2] = apexPoint.z;
    writeAngularDim(text, line, apex, ext1, apex, ext2, dimText);
}

void ImpExpDxfWrite::exportRadialDim(
    Base::Vector3d centerPoint,
    Base::Vector3d textLocn,
    Base::Vector3d arcPoint,
    char* dimText
)
{
    double center[3] = {0, 0, 0};
    center[0] = centerPoint.x;
    center[1] = centerPoint.y;
    center[2] = centerPoint.z;
    double text[3] = {0, 0, 0};
    text[0] = textLocn.x;
    text[1] = textLocn.y;
    text[2] = textLocn.z;
    double arc[3] = {0, 0, 0};
    arc[0] = arcPoint.x;
    arc[1] = arcPoint.y;
    arc[2] = arcPoint.z;
    writeRadialDim(center, text, arc, dimText);
}

void ImpExpDxfWrite::exportDiametricDim(
    Base::Vector3d textLocn,
    Base::Vector3d arcPoint1,
    Base::Vector3d arcPoint2,
    char* dimText
)
{
    double text[3] = {0, 0, 0};
    text[0] = textLocn.x;
    text[1] = textLocn.y;
    text[2] = textLocn.z;
    double arc1[3] = {0, 0, 0};
    arc1[0] = arcPoint1.x;
    arc1[1] = arcPoint1.y;
    arc1[2] = arcPoint1.z;
    double arc2[3] = {0, 0, 0};
    arc2[0] = arcPoint2.x;
    arc2[1] = arcPoint2.y;
    arc2[2] = arcPoint2.z;
    writeDiametricDim(text, arc1, arc2, dimText);
}

Py::Object ImpExpDxfRead::getStatsAsPyObject()
{
    // Create a Python dictionary to hold all import statistics.
    Py::Dict statsDict;

    // Populate the dictionary with general information about the import.
    statsDict.setItem("dxfVersion", Py::String(m_stats.dxfVersion));
    statsDict.setItem("dxfEncoding", Py::String(m_stats.dxfEncoding));
    statsDict.setItem("scalingSource", Py::String(m_stats.scalingSource));
    statsDict.setItem("fileUnits", Py::String(m_stats.fileUnits));
    statsDict.setItem("finalScalingFactor", Py::Float(m_stats.finalScalingFactor));
    statsDict.setItem("importTimeSeconds", Py::Float(m_stats.importTimeSeconds));
    statsDict.setItem("totalEntitiesCreated", Py::Long(m_stats.totalEntitiesCreated));

    // Create a nested dictionary for the counts of each DXF entity type read.
    Py::Dict entityCountsDict;
    for (const auto& pair : m_stats.entityCounts) {
        entityCountsDict.setItem(pair.first.c_str(), Py::Long(pair.second));
    }
    statsDict.setItem("entityCounts", entityCountsDict);

    // Create a nested dictionary for the import settings used for this session.
    Py::Dict importSettingsDict;
    for (const auto& pair : m_stats.importSettings) {
        importSettingsDict.setItem(pair.first.c_str(), Py::String(pair.second));
    }
    statsDict.setItem("importSettings", importSettingsDict);

    // Create a nested dictionary for any unsupported DXF features encountered.
    Py::Dict unsupportedFeaturesDict;
    for (const auto& pair : m_stats.unsupportedFeatures) {
        Py::List occurrencesList;
        for (const auto& occurrence : pair.second) {
            Py::Tuple infoTuple(2);
            infoTuple.setItem(0, Py::Long(occurrence.first));
            infoTuple.setItem(1, Py::String(occurrence.second));
            occurrencesList.append(infoTuple);
        }
        unsupportedFeaturesDict.setItem(pair.first.c_str(), occurrencesList);
    }
    statsDict.setItem("unsupportedFeatures", unsupportedFeaturesDict);

    // Create a nested dictionary for the counts of system blocks encountered.
    Py::Dict systemBlockCountsDict;
    for (const auto& pair : m_stats.systemBlockCounts) {
        systemBlockCountsDict.setItem(pair.first.c_str(), Py::Long(pair.second));
    }
    statsDict.setItem("systemBlockCounts", systemBlockCountsDict);

    // Return the fully populated statistics dictionary to the Python caller.
    return statsDict;
}
