// SPDX-License-Identifier: LGPL-2.1-or-later

/***************************************************************************
 *   Copyright (c) 2026 FreeCAD contributors                              *
 *                                                                         *
 *   This file is part of the FreeCAD CAx development system.              *
 *                                                                         *
 *   This library is free software; you can redistribute it and/or         *
 *   modify it under the terms of the GNU Library General Public           *
 *   License as published by the Free Software Foundation; either          *
 *   version 2 of the License, or (at your option) any later version.     *
 *                                                                         *
 *   This library  is distributed in the hope that it will be useful,      *
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
 *   GNU Library General Public License for more details.                  *
 *                                                                         *
 *   You should have received a copy of the GNU Library General Public     *
 *   License along with this library; see the file COPYING.LIB. If not,   *
 *   write to the Free Software Foundation, Inc., 59 Temple Place,         *
 *   Suite 330, Boston, MA  02111-1307, USA                                *
 *                                                                         *
 ***************************************************************************/

#include "PreCompiled.h"

#ifndef _PreComp_
#include <BRepPrimAPI_MakeBox.hxx>
#include <BRepPrimAPI_MakePrism.hxx>
#include <BRepBuilderAPI_MakeFace.hxx>
#include <BRepBuilderAPI_MakeWire.hxx>
#include <BRepAlgoAPI_Fuse.hxx>
#include <gp_Vec.hxx>
#include <TopoDS.hxx>
#include <TopoDS_Face.hxx>
#include <TopoDS_Wire.hxx>
#include <TopExp_Explorer.hxx>
#endif

#include <cmath>

#include <Base/Console.h>
#include <Mod/Part/App/PartFeature.h>

#include "SheetMetalFeature.h"


using namespace SheetMetal;

// ─── SheetMetalFeature (base) ───────────────────────────────────────────────

PROPERTY_SOURCE(SheetMetal::SheetMetalFeature, Part::Feature)

SheetMetalFeature::SheetMetalFeature()
{
    ADD_PROPERTY_TYPE(Thickness, (1.0), "SheetMetal", App::Prop_None,
                      "Material thickness");
    ADD_PROPERTY_TYPE(BendRadius, (1.0), "SheetMetal", App::Prop_None,
                      "Default bend radius");

    static const App::PropertyFloatConstraint::Constraints kConstr = {0.0, 1.0, 0.01};
    ADD_PROPERTY_TYPE(KFactor, (0.44), "SheetMetal", App::Prop_None,
                      "K-factor for bend allowance (0.0–1.0)");
    KFactor.setConstraints(&kConstr);
}

App::DocumentObjectExecReturn* SheetMetalFeature::execute()
{
    return App::DocumentObject::StdReturn;
}

double SheetMetalFeature::bendAllowance(double angleDeg) const
{
    double r = BendRadius.getValue();
    double t = Thickness.getValue();
    double k = KFactor.getValue();
    return (M_PI / 180.0) * angleDeg * (r + k * t);
}


// ─── BaseFlange ─────────────────────────────────────────────────────────────

PROPERTY_SOURCE(SheetMetal::BaseFlange, SheetMetal::SheetMetalFeature)

BaseFlange::BaseFlange()
{
    ADD_PROPERTY_TYPE(Profile, (nullptr), "BaseFlange", App::Prop_None,
                      "Sketch profile for the base flange");
    ADD_PROPERTY_TYPE(Length, (100.0), "BaseFlange", App::Prop_None,
                      "Extrusion length");
}

