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
#include <QVariantAnimation>
#include <QMenu>
#include <QMouseEvent>
#include <QPainterPath>
#include <QLinearGradient>
#include <QKeyEvent>
#include <QToolBar>
#include <QStringList>
#include <QTabBar>

#include <App/Application.h>
#include <Base/Parameter.h>

#include "RibbonBar.h"
#include "Action.h"
#include "ToolBarManager.h"
#include "Application.h"
#include "Command.h"
#include "BitmapFactory.h"
#include "BackstageView.h"
#include "CommandSearch.h"
#include "Document.h"
#include "MainWindow.h"
#include "RibbonGallery.h"
#include "RibbonKeyTip.h"
#include "ViewProviderDocumentObject.h"
#include "WorkbenchManager.h"


using namespace Gui;

RibbonBar* RibbonBar::_instance = nullptr;

// ============================================================================
// Ribbon style constants — Inventor-style dimensions
// ============================================================================

namespace {
    constexpr int LargeIconSize      = 28;
    constexpr int SmallIconSize      = 16;
    constexpr int QATIconSize        = 16;
    constexpr int LargeButtonWidth   = 92;
    constexpr int LargeButtonHeight  = 70;
    constexpr int SmallButtonWidth   = 116;
    constexpr int SmallButtonHeight  = 24;
    constexpr int PanelMinWidth      = 78;
    constexpr int RibbonHeight       = 132;
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
        int textWidth = 0;
        const QStringList lines = text().split(QChar::fromLatin1('\n'));
        for (const QString& line : lines) {
            textWidth = qMax(textWidth, fm.horizontalAdvance(line));
        }
        textWidth += 16;
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

void RibbonPanel::addCustomWidget(QWidget* widget)
{
    if (!widget) {
        return;
    }

    widget->setParent(buttonArea);
    customWidgets.append(widget);
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

    if (buttons.isEmpty() && customWidgets.isEmpty()) {
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
                currentSmallColumn->setSpacing(SmallColumnSpacing);
                hLayout->addLayout(currentSmallColumn);
                smallInColumn = 0;
            }
            currentSmallColumn->addWidget(btn);
            ++smallInColumn;
        }
    }

    // Custom widgets (e.g. RibbonGallery) are appended as their own columns.
    for (auto* widget : customWidgets) {
        if (!widget) {
            continue;
        }

        if (currentSmallColumn) {
            currentSmallColumn->addStretch();
            currentSmallColumn = nullptr;
            smallInColumn = 0;
        }

        widget->setSizePolicy(QSizePolicy::Preferred, QSizePolicy::Fixed);
        hLayout->addWidget(widget);
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
    scrollArea->setWidgetResizable(false);
    scrollArea->setHorizontalScrollBarPolicy(Qt::ScrollBarAsNeeded);
    scrollArea->setVerticalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
    scrollArea->setFrameStyle(QFrame::NoFrame);
    scrollArea->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed);

    scrollContent = new QWidget(scrollArea);
    scrollContent->setSizePolicy(QSizePolicy::Minimum, QSizePolicy::Fixed);
    panelLayout = new QHBoxLayout(scrollContent);
    panelLayout->setContentsMargins(4, 0, 4, 0);
    panelLayout->setSpacing(6);
    panelLayout->addStretch(1);
    scrollContent->setLayout(panelLayout);
    scrollContent->adjustSize();

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
    scrollContent->adjustSize();
}

