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

#pragma once

#include <Inventor/fields/SoSFFloat.h>
#include <Inventor/nodes/SoSeparator.h>

#include <FCGlobal.h>

namespace Gui {

/**
 * SoFCSmallFeatureCull — screen-area based LOD culling node.
 *
 * A lightweight SoSeparator subclass that skips rendering its children when
 * the bounding box projects to fewer than `minScreenArea` pixels² on screen.
 * This is critical for large assemblies where hundreds of distant parts are
 * tiny specks — skipping their full geometry traversal provides a massive
 * rendering speedup.
 *
 * Uses the parent SoSeparator's bounding box cache (boundingBoxCaching = ON)
 * so the projected area check costs only a matrix multiply + comparison per
 * object per frame — negligible compared to actually traversing the geometry.
 *
 * Hierarchy (in ViewProviderPartExt):
 *   pcRoot (SoFCSelectionRoot)
 *     └── pcTransform
 *     └── SoFCSmallFeatureCull   ← this node
 *           └── coords (SoCoordinate3)
 *           └── pcModeSwitch (SoSwitch)
 */
class GuiExport SoFCSmallFeatureCull : public SoSeparator
{
    using inherited = SoSeparator;
    SO_NODE_HEADER(SoFCSmallFeatureCull);

public:
    static void initClass();
    SoFCSmallFeatureCull();

    /// Minimum projected screen area in pixels² — below this, children are
    /// not rendered.  Default 25.0 (≈ 5×5 pixel square).
    SoSFFloat minScreenArea;

    void GLRenderBelowPath(SoGLRenderAction* action) override;
    void GLRenderInPath(SoGLRenderAction* action) override;

protected:
    ~SoFCSmallFeatureCull() override = default;

private:
    bool shouldCull(SoGLRenderAction* action) const;
};

} // namespace Gui
