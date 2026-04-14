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
#include <QStringList>

#include <FCGlobal.h>

class QHBoxLayout;
class QVBoxLayout;
class QLabel;
class QFrame;
class QToolBar;

namespace Gui {

class ToolBarItem;
class CommandBase;


// ============================================================================
// RibbonButton — Large (icon-above-text) or Small (icon-beside-text)
// ============================================================================

class GuiExport RibbonButton : public QToolButton
{
    Q_OBJECT

public:
    enum ButtonSize { Large, Small };

    explicit RibbonButton(const QString& cmdName, ButtonSize size = Large,
                          QWidget* parent = nullptr);

    void setCommandName(const QString& name) { commandName = name; }
    const QString& getCommandName() const { return commandName; }
    void setButtonSize(ButtonSize size);

    QSize sizeHint() const override;
    QSize minimumSizeHint() const override;

private:
    QString commandName;
    ButtonSize btnSize;
};


// ============================================================================
// RibbonPanel — Labeled group of buttons with title bar + optional expand
// ============================================================================

class GuiExport RibbonPanel : public QFrame
{
    Q_OBJECT

public:
    explicit RibbonPanel(const QString& title, QWidget* parent = nullptr);

    void addButton(RibbonButton* button);
    void addSeparator();

    const QString& panelTitle() const { return title; }
    int buttonCount() const { return buttons.size(); }

Q_SIGNALS:
    void expandClicked();

protected:
    void paintEvent(QPaintEvent* event) override;

private:
    void relayoutButtons();

    QString title;
    QWidget* buttonArea{nullptr};
    QWidget* titleBar{nullptr};
    QLabel* titleLabel{nullptr};
    QToolButton* expandBtn{nullptr};
    QList<RibbonButton*> buttons;

    static constexpr int MaxRows = 3;
    static constexpr int ButtonSpacing = 2;
};


// ============================================================================
// RibbonTabPage — Horizontal row of panels inside a scroll area
// ============================================================================

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


// ============================================================================
// QuickAccessToolBar — Small toolbar above the ribbon tabs
// ============================================================================

class GuiExport QuickAccessToolBar : public QWidget
{
    Q_OBJECT

public:
    explicit QuickAccessToolBar(QWidget* parent = nullptr);

    void addCommand(const QString& cmdName);
    void removeCommand(const QString& cmdName);
    void setup();

    QStringList commands() const { return commandList; }

    static QStringList defaultCommands();

private:
    QHBoxLayout* layout{nullptr};
    QStringList commandList;
    QList<QToolButton*> buttonList;

    QToolButton* createSmallButton(const QString& cmdName);
    void loadPreferences();
    void savePreferences();
};


// ============================================================================
// RibbonBar — Main Inventor-style ribbon replacing classic toolbars
//
//  ┌─────────────────────────────────────────────────────────┐
//  │ [QAT: Save|Undo|Redo|...]                              │  ← QuickAccessToolBar
//  ├──[Home]──[View]──[Design]──[Part]──[Sketch]────────────┤  ← Tab bar
//  │ ┌──────┐ ┌──────────┐ ┌────────┐ ┌──────────────────┐  │
//  │ │ Clip │ │  Model   │ │ Modify │ │   Primitives     │  │  ← Panels
//  │ │ board│ │          │ │        │ │                   │  │
//  │ └──────┘ └──────────┘ └────────┘ └──────────────────┘  │
//  └─────────────────────────────────────────────────────────┘
// ============================================================================

class GuiExport RibbonBar : public QWidget
{
    Q_OBJECT

public:
    explicit RibbonBar(QWidget* parent = nullptr);
    ~RibbonBar() override;

    void setup(ToolBarItem* toolBarItems);
    void clear();

    static bool isRibbonEnabled();
    static void setRibbonEnabled(bool enabled);
    static RibbonBar* instance();

    QuickAccessToolBar* quickAccessToolBar() const { return qatBar; }

Q_SIGNALS:
    void ribbonVisibilityChanged(bool visible);

private:
    void setupStyle();
    RibbonPanel* createPanel(const QString& name, ToolBarItem* toolbarItem);
    RibbonButton* createButton(const QString& cmdName);
    QString categorizeToolbar(const QString& tbName) const;

    QuickAccessToolBar* qatBar{nullptr};
    QTabWidget* tabWidget{nullptr};
    QMap<QString, RibbonTabPage*> tabPages;

    static RibbonBar* _instance;
};


} // namespace Gui