void RibbonTabPage::clearPanels()
{
    for (auto* panel : std::as_const(panelList)) {
        panelLayout->removeWidget(panel);
        delete panel;
    }
    panelList.clear();
    scrollContent->adjustSize();
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

    // Top row: quick access toolbar on the left, command search on the right.
    auto* topRow = new QWidget(this);
    auto* topRowLayout = new QHBoxLayout(topRow);
    topRowLayout->setContentsMargins(0, 0, 0, 0);
    topRowLayout->setSpacing(8);

    qatBar = new QuickAccessToolBar(topRow);
    topRowLayout->addWidget(qatBar, 1);

    searchField = new QLineEdit(topRow);
    searchField->setObjectName(QStringLiteral("ribbonCommandSearch"));
    searchField->setClearButtonEnabled(true);
    searchField->setFixedHeight(QATBarHeight - 4);
    searchField->setMinimumWidth(220);
    searchField->setMaximumWidth(320);
    searchField->setPlaceholderText(tr("Search commands"));
    searchField->addAction(BitmapFactory().iconFromTheme("edit-find"), QLineEdit::LeadingPosition);
    topRowLayout->addWidget(searchField, 0, Qt::AlignRight | Qt::AlignVCenter);

    minimizeButton = new QToolButton(topRow);
    minimizeButton->setAutoRaise(true);
    minimizeButton->setFixedSize(QATBarHeight - 4, QATBarHeight - 4);
    minimizeButton->setToolButtonStyle(Qt::ToolButtonTextOnly);
    topRowLayout->addWidget(minimizeButton, 0, Qt::AlignRight | Qt::AlignVCenter);

    ribbonStateBadge = new QLabel(topRow);
    ribbonStateBadge->setObjectName(QStringLiteral("ribbonStateBadge"));
    ribbonStateBadge->setAlignment(Qt::AlignCenter);
    ribbonStateBadge->setMinimumWidth(58);
    ribbonStateBadge->setFixedHeight(QATBarHeight - 6);
    ribbonStateBadge->setStyleSheet(QStringLiteral(
        "QLabel#ribbonStateBadge {"
        "  border: 1px solid palette(mid);"
        "  border-radius: 7px;"
        "  padding: 0 6px;"
        "  color: palette(window-text);"
        "  background: palette(base);"
        "  font-size: 9px;"
        "  font-weight: 600;"
        "}"
    ));
    topRowLayout->addWidget(ribbonStateBadge, 0, Qt::AlignRight | Qt::AlignVCenter);

    mainLayout->addWidget(topRow);

    // Tab widget for ribbon panels
    tabWidget = new QTabWidget(this);
    tabWidget->setTabPosition(QTabWidget::North);
    tabWidget->setDocumentMode(false);
    tabWidget->setUsesScrollButtons(true);
    tabWidget->setElideMode(Qt::ElideNone);

    mainLayout->addWidget(tabWidget, 1);
    setLayout(mainLayout);

    auto hGrp = App::GetApplication()
        .GetUserParameter()
        .GetGroup("BaseApp")
        ->GetGroup("Preferences")
        ->GetGroup("MainWindow");
    ribbonMinimized = hGrp->GetBool("RibbonMinimized", false);

    applyMinimizedState(false);
    setupStyle();
    updateMinimizeAffordance();

    keyTipOverlay = new RibbonKeyTip(this);

    qApp->installEventFilter(this);

    connect(tabWidget->tabBar(), &QTabBar::tabBarDoubleClicked, this, [this](int) {
        toggleMinimized();
    });
    connect(tabWidget->tabBar(), &QTabBar::tabBarClicked, this, [this](int index) {
        if (index == fileTabIndex) {
            openBackstage();
            return;
        }
        if (!ribbonMinimized || index < 0) {
            if (index >= 0) {
                lastContentTabIndex = index;
            }
            return;
        }
        if (previewExpandedWhileMinimized && tabWidget->currentIndex() == index) {
            collapseMinimizedPreview();
            return;
        }
        showMinimizedPreview();
    });
    connect(tabWidget, &QTabWidget::currentChanged, this, [this](int index) {
        if (index == fileTabIndex) {
            openBackstage();
            return;
        }
        if (index >= 0) {
            lastContentTabIndex = index;
        }
    });
    connect(minimizeButton, &QToolButton::clicked, this, [this]() {
        toggleMinimized();
    });

    ribbonHeightAnimation = new QVariantAnimation(this);
    ribbonHeightAnimation->setDuration(130);
    ribbonHeightAnimation->setEasingCurve(QEasingCurve::InOutCubic);
    connect(ribbonHeightAnimation, &QVariantAnimation::valueChanged, this, [this](const QVariant& v) {
        setFixedHeight(v.toInt());
        updateGeometry();
    });
    connect(ribbonHeightAnimation, &QVariantAnimation::finished, this, [this]() {
        finalizeMinimizedLayout(pendingShowPanelArea);
    });

    connect(searchField, &QLineEdit::returnPressed, this, [this]() {
        CommandSearch::openPalette(this, searchField->text());
        searchField->clear();
    });
    connect(searchField, &QLineEdit::selectionChanged, this, [this]() {
        if (searchField->hasFocus() && !searchField->selectedText().isEmpty()) {
            searchField->deselect();
        }
    });

    if (auto* mainWindow = getMainWindow()) {
        connect(mainWindow, &MainWindow::workbenchActivated, this, [this](const QString&) {
            refreshContextualTabs();
        });
    }

    inEditConnection = Application::Instance->signalInEdit.connect([this](const ViewProviderDocumentObject&) {
        refreshContextualTabs();
    });
    resetEditConnection
        = Application::Instance->signalResetEdit.connect([this](const ViewProviderDocumentObject&) {
              refreshContextualTabs();
          });
}

