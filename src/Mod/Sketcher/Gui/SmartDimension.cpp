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

#include "PreCompiled.h"

#include <algorithm>
#include <cmath>
#include <sstream>
#include <iomanip>

#include <Mod/Part/App/Geometry.h>
#include <Mod/Sketcher/App/SketchObject.h>

#include "SmartDimension.h"

using namespace SketcherGui;
using namespace Sketcher;

// ---------------------------------------------------------------------------
// Helper: angle between horizontal and a line segment (radians)
// ---------------------------------------------------------------------------
static double lineAngle(const Base::Vector3d& p1, const Base::Vector3d& p2)
{
    Base::Vector3d dir = p2 - p1;
    return std::atan2(dir.y, dir.x);
}

static constexpr double ANGLE_THRESHOLD = 5.0 * M_PI / 180.0;  // 5 degrees

// ---------------------------------------------------------------------------
// classify — single selection
// ---------------------------------------------------------------------------
SmartDimensionHint SmartDimension::classify(SketchObject* sketch,
                                             int geoId,
                                             PointPos posId)
{
    if (!sketch) {
        return {};
    }

    // If a specific vertex is selected, return empty — need a second point
    if (posId != PointPos::none) {
        SmartDimensionHint hint;
        hint.geoId1 = geoId;
        hint.posId1 = posId;
        hint.type = ConstraintType::Distance;
        hint.value = 0.0;
        hint.label = "Select second element";
        hint.anchorPoint = sketch->getPoint(geoId, posId);
        return hint;
    }

    const Part::Geometry* geom = sketch->getGeometry(geoId);
    if (!geom) {
        return {};
    }

    if (geom->is<Part::GeomLineSegment>()) {
        return classifyLine(sketch, geoId, geom);
    }
    if (geom->is<Part::GeomCircle>() || geom->is<Part::GeomArcOfCircle>()) {
        return classifyCircleOrArc(sketch, geoId, geom);
    }

    // Default: generic distance
    SmartDimensionHint hint;
    hint.geoId1 = geoId;
    hint.type = ConstraintType::Distance;
    return hint;
}

// ---------------------------------------------------------------------------
// classifyPair — two selections
// ---------------------------------------------------------------------------
SmartDimensionHint SmartDimension::classifyPair(SketchObject* sketch,
                                                 int geoId1, PointPos posId1,
                                                 int geoId2, PointPos posId2)
{
    if (!sketch) {
        return {};
    }

    bool isPoint1 = (posId1 != PointPos::none);
    bool isPoint2 = (posId2 != PointPos::none);

    // Two points → Distance
    if (isPoint1 && isPoint2) {
        return classifyTwoPoints(sketch, geoId1, posId1, geoId2, posId2);
    }

    // Point + Edge → perpendicular distance
    if (isPoint1 && !isPoint2) {
        return classifyPointLine(sketch, geoId1, posId1, geoId2);
    }
    if (!isPoint1 && isPoint2) {
        return classifyPointLine(sketch, geoId2, posId2, geoId1);
    }

    // Two edges
    const Part::Geometry* geom1 = sketch->getGeometry(geoId1);
    const Part::Geometry* geom2 = sketch->getGeometry(geoId2);
    if (!geom1 || !geom2) {
        return {};
    }

    bool isLine1 = geom1->is<Part::GeomLineSegment>();
    bool isLine2 = geom2->is<Part::GeomLineSegment>();

    // Two lines → Angle
    if (isLine1 && isLine2) {
        return classifyTwoLines(sketch, geoId1, geoId2);
    }

    // Fallback: generic Distance
    SmartDimensionHint hint;
    hint.geoId1 = geoId1;
    hint.geoId2 = geoId2;
    hint.type = ConstraintType::Distance;
    return hint;
}

// ---------------------------------------------------------------------------
// classifyLine
// ---------------------------------------------------------------------------
SmartDimensionHint SmartDimension::classifyLine(SketchObject* sketch,
                                                 int geoId,
                                                 const Part::Geometry* geom)
{
    auto* line = static_cast<const Part::GeomLineSegment*>(geom);
    Base::Vector3d p1 = line->getStartPoint();
    Base::Vector3d p2 = line->getEndPoint();

    double angle = std::abs(lineAngle(p1, p2));
    double length = (p2 - p1).Length();

    SmartDimensionHint hint;
    hint.geoId1 = geoId;
    hint.value = length;
    hint.anchorPoint = (p1 + p2) * 0.5;

    // Near-horizontal → DistanceX
    if (angle < ANGLE_THRESHOLD || std::abs(angle - M_PI) < ANGLE_THRESHOLD) {
        hint.type = ConstraintType::DistanceX;
        hint.value = std::abs(p2.x - p1.x);
        hint.label = "Horizontal distance";
    }
    // Near-vertical → DistanceY
    else if (std::abs(angle - M_PI_2) < ANGLE_THRESHOLD
             || std::abs(angle + M_PI_2) < ANGLE_THRESHOLD) {
        hint.type = ConstraintType::DistanceY;
        hint.value = std::abs(p2.y - p1.y);
        hint.label = "Vertical distance";
    }
    // General → Distance
    else {
        hint.type = ConstraintType::Distance;
        hint.label = "Distance";
    }

    return hint;
}

