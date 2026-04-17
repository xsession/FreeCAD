// SPDX-License-Identifier: LGPL-2.1-or-later

/***************************************************************************
 *   Copyright (c) 2026 FreeCAD contributors                              *
 *                                                                         *
 *   This file is part of FreeCAD.                                         *
 *                                                                         *
 *   FreeCAD is free software: you can redistribute it and/or modify it    *
 *   under the terms of the GNU Lesser General Public License as           *
 *   published by the Free Software Foundation, either version 2.1 of the  *
 *   License, or (at your option) any later version.                       *
 *                                                                         *
 *   FreeCAD is distributed in the hope that it will be useful, but        *
 *   WITHOUT ANY WARRANTY; without even the implied warranty of            *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU      *
 *   Lesser General Public License for more details.                       *
 *                                                                         *
 *   You should have received a copy of the GNU Lesser General Public      *
 *   License along with FreeCAD. If not, see                               *
 *   <https://www.gnu.org/licenses/>.                                      *
 *                                                                         *
 **************************************************************************/

#pragma once

#include <string>
#include <variant>
#include <vector>

#include <Mod/Part/PartGlobal.h>
#include "TopoShape.h"

namespace OcctService
{

/// Error information from a failed OCCT operation.
struct PartExport OcctError
{
    std::string message;       ///< Human-readable error description.
    std::string occtClass;     ///< OCCT exception class name (e.g. "Standard_NullObject").
    std::string operation;     ///< The operation that failed (e.g. "fuse", "fillet").

    OcctError() = default;
    OcctError(std::string msg, std::string cls, std::string op)
        : message(std::move(msg))
        , occtClass(std::move(cls))
        , operation(std::move(op))
    {}
};

/// Result type: either a valid shape or an error.
template<typename T>
using Result = std::variant<T, OcctError>;

/// Check if a Result holds a success value.
template<typename T>
bool isOk(const Result<T>& r)
{
    return std::holds_alternative<T>(r);
}

/// Get the success value from a Result. Throws std::bad_variant_access if error.
template<typename T>
const T& getValue(const Result<T>& r)
{
    return std::get<T>(r);
}

/// Get the error from a Result. Throws std::bad_variant_access if success.
template<typename T>
const OcctError& getError(const Result<T>& r)
{
    return std::get<OcctError>(r);
}

// ── Boolean Operations ────────────────────────────────────────────────

/// Fuse (boolean union) two shapes with TNP element mapping.
///
/// @param base   The base shape.
/// @param tool   The tool shape to fuse with.
/// @param op     Operation name for TNP tracking (defaults to "FUS").
/// @param tol    Fuzzy tolerance (-1.0 = use default).
/// @return       Result containing the fused TopoShape, or an OcctError.
PartExport Result<Part::TopoShape> fuse(const Part::TopoShape& base,
                                        const Part::TopoShape& tool,
                                        const char* op = nullptr,
                                        double tol = -1.0);

/// Cut (boolean subtraction) tool from base with TNP element mapping.
PartExport Result<Part::TopoShape> cut(const Part::TopoShape& base,
                                       const Part::TopoShape& tool,
                                       const char* op = nullptr,
                                       double tol = -1.0);

/// Common (boolean intersection) of two shapes with TNP element mapping.
PartExport Result<Part::TopoShape> common(const Part::TopoShape& base,
                                          const Part::TopoShape& tool,
                                          const char* op = nullptr,
                                          double tol = -1.0);

// ── Feature Operations ────────────────────────────────────────────────

/// Fillet edges on a shape with TNP element mapping.
///
/// @param base    The shape to fillet.
/// @param edges   TopoShapes representing the edges to fillet.
/// @param radius1 Fillet radius (or first radius for variable fillet).
/// @param radius2 Second radius for variable fillet (0 = constant radius).
/// @param op      Operation name for TNP tracking.
/// @return        Result containing the filleted TopoShape, or an OcctError.
PartExport Result<Part::TopoShape> fillet(const Part::TopoShape& base,
                                          const std::vector<Part::TopoShape>& edges,
                                          double radius1,
                                          double radius2 = 0.0,
                                          const char* op = nullptr);

/// Chamfer edges on a shape with TNP element mapping.
///
/// @param base       The shape to chamfer.
/// @param edges      TopoShapes representing the edges to chamfer.
/// @param chamferType Type of chamfer measurement.
/// @param size1      First chamfer size (distance or distance).
/// @param size2      Second size (distance or angle in radians).
/// @param op         Operation name for TNP tracking.
/// @param flipDir    Whether to flip chamfer direction.
/// @return           Result containing the chamfered TopoShape, or an OcctError.
PartExport Result<Part::TopoShape> chamfer(const Part::TopoShape& base,
                                           const std::vector<Part::TopoShape>& edges,
                                           Part::ChamferType chamferType,
                                           double size1,
                                           double size2 = 0.0,
                                           const char* op = nullptr,
                                           Part::Flip flipDir = Part::Flip::none);

// ── Validation ────────────────────────────────────────────────────────

/// Check if a shape is valid (non-null and not empty).
PartExport bool isValid(const Part::TopoShape& shape);

/// Check if a shape is a solid.
PartExport bool isSolid(const Part::TopoShape& shape);

}  // namespace OcctService
