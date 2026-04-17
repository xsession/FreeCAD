// SPDX-License-Identifier: LGPL-2.1-or-later
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
 *   This library  is distributed in the hope that it will be useful,      *
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
 *   GNU Library General Public License for more details.                  *
 *                                                                         *
 *   You should have received a copy of the GNU Library General Public     *
 *   License along with this library; see the file COPYING.LIB. If not,    *
 *   write to the Free Software Foundation, Inc., 59 Temple Place,         *
 *   Suite 330, Boston, MA  02111-1307, USA                                *
 *                                                                         *
 ***************************************************************************/

#include <algorithm>
#include <Inventor/nodes/SoSeparator.h>
#include <Inventor/nodes/SoSwitch.h>
#include <Inventor/nodes/SoTransform.h>
#include <Inventor/nodes/SoMaterial.h>
#include <Inventor/nodes/SoCone.h>
#include <Inventor/nodes/SoCylinder.h>
#include <Inventor/nodes/SoLineSet.h>
#include <Inventor/nodes/SoCoordinate3.h>
#include <Inventor/nodes/SoDrawStyle.h>

#include <App/DocumentObject.h>
#include <App/PropertyStandard.h>
#include <App/PropertyLinks.h>
#include <Base/Console.h>
#include <Base/Placement.h>
#include <Base/Rotation.h>

#include <Mod/Assembly/App/AssemblyObject.h>

#include "DofOverlay.h"

#include <cmath>
#include <unordered_map>
#include <unordered_set>

using namespace AssemblyGui;

namespace
{

// Joint type names (matches Python JointObject.py JointTypes list)
enum class JointKind
{
    Fixed,         // 0 DOF
    Revolute,      // 1 rot
    Cylindrical,   // 1 rot + 1 trans (along same axis)
    Slider,        // 1 trans
    Ball,          // 3 rot
    Distance,      // Keeps distance — contributes 1 constraint
    Parallel,      // Axes parallel — 2 rot constraints
    Perpendicular, // Axes perpendicular — 1 rot constraint
    Angle,         // Fixed angle — 1 rot constraint
    RackPinion,
    Screw,
    Gears,
    Belt,
    Unknown
};

JointKind jointKindFromType(int typeIndex)
{
    if (typeIndex >= 0 && typeIndex <= static_cast<int>(JointKind::Belt)) {
        return static_cast<JointKind>(typeIndex);
    }
    return JointKind::Unknown;
}

/// Determine the joint axis in world space from joint placement
Base::Vector3d getJointAxis(App::DocumentObject* joint, const char* plcProp)
{
    auto* prop = dynamic_cast<App::PropertyPlacement*>(joint->getPropertyByName(plcProp));
    if (!prop) {
        return Base::Vector3d(0, 0, 1);
    }
    // The joint Z-axis is the constraint axis
    Base::Vector3d zAxis(0, 0, 1);
    prop->getValue().getRotation().multVec(zAxis, zAxis);
    return zAxis;
}

/// Get object center from its Placement property
Base::Vector3d getPartCenter(App::DocumentObject* obj)
{
    auto* plcProp = dynamic_cast<App::PropertyPlacement*>(
        obj->getPropertyByName("Placement"));
    if (!plcProp) {
        return Base::Vector3d(0, 0, 0);
    }
    return plcProp->getValue().getPosition();
}

/// Get the target part on one side of a joint
App::DocumentObject* getJointPart(App::DocumentObject* joint, const char* refPropName)
{
    auto* prop = dynamic_cast<App::PropertyXLinkSub*>(
        joint->getPropertyByName(refPropName));
    if (!prop) {
        return nullptr;
    }
    return prop->getValue();
}

constexpr float ArrowLength = 40.0f;   // mm
constexpr float ArrowRadius = 1.5f;    // mm
constexpr float ConeHeight  = 6.0f;    // mm
constexpr float ConeRadius  = 3.0f;    // mm
constexpr int   ArcSegments = 24;
constexpr float ArcRadius   = 25.0f;   // mm
constexpr float ArcAngle    = 4.71f;   // ~270 degrees in radians

}  // anonymous namespace


// ============================================================================
// DofOverlay
// ============================================================================

DofOverlay::DofOverlay() = default;

DofOverlay::~DofOverlay()
{
    clear();
}

void DofOverlay::clear()
{
    if (rootSwitch) {
        rootSwitch->removeAllChildren();
        rootSwitch->unref();
        rootSwitch = nullptr;
    }
}

void DofOverlay::setVisible(bool visible)
{
    if (rootSwitch) {
        rootSwitch->whichChild.setValue(visible ? SO_SWITCH_ALL : SO_SWITCH_NONE);
    }
}

