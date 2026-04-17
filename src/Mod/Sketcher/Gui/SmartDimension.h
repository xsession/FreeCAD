/***************************************************************************
 *   Copyright (c) 2024 FreeCAD Project                                   *
 *                                                                         *
 *   This file is part of the FreeCAD CAx development system.              *
 *                                                                         *
 *   This library is free software; you can redistribute it and/or         *
 *   modify it under the terms of the GNU Library General Public           *
 *   License as published by the Free Software Foundation; either          *
 *   version 2 of the License, or (at your option) any later version.      *
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

#include <string>
#include <vector>

#include <Base/Vector3D.h>
#include <Mod/Sketcher/App/Constraint.h>
#include <Mod/Sketcher/SketcherGlobal.h>

namespace Part {
class Geometry;
}

namespace Sketcher {
class SketchObject;
}

namespace SketcherGui {

/// Describes a dimension that SmartDimension would create for a given
/// hover location / pre-selection state.
struct SmartDimensionHint
{
    SmartDimensionHint() = default;

    Sketcher::ConstraintType type = Sketcher::ConstraintType::Distance;
    int geoId1 = -2000;
    int geoId2 = -2000;
    Sketcher::PointPos posId1 = Sketcher::PointPos::none;
    Sketcher::PointPos posId2 = Sketcher::PointPos::none;
    double value = 0.0;                ///< measured value (length / angle / radius)
    std::string label;                 ///< human-readable hint, e.g. "Radius 12.5 mm"
    Base::Vector3d anchorPoint;        ///< where to draw the overlay hint in sketch space
};

/// SmartDimension engine — analyses the sketch geometry under the cursor
/// and proposes the most appropriate dimension constraint.
///
/// This is a stateless helper used by the Sketcher_Dimension command and
/// by the in-canvas hover overlay to show a dimension preview ghost
/// before the user clicks.
///
/// Mapping rules (§6.6.1 of MODERNIZATION_PLAN):
///   Horizontal line   → DistanceX
///   Vertical line     → DistanceY
///   General line      → Distance
///   Circle            → Radius (or Diameter via M key)
///   Arc               → Radius
///   Ellipse major     → Distance (semi-major)
///   Two points        → Distance
///   Point + line      → Distance (perpendicular)
///   Two lines         → Angle
///   Line + circle     → Distance (closest)
class SketcherGuiExport SmartDimension
{
public:
    /// Classify a single edge or vertex pre-selection and return the
    /// best dimension hint.  Returns an empty hint (geoId1 == GeoUndef)
    /// if no sensible dimension can be inferred.
    static SmartDimensionHint classify(Sketcher::SketchObject* sketch,
                                       int geoId,
                                       Sketcher::PointPos posId);

    /// Classify a pair of selections (two edges, two points, edge+point, etc.)
    static SmartDimensionHint classifyPair(Sketcher::SketchObject* sketch,
                                            int geoId1, Sketcher::PointPos posId1,
                                            int geoId2, Sketcher::PointPos posId2);

    /// Format the hint label (e.g. "Distance 25.4 mm", "Radius 10 mm").
    static std::string formatLabel(const SmartDimensionHint& hint,
                                    const char* unitSuffix = "mm");

private:
    static SmartDimensionHint classifyLine(Sketcher::SketchObject* sketch,
                                            int geoId,
                                            const Part::Geometry* geom);
    static SmartDimensionHint classifyCircleOrArc(Sketcher::SketchObject* sketch,
                                                   int geoId,
                                                   const Part::Geometry* geom);
    static SmartDimensionHint classifyTwoLines(Sketcher::SketchObject* sketch,
                                                int geoId1, int geoId2);
    static SmartDimensionHint classifyPointLine(Sketcher::SketchObject* sketch,
                                                 int ptGeoId, Sketcher::PointPos ptPos,
                                                 int lineGeoId);
    static SmartDimensionHint classifyTwoPoints(Sketcher::SketchObject* sketch,
                                                 int geoId1, Sketcher::PointPos pos1,
                                                 int geoId2, Sketcher::PointPos pos2);
};

} // namespace SketcherGui
