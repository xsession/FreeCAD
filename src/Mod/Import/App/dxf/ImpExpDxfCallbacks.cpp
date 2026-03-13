// SPDX-License-Identifier: LGPL-2.1-or-later
// ImpExpDxfCallbacks.cpp — OnRead* callbacks, DrawingEntityCollector, and Layer methods.
// Split from ImpExpDxf.cpp to improve code organization.

#include <Standard_Version.hxx>
#if OCC_VERSION_HEX < 0x070600
# include <BRepAdaptor_HCurve.hxx>
#endif
#include <Approx_Curve3d.hxx>
#include <BRepAdaptor_Curve.hxx>
#include <BRepBuilderAPI_MakeEdge.hxx>
#include <BRepBuilderAPI_MakeVertex.hxx>
#include <BRep_Tool.hxx>
#include <GeomAPI_Interpolate.hxx>
#include <GeomAPI_PointsToBSpline.hxx>
#include <Geom_BSplineCurve.hxx>
#include <Geom_Circle.hxx>
#include <Geom_Ellipse.hxx>
#include <TColgp_Array1OfPnt.hxx>
#include <TColgp_HArray1OfPnt.hxx>
#include <TColStd_Array1OfInteger.hxx>
#include <TColStd_Array1OfReal.hxx>
#include <TopExp.hxx>
#include <TopoDS.hxx>
#include <TopoDS_Edge.hxx>
#include <TopoDS_Vertex.hxx>
#include <TopoDS_Wire.hxx>
#include <Precision.hxx>
#include <gp_Ax1.hxx>
#include <gp_Ax2.hxx>
#include <gp_Circ.hxx>
#include <gp_Dir.hxx>
#include <gp_Elips.hxx>
#include <gp_Pnt.hxx>

#include <App/Application.h>
#include <App/Document.h>
#include <App/DocumentObjectPy.h>
#include <App/FeaturePython.h>
#include <App/FeaturePythonPyImp.h>
#include <App/Link.h>
#include <App/PropertyUnits.h>
#include <Base/Console.h>
#include <Base/Matrix.h>
#include <Base/Parameter.h>
#include <Base/Placement.h>
#include <Base/Tools.h>
#include <Base/Vector3D.h>
#include <Mod/Part/App/PartFeature.h>
#include <Mod/Part/App/FeatureCompound.h>
#include <Mod/Part/App/PrimitiveFeature.h>
#include <Mod/Part/App/FeaturePartCircle.h>

#include "ImpExpDxf.h"
#include "ImpExpDxfHelpers.h"


using namespace Import;
using namespace Import::detail;

#if OCC_VERSION_HEX >= 0x070600
using BRepAdaptor_HCurve = BRepAdaptor_Curve;
#endif


// Helper to map the current import mode to a PrimitiveType for entity callbacks.
ImpExpDxfRead::GeometryBuilder::PrimitiveType
ImpExpDxfRead::mapImportModeToPrimitiveType(GeometryBuilder::PrimitiveType editableType) const
{
    if (m_importMode == ImportMode::EditableDraft
        || m_importMode == ImportMode::EditablePrimitives) {
        return editableType;
    }
    return GeometryBuilder::PrimitiveType::None;
}

void ImpExpDxfRead::OnReadLine(const Base::Vector3d& start, const Base::Vector3d& end, bool /*hidden*/)
{
    if (shouldSkipEntity()) {
        return;
    }

    gp_Pnt p0 = makePoint(start);
    gp_Pnt p1 = makePoint(end);
    if (p0.IsEqual(p1, 1e-8)) {
        return;
    }
    TopoDS_Edge edge = BRepBuilderAPI_MakeEdge(p0, p1).Edge();
    GeometryBuilder builder(edge);
    builder.type = mapImportModeToPrimitiveType(GeometryBuilder::PrimitiveType::Line);
    Collector->AddGeometry(builder);
}


