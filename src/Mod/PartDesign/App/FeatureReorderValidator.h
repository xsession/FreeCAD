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

#include <string>
#include <vector>

#include <Mod/PartDesign/PartDesignGlobal.h>


namespace App
{
class DocumentObject;
}

namespace PartDesign
{
class Body;

/** Validate whether a feature can be reordered within a PartDesign::Body.
 *
 *  A feature cannot move before any of its dependencies (inputs).
 *  This validator checks the dependency graph and provides:
 *   - Binary can/cannot-move decision
 *   - Earliest valid position (closest to top)
 *   - Latest valid position (closest to bottom)
 *   - Human-readable reason for rejection
 *
 *  Intended to be called from TreeWidget::dropEvent() / dropInObject()
 *  to gate drag-to-reorder operations.
 */
class PartDesignExport FeatureReorderValidator
{
public:
    struct ValidationResult
    {
        bool isValid = false;
        int  earliestIndex = -1;     ///< Earliest allowed position (0-based in body feature list)
        int  latestIndex = -1;       ///< Latest allowed position
        std::string reason;          ///< Explanation if invalid
    };

    /** Check if @a feature can be moved to @a targetIndex within @a body.
     *  @param body          The PartDesign body containing the feature
     *  @param feature       The feature being moved
     *  @param targetIndex   Proposed insertion index (0-based in body's Group list)
     *  @return Validation result with earliest/latest bounds and reason if invalid
     */
    static ValidationResult validate(
        const Body* body,
        const App::DocumentObject* feature,
        int targetIndex
    );

    /** Execute the reorder: move @a feature to @a targetIndex within @a body.
     *  Opens a transaction, calls Body::insertObject(), updates Tip if needed,
     *  and triggers partial recompute from the moved feature downward.
     *  @return true on success
     */
    static bool executeReorder(
        Body* body,
        App::DocumentObject* feature,
        int targetIndex
    );
};

}  // namespace PartDesign
