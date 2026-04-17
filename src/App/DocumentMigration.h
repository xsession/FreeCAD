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

#include <functional>
#include <map>
#include <string>
#include <vector>

#include <FCGlobal.h>

namespace App
{

class Document;

/// The current schema version written into new documents.
/// Increment this when adding a new migration step.
constexpr int CurrentSchemaVersion = 4;

/// The minimum schema version that this build can read.
/// Documents older than this require an older FreeCAD to open.
constexpr int MinReadableSchemaVersion = 1;

/// A single migration step that transforms a document from one schema
/// version to the next.
///
/// Migration functions receive a mutable reference to the Document after
/// its XML has been parsed but before objects are fully restored.  They
/// can rename properties, convert values, or set migration flags.
using MigrationFunc = std::function<void(Document& doc)>;

/// Registry and executor for document schema migrations.
///
/// Modules register migration steps at static-init time via
/// registerMigration().  When a document is opened, Document::Restore()
/// calls DocumentMigration::migrate() which runs all steps between the
/// file's schema version and CurrentSchemaVersion in order.
///
/// Example registration (in a .cpp file):
///
///   static int _init = []() {
///       App::DocumentMigration::registerMigration(4, 5, [](App::Document& doc) {
///           // Rename a property, fix up values, etc.
///       });
///       return 0;
///   }();
///
class AppExport DocumentMigration
{
public:
    /// Register a migration step from version \a fromVersion to
    /// \a fromVersion + 1.  Steps must be registered for consecutive
    /// version pairs.
    static void registerMigration(int fromVersion, int toVersion, MigrationFunc func);

    /// Run all registered migration steps needed to bring \a doc from
    /// \a fileSchemaVersion up to CurrentSchemaVersion.
    ///
    /// Returns the final schema version achieved (normally == CurrentSchemaVersion).
    /// If a step is missing, migration stops at that version and the
    /// partial version is returned.
    static int migrate(Document& doc, int fileSchemaVersion);

    /// Return the list of registered migration version pairs (for diagnostics).
    static std::vector<std::pair<int, int>> registeredMigrations();

private:
    struct MigrationStep
    {
        int fromVersion;
        int toVersion;
        MigrationFunc func;
    };

    static std::vector<MigrationStep>& registry();
};

}  // namespace App