RibbonBar::~RibbonBar()
{
    qApp->removeEventFilter(this);

    if (_instance == this) {
        _instance = nullptr;
    }
}

RibbonBar* RibbonBar::instance()
{
    return _instance;
}

void RibbonBar::setMinimized(bool minimized)
{
    if (ribbonMinimized == minimized) {
        return;
    }

    ribbonMinimized = minimized;
    previewExpandedWhileMinimized = false;

    auto hGrp = App::GetApplication()
        .GetUserParameter()
        .GetGroup("BaseApp")
        ->GetGroup("Preferences")
        ->GetGroup("MainWindow");
    hGrp->SetBool("RibbonMinimized", ribbonMinimized);

    applyMinimizedState();
    updateMinimizeAffordance();
    Q_EMIT ribbonVisibilityChanged(!ribbonMinimized);
}

void RibbonBar::applyMinimizedState(bool animated)
{
    if (!tabWidget) {
        return;
    }

    const bool showPanelArea = !ribbonMinimized || previewExpandedWhileMinimized;
    pendingShowPanelArea = showPanelArea;

    // Keep content unconstrained while animating to avoid jump cuts.
    tabWidget->setMinimumHeight(0);
    tabWidget->setMaximumHeight(QWIDGETSIZE_MAX);

    const int targetHeight = showPanelArea
        ? (RibbonHeight + QATBarHeight)
        : (QATBarHeight + TabBarHeight + 8);

    if (!animated || !ribbonHeightAnimation) {
        setFixedHeight(targetHeight);
        finalizeMinimizedLayout(showPanelArea);
        updateGeometry();
        return;
    }

    if (ribbonHeightAnimation->state() == QVariantAnimation::Running) {
        ribbonHeightAnimation->stop();
    }

    ribbonHeightAnimation->setStartValue(height());
    ribbonHeightAnimation->setEndValue(targetHeight);
    ribbonHeightAnimation->start();
}

void RibbonBar::finalizeMinimizedLayout(bool showPanelArea)
{
    if (!tabWidget) {
        return;
    }

    if (showPanelArea) {
        tabWidget->setMinimumHeight(0);
        tabWidget->setMaximumHeight(QWIDGETSIZE_MAX);
        setFixedHeight(RibbonHeight + QATBarHeight);
    }
    else {
        tabWidget->setMinimumHeight(TabBarHeight + 6);
        tabWidget->setMaximumHeight(TabBarHeight + 6);
        setFixedHeight(QATBarHeight + TabBarHeight + 8);
    }

    updateGeometry();
}

