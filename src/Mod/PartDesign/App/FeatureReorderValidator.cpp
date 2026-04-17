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
#include <set>

#include <App/Document.h>
#include <App/DocumentObject.h>
#include <Base/Console.h>

#include "Body.h"
#include "FeatureReorderValidator.h"


using namespace PartDesign;

namespace
{

/// Get index of @a obj in the body's group, or -1 if not found.
int indexInBody(const Body* body, const App::DocumentObject* obj)
{
    const auto& group = body->Group.getValues();
    for (int i = 0; i < static_cast<int>(group.size()); ++i) {
        if (group[i] == obj) {
            return i;
        }
    }
    return -1;
}

/// Collect all direct dependencies of @a obj that are also in @a body.
std::set<const App::DocumentObject*> depsInBody(const Body* body,
                                                 const App::DocumentObject* obj)
{
    std::set<const App::DocumentObject*> result;
    const auto& group = body->Group.getValues();
    std::set<const App::DocumentObject*> bodySet(group.begin(), group.end());

    for (auto* dep : obj->getOutList()) {
        if (bodySet.count(dep)) {
            result.insert(dep);
        }
    }
    return result;
}

/// Collect all objects that depend on @a obj and are in @a body (dependents).
std::set<const App::DocumentObject*> dependentsInBody(const Body* body,
                                                       const App::DocumentObject* obj)
{
    std::set<const App::DocumentObject*> result;
    const auto& group = body->Group.getValues();
    std::set<const App::DocumentObject*> bodySet(group.begin(), group.end());

    for (auto* dep : obj->getInList()) {
        if (bodySet.count(dep)) {
            result.insert(dep);
        }
    }
    return result;
}

}  // namespace


FeatureReorderValidator::ValidationResult FeatureReorderValidator::validate(
    const Body* body,
    const App::DocumentObject* feature,
    int targetIndex)
{
    ValidationResult result;

    if (!body || !feature) {
        result.reason = "Null body or feature.";
        return result;
    }

    const auto& group = body->Group.getValues();
    int currentIndex = indexInBody(body, feature);
    if (currentIndex < 0) {
        result.reason = "Feature is not in this body.";
        return result;
    }

    int groupSize = static_cast<int>(group.size());

    // Earliest position: must be after all dependencies
    int earliest = 0;
    for (auto* dep : depsInBody(body, feature)) {
        int depIdx = indexInBody(body, dep);
        if (depIdx >= 0) {
            earliest = std::max(earliest, depIdx + 1);
        }
    }

    // Latest position: must be before all dependents
    int latest = groupSize - 1;
    for (auto* dep : dependentsInBody(body, feature)) {
        int depIdx = indexInBody(body, dep);
        if (depIdx >= 0) {
            latest = std::min(latest, depIdx - 1);
        }
    }

    result.earliestIndex = earliest;
    result.latestIndex = latest;

    if (earliest > latest) {
        result.reason = "Circular or conflicting dependencies prevent reordering.";
        return result;
    }

    if (targetIndex < earliest) {
        result.reason = "Cannot move before dependencies (earliest: index "
                        + std::to_string(earliest) + ").";
        return result;
    }

    if (targetIndex > latest) {
        result.reason = "Cannot move after features that depend on this "
                        "(latest: index " + std::to_string(latest) + ").";
        return result;
    }

    result.isValid = true;
    return result;
}


bool FeatureReorderValidator::executeReorder(
    Body* body,
    App::DocumentObject* feature,
    int targetIndex)
{
    auto validation = validate(body, feature, targetIndex);
    if (!validation.isValid) {
        Base::Console().Error("FeatureReorderValidator: %s\n", validation.reason.c_str());
        return false;
    }

    auto* doc = body->getDocument();
    if (!doc) {
        return false;
    }

    const auto& group = body->Group.getValues();
    int groupSize = static_cast<int>(group.size());
    if (targetIndex < 0 || targetIndex >= groupSize) {
        return false;
    }

    // Determine the target feature (insert before/after)
    App::DocumentObject* target = group[targetIndex];
    int currentIndex = indexInBody(body, feature);

    doc->openTransaction("Reorder Feature");

    // Remove then re-insert
    body->removeObject(feature);

    // After removal, indices shift — recalculate target
    bool insertAfter = (targetIndex > currentIndex);
    body->insertObject(feature, target, insertAfter);

    doc->commitTransaction();

    // Trigger recompute from the earlier of old/new position
    doc->recompute();

    Base::Console().Message("FeatureReorderValidator: Moved '%s' to index %d.\n",
                            feature->getNameInDocument(), targetIndex);
    return true;
}
