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
#include <QLineEdit>
#include <fastsignals/signal.h>

#include <FCGlobal.h>

class QHBoxLayout;
class QVBoxLayout;
class QLabel;
class QFrame;
class QToolBar;
class QVariantAnimation;

namespace Gui {

class ToolBarItem;
class CommandBase;
class ViewProviderDocumentObject;
class RibbonKeyTip;


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
    void addCustomWidget(QWidget* widget);
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
    QList<QWidget*> customWidgets;

    static constexpr int MaxRows = 3;
    static constexpr int ButtonSpacing = 6;
    static constexpr int SmallColumnSpacing = 4;
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
    void clearPanels();

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

    bool isMinimized() const { return ribbonMinimized; }
    void setMinimized(bool minimized);
    void toggleMinimized() { setMinimized(!ribbonMinimized); }

    QuickAccessToolBar* quickAccessToolBar() const { return qatBar; }
    QLineEdit* commandSearchField() const { return searchField; }

    // ── Contextual Tab API ────────────────────────────────────────────
    // Contextual tabs appear/disappear based on the active editing context
    // (e.g., sketch editing, assembly mode).  They are visually distinguished
    // by a colored header strip.

    /// Show a contextual tab.  If it already exists, it is made visible
    /// and optionally activated.  The accentColor tints the tab header.
    /// Returns the tab page for adding panels.
    RibbonTabPage* showContextualTab(const QString& name,
                                     const QColor& accentColor = {},
                                     bool activate = true);

    /// Hide (but don't destroy) a contextual tab.
    void hideContextualTab(const QString& name);

    /// Remove a contextual tab entirely.
    void removeContextualTab(const QString& name);

    /// Check if a contextual tab is currently visible.
    bool isContextualTabVisible(const QString& name) const;

protected:
    bool eventFilter(QObject* watched, QEvent* event) override;

Q_SIGNALS:
    void ribbonVisibilityChanged(bool visible);
    void contextualTabShown(const QString& name);
    void contextualTabHidden(const QString& name);

private:
    void setupStyle();
    RibbonPanel* createPanel(const QString& name, ToolBarItem* toolbarItem);
    RibbonPanel* createContextPanel(const QString& title, const QStringList& commandNames);
    RibbonButton* createButton(const QString& cmdName);
    QString categorizeToolbar(const QString& tbName) const;
    void refreshContextualTabs();
    void populateSketchContextualTab(RibbonTabPage* page);
    void populateAssemblyContextualTab(RibbonTabPage* page);
    void openBackstage();
    void applyMinimizedState(bool animated = true);
    void finalizeMinimizedLayout(bool showPanelArea);
    void updateMinimizeAffordance();
    void showMinimizedPreview();
    void collapseMinimizedPreview();
    bool shouldShowSketchContext(const QString& activeWorkbench,
                                 const ViewProviderDocumentObject* editViewProvider) const;
    bool shouldShowAssemblyContext(const QString& activeWorkbench,
                                   const ViewProviderDocumentObject* editViewProvider) const;

    QuickAccessToolBar* qatBar{nullptr};
    QToolButton* minimizeButton{nullptr};
    QLabel* ribbonStateBadge{nullptr};
    RibbonKeyTip* keyTipOverlay{nullptr};
    QLineEdit* searchField{nullptr};
    QTabWidget* tabWidget{nullptr};
    QMap<QString, RibbonTabPage*> tabPages;
    int fileTabIndex{-1};
    int lastContentTabIndex{-1};

    /// Contextual tabs: name -> (page, accentColor, tabIndex when visible)
    struct ContextualTabInfo {
        RibbonTabPage* page{nullptr};
        QColor accentColor;
        int tabIndex{-1};     ///< -1 when hidden
    };
    QMap<QString, ContextualTabInfo> contextualTabs;
    bool ribbonMinimized{false};
    bool previewExpandedWhileMinimized{false};
    bool pendingShowPanelArea{true};
    QVariantAnimation* ribbonHeightAnimation{nullptr};
    fastsignals::scoped_connection inEditConnection;
    fastsignals::scoped_connection resetEditConnection;

    static RibbonBar* _instance;
};


} // namespace Gui
