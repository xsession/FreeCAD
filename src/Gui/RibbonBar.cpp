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

#include <QHBoxLayout>
#include <QVBoxLayout>
#include <QLabel>
#include <QFrame>
#include <QPainter>
#include <QApplication>
#include <QScrollArea>
#include <QStyle>
#include <QAction>
#include <QMenu>
#include <QPainterPath>

#include <App/Application.h>

#include "RibbonBar.h"
#include "Action.h"
#include "ToolBarManager.h"
#include "Application.h"
#include "Command.h"
#include "BitmapFactory.h"
#include "MainWindow.h"


using namespace Gui;

RibbonBar* RibbonBar::_instance = nullptr;

// ============================================================================
// Ribbon style constants
// ============================================================================

namespace {
    constexpr int LargeIconSize      = 32;
    constexpr int SmallIconSize      = 16;
    constexpr int LargeButtonWidth   = 64;
    constexpr int LargeButtonHeight  = 66;
    constexpr int SmallButtonWidth   = 110;
    constexpr int SmallButtonHeight  = 22;
    constexpr int PanelMinWidth      = 54;
    constexpr int RibbonHeight       = 120;
    constexpr int PanelTitleHeight   = 18;
    constexpr int TabBarHeight       = 24;
}


// ============================================================================
// RibbonButton
// ============================================================================

RibbonButton::RibbonButton(const QString& cmdName, ButtonSize size, QWidget* parent)
    : QToolButton(parent)
    , commandName(cmdName)
    , btnSize(size)
{
    setAutoRaise(true);
    setFocusPolicy(Qt::NoFocus);

    if (size == Large) {
        setToolButtonStyle(Qt::ToolButtonTextUnderIcon);
        setIconSize(QSize(LargeIconSize, LargeIconSize));
        setFixedHeight(LargeButtonHeight);
        setMinimumWidth(LargeButtonWidth);
    }
    else {
        setToolButtonStyle(Qt::ToolButtonTextBesideIcon);
        setIconSize(QSize(SmallIconSize, SmallIconSize));
        setFixedHeight(SmallButtonHeight);
        setMinimumWidth(SmallButtonWidth);
    }

    setSizePolicy(QSizePolicy::Preferred, QSizePolicy::Fixed);
}

QSize RibbonButton::sizeHint() const
{
    if (btnSize == Large) {
        QFontMetrics fm(font());
        int textWidth = fm.horizontalAdvance(text()) + 12;
        int w = qMax(LargeButtonWidth, textWidth);
        return QSize(w, LargeButtonHeight);
    }
    return QSize(SmallButtonWidth, SmallButtonHeight);
}

QSize RibbonButton::minimumSizeHint() const
{
    if (btnSize == Large) {
        return QSize(LargeButtonWidth, LargeButtonHeight);
    }
    return QSize(SmallButtonWidth, SmallButtonHeight);
}


// ============================================================================
// RibbonPanel
// ============================================================================

RibbonPanel::RibbonPanel(const QString& title, QWidget* parent)
    : QFrame(parent)
    , title(title)
{
    setFrameStyle(QFrame::NoFrame);
    setSizePolicy(QSizePolicy::Preferred, QSizePolicy::Fixed);

    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(3, 2, 3, 0);
    mainLayout->setSpacing(0);

    // Button area
    buttonArea = new QWidget(this);
    buttonArea->setSizePolicy(QSizePolicy::Preferred, QSizePolicy::Expanding);
    mainLayout->addWidget(buttonArea, 1);

    // Title label at bottom
    titleLabel = new QLabel(title, this);
    titleLabel->setAlignment(Qt::AlignHCenter | Qt::AlignBottom);
    titleLabel->setFixedHeight(PanelTitleHeight);
    QFont titleFont = titleLabel->font();
    titleFont.setPointSize(titleFont.pointSize() - 1);
    titleLabel->setFont(titleFont);
    titleLabel->setStyleSheet(QStringLiteral(
        "QLabel { color: palette(mid); padding: 0px; margin: 0px; }"));
    mainLayout->addWidget(titleLabel);

    setLayout(mainLayout);
}

void RibbonPanel::addButton(RibbonButton* button)
{
    button->setParent(buttonArea);
    buttons.append(button);
    relayoutButtons();
}

void RibbonPanel::addSeparator()
{
    // Visual separator handled implicitly by layout spacing
}

void RibbonPanel::paintEvent(QPaintEvent* event)
{
    QFrame::paintEvent(event);

    QPainter painter(this);
    painter.setRenderHint(QPainter::Antialiasing, false);

    // Draw right-side separator line
    QPen pen(palette().mid().color());
    pen.setWidth(1);
    painter.setPen(pen);
    painter.drawLine(width() - 1, 4, width() - 1, height() - 4);
}

