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
#include <QMetaObject>
#include <QPointer>
#include <QSignalBlocker>
#include <QSet>
#include <QToolBar>
#include <QStringList>
#include <QTabBar>
#include <algorithm>
#include <limits>

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
#include "Selection/Selection.h"
#include "ViewProviderDocumentObject.h"
#include "WorkbenchManager.h"


using namespace Gui;

RibbonBar* RibbonBar::_instance = nullptr;

namespace {
QMap<QString, QStringList> g_registeredRibbonPanels;
QMap<QString, QStringList> g_registeredContextualRibbonPanels;
}

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
    constexpr int MaxHomePanels      = 3;
    constexpr int DefaultRibbonPanelOrder = std::numeric_limits<int>::max();
    const auto RibbonMetadataPrefix  = QStringLiteral("Ribbon::");
    const auto RibbonContextMetadataPrefix = QStringLiteral("RibbonContext::");

    struct RibbonToolbarMetadata {
        QString tabName;
        QString panelName;
        bool promoteToHome = false;
        int homePriority = 1;
        int order = DefaultRibbonPanelOrder;

        [[nodiscard]] bool isValid() const
        {
            return !tabName.isEmpty() && !panelName.isEmpty();
        }
    };

    struct RibbonContextualToolbarMetadata {
        QString tabName;
        QString panelName;
        QString workbenchName;
        QStringList typeKeywords;
        QColor accentColor;
        int order = DefaultRibbonPanelOrder;

        [[nodiscard]] bool isValid() const
        {
            return !tabName.isEmpty() && !panelName.isEmpty();
        }
    };

    RibbonToolbarMetadata parseRibbonToolbarMetadata(const QString& toolbarName)
    {
        if (!toolbarName.startsWith(RibbonMetadataPrefix)) {
            return {};
        }

        const QStringList parts = toolbarName.split(QStringLiteral("::"), Qt::KeepEmptyParts);
        if (parts.size() < 3) {
            return {};
        }

        RibbonToolbarMetadata metadata;
        metadata.tabName = parts.at(1).trimmed();
        metadata.panelName = parts.at(2).trimmed();
        for (int index = 3; index < parts.size(); ++index) {
            const QString flag = parts.at(index).trimmed();
            if (flag.compare(QStringLiteral("Home"), Qt::CaseInsensitive) == 0) {
                metadata.promoteToHome = true;
                metadata.homePriority = 1;
            }
            else if (flag.compare(QStringLiteral("HomePrimary"), Qt::CaseInsensitive) == 0) {
                metadata.promoteToHome = true;
                metadata.homePriority = 0;
            }
            else if (flag.compare(QStringLiteral("HomeSecondary"), Qt::CaseInsensitive) == 0) {
                metadata.promoteToHome = true;
                metadata.homePriority = 1;
            }
            else if (flag.startsWith(QStringLiteral("Order="), Qt::CaseInsensitive)) {
                bool ok = false;
                int parsedOrder = flag.mid(QStringLiteral("Order=").size()).toInt(&ok);
                if (ok) {
                    metadata.order = parsedOrder;
                }
            }
        }
        return metadata;
    }

    RibbonContextualToolbarMetadata parseRibbonContextualToolbarMetadata(const QString& toolbarName)
    {
        if (!toolbarName.startsWith(RibbonContextMetadataPrefix)) {
            return {};
        }

        const QStringList parts = toolbarName.split(QStringLiteral("::"), Qt::KeepEmptyParts);
        if (parts.size() < 3) {
            return {};
        }

        RibbonContextualToolbarMetadata metadata;
        metadata.tabName = parts.at(1).trimmed();
        metadata.panelName = parts.at(2).trimmed();
        for (int index = 3; index < parts.size(); ++index) {
            const QString flag = parts.at(index).trimmed();
            if (flag.startsWith(QStringLiteral("Order="), Qt::CaseInsensitive)) {
                bool ok = false;
                int parsedOrder = flag.mid(QStringLiteral("Order=").size()).toInt(&ok);
                if (ok) {
                    metadata.order = parsedOrder;
                }
            }
            else if (flag.startsWith(QStringLiteral("Workbench="), Qt::CaseInsensitive)) {
                metadata.workbenchName = flag.mid(QStringLiteral("Workbench=").size()).trimmed();
            }
            else if (flag.startsWith(QStringLiteral("Types="), Qt::CaseInsensitive)) {
                const QStringList keywords = flag.mid(QStringLiteral("Types=").size())
                                                 .split(QStringLiteral(","), Qt::SkipEmptyParts);
                for (const QString& keyword : keywords) {
                    metadata.typeKeywords.append(keyword.trimmed());
                }
            }
            else if (flag.startsWith(QStringLiteral("Color="), Qt::CaseInsensitive)) {
                const QColor color(flag.mid(QStringLiteral("Color=").size()).trimmed());
                if (color.isValid()) {
                    metadata.accentColor = color;
                }
            }
        }

        return metadata;
    }

    bool matchesContextualToolbar(const RibbonContextualToolbarMetadata& metadata,
                                  const QString& activeWorkbench,
                                  const ViewProviderDocumentObject* editViewProvider)
    {
        if (!metadata.isValid() || !editViewProvider || !editViewProvider->getObject()) {
            return false;
        }

        if (metadata.workbenchName.isEmpty()
            && metadata.tabName.compare(QStringLiteral("Sketch"), Qt::CaseInsensitive) == 0
            && activeWorkbench.contains(QStringLiteral("SketcherWorkbench"), Qt::CaseInsensitive)) {
            return false;
        }

        if (!metadata.workbenchName.isEmpty()
            && !activeWorkbench.contains(metadata.workbenchName, Qt::CaseInsensitive)) {
            return false;
        }

        if (metadata.typeKeywords.isEmpty()) {
            return true;
        }

        const QString typeName
            = QString::fromLatin1(editViewProvider->getObject()->getTypeId().getName());
        for (const QString& keyword : metadata.typeKeywords) {
            if (typeName.contains(keyword, Qt::CaseInsensitive)) {
                return true;
            }
        }

        return false;
    }
    QString toolbarLabelForHeuristics(const QString& toolbarName);
    int toolbarOrderForMetadata(const QString& toolbarName);
    int toolbarHomePriorityForMetadata(const QString& toolbarName);
    bool nameContainsAny(const QString& source, std::initializer_list<const char*> keywords);

    bool activeWorkbenchMatches(const QString& activeWorkbench, const QString& workbenchName)
    {
        return activeWorkbench.contains(workbenchName, Qt::CaseInsensitive);
    }

    QString activeEditObjectTypeName(const ViewProviderDocumentObject* editViewProvider)
    {
        if (!editViewProvider || !editViewProvider->getObject()) {
            return {};
        }

        return QString::fromLatin1(editViewProvider->getObject()->getTypeId().getName());
    }

    bool selectionContainsObjectType(const QString& typeName)
    {
        for (const auto& selection : Gui::Selection().getSelection()) {
            if (selection.pObject
                && QString::fromLatin1(selection.pObject->getTypeId().getName()).contains(
                    typeName,
                    Qt::CaseInsensitive)) {
                return true;
            }
        }

        return false;
    }

    int adaptiveHomePriorityForToolbar(const QString& toolbarName,
                                       const QString& activeWorkbench,
                                       const ViewProviderDocumentObject* editViewProvider)
    {
        const QString label = toolbarLabelForHeuristics(toolbarName);
        const QString editTypeName = activeEditObjectTypeName(editViewProvider);
        const int metadataPriority = toolbarHomePriorityForMetadata(toolbarName) * 100;
        const bool sketchSelectedWithoutEdit = editTypeName.isEmpty()
            && selectionContainsObjectType(QStringLiteral("Sketcher::SketchObject"));

        if (activeWorkbenchMatches(activeWorkbench, QStringLiteral("PartDesignWorkbench"))) {
            if (label.contains(QStringLiteral("Helper"), Qt::CaseInsensitive)) {
                return metadataPriority;
            }

            if (editTypeName.contains(QStringLiteral("Sketcher::SketchObject"), Qt::CaseInsensitive)
                && label.contains(QStringLiteral("Modeling"), Qt::CaseInsensitive)) {
                return metadataPriority + 5;
            }

            if (editTypeName.contains(QStringLiteral("DressUp"), Qt::CaseInsensitive)
                && label.contains(QStringLiteral("Dress-Up"), Qt::CaseInsensitive)) {
                return metadataPriority + 10;
            }

            if ((editTypeName.contains(QStringLiteral("Transformed"), Qt::CaseInsensitive)
                 || editTypeName.contains(QStringLiteral("MultiTransform"), Qt::CaseInsensitive))
                && label.contains(QStringLiteral("Transformation"), Qt::CaseInsensitive)) {
                return metadataPriority + 10;
            }

            if (sketchSelectedWithoutEdit
                && label.contains(QStringLiteral("Modeling"), Qt::CaseInsensitive)) {
                return metadataPriority + 80;
            }

            if (label.contains(QStringLiteral("Modeling"), Qt::CaseInsensitive)) {
                return metadataPriority + 20;
            }

            if (label.contains(QStringLiteral("Dress-Up"), Qt::CaseInsensitive)) {
                return metadataPriority + 30;
            }

            if (label.contains(QStringLiteral("Transformation"), Qt::CaseInsensitive)) {
                return metadataPriority + 40;
            }
        }

        if (activeWorkbenchMatches(activeWorkbench, QStringLiteral("SketcherWorkbench"))) {
            if (label.compare(QStringLiteral("Sketcher"), Qt::CaseInsensitive) == 0) {
                return metadataPriority;
            }
            if (label.compare(QStringLiteral("Edit Mode"), Qt::CaseInsensitive) == 0) {
                return metadataPriority + 10;
            }
            if (label.compare(QStringLiteral("Geometries"), Qt::CaseInsensitive) == 0) {
                return metadataPriority + 20;
            }
            if (label.compare(QStringLiteral("Constraints"), Qt::CaseInsensitive) == 0) {
                return metadataPriority + 30;
            }
            if (nameContainsAny(label, {"Sketcher Tools", "Sketcher Edit Tools"})) {
                return metadataPriority + 40;
            }
            if (label.compare(QStringLiteral("B-Spline Tools"), Qt::CaseInsensitive) == 0) {
                return metadataPriority + 50;
            }
            if (nameContainsAny(label, {"Visual Helpers", "Virtual Space"})) {
                return metadataPriority + 60;
            }
        }

        if (activeWorkbenchMatches(activeWorkbench, QStringLiteral("AssemblyWorkbench"))) {
            if (label.compare(QStringLiteral("Workflow"), Qt::CaseInsensitive) == 0) {
                return metadataPriority;
            }
            if (label.compare(QStringLiteral("Joints"), Qt::CaseInsensitive) == 0) {
                return metadataPriority + 10;
            }
        }

        if (activeWorkbenchMatches(activeWorkbench, QStringLiteral("FlowStudioWorkbench"))) {
            if (label.compare(QStringLiteral("Analysis"), Qt::CaseInsensitive) == 0) {
                return metadataPriority;
            }
            if (label.compare(QStringLiteral("Setup"), Qt::CaseInsensitive) == 0) {
                return metadataPriority + 10;
            }
            if (label.compare(QStringLiteral("Solve"), Qt::CaseInsensitive) == 0) {
                return metadataPriority + 20;
            }
            if (label.compare(QStringLiteral("Boundary Conditions"), Qt::CaseInsensitive) == 0) {
                return metadataPriority + 30;
            }
            if (label.compare(QStringLiteral("Mesh"), Qt::CaseInsensitive) == 0) {
                return metadataPriority + 40;
            }
            if (label.compare(QStringLiteral("Geometry"), Qt::CaseInsensitive) == 0) {
                return metadataPriority + 50;
            }
            if (label.compare(QStringLiteral("Post-Processing"), Qt::CaseInsensitive) == 0) {
                return metadataPriority + 60;
            }
        }

        if (activeWorkbenchMatches(activeWorkbench, QStringLiteral("TechDrawWorkbench"))) {
            if (nameContainsAny(label, {"TechDraw Pages", "Page"})) {
                return metadataPriority;
            }
            if (nameContainsAny(label, {"TechDraw Views", "Views"})) {
                return metadataPriority + 10;
            }
            if (nameContainsAny(label, {"TechDraw Dimensions", "Dimensions"})) {
                return metadataPriority + 20;
            }
            if (nameContainsAny(label, {"TechDraw Annotation", "Annotations"})) {
                return metadataPriority + 30;
            }
            if (nameContainsAny(label, {"TechDraw Decoration", "Decoration"})) {
                return metadataPriority + 40;
            }
            if (nameContainsAny(label, {"TechDraw Attributes", "Attributes"})) {
                return metadataPriority + 50;
            }
        }

        return metadataPriority + toolbarOrderForMetadata(toolbarName);
    }

    int adaptiveHomePriorityForContextPanel(const RibbonContextualToolbarMetadata& metadata)
    {
        if (metadata.tabName.compare(QStringLiteral("Sketch"), Qt::CaseInsensitive) == 0) {
            if (metadata.panelName.compare(QStringLiteral("Sketch"), Qt::CaseInsensitive) == 0) {
                return 0;
            }
            if (metadata.panelName.compare(QStringLiteral("Geometry"), Qt::CaseInsensitive) == 0) {
                return 10;
            }
            if (metadata.panelName.compare(QStringLiteral("Constraints"), Qt::CaseInsensitive) == 0) {
                return 20;
            }
            if (metadata.panelName.compare(QStringLiteral("Tools"), Qt::CaseInsensitive) == 0) {
                return 30;
            }
            if (metadata.panelName.compare(QStringLiteral("B-Spline"), Qt::CaseInsensitive) == 0) {
                return 40;
            }
            if (metadata.panelName.compare(QStringLiteral("Visual"), Qt::CaseInsensitive) == 0) {
                return 50;
            }
        }

        if (metadata.tabName.compare(QStringLiteral("Assembly"), Qt::CaseInsensitive) == 0) {
            if (metadata.panelName.compare(QStringLiteral("Assembly"), Qt::CaseInsensitive) == 0) {
                return 0;
            }
            if (metadata.panelName.compare(QStringLiteral("Joints"), Qt::CaseInsensitive) == 0) {
                return 10;
            }
            if (metadata.panelName.compare(QStringLiteral("Solve"), Qt::CaseInsensitive) == 0) {
                return 20;
            }
            if (metadata.panelName.compare(QStringLiteral("Joint Presets"), Qt::CaseInsensitive) == 0) {
                return 30;
            }
        }

        if (metadata.tabName.compare(QStringLiteral("Simulation"), Qt::CaseInsensitive) == 0) {
            if (metadata.panelName.compare(QStringLiteral("Setup"), Qt::CaseInsensitive) == 0) {
                return 0;
            }
            if (metadata.panelName.compare(QStringLiteral("Boundary Conditions"), Qt::CaseInsensitive) == 0) {
                return 10;
            }
            if (metadata.panelName.compare(QStringLiteral("Mesh & Solve"), Qt::CaseInsensitive) == 0) {
                return 20;
            }
            if (metadata.panelName.compare(QStringLiteral("Results"), Qt::CaseInsensitive) == 0) {
                return 30;
            }
        }

        return metadata.order;
    }

    QString toolbarLabelForHeuristics(const QString& toolbarName)
    {
        const auto metadata = parseRibbonToolbarMetadata(toolbarName);
        if (metadata.isValid()) {
            return metadata.panelName;
        }

        const auto contextualMetadata = parseRibbonContextualToolbarMetadata(toolbarName);
        return contextualMetadata.isValid() ? contextualMetadata.panelName : toolbarName;
    }

    int toolbarOrderForMetadata(const QString& toolbarName)
    {
        const auto metadata = parseRibbonToolbarMetadata(toolbarName);
        if (metadata.isValid()) {
            return metadata.order;
        }

        const auto contextualMetadata = parseRibbonContextualToolbarMetadata(toolbarName);
        return contextualMetadata.isValid() ? contextualMetadata.order : DefaultRibbonPanelOrder;
    }

    int toolbarHomePriorityForMetadata(const QString& toolbarName)
    {
        const auto metadata = parseRibbonToolbarMetadata(toolbarName);
        if (metadata.isValid() && metadata.promoteToHome) {
            return metadata.homePriority;
        }

        return 2;
    }

    bool nameContainsAny(const QString& source, std::initializer_list<const char*> keywords)
    {
        for (const auto* keyword : keywords) {
            if (source.contains(QString::fromLatin1(keyword), Qt::CaseInsensitive)) {
                return true;
            }
        }

        return false;
    }

    bool isUtilityToolbarName(const QString& toolbarName)
    {
        const QString label = toolbarLabelForHeuristics(toolbarName);
        return nameContainsAny(
            label,
            {"View", "Navigation", "Clipboard", "Macro", "Help", "Window", "Selection"}
        );
    }

    bool shouldPromoteToolbarToHome(const QString& toolbarName)
    {
        const auto metadata = parseRibbonToolbarMetadata(toolbarName);
        if (metadata.isValid()) {
            return metadata.promoteToHome;
        }

        const QString label = toolbarLabelForHeuristics(toolbarName);

        if (label.compare(QStringLiteral("File"), Qt::CaseInsensitive) == 0) {
            return false;
        }

        if (isUtilityToolbarName(toolbarName)) {
            return false;
        }

        return nameContainsAny(
                   label,
                   {
                       "Home",
                       "Analysis",
                       "Setup",
                       "Create",
                       "Feature",
                       "Model",
                       "Part",
                       "Sketch",
                       "Assembly",
                       "Mesh",
                       "Solve",
                       "Results",
                       "FlowStudio",
                   })
            || !label.isEmpty();
    }

    int ribbonTabPriority(const QString& tabName)
    {
        if (tabName == QObject::tr("Home")) {
            return 0;
        }
        if (tabName == QObject::tr("Model")) {
            return 1;
        }
        if (tabName == QObject::tr("Sketch")) {
            return 2;
        }
        if (tabName == QObject::tr("Assembly")) {
            return 3;
        }
        if (tabName == QObject::tr("Setup")) {
            return 4;
        }
        if (tabName == QObject::tr("Simulation")) {
            return 5;
        }
        if (tabName == QObject::tr("Solve")) {
            return 6;
        }
        if (tabName == QObject::tr("Results")) {
            return 7;
        }
        if (tabName == QObject::tr("Inspect")) {
            return 8;
        }
        if (tabName == QObject::tr("Drawing")) {
            return 9;
        }
        if (tabName == QObject::tr("Manufacturing")) {
            return 10;
        }
        if (tabName == QObject::tr("View")) {
            return 11;
        }
        if (tabName == QObject::tr("Tools")) {
            return 12;
        }

        return 50;
    }
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
        QStringLiteral("Std_Save"),
        QStringLiteral("Std_Undo"),
        QStringLiteral("Std_Redo"),
        QStringLiteral("Std_Refresh"),
        QStringLiteral("Std_ViewFitAll"),
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

    // Top row: application shell button + quick access on the left, command search on the right.
    auto* topRow = new QWidget(this);
    auto* topRowLayout = new QHBoxLayout(topRow);
    topRowLayout->setContentsMargins(0, 0, 0, 0);
    topRowLayout->setSpacing(8);

    applicationButton = new QToolButton(topRow);
    applicationButton->setObjectName(QStringLiteral("ribbonApplicationButton"));
    applicationButton->setAutoRaise(true);
    applicationButton->setFocusPolicy(Qt::NoFocus);
    applicationButton->setFixedHeight(QATBarHeight - 2);
    applicationButton->setToolButtonStyle(Qt::ToolButtonTextOnly);
    applicationButton->setText(qApp->applicationName().isEmpty() ? QStringLiteral("FreeCAD")
                                                                  : qApp->applicationName());
    applicationButton->setToolTip(tr("Open Backstage view"));
    applicationButton->setCursor(Qt::PointingHandCursor);
    applicationButton->setStyleSheet(QStringLiteral(
        "QToolButton#ribbonApplicationButton {"
        "  margin-left: 6px;"
        "  padding: 0 10px;"
        "  border: 1px solid palette(mid);"
        "  border-radius: 8px;"
        "  font-weight: 600;"
        "  background: palette(button);"
        "}"
        "QToolButton#ribbonApplicationButton:hover {"
        "  background: palette(light);"
        "}"
        "QToolButton#ribbonApplicationButton:pressed {"
        "  background: palette(midlight);"
        "}"
    ));
    topRowLayout->addWidget(applicationButton, 0, Qt::AlignLeft | Qt::AlignVCenter);

    qatBar = new QuickAccessToolBar(topRow);
    topRowLayout->addWidget(qatBar, 1);

    searchField = new QLineEdit(topRow);
    searchField->setObjectName(QStringLiteral("ribbonCommandSearch"));
    searchField->setClearButtonEnabled(true);
    searchField->setFixedHeight(QATBarHeight - 4);
    searchField->setMinimumWidth(220);
    searchField->setMaximumWidth(320);
    searchField->setPlaceholderText(tr("Search commands or press Ctrl+Shift+P"));
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
        if (index >= 0 && index != fileTabIndex) {
            lastContentTabIndex = index;
        }
    });
    connect(applicationButton, &QToolButton::clicked, this, [this]() {
        openBackstage();
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
            scheduleContextualTabsRefresh();
        });
    }

    inEditConnection = Application::Instance->signalInEdit.connect([this](const ViewProviderDocumentObject&) {
        scheduleContextualTabsRefresh();
    });
    resetEditConnection
        = Application::Instance->signalResetEdit.connect([this](const ViewProviderDocumentObject&) {
              scheduleContextualTabsRefresh();
          });
}

