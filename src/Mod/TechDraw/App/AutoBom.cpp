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
#include <map>
#include <sstream>

#include <App/Document.h>
#include <App/DocumentObject.h>
#include <App/GeoFeatureGroupExtension.h>
#include <App/PropertyStandard.h>
#include <Base/Console.h>
#include <Mod/Part/App/PartFeature.h>
#include <Mod/Spreadsheet/App/Sheet.h>

#include "AutoBom.h"
#include "DrawPage.h"
#include "DrawViewBalloon.h"
#include "DrawViewPart.h"


using namespace TechDraw;


std::vector<BomEntry> AutoBom::generateBom(App::DocumentObject* source)
{
    std::vector<BomEntry> entries;

    if (!source) {
        return entries;
    }

    // Collect all children recursively
    std::vector<App::DocumentObject*> children;

    if (auto* group = source->getExtensionByType<App::GeoFeatureGroupExtension>(true)) {
        children = group->getObjects();
    }
    else {
        // Try outList for non-group sources
        children = source->getOutList();
    }

    if (children.empty()) {
        return entries;
    }

    // Count unique parts by TypeId + Label combination
    // (same label + same type = same part)
    struct PartKey
    {
        std::string typeId;
        std::string label;

        bool operator<(const PartKey& other) const
        {
            if (typeId != other.typeId) {
                return typeId < other.typeId;
            }
            return label < other.label;
        }
    };

    std::map<PartKey, BomEntry> partMap;

    for (auto* child : children) {
        if (!child) {
            continue;
        }

        // Skip non-shape objects (sketches, datums, etc. are not BOM items)
        if (!child->isDerivedFrom<Part::Feature>()
            && !child->hasExtension(App::GeoFeatureGroupExtension::getExtensionClassTypeId())) {
            continue;
        }

        PartKey key;
        key.typeId = child->getTypeId().getName();
        key.label = child->Label.getStrValue();

        auto it = partMap.find(key);
        if (it != partMap.end()) {
            it->second.quantity++;
        }
        else {
            BomEntry entry;
            entry.partName = child->Label.getStrValue();
            entry.quantity = 1;

            // Try to get Description property as part number
            auto* descProp = dynamic_cast<App::PropertyString*>(
                child->getPropertyByName("Description"));
            if (descProp) {
                entry.partNumber = descProp->getStrValue();
            }

            // Try to get material name
            auto* matProp = dynamic_cast<App::PropertyString*>(
                child->getPropertyByName("Material"));
            if (matProp) {
                entry.material = matProp->getStrValue();
            }

            partMap[key] = entry;
        }
    }

    // Assign item numbers and build sorted result
    int itemNum = 1;
    for (auto& [key, entry] : partMap) {
        entry.itemNumber = itemNum++;
        entries.push_back(entry);
    }

    return entries;
}


std::vector<DrawViewBalloon*> AutoBom::createBalloons(
    DrawPage* page,
    DrawViewPart* view,
    const std::vector<BomEntry>& entries)
{
    std::vector<DrawViewBalloon*> balloons;

    if (!page || !view || entries.empty()) {
        return balloons;
    }

    auto* doc = page->getDocument();
    if (!doc) {
        return balloons;
    }

    // Place balloons in a column to the right of the view
    double viewX = view->X.getValue();
    double viewY = view->Y.getValue();
    double startX = viewX + 80.0;  // 80mm to the right
    double startY = viewY + 40.0;  // Start near top
    double spacing = 15.0;         // 15mm vertical spacing

    for (size_t i = 0; i < entries.size(); ++i) {
        const auto& entry = entries[i];

        std::string balloonName = std::string("Balloon_") + std::to_string(entry.itemNumber);
        auto* balloon = dynamic_cast<DrawViewBalloon*>(
            doc->addObject("TechDraw::DrawViewBalloon", balloonName.c_str()));

        if (!balloon) {
            continue;
        }

        balloon->SourceView.setValue(view);
        balloon->Text.setValue(std::to_string(entry.itemNumber).c_str());
        balloon->OriginX.setValue(startX);
        balloon->OriginY.setValue(startY - static_cast<double>(i) * spacing);

        page->addView(balloon);
        balloons.push_back(balloon);
    }

    Base::Console().Message("AutoBom: Created %zu balloons.\n", balloons.size());
    return balloons;
}


App::DocumentObject* AutoBom::exportToSpreadsheet(
    App::Document* doc,
    const std::vector<BomEntry>& entries,
    const std::string& sheetName)
{
    if (!doc || entries.empty()) {
        return nullptr;
    }

    auto* sheetObj = doc->addObject("Spreadsheet::Sheet", sheetName.c_str());
    auto* sheet = dynamic_cast<Spreadsheet::Sheet*>(sheetObj);
    if (!sheet) {
        return nullptr;
    }

    // Header row
    sheet->setCell("A1", "Item");
    sheet->setCell("B1", "Part Name");
    sheet->setCell("C1", "Part Number");
    sheet->setCell("D1", "Qty");
    sheet->setCell("E1", "Material");

    // Data rows
    for (size_t i = 0; i < entries.size(); ++i) {
        const auto& entry = entries[i];
        int row = static_cast<int>(i) + 2;  // 1-indexed, +1 for header

        std::string rowStr = std::to_string(row);
        sheet->setCell(("A" + rowStr).c_str(), std::to_string(entry.itemNumber).c_str());
        sheet->setCell(("B" + rowStr).c_str(), entry.partName.c_str());
        sheet->setCell(("C" + rowStr).c_str(), entry.partNumber.c_str());
        sheet->setCell(("D" + rowStr).c_str(), std::to_string(entry.quantity).c_str());
        sheet->setCell(("E" + rowStr).c_str(), entry.material.c_str());
    }

    Base::Console().Message("AutoBom: Exported %zu BOM entries to spreadsheet '%s'.\n",
                            entries.size(), sheetName.c_str());
    return sheetObj;
}