void ImpExpDxfRead::OnReadPoint(const Base::Vector3d& start)
{
    if (shouldSkipEntity()) {
        return;
    }
    TopoDS_Vertex vertex = BRepBuilderAPI_MakeVertex(makePoint(start)).Vertex();
    GeometryBuilder builder(vertex);
    builder.type = mapImportModeToPrimitiveType(GeometryBuilder::PrimitiveType::Point);
    Collector->AddGeometry(builder);
}


void ImpExpDxfRead::OnReadArc(
    const Base::Vector3d& start,
    const Base::Vector3d& end,
    const Base::Vector3d& center,
    bool dir,
    bool /*hidden*/
)
{
    if (shouldSkipEntity()) {
        return;
    }

    gp_Pnt p0 = makePoint(start);
    gp_Pnt p1 = makePoint(end);
    gp_Dir up(0, 0, 1);
    if (!dir) {
        up.Reverse();
    }
    gp_Pnt pc = makePoint(center);
    gp_Circ circle(gp_Ax2(pc, up), p0.Distance(pc));
    if (circle.Radius() < 1e-9) {
        Base::Console().warning("ImpExpDxf - ignore degenerate arc of circle\n");
        return;
    }

    TopoDS_Edge edge = BRepBuilderAPI_MakeEdge(circle, p0, p1).Edge();
    GeometryBuilder builder(edge);
    builder.type = mapImportModeToPrimitiveType(GeometryBuilder::PrimitiveType::Arc);
    Collector->AddGeometry(builder);
}


void ImpExpDxfRead::OnReadCircle(const Base::Vector3d& start, const Base::Vector3d& center, bool dir, bool /*hidden*/)
{
    if (shouldSkipEntity()) {
        return;
    }

    gp_Pnt p0 = makePoint(start);
    gp_Dir up(0, 0, 1);
    if (!dir) {
        up.Reverse();
    }
    gp_Pnt pc = makePoint(center);
    gp_Circ circle(gp_Ax2(pc, up), p0.Distance(pc));
    if (circle.Radius() < 1e-9) {
        Base::Console().warning("ImpExpDxf - ignore degenerate circle\n");
        return;
    }

    TopoDS_Edge edge = BRepBuilderAPI_MakeEdge(circle).Edge();
    GeometryBuilder builder(edge);
    builder.type = mapImportModeToPrimitiveType(GeometryBuilder::PrimitiveType::Circle);
    Collector->AddGeometry(builder);
}