void RibbonPanel::relayoutButtons()
{
    // Delete old layout
    if (buttonArea->layout()) {
        QLayoutItem* item;
        while ((item = buttonArea->layout()->takeAt(0)) != nullptr) {
            delete item;
        }
        delete buttonArea->layout();
    }

    if (buttons.isEmpty()) {
        return;
    }

    // Count large and small buttons
    int largeCount = 0;
    int smallCount = 0;
    for (auto* btn : buttons) {
        if (btn->sizeHint().height() > SmallButtonHeight + 4) {
            ++largeCount;
        }
        else {
            ++smallCount;
        }
    }

    // Layout strategy:
    // - Large buttons are placed in a horizontal row
    // - Small buttons are stacked in columns of MaxRows (3)
    auto* hLayout = new QHBoxLayout(buttonArea);
    hLayout->setContentsMargins(0, 0, 0, 0);
    hLayout->setSpacing(ButtonSpacing);

    QVBoxLayout* currentSmallColumn = nullptr;
    int smallInColumn = 0;

    for (auto* btn : buttons) {
        bool isLarge = (btn->sizeHint().height() > SmallButtonHeight + 4);

        if (isLarge) {
            // Flush any pending small column
            if (currentSmallColumn) {
                currentSmallColumn->addStretch();
                currentSmallColumn = nullptr;
                smallInColumn = 0;
            }
            hLayout->addWidget(btn);
        }
        else {
            // Stack small buttons in columns of 3
            if (!currentSmallColumn || smallInColumn >= MaxRows) {
                currentSmallColumn = new QVBoxLayout();
                currentSmallColumn->setContentsMargins(0, 0, 0, 0);
                currentSmallColumn->setSpacing(1);
                hLayout->addLayout(currentSmallColumn);
                smallInColumn = 0;
            }
            currentSmallColumn->addWidget(btn);
            ++smallInColumn;
        }
    }

    if (currentSmallColumn && smallInColumn < MaxRows) {
        currentSmallColumn->addStretch();
    }

    hLayout->addStretch(0);
    buttonArea->setLayout(hLayout);
}


// ============================================================================
// RibbonTabPage
// ============================================================================

RibbonTabPage::RibbonTabPage(QWidget* parent)
    : QWidget(parent)
{
    auto* mainLayout = new QHBoxLayout(this);
    mainLayout->setContentsMargins(0, 0, 0, 0);
    mainLayout->setSpacing(0);

    scrollArea = new QScrollArea(this);
    scrollArea->setWidgetResizable(true);
    scrollArea->setHorizontalScrollBarPolicy(Qt::ScrollBarAsNeeded);
    scrollArea->setVerticalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
    scrollArea->setFrameStyle(QFrame::NoFrame);
    scrollArea->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed);

    scrollContent = new QWidget(scrollArea);
    panelLayout = new QHBoxLayout(scrollContent);
    panelLayout->setContentsMargins(4, 0, 4, 0);
    panelLayout->setSpacing(2);
    panelLayout->addStretch(1);
    scrollContent->setLayout(panelLayout);

    scrollArea->setWidget(scrollContent);
    mainLayout->addWidget(scrollArea);
    setLayout(mainLayout);
}

void RibbonTabPage::addPanel(RibbonPanel* panel)
{
    // Insert before the stretch
    int idx = panelLayout->count() - 1;  // before stretch
    panelLayout->insertWidget(idx, panel);
    panelList.append(panel);
}


// ============================================================================
// RibbonBar
// ============================================================================

RibbonBar::RibbonBar(QWidget* parent)
    : QWidget(parent)
{
    _instance = this;

    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(0, 0, 0, 0);
    mainLayout->setSpacing(0);

    tabWidget = new QTabWidget(this);
    tabWidget->setTabPosition(QTabWidget::North);
    tabWidget->setDocumentMode(false);
    tabWidget->setUsesScrollButtons(true);
    tabWidget->setElideMode(Qt::ElideNone);
    tabWidget->setFixedHeight(RibbonHeight);

    mainLayout->addWidget(tabWidget);
    setLayout(mainLayout);

    setFixedHeight(RibbonHeight);
    setupStyle();
}

RibbonBar::~RibbonBar()
{
    if (_instance == this) {
        _instance = nullptr;
    }
}

RibbonBar* RibbonBar::instance()
{
    return _instance;
}

bool RibbonBar::isRibbonEnabled()
{
    return App::GetApplication()
        .GetUserParameter()
        .GetGroup("BaseApp")
        ->GetGroup("Preferences")
        ->GetGroup("MainWindow")
        ->GetBool("UseRibbonBar", false);
}

