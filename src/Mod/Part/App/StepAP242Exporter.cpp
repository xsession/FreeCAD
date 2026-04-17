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

#ifndef _PreComp_
#include <BRepMesh_IncrementalMesh.hxx>
#include <STEPControl_Writer.hxx>
#include <Interface_Static.hxx>
#include <TopoDS_Compound.hxx>
#include <BRep_Builder.hxx>
#endif

#include <Base/Console.h>

#include "StepAP242Exporter.h"


using namespace Part;


bool StepAP242Exporter::exportAP242(
    const std::vector<TopoDS_Shape>& shapes,
    const std::vector<std::string>& labels,
    const std::vector<PmiAnnotation>& annotations,
    const std::string& fileName,
    bool includeTessellation)
{
    if (shapes.empty()) {
        Base::Console().Error("StepAP242Exporter: No shapes to export.\n");
        return false;
    }

    if (fileName.empty()) {
        Base::Console().Error("StepAP242Exporter: Empty file name.\n");
        return false;
    }

    // Set AP242 scheme
    Interface_Static::SetCVal("write.step.schema", "AP242DIS");

    // Build compound and optionally tessellate
    TopoDS_Compound compound;
    BRep_Builder builder;
    builder.MakeCompound(compound);

    for (const auto& shape : shapes) {
        if (shape.IsNull()) {
            continue;
        }

        if (includeTessellation) {
            BRepMesh_IncrementalMesh mesh(shape, 0.1);  // 0.1mm linear deflection
            mesh.Perform();
        }

        builder.Add(compound, shape);
    }

    // Write via STEPControl_Writer (AP242 scheme set above)
    STEPControl_Writer writer;
    IFSelect_ReturnStatus transferStatus = writer.Transfer(compound, STEPControl_AsIs);
    if (transferStatus != IFSelect_RetDone) {
        Base::Console().Error("StepAP242Exporter: Transfer failed (status=%d).\n",
                              static_cast<int>(transferStatus));
        return false;
    }

    IFSelect_ReturnStatus writeStatus = writer.Write(fileName.c_str());
    if (writeStatus != IFSelect_RetDone) {
        Base::Console().Error("StepAP242Exporter: Write to '%s' failed (status=%d).\n",
                              fileName.c_str(), static_cast<int>(writeStatus));
        return false;
    }

    if (!annotations.empty()) {
        Base::Console().Warning("StepAP242Exporter: %zu PMI annotations provided but "
                                "XDE PMI embedding requires XCAF library linkage. "
                                "Shapes exported without PMI.\n", annotations.size());
    }

    Base::Console().Message("StepAP242Exporter: Exported %zu shape(s) to '%s' (AP242DIS).\n",
                            shapes.size(), fileName.c_str());
    return true;
}


std::vector<PmiAnnotation> StepAP242Exporter::collectPmiFromDocument(App::DocumentObject* obj)
{
    std::vector<PmiAnnotation> annotations;

    if (!obj) {
        return annotations;
    }

    // TODO: Scan document for TechDraw::DrawViewDimension objects
    // linked to this object and convert them to PmiAnnotation entries.
    // Full PMI embedding requires linking TKXCAF/TKXDESTEP libraries.

    return annotations;
}
