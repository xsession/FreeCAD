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

#include "ThemeTokens.h"

#include "Application.h"
#include "StyleParameters/ParameterManager.h"

#include <unordered_map>

using namespace Gui;

namespace {

/// Built-in defaults for all theme tokens.
/// These ensure the UI is functional even without a theme YAML file.
const std::unordered_map<std::string, QColor>& builtInDefaults()
{
    static const std::unordered_map<std::string, QColor> defaults = {
        // Surfaces
        {ThemeTokens::SurfacePrimary,     QColor(255, 255, 255)},
        {ThemeTokens::SurfaceSecondary,   QColor(243, 243, 243)},
        {ThemeTokens::SurfaceElevated,    QColor(255, 255, 255)},
        {ThemeTokens::SurfaceSunken,      QColor(230, 230, 230)},

        // Content
        {ThemeTokens::ContentPrimary,     QColor(30, 30, 30)},
        {ThemeTokens::ContentSecondary,   QColor(100, 100, 100)},
        {ThemeTokens::ContentDisabled,    QColor(160, 160, 160)},
        {ThemeTokens::ContentInverse,     QColor(255, 255, 255)},

        // Accent
        {ThemeTokens::AccentPrimary,      QColor(0, 120, 215)},
        {ThemeTokens::AccentHover,        QColor(0, 100, 190)},
        {ThemeTokens::AccentActive,       QColor(0, 84, 163)},
        {ThemeTokens::AccentSubtle,       QColor(204, 228, 247)},

        // Status
        {ThemeTokens::StatusError,        QColor(196, 43, 28)},
        {ThemeTokens::StatusWarning,      QColor(255, 185, 0)},
        {ThemeTokens::StatusSuccess,      QColor(16, 124, 16)},
        {ThemeTokens::StatusInfo,         QColor(0, 120, 215)},

        // 3D Viewport
        {ThemeTokens::ViewportPreselect,  QColor(0, 255, 255)},     // Cyan
        {ThemeTokens::ViewportSelect,     QColor(0, 255, 0)},       // Green
        {ThemeTokens::ViewportEdge,       QColor(0, 0, 0)},
        {ThemeTokens::ViewportBackground, QColor(237, 237, 242)},

        // Tree View
        {ThemeTokens::TreeSearchHighlight,      QColor(255, 255, 0, 100)},
        {ThemeTokens::TreeRollbackActive,       QColor(255, 255, 255)},
        {ThemeTokens::TreeRollbackSuppressed,   QColor(180, 180, 180)},

        // Borders
        {ThemeTokens::BorderDefault,      QColor(200, 200, 200)},
        {ThemeTokens::BorderStrong,       QColor(140, 140, 140)},
        {ThemeTokens::BorderSubtle,       QColor(225, 225, 225)},
    };
    return defaults;
}

/// Try to resolve a color from the StyleParameters system.
std::optional<QColor> resolveFromStyleParams(const char* tokenName)
{
    auto* mgr = Application::Instance ? Application::Instance->styleParameterManager() : nullptr;
    if (!mgr) {
        return std::nullopt;
    }

    auto params = mgr->parameters();
    for (const auto& param : params) {
        if (param.name == tokenName && !param.value.empty()) {
            // Try to parse the parameter value as a color
            QColor color(QString::fromStdString(param.value));
            if (color.isValid()) {
                return color;
            }
        }
    }
    return std::nullopt;
}

}  // anonymous namespace


QColor ThemeTokens::resolve(const char* tokenName)
{
    // 1. Try the StyleParameters system (user override + theme YAML)
    if (auto color = resolveFromStyleParams(tokenName)) {
        return *color;
    }

    // 2. Fall back to built-in defaults
    auto& defaults = builtInDefaults();
    auto it = defaults.find(tokenName);
    if (it != defaults.end()) {
        return it->second;
    }

    // 3. Missing token — return magenta to make it visually obvious
    return QColor(255, 0, 255);
}

QColor ThemeTokens::resolve(const char* tokenName, const QColor& fallback)
{
    if (auto color = resolveFromStyleParams(tokenName)) {
        return *color;
    }

    auto& defaults = builtInDefaults();
    auto it = defaults.find(tokenName);
    if (it != defaults.end()) {
        return it->second;
    }

    return fallback;
}
