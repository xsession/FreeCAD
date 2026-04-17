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

#include <Mod/TechDraw/TechDrawGlobal.h>


namespace App
{
class DocumentObject;
class Document;
}

namespace TechDraw
{
class DrawPage;
class DrawViewPart;
class DrawViewBalloon;

/** A single BOM entry describing one part type in an assembly. */
struct TechDrawExport BomEntry
{
    int itemNumber = 0;           ///< BOM item number (1, 2, 3, ...)
    std::string partName;         ///< Object label
    std::string partNumber;       ///< Part number string (from Description property if available)
    int quantity = 0;             ///< Count of identical parts
    std::string material;         ///< Material name if known
};


/** Auto-BOM generator for TechDraw.
 *
 *  Given an assembly (or group of objects) and a DrawViewPart, this class:
 *   1. Enumerates unique parts and counts quantities
 *   2. Generates a BOM table (vector of BomEntry)
 *   3. Creates DrawViewBalloon objects on the drawing view, one per part type
 *   4. Populates balloon text with matching BOM item numbers
 *
 *  The BOM table can then be rendered as a DrawViewSpreadsheet by
 *  exporting to a Spreadsheet::Sheet.
 */
class TechDrawExport AutoBom
{
public:
    /** Generate BOM entries from an assembly source.
     *  @param source  The assembly or App::Part containing components
     *  @return Sorted BOM entries (by label)
     */
    static std::vector<BomEntry> generateBom(App::DocumentObject* source);

    /** Create balloons on a DrawViewPart for each BOM entry.
     *  Balloons are placed at auto-computed positions around the view.
     *  @param page     TechDraw page to add balloons to
     *  @param view     The part view to annotate
     *  @param entries  BOM entries from generateBom()
     *  @return Created balloon objects
     */
    static std::vector<DrawViewBalloon*> createBalloons(
        DrawPage* page,
        DrawViewPart* view,
        const std::vector<BomEntry>& entries
    );

    /** Export BOM entries to a Spreadsheet::Sheet for table rendering.
     *  Creates rows: Header + one row per entry.
     *  Columns: Item | Part Name | Part Number | Qty | Material
     *  @param doc       Document to create the sheet in
     *  @param entries   BOM entries
     *  @param sheetName Name for the spreadsheet object
     *  @return The created sheet object, or nullptr on failure
     */
    static App::DocumentObject* exportToSpreadsheet(
        App::Document* doc,
        const std::vector<BomEntry>& entries,
        const std::string& sheetName = "BOM"
    );
};

}  // namespace TechDraw
