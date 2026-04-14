/***************************************************************************
 *   Copyright (c) 2026 FreeCAD contributors                              *
 *                                                                         *
 *   This file is part of the FreeCAD CAx development system.              *
 *                                                                         *
 *   This library is free software; you can redistribute it and/or         *
 *   modify it under the terms of the GNU Library General Public           *
 *   License as published by the Free Software Foundation; either          *
 *   version 2 of the License, or (at your option) any later version.      *
 *                                                                         *
 *   This library is distributed in the hope that it will be useful,       *
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

#include "SoFCSmallFeatureCull.h"

#include <Inventor/actions/SoGetBoundingBoxAction.h>
#include <Inventor/actions/SoGLRenderAction.h>
#include <Inventor/elements/SoModelMatrixElement.h>
#include <Inventor/elements/SoViewVolumeElement.h>
#include <Inventor/elements/SoViewportRegionElement.h>
#include <Inventor/misc/SoState.h>

#include <Gui/SoFCInteractiveElement.h>

#include <algorithm>
#include <cmath>

using namespace Gui;

SO_NODE_SOURCE(SoFCSmallFeatureCull)

void SoFCSmallFeatureCull::initClass()
{
    SO_NODE_INIT_CLASS(SoFCSmallFeatureCull, SoSeparator, "Separator");
}

SoFCSmallFeatureCull::SoFCSmallFeatureCull()
{
    SO_NODE_CONSTRUCTOR(SoFCSmallFeatureCull);
    SO_NODE_ADD_FIELD(minScreenArea, (25.0F));  // 5×5 pixels

    // Enable bounding box caching so the bbox is maintained cheaply.
    // Coin3D will cache the bbox and recompute only when children change.
    boundingBoxCaching = SoSeparator::ON;
    // Disable render caching — pcRoot handles it
    renderCaching = SoSeparator::OFF;
}

// ---------------------------------------------------------------------------
//  Check whether the projected screen area is below the cull threshold.
//
//  Strategy: get the bounding box (cached by SoSeparator), compute a
//  bounding sphere, project it to screen using the current view volume,
//  and compare the projected area to the threshold.
// ---------------------------------------------------------------------------

bool SoFCSmallFeatureCull::shouldCull(SoGLRenderAction* action) const
{
    float threshold = minScreenArea.getValue();
    if (threshold <= 0.0F) {
        return false;  // culling disabled
    }

    SoState* state = action->getState();

    // Phase F: During interactive navigation, use 4× the normal threshold
    // to aggressively cull more small features for smooth framerate.
    // This mimics Autodesk Inventor's LOD scaling during rotation/pan.
    if (SoFCInteractiveElement::get(state)) {
        threshold *= 4.0F;
    }

    // Get viewport dimensions
    const SbViewportRegion& vp = SoViewportRegionElement::get(state);
    SbVec2s vpSize = vp.getViewportSizePixels();
    if (vpSize[0] <= 0 || vpSize[1] <= 0) {
        return false;
    }

    // Get our bounding box.  With boundingBoxCaching = ON on this
    // SoSeparator, this hits the Coin3D internal cache on most frames
    // (O(1) unless children changed since last query).
    SoGetBoundingBoxAction bbAction(vp);
    bbAction.apply(const_cast<SoFCSmallFeatureCull*>(this));
    SbBox3f bbox = bbAction.getBoundingBox();
    if (bbox.isEmpty()) {
        return false;  // no geometry — don't cull
    }

    // Compute bounding sphere in local coordinates
    SbVec3f minPt;
    SbVec3f maxPt;
    bbox.getBounds(minPt, maxPt);
    float radius = (maxPt - minPt).length() * 0.5F;
    SbVec3f center = (minPt + maxPt) * 0.5F;

    // Transform center to world space via the current model matrix
    const SbMatrix& modelMatrix = SoModelMatrixElement::get(state);
    SbVec3f worldCenter;
    modelMatrix.multVecMatrix(center, worldCenter);

    // Scale radius by the maximum scale factor of the model matrix
    SbVec3f xAxis(modelMatrix[0][0], modelMatrix[0][1], modelMatrix[0][2]);
    SbVec3f yAxis(modelMatrix[1][0], modelMatrix[1][1], modelMatrix[1][2]);
    SbVec3f zAxis(modelMatrix[2][0], modelMatrix[2][1], modelMatrix[2][2]);
    float maxScale = std::max({xAxis.length(), yAxis.length(), zAxis.length()});
    radius *= maxScale;

    // Get view volume for projection
    const SbViewVolume& vv = SoViewVolumeElement::get(state);

    // Compute distance from camera to object center
    SbVec3f camPos = vv.getProjectionPoint();
    float dist = (worldCenter - camPos).length();

    // If we're inside or very close to the object, always render
    if (dist < radius * 2.0F) {
        return false;
    }

    // Compute projected diameter in screen pixels
    float projPixels;
    if (vv.getProjectionType() == SbViewVolume::PERSPECTIVE) {
        float halfHeight = vv.getHeight() * 0.5F;
        projPixels = (radius / dist)
            * (static_cast<float>(vpSize[1]) / (2.0F * halfHeight));
    }
    else {
        // Orthographic: radius relative to view height
        projPixels = (radius / vv.getHeight()) * static_cast<float>(vpSize[1]);
    }

    float screenArea = projPixels * projPixels;
    return screenArea < threshold;
}

void SoFCSmallFeatureCull::GLRenderBelowPath(SoGLRenderAction* action)
{
    if (shouldCull(action)) {
        return;  // skip rendering entirely
    }
    inherited::GLRenderBelowPath(action);
}

void SoFCSmallFeatureCull::GLRenderInPath(SoGLRenderAction* action)
{
    if (action->getCurPathCode() == SoAction::BELOW_PATH) {
        GLRenderBelowPath(action);
        return;
    }
    // In-path rendering: always render (object is on the path, e.g. selection)
    inherited::GLRenderInPath(action);
}