std::vector<DofIndicator> DofOverlay::analyze(Assembly::AssemblyObject* assembly)
{
    std::vector<DofIndicator> result;
    if (!assembly) {
        return result;
    }

    // Get all joints
    auto joints = assembly->getJoints(false);

    // Collect grounded parts
    auto grounded = assembly->getGroundedParts();

    // For each non-grounded part, determine remaining DOF from connected joints
    // We track per-part: which translational and rotational DOFs are constrained
    struct PartDofState
    {
        App::DocumentObject* obj{nullptr};
        Base::Vector3d center;
        // Constrained translation axes (unit vectors)
        std::vector<Base::Vector3d> transConstrained;
        // Constrained rotation axes
        std::vector<Base::Vector3d> rotConstrained;
        bool fullyFixed{false};
    };

    std::unordered_map<App::DocumentObject*, PartDofState> partStates;

    // Initialize all parts
    auto children = assembly->getObjects();
    for (auto* child : children) {
        if (!child || grounded.count(child)) {
            continue;
        }
        // Only consider objects with Placement (actual parts)
        if (!child->getPropertyByName("Placement")) {
            continue;
        }
        // Skip joint objects, groups, etc
        if (child->getPropertyByName("Reference1")) {
            continue;
        }
        auto& state = partStates[child];
        state.obj = child;
        state.center = getPartCenter(child);
    }

    // Process each joint and mark constrained DOFs on connected parts
    for (auto* joint : joints) {
        if (!joint) {
            continue;
        }

        // Get joint type
        auto* typeProp = dynamic_cast<App::PropertyEnumeration*>(
            joint->getPropertyByName("JointType"));
        if (!typeProp) {
            continue;
        }
        JointKind kind = jointKindFromType(typeProp->getValue());

        // Get the two parts
        App::DocumentObject* part1 = getJointPart(joint, "Reference1");
        App::DocumentObject* part2 = getJointPart(joint, "Reference2");

        // Get joint axis (from Placement1 — the local coordinate system)
        Base::Vector3d axis = getJointAxis(joint, "Placement1");

        // For each non-grounded part in this joint, apply constraints
        auto applyConstraints = [&](App::DocumentObject* part) {
            if (!part || grounded.count(part)) {
                return;
            }
            auto it = partStates.find(part);
            if (it == partStates.end()) {
                return;
            }
            auto& state = it->second;

            switch (kind) {
            case JointKind::Fixed:
                state.fullyFixed = true;
                break;

            case JointKind::Revolute:
                // Locks all translation + 2 of 3 rotations (free: rotation around axis)
                state.transConstrained.push_back(Base::Vector3d(1, 0, 0));
                state.transConstrained.push_back(Base::Vector3d(0, 1, 0));
                state.transConstrained.push_back(Base::Vector3d(0, 0, 1));
                // Constrain rotations perpendicular to axis
                {
                    Base::Vector3d perp1, perp2;
                    if (std::abs(axis.x) < 0.9) {
                        perp1 = Base::Vector3d(1, 0, 0).Cross(axis);
                    }
                    else {
                        perp1 = Base::Vector3d(0, 1, 0).Cross(axis);
                    }
                    perp1.Normalize();
                    perp2 = axis.Cross(perp1);
                    state.rotConstrained.push_back(perp1);
                    state.rotConstrained.push_back(perp2);
                }
                break;

            case JointKind::Cylindrical:
                // Free: translation along axis + rotation around axis
                // Constrain translations perpendicular to axis
                {
                    Base::Vector3d perp1c, perp2c;
                    if (std::abs(axis.x) < 0.9) {
                        perp1c = Base::Vector3d(1, 0, 0).Cross(axis);
                    }
                    else {
                        perp1c = Base::Vector3d(0, 1, 0).Cross(axis);
                    }
                    perp1c.Normalize();
                    perp2c = axis.Cross(perp1c);
                    state.transConstrained.push_back(perp1c);
                    state.transConstrained.push_back(perp2c);
                    // Constrain rotations perpendicular to axis
                    state.rotConstrained.push_back(perp1c);
                    state.rotConstrained.push_back(perp2c);
                }
                break;

            case JointKind::Slider:
                // Free: translation along axis only
                // Constrain all rotations + translation perpendicular to axis
                state.rotConstrained.push_back(Base::Vector3d(1, 0, 0));
                state.rotConstrained.push_back(Base::Vector3d(0, 1, 0));
                state.rotConstrained.push_back(Base::Vector3d(0, 0, 1));
                {
                    Base::Vector3d perp1s, perp2s;
                    if (std::abs(axis.x) < 0.9) {
                        perp1s = Base::Vector3d(1, 0, 0).Cross(axis);
                    }
                    else {
                        perp1s = Base::Vector3d(0, 1, 0).Cross(axis);
                    }
                    perp1s.Normalize();
                    perp2s = axis.Cross(perp1s);
                    state.transConstrained.push_back(perp1s);
                    state.transConstrained.push_back(perp2s);
                }
                break;

            case JointKind::Ball:
                // Locks all translation, all rotations free
                state.transConstrained.push_back(Base::Vector3d(1, 0, 0));
                state.transConstrained.push_back(Base::Vector3d(0, 1, 0));
                state.transConstrained.push_back(Base::Vector3d(0, 0, 1));
                break;

            case JointKind::Parallel:
                // Constrains 2 rotational DOFs (axes must be parallel)
                {
                    Base::Vector3d perp1p, perp2p;
                    if (std::abs(axis.x) < 0.9) {
                        perp1p = Base::Vector3d(1, 0, 0).Cross(axis);
                    }
                    else {
                        perp1p = Base::Vector3d(0, 1, 0).Cross(axis);
                    }
                    perp1p.Normalize();
                    perp2p = axis.Cross(perp1p);
                    state.rotConstrained.push_back(perp1p);
                    state.rotConstrained.push_back(perp2p);
                }
                break;

            default:
                // Distance, Perpendicular, Angle, RackPinion, Screw, Gears, Belt
                // These are more complex coupling constraints — skip for now
                break;
            }
        };

        applyConstraints(part1);
        applyConstraints(part2);
    }

    // For each part, determine remaining free DOFs
    auto isAxisConstrained = [](const std::vector<Base::Vector3d>& constrained,
                                const Base::Vector3d& testAxis) -> bool {
        // Check if testAxis can be expressed as a combination of constrained axes
        // Simplified: check if any constrained axis is nearly parallel
        for (const auto& c : constrained) {
            double dot = std::abs(c.Dot(testAxis));
            if (dot > 0.9) {
                return true;
            }
        }
        // If 2+ constrained axes span a plane containing testAxis, it's constrained
        if (constrained.size() >= 2) {
            // Check if any pair spans the axis
            for (size_t i = 0; i < constrained.size(); ++i) {
                for (size_t j = i + 1; j < constrained.size(); ++j) {
                    Base::Vector3d normal = constrained[i].Cross(constrained[j]);
                    if (normal.Length() > 0.1) {
                        normal.Normalize();
                        double dot = std::abs(normal.Dot(testAxis));
                        if (dot < 0.1) {
                            // testAxis lies in the plane spanned by these two
                            return true;
                        }
                    }
                }
            }
        }
        if (constrained.size() >= 3) {
            return true;  // 3 independent axes = fully constrained
        }
        return false;
    };

    Base::Vector3d worldAxes[3] = {
        Base::Vector3d(1, 0, 0),
        Base::Vector3d(0, 1, 0),
        Base::Vector3d(0, 0, 1)
    };

    for (auto& [obj, state] : partStates) {
        if (state.fullyFixed) {
            continue;  // No DOF indicators needed
        }

        // Check each world axis for free translational DOF
        for (const auto& ax : worldAxes) {
            if (!isAxisConstrained(state.transConstrained, ax)) {
                DofIndicator ind;
                ind.kind = DofIndicator::Kind::Translation;
                ind.axis = ax;
                ind.origin = state.center;
                result.push_back(ind);
            }
        }

        // Check each world axis for free rotational DOF
        for (const auto& ax : worldAxes) {
            if (!isAxisConstrained(state.rotConstrained, ax)) {
                DofIndicator ind;
                ind.kind = DofIndicator::Kind::Rotation;
                ind.axis = ax;
                ind.origin = state.center;
                result.push_back(ind);
            }
        }
    }

    return result;
}

