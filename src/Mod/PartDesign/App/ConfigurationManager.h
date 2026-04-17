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

#include <App/DocumentObject.h>
#include <App/PropertyStandard.h>
#include <App/PropertyLinks.h>
#include <Mod/PartDesign/PartDesignGlobal.h>


namespace Spreadsheet
{
class Sheet;
}

namespace PartDesign
{

/** Design-table-style configuration manager.
 *
 *  Each ConfigurationManager links to a Spreadsheet::Sheet where:
 *   - Row 1 contains parameter headers (property paths like "Pad.Length")
 *   - Subsequent rows each represent a named configuration
 *   - Column A holds the configuration name ("Default", "Heavy Duty", etc.)
 *
 *  When a configuration is activated, the manager writes expression bindings
 *  from the spreadsheet cells to the referenced feature properties, then
 *  triggers a recompute.
 *
 *  Example spreadsheet layout:
 *    |   A          |  B            |  C              |  D              |
 *    | Config       | Pad.Length    | Pocket.Depth    | Fillet.Radius   |
 *    | Default      | 10           | 5               | 1               |
 *    | Heavy Duty   | 15           | 8               | 2               |
 *    | Lightweight  | 6            | 3               | 0.5             |
 */
class PartDesignExport ConfigurationManager : public App::DocumentObject
{
    PROPERTY_HEADER_WITH_OVERRIDE(PartDesign::ConfigurationManager);

public:
    ConfigurationManager();

    /// Link to the driving spreadsheet
    App::PropertyLink  SpreadsheetLink;

    /// Currently active configuration name
    App::PropertyString ActiveConfiguration;

    /// Row number in spreadsheet where parameter headers live (1-based, default 1)
    App::PropertyIntegerConstraint HeaderRow;

    /// Column index (0-based) where configuration names are stored (default 0 = col A)
    App::PropertyInteger NameColumn;

    App::DocumentObjectExecReturn* execute() override;

    /// Get the list of available configuration names from the spreadsheet.
    std::vector<std::string> getConfigurationNames() const;

    /// Activate a configuration by name: bind expressions and recompute.
    /// Returns true on success.
    bool activateConfiguration(const std::string& name);

    const char* getViewProviderName() const override
    {
        return "PartDesignGui::ViewProviderConfigurationManager";
    }

protected:
    void onChanged(const App::Property* prop) override;
};

}  // namespace PartDesign
