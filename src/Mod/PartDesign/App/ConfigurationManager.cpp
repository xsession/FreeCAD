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

#include <sstream>

#include <App/Document.h>
#include <App/Expression.h>
#include <Base/Console.h>
#include <Mod/Spreadsheet/App/Cell.h>
#include <Mod/Spreadsheet/App/Sheet.h>

#include "ConfigurationManager.h"


using namespace PartDesign;

PROPERTY_SOURCE(PartDesign::ConfigurationManager, App::DocumentObject)


ConfigurationManager::ConfigurationManager()
{
    ADD_PROPERTY_TYPE(SpreadsheetLink, (nullptr),
                      "Configuration", App::Prop_None,
                      "Spreadsheet containing configuration data");
    ADD_PROPERTY_TYPE(ActiveConfiguration, (""),
                      "Configuration", App::Prop_None,
                      "Name of the currently active configuration");

    // Row 1 = headers by default
    static const App::PropertyIntegerConstraint::Constraints rowConstr = {1, 9999, 1};
    ADD_PROPERTY_TYPE(HeaderRow, (1),
                      "Configuration", App::Prop_None,
                      "Row containing parameter headers (1-based)");
    HeaderRow.setConstraints(&rowConstr);

    ADD_PROPERTY_TYPE(NameColumn, (0),
                      "Configuration", App::Prop_None,
                      "Column index for configuration names (0=A, 1=B, ...)");
}


std::vector<std::string> ConfigurationManager::getConfigurationNames() const
{
    std::vector<std::string> names;

    auto* sheet = dynamic_cast<Spreadsheet::Sheet*>(SpreadsheetLink.getValue());
    if (!sheet) {
        return names;
    }

    int header = HeaderRow.getValue();
    int nameCol = NameColumn.getValue();

    // Scan rows below the header for configuration names
    for (int row = header + 1; row < 10000; ++row) {
        App::CellAddress addr(row - 1, nameCol);  // CellAddress is 0-based
        auto* cell = sheet->getCell(addr);
        if (!cell) {
            break;  // Stop at first empty row
        }
        std::string content;
        cell->getStringContent(content);
        if (content.empty()) {
            break;
        }
        names.push_back(content);
    }

    return names;
}


bool ConfigurationManager::activateConfiguration(const std::string& name)
{
    auto* sheet = dynamic_cast<Spreadsheet::Sheet*>(SpreadsheetLink.getValue());
    if (!sheet) {
        Base::Console().Error("ConfigurationManager: No spreadsheet linked.\n");
        return false;
    }

    auto* doc = getDocument();
    if (!doc) {
        return false;
    }

    int header = HeaderRow.getValue();
    int nameCol = NameColumn.getValue();

    // Find the row for this configuration name
    int targetRow = -1;
    for (int row = header + 1; row < 10000; ++row) {
        App::CellAddress addr(row - 1, nameCol);
        auto* cell = sheet->getCell(addr);
        if (!cell) {
            break;
        }
        std::string content;
        cell->getStringContent(content);
        if (content == name) {
            targetRow = row;
            break;
        }
        if (content.empty()) {
            break;
        }
    }

    if (targetRow < 0) {
        Base::Console().Error("ConfigurationManager: Configuration '%s' not found.\n",
                              name.c_str());
        return false;
    }

    // Read parameter headers from the header row
    // Columns start after the name column
    std::vector<std::pair<int, std::string>> paramCols;  // <colIndex, headerText>
    for (int col = 0; col < 256; ++col) {
        if (col == nameCol) {
            continue;
        }
        App::CellAddress hAddr(header - 1, col);
        auto* hCell = sheet->getCell(hAddr);
        if (!hCell) {
            break;
        }
        std::string hText;
        hCell->getStringContent(hText);
        if (hText.empty()) {
            break;
        }
        paramCols.emplace_back(col, hText);
    }

    if (paramCols.empty()) {
        Base::Console().Warning("ConfigurationManager: No parameter columns found.\n");
        return false;
    }

    // For each parameter column, set up expression binding:
    //   target.Property = spreadsheet.CellRef
    doc->openTransaction("Activate Configuration");

    for (const auto& [col, paramPath] : paramCols) {
        // paramPath is "ObjectName.PropertyName"
        auto dotPos = paramPath.find('.');
        if (dotPos == std::string::npos) {
            Base::Console().Warning("ConfigurationManager: Invalid header '%s' "
                                    "(expected Object.Property)\n", paramPath.c_str());
            continue;
        }

        std::string objName = paramPath.substr(0, dotPos);
        std::string propName = paramPath.substr(dotPos + 1);

        auto* target = doc->getObject(objName.c_str());
        if (!target) {
            Base::Console().Warning("ConfigurationManager: Object '%s' not found.\n",
                                    objName.c_str());
            continue;
        }

        auto* prop = target->getPropertyByName(propName.c_str());
        if (!prop) {
            Base::Console().Warning("ConfigurationManager: Property '%s.%s' not found.\n",
                                    objName.c_str(), propName.c_str());
            continue;
        }

        // Build cell reference: SheetName.CellAddr
        App::CellAddress valAddr(targetRow - 1, col);
        std::string cellRef = std::string(sheet->getNameInDocument())
                              + "." + valAddr.toString();

        // Build and set expression
        try {
            auto expr = App::Expression::parse(target, cellRef);
            if (expr) {
                target->setExpression(App::ObjectIdentifier(*prop), std::move(expr));
            }
        }
        catch (const Base::Exception& e) {
            Base::Console().Warning("ConfigurationManager: Failed to set expression for "
                                    "'%s.%s': %s\n",
                                    objName.c_str(), propName.c_str(), e.what());
        }
    }

    ActiveConfiguration.setValue(name.c_str());
    doc->commitTransaction();
    doc->recompute();

    Base::Console().Message("ConfigurationManager: Activated configuration '%s'.\n",
                            name.c_str());
    return true;
}


App::DocumentObjectExecReturn* ConfigurationManager::execute()
{
    // No shape computation — this is a metadata-only object
    return App::DocumentObject::StdReturn;
}


void ConfigurationManager::onChanged(const App::Property* prop)
{
    App::DocumentObject::onChanged(prop);
}