SoSeparator* DofOverlay::makeArrow(const DofIndicator& dof, float scale)
{
    auto* sep = new SoSeparator;

    // Material: green for translational DOF
    auto* mat = new SoMaterial;
    mat->diffuseColor.setValue(0.2f, 0.8f, 0.2f);
    mat->transparency.setValue(0.3f);
    sep->addChild(mat);

    // Transform to position at part center, oriented along DOF axis
    auto* xform = new SoTransform;
    xform->translation.setValue(
        static_cast<float>(dof.origin.x),
        static_cast<float>(dof.origin.y),
        static_cast<float>(dof.origin.z)
    );

    // Rotate from Y-up (Coin3D cylinder default) to DOF axis
    Base::Vector3d yAxis(0, 1, 0);
    Base::Vector3d rotAxis = yAxis.Cross(dof.axis);
    double dot = yAxis.Dot(dof.axis);
    if (rotAxis.Length() > 1e-6) {
        rotAxis.Normalize();
        float angle = static_cast<float>(std::acos(std::clamp(dot, -1.0, 1.0)));
        xform->rotation.setValue(SbVec3f(
            static_cast<float>(rotAxis.x),
            static_cast<float>(rotAxis.y),
            static_cast<float>(rotAxis.z)
        ), angle);
    }
    else if (dot < 0) {
        // 180-degree rotation
        xform->rotation.setValue(SbVec3f(1, 0, 0), static_cast<float>(M_PI));
    }
    sep->addChild(xform);

    // Shaft (cylinder)
    auto* shaft = new SoCylinder;
    shaft->radius.setValue(ArrowRadius * scale);
    shaft->height.setValue(ArrowLength * scale);
    sep->addChild(shaft);

    // Arrowhead (cone at tip)
    auto* tipXform = new SoTransform;
    tipXform->translation.setValue(0, (ArrowLength * scale) / 2.0f + (ConeHeight * scale) / 2.0f, 0);
    sep->addChild(tipXform);

    auto* cone = new SoCone;
    cone->bottomRadius.setValue(ConeRadius * scale);
    cone->height.setValue(ConeHeight * scale);
    sep->addChild(cone);

    return sep;
}

