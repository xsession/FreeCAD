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
#include <QTabWidget>
#include <QToolButton>
#include <QScrollArea>
#include <QMap>
#include <QString>
#include <QIcon>

#include <FCGlobal.h>

class QHBoxLayout;
class QVBoxLayout;
class QLabel;
class QFrame;

namespace Gui {

class ToolBarItem;
class CommandBase;


/**
 * @brief A single large command button — Inventor-style.
 *
 * Shows a 32×32 icon above a two-line label (command name).
 * Optionally shows only icon + one-line label for compact mode.
 */
class GuiExport RibbonButton : public QToolButton
{
    Q_OBJECT

public:
    enum ButtonSize { Large, Small };

    explicit RibbonButton(const QString& cmdName, ButtonSize size = Large,
                          QWidget* parent = nullptr);

    void setCommandName(const QString& name) { commandName = name; }
    const QString& getCommandName() const { return commandName; }

    QSize sizeHint() const override;
    QSize minimumSizeHint() const override;

private:
    QString commandName;
    ButtonSize btnSize;
};


/**
 * @brief A named group of buttons inside a ribbon tab — Inventor "panel" style.
 *
 * Layout:
 *  ┌─────────────────────────────────┐
 *  │ [icon+txt] [icon+txt] [icon+txt]│
 *  │ [icon+txt] [icon+txt]           │
 *  ├─────────────────────────────────┤
 *  │        Panel Title              │
 *  └─────────────────────────────────┘
 */
class GuiExport RibbonPanel : public QFrame
{
    Q_OBJECT

public:
    explicit RibbonPanel(const QString& title, QWidget* parent = nullptr);

    void addButton(RibbonButton* button);
    void addSeparator();

    const QString& panelTitle() const { return title; }
    int buttonCount() const { return buttons.size(); }

protected:
    void paintEvent(QPaintEvent* event) override;

private:
    void relayoutButtons();

    QString title;
    QWidget* buttonArea{nullptr};
    QLabel* titleLabel{nullptr};
    QList<RibbonButton*> buttons;

    static constexpr int MaxRows = 3;       ///< Max rows before adding a column
    static constexpr int ButtonSpacing = 2;
};


/**
 * @brief A ribbon tab page containing multiple panels.
 *
 * Layout:
 *  ┌──────────┬──────────┬──────────┬──────────┐
 *  │ Panel 1  │ Panel 2  │ Panel 3  │ Panel 4  │
 *  └──────────┴──────────┴──────────┴──────────┘
 */
class GuiExport RibbonTabPage : public QWidget
{
    Q_OBJECT

public:
    explicit RibbonTabPage(QWidget* parent = nullptr);

    void addPanel(RibbonPanel* panel);

    const QList<RibbonPanel*>& panels() const { return panelList; }

private:
    QHBoxLayout* panelLayout{nullptr};
    QScrollArea* scrollArea{nullptr};
    QWidget* scrollContent{nullptr};
    QList<RibbonPanel*> panelList;
};


/**
 * @brief Autodesk Inventor-style ribbon bar — replaces traditional toolbars.
 *
 * Uses QTabWidget where each tab maps to a toolbar group from the workbench.
 * Commands are shown as large icon buttons with descriptive text, organized
 * into labeled panels for easy discovery.
 *
 * Integration:
 *  - Called from ToolBarManager::setup() to populate
 *  - Reads command icons and text from CommandManager
 *  - Preference "UseRibbonBar" toggles between ribbon and classic toolbars
 */
class GuiExport RibbonBar : public QWidget
{
    Q_OBJECT

public:
    explicit RibbonBar(QWidget* parent = nullptr);
    ~RibbonBar() override;

    /// Populate the ribbon from ToolBarItem data (called from workbench activation)
    void setup(ToolBarItem* toolBarItems);

    /// Clear all tabs and panels
    void clear();

    /// Check if ribbon mode is enabled in preferences
    static bool isRibbonEnabled();

    /// Enable or disable ribbon mode
    static void setRibbonEnabled(bool enabled);

    /// Get the singleton instance (created by MainWindow)
    static RibbonBar* instance();

Q_SIGNALS:
    void ribbonVisibilityChanged(bool visible);

private:
    void setupStyle();
    RibbonPanel* createPanel(const QString& name, ToolBarItem* toolbarItem);
    RibbonButton* createButton(const QString& cmdName);

    QTabWidget* tabWidget{nullptr};
    QMap<QString, RibbonTabPage*> tabPages;

    static RibbonBar* _instance;
};


} // namespace Gui
