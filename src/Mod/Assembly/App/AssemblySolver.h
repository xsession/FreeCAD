// SPDX-License-Identifier: LGPL-2.1-or-later
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

#include <memory>
#include <string>
#include <vector>

#include <Base/Placement.h>
#include <Mod/Assembly/AssemblyGlobal.h>

namespace App {
class DocumentObject;
}

namespace Assembly {

class AssemblyObject;

/// Joint types supported by the solver (§7.3.1).
enum class JointType : int {
    Fixed       = 0,
    Revolute    = 1,
    Prismatic   = 2,
    Cylindrical = 3,
    Planar      = 4,
    Ball        = 5,
    RackPinion  = 6,
    Screw       = 7,
    Gear        = 8,
    Distance    = 9,
    Angle       = 10,
};

/// Lightweight description of a joint between two assembly parts.
struct AssemblyExport Joint
{
    std::string name;
    JointType type = JointType::Fixed;
    App::DocumentObject* part1 = nullptr;
    App::DocumentObject* part2 = nullptr;
    Base::Placement frame1;         ///< attachment on part1
    Base::Placement frame2;         ///< attachment on part2
    double parameter = 0.0;        ///< joint parameter (distance, angle, ratio, etc.)
    double limitLow  = 0.0;
    double limitHigh = 0.0;
    bool   hasLimits = false;
};

/// Result of a solver run.
struct AssemblyExport SolveResult
{
    enum Status {
        Success = 0,
        RedundantConstraints,
        InsufficientConstraints,
        Singular,
        Failed
    };

    Status status = Failed;
    int    iterations = 0;
    double residual   = 0.0;

    /// Updated placements indexed in the same order as the parts vector
    /// passed to AssemblySolver::solve().
    std::vector<Base::Placement> placements;

    /// Human-readable diagnostic string
    std::string message;

    /// Indices of over-constrained joints (if status == RedundantConstraints)
    std::vector<int> redundantJoints;
};

/// High-level C++ assembly constraint solver.
///
/// This is a thin wrapper around the OndselSolver / MbD backend that
/// provides a simpler, typed API for the rest of FreeCAD.
///
/// Usage:
/// @code
///     AssemblySolver solver;
///     solver.addPart(partObj, placement);
///     solver.addJoint(joint);
///     auto result = solver.solve();
///     if (result.status == SolveResult::Success) { ... }
/// @endcode
class AssemblyExport AssemblySolver
{
public:
    AssemblySolver();
    ~AssemblySolver();

    /// Remove all parts and joints.
    void clear();

    /// Add a part to the solver.  Returns the part index.
    int addPart(App::DocumentObject* obj, const Base::Placement& placement,
                double mass = 1.0);

    /// Add a joint between two previously-added parts.  Returns the joint index.
    int addJoint(const Joint& joint);

    /// Run the solver.  Returns a SolveResult with updated placements.
    SolveResult solve();

    /// Convenience: solve an entire AssemblyObject in place.
    static SolveResult solveAssembly(AssemblyObject* assembly);

    /// Compute remaining DOF for the current system.
    int degreesOfFreedom() const;

    /// Return joint count.
    int jointCount() const { return static_cast<int>(_joints.size()); }

    /// Return part count.
    int partCount() const { return static_cast<int>(_parts.size()); }

private:
    struct PartEntry {
        App::DocumentObject* obj;
        Base::Placement placement;
        double mass;
    };

    std::vector<PartEntry> _parts;
    std::vector<Joint> _joints;
};

} // namespace Assembly
