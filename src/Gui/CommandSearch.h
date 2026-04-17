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
#include <QLineEdit>
#include <QListWidget>
#include <QFrame>

#include <FCGlobal.h>

namespace Gui {

class Command;

/// Command palette / search bar for quickly finding and executing any
/// registered FreeCAD command.  Activated via Ctrl+Shift+P or the search
/// icon in the ribbon bar.
///
/// Shows a floating popup with fuzzy-matched command list.  Selecting an
/// entry executes the command and closes the palette.
class GuiExport CommandSearch : public QFrame
{
    Q_OBJECT

public:
    explicit CommandSearch(QWidget* parent = nullptr);
    ~CommandSearch() override = default;

    /// Show the palette centered on its parent, pre-populating the search text.
    void activate(const QString& initialText = {});

    /// Register the global shortcut (Ctrl+Shift+P).
    static void registerShortcut();
    static void openPalette(QWidget* parent = nullptr, const QString& initialText = {});

protected:
    bool eventFilter(QObject* obj, QEvent* event) override;

private Q_SLOTS:
    void onTextChanged(const QString& text);
    void onItemActivated(QListWidgetItem* item);

private:
    struct CommandEntry {
        Command* command{nullptr};
        QString displayName;
        QString searchText;   // lowercase, includes tooltip for broader matching
        QString shortcut;
    };

    void buildCommandIndex();
    void updateResults(const QString& query);
    bool fuzzyMatch(const QString& query, const QString& target) const;

    QLineEdit* searchEdit{nullptr};
    QListWidget* resultList{nullptr};
    std::vector<CommandEntry> commandIndex;

    static constexpr int MaxVisibleResults = 12;
    static constexpr int PopupWidth = 500;
};

}  // namespace Gui
