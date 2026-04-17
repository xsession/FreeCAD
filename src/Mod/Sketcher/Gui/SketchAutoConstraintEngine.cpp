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

#include <algorithm>
#include <cmath>

#include <Mod/Part/App/Geometry.h>
#include <Mod/Sketcher/App/GeoEnum.h>

#include "SketchAutoConstraintEngine.h"


using namespace SketcherGui;
using namespace Sketcher;

namespace
{

/// Get line direction as normalized 2D vector. Returns false if geometry is not a line.
bool getLineDir(const Part::Geometry* geo, Base::Vector2d& dir, double& length)
{
    if (!geo || geo->getTypeId() != Part::GeomLineSegment::getClassTypeId()) {
        return false;
    }
    auto line = static_cast<const Part::GeomLineSegment*>(geo);
    Base::Vector3d s = line->getStartPoint();
    Base::Vector3d e = line->getEndPoint();
    Base::Vector2d d(e.x - s.x, e.y - s.y);
    length = d.Length();
    if (length < 1e-10) {
        return false;
    }
    dir = Base::Vector2d(d.x / length, d.y / length);
    return true;
}

/// Get the midpoint of a line segment.
bool getLineMidpoint(const Part::Geometry* geo, Base::Vector2d& mid)
{
    if (!geo || geo->getTypeId() != Part::GeomLineSegment::getClassTypeId()) {
        return false;
    }
    auto line = static_cast<const Part::GeomLineSegment*>(geo);
    Base::Vector3d s = line->getStartPoint();
    Base::Vector3d e = line->getEndPoint();
    mid = Base::Vector2d((s.x + e.x) * 0.5, (s.y + e.y) * 0.5);
    return true;
}

/// Angle between two normalized direction vectors (0..π/2 range, ignoring sign).
double angleBetween(const Base::Vector2d& a, const Base::Vector2d& b)
{
    double dot = std::abs(a.x * b.x + a.y * b.y);
    if (dot > 1.0) {
        dot = 1.0;
    }
    return std::acos(dot);
}

/// Signed angle between two directions (for perpendicularity: compare to π/2).
double signedAngle(const Base::Vector2d& a, const Base::Vector2d& b)
{
    double dot = a.x * b.x + a.y * b.y;
    if (dot > 1.0) {
        dot = 1.0;
    }
    if (dot < -1.0) {
        dot = -1.0;
    }
    return std::acos(dot);
}

}  // namespace


std::vector<ConstraintProposal> SketchAutoConstraintEngine::analyze(
    const SketchObject* sketch,
    const Base::Vector2d& startPt,
    const Base::Vector2d& endPt,
    int newGeoId,
    double viewScale) const
{
    if (!sketch) {
        return {};
    }

    Base::Vector2d seg = endPt - startPt;
    double newLength = seg.Length();

    std::vector<ConstraintProposal> proposals;

    // Need a meaningful segment direction for parallel/perpendicular
    if (newLength > 1e-8) {
        Base::Vector2d dir(seg.x / newLength, seg.y / newLength);
        seekParallel(proposals, sketch, dir, newGeoId);
        seekPerpendicular(proposals, sketch, dir, newGeoId);
    }

    // Equal length: need non-trivial length
    if (newLength > 1e-6) {
        seekEqual(proposals, sketch, newLength, newGeoId);
    }

    // Midpoint: check if endpoint is near midpoint of any edge
    double distThreshold = MidpointDistFactor * viewScale;
    if (distThreshold > 1e-8) {
        seekMidpoint(proposals, sketch, endPt, newGeoId, distThreshold);
    }

    // Sort by confidence descending
    std::sort(proposals.begin(), proposals.end(),
              [](const ConstraintProposal& a, const ConstraintProposal& b) {
                  return a.confidence > b.confidence;
              });

    return proposals;
}


std::vector<AutoConstraint> SketchAutoConstraintEngine::toAutoConstraints(
    const std::vector<ConstraintProposal>& proposals,
    int maxCount)
{
    std::vector<AutoConstraint> result;
    int count = 0;
    for (const auto& p : proposals) {
        if (count >= maxCount) {
            break;
        }
        if (p.confidence < MinConfidence) {
            break;
        }
        AutoConstraint ac;
        ac.Type = p.type;
        ac.GeoId = p.geoId2;
        ac.PosId = p.posId2;
        result.push_back(ac);
        ++count;
    }
    return result;
}


