// SPDX-License-Identifier: LGPL-2.1-or-later
/***************************************************************************
 *   FreeCAD Public Plugin API – ABI-Stable Plugin Entry Point             *
 *                                                                         *
 *   C++ plugins implement these three entry points for lifecycle          *
 *   management.  FreeCAD loads the shared library and calls them in       *
 *   order: getPluginInfo → initPlugin → (runtime) → cleanupPlugin.       *
 *                                                                         *
 *   API Version: 2.0                                                      *
 ***************************************************************************/

#pragma once

#include <FCGlobal.h>

#include <string>

namespace FreeCAD
{

/// Information about a plugin, returned by getPluginInfo().
struct PluginInfo
{
    const char* name;           ///< Human-readable plugin name
    const char* author;         ///< Author name or organization
    const char* description;    ///< Brief description
    int         apiVersionMajor; ///< API version this plugin targets (major)
    int         apiVersionMinor; ///< API version this plugin targets (minor)
    const char* pluginVersion;  ///< Plugin's own version string
};

/// Context passed to initPlugin() — provides access to FreeCAD internals.
struct PluginContext
{
    void* application;   ///< Pointer to App::Application (cast internally)
    void* guiApplication; ///< Pointer to Gui::Application, or nullptr if headless
    int   apiVersion;     ///< Runtime API version for compatibility checks
};

}  // namespace FreeCAD

// ── Plugin export macros ────────────────────────────────────────────────

#ifdef _WIN32
#  define FREECAD_PLUGIN_EXPORT __declspec(dllexport)
#else
#  define FREECAD_PLUGIN_EXPORT __attribute__((visibility("default")))
#endif

/// Declare the three mandatory plugin entry points.
/// Use this macro in your plugin's main .cpp file after implementing the
/// three functions.
#define FREECAD_DECLARE_PLUGIN_EXPORTS()                                    \
    extern "C" {                                                            \
        FREECAD_PLUGIN_EXPORT FreeCAD::PluginInfo getPluginInfo();          \
        FREECAD_PLUGIN_EXPORT bool initPlugin(FreeCAD::PluginContext& ctx); \
        FREECAD_PLUGIN_EXPORT void cleanupPlugin();                         \
    }