namespace
{

Handle(Geom_BSplineCurve) getSplineFromPolesAndKnots(struct SplineData& sd)
{
    std::size_t numPoles = sd.control_points;
    if (sd.controlx.size() > numPoles || sd.controly.size() > numPoles
        || sd.controlz.size() > numPoles || sd.weight.size() > numPoles) {
        return nullptr;
    }

    // handle the poles
    TColgp_Array1OfPnt occpoles(1, sd.control_points);
    int index = 1;
    for (auto coordinate : sd.controlx) {
        occpoles(index++).SetX(coordinate);
    }

    index = 1;
    for (auto coordinate : sd.controly) {
        occpoles(index++).SetY(coordinate);
    }

    index = 1;
    for (auto coordinate : sd.controlz) {
        occpoles(index++).SetZ(coordinate);
    }

    // handle knots and mults
    std::set<double> unique;
    unique.insert(sd.knot.begin(), sd.knot.end());

    int numKnots = int(unique.size());
    TColStd_Array1OfInteger occmults(1, numKnots);
    TColStd_Array1OfReal occknots(1, numKnots);
    index = 1;
    for (auto knot : unique) {
        occknots(index) = knot;
        occmults(index) = (int)std::count(sd.knot.begin(), sd.knot.end(), knot);
        index++;
    }

    // handle weights
    TColStd_Array1OfReal occweights(1, sd.control_points);
    if (sd.weight.size() == std::size_t(sd.control_points)) {
        index = 1;
        for (auto weight : sd.weight) {
            occweights(index++) = weight;
        }
    }
    else {
        // non-rational
        for (int i = occweights.Lower(); i <= occweights.Upper(); i++) {
            occweights(i) = 1.0;
        }
    }

    Standard_Boolean periodic = sd.flag == 2;
    Handle(Geom_BSplineCurve) geom
        = new Geom_BSplineCurve(occpoles, occweights, occknots, occmults, sd.degree, periodic);
    return geom;
}

Handle(Geom_BSplineCurve) getInterpolationSpline(struct SplineData& sd)
{
    std::size_t numPoints = sd.fit_points;
    if (sd.fitx.size() > numPoints || sd.fity.size() > numPoints || sd.fitz.size() > numPoints) {
        return nullptr;
    }

    // handle the poles
    Handle(TColgp_HArray1OfPnt) fitpoints = new TColgp_HArray1OfPnt(1, sd.fit_points);
    int index = 1;
    for (auto coordinate : sd.fitx) {
        fitpoints->ChangeValue(index++).SetX(coordinate);
    }

    index = 1;
    for (auto coordinate : sd.fity) {
        fitpoints->ChangeValue(index++).SetY(coordinate);
    }

    index = 1;
    for (auto coordinate : sd.fitz) {
        fitpoints->ChangeValue(index++).SetZ(coordinate);
    }

    Standard_Boolean periodic = sd.flag == 2;
    GeomAPI_Interpolate interp(fitpoints, periodic, Precision::Confusion());
    interp.Perform();
    return interp.Curve();
}

}  // namespace


void ImpExpDxfRead::OnReadSpline(struct SplineData& sd)
{
    // https://documentation.help/AutoCAD-DXF/WS1a9193826455f5ff18cb41610ec0a2e719-79e1.htm
    // Flags:
    // 1: Closed, 2: Periodic, 4: Rational, 8: Planar, 16: Linear

    if (shouldSkipEntity()) {
        return;
    }

    try {
        Handle(Geom_BSplineCurve) geom;
        if (sd.control_points > 0) {
            geom = getSplineFromPolesAndKnots(sd);
        }
        else if (sd.fit_points > 0) {
            geom = getInterpolationSpline(sd);
        }

        if (!geom.IsNull()) {
            TopoDS_Edge edge = BRepBuilderAPI_MakeEdge(geom).Edge();
            GeometryBuilder builder(edge);
            builder.type = mapImportModeToPrimitiveType(GeometryBuilder::PrimitiveType::Spline);
            Collector->AddGeometry(builder);
        }
    }
    catch (const Standard_Failure&) {
        Base::Console().warning("ImpExpDxf - failed to create bspline\n");
    }
}

// NOLINTBEGIN(bugprone-easily-swappable-parameters)
void ImpExpDxfRead::OnReadEllipse(
    const Base::Vector3d& center,
    double major_radius,
    double minor_radius,
    double rotation,
    double /*start_angle*/,
    double /*end_angle*/,
    bool dir
)
// NOLINTEND(bugprone-easily-swappable-parameters)
{
    if (shouldSkipEntity()) {
        return;
    }

    gp_Dir up(0, 0, 1);
    if (!dir) {
        up.Reverse();
    }
    gp_Pnt pc = makePoint(center);
    gp_Elips ellipse(gp_Ax2(pc, up), major_radius, minor_radius);
    ellipse.Rotate(gp_Ax1(pc, up), rotation);
    if (ellipse.MinorRadius() < 1e-9) {
        Base::Console().warning("ImpExpDxf - ignore degenerate ellipse\n");
        return;
    }

    TopoDS_Edge edge = BRepBuilderAPI_MakeEdge(ellipse).Edge();
    GeometryBuilder builder(edge);
    builder.type = mapImportModeToPrimitiveType(GeometryBuilder::PrimitiveType::Ellipse);
    Collector->AddGeometry(builder);
}