void RibbonBar::updateMinimizeAffordance()
{
    if (!minimizeButton || !tabWidget || !ribbonStateBadge) {
        return;
    }

    if (ribbonMinimized) {
        minimizeButton->setText(QStringLiteral("▾"));
        if (previewExpandedWhileMinimized) {
            minimizeButton->setToolTip(tr("Collapse ribbon preview"));
            ribbonStateBadge->setText(tr("Preview"));
            ribbonStateBadge->setToolTip(tr("Temporary ribbon preview is open."));
        }
        else {
            minimizeButton->setToolTip(tr("Expand ribbon (double-click a tab to pin open)"));
            ribbonStateBadge->setText(tr("Auto-hide"));
            ribbonStateBadge->setToolTip(tr("Ribbon is minimized and will auto-hide."));
        }
        tabWidget->tabBar()->setToolTip(
            tr("Ribbon is minimized. Click a tab to preview, click outside to collapse.")
        );
    }
    else {
        minimizeButton->setText(QStringLiteral("▴"));
        minimizeButton->setToolTip(tr("Minimize ribbon"));
        ribbonStateBadge->setText(tr("Pinned"));
        ribbonStateBadge->setToolTip(tr("Ribbon is pinned open."));
        tabWidget->tabBar()->setToolTip(tr("Double-click a tab to minimize ribbon."));
    }
}

void RibbonBar::showMinimizedPreview()
{
    if (!ribbonMinimized || previewExpandedWhileMinimized) {
        return;
    }

    previewExpandedWhileMinimized = true;
    applyMinimizedState();
    updateMinimizeAffordance();
    Q_EMIT ribbonVisibilityChanged(true);
}

void RibbonBar::collapseMinimizedPreview()
{
    if (!previewExpandedWhileMinimized) {
        return;
    }

    previewExpandedWhileMinimized = false;
    applyMinimizedState();
    updateMinimizeAffordance();
    Q_EMIT ribbonVisibilityChanged(false);
}

bool RibbonBar::eventFilter(QObject* watched, QEvent* event)
{
    Q_UNUSED(watched)

    if (!previewExpandedWhileMinimized) {
        return QWidget::eventFilter(watched, event);
    }

    if (event->type() == QEvent::MouseButtonPress) {
        auto* mouseEvent = static_cast<QMouseEvent*>(event);
#if QT_VERSION >= QT_VERSION_CHECK(6, 0, 0)
        const QPoint globalPos = mouseEvent->globalPosition().toPoint();
#else
        const QPoint globalPos = mouseEvent->globalPos();
#endif
        if (!rect().contains(mapFromGlobal(globalPos))) {
            collapseMinimizedPreview();
        }
    }
    else if (event->type() == QEvent::KeyPress) {
        auto* keyEvent = static_cast<QKeyEvent*>(event);
        if (keyEvent->key() == Qt::Key_Escape) {
            collapseMinimizedPreview();
        }
    }

    return QWidget::eventFilter(watched, event);
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
        "  background: #1a3a5c;"
        "  color: white;"
        "  border-color: #1a3a5c;"
        "  padding-left: 16px;"
        "  padding-right: 16px;"
        "}"
        "QTabBar::tab:first:hover {"
        "  background: #2a5a8c;"
        "  border-color: #2a5a8c;"
        "}"
        "QTabBar::tab:first:selected {"
        "  background: #2a5a8c;"
        "  border-color: #2a5a8c;"
        "}"
        "QLineEdit#ribbonCommandSearch {"
        "  padding: 2px 8px;"
        "  border: 1px solid palette(mid);"
        "  border-radius: 10px;"
        "  background: palette(base);"
        "}"
        "QLineEdit#ribbonCommandSearch:focus {"
        "  border: 1px solid palette(highlight);"
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

    auto* filePage = new RibbonTabPage(tabWidget);
    fileTabIndex = tabWidget->addTab(filePage, tr("File"));
    tabWidget->setTabToolTip(fileTabIndex, tr("Open Backstage view"));
    auto fileTabIcon = BitmapFactory().iconFromTheme("document-open");
    if (!fileTabIcon.isNull()) {
        tabWidget->setTabIcon(fileTabIndex, fileTabIcon);
    }
    tabWidget->tabBar()->setTabTextColor(fileTabIndex, QColor(255, 255, 255));

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

    if (tabWidget->count() > 1) {
        lastContentTabIndex = 1;
        tabWidget->setCurrentIndex(lastContentTabIndex);
    }

    refreshContextualTabs();
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
    const QStringList contextualNames = contextualTabs.keys();
    for (const QString& name : contextualNames) {
        removeContextualTab(name);
    }
    tabWidget->clear();
    tabPages.clear();
    fileTabIndex = -1;
    lastContentTabIndex = -1;
}