// ---------------------------------------------------------------------------
// classifyCircleOrArc
// ---------------------------------------------------------------------------
SmartDimensionHint SmartDimension::classifyCircleOrArc(SketchObject* sketch,
                                                        int geoId,
                                                        const Part::Geometry* geom)
{
    SmartDimensionHint hint;
    hint.geoId1 = geoId;

    if (auto* circle = dynamic_cast<const Part::GeomCircle*>(geom)) {
        hint.type = ConstraintType::Radius;
        hint.value = circle->getRadius();
        hint.label = "Radius";
        hint.anchorPoint = circle->getCenter();
    }
    else if (auto* arc = dynamic_cast<const Part::GeomArcOfCircle*>(geom)) {
        hint.type = ConstraintType::Radius;
        hint.value = arc->getRadius();
        hint.label = "Radius";
        hint.anchorPoint = arc->getCenter();
    }

    return hint;
}

// ---------------------------------------------------------------------------
// classifyTwoLines → Angle
// ---------------------------------------------------------------------------
SmartDimensionHint SmartDimension::classifyTwoLines(SketchObject* sketch,
                                                     int geoId1, int geoId2)
{
    auto* line1 = static_cast<const Part::GeomLineSegment*>(sketch->getGeometry(geoId1));
    auto* line2 = static_cast<const Part::GeomLineSegment*>(sketch->getGeometry(geoId2));

    Base::Vector3d d1 = line1->getEndPoint() - line1->getStartPoint();
    Base::Vector3d d2 = line2->getEndPoint() - line2->getStartPoint();

    double dot = d1.Normalize() * d2.Normalize();
    double angle = std::acos(std::clamp(dot, -1.0, 1.0));

    SmartDimensionHint hint;
    hint.geoId1 = geoId1;
    hint.geoId2 = geoId2;
    hint.type = ConstraintType::Angle;
    hint.value = angle * 180.0 / M_PI;
    hint.label = "Angle";
    hint.anchorPoint = (line1->getStartPoint() + line2->getStartPoint()) * 0.5;

    return hint;
}

// ---------------------------------------------------------------------------
// classifyPointLine → Distance (point-to-line)
// ---------------------------------------------------------------------------
SmartDimensionHint SmartDimension::classifyPointLine(SketchObject* sketch,
                                                      int ptGeoId, PointPos ptPos,
                                                      int lineGeoId)
{
    Base::Vector3d pt = sketch->getPoint(ptGeoId, ptPos);
    const Part::Geometry* geom = sketch->getGeometry(lineGeoId);

    SmartDimensionHint hint;
    hint.geoId1 = ptGeoId;
    hint.posId1 = ptPos;
    hint.geoId2 = lineGeoId;
    hint.type = ConstraintType::Distance;
    hint.anchorPoint = pt;

    if (auto* line = dynamic_cast<const Part::GeomLineSegment*>(geom)) {
        Base::Vector3d p1 = line->getStartPoint();
        Base::Vector3d p2 = line->getEndPoint();
        Base::Vector3d dir = p2 - p1;
        double len = dir.Length();
        if (len > 1e-10) {
            dir = dir / len;
            Base::Vector3d diff = pt - p1;
            double proj = diff * dir;
            Base::Vector3d closest = p1 + dir * proj;
            hint.value = (pt - closest).Length();
        }
        hint.label = "Distance";
    }

    return hint;
}

// ---------------------------------------------------------------------------
// classifyTwoPoints → Distance
// ---------------------------------------------------------------------------
SmartDimensionHint SmartDimension::classifyTwoPoints(SketchObject* sketch,
                                                      int geoId1, PointPos pos1,
                                                      int geoId2, PointPos pos2)
{
    Base::Vector3d p1 = sketch->getPoint(geoId1, pos1);
    Base::Vector3d p2 = sketch->getPoint(geoId2, pos2);

    SmartDimensionHint hint;
    hint.geoId1 = geoId1;
    hint.posId1 = pos1;
    hint.geoId2 = geoId2;
    hint.posId2 = pos2;
    hint.type = ConstraintType::Distance;
    hint.value = (p2 - p1).Length();
    hint.label = "Distance";
    hint.anchorPoint = (p1 + p2) * 0.5;

    return hint;
}

// ---------------------------------------------------------------------------
// formatLabel
// ---------------------------------------------------------------------------
std::string SmartDimension::formatLabel(const SmartDimensionHint& hint,
                                         const char* unitSuffix)
{
    std::ostringstream ss;
    ss << hint.label;
    if (hint.value != 0.0) {
        ss << " " << std::fixed << std::setprecision(2) << hint.value;
        if (unitSuffix && unitSuffix[0]) {
            ss << " " << unitSuffix;
        }
    }
    return ss.str();
}