void ImpExpDxfRead::OnReadText(
    const Base::Vector3d& point,
    const double height,
    const std::string& text,
    const double rotation
)
{
    if (shouldSkipEntity() || !m_importAnnotations) {
        return;
    }

    auto* p = static_cast<App::FeaturePython*>(document->addObject("App::FeaturePython", "Text"));
    if (p) {
        p->addDynamicProperty("App::PropertyString", "DxfEntityType", "Internal", "DXF entity type");
        static_cast<App::PropertyString*>(p->getPropertyByName("DxfEntityType"))->setValue("TEXT");

        p->addDynamicProperty("App::PropertyStringList", "Text", "Data", "Text content");
        // Explicitly create the vector to resolve ambiguity
        std::vector<std::string> text_values = {text};
        static_cast<App::PropertyStringList*>(p->getPropertyByName("Text"))->setValues(text_values);

        p->addDynamicProperty("App::PropertyFloat", "DxfTextHeight", "Internal", "Original text height");
        static_cast<App::PropertyFloat*>(p->getPropertyByName("DxfTextHeight"))->setValue(height);

        p->addDynamicProperty("App::PropertyPlacement", "Placement", "Base", "Object placement");
        Base::Placement pl;
        pl.setPosition(point);
        pl.setRotation(Base::Rotation(Base::Vector3d(0, 0, 1), Base::toRadians(rotation)));
        static_cast<App::PropertyPlacement*>(p->getPropertyByName("Placement"))->setValue(pl);

        Collector->AddObject(p, "Text");
    }
}


void ImpExpDxfRead::OnReadInsert(
    const Base::Vector3d& point,
    const Base::Vector3d& scale,
    const std::string& name,
    double rotation
)
{
    if (shouldSkipEntity()) {
        return;
    }

    // Delegate the action to the currently active collector.
    // If the BlockDefinitionCollector is active, it will just store the data.
    // If the DrawingEntityCollector is active, it will create the App::Link.
    Collector->AddInsert(point, scale, name, rotation);
}


void ImpExpDxfRead::OnReadDimension(
    const Base::Vector3d& start,
    const Base::Vector3d& end,
    const Base::Vector3d& point,
    int dimensionType,
    double rotation
)
{
    if (shouldSkipEntity() || !m_importAnnotations) {
        return;
    }

    auto* p = static_cast<App::FeaturePython*>(document->addObject("App::FeaturePython", "Dimension"));
    if (p) {
        p->addDynamicProperty("App::PropertyString", "DxfEntityType", "Internal", "DXF entity type");
        static_cast<App::PropertyString*>(p->getPropertyByName("DxfEntityType"))->setValue("DIMENSION");

        p->addDynamicProperty("App::PropertyVector", "Start", "Data", "Start point of dimension");
        static_cast<App::PropertyVector*>(p->getPropertyByName("Start"))->setValue(start);

        p->addDynamicProperty("App::PropertyVector", "End", "Data", "End point of dimension");
        static_cast<App::PropertyVector*>(p->getPropertyByName("End"))->setValue(end);

        p->addDynamicProperty("App::PropertyVector", "Dimline", "Data", "Point on dimension line");
        static_cast<App::PropertyVector*>(p->getPropertyByName("Dimline"))->setValue(point);

        p->addDynamicProperty(
            "App::PropertyInteger",
            "DxfDimensionType",
            "Internal",
            "Original dimension type flag"
        );
        static_cast<App::PropertyInteger*>(p->getPropertyByName("DxfDimensionType"))
            ->setValue(dimensionType);

        p->addDynamicProperty(
            "App::PropertyAngle",
            "DxfRotation",
            "Internal",
            "Original dimension rotation"
        );
        // rotation is already in radians from the caller
        static_cast<App::PropertyAngle*>(p->getPropertyByName("DxfRotation"))->setValue(rotation);

        p->addDynamicProperty("App::PropertyPlacement", "Placement", "Base", "Object placement");
        Base::Placement pl;
        // Correctly construct the rotation directly from the 4x4 matrix.
        // The Base::Rotation constructor will extract the rotational part.
        pl.setRotation(Base::Rotation(OCSOrientationTransform));
        static_cast<App::PropertyPlacement*>(p->getPropertyByName("Placement"))->setValue(pl);

        Collector->AddObject(p, "Dimension");
    }
}

