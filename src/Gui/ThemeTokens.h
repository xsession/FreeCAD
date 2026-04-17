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

#include <QColor>
#include <QString>

#include <FCGlobal.h>

namespace Gui {

/// Design token names for consistent theming across the entire UI.
///
/// Resolution chain:  User Override -> Theme YAML -> Built-in Default
///
/// Usage:
///   QColor bg = ThemeTokens::resolve(ThemeTokens::SurfacePrimary);
///
/// Token names map to entries in the StyleParameters system.  Theme YAML
/// files should define these tokens.  Built-in defaults ensure the UI
/// works even without a theme file.
///
namespace ThemeTokens {

    // ── Surfaces ──────────────────────────────────────────────────────
    constexpr const char* SurfacePrimary     = "surface.primary";
    constexpr const char* SurfaceSecondary   = "surface.secondary";
    constexpr const char* SurfaceElevated    = "surface.elevated";
    constexpr const char* SurfaceSunken      = "surface.sunken";

    // ── Content ───────────────────────────────────────────────────────
    constexpr const char* ContentPrimary     = "content.primary";
    constexpr const char* ContentSecondary   = "content.secondary";
    constexpr const char* ContentDisabled    = "content.disabled";
    constexpr const char* ContentInverse     = "content.inverse";

    // ── Accent ────────────────────────────────────────────────────────
    constexpr const char* AccentPrimary      = "accent.primary";
    constexpr const char* AccentHover        = "accent.hover";
    constexpr const char* AccentActive       = "accent.active";
    constexpr const char* AccentSubtle       = "accent.subtle";

    // ── Status ────────────────────────────────────────────────────────
    constexpr const char* StatusError        = "status.error";
    constexpr const char* StatusWarning      = "status.warning";
    constexpr const char* StatusSuccess      = "status.success";
    constexpr const char* StatusInfo         = "status.info";

    // ── 3D Viewport ──────────────────────────────────────────────────
    constexpr const char* ViewportPreselect  = "viewport.preselect";
    constexpr const char* ViewportSelect     = "viewport.select";
    constexpr const char* ViewportEdge       = "viewport.edge";
    constexpr const char* ViewportBackground = "viewport.background";

    // ── Tree View ────────────────────────────────────────────────────
    constexpr const char* TreeSearchHighlight = "tree.search.highlight";
    constexpr const char* TreeRollbackActive  = "tree.rollback.active";
    constexpr const char* TreeRollbackSuppressed = "tree.rollback.suppressed";

    // ── Borders ──────────────────────────────────────────────────────
    constexpr const char* BorderDefault      = "border.default";
    constexpr const char* BorderStrong       = "border.strong";
    constexpr const char* BorderSubtle       = "border.subtle";

    /// Resolve a theme token to a QColor.
    ///
    /// Looks up the token in the StyleParameters system.  If not found,
    /// returns the built-in default for that token.  If no default is
    /// registered, returns a magenta color (#FF00FF) to make missing
    /// tokens visually obvious during development.
    GuiExport QColor resolve(const char* tokenName);

    /// Resolve a theme token to a QColor with an explicit fallback.
    GuiExport QColor resolve(const char* tokenName, const QColor& fallback);

}  // namespace ThemeTokens

}  // namespace Gui
