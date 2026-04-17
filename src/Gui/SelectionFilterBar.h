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

#include <QWidget>
#include <QToolButton>

#include <FCGlobal.h>

namespace Base
{
class ParameterGrp;
}

namespace Gui {

/// Status bar widget that provides toggle buttons for selection element
/// filtering: Vertex, Edge, Face, Solid.
///
/// When a filter is active, only the specified sub-element types can be
/// selected in the 3D viewport via the SelectionGate system.
///
/// Integrates with the existing SelectionSingleton and SelectionGate API.
class GuiExport SelectionFilterBar : public QWidget
{
    Q_OBJECT

public:
    enum ElementType {
        Vertex = 0,
        Edge   = 1,
        Face   = 2,
        Solid  = 3
    };

    explicit SelectionFilterBar(QWidget* parent = nullptr);
    ~SelectionFilterBar() override = default;

    /// Check if a specific element type is enabled for selection.
    bool isTypeEnabled(ElementType type) const;

    /// Set the enabled state of a specific element type.
    void setTypeEnabled(ElementType type, bool enabled);

    /// Reset all filters (allow everything).
    void resetAll();

    /// Install the selection gate based on current filter state.
    /// Called automatically when toggles change.  Public for programmatic control.
    void applyFilter();

Q_SIGNALS:
    void filterChanged();

private:
    void createButtons();
    QToolButton* makeToggle(const QString& iconName,
                            const QString& tooltip,
                            ElementType type);
    void loadState();
    void saveState() const;
    void refreshUi();
    bool areAllTypesEnabled() const;
    QString buildFilterString() const;
    QString buildSummaryText() const;

    QToolButton* buttons[4]{};
    QToolButton* resetButton = nullptr;

    static constexpr int NumTypes = 4;
    static constexpr const char* typeNames[] = {"Vertex", "Edge", "Face", "Solid"};
};

}  // namespace Gui