SoSeparator* DofOverlay::makeArc(const DofIndicator& dof, float scale)
{
    auto* sep = new SoSeparator;

    // Material: blue for rotational DOF
    auto* mat = new SoMaterial;
    mat->diffuseColor.setValue(0.2f, 0.4f, 0.9f);
    mat->transparency.setValue(0.3f);
    sep->addChild(mat);

    // Transform to part center
    auto* xform = new SoTransform;
    xform->translation.setValue(
        static_cast<float>(dof.origin.x),
        static_cast<float>(dof.origin.y),
        static_cast<float>(dof.origin.z)
    );

    // Rotate from Z-up to DOF axis
    Base::Vector3d zAxis(0, 0, 1);
    Base::Vector3d rotAxis = zAxis.Cross(dof.axis);
    double dot = zAxis.Dot(dof.axis);
    if (rotAxis.Length() > 1e-6) {
        rotAxis.Normalize();
        float angle = static_cast<float>(std::acos(std::clamp(dot, -1.0, 1.0)));
        xform->rotation.setValue(SbVec3f(
            static_cast<float>(rotAxis.x),
            static_cast<float>(rotAxis.y),
            static_cast<float>(rotAxis.z)
        ), angle);
    }
    else if (dot < 0) {
        xform->rotation.setValue(SbVec3f(1, 0, 0), static_cast<float>(M_PI));
    }
    sep->addChild(xform);

    // Draw arc as a line strip in the XY plane (around Z axis, which we rotated to match dof.axis)
    auto* drawStyle = new SoDrawStyle;
    drawStyle->lineWidth.setValue(3.0f);
    sep->addChild(drawStyle);

    auto* coords = new SoCoordinate3;
    float radius = ArcRadius * scale;
    for (int i = 0; i <= ArcSegments; ++i) {
        float t = (static_cast<float>(i) / static_cast<float>(ArcSegments)) * ArcAngle;
        float x = radius * std::cos(t);
        float y = radius * std::sin(t);
        coords->point.set1Value(i, x, y, 0.0f);
    }
    sep->addChild(coords);

    auto* lineSet = new SoLineSet;
    lineSet->numVertices.setValue(ArcSegments + 1);
    sep->addChild(lineSet);

    // Small arrowhead at the arc tip
    float endAngle = ArcAngle;
    auto* tipXform = new SoTransform;
    tipXform->translation.setValue(
        radius * std::cos(endAngle),
        radius * std::sin(endAngle),
        0
    );
    // Rotate cone to point tangent to the arc
    float tangentAngle = endAngle + static_cast<float>(M_PI) / 2.0f;
    tipXform->rotation.setValue(SbVec3f(0, 0, 1), tangentAngle);
    sep->addChild(tipXform);

    auto* tipCone = new SoCone;
    tipCone->bottomRadius.setValue(ConeRadius * scale * 0.6f);
    tipCone->height.setValue(ConeHeight * scale * 0.6f);
    sep->addChild(tipCone);

    return sep;
}

SoSwitch* DofOverlay::buildOverlay(Assembly::AssemblyObject* assembly)
{
    clear();

    rootSwitch = new SoSwitch;
    rootSwitch->ref();
    rootSwitch->whichChild.setValue(SO_SWITCH_ALL);

    auto indicators = analyze(assembly);
    if (indicators.empty()) {
        rootSwitch->whichChild.setValue(SO_SWITCH_NONE);
        return rootSwitch;
    }

    auto* container = new SoSeparator;
    rootSwitch->addChild(container);

    // Scale based on assembly bounding box (heuristic: 1.0 for typical assemblies)
    float scale = 1.0f;

    for (const auto& dof : indicators) {
        if (dof.kind == DofIndicator::Kind::Translation) {
            container->addChild(makeArrow(dof, scale));
        }
        else {
            container->addChild(makeArc(dof, scale));
        }
    }

    return rootSwitch;
}