RibbonBar::~RibbonBar()
{
    qApp->removeEventFilter(this);

    if (_instance == this) {
        _instance = nullptr;
    }
}

void RibbonBar::scheduleRibbonSetupRefresh()
{
    if (!_instance || _instance->ribbonSetupRefreshPending || !_instance->configuredToolbarRoot
        || (Application::Instance && Application::Instance->isClosing())) {
        return;
    }

    _instance->ribbonSetupRefreshPending = true;
    QPointer<RibbonBar> instance(_instance);
    QMetaObject::invokeMethod(
        _instance,
        [instance]() {
            if (!instance) {
                return;
            }

            instance->ribbonSetupRefreshPending = false;
            if (!instance->configuredToolbarRoot) {
                return;
            }

            ToolBarItem* toolbars = instance->configuredToolbarRoot->copy();
            instance->setup(toolbars);
            delete toolbars;
        },
        Qt::QueuedConnection);
}

void RibbonBar::registerRibbonPanel(const QString& name, const QStringList& commandNames)
{
    if (name.isEmpty()) {
        return;
    }

    g_registeredRibbonPanels.insert(name, commandNames);
    scheduleRibbonSetupRefresh();
}

void RibbonBar::unregisterRibbonPanel(const QString& name)
{
    if (name.isEmpty()) {
        return;
    }

    g_registeredRibbonPanels.remove(name);
    scheduleRibbonSetupRefresh();
}

