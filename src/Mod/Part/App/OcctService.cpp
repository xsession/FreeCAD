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

#include "PreCompiled.h"

#include "OcctService.h"

#include <Standard_Failure.hxx>
#include <TopoDS.hxx>
#include <TopoDS_Shape.hxx>
#include <BRepCheck_Analyzer.hxx>

#include <Base/Console.h>
#include <Base/Exception.h>

namespace OcctService
{

/// Helper: catch Standard_Failure and convert to OcctError.
/// The callable should return a Part::TopoShape.
template<typename Func>
static Result<Part::TopoShape> safeExec(const char* operationName, Func&& func)
{
    try {
        Part::TopoShape result = func();
        if (result.isNull()) {
            return OcctError("Operation produced a null shape", "", operationName);
        }
        return result;
    }
    catch (const Standard_Failure& e) {
        std::string msg;
        std::string cls;
        if (e.GetMessageString()) {
            msg = e.GetMessageString();
        }
        else {
            msg = "OCCT operation failed";
        }
        cls = e.DynamicType()->Name();
        Base::Console().error("OcctService::%s: %s (%s)\n", operationName, msg.c_str(), cls.c_str());
        return OcctError(std::move(msg), std::move(cls), operationName);
    }
    catch (const Base::Exception& e) {
        Base::Console().error("OcctService::%s: %s\n", operationName, e.what());
        return OcctError(e.what(), "Base::Exception", operationName);
    }
    catch (const std::exception& e) {
        Base::Console().error("OcctService::%s: %s\n", operationName, e.what());
        return OcctError(e.what(), "std::exception", operationName);
    }
}

// ── Boolean Operations ────────────────────────────────────────────────

Result<Part::TopoShape> fuse(const Part::TopoShape& base,
                             const Part::TopoShape& tool,
                             const char* op,
                             double tol)
{
    return safeExec("fuse", [&]() {
        return base.makeElementFuse(tool, op, tol);
    });
}

Result<Part::TopoShape> cut(const Part::TopoShape& base,
                            const Part::TopoShape& tool,
                            const char* op,
                            double tol)
{
    return safeExec("cut", [&]() {
        return base.makeElementCut(tool, op, tol);
    });
}

Result<Part::TopoShape> common(const Part::TopoShape& base,
                               const Part::TopoShape& tool,
                               const char* op,
                               double tol)
{
    return safeExec("common", [&]() {
        std::vector<Part::TopoShape> sources = {base, tool};
        return Part::TopoShape(0, base.Hasher)
            .makeElementBoolean("BRepAlgoAPI_Common", sources, op, tol);
    });
}

// ── Feature Operations ────────────────────────────────────────────────

Result<Part::TopoShape> fillet(const Part::TopoShape& base,
                               const std::vector<Part::TopoShape>& edges,
                               double radius1,
                               double radius2,
                               const char* op)
{
    return safeExec("fillet", [&]() {
        return base.makeElementFillet(edges, radius1, radius2, op);
    });
}

Result<Part::TopoShape> chamfer(const Part::TopoShape& base,
                                const std::vector<Part::TopoShape>& edges,
                                Part::ChamferType chamferType,
                                double size1,
                                double size2,
                                const char* op,
                                Part::Flip flipDir)
{
    return safeExec("chamfer", [&]() {
        return base.makeElementChamfer(edges, chamferType, size1, size2, op, flipDir);
    });
}

// ── Validation ────────────────────────────────────────────────────────

bool isValid(const Part::TopoShape& shape)
{
    if (shape.isNull()) {
        return false;
    }
    const TopoDS_Shape& s = shape.getShape();
    return !s.IsNull();
}

bool isSolid(const Part::TopoShape& shape)
{
    if (shape.isNull()) {
        return false;
    }
    const TopoDS_Shape& s = shape.getShape();
    return !s.IsNull() && s.ShapeType() == TopAbs_SOLID;
}

}  // namespace OcctService
