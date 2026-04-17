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

#include <vector>

#include <Base/Tools2D.h>
#include <Mod/Sketcher/App/Constraint.h>
#include <Mod/Sketcher/App/SketchObject.h>

#include "AutoConstraint.h"


namespace SketcherGui
{

/// Extended auto-constraint proposal with confidence scoring.
/// Supplements the existing seekAutoConstraint() strategies with
/// higher-order relationship inference (parallel, perpendicular, equal).
struct ConstraintProposal
{
    Sketcher::ConstraintType type;  ///< Proposed constraint type
    int geoId1;                     ///< First geometry element
    Sketcher::PointPos posId1;      ///< Point on first element
    int geoId2;                     ///< Second geometry element (reference)
    Sketcher::PointPos posId2;      ///< Point on second element
    float confidence;               ///< 0.0 – 1.0 confidence score
};

/** Inference engine that detects constraint-worthy relationships
 *  between the geometry currently being drawn and existing sketch geometry.
 *
 *  The existing seekAutoConstraint() in DrawSketchHandler handles:
 *   - Coincident / PointOnObject via preselection proximity
 *   - Horizontal / Vertical via drawing direction alignment
 *   - Tangent via curve-to-line tangency analysis
 *
 *  This engine adds:
 *   - Parallel:        new line direction ≈ existing line direction
 *   - Perpendicular:   new line direction ⊥ existing line direction
 *   - Equal (length):  new segment length ≈ existing segment length
 *   - Midpoint:        endpoint lands near midpoint of existing edge
 */
class SketchAutoConstraintEngine
{
public:
    /// Angular tolerance (radians) for parallel/perpendicular detection.
    static constexpr double AngleTolerance = 3.0 * M_PI / 180.0;  // 3°

    /// Relative length tolerance for equal-length detection.
    static constexpr double LengthRelTolerance = 0.03;  // 3%

    /// Distance tolerance factor (multiplied by view scale) for midpoint.
    static constexpr double MidpointDistFactor = 0.02;

    /// Minimum confidence to include a proposal.
    static constexpr float MinConfidence = 0.5f;

    /** Analyze the drawing context and return constraint proposals.
     *  @param sketch  Active SketchObject
     *  @param startPt Start point of the segment being drawn (sketch coords)
     *  @param endPt   Current cursor position (sketch coords)
     *  @param newGeoId GeoId that will be assigned to the new geometry (-1 if unknown)
     *  @param viewScale Current view scale factor (for distance thresholds)
     *  @return Sorted vector of proposals (highest confidence first)
     */
    std::vector<ConstraintProposal> analyze(
        const Sketcher::SketchObject* sketch,
        const Base::Vector2d& startPt,
        const Base::Vector2d& endPt,
        int newGeoId,
        double viewScale
    ) const;

    /** Convert the top-ranked proposals into AutoConstraint entries
     *  that the existing createAutoConstraints() can apply.
     *  @param proposals  Proposals from analyze()
     *  @param maxCount   Maximum number to convert (default 2)
     *  @return AutoConstraint vector suitable for createAutoConstraints()
     */
    static std::vector<AutoConstraint> toAutoConstraints(
        const std::vector<ConstraintProposal>& proposals,
        int maxCount = 2
    );

private:
    void seekParallel(
        std::vector<ConstraintProposal>& out,
        const Sketcher::SketchObject* sketch,
        const Base::Vector2d& dir,
        int newGeoId
    ) const;

    void seekPerpendicular(
        std::vector<ConstraintProposal>& out,
        const Sketcher::SketchObject* sketch,
        const Base::Vector2d& dir,
        int newGeoId
    ) const;

    void seekEqual(
        std::vector<ConstraintProposal>& out,
        const Sketcher::SketchObject* sketch,
        double newLength,
        int newGeoId
    ) const;

    void seekMidpoint(
        std::vector<ConstraintProposal>& out,
        const Sketcher::SketchObject* sketch,
        const Base::Vector2d& endPt,
        int newGeoId,
        double distThreshold
    ) const;
};

}  // namespace SketcherGui