void RibbonBar::setRibbonEnabled(bool enabled)
{
    App::GetApplication()
        .GetUserParameter()
        .GetGroup("BaseApp")
        ->GetGroup("Preferences")
        ->GetGroup("MainWindow")
        ->SetBool("UseRibbonBar", enabled);
}

void RibbonBar::setupStyle()
{
    tabWidget->setStyleSheet(QStringLiteral(
        "QTabWidget::pane {"
        "  border: none;"
        "  border-top: 1px solid palette(mid);"
        "  background: palette(window);"
        "}"
        "QTabWidget::tab-bar {"
        "  left: 4px;"
        "}"
        "QTabBar::tab {"
        "  padding: 4px 14px;"
        "  margin-right: 2px;"
        "  background: palette(button);"
        "  border: 1px solid palette(mid);"
        "  border-bottom: none;"
        "  border-top-left-radius: 4px;"
        "  border-top-right-radius: 4px;"
        "  font-weight: bold;"
        "  min-width: 60px;"
        "}"
        "QTabBar::tab:selected {"
        "  background: palette(window);"
        "  border-bottom: 1px solid palette(window);"
        "}"
        "QTabBar::tab:hover:!selected {"
        "  background: palette(midlight);"
        "}"
    ));
}

void RibbonBar::setup(ToolBarItem* toolBarItems)
{
    if (!toolBarItems) {
        return;
    }

    clear();

    // Categorization map: group related toolbars into ribbon tabs
    // Key = tab name, Value = list of toolbar items for that tab
    struct TabDef {
        QString name;
        QList<ToolBarItem*> toolbars;
    };

    QList<ToolBarItem*> items = toolBarItems->getItems();

    // Category mapping: map toolbar names to logical ribbon tabs
    // This creates an Inventor-like grouping
    QMap<QString, QStringList> categoryMap;

    // Pass 1: Categorize toolbars into tabs
    // Standard toolbars go into "Home" tab
    // Workbench-specific toolbars get their own tabs or go into themed tabs
    QMap<QString, QList<ToolBarItem*>> tabMap;
    QStringList tabOrder;

    for (ToolBarItem* it : items) {
        QString tbName = QString::fromUtf8(it->command().c_str());

        // Classify into ribbon tabs
        QString tabName;
        if (tbName == QStringLiteral("File")
            || tbName == QStringLiteral("Edit")
            || tbName == QStringLiteral("Clipboard")
            || tbName == QStringLiteral("Macro")) {
            tabName = tr("Home");
        }
        else if (tbName == QStringLiteral("View")
                 || tbName == QStringLiteral("Navigation")
                 || tbName == QStringLiteral("Individual views")) {
            tabName = tr("View");
        }
        else if (tbName.contains(QStringLiteral("Sketch"))
                 || tbName.contains(QStringLiteral("sketch"))) {
            tabName = tr("Sketch");
        }
        else if (tbName.contains(QStringLiteral("Part Design"))
                 || tbName.contains(QStringLiteral("PartDesign"))) {
            tabName = tr("Design");
        }
        else if (tbName.contains(QStringLiteral("Part"))
                 && !tbName.contains(QStringLiteral("Design"))) {
            tabName = tr("Part");
        }
        else if (tbName.contains(QStringLiteral("Assembly"))) {
            tabName = tr("Assembly");
        }
        else if (tbName.contains(QStringLiteral("Mesh"))
                 || tbName.contains(QStringLiteral("FEM"))
                 || tbName.contains(QStringLiteral("Fem"))) {
            tabName = tr("Analysis");
        }
        else if (tbName.contains(QStringLiteral("Drawing"))
                 || tbName.contains(QStringLiteral("TechDraw"))) {
            tabName = tr("Drawing");
        }
        else if (tbName.contains(QStringLiteral("CAM"))
                 || tbName.contains(QStringLiteral("Path"))) {
            tabName = tr("Manufacturing");
        }
        else if (tbName == QStringLiteral("Structure")
                 || tbName == QStringLiteral("Help")) {
            tabName = tr("Home");
        }
        else {
            // Unknown toolbars go into a "Tools" tab
            tabName = tr("Tools");
        }

        if (!tabMap.contains(tabName)) {
            tabOrder.append(tabName);
        }
        tabMap[tabName].append(it);
    }

    // Pass 2: Create ribbon tabs and panels
    for (const QString& tabName : tabOrder) {
        auto* tabPage = new RibbonTabPage(tabWidget);
        tabWidget->addTab(tabPage, tabName);
        tabPages[tabName] = tabPage;

        for (ToolBarItem* tbItem : tabMap[tabName]) {
            RibbonPanel* panel = createPanel(
                QString::fromUtf8(tbItem->command().c_str()), tbItem);
            if (panel && panel->buttonCount() > 0) {
                tabPage->addPanel(panel);
            }
            else {
                delete panel;
            }
        }
    }
}

