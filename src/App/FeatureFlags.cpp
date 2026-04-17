// SPDX-License-Identifier: LGPL-2.1-or-later
/***************************************************************************
 *   Copyright (c) 2026 FreeCAD contributors                              *
 *                                                                         *
 *   This file is part of the FreeCAD CAx development system.              *
 *                                                                         *
 *   This library is free software; you can redistribute it and/or         *
 *   modify it under the terms of the GNU Library General Public           *
 *   License as published by the Free Software Foundation; either          *
 *   version 2 of the License, or (at your option) any later version.      *
 *                                                                         *
 *   This library  is distributed in the hope that it will be useful,      *
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
 *   GNU Library General Public License for more details.                  *
 *                                                                         *
 *   You should have received a copy of the GNU Library General Public     *
 *   License along with this library; see the file COPYING.LIB. If not,    *
 *   write to the Free Software Foundation, Inc., 59 Temple Place,         *
 *   Suite 330, Boston, MA  02111-1307, USA                                *
 *                                                                         *
 ***************************************************************************/

#include "PreCompiled.h"

#include "FeatureFlags.h"
#include "Application.h"

#include <Base/Console.h>
#include <Base/Parameter.h>

using namespace App;

namespace
{
    const char* const PreferencePath = "User parameter:BaseApp/Preferences/FeatureFlags";

    // Known flags with their default compile-time states
    struct FlagDefault
    {
        const char* name;
        bool        defaultEnabled;
    };

    // clang-format off
    constexpr FlagDefault knownFlags[] = {
        { FeatureFlagDefs::ParallelRecompute,   false },
        { FeatureFlagDefs::PluginSandbox,       false },
        { FeatureFlagDefs::RestAPI,             false },
        { FeatureFlagDefs::ObjectLocking,       false },
        { FeatureFlagDefs::AuditTrail,          false },
        { FeatureFlagDefs::SketchAutoConstrain, true  },
        { FeatureFlagDefs::SheetMetal,          true  },
        { FeatureFlagDefs::ConfigurationTable,  true  },
    };
    // clang-format on
}

std::unordered_map<std::string, FeatureFlags::Override>& FeatureFlags::overrides()
{
    static std::unordered_map<std::string, Override> s_overrides;
    return s_overrides;
}

std::mutex& FeatureFlags::mutex()
{
    static std::mutex s_mutex;
    return s_mutex;
}

bool FeatureFlags::isEnabled(const char* flagName, bool defaultValue)
{
    std::lock_guard<std::mutex> guard(mutex());

    // 1. Check programmatic overrides first
    auto& ov = overrides();
    auto it = ov.find(flagName);
    if (it != ov.end()) {
        return it->second.enabled;
    }

    // 2. Check user preferences
    try {
        auto grp = App::GetApplication().GetParameterGroupByPath(PreferencePath);
        if (grp.isValid()) {
            // Look up default from known flags table
            bool knownDefault = defaultValue;
            for (const auto& kf : knownFlags) {
                if (std::strcmp(kf.name, flagName) == 0) {
                    knownDefault = kf.defaultEnabled;
                    break;
                }
            }
            return grp->GetBool(flagName, knownDefault);
        }
    }
    catch (...) {
        // Application not initialized yet — use default
    }

    return defaultValue;
}

void FeatureFlags::setOverride(const char* flagName, bool enabled)
{
    std::lock_guard<std::mutex> guard(mutex());
    overrides()[flagName] = Override{enabled};
    Base::Console().Log("FeatureFlags: '%s' overridden to %s\n",
                        flagName, enabled ? "true" : "false");
}

void FeatureFlags::clearOverride(const char* flagName)
{
    std::lock_guard<std::mutex> guard(mutex());
    overrides().erase(flagName);
}

void FeatureFlags::clearAllOverrides()
{
    std::lock_guard<std::mutex> guard(mutex());
    overrides().clear();
}

std::unordered_map<std::string, bool> FeatureFlags::allFlags()
{
    std::unordered_map<std::string, bool> result;
    for (const auto& kf : knownFlags) {
        result[kf.name] = isEnabled(kf.name);
    }
    return result;
}