void ImpExpDxfRead::OnReadPolyline(std::list<VertexInfo>& vertices, int flags)
{
    if (shouldSkipEntity()) {
        return;
    }

    if (vertices.size() < 2 && (flags & 1) == 0) {
        return;  // Not enough vertices for an open polyline
    }

    TopoDS_Wire wire = BuildWireFromPolyline(vertices, flags);
    if (wire.IsNull()) {
        return;
    }

    if (m_importMode == ImportMode::EditableDraft) {
        GeometryBuilder builder(wire);
        builder.type = GeometryBuilder::PrimitiveType::PolylineFlattened;
        Collector->AddGeometry(builder);
    }
    else if (m_importMode == ImportMode::EditablePrimitives) {
        GeometryBuilder builder(wire);
        builder.type = GeometryBuilder::PrimitiveType::PolylineParametric;
        Collector->AddGeometry(builder);
    }
    else {
        Collector->AddObject(wire, "Polyline");
    }
}

void ImpExpDxfRead::DrawingEntityCollector::AddGeometry(const GeometryBuilder& builder)
{
    App::DocumentObject* newDocObj = nullptr;

    switch (builder.type) {
        case GeometryBuilder::PrimitiveType::Line: {
            newDocObj = createLinePrimitive(TopoDS::Edge(builder.shape), Reader.document, "Line");
            break;
        }
        case GeometryBuilder::PrimitiveType::Circle: {
            auto* p = createCirclePrimitive(TopoDS::Edge(builder.shape), Reader.document, "Circle");
            if (p) {
                p->Angle1.setValue(0.0);
                p->Angle2.setValue(360.0);  // Ensure it's a full circle if it's a circle entity
            }
            newDocObj = p;
            break;
        }
        case GeometryBuilder::PrimitiveType::Arc: {
            newDocObj = createCirclePrimitive(TopoDS::Edge(builder.shape), Reader.document, "Arc");
            break;
        }
        case GeometryBuilder::PrimitiveType::Point: {
            newDocObj = createVertexPrimitive(TopoDS::Vertex(builder.shape), Reader.document, "Point");
            break;
        }
        case GeometryBuilder::PrimitiveType::Ellipse: {
            newDocObj = createEllipsePrimitive(TopoDS::Edge(builder.shape), Reader.document, "Ellipse");
            break;
        }
        case GeometryBuilder::PrimitiveType::Spline: {
            newDocObj = createGenericShapeFeature(builder.shape, Reader.document, "Spline");
            break;
        }
        case GeometryBuilder::PrimitiveType::PolylineFlattened: {
            Reader.CreateFlattenedPolyline(TopoDS::Wire(builder.shape), "Polyline");
            newDocObj = nullptr;  // Object handled by helper
            break;
        }
        case GeometryBuilder::PrimitiveType::PolylineParametric: {
            Reader.CreateParametricPolyline(TopoDS::Wire(builder.shape), "Polyline");
            newDocObj = nullptr;  // Object handled by helper
            break;
        }
        case GeometryBuilder::PrimitiveType::None:  // Fallback for generic shapes (e.g., 3DFACE)
        default: {
            newDocObj = createGenericShapeFeature(builder.shape, Reader.document, "Shape");
            break;
        }
    }

    // Common post-creation steps for objects NOT handled by helper functions
    if (newDocObj) {
        Reader.IncrementCreatedObjectCount();
        Reader._addOriginalLayerProperty(newDocObj);
        Reader.MoveToLayer(newDocObj);
        Reader.ApplyGuiStyles(static_cast<Part::Feature*>(newDocObj));
    }
}