void RibbonBar::scheduleContextualTabsRefresh()
{
    if (!_instance || _instance->contextualTabsRefreshPending
        || !_instance->isVisible()
        || (Application::Instance && Application::Instance->isClosing())) {
        return;
    }

    _instance->contextualTabsRefreshPending = true;
    QPointer<RibbonBar> instance(_instance);
    QMetaObject::invokeMethod(
        _instance,
        [instance]() {
            if (!instance) {
                return;
            }

            instance->contextualTabsRefreshPending = false;
            instance->refreshContextualTabs();
        },
        Qt::QueuedConnection);
}

void RibbonBar::registerContextualRibbonPanel(const QString& name, const QStringList& commandNames)
{
    if (name.isEmpty()) {
        return;
    }

    g_registeredContextualRibbonPanels.insert(name, commandNames);
    scheduleContextualTabsRefresh();
}

void RibbonBar::unregisterContextualRibbonPanel(const QString& name)
{
    if (name.isEmpty()) {
        return;
    }

    g_registeredContextualRibbonPanels.remove(name);
    scheduleContextualTabsRefresh();
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

    contextualTabsRefreshPending = false;

    const QSignalBlocker blocker(tabWidget);
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

    delete configuredToolbarRoot;
    configuredToolbarRoot = toolBarItems->copy();
    configuredToolbarItems = configuredToolbarRoot ? configuredToolbarRoot->getItems() : QList<ToolBarItem*> {};
    QList<ToolBarItem*> items = configuredToolbarItems;

    // Group toolbars into ribbon tabs by category
    QMap<QString, QList<ToolBarItem*>> tabMap;
    QMap<QString, QList<QPair<RibbonToolbarMetadata, QStringList>>> registeredPanelMap;
    QStringList tabOrder;
    for (ToolBarItem* it : items) {
        QString tbName = QString::fromUtf8(it->command().c_str());
        if (parseRibbonContextualToolbarMetadata(tbName).isValid()) {
            continue;
        }

        QString tabName = categorizeToolbar(tbName);

        if (!tabMap.contains(tabName)) {
            tabOrder.append(tabName);
        }
        tabMap[tabName].append(it);
    }

    for (auto it = g_registeredRibbonPanels.begin(); it != g_registeredRibbonPanels.end(); ++it) {
        const auto metadata = parseRibbonToolbarMetadata(it.key());
        if (!metadata.isValid()) {
            continue;
        }

        if (!tabMap.contains(metadata.tabName) && !registeredPanelMap.contains(metadata.tabName)) {
            tabOrder.append(metadata.tabName);
        }
        registeredPanelMap[metadata.tabName].append({metadata, it.value()});
    }

    for (auto it = tabMap.begin(); it != tabMap.end(); ++it) {
        auto& tabItems = it.value();
        std::stable_sort(tabItems.begin(), tabItems.end(), [](ToolBarItem* left, ToolBarItem* right) {
            const int leftOrder = toolbarOrderForMetadata(QString::fromUtf8(left->command().c_str()));
            const int rightOrder = toolbarOrderForMetadata(QString::fromUtf8(right->command().c_str()));
            return leftOrder < rightOrder;
        });
    }

    for (auto it = registeredPanelMap.begin(); it != registeredPanelMap.end(); ++it) {
        auto& panels = it.value();
        std::stable_sort(panels.begin(), panels.end(), [](const auto& left, const auto& right) {
            return left.first.order < right.first.order;
        });
    }

    if (!items.isEmpty() || !g_registeredRibbonPanels.isEmpty()) {
        auto* homePage = new RibbonTabPage(tabWidget);
        int homeTabIndex = tabWidget->addTab(homePage, tr("Home"));
        tabWidget->setTabToolTip(homeTabIndex, tr("Most common actions for the active workflow context"));
        tabPages[tr("Home")] = homePage;
    }

    std::stable_sort(tabOrder.begin(), tabOrder.end(), [](const QString& left, const QString& right) {
        return ribbonTabPriority(left) < ribbonTabPriority(right);
    });

    // Create ribbon tabs and panels
    for (const QString& tabName : tabOrder) {
        if (tabPages.contains(tabName)) {
            continue;
        }

        auto* tabPage = new RibbonTabPage(tabWidget);
        int tabIndex = tabWidget->addTab(tabPage, tabName);
        if (tabName == tr("View")) {
            tabWidget->setTabToolTip(tabIndex, tr("Display, navigation, and panel visibility tools"));
        }
        else if (tabName == tr("Inspect")) {
            tabWidget->setTabToolTip(tabIndex, tr("Validation, diagnostics, and measurement tools"));
        }
        else if (tabName == tr("Simulation")) {
            tabWidget->setTabToolTip(tabIndex, tr("Analysis setup, solving, and simulation workflow tools"));
        }
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

        for (const auto& panelEntry : registeredPanelMap.value(tabName)) {
            auto* panel = createContextPanel(panelEntry.first.panelName, panelEntry.second);
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
    const auto metadata = parseRibbonToolbarMetadata(tbName);
    if (metadata.isValid()) {
        return metadata.tabName;
    }

    const QString label = toolbarLabelForHeuristics(tbName);

    if (nameContainsAny(label, {"View", "Navigation", "Individual views", "Display"})) {
        return tr("View");
    }

    if (nameContainsAny(label, {"Inspect", "Measure", "Validate", "Check", "Report", "Diagnostic"})) {
        return tr("Inspect");
    }

    if (nameContainsAny(label, {"Results", "Post", "Plot", "Probe", "Contour", "Trajectory", "Streamline"})) {
        return tr("Results");
    }

    if (nameContainsAny(label,
                        {"Sketch",
                         "Edit Mode",
                         "Geometries",
                         "Constraints",
                         "Sketcher Tools",
                         "B-Spline Tools",
                         "Visual Helpers"})) {
        return tr("Sketch");
    }

    if (label.contains(QStringLiteral("Sketch"), Qt::CaseInsensitive)) {
        return tr("Sketch");
    }

    if (label.contains(QStringLiteral("Assembly"), Qt::CaseInsensitive)) {
        return tr("Assembly");
    }

    if (nameContainsAny(label, {"FlowStudio", "CFD", "FEM", "Mesh", "Solve", "Solver", "Thermal", "Electro", "Optical"})) {
        return tr("Simulation");
    }

    if (nameContainsAny(label, {"Drawing", "TechDraw"})) {
        return tr("Drawing");
    }

    if (nameContainsAny(label, {"CAM", "Path", "Manufacturing"})) {
        return tr("Manufacturing");
    }

    if (nameContainsAny(label, {"Part Design", "PartDesign", "Part", "Body", "Feature", "Create", "Modify", "Insert", "Draft"})) {
        return tr("Model");
    }

    if (nameContainsAny(label, {"Edit", "Clipboard", "Macro", "Structure", "Help", "File"})) {
        return tr("Tools");
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
    delete configuredToolbarRoot;
    configuredToolbarRoot = nullptr;
    configuredToolbarItems.clear();
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
    const auto metadata = parseRibbonToolbarMetadata(name);
    const auto contextualMetadata = parseRibbonContextualToolbarMetadata(name);
    const QString panelName = metadata.isValid()
        ? metadata.panelName
        : (contextualMetadata.isValid() ? contextualMetadata.panelName : name);
    QByteArray tbNameBytes = panelName.toUtf8();
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
    int primaryCount = 0;
    constexpr int primaryLimit = 3;
    for (const QString& commandName : commandNames) {
        if (commandName == QStringLiteral("Separator")) {
            panel->addSeparator();
            continue;
        }

        if (auto* button = createButton(commandName)) {
            const bool hasMenu = (button->menu() || button->popupMode() != QToolButton::DelayedPopup);
            const bool isPrimary = (primaryCount < primaryLimit);
            button->setButtonSize((hasMenu || isPrimary)
                                      ? RibbonButton::Large
                                      : RibbonButton::Small);
            panel->addButton(button);
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

void RibbonBar::refreshContextualTabs()
{
    if (!Application::Instance || !tabWidget || !isVisible() || QApplication::closingDown()
        || Application::Instance->isClosing()) {
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

    QMap<QString, QList<ToolBarItem*>> contextualToolbarMap;
    QMap<QString, QColor> contextualAccentColors;
    for (ToolBarItem* tbItem : std::as_const(configuredToolbarItems)) {
        const QString tbName = QString::fromUtf8(tbItem->command().c_str());
        const auto metadata = parseRibbonContextualToolbarMetadata(tbName);
        if (!matchesContextualToolbar(metadata, activeWorkbench, editVp)) {
            continue;
        }

        contextualToolbarMap[metadata.tabName].append(tbItem);
        if (metadata.accentColor.isValid() && !contextualAccentColors.contains(metadata.tabName)) {
            contextualAccentColors.insert(metadata.tabName, metadata.accentColor);
        }
    }

    QMap<QString, QList<QPair<RibbonContextualToolbarMetadata, QStringList>>> registeredContextualPanels;
    for (auto it = g_registeredContextualRibbonPanels.begin(); it != g_registeredContextualRibbonPanels.end(); ++it) {
        const auto metadata = parseRibbonContextualToolbarMetadata(it.key());
        if (!matchesContextualToolbar(metadata, activeWorkbench, editVp)) {
            continue;
        }

        registeredContextualPanels[metadata.tabName].append({metadata, it.value()});
        if (metadata.accentColor.isValid() && !contextualAccentColors.contains(metadata.tabName)) {
            contextualAccentColors.insert(metadata.tabName, metadata.accentColor);
        }
    }

    auto homeIt = tabPages.find(tr("Home"));
    if (homeIt != tabPages.end()) {
        auto* homePage = homeIt.value();
        homePage->clearPanels();

        struct ToolbarHomeCandidate {
            ToolBarItem* item{};
            int priority = DefaultRibbonPanelOrder;
            int order = DefaultRibbonPanelOrder;
        };

        struct RegisteredHomeCandidate {
            RibbonContextualToolbarMetadata metadata;
            QStringList commands;
            int priority = DefaultRibbonPanelOrder;
        };

        struct RegisteredRibbonHomeCandidate {
            RibbonToolbarMetadata metadata;
            QStringList commands;
            int priority = DefaultRibbonPanelOrder;
        };

        QList<ToolbarHomeCandidate> contextualHomeCandidates;
        for (auto it = contextualToolbarMap.begin(); it != contextualToolbarMap.end(); ++it) {
            for (ToolBarItem* tbItem : std::as_const(it.value())) {
                const QString tbName = QString::fromUtf8(tbItem->command().c_str());
                const auto metadata = parseRibbonContextualToolbarMetadata(tbName);
                contextualHomeCandidates.push_back(
                    {tbItem, adaptiveHomePriorityForContextPanel(metadata), metadata.order}
                );
            }
        }
        std::stable_sort(contextualHomeCandidates.begin(),
                         contextualHomeCandidates.end(),
                         [](const ToolbarHomeCandidate& left, const ToolbarHomeCandidate& right) {
                             if (left.priority != right.priority) {
                                 return left.priority < right.priority;
                             }
                             return left.order < right.order;
                         });

        QList<RegisteredHomeCandidate> registeredHomeCandidates;
        for (auto it = registeredContextualPanels.begin(); it != registeredContextualPanels.end(); ++it) {
            for (const auto& panel : std::as_const(it.value())) {
                registeredHomeCandidates.push_back(
                    {panel.first, panel.second, adaptiveHomePriorityForContextPanel(panel.first)}
                );
            }
        }
        std::stable_sort(registeredHomeCandidates.begin(),
                         registeredHomeCandidates.end(),
                         [](const RegisteredHomeCandidate& left, const RegisteredHomeCandidate& right) {
                             if (left.priority != right.priority) {
                                 return left.priority < right.priority;
                             }
                             return left.metadata.order < right.metadata.order;
                         });

        QList<RegisteredRibbonHomeCandidate> registeredRibbonHomeCandidates;
        for (auto it = g_registeredRibbonPanels.begin(); it != g_registeredRibbonPanels.end(); ++it) {
            const auto metadata = parseRibbonToolbarMetadata(it.key());
            if (!metadata.isValid() || !metadata.promoteToHome) {
                continue;
            }

            registeredRibbonHomeCandidates.push_back(
                {metadata, it.value(), toolbarHomePriorityForMetadata(it.key()) * 100}
            );
        }
        std::stable_sort(registeredRibbonHomeCandidates.begin(),
                         registeredRibbonHomeCandidates.end(),
                         [](const RegisteredRibbonHomeCandidate& left,
                            const RegisteredRibbonHomeCandidate& right) {
                             if (left.priority != right.priority) {
                                 return left.priority < right.priority;
                             }
                             return left.metadata.order < right.metadata.order;
                         });

        QList<ToolbarHomeCandidate> toolbarHomeCandidates;
        for (ToolBarItem* tbItem : std::as_const(configuredToolbarItems)) {
            const QString tbName = QString::fromUtf8(tbItem->command().c_str());
            if (parseRibbonContextualToolbarMetadata(tbName).isValid() || isUtilityToolbarName(tbName)) {
                continue;
            }

            toolbarHomeCandidates.push_back(
                {tbItem,
                 adaptiveHomePriorityForToolbar(tbName, activeWorkbench, editVp),
                 toolbarOrderForMetadata(tbName)}
            );
        }
        std::stable_sort(toolbarHomeCandidates.begin(),
                         toolbarHomeCandidates.end(),
                         [](const ToolbarHomeCandidate& left, const ToolbarHomeCandidate& right) {
                             if (left.priority != right.priority) {
                                 return left.priority < right.priority;
                             }
                             return left.order < right.order;
                         });

        QSet<QString> usedHomePanels;
        int homePanelCount = 0;
        auto addHomePanel = [&](RibbonPanel* panel, const QString& panelKey) {
            if (!panel || panel->buttonCount() <= 0 || usedHomePanels.contains(panelKey)
                || homePanelCount >= MaxHomePanels) {
                delete panel;
                return;
            }

            usedHomePanels.insert(panelKey);
            homePage->addPanel(panel);
            ++homePanelCount;
        };

        for (const auto& candidate : contextualHomeCandidates) {
            addHomePanel(createPanel(QString::fromUtf8(candidate.item->command().c_str()), candidate.item),
                         QString::fromUtf8(candidate.item->command().c_str()));
        }

        for (const auto& candidate : registeredHomeCandidates) {
            addHomePanel(createContextPanel(candidate.metadata.panelName, candidate.commands),
                         candidate.metadata.tabName + QStringLiteral("::") + candidate.metadata.panelName);
        }

        for (const auto& candidate : registeredRibbonHomeCandidates) {
            addHomePanel(createContextPanel(candidate.metadata.panelName, candidate.commands),
                         candidate.metadata.tabName + QStringLiteral("::") + candidate.metadata.panelName);
        }

        for (const auto& candidate : toolbarHomeCandidates) {
            addHomePanel(createPanel(QString::fromUtf8(candidate.item->command().c_str()), candidate.item),
                         QString::fromUtf8(candidate.item->command().c_str()));
        }

        if (homePanelCount == 0) {
            for (const auto& candidate : toolbarHomeCandidates) {
                if (homePanelCount >= MaxHomePanels) {
                    break;
                }

                addHomePanel(createPanel(QString::fromUtf8(candidate.item->command().c_str()), candidate.item),
                             QString::fromUtf8(candidate.item->command().c_str()));
            }
        }
    }

    QSet<QString> preparedContextualTabs;
    auto prepareContextualPage = [&](const QString& tabName) {
        auto* page = showContextualTab(tabName, contextualAccentColors.value(tabName), editVp != nullptr);
        if (!preparedContextualTabs.contains(tabName)) {
            page->clearPanels();
            preparedContextualTabs.insert(tabName);
        }
        return page;
    };

    for (auto it = contextualToolbarMap.begin(); it != contextualToolbarMap.end(); ++it) {
        auto& toolbars = it.value();
        std::stable_sort(toolbars.begin(), toolbars.end(), [](ToolBarItem* left, ToolBarItem* right) {
            const int leftOrder = toolbarOrderForMetadata(QString::fromUtf8(left->command().c_str()));
            const int rightOrder = toolbarOrderForMetadata(QString::fromUtf8(right->command().c_str()));
            return leftOrder < rightOrder;
        });

        auto* page = prepareContextualPage(it.key());
        for (ToolBarItem* tbItem : std::as_const(toolbars)) {
            RibbonPanel* panel = createPanel(QString::fromUtf8(tbItem->command().c_str()), tbItem);
            if (panel && panel->buttonCount() > 0) {
                page->addPanel(panel);
            }
            else {
                delete panel;
            }
        }
    }

    for (auto it = registeredContextualPanels.begin(); it != registeredContextualPanels.end(); ++it) {
        auto panels = it.value();
        std::stable_sort(panels.begin(), panels.end(), [](const auto& left, const auto& right) {
            return left.first.order < right.first.order;
        });

        auto* page = prepareContextualPage(it.key());
        for (const auto& panelEntry : panels) {
            auto* panel = createContextPanel(panelEntry.first.panelName, panelEntry.second);
            if (panel && panel->buttonCount() > 0) {
                page->addPanel(panel);
            }
            else {
                delete panel;
            }
        }
    }
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
