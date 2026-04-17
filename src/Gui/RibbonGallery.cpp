/***************************************************************************
 *   Copyright (c) 2024 FreeCAD Project                                   *
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
 *   License along with this library; see the file COPYING.LIB. If not,   *
 *   write to the Free Software Foundation, Inc., 59 Temple Place,         *
 *   Suite 330, Boston, MA  02111-1307, USA                                *
 *                                                                         *
 ***************************************************************************/

#include "PreCompiled.h"

#include <QGridLayout>
#include <QHBoxLayout>
#include <QVBoxLayout>
#include <QToolButton>
#include <QScrollArea>
#include <QLabel>
#include <QMenu>
#include <QWidgetAction>
#include <QApplication>
#include <QPainter>
#include <QStyle>

#include "RibbonGallery.h"

using namespace Gui;

// ============================================================================
// RibbonGallery
// ============================================================================

RibbonGallery::RibbonGallery(QWidget* parent)
    : QWidget(parent)
{
    auto* mainLayout = new QHBoxLayout(this);
    mainLayout->setContentsMargins(0, 0, 0, 0);
    mainLayout->setSpacing(0);

    // Inline thumbnail strip
    stripWidget_ = new QWidget(this);
    stripLayout_ = new QGridLayout(stripWidget_);
    stripLayout_->setContentsMargins(0, 0, 0, 0);
    stripLayout_->setSpacing(2);
    mainLayout->addWidget(stripWidget_, 1);

    // Expand button (right-side arrow)
    expandBtn_ = new QToolButton(this);
    expandBtn_->setArrowType(Qt::DownArrow);
    expandBtn_->setAutoRaise(true);
    expandBtn_->setFixedWidth(16);
    expandBtn_->setToolTip(tr("Show all items"));
    connect(expandBtn_, &QToolButton::clicked,
            this, &RibbonGallery::onExpandClicked);
    mainLayout->addWidget(expandBtn_, 0);

    // Popup menu created on demand
    popupMenu_ = nullptr;
}

// ---------------------------------------------------------------------------
// Item management
// ---------------------------------------------------------------------------

void RibbonGallery::addItem(const RibbonGalleryItem& item)
{
    items_.append(item);
    rebuildInlineStrip();
}

void RibbonGallery::addItems(const QList<RibbonGalleryItem>& items)
{
    items_.append(items);
    rebuildInlineStrip();
}

void RibbonGallery::clear()
{
    items_.clear();
    categories_.clear();
    selectedId_.clear();
    rebuildInlineStrip();
}

void RibbonGallery::addCategory(const QString& name)
{
    CategoryMarker marker;
    marker.name = name;
    marker.insertBeforeIndex = items_.size();
    categories_.append(marker);
}

// ---------------------------------------------------------------------------
// Appearance setters
// ---------------------------------------------------------------------------

void RibbonGallery::setThumbnailSize(const QSize& size)
{
    thumbSize_ = size;
    rebuildInlineStrip();
}

void RibbonGallery::setVisibleRows(int rows)
{
    visibleRows_ = qMax(1, rows);
    rebuildInlineStrip();
}

void RibbonGallery::setVisibleColumns(int cols)
{
    visibleCols_ = qMax(0, cols);
    rebuildInlineStrip();
}

void RibbonGallery::setSelectedItemId(const QString& id)
{
    selectedId_ = id;
    rebuildInlineStrip();
}

// ---------------------------------------------------------------------------
// Rebuild the inline thumbnail strip
// ---------------------------------------------------------------------------

void RibbonGallery::rebuildInlineStrip()
{
    // Remove existing buttons
    QLayoutItem* child = nullptr;
    while ((child = stripLayout_->takeAt(0)) != nullptr) {
        delete child->widget();
        delete child;
    }

    if (items_.isEmpty()) {
        expandBtn_->setVisible(false);
        return;
    }

    int cols = visibleCols_;
    if (cols <= 0) {
        // Auto-fit: estimate from widget width and thumbnail size
        int availableWidth = stripWidget_->width();
        if (availableWidth <= 0) {
            availableWidth = 200;  // reasonable default before first layout
        }
        cols = qMax(1, availableWidth / (thumbSize_.width() + 4));
    }

    int maxInline = cols * visibleRows_;
    int count = qMin(items_.size(), maxInline);

    for (int i = 0; i < count; ++i) {
        int row = i / cols;
        int col = i % cols;
        auto* btn = createThumbnailButton(items_[i], i, /*forPopup=*/false);
        stripLayout_->addWidget(btn, row, col);
    }

    // Show expand button only if there are more items than visible
    expandBtn_->setVisible(items_.size() > maxInline);
}

// ---------------------------------------------------------------------------
// Create a thumbnail button
// ---------------------------------------------------------------------------