ImpExpDxfRead::Layer::Layer(
    const std::string& name,
    ColorIndex_t color,
    std::string&& lineType,
    PyObject* drawingLayer
)
    : CDxfRead::Layer(name, color, std::move(lineType))
    , DraftLayerView(
          drawingLayer == nullptr ? Py_None : PyObject_GetAttrString(drawingLayer, "ViewObject")
      )
    , GroupContents(
          drawingLayer == nullptr ? nullptr
                                  : dynamic_cast<App::PropertyLinkListHidden*>(
                                        (((App::FeaturePythonPyT<App::DocumentObjectPy>*)drawingLayer)
                                             ->getPropertyContainerPtr())
                                            ->getDynamicPropertyByName("Group")
                                    )
      )
{}
ImpExpDxfRead::Layer::~Layer()
{
    Py_XDECREF(DraftLayerView);
}

void ImpExpDxfRead::Layer::FinishLayer() const
{
    if (GroupContents != nullptr) {
        // We have to move the object to layer->DraftLayer
        // The DraftLayer will have a Proxy attribute which has a addObject attribute which we
        // call with (draftLayer, draftObject) Checking from python, the layer is a
        // App::FeaturePython, and its Proxy is a draftobjects.layer.Layer
        GroupContents->setValue(Contents);
    }
    if (DraftLayerView != Py_None && Hidden) {
        // Hide the Hidden layers if possible (if GUI exists)
        // We do this now rather than when the layer is created so all objects
        // within the layers also become hidden.
        PyObject_CallMethod(DraftLayerView, "hide", nullptr);
    }
}

CDxfRead::Layer* ImpExpDxfRead::MakeLayer(const std::string& name, ColorIndex_t color, std::string&& lineType)
{
    if (m_preserveLayers) {
        // Hidden layers are implemented in the wrapup code after the entire file has been read.
        Base::Color appColor = ObjectColor(color);
        PyObject* draftModule = nullptr;
        PyObject* layer = nullptr;
        draftModule = getDraftModule();
        if (draftModule != nullptr) {
            // After the colours, I also want to pass the draw_style, but there is an
            // intervening line-width parameter. It is easier to just pass that parameter's
            // default value than to do the handstands to pass a named parameter.
            // TODO: Pass the appropriate draw_style (from "Solid" "Dashed" "Dotted" "DashDot")
            // This needs an ObjectDrawStyleName analogous to ObjectColor but at the
            // ImpExpDxfGui level.
            layer =
                // NOLINTNEXTLINE(readability/nolint)
                // NOLINTNEXTLINE(cppcoreguidelines-pro-type-cstyle-cast)
                (Base::PyObjectBase*)PyObject_CallMethod(
                    draftModule,
                    "make_layer",
                    "s(fff)(fff)fs",
                    name.c_str(),
                    appColor.r,
                    appColor.g,
                    appColor.b,
                    appColor.r,
                    appColor.g,
                    appColor.b,
                    2.0,
                    "Solid"
                );
        }
        auto result = new Layer(name, color, std::move(lineType), layer);
        if (result->DraftLayerView != Py_None) {
            // Get the correct boolean value based on the user's preference.
            PyObject* overrideValue = m_preserveColors ? Py_True : Py_False;
            PyObject_SetAttrString(result->DraftLayerView, "OverrideLineColorChildren", overrideValue);
            PyObject_SetAttrString(
                result->DraftLayerView,
                "OverrideShapeAppearanceChildren",
                overrideValue
            );
        }

        // We make our own layer class even if we could not make a layer. MoveToLayer will
        // ignore such layers but we have to do this because it is not a polymorphic type so we
        // can't tell what we pull out of m_entityAttributes.m_Layer.
        return result;
    }
    return CDxfRead::MakeLayer(name, color, std::move(lineType));
}
void ImpExpDxfRead::MoveToLayer(App::DocumentObject* object) const
{
    if (m_preserveLayers) {
        static_cast<Layer*>(m_entityAttributes.m_Layer)->Contents.push_back(object);
    }
    // TODO: else Hide the object if it is in a Hidden layer? That won't work because we've
    // cleared out m_entityAttributes.m_Layer
}


