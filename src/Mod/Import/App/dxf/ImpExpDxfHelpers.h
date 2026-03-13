// SPDX-License-Identifier: LGPL-2.1-or-later
// Internal helpers for ImpExpDxf, shared across translation units.
// This file is intentionally NOT a public header — it should only be
// included by ImpExpDxf*.cpp files.

#pragma once

#include <BRep_Tool.hxx>
#include <Geom_Circle.hxx>
#include <Geom_Ellipse.hxx>
#include <TopExp.hxx>
#include <TopoDS.hxx>
#include <TopoDS_Edge.hxx>
#include <TopoDS_Vertex.hxx>

#include <Base/Placement.h>
#include <Base/Rotation.h>
#include <Base/Tools.h>
#include <Mod/Part/App/PartFeature.h>
#include <Mod/Part/App/PrimitiveFeature.h>
#include <Mod/Part/App/FeaturePartCircle.h>

namespace Import::detail
{

// Helper function to create and configure a Part::Ellipse primitive from a TopoDS_Edge
inline Part::Ellipse* createEllipsePrimitive(const TopoDS_Edge& edge, App::Document* doc, const char* name)
{
    auto* p = doc->addObject<Part::Ellipse>(name);
    if (!p) {
        return nullptr;
    }

    TopLoc_Location loc;
    Standard_Real first, last;
    Handle(Geom_Curve) aCurve = BRep_Tool::Curve(edge, loc, first, last);

    if (aCurve->IsInstance(Geom_Ellipse::get_type_descriptor())) {
        Handle(Geom_Ellipse) ellipse = Handle(Geom_Ellipse)::DownCast(aCurve);

        p->MajorRadius.setValue(ellipse->MajorRadius());
        p->MinorRadius.setValue(ellipse->MinorRadius());

        gp_Ax2 axis = ellipse->Position().Transformed(loc.Transformation());
        gp_Pnt center = axis.Location();
        gp_Dir xDir = axis.XDirection();
        gp_Dir yDir = axis.YDirection();
        gp_Dir zDir = axis.Direction();

        Base::Placement plc;
        plc.setPosition(Base::Vector3d(center.X(), center.Y(), center.Z()));
        plc.setRotation(
            Base::Rotation::makeRotationByAxes(
                Base::Vector3d(xDir.X(), xDir.Y(), xDir.Z()),
                Base::Vector3d(yDir.X(), yDir.Y(), yDir.Z()),
                Base::Vector3d(zDir.X(), zDir.Y(), zDir.Z())
            )
        );
        p->Placement.setValue(plc);

        BRep_Tool::Range(edge, first, last);
        p->Angle1.setValue(Base::toDegrees(first));
        p->Angle2.setValue(Base::toDegrees(last));
    }
    return p;
}

// Helper function to create and configure a Part::Circle primitive from a TopoDS_Edge
inline Part::Circle* createCirclePrimitive(const TopoDS_Edge& edge, App::Document* doc, const char* name)
{
    auto* p = doc->addObject<Part::Circle>(name);
    if (!p) {
        return nullptr;
    }

    TopLoc_Location loc;
    Standard_Real first, last;
    Handle(Geom_Curve) aCurve = BRep_Tool::Curve(edge, loc, first, last);

    if (aCurve->IsInstance(Geom_Circle::get_type_descriptor())) {
        Handle(Geom_Circle) circle = Handle(Geom_Circle)::DownCast(aCurve);
        p->Radius.setValue(circle->Radius());

        gp_Ax2 axis = circle->Position().Transformed(loc.Transformation());
        gp_Pnt center = axis.Location();
        gp_Dir xDir = axis.XDirection();
        gp_Dir yDir = axis.YDirection();
        gp_Dir zDir = axis.Direction();

        Base::Placement plc;
        plc.setPosition(Base::Vector3d(center.X(), center.Y(), center.Z()));
        plc.setRotation(
            Base::Rotation::makeRotationByAxes(
                Base::Vector3d(xDir.X(), xDir.Y(), xDir.Z()),
                Base::Vector3d(yDir.X(), yDir.Y(), yDir.Z()),
                Base::Vector3d(zDir.X(), zDir.Y(), zDir.Z())
            )
        );
        p->Placement.setValue(plc);

        BRep_Tool::Range(edge, first, last);
        p->Angle1.setValue(Base::toDegrees(first));
        p->Angle2.setValue(Base::toDegrees(last));
    }
    return p;
}

// Helper function to create and configure a Part::Line primitive from a TopoDS_Edge
inline Part::Line* createLinePrimitive(const TopoDS_Edge& edge, App::Document* doc, const char* name)
{
    auto* p = doc->addObject<Part::Line>(name);
    if (!p) {
        return nullptr;
    }

    TopoDS_Vertex v1, v2;
    TopExp::Vertices(edge, v1, v2);
    gp_Pnt p1 = BRep_Tool::Pnt(v1);
    gp_Pnt p2 = BRep_Tool::Pnt(v2);

    p->X1.setValue(p1.X());
    p->Y1.setValue(p1.Y());
    p->Z1.setValue(p1.Z());
    p->X2.setValue(p2.X());
    p->Y2.setValue(p2.Y());
    p->Z2.setValue(p2.Z());

    return p;
}

// Helper function to create and configure a Part::Vertex primitive from a TopoDS_Vertex
inline Part::Vertex* createVertexPrimitive(const TopoDS_Vertex& vertex, App::Document* doc, const char* name)
{
    auto* p = doc->addObject<Part::Vertex>(name);
    if (p) {
        gp_Pnt pnt = BRep_Tool::Pnt(vertex);
        p->X.setValue(pnt.X());
        p->Y.setValue(pnt.Y());
        p->Z.setValue(pnt.Z());
    }
    return p;
}

// Helper function to create a generic Part::Feature for any non-parametric shape
inline Part::Feature* createGenericShapeFeature(const TopoDS_Shape& shape, App::Document* doc, const char* name)
{
    auto* p = doc->addObject<Part::Feature>(name);
    if (p) {
        p->Shape.setValue(shape);
    }
    return p;
}

}  // namespace Import::detail