void RibbonBar::clear()
{
    tabWidget->clear();
    tabPages.clear();
}

RibbonPanel* RibbonBar::createPanel(const QString& name, ToolBarItem* toolbarItem)
{
    // Translate the toolbar name for display
    QByteArray tbNameBytes = name.toUtf8();
    QString displayName = QApplication::translate("Workbench", tbNameBytes.constData());

    auto* panel = new RibbonPanel(displayName);

    QList<ToolBarItem*> commands = toolbarItem->getItems();

    // Heuristic: first few commands in a toolbar are "primary" → large buttons
    // Remaining commands are "secondary" → small buttons in stacked columns
    // Threshold: first 4 non-separator commands get large buttons
    int primaryCount = 0;
    constexpr int primaryLimit = 6;

    for (ToolBarItem* cmdItem : commands) {
        QString cmdName = QString::fromLatin1(cmdItem->command().c_str());

        if (cmdName == QStringLiteral("Separator")) {
            panel->addSeparator();
            continue;
        }

        RibbonButton::ButtonSize size = (primaryCount < primaryLimit)
            ? RibbonButton::Large
            : RibbonButton::Small;

        RibbonButton* btn = createButton(cmdName);
        if (btn) {
            // If this is complex (dropdown), keep it large regardless
            if (btn->menu() || btn->popupMode() != QToolButton::DelayedPopup) {
                size = RibbonButton::Large;
            }

            // Rebuild button with correct size if needed
            if (size == RibbonButton::Small
                && btn->toolButtonStyle() != Qt::ToolButtonTextBesideIcon) {
                btn->setToolButtonStyle(Qt::ToolButtonTextBesideIcon);
                btn->setIconSize(QSize(SmallIconSize, SmallIconSize));
                btn->setFixedHeight(SmallButtonHeight);
                btn->setMinimumWidth(SmallButtonWidth);
            }

            panel->addButton(btn);
            ++primaryCount;
        }
    }

    return panel;
}

RibbonButton* RibbonBar::createButton(const QString& cmdName)
{
    CommandManager& mgr = Application::Instance->commandManager();
    Command* cmd = mgr.getCommandByName(cmdName.toLatin1().constData());
    if (!cmd) {
        return nullptr;
    }

    auto* btn = new RibbonButton(cmdName, RibbonButton::Large);

    // Get icon
    const char* pixmapName = cmd->getPixmap();
    if (pixmapName && pixmapName[0]) {
        QPixmap pm = BitmapFactory().pixmapFromSvg(
            pixmapName, QSizeF(LargeIconSize, LargeIconSize));
        if (pm.isNull()) {
            pm = BitmapFactory().pixmap(pixmapName);
        }
        if (!pm.isNull()) {
            btn->setIcon(QIcon(pm));
        }
    }

    // Get display text — use menu text, strip "&" accelerator
    const char* menuText = cmd->getMenuText();
    if (menuText && menuText[0]) {
        QString text = QApplication::translate(cmd->className(), menuText);
        text.remove(QChar::fromLatin1('&'));
        // For large buttons, word-wrap at ~10 chars
        if (text.length() > 12) {
            int mid = text.length() / 2;
            int spacePos = text.indexOf(QChar::fromLatin1(' '), mid);
            int spaceBefore = text.lastIndexOf(QChar::fromLatin1(' '), mid);
            if (spacePos >= 0 && (spaceBefore < 0
                || (spacePos - mid) < (mid - spaceBefore))) {
                text[spacePos] = QChar::fromLatin1('\n');
            }
            else if (spaceBefore >= 0) {
                text[spaceBefore] = QChar::fromLatin1('\n');
            }
        }
        btn->setText(text);
    }

    // Get tooltip
    const char* toolTip = cmd->getToolTipText();
    if (toolTip && toolTip[0]) {
        btn->setToolTip(QApplication::translate(cmd->className(), toolTip));
    }

    // Connect to command execution
    QObject::connect(btn, &QToolButton::clicked, [cmdName]() {
        CommandManager& mgr = Application::Instance->commandManager();
        mgr.runCommandByName(cmdName.toLatin1().constData());
    });

    // If the command has a menu/dropdown (ActionGroup), try to set popupMode
    Action* cmdAction = cmd->getAction();
    if (cmdAction) {
        QAction* qaction = cmdAction->action();
        if (qaction && qaction->menu()) {
            btn->setMenu(qaction->menu());
            btn->setPopupMode(QToolButton::MenuButtonPopup);
        }
    }

    return btn;
}
