/***************************************************************************
 *   Copyright (c) 2024 FreeCAD Project                                   *
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
 *   License along with this library; see the file COPYING.LIB. If not,   *
 *   write to the Free Software Foundation, Inc., 59 Temple Place,         *
 *   Suite 330, Boston, MA  02111-1307, USA                                *
 *                                                                         *
 ***************************************************************************/

#pragma once

#include <functional>
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

#include <FCGlobal.h>

namespace App {

class Document;

/// Semantic version for API compatibility checking (§9.2.1).
struct AppExport ApiVersion
{
    int major = 1;
    int minor = 0;
    int patch = 0;

    bool operator<(const ApiVersion& o) const {
        if (major != o.major) return major < o.major;
        if (minor != o.minor) return minor < o.minor;
        return patch < o.patch;
    }
    bool operator>(const ApiVersion& o) const { return o < *this; }
    bool operator<=(const ApiVersion& o) const { return !(o < *this); }
    bool operator>=(const ApiVersion& o) const { return !(*this < o); }
    bool operator==(const ApiVersion& o) const {
        return major == o.major && minor == o.minor && patch == o.patch;
    }
    bool operator!=(const ApiVersion& o) const { return !(*this == o); }

    std::string toString() const;
    static ApiVersion parse(const std::string& s);
    static ApiVersion current();
};

/// Result of an API version compatibility check.
enum class CompatResult {
    Compatible,
    TooOld,         ///< plugin requires a newer API than host provides
    TooNew,         ///< plugin is built for an older API (min > current)
    Invalid         ///< version string could not be parsed
};

/// Lifecycle event types (§9.2.2).
enum class PluginEvent {
    OnInstall,
    OnUpdate,
    OnUninstall,
    OnActivate,
    OnDeactivate,
    OnDocumentOpened
};

/// Metadata extracted from a plugin's package.xml.
struct AppExport PluginInfo
{
    std::string name;
    std::string version;
    std::string description;
    std::string author;
    ApiVersion  apiMin;             ///< <api-version min="...">
    ApiVersion  apiMax;             ///< <api-version max="...">
    std::string path;               ///< filesystem path to the addon directory
    bool        enabled = true;

    CompatResult checkCompat() const;
};

/// Callback signature for lifecycle hooks.
using PluginCallback = std::function<void(const PluginInfo&, PluginEvent)>;

/// PluginLifecycle — manages addon version checking, lifecycle hooks,
/// and plugin activation/deactivation.
///
/// Usage:
/// @code
///     auto& plm = PluginLifecycle::instance();
///     plm.registerPlugin(info);
///     plm.addHook(PluginEvent::OnActivate, [](auto& pi, auto ev) {
///         // handle activation
///     });
///     plm.activate("MyAddon");
/// @endcode
class AppExport PluginLifecycle
{
public:
    static PluginLifecycle& instance();

    /// Register a plugin from its package.xml metadata.
    /// Returns false if the API version check fails.
    bool registerPlugin(const PluginInfo& info);

    /// Unregister and run OnUninstall hooks.
    void unregisterPlugin(const std::string& name);

    /// Activate a registered plugin (runs OnActivate hooks).
    bool activate(const std::string& name);

    /// Deactivate a plugin (runs OnDeactivate hooks).
    void deactivate(const std::string& name);

    /// Notify all plugins that a document was opened.
    void notifyDocumentOpened(Document* doc);

    /// Add a global lifecycle hook for a specific event.
    void addHook(PluginEvent event, PluginCallback callback);

    /// Remove all hooks for a given event.
    void clearHooks(PluginEvent event);

    /// Get info for a registered plugin (nullptr if not found).
    const PluginInfo* pluginInfo(const std::string& name) const;

    /// List all registered plugins.
    std::vector<std::string> pluginNames() const;

    /// Check if a plugin is currently active.
    bool isActive(const std::string& name) const;

    /// Parse a package.xml file and return PluginInfo.
    static PluginInfo parsePackageXml(const std::string& xmlPath);

private:
    PluginLifecycle() = default;

    void fireEvent(const std::string& pluginName, PluginEvent event);

    std::unordered_map<std::string, PluginInfo> _plugins;
    std::unordered_map<std::string, bool> _active;
    std::unordered_map<int, std::vector<PluginCallback>> _hooks;
};

} // namespace App
