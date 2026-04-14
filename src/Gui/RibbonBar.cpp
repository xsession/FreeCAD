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
#include <QLinearGradient>
#include <QToolBar>
#include <QStringList>

#include <App/Application.h>
#include <Base/Parameter.h>

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
// Ribbon style constants — Inventor-style dimensions
// ============================================================================

namespace {
    constexpr int LargeIconSize      = 32;
    constexpr int SmallIconSize      = 16;
    constexpr int QATIconSize        = 16;
    constexpr int LargeButtonWidth   = 60;
    constexpr int LargeButtonHeight  = 66;
    constexpr int SmallButtonWidth   = 100;
    constexpr int SmallButtonHeight  = 22;
    constexpr int PanelMinWidth      = 48;
    constexpr int RibbonHeight       = 125;
    constexpr int PanelTitleHeight   = 20;
    constexpr int TabBarHeight       = 24;
    constexpr int QATBarHeight       = 26;
    constexpr int PanelContentHeight = RibbonHeight - TabBarHeight - PanelTitleHeight - 6;
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
    setButtonSize(size);
}

void RibbonButton::setButtonSize(ButtonSize size)
{
    btnSize = size;
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
// RibbonPanel — Inventor-style panel with title bar and expand button
// ============================================================================

RibbonPanel::RibbonPanel(const QString& title, QWidget* parent)
    : QFrame(parent)
    , title(title)
{
    setFrameStyle(QFrame::NoFrame);
    setSizePolicy(QSizePolicy::Preferred, QSizePolicy::Fixed);
    setMinimumWidth(PanelMinWidth);

    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(2, 2, 2, 0);
    mainLayout->setSpacing(0);

    // Button area — expands to fill panel height
    buttonArea = new QWidget(this);
    buttonArea->setSizePolicy(QSizePolicy::Preferred, QSizePolicy::Expanding);
    buttonArea->setFixedHeight(PanelContentHeight);
    mainLayout->addWidget(buttonArea, 1);

    // Title bar at bottom — label + expand arrow (Inventor-style)
    titleBar = new QWidget(this);
    titleBar->setFixedHeight(PanelTitleHeight);
    auto* titleLayout = new QHBoxLayout(titleBar);
    titleLayout->setContentsMargins(4, 0, 2, 2);
    titleLayout->setSpacing(2);

    titleLabel = new QLabel(title, titleBar);
    titleLabel->setAlignment(Qt::AlignLeft | Qt::AlignVCenter);
    QFont titleFont = titleLabel->font();
    titleFont.setPointSizeF(titleFont.pointSizeF() - 0.5);
    titleLabel->setFont(titleFont);
    titleLayout->addWidget(titleLabel, 1);

    // Panel dialog launcher / expand button (small diagonal arrow like Inventor)
    expandBtn = new QToolButton(titleBar);
    expandBtn->setFixedSize(14, 14);
    expandBtn->setAutoRaise(true);
    expandBtn->setArrowType(Qt::NoArrow);
    expandBtn->setText(QStringLiteral("\u2197"));  // ↗ arrow character
    expandBtn->setToolTip(tr("Expand panel"));
    expandBtn->setStyleSheet(QStringLiteral(
        "QToolButton { font-size: 9px; border: none; padding: 0; }"
        "QToolButton:hover { background: palette(midlight); border-radius: 2px; }"));
    connect(expandBtn, &QToolButton::clicked, this, &RibbonPanel::expandClicked);
    titleLayout->addWidget(expandBtn);

    titleBar->setLayout(titleLayout);
    mainLayout->addWidget(titleBar);

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
    // Handled by layout spacing
}

void RibbonPanel::paintEvent(QPaintEvent* event)
{
    QFrame::paintEvent(event);

    QPainter painter(this);
    painter.setRenderHint(QPainter::Antialiasing, false);

    QColor sepColor = palette().mid().color();
    sepColor.setAlpha(120);
    QPen pen(sepColor);
    pen.setWidth(1);
    painter.setPen(pen);

    // Right-side panel separator
    painter.drawLine(width() - 1, 4, width() - 1, height() - 4);

    // Top line of title bar area
    int titleY = height() - PanelTitleHeight;
    QColor lineColor = palette().mid().color();
    lineColor.setAlpha(60);
    painter.setPen(QPen(lineColor));
    painter.drawLine(4, titleY, width() - 4, titleY);
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
// QuickAccessToolBar — compact toolbar above the ribbon tabs
// ============================================================================

QuickAccessToolBar::QuickAccessToolBar(QWidget* parent)
    : QWidget(parent)
{
    setFixedHeight(QATBarHeight);
    setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed);

    layout = new QHBoxLayout(this);
    layout->setContentsMargins(8, 2, 8, 2);
    layout->setSpacing(1);
    layout->addStretch(1);
    setLayout(layout);

    setStyleSheet(QStringLiteral(
        "QuickAccessToolBar {"
        "  background: palette(window);"
        "  border-bottom: 1px solid palette(mid);"
        "}"
    ));

    loadPreferences();
}

QStringList QuickAccessToolBar::defaultCommands()
{
    return {
        QStringLiteral("Std_New"),
        QStringLiteral("Std_Open"),
        QStringLiteral("Std_Save"),
        QStringLiteral("Std_Undo"),
        QStringLiteral("Std_Redo"),
        QStringLiteral("Std_Print"),
    };
}

void QuickAccessToolBar::loadPreferences()
{
    auto hGrp = App::GetApplication()
        .GetUserParameter()
        .GetGroup("BaseApp")
        ->GetGroup("Preferences")
        ->GetGroup("MainWindow");

    std::string cmds = hGrp->GetASCII("QuickAccessCommands", "");
    commandList.clear();

    if (cmds.empty()) {
        commandList = defaultCommands();
    }
    else {
        commandList = QString::fromUtf8(cmds.c_str()).split(QStringLiteral(";"),
                                                             Qt::SkipEmptyParts);
    }
}

void QuickAccessToolBar::savePreferences()
{
    auto hGrp = App::GetApplication()
        .GetUserParameter()
        .GetGroup("BaseApp")
        ->GetGroup("Preferences")
        ->GetGroup("MainWindow");

    hGrp->SetASCII("QuickAccessCommands",
                    commandList.join(QStringLiteral(";")).toUtf8().constData());
}

QToolButton* QuickAccessToolBar::createSmallButton(const QString& cmdName)
{
    CommandManager& mgr = Application::Instance->commandManager();
    Command* cmd = mgr.getCommandByName(cmdName.toLatin1().constData());
    if (!cmd) {
        return nullptr;
    }

    auto* btn = new QToolButton(this);
    btn->setAutoRaise(true);
    btn->setFocusPolicy(Qt::NoFocus);
    btn->setIconSize(QSize(QATIconSize, QATIconSize));
    btn->setFixedSize(QATBarHeight - 4, QATBarHeight - 4);
    btn->setToolButtonStyle(Qt::ToolButtonIconOnly);

    const char* pixmapName = cmd->getPixmap();
    if (pixmapName && pixmapName[0]) {
        QPixmap pm = BitmapFactory().pixmapFromSvg(
            pixmapName, QSizeF(QATIconSize, QATIconSize));
        if (pm.isNull()) {
            pm = BitmapFactory().pixmap(pixmapName);
        }
        if (!pm.isNull()) {
            btn->setIcon(QIcon(pm));
        }
    }

    const char* toolTip = cmd->getToolTipText();
    if (toolTip && toolTip[0]) {
        btn->setToolTip(QApplication::translate(cmd->className(), toolTip));
    }

    QObject::connect(btn, &QToolButton::clicked, [cmdName]() {
        CommandManager& mgr = Application::Instance->commandManager();
        mgr.runCommandByName(cmdName.toLatin1().constData());
    });

    // Dropdown menu support
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

void QuickAccessToolBar::setup()
{
    // Clear existing buttons
    for (auto* btn : buttonList) {
        layout->removeWidget(btn);
        delete btn;
    }
    buttonList.clear();

    // Remove the stretch
    while (layout->count() > 0) {
        auto* item = layout->takeAt(0);
        delete item;
    }

    for (const QString& cmdName : commandList) {
        auto* btn = createSmallButton(cmdName);
        if (btn) {
            layout->addWidget(btn);
            buttonList.append(btn);
        }
    }

    // Separator then a customize dropdown
    if (!buttonList.isEmpty()) {
        auto* sep = new QFrame(this);
        sep->setFrameShape(QFrame::VLine);
        sep->setFrameShadow(QFrame::Sunken);
        sep->setFixedWidth(2);
        sep->setFixedHeight(QATBarHeight - 8);
        layout->addWidget(sep);
    }

    layout->addStretch(1);
}

void QuickAccessToolBar::addCommand(const QString& cmdName)
{
    if (!commandList.contains(cmdName)) {
        commandList.append(cmdName);
        savePreferences();
        setup();
    }
}

void QuickAccessToolBar::removeCommand(const QString& cmdName)
{
    if (commandList.removeAll(cmdName) > 0) {
        savePreferences();
        setup();
    }
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

    // Quick Access Toolbar — small icons above ribbon tabs
    qatBar = new QuickAccessToolBar(this);
    mainLayout->addWidget(qatBar);

    // Tab widget for ribbon panels
    tabWidget = new QTabWidget(this);
    tabWidget->setTabPosition(QTabWidget::North);
    tabWidget->setDocumentMode(false);
    tabWidget->setUsesScrollButtons(true);
    tabWidget->setElideMode(Qt::ElideNone);

    mainLayout->addWidget(tabWidget, 1);
    setLayout(mainLayout);

    setFixedHeight(RibbonHeight + QATBarHeight);
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
    // Inventor-style ribbon:
    // - Tabs: compact, bold text, active tab blends into panel area
    // - Panels: subtle gradient background, thin separator lines
    // - Active tab: same background as panel area (seamless)
    tabWidget->setStyleSheet(QStringLiteral(
        "QTabWidget {"
        "  background: transparent;"
        "}"
        "QTabWidget::pane {"
        "  border: none;"
        "  border-top: 1px solid palette(mid);"
        "  border-bottom: 1px solid palette(mid);"
        "  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,"
        "    stop:0 palette(window), stop:1 palette(button));"
        "}"
        "QTabWidget::tab-bar {"
        "  left: 2px;"
        "}"
        "QTabBar {"
        "  background: transparent;"
        "}"
        "QTabBar::tab {"
        "  padding: 3px 14px;"
        "  margin-right: 1px;"
        "  background: palette(button);"
        "  border: 1px solid palette(mid);"
        "  border-bottom: none;"
        "  border-top-left-radius: 3px;"
        "  border-top-right-radius: 3px;"
        "  font-weight: bold;"
        "  font-size: 11px;"
        "  min-width: 50px;"
        "  color: palette(text);"
        "}"
        "QTabBar::tab:selected {"
        "  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,"
        "    stop:0 palette(light), stop:1 palette(window));"
        "  border-bottom: 1px solid palette(window);"
        "  margin-bottom: -1px;"
        "}"
        "QTabBar::tab:hover:!selected {"
        "  background: palette(midlight);"
        "}"
        "QTabBar::tab:first {"
        "  margin-left: 2px;"
        "}"
    ));
}

void RibbonBar::setup(ToolBarItem* toolBarItems)
{
    if (!toolBarItems) {
        return;
    }

    clear();

    // Populate Quick Access Toolbar
    qatBar->setup();

    QList<ToolBarItem*> items = toolBarItems->getItems();

    // Group toolbars into ribbon tabs by category
    QMap<QString, QList<ToolBarItem*>> tabMap;
    QStringList tabOrder;

    for (ToolBarItem* it : items) {
        QString tbName = QString::fromUtf8(it->command().c_str());
        QString tabName = categorizeToolbar(tbName);

        if (!tabMap.contains(tabName)) {
            tabOrder.append(tabName);
        }
        tabMap[tabName].append(it);
    }

    // Create ribbon tabs and panels
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

QString RibbonBar::categorizeToolbar(const QString& tbName) const
{
    // Inventor-style tab grouping
    if (tbName == QStringLiteral("File")
        || tbName == QStringLiteral("Edit")
        || tbName == QStringLiteral("Clipboard")
        || tbName == QStringLiteral("Macro")
        || tbName == QStringLiteral("Structure")
        || tbName == QStringLiteral("Help")) {
        return tr("Home");
    }
    if (tbName == QStringLiteral("View")
        || tbName == QStringLiteral("Navigation")
        || tbName == QStringLiteral("Individual views")) {
        return tr("View");
    }
    if (tbName.contains(QStringLiteral("Sketch"), Qt::CaseInsensitive)) {
        return tr("Sketch");
    }
    if (tbName.contains(QStringLiteral("Part Design"), Qt::CaseInsensitive)
        || tbName.contains(QStringLiteral("PartDesign"), Qt::CaseInsensitive)) {
        return tr("Design");
    }
    if (tbName.contains(QStringLiteral("Part"), Qt::CaseInsensitive)
        && !tbName.contains(QStringLiteral("Design"), Qt::CaseInsensitive)) {
        return tr("Part");
    }
    if (tbName.contains(QStringLiteral("Assembly"), Qt::CaseInsensitive)) {
        return tr("Assembly");
    }
    if (tbName.contains(QStringLiteral("Mesh"), Qt::CaseInsensitive)
        || tbName.contains(QStringLiteral("FEM"), Qt::CaseInsensitive)) {
        return tr("Analysis");
    }
    if (tbName.contains(QStringLiteral("Drawing"), Qt::CaseInsensitive)
        || tbName.contains(QStringLiteral("TechDraw"), Qt::CaseInsensitive)) {
        return tr("Drawing");
    }
    if (tbName.contains(QStringLiteral("CAM"), Qt::CaseInsensitive)
        || tbName.contains(QStringLiteral("Path"), Qt::CaseInsensitive)) {
        return tr("Manufacturing");
    }
    if (tbName.contains(QStringLiteral("FlowStudio"), Qt::CaseInsensitive)
        || tbName.contains(QStringLiteral("CFD"), Qt::CaseInsensitive)) {
        return tr("Simulation");
    }

    return tr("Tools");
}

void RibbonBar::clear()
{
    tabWidget->clear();
    tabPages.clear();
}

RibbonPanel* RibbonBar::createPanel(const QString& name, ToolBarItem* toolbarItem)
{
    QByteArray tbNameBytes = name.toUtf8();
    QString displayName = QApplication::translate("Workbench", tbNameBytes.constData());

    auto* panel = new RibbonPanel(displayName);

    QList<ToolBarItem*> commands = toolbarItem->getItems();

    // Inventor-style heuristic:
    // - Commands with menus/dropdowns → Large
    // - First 3 non-separator commands → Large (primary actions)
    // - Everything else → Small (stacked in rows of 3)
    int primaryCount = 0;
    constexpr int primaryLimit = 3;

    for (ToolBarItem* cmdItem : commands) {
        QString cmdName = QString::fromLatin1(cmdItem->command().c_str());

        if (cmdName == QStringLiteral("Separator")) {
            panel->addSeparator();
            continue;
        }

        RibbonButton* btn = createButton(cmdName);
        if (!btn) {
            continue;
        }

        // Determine sizing
        bool hasMenu = (btn->menu() || btn->popupMode() != QToolButton::DelayedPopup);
        bool isPrimary = (primaryCount < primaryLimit);
        RibbonButton::ButtonSize size = (hasMenu || isPrimary)
            ? RibbonButton::Large
            : RibbonButton::Small;

        btn->setButtonSize(size);
        panel->addButton(btn);
        ++primaryCount;
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
