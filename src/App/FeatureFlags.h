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

#pragma once

#include <FCGlobal.h>

#include <mutex>
#include <string>
#include <unordered_map>

namespace App
{

/// Compile-time feature flag definitions.
/// Add new flags here as `inline constexpr`.
namespace FeatureFlagDefs
{
    inline constexpr const char* ParallelRecompute   = "ParallelRecompute";
    inline constexpr const char* PluginSandbox       = "PluginSandbox";
    inline constexpr const char* RestAPI             = "RestAPI";
    inline constexpr const char* ObjectLocking       = "ObjectLocking";
    inline constexpr const char* AuditTrail          = "AuditTrail";
    inline constexpr const char* SketchAutoConstrain = "SketchAutoConstrain";
    inline constexpr const char* SheetMetal          = "SheetMetal";
    inline constexpr const char* ConfigurationTable  = "ConfigurationTable";
}

/// Runtime feature flag system.
///
/// Flags are read from user preferences at:
///   `User parameter:BaseApp/Preferences/FeatureFlags/<FlagName>`
///
/// Flags can also be set programmatically (overrides preference).
/// Thread-safe: reads may be concurrent with writes.
///
/// Usage:
/// @code
///   if (FeatureFlags::isEnabled("ParallelRecompute")) {
///       RecomputeEngine::parallelRecompute(dirty);
///   } else {
///       Document::serialRecompute(dirty);
///   }
/// @endcode
class AppExport FeatureFlags
{
public:
    /// Check if a feature flag is enabled.
    /// First checks programmatic overrides, then user preferences.
    /// If neither is set, returns @p defaultValue.
    static bool isEnabled(const char* flagName, bool defaultValue = false);

    /// Programmatically enable/disable a flag (overrides preferences).
    static void setOverride(const char* flagName, bool enabled);

    /// Remove a programmatic override (reverts to preference/default).
    static void clearOverride(const char* flagName);

    /// Remove all programmatic overrides.
    static void clearAllOverrides();

    /// Get all known flags and their current state.
    /// Returns map of flagName → enabled.
    static std::unordered_map<std::string, bool> allFlags();

private:
    struct Override
    {
        bool enabled;
    };

    static std::unordered_map<std::string, Override>& overrides();
    static std::mutex& mutex();
};

}  // namespace App