App::DocumentObjectExecReturn* BaseFlange::execute()
{
    auto* profileObj = Profile.getValue();
    if (!profileObj) {
        return new App::DocumentObjectExecReturn("No profile sketch linked.");
    }

    // Get the sketch shape (wire)
    auto* partFeat = dynamic_cast<Part::Feature*>(profileObj);
    if (!partFeat) {
        return new App::DocumentObjectExecReturn("Profile must be a Part::Feature.");
    }

    TopoDS_Shape profileShape = partFeat->Shape.getValue();
    if (profileShape.IsNull()) {
        return new App::DocumentObjectExecReturn("Profile shape is null.");
    }

    // Try to make a face from the wire
    TopoDS_Wire wire;
    TopExp_Explorer exp(profileShape, TopAbs_WIRE);
    if (exp.More()) {
        wire = TopoDS::Wire(exp.Current());
    }
    else {
        return new App::DocumentObjectExecReturn("Profile does not contain a wire.");
    }

    BRepBuilderAPI_MakeFace mkFace(wire);
    if (!mkFace.IsDone()) {
        return new App::DocumentObjectExecReturn("Cannot make face from profile wire.");
    }
    TopoDS_Face face = mkFace.Face();

    // Extrude the face by thickness in the normal direction
    double thick = Thickness.getValue();
    if (thick <= 0) {
        return new App::DocumentObjectExecReturn("Thickness must be positive.");
    }

    // Extrude along Z by thickness to create the sheet
    gp_Vec extDir(0, 0, thick);
    BRepPrimAPI_MakePrism mkPrism(face, extDir);
    if (!mkPrism.IsDone()) {
        return new App::DocumentObjectExecReturn("Failed to extrude base flange.");
    }

    // If Length > 0, we also extrude the profile along X by Length
    // (typical base flange: sketch in YZ plane, extruded along X)
    double len = Length.getValue();
    if (len > 0) {
        gp_Vec lenDir(len, 0, 0);
        BRepPrimAPI_MakePrism mkLen(face, lenDir);
        if (mkLen.IsDone()) {
            Shape.setValue(mkLen.Shape());
            return App::DocumentObject::StdReturn;
        }
    }

    Shape.setValue(mkPrism.Shape());
    return App::DocumentObject::StdReturn;
}


// ─── EdgeFlange ─────────────────────────────────────────────────────────────

PROPERTY_SOURCE(SheetMetal::EdgeFlange, SheetMetal::SheetMetalFeature)

EdgeFlange::EdgeFlange()
{
    ADD_PROPERTY_TYPE(BaseShape, (nullptr), "EdgeFlange", App::Prop_None,
                      "Base sheet metal shape");
    ADD_PROPERTY_TYPE(Edges, (nullptr, {}), "EdgeFlange", App::Prop_None,
                      "Edges to add flanges to");
    ADD_PROPERTY_TYPE(FlangeLength, (20.0), "EdgeFlange", App::Prop_None,
                      "Flange length from bend line");
    ADD_PROPERTY_TYPE(BendAngle, (90.0), "EdgeFlange", App::Prop_None,
                      "Bend angle in degrees");
}

App::DocumentObjectExecReturn* EdgeFlange::execute()
{
    auto* baseObj = dynamic_cast<Part::Feature*>(BaseShape.getValue());
    if (!baseObj) {
        return new App::DocumentObjectExecReturn("No base shape linked.");
    }

    TopoDS_Shape base = baseObj->Shape.getValue();
    if (base.IsNull()) {
        return new App::DocumentObjectExecReturn("Base shape is null.");
    }

    // TODO: Iterate selected edges, create bent flange geometry per edge
    // using BendRadius, BendAngle, FlangeLength, and Thickness.
    // For now, pass through the base shape.
    Shape.setValue(base);

    Base::Console().Message("EdgeFlange: Stub — edge flange generation not yet implemented.\n");
    return App::DocumentObject::StdReturn;
}


// ─── Unfold ─────────────────────────────────────────────────────────────────

PROPERTY_SOURCE(SheetMetal::Unfold, Part::Feature)

Unfold::Unfold()
{
    ADD_PROPERTY_TYPE(Source, (nullptr), "Unfold", App::Prop_None,
                      "Bent sheet metal body to unfold");

    static const App::PropertyFloatConstraint::Constraints kConstr = {0.0, 1.0, 0.01};
    ADD_PROPERTY_TYPE(KFactor, (0.44), "Unfold", App::Prop_None,
                      "K-factor override for unfolding");
    KFactor.setConstraints(&kConstr);
}

App::DocumentObjectExecReturn* Unfold::execute()
{
    auto* sourceObj = dynamic_cast<Part::Feature*>(Source.getValue());
    if (!sourceObj) {
        return new App::DocumentObjectExecReturn("No source shape linked.");
    }

    TopoDS_Shape src = sourceObj->Shape.getValue();
    if (src.IsNull()) {
        return new App::DocumentObjectExecReturn("Source shape is null.");
    }

    // TODO: Implement bend detection and flat-pattern computation.
    // Algorithm:
    //   1. Detect cylindrical faces (bends) vs planar faces (flat segments)
    //   2. Build connectivity graph of flat segments joined by bends
    //   3. Traverse graph, rotating each flat face by bend angle
    //      and offsetting by bend allowance
    //   4. Project all faces to a common plane to produce flat pattern
    //
    // For now, pass through the source shape.
    Shape.setValue(src);

    Base::Console().Message("Unfold: Stub — flat pattern generation not yet implemented.\n");
    return App::DocumentObject::StdReturn;
}
