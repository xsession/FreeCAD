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

#include "DocumentMigration.h"
#include "Document.h"

#include <Base/Console.h>
#include <Base/Exception.h>

#include <algorithm>

using namespace App;

std::vector<DocumentMigration::MigrationStep>& DocumentMigration::registry()
{
    static std::vector<MigrationStep> steps;
    return steps;
}

void DocumentMigration::registerMigration(int fromVersion, int toVersion, MigrationFunc func)
{
    if (toVersion != fromVersion + 1) {
        Base::Console().warning(
            "DocumentMigration::registerMigration: non-consecutive versions %d -> %d\n",
            fromVersion,
            toVersion);
    }
    registry().push_back({fromVersion, toVersion, std::move(func)});
}

int DocumentMigration::migrate(Document& doc, int fileSchemaVersion)
{
    if (fileSchemaVersion >= CurrentSchemaVersion) {
        return fileSchemaVersion;  // Nothing to do
    }

    if (fileSchemaVersion < MinReadableSchemaVersion) {
        Base::Console().error(
            "DocumentMigration: file schema version %d is older than minimum readable %d\n",
            fileSchemaVersion,
            MinReadableSchemaVersion);
        return fileSchemaVersion;
    }

    auto& steps = registry();

    // Sort steps by fromVersion to ensure correct ordering
    std::sort(steps.begin(), steps.end(), [](const MigrationStep& a, const MigrationStep& b) {
        return a.fromVersion < b.fromVersion;
    });

    int currentVersion = fileSchemaVersion;
    while (currentVersion < CurrentSchemaVersion) {
        // Find the step for this version
        auto it = std::find_if(steps.begin(), steps.end(), [currentVersion](const MigrationStep& s) {
            return s.fromVersion == currentVersion;
        });

        if (it == steps.end()) {
            // No migration registered for this version — skip gap
            // This is normal for versions that had no structural changes
            ++currentVersion;
            continue;
        }

        Base::Console().log("DocumentMigration: migrating schema %d -> %d\n",
                            it->fromVersion,
                            it->toVersion);
        try {
            it->func(doc);
        }
        catch (const Base::Exception& e) {
            e.reportException();
            Base::Console().error("DocumentMigration: migration %d -> %d failed: %s\n",
                                  it->fromVersion,
                                  it->toVersion,
                                  e.what());
            return currentVersion;  // Stop at failed step
        }
        catch (const std::exception& e) {
            Base::Console().error("DocumentMigration: migration %d -> %d failed: %s\n",
                                  it->fromVersion,
                                  it->toVersion,
                                  e.what());
            return currentVersion;
        }

        currentVersion = it->toVersion;
    }

    return currentVersion;
}

std::vector<std::pair<int, int>> DocumentMigration::registeredMigrations()
{
    std::vector<std::pair<int, int>> result;
    for (const auto& step : registry()) {
        result.emplace_back(step.fromVersion, step.toVersion);
    }
    return result;
}