QToolButton* RibbonGallery::createThumbnailButton(const RibbonGalleryItem& item,
                                                    int index, bool forPopup)
{
    auto* btn = new QToolButton();
    btn->setIcon(item.icon);
    btn->setIconSize(thumbSize_);
    btn->setToolTip(item.toolTip.isEmpty() ? item.label : item.toolTip);
    btn->setAutoRaise(true);
    btn->setEnabled(item.enabled);
    btn->setCheckable(true);
    btn->setChecked(item.itemId == selectedId_);

    // Fixed size for uniform grid
    QSize btnSize(thumbSize_.width() + 6, thumbSize_.height() + 6);
    btn->setFixedSize(btnSize);

    if (forPopup) {
        connect(btn, &QToolButton::clicked, [this, index]() {
            onPopupItemClicked(index);
        });
    }
    else {
        connect(btn, &QToolButton::clicked, [this, index]() {
            onInlineItemClicked(index);
        });
    }

    return btn;
}

// ---------------------------------------------------------------------------
// Expand popup
// ---------------------------------------------------------------------------

void RibbonGallery::onExpandClicked()
{
    if (!popupMenu_) {
        popupMenu_ = new QMenu(this);
    }
    popupMenu_->clear();

    // Build a widget with a grid of all items, grouped by category
    auto* popupWidget = new QWidget();
    auto* popupLayout = new QVBoxLayout(popupWidget);
    popupLayout->setContentsMargins(8, 8, 8, 8);
    popupLayout->setSpacing(4);

    // Determine columns for the popup (wider than inline)
    int popupCols = qMax(4, static_cast<int>(
        std::sqrt(static_cast<double>(items_.size())) + 0.5));

    int categoryIdx = 0;
    int itemIdx = 0;

    QGridLayout* currentGrid = nullptr;

    auto startNewGrid = [&](const QString& catName) {
        if (!catName.isEmpty()) {
            auto* label = new QLabel(catName, popupWidget);
            QFont f = label->font();
            f.setBold(true);
            label->setFont(f);
            popupLayout->addWidget(label);
        }
        currentGrid = new QGridLayout();
        currentGrid->setSpacing(2);
        popupLayout->addLayout(currentGrid);
    };

    // If there are categories, use them; otherwise single grid
    if (categories_.isEmpty()) {
        startNewGrid({});
        for (int i = 0; i < items_.size(); ++i) {
            int row = i / popupCols;
            int col = i % popupCols;
            auto* btn = createThumbnailButton(items_[i], i, /*forPopup=*/true);
            currentGrid->addWidget(btn, row, col);
        }
    }
    else {
        for (int ci = 0; ci < categories_.size(); ++ci) {
            startNewGrid(categories_[ci].name);
            int startIdx = categories_[ci].insertBeforeIndex;
            int endIdx = (ci + 1 < categories_.size())
                             ? categories_[ci + 1].insertBeforeIndex
                             : items_.size();
            int localIdx = 0;
            for (int i = startIdx; i < endIdx; ++i) {
                int row = localIdx / popupCols;
                int col = localIdx % popupCols;
                auto* btn = createThumbnailButton(items_[i], i, /*forPopup=*/true);
                currentGrid->addWidget(btn, row, col);
                ++localIdx;
            }
        }
        // Items before the first category marker
        if (!categories_.isEmpty() && categories_[0].insertBeforeIndex > 0) {
            startNewGrid({});
            for (int i = 0; i < categories_[0].insertBeforeIndex; ++i) {
                int row = i / popupCols;
                int col = i % popupCols;
                auto* btn = createThumbnailButton(items_[i], i, /*forPopup=*/true);
                currentGrid->addWidget(btn, row, col);
            }
        }
    }

    auto* widgetAction = new QWidgetAction(popupMenu_);
    widgetAction->setDefaultWidget(popupWidget);
    popupMenu_->addAction(widgetAction);

    popupMenu_->popup(expandBtn_->mapToGlobal(
        QPoint(0, expandBtn_->height())));
}

// ---------------------------------------------------------------------------
// Click handlers
// ---------------------------------------------------------------------------

void RibbonGallery::onInlineItemClicked(int index)
{
    if (index < 0 || index >= items_.size()) {
        return;
    }
    selectedId_ = items_[index].itemId;
    rebuildInlineStrip();
    Q_EMIT itemActivated(items_[index].itemId);
}

void RibbonGallery::onPopupItemClicked(int index)
{
    if (index < 0 || index >= items_.size()) {
        return;
    }
    selectedId_ = items_[index].itemId;
    if (popupMenu_) {
        popupMenu_->close();
    }
    rebuildInlineStrip();
    Q_EMIT itemActivated(items_[index].itemId);
}