std::string ImpExpDxfRead::Deformat(const char* text)
{
    // this function removes DXF formatting from texts
    std::stringstream ss;
    bool escape = false;      // turned on when finding an escape character
    bool longescape = false;  // turned on for certain escape codes that expect additional chars
    for (unsigned int i = 0; i < strlen(text); i++) {
        char ch = text[i];
        if (ch == '\\') {
            escape = true;
        }
        else if (escape) {
            if (longescape) {
                if (ch == ';') {
                    escape = false;
                    longescape = false;
                }
            }
            else if ((ch == 'H') || (ch == 'h') || (ch == 'Q') || (ch == 'q') || (ch == 'W')
                     || (ch == 'w') || (ch == 'F') || (ch == 'f') || (ch == 'A') || (ch == 'a')
                     || (ch == 'C') || (ch == 'c') || (ch == 'T') || (ch == 't')) {
                longescape = true;
            }
            else {
                if ((ch == 'P') || (ch == 'p')) {
                    ss << "\n";
                }
                escape = false;
            }
        }
        else if ((ch != '{') && (ch != '}')) {
            ss << ch;
        }
    }
    return ss.str();
}

void ImpExpDxfRead::_addOriginalLayerProperty(App::DocumentObject* obj)
{
    if (obj && m_entityAttributes.m_Layer) {
        obj->addDynamicProperty(
            "App::PropertyString",
            "OriginalLayer",
            "Internal",
            "Layer name from the original DXF file.",
            App::Property::Hidden
        );
        static_cast<App::PropertyString*>(obj->getPropertyByName("OriginalLayer"))
            ->setValue(m_entityAttributes.m_Layer->Name.c_str());
    }
}

void ImpExpDxfRead::DrawingEntityCollector::AddObject(const TopoDS_Shape& shape, const char* nameBase)
{
    auto pcFeature = Reader.document->addObject<Part::Feature>(nameBase);

    if (pcFeature) {
        Reader.IncrementCreatedObjectCount();
        pcFeature->Shape.setValue(shape);
        Reader._addOriginalLayerProperty(pcFeature);
        Reader.MoveToLayer(pcFeature);
        Reader.ApplyGuiStyles(pcFeature);
    }
}

void ImpExpDxfRead::DrawingEntityCollector::AddObject(App::DocumentObject* obj, const char* /*nameBase*/)
{
    Reader.MoveToLayer(obj);
    Reader._addOriginalLayerProperty(obj);

    // Safely apply styles by checking the object's actual type (only for objects not replaced
    // by Python)
    if (auto feature = dynamic_cast<Part::Feature*>(obj)) {
        Reader.ApplyGuiStyles(feature);
    }
    else if (auto pyFeature = dynamic_cast<App::FeaturePython*>(obj)) {
        Reader.ApplyGuiStyles(pyFeature);
    }
    else if (auto link = dynamic_cast<App::Link*>(obj)) {
        Reader.ApplyGuiStyles(link);
    }
}

void ImpExpDxfRead::DrawingEntityCollector::AddObject(FeaturePythonBuilder shapeBuilder)
{
    Reader.IncrementCreatedObjectCount();
    App::FeaturePython* shape = shapeBuilder(Reader.OCSOrientationTransform);
    if (shape != nullptr) {
        Reader._addOriginalLayerProperty(shape);
    }
}