void RibbonBar::openBackstage()
{
    auto* backstage = BackstageView::instance();
    if (!backstage) {
        return;
    }

    backstage->navigateTo(tr("New"));
    backstage->show();
    backstage->raise();
    backstage->activateWindow();

    const int fallbackIndex = (lastContentTabIndex >= 0 && lastContentTabIndex < tabWidget->count()
                               && lastContentTabIndex != fileTabIndex)
        ? lastContentTabIndex
        : (tabWidget->count() > 1 ? 1 : -1);
    if (fallbackIndex >= 0 && tabWidget->currentIndex() != fallbackIndex) {
        tabWidget->setCurrentIndex(fallbackIndex);
    }
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

RibbonPanel* RibbonBar::createContextPanel(const QString& title, const QStringList& commandNames)
{
    auto* panel = new RibbonPanel(title);
    for (const QString& commandName : commandNames) {
        if (commandName == QStringLiteral("Separator")) {
            panel->addSeparator();
            continue;
        }

        if (auto* button = createButton(commandName)) {
            panel->addButton(button);
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

void RibbonBar::refreshContextualTabs()
{
    if (!tabWidget) {
        return;
    }

    Gui::Document* activeDoc = Application::Instance->activeDocument();
    ViewProviderDocumentObject* editVp = nullptr;
    if (activeDoc) {
        editVp = dynamic_cast<ViewProviderDocumentObject*>(activeDoc->getInEdit());
    }

    const QString activeWorkbench
        = QString::fromStdString(WorkbenchManager::instance()->activeName());

    const QStringList contextualNames = contextualTabs.keys();
    for (const QString& name : contextualNames) {
        removeContextualTab(name);
    }

    if (shouldShowSketchContext(activeWorkbench, editVp)) {
        auto* page = showContextualTab(tr("Sketch"), QColor(217, 110, 43), editVp != nullptr);
        populateSketchContextualTab(page);
    }

    if (shouldShowAssemblyContext(activeWorkbench, editVp)) {
        auto* page = showContextualTab(tr("Assembly"), QColor(42, 124, 176), editVp != nullptr);
        populateAssemblyContextualTab(page);
    }
}

void RibbonBar::populateSketchContextualTab(RibbonTabPage* page)
{
    if (!page) {
        return;
    }

    page->clearPanels();

    auto* sketchPanel = createContextPanel(
        tr("Sketch"),
        {
            QStringLiteral("Sketcher_NewSketch"),
            QStringLiteral("Sketcher_EditSketch"),
            QStringLiteral("Sketcher_ValidateSketch"),
            QStringLiteral("Sketcher_LeaveSketch"),
        }
    );
    if (sketchPanel->buttonCount() > 0) {
        page->addPanel(sketchPanel);
    }
    else {
        delete sketchPanel;
    }

    auto* geometryPanel = createContextPanel(
        tr("Geometry"),
        {
            QStringLiteral("Sketcher_CreateLine"),
            QStringLiteral("Sketcher_CreateCircle"),
            QStringLiteral("Sketcher_CreateArc"),
            QStringLiteral("Sketcher_CreateRectangle"),
            QStringLiteral("Sketcher_CreatePoint"),
            QStringLiteral("Sketcher_ToggleConstruction"),
        }
    );
    if (geometryPanel->buttonCount() > 0) {
        page->addPanel(geometryPanel);
    }
    else {
        delete geometryPanel;
    }

    auto* constraintsPanel = createContextPanel(
        tr("Constraints"),
        {
            QStringLiteral("Sketcher_ConstrainCoincidentUnified"),
            QStringLiteral("Sketcher_ConstrainHorizontal"),
            QStringLiteral("Sketcher_ConstrainVertical"),
            QStringLiteral("Sketcher_ConstrainParallel"),
            QStringLiteral("Sketcher_ConstrainPerpendicular"),
            QStringLiteral("Sketcher_Dimension"),
            QStringLiteral("Sketcher_ConstrainDistance"),
            QStringLiteral("Sketcher_ConstrainAngle"),
        }
    );
    if (constraintsPanel->buttonCount() > 0) {
        page->addPanel(constraintsPanel);
    }
    else {
        delete constraintsPanel;
    }

    auto* smartDimPanel = new RibbonPanel(tr("Smart Dimension"));
    auto* gallery = new RibbonGallery(smartDimPanel);
    gallery->setThumbnailSize(QSize(26, 26));
    gallery->setVisibleColumns(4);
    gallery->setVisibleRows(1);

    auto addGalleryCommand = [gallery](const QString& cmdName) {
        CommandManager& mgr = Application::Instance->commandManager();
        Command* cmd = mgr.getCommandByName(cmdName.toLatin1().constData());
        if (!cmd) {
            return;
        }

        const char* menuText = cmd->getMenuText();
        QString label = menuText && menuText[0]
            ? QApplication::translate(cmd->className(), menuText)
            : cmdName;
        label.remove(QLatin1Char('&'));

        QIcon icon;
        const char* pixmapName = cmd->getPixmap();
        if (pixmapName && pixmapName[0]) {
            icon = BitmapFactory().iconFromTheme(pixmapName);
            if (icon.isNull()) {
                QPixmap pm = BitmapFactory().pixmap(pixmapName);
                if (!pm.isNull()) {
                    icon = QIcon(pm);
                }
            }
        }

        gallery->addItem(RibbonGalleryItem(cmdName, icon, label, label));
    };

    gallery->addCategory(tr("Dimensions"));
    addGalleryCommand(QStringLiteral("Sketcher_Dimension"));
    addGalleryCommand(QStringLiteral("Sketcher_ConstrainDistance"));
    addGalleryCommand(QStringLiteral("Sketcher_ConstrainDistanceX"));
    addGalleryCommand(QStringLiteral("Sketcher_ConstrainDistanceY"));
    addGalleryCommand(QStringLiteral("Sketcher_ConstrainAngle"));
    addGalleryCommand(QStringLiteral("Sketcher_ConstrainRadius"));
    addGalleryCommand(QStringLiteral("Sketcher_ConstrainDiameter"));

    connect(gallery, &RibbonGallery::itemActivated, this, [](const QString& cmdName) {
        if (cmdName.isEmpty()) {
            return;
        }
        CommandManager& mgr = Application::Instance->commandManager();
        mgr.runCommandByName(cmdName.toLatin1().constData());
    });

    if (gallery->itemCount() > 0) {
        smartDimPanel->addCustomWidget(gallery);
        page->addPanel(smartDimPanel);
    }
    else {
        delete smartDimPanel;
    }
}

void RibbonBar::populateAssemblyContextualTab(RibbonTabPage* page)
{
    if (!page) {
        return;
    }

    page->clearPanels();

    auto* assemblyPanel = createContextPanel(
        tr("Assembly"),
        {
            QStringLiteral("Assembly_CreateAssembly"),
            QStringLiteral("Assembly_ActivateAssembly"),
            QStringLiteral("Assembly_InsertLink"),
            QStringLiteral("Assembly_CreateBom"),
        }
    );
    if (assemblyPanel->buttonCount() > 0) {
        page->addPanel(assemblyPanel);
    }
    else {
        delete assemblyPanel;
    }

    auto* jointsPanel = createContextPanel(
        tr("Joints"),
        {
            QStringLiteral("Assembly_CreateJointFixed"),
            QStringLiteral("Assembly_CreateJointRevolute"),
            QStringLiteral("Assembly_CreateJointSlider"),
            QStringLiteral("Assembly_CreateJointCylindrical"),
            QStringLiteral("Assembly_CreateJointBall"),
            QStringLiteral("Assembly_CreateJointDistance"),
        }
    );
    if (jointsPanel->buttonCount() > 0) {
        page->addPanel(jointsPanel);
    }
    else {
        delete jointsPanel;
    }

    auto* solvePanel = createContextPanel(
        tr("Solve"),
        {
            QStringLiteral("Assembly_ToggleGrounded"),
            QStringLiteral("Assembly_CreateJointParallel"),
            QStringLiteral("Assembly_CreateJointPerpendicular"),
            QStringLiteral("Assembly_CreateJointAngle"),
        }
    );
    if (solvePanel->buttonCount() > 0) {
        page->addPanel(solvePanel);
    }
    else {
        delete solvePanel;
    }

    auto* jointPresetPanel = new RibbonPanel(tr("Joint Presets"));
    auto* gallery = new RibbonGallery(jointPresetPanel);
    gallery->setThumbnailSize(QSize(26, 26));
    gallery->setVisibleColumns(5);
    gallery->setVisibleRows(1);

    auto addGalleryCommand = [gallery](const QString& cmdName) {
        CommandManager& mgr = Application::Instance->commandManager();
        Command* cmd = mgr.getCommandByName(cmdName.toLatin1().constData());
        if (!cmd) {
            return;
        }

        const char* menuText = cmd->getMenuText();
        QString label = menuText && menuText[0]
            ? QApplication::translate(cmd->className(), menuText)
            : cmdName;
        label.remove(QLatin1Char('&'));

        QIcon icon;
        const char* pixmapName = cmd->getPixmap();
        if (pixmapName && pixmapName[0]) {
            icon = BitmapFactory().iconFromTheme(pixmapName);
            if (icon.isNull()) {
                QPixmap pm = BitmapFactory().pixmap(pixmapName);
                if (!pm.isNull()) {
                    icon = QIcon(pm);
                }
            }
        }

        gallery->addItem(RibbonGalleryItem(cmdName, icon, label, label));
    };

    gallery->addCategory(tr("Primary Joints"));
    addGalleryCommand(QStringLiteral("Assembly_CreateJointFixed"));
    addGalleryCommand(QStringLiteral("Assembly_CreateJointRevolute"));
    addGalleryCommand(QStringLiteral("Assembly_CreateJointSlider"));
    addGalleryCommand(QStringLiteral("Assembly_CreateJointCylindrical"));
    addGalleryCommand(QStringLiteral("Assembly_CreateJointBall"));
    addGalleryCommand(QStringLiteral("Assembly_CreateJointDistance"));

    gallery->addCategory(tr("Auxiliary Joints"));
    addGalleryCommand(QStringLiteral("Assembly_CreateJointParallel"));
    addGalleryCommand(QStringLiteral("Assembly_CreateJointPerpendicular"));
    addGalleryCommand(QStringLiteral("Assembly_CreateJointAngle"));

    connect(gallery, &RibbonGallery::itemActivated, this, [](const QString& cmdName) {
        if (cmdName.isEmpty()) {
            return;
        }
        CommandManager& mgr = Application::Instance->commandManager();
        mgr.runCommandByName(cmdName.toLatin1().constData());
    });

    if (gallery->itemCount() > 0) {
        jointPresetPanel->addCustomWidget(gallery);
        page->addPanel(jointPresetPanel);
    }
    else {
        delete jointPresetPanel;
    }
}

bool RibbonBar::shouldShowSketchContext(const QString& activeWorkbench,
                                        const ViewProviderDocumentObject* editViewProvider) const
{
    if (activeWorkbench.contains(QStringLiteral("Sketch"), Qt::CaseInsensitive)) {
        return true;
    }
    if (!editViewProvider || !editViewProvider->getObject()) {
        return false;
    }

    const QString typeName = QString::fromLatin1(editViewProvider->getObject()->getTypeId().getName());
    return typeName.contains(QStringLiteral("Sketch"), Qt::CaseInsensitive);
}

bool RibbonBar::shouldShowAssemblyContext(const QString& activeWorkbench,
                                          const ViewProviderDocumentObject* editViewProvider) const
{
    if (activeWorkbench.contains(QStringLiteral("Assembly"), Qt::CaseInsensitive)) {
        return true;
    }
    if (!editViewProvider || !editViewProvider->getObject()) {
        return false;
    }

    const QString typeName = QString::fromLatin1(editViewProvider->getObject()->getTypeId().getName());
    return typeName.contains(QStringLiteral("Assembly"), Qt::CaseInsensitive);
}

// ============================================================================
// Contextual Tab API
// ============================================================================

RibbonTabPage* RibbonBar::showContextualTab(const QString& name,
                                             const QColor& accentColor,
                                             bool activate)
{
    auto it = contextualTabs.find(name);

    if (it != contextualTabs.end()) {
        // Tab already exists — if currently hidden, re-insert it
        auto& info = it.value();
        if (info.tabIndex < 0 && info.page) {
            info.tabIndex = tabWidget->addTab(info.page, name);
            if (accentColor.isValid()) {
                info.accentColor = accentColor;
            }
            if (info.accentColor.isValid()) {
                tabWidget->tabBar()->setTabTextColor(info.tabIndex, info.accentColor);
            }
        }
        if (activate && info.tabIndex >= 0) {
            tabWidget->setCurrentIndex(info.tabIndex);
        }
        Q_EMIT contextualTabShown(name);
        return info.page;
    }

    // Create new contextual tab
    ContextualTabInfo info;
    info.page = new RibbonTabPage(tabWidget);
    info.accentColor = accentColor.isValid() ? accentColor : QColor(0, 120, 215);
    info.tabIndex = tabWidget->addTab(info.page, name);

    if (info.accentColor.isValid()) {
        tabWidget->tabBar()->setTabTextColor(info.tabIndex, info.accentColor);
    }

    contextualTabs.insert(name, info);

    if (activate) {
        tabWidget->setCurrentIndex(info.tabIndex);
    }

    Q_EMIT contextualTabShown(name);
    return info.page;
}

void RibbonBar::hideContextualTab(const QString& name)
{
    auto it = contextualTabs.find(name);
    if (it == contextualTabs.end()) {
        return;
    }
    auto& info = it.value();
    if (info.tabIndex >= 0) {
        tabWidget->removeTab(info.tabIndex);
        info.tabIndex = -1;
        // Re-sync all contextual tab indices after removal
        for (auto ctIt = contextualTabs.begin(); ctIt != contextualTabs.end(); ++ctIt) {
            if (ctIt.value().page && ctIt.value().tabIndex >= 0) {
                ctIt.value().tabIndex = tabWidget->indexOf(ctIt.value().page);
            }
        }
    }
    Q_EMIT contextualTabHidden(name);
}

void RibbonBar::removeContextualTab(const QString& name)
{
    auto it = contextualTabs.find(name);
    if (it == contextualTabs.end()) {
        return;
    }
    auto& info = it.value();
    if (info.tabIndex >= 0) {
        tabWidget->removeTab(info.tabIndex);
    }
    delete info.page;
    contextualTabs.erase(it);

    // Re-sync remaining contextual tab indices
    for (auto ctIt = contextualTabs.begin(); ctIt != contextualTabs.end(); ++ctIt) {
        if (ctIt.value().page && ctIt.value().tabIndex >= 0) {
            ctIt.value().tabIndex = tabWidget->indexOf(ctIt.value().page);
        }
    }
    Q_EMIT contextualTabHidden(name);
}

bool RibbonBar::isContextualTabVisible(const QString& name) const
{
    auto it = contextualTabs.find(name);
    if (it == contextualTabs.end()) {
        return false;
    }
    return it.value().tabIndex >= 0;
}