void SketchAutoConstraintEngine::seekParallel(
    std::vector<ConstraintProposal>& out,
    const SketchObject* sketch,
    const Base::Vector2d& dir,
    int newGeoId) const
{
    const auto& geos = sketch->getInternalGeometry();
    for (int i = 0; i < static_cast<int>(geos.size()); ++i) {
        Base::Vector2d existDir;
        double existLen = 0;
        if (!getLineDir(geos[i], existDir, existLen)) {
            continue;
        }
        double angle = angleBetween(dir, existDir);
        if (angle < AngleTolerance) {
            // Confidence: closer to 0° → higher confidence
            float conf = static_cast<float>(1.0 - angle / AngleTolerance);
            if (conf >= MinConfidence) {
                ConstraintProposal p;
                p.type = Sketcher::Parallel;
                p.geoId1 = newGeoId;
                p.posId1 = Sketcher::PointPos::none;
                p.geoId2 = i;
                p.posId2 = Sketcher::PointPos::none;
                p.confidence = conf;
                out.push_back(p);
            }
        }
    }
}


void SketchAutoConstraintEngine::seekPerpendicular(
    std::vector<ConstraintProposal>& out,
    const SketchObject* sketch,
    const Base::Vector2d& dir,
    int newGeoId) const
{
    const auto& geos = sketch->getInternalGeometry();
    for (int i = 0; i < static_cast<int>(geos.size()); ++i) {
        Base::Vector2d existDir;
        double existLen = 0;
        if (!getLineDir(geos[i], existDir, existLen)) {
            continue;
        }
        double angle = signedAngle(dir, existDir);
        double deviation = std::abs(angle - M_PI / 2.0);
        if (deviation < AngleTolerance) {
            float conf = static_cast<float>(1.0 - deviation / AngleTolerance);
            if (conf >= MinConfidence) {
                ConstraintProposal p;
                p.type = Sketcher::Perpendicular;
                p.geoId1 = newGeoId;
                p.posId1 = Sketcher::PointPos::none;
                p.geoId2 = i;
                p.posId2 = Sketcher::PointPos::none;
                p.confidence = conf;
                out.push_back(p);
            }
        }
    }
}


void SketchAutoConstraintEngine::seekEqual(
    std::vector<ConstraintProposal>& out,
    const SketchObject* sketch,
    double newLength,
    int newGeoId) const
{
    const auto& geos = sketch->getInternalGeometry();
    for (int i = 0; i < static_cast<int>(geos.size()); ++i) {
        Base::Vector2d existDir;
        double existLen = 0;
        if (!getLineDir(geos[i], existDir, existLen)) {
            continue;
        }
        double relDiff = std::abs(existLen - newLength) / std::max(existLen, newLength);
        if (relDiff < LengthRelTolerance) {
            float conf = static_cast<float>(1.0 - relDiff / LengthRelTolerance);
            if (conf >= MinConfidence) {
                ConstraintProposal p;
                p.type = Sketcher::Equal;
                p.geoId1 = newGeoId;
                p.posId1 = Sketcher::PointPos::none;
                p.geoId2 = i;
                p.posId2 = Sketcher::PointPos::none;
                p.confidence = conf;
                out.push_back(p);
            }
        }
    }
}


void SketchAutoConstraintEngine::seekMidpoint(
    std::vector<ConstraintProposal>& out,
    const SketchObject* sketch,
    const Base::Vector2d& endPt,
    int newGeoId,
    double distThreshold) const
{
    const auto& geos = sketch->getInternalGeometry();
    for (int i = 0; i < static_cast<int>(geos.size()); ++i) {
        Base::Vector2d mid;
        if (!getLineMidpoint(geos[i], mid)) {
            continue;
        }
        double dist = (endPt - mid).Length();
        if (dist < distThreshold) {
            float conf = static_cast<float>(1.0 - dist / distThreshold);
            if (conf >= MinConfidence) {
                ConstraintProposal p;
                p.type = Sketcher::Symmetric;  // Midpoint → Symmetric about center
                p.geoId1 = newGeoId;
                p.posId1 = Sketcher::PointPos::end;
                p.geoId2 = i;
                p.posId2 = Sketcher::PointPos::mid;
                p.confidence = conf;
                out.push_back(p);
            }
        }
    }
}
