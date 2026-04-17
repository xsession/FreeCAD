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

#include <TopoDS_Shape.hxx>

#include <Mod/Part/PartGlobal.h>


namespace App
{
class DocumentObject;
}

namespace Part
{

/** Product Manufacturing Information annotation for STEP AP242 export.
 *  Represents a single PMI annotation (dimension, GD&T, datum, note)
 *  to be embedded in STEP AP242 structured data.
 */
struct PartExport PmiAnnotation
{
    enum class Kind
    {
        Dimension,        ///< Linear/angular/radial dimension
        GeometricTolerance,  ///< GD&T feature control frame
        DatumFeature,     ///< Datum reference
        SurfaceFinish,    ///< Surface finish symbol
        Note              ///< General text note
    };

    Kind kind = Kind::Note;
    std::string text;           ///< Display text
    std::string semanticId;     ///< Semantic identifier (e.g., "flatness", "parallelism")
    double value = 0.0;         ///< Numeric value (for dimensions/tolerances)
    double upperTol = 0.0;      ///< Upper tolerance
    double lowerTol = 0.0;      ///< Lower tolerance
    std::string datumRefs;      ///< Comma-separated datum references (e.g., "A,B")
    TopoDS_Shape targetFace;    ///< Face/edge this annotation is attached to
};


/** STEP AP242 exporter with PMI and tessellation support.
 *
 *  Extends the base STEP export (AP214) with:
 *   - Embedded tessellation (triangulated shape alongside B-rep)
 *   - Product Manufacturing Information (PMI) semantic annotations
 *   - Validation properties (geometric validation data)
 *
 *  Uses OCCT's STEPCAFControl_Writer for XDE-based AP242 output.
 */
class PartExport StepAP242Exporter
{
public:
    /** Export shapes with AP242 features to a STEP file.
     *  @param shapes       Shapes to export
     *  @param labels       Labels for each shape (1:1 with shapes)
     *  @param annotations  PMI annotations to embed
     *  @param fileName     Output file path
     *  @param includeTessellation  Whether to include triangulated mesh
     *  @return true on success
     */
    static bool exportAP242(
        const std::vector<TopoDS_Shape>& shapes,
        const std::vector<std::string>& labels,
        const std::vector<PmiAnnotation>& annotations,
        const std::string& fileName,
        bool includeTessellation = true
    );

    /** Collect PMI annotations from TechDraw dimensions and GD&T
     *  objects associated with a document object.
     *  @param obj  Source document object
     *  @return Collected PMI annotations
     */
    static std::vector<PmiAnnotation> collectPmiFromDocument(App::DocumentObject* obj);
};

}  // namespace Part
