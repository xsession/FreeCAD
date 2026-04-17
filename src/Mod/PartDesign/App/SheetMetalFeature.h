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

#pragma once

#include <App/PropertyStandard.h>
#include <App/PropertyUnits.h>
#include <Mod/Part/App/PartFeature.h>
#include <Mod/PartDesign/PartDesignGlobal.h>


namespace SheetMetal
{

/** Base class for all sheet metal features.
 *  Provides shared properties: material thickness, K-factor, and bend radius.
 */
class PartDesignExport SheetMetalFeature : public Part::Feature
{
    PROPERTY_HEADER_WITH_OVERRIDE(SheetMetal::SheetMetalFeature);

public:
    SheetMetalFeature();

    /// Sheet material thickness
    App::PropertyLength Thickness;

    /// Default bend radius (can be overridden per bend)
    App::PropertyLength BendRadius;

    /// K-factor for bend allowance calculation (0.0–1.0, typical: 0.33–0.50)
    App::PropertyFloatConstraint KFactor;

    App::DocumentObjectExecReturn* execute() override;

    const char* getViewProviderName() const override
    {
        return "PartGui::ViewProviderPart";
    }

protected:
    /// Calculate bend allowance: π/180 × angle × (BendRadius + K × Thickness)
    double bendAllowance(double angleDeg) const;
};


/** Base Flange: creates the initial sheet metal body from a sketch profile.
 *  Sketch profile is extruded by Thickness to produce a flat sheet, then
 *  edges can receive flanges via EdgeFlange features.
 */
class PartDesignExport BaseFlange : public SheetMetalFeature
{
    PROPERTY_HEADER_WITH_OVERRIDE(SheetMetal::BaseFlange);

public:
    BaseFlange();

    /// Sketch defining the base profile
    App::PropertyLink Profile;

    /// Length of the base flange extrusion
    App::PropertyLength Length;

    App::DocumentObjectExecReturn* execute() override;

    const char* getViewProviderName() const override
    {
        return "PartGui::ViewProviderPart";
    }
};


/** Edge Flange: adds a flange along selected edges of an existing sheet.
 */
class PartDesignExport EdgeFlange : public SheetMetalFeature
{
    PROPERTY_HEADER_WITH_OVERRIDE(SheetMetal::EdgeFlange);

public:
    EdgeFlange();

    /// Base shape to add flange to
    App::PropertyLink BaseShape;

    /// Selected edges (sub-element references)
    App::PropertyLinkSub Edges;

    /// Flange length (measured from bend line)
    App::PropertyLength FlangeLength;

    /// Bend angle in degrees (default 90°)
    App::PropertyAngle BendAngle;

    App::DocumentObjectExecReturn* execute() override;

    const char* getViewProviderName() const override
    {
        return "PartGui::ViewProviderPart";
    }
};


/** Unfold: generates a flat pattern from a bent sheet metal body.
 *  Uses bend allowance calculations with K-factor to flatten bends.
 */
class PartDesignExport Unfold : public Part::Feature
{
    PROPERTY_HEADER_WITH_OVERRIDE(SheetMetal::Unfold);

public:
    Unfold();

    /// The bent sheet metal shape to unfold
    App::PropertyLink Source;

    /// Override K-factor (if different from source feature)
    App::PropertyFloatConstraint KFactor;

    App::DocumentObjectExecReturn* execute() override;

    const char* getViewProviderName() const override
    {
        return "PartGui::ViewProviderPart";
    }
};

}  // namespace SheetMetal
