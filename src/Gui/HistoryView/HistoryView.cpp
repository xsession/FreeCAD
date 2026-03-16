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

#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QPainter>
#include <QMenu>
#include <QAction>
#include <QClipboard>
#include <QFileDialog>
#include <QMessageBox>
#include <QScrollBar>
#include <QApplication>
#include <QTextStream>
#include <QMouseEvent>
#include <QWheelEvent>
#include <QToolTip>
#include <QInputDialog>
#include <QPainterPath>

#include <App/Document.h>
#include <App/DocumentObject.h>
#include <App/SuppressibleExtension.h>
#include <Gui/Application.h>
#include <Gui/Document.h>
#include <Gui/BitmapFactory.h>
#include <Gui/MainWindow.h>
#include <Gui/Selection/Selection.h>
#include <Gui/View3DInventor.h>
#include <Gui/View3DInventorViewer.h>

#include "HistoryView.h"


using namespace Gui::HistoryView;
namespace sp = std::placeholders;


// ============================================================================
// HistoryDelegate — Vertical list view rendering (detail view)
// ============================================================================

HistoryDelegate::HistoryDelegate(QObject* parent)
    : QStyledItemDelegate(parent)
{
}

void HistoryDelegate::paint(QPainter* painter,
                             const QStyleOptionViewItem& option,
                             const QModelIndex& index) const
{
    painter->save();
    painter->setRenderHint(QPainter::Antialiasing, true);

    QRect rect = option.rect;
    bool isSelected = option.state & QStyle::State_Selected;
    bool isHovered = option.state & QStyle::State_MouseOver;
    bool isUndone = index.data(IsUndoneRole).toBool();
    bool isRollbackTarget = index.data(IsRollbackTargetRole).toBool();
    bool isSuppressed = index.data(IsSuppressedRole).toBool();
    QColor typeColor = index.data(ColorRole).value<QColor>();
    QString description = index.data(DescriptionRole).toString();
    QString typeLabel = index.data(TypeLabelRole).toString();
    QString featureLabel = index.data(FeatureLabelRole).toString();
    QDateTime timestamp = index.data(TimestampRole).toDateTime();

    // --- Background ---
    QColor bgColor;
    if (isSelected) {
        bgColor = option.palette.highlight().color();
    }
    else if (isHovered) {
        bgColor = option.palette.midlight().color();
    }
    else if (isUndone) {
        bgColor = option.palette.base().color();
        bgColor.setAlpha(128);
    }
    else {
        bgColor = option.palette.base().color();
    }
    painter->fillRect(rect, bgColor);

    // --- Colored left edge indicator (4px wide) ---
    QRect edgeRect(rect.left(), rect.top(), 4, rect.height());
    if (isRollbackTarget) {
        QLinearGradient gradient(edgeRect.topLeft(), edgeRect.bottomLeft());
        gradient.setColorAt(0, QColor(0xFF, 0xD5, 0x4F));
        gradient.setColorAt(1, QColor(0xFF, 0xA0, 0x00));
        painter->fillRect(edgeRect, gradient);
    }
    else if (isSuppressed) {
        painter->fillRect(edgeRect, QColor(0xF4, 0x43, 0x36));  // red for suppressed
    }
    else {
        painter->fillRect(edgeRect, typeColor);
    }

    // --- Timeline line (vertical connecting line) ---
    int lineX = rect.left() + 20;
    QPen linePen(isUndone ? QColor(0x60, 0x60, 0x60) : QColor(0x90, 0x90, 0x90), 2);
    if (isSuppressed) {
        linePen.setStyle(Qt::DashLine);  // Dashed for suppressed (Fusion 360)
    }
    painter->setPen(linePen);
    painter->drawLine(lineX, rect.top(), lineX, rect.bottom());

    // --- Timeline dot ---
    int dotY = rect.top() + rect.height() / 2;
    int dotRadius = isRollbackTarget ? 6 : 4;
    QColor dotColor = isRollbackTarget ? QColor(0xFF, 0xA0, 0x00) : typeColor;
    if (isUndone) {
        dotColor.setAlpha(100);
    }
    painter->setPen(Qt::NoPen);
    painter->setBrush(dotColor);
    painter->drawEllipse(QPoint(lineX, dotY), dotRadius, dotRadius);

    if (isRollbackTarget) {
        QPen ringPen(QColor(0xFF, 0xD5, 0x4F), 2);
        painter->setPen(ringPen);
        painter->setBrush(Qt::NoBrush);
        painter->drawEllipse(QPoint(lineX, dotY), 8, 8);
    }

    // --- Icon ---
    QIcon icon = index.data(Qt::DecorationRole).value<QIcon>();
    QRect iconRect(rect.left() + 32, rect.top() + (rect.height() - 18) / 2, 18, 18);
    if (!icon.isNull()) {
        QIcon::Mode iconMode = isUndone ? QIcon::Disabled : QIcon::Normal;
        icon.paint(painter, iconRect, Qt::AlignCenter, iconMode);
    }

    // --- Suppressed X overlay ---
    if (isSuppressed) {
        painter->setPen(QPen(QColor(0xF4, 0x43, 0x36, 200), 2));
        painter->drawLine(iconRect.topLeft() + QPoint(2, 2),
                          iconRect.bottomRight() - QPoint(2, 2));
        painter->drawLine(iconRect.topRight() + QPoint(-2, 2),
                          iconRect.bottomLeft() + QPoint(2, -2));
    }

    // --- Feature label badge ---
    if (!featureLabel.isEmpty()) {
        QFont badgeFont = option.font;
        badgeFont.setPointSize(badgeFont.pointSize() - 2);
        badgeFont.setBold(true);
        QFontMetrics badgeFm(badgeFont);
        int badgeWidth = badgeFm.horizontalAdvance(featureLabel) + 8;
        QRect badgeRect(rect.left() + 56, rect.top() + 3, badgeWidth, 16);

        QColor badgeBg = typeColor;
        badgeBg.setAlpha(isUndone ? 60 : 180);
        painter->setPen(Qt::NoPen);
        painter->setBrush(badgeBg);
        painter->drawRoundedRect(badgeRect, 3, 3);

        painter->setPen(isUndone ? QColor(0x80, 0x80, 0x80) : Qt::white);
        painter->setFont(badgeFont);
        painter->drawText(badgeRect, Qt::AlignCenter, featureLabel);
    }

    // --- Description text ---
    QFont descFont = option.font;
    if (isRollbackTarget) {
        descFont.setBold(true);
    }
    if (isSuppressed || isUndone) {
        descFont.setStrikeOut(true);
    }
    QFontMetrics descFm(descFont);
    painter->setFont(descFont);

    QColor textColor = isSelected ? option.palette.highlightedText().color()
                                  : (isUndone ? QColor(0x80, 0x80, 0x80)
                                              : option.palette.text().color());
    if (isSuppressed && !isUndone) {
        textColor = QColor(0xA0, 0x60, 0x60);  // muted red
    }
    painter->setPen(textColor);

    int textLeft = rect.left() + 56;
    int textTop = rect.top() + 20;
    int textWidth = rect.width() - textLeft - 70;

    QString elidedDesc = descFm.elidedText(description, Qt::ElideRight, textWidth);
    painter->drawText(textLeft, textTop, rect.width() - textLeft - 10, 20,
                      Qt::AlignLeft | Qt::AlignVCenter, elidedDesc);

    // --- Timestamp (right side) ---
    QFont timeFont = option.font;
    timeFont.setPointSize(timeFont.pointSize() - 2);
    timeFont.setStrikeOut(false);  // never strikethrough timestamp
    painter->setFont(timeFont);
    QColor timeColor = isUndone ? QColor(0x60, 0x60, 0x60) : QColor(0x90, 0x90, 0x90);
    painter->setPen(timeColor);

    QString timeStr = timestamp.toString(QStringLiteral("HH:mm:ss"));
    QRect timeRect(rect.right() - 65, rect.top() + 4, 60, rect.height() - 8);
    painter->drawText(timeRect, Qt::AlignRight | Qt::AlignTop, timeStr);

    // --- Rollback marker label ---
    if (isRollbackTarget) {
        QFont markerFont = option.font;
        markerFont.setPointSize(markerFont.pointSize() - 2);
        markerFont.setItalic(true);
        markerFont.setStrikeOut(false);
        painter->setFont(markerFont);
        painter->setPen(QColor(0xFF, 0xA0, 0x00));
        painter->drawText(rect.right() - 90, rect.bottom() - 16, 85, 14,
                          Qt::AlignRight | Qt::AlignVCenter,
                          tr("▶ Current"));
    }

    // --- Bottom separator ---
    QPen sepPen(option.palette.mid().color(), 1);
    painter->setPen(sepPen);
    painter->drawLine(rect.left() + 32, rect.bottom(), rect.right(), rect.bottom());

    painter->restore();
}

QSize HistoryDelegate::sizeHint(const QStyleOptionViewItem& option,
                                 const QModelIndex& index) const
{
    Q_UNUSED(option);
    bool isRollbackTarget = index.data(IsRollbackTargetRole).toBool();
    return QSize(250, isRollbackTarget ? 48 : 40);
}


// ============================================================================
// TimelineBar — Fusion 360-style horizontal timeline
// ============================================================================

TimelineBar::TimelineBar(QWidget* parent)
    : QWidget(parent)
{
    setMinimumHeight(TimelineHeight);
    setMaximumHeight(TimelineHeight);
    setMouseTracking(true);
    setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed);
    setFocusPolicy(Qt::ClickFocus);
}

void TimelineBar::setModel(HistoryModel* model)
{
    histModel = model;
    if (histModel) {
        connect(histModel, &HistoryModel::entryAdded, this, [this](int) {
            scrollToEnd();
            update();
        });
        connect(histModel, &QAbstractItemModel::dataChanged, this, [this]() {
            update();
        });
        connect(histModel, &QAbstractItemModel::modelReset, this, [this]() {
            scrollOffset = 0;
            update();
        });
    }
    update();
}

void TimelineBar::setFilterProxy(QSortFilterProxyModel* proxy)
{
    filterProxy = proxy;
    if (filterProxy) {
        connect(filterProxy, &QAbstractItemModel::layoutChanged, this, [this]() {
            update();
        });
    }
}

QSize TimelineBar::sizeHint() const
{
    return QSize(400, TimelineHeight);
}

QSize TimelineBar::minimumSizeHint() const
{
    return QSize(100, TimelineHeight);
}

int TimelineBar::visibleToSource(int visibleIdx) const
{
    if (!filterProxy || visibleIdx < 0) {
        return visibleIdx;
    }
    QModelIndex proxyIdx = filterProxy->index(visibleIdx, 0);
    QModelIndex srcIdx = filterProxy->mapToSource(proxyIdx);
    return srcIdx.row();
}

int TimelineBar::sourceToVisible(int sourceIdx) const
{
    if (!filterProxy || !histModel || sourceIdx < 0) {
        return -1;
    }
    QModelIndex srcIdx = histModel->index(sourceIdx, 0);
    QModelIndex proxyIdx = filterProxy->mapFromSource(srcIdx);
    return proxyIdx.row();
}

int TimelineBar::rollbackVisibleIndex() const
{
    if (!histModel) {
        return -1;
    }
    return sourceToVisible(histModel->rollbackPosition());
}

QRect TimelineBar::nodeRect(int visibleIndex) const
{
    int x = LeftMargin + visibleIndex * nodeSpacing - scrollOffset;
    int y = NodeY;
    return QRect(x - nodeSize / 2, y, nodeSize, nodeSize);
}

QRect TimelineBar::rollbackMarkerRect() const
{
    int rbIdx = rollbackVisibleIndex();
    if (rbIdx < 0) {
        return {};
    }
    int x = LeftMargin + rbIdx * nodeSpacing - scrollOffset;
    return QRect(x - MarkerTriangleSize, LineY + 2,
                 MarkerTriangleSize * 2, MarkerTriangleSize + 4);
}

int TimelineBar::nodeAtPos(const QPoint& pos) const
{
    int count = filterProxy ? filterProxy->rowCount() : (histModel ? histModel->rowCount() : 0);
    for (int i = 0; i < count; ++i) {
        QRect r = nodeRect(i);
        r.adjust(-4, -4, 4, 4);  // slight hit-area expansion
        if (r.contains(pos)) {
            return i;
        }
    }
    return -1;
}

void TimelineBar::scrollToEnd()
{
    int count = filterProxy ? filterProxy->rowCount() : (histModel ? histModel->rowCount() : 0);
    int totalWidth = LeftMargin * 2 + count * nodeSpacing;
    int maxScroll = qMax(0, totalWidth - width());
    scrollOffset = maxScroll;
}

void TimelineBar::paintEvent(QPaintEvent* /*event*/)
{
    QPainter painter(this);
    painter.setRenderHint(QPainter::Antialiasing, true);

    int w = width();
    int h = height();

    // Background
    QColor bgColor = palette().window().color();
    bgColor = bgColor.darker(110);
    painter.fillRect(rect(), bgColor);

    int count = filterProxy ? filterProxy->rowCount() : (histModel ? histModel->rowCount() : 0);
    if (count == 0) {
        painter.setPen(palette().mid().color());
        QFont f = font();
        f.setItalic(true);
        painter.setFont(f);
        painter.drawText(rect(), Qt::AlignCenter, tr("No history entries"));
        return;
    }

    // --- Connecting line ---
    int lineStartX = LeftMargin - scrollOffset;
    int lineEndX = LeftMargin + (count - 1) * nodeSpacing - scrollOffset;

    // Draw line in two sections: active (before rollback) and inactive (after)
    int rbVisIdx = rollbackVisibleIndex();

    // Active portion
    if (rbVisIdx >= 0) {
        int activeEndX = LeftMargin + rbVisIdx * nodeSpacing - scrollOffset;
        painter.setPen(QPen(QColor(0x90, 0x90, 0x90), 2));
        painter.drawLine(qMax(0, lineStartX), LineY,
                         qMin(w, activeEndX), LineY);

        // Inactive portion (past rollback)
        if (rbVisIdx < count - 1) {
            painter.setPen(QPen(QColor(0x50, 0x50, 0x50), 1, Qt::DashLine));
            painter.drawLine(qMin(w, activeEndX), LineY,
                             qMin(w, lineEndX), LineY);
        }
    }
    else {
        painter.setPen(QPen(QColor(0x90, 0x90, 0x90), 2));
        painter.drawLine(qMax(0, lineStartX), LineY,
                         qMin(w, lineEndX), LineY);
    }

    // --- Feature nodes ---
    for (int i = 0; i < count; ++i) {
        QRect nRect = nodeRect(i);

        // Skip if off-screen
        if (nRect.right() < -nodeSize || nRect.left() > w + nodeSize) {
            continue;
        }

        QModelIndex idx = filterProxy
            ? filterProxy->index(i, 0)
            : histModel->index(i, 0);

        bool isUndone = idx.data(IsUndoneRole).toBool();
        bool isRollbackTarget = idx.data(IsRollbackTargetRole).toBool();
        bool isSuppressed = idx.data(IsSuppressedRole).toBool();
        QColor color = idx.data(ColorRole).value<QColor>();
        QIcon icon = idx.data(Qt::DecorationRole).value<QIcon>();

        // Node background
        QColor nodeBg = bgColor.lighter(120);
        if (i == hoveredNode) {
            nodeBg = nodeBg.lighter(130);
        }
        if (i == selectedNode) {
            nodeBg = palette().highlight().color();
        }
        if (isUndone) {
            nodeBg.setAlpha(80);
        }

        // Selection glow effect — pulsing highlight ring around clicked node
        if (i == selectedNode && !isUndone) {
            QColor glowColor = color;
            glowColor.setAlpha(60);
            for (int g = 3; g >= 1; --g) {
                QRect glowRect = nRect.adjusted(-g * 2, -g * 2, g * 2, g * 2);
                glowColor.setAlpha(30 + (3 - g) * 20);
                painter.setPen(QPen(glowColor, 1));
                painter.setBrush(Qt::NoBrush);
                painter.drawRoundedRect(glowRect, 4 + g, 4 + g);
            }
        }

        // Node border
        QPen borderPen(color, isRollbackTarget ? 3 : 2);
        if (i == selectedNode && !isUndone) {
            borderPen.setWidth(3);
            borderPen.setColor(color.lighter(140));
        }
        if (isUndone) {
            borderPen.setColor(QColor(0x60, 0x60, 0x60));
        }
        if (isSuppressed) {
            borderPen.setStyle(Qt::DashLine);
            borderPen.setColor(QColor(0xF4, 0x43, 0x36));
        }

        painter.setPen(borderPen);
        painter.setBrush(nodeBg);
        painter.drawRoundedRect(nRect, 4, 4);

        // Icon inside node
        if (!icon.isNull()) {
            QIcon::Mode iconMode = isUndone ? QIcon::Disabled : QIcon::Normal;
            QRect iconR = nRect.adjusted(4, 4, -4, -4);
            icon.paint(&painter, iconR, Qt::AlignCenter, iconMode);
        }

        // Suppressed X overlay
        if (isSuppressed) {
            painter.setPen(QPen(QColor(0xF4, 0x43, 0x36, 200), 2));
            painter.drawLine(nRect.topLeft() + QPoint(4, 4),
                             nRect.bottomRight() - QPoint(4, 4));
            painter.drawLine(nRect.topRight() + QPoint(-4, 4),
                             nRect.bottomLeft() + QPoint(4, -4));
        }

        // Connection dot on the timeline line
        int centerX = nRect.center().x();
        int dotR = isRollbackTarget ? 5 : 3;
        QColor dotColor = isRollbackTarget ? QColor(0xFF, 0xA0, 0x00) : color;
        if (isUndone) {
            dotColor.setAlpha(80);
        }
        painter.setPen(Qt::NoPen);
        painter.setBrush(dotColor);
        painter.drawEllipse(QPoint(centerX, LineY), dotR, dotR);

        // Feature name below the line
        QString featureLabel = idx.data(FeatureLabelRole).toString();
        if (!featureLabel.isEmpty()) {
            QFont labelFont = font();
            labelFont.setPointSize(labelFont.pointSize() - 2);
            if (isRollbackTarget) {
                labelFont.setBold(true);
            }
            if (i == selectedNode) {
                labelFont.setBold(true);
            }
            if (isSuppressed || isUndone) {
                labelFont.setStrikeOut(true);
            }
            painter.setFont(labelFont);

            QColor textCol = isUndone ? QColor(0x60, 0x60, 0x60)
                           : isSuppressed ? QColor(0xA0, 0x60, 0x60)
                           : palette().text().color();
            painter.setPen(textCol);

            QFontMetrics fm(labelFont);
            QString elided = fm.elidedText(featureLabel, Qt::ElideRight, nodeSpacing - 4);
            QRect textRect(centerX - nodeSpacing / 2, LineY + 6,
                           nodeSpacing, 16);
            painter.drawText(textRect, Qt::AlignHCenter | Qt::AlignTop, elided);
        }
    }

    // --- Rollback marker (triangle below the line) ---
    int markerVisIdx = (draggingRollback && dragTargetNode >= 0)
                           ? dragTargetNode
                           : rollbackVisibleIndex();
    if (markerVisIdx >= 0) {
        int markerX = LeftMargin + markerVisIdx * nodeSpacing - scrollOffset;

        QPainterPath triangle;
        triangle.moveTo(markerX, LineY + 3);
        triangle.lineTo(markerX - MarkerTriangleSize, LineY + 3 + MarkerTriangleSize);
        triangle.lineTo(markerX + MarkerTriangleSize, LineY + 3 + MarkerTriangleSize);
        triangle.closeSubpath();

        QColor markerColor = draggingRollback ? QColor(0xFF, 0x80, 0x00)
                                              : QColor(0xFF, 0xA0, 0x00);
        painter.setPen(QPen(markerColor.darker(120), 1));
        painter.setBrush(markerColor);
        painter.drawPath(triangle);

        // Marker label
        if (!draggingRollback) {
            QFont mFont = font();
            mFont.setPointSize(mFont.pointSize() - 3);
            mFont.setBold(true);
            painter.setFont(mFont);
            painter.setPen(markerColor);
            // Show below triangle
        }
    }

    // --- Scroll indicators ---
    if (scrollOffset > 0) {
        // Left arrow
        painter.setPen(Qt::NoPen);
        painter.setBrush(QColor(255, 255, 255, 120));
        QPainterPath leftArr;
        leftArr.moveTo(12, LineY);
        leftArr.lineTo(4, LineY - 6);
        leftArr.lineTo(4, LineY + 6);
        leftArr.closeSubpath();
        painter.drawPath(leftArr);
    }

    int totalWidth = LeftMargin * 2 + count * nodeSpacing;
    if (scrollOffset < totalWidth - w) {
        // Right arrow
        painter.setPen(Qt::NoPen);
        painter.setBrush(QColor(255, 255, 255, 120));
        QPainterPath rightArr;
        rightArr.moveTo(w - 12, LineY);
        rightArr.lineTo(w - 4, LineY - 6);
        rightArr.lineTo(w - 4, LineY + 6);
        rightArr.closeSubpath();
        painter.drawPath(rightArr);
    }
}

void TimelineBar::mousePressEvent(QMouseEvent* event)
{
    if (event->button() == Qt::LeftButton) {
        // Check if pressing on rollback marker
        QRect rbRect = rollbackMarkerRect();
        if (rbRect.isValid() && rbRect.contains(event->pos())) {
            draggingRollback = true;
            dragTargetNode = rollbackVisibleIndex();
            setCursor(Qt::SizeHorCursor);
            event->accept();
            return;
        }

        int node = nodeAtPos(event->pos());
        if (node >= 0) {
            selectedNode = node;
            update();
            int srcIdx = visibleToSource(node);
            Q_EMIT featureClicked(srcIdx);
        }
    }
    else if (event->button() == Qt::RightButton) {
        int node = nodeAtPos(event->pos());
        if (node >= 0) {
            selectedNode = node;
            update();
            int srcIdx = visibleToSource(node);
            Q_EMIT featureContextMenu(srcIdx, event->globalPos());
        }
    }
    QWidget::mousePressEvent(event);
}

void TimelineBar::mouseMoveEvent(QMouseEvent* event)
{
    if (draggingRollback) {
        // Find nearest node to cursor X
        int count = filterProxy ? filterProxy->rowCount()
                                : (histModel ? histModel->rowCount() : 0);
        int bestDist = INT_MAX;
        int bestNode = -1;
        for (int i = 0; i < count; ++i) {
            QRect r = nodeRect(i);
            int dist = qAbs(r.center().x() - event->pos().x());
            if (dist < bestDist) {
                bestDist = dist;
                bestNode = i;
            }
        }
        if (bestNode >= 0 && bestNode != dragTargetNode) {
            dragTargetNode = bestNode;
            update();
        }
        event->accept();
        return;
    }

    int node = nodeAtPos(event->pos());
    if (node != hoveredNode) {
        hoveredNode = node;
        update();
    }

    // Change cursor for rollback marker
    QRect rbRect = rollbackMarkerRect();
    if (rbRect.isValid() && rbRect.contains(event->pos())) {
        setCursor(Qt::SizeHorCursor);
    }
    else {
        setCursor(Qt::ArrowCursor);
    }

    QWidget::mouseMoveEvent(event);
}

void TimelineBar::mouseReleaseEvent(QMouseEvent* event)
{
    if (draggingRollback && event->button() == Qt::LeftButton) {
        draggingRollback = false;
        setCursor(Qt::ArrowCursor);

        if (dragTargetNode >= 0) {
            int srcIdx = visibleToSource(dragTargetNode);
            Q_EMIT rollbackDragged(srcIdx);
        }
        dragTargetNode = -1;
        update();
        event->accept();
        return;
    }
    QWidget::mouseReleaseEvent(event);
}

void TimelineBar::mouseDoubleClickEvent(QMouseEvent* event)
{
    if (event->button() == Qt::LeftButton) {
        int node = nodeAtPos(event->pos());
        if (node >= 0) {
            int srcIdx = visibleToSource(node);
            Q_EMIT featureDoubleClicked(srcIdx);
            event->accept();
            return;
        }
    }
    QWidget::mouseDoubleClickEvent(event);
}

void TimelineBar::wheelEvent(QWheelEvent* event)
{
    if (event->modifiers() & Qt::ControlModifier) {
        // Zoom: adjust node spacing
        int delta = event->angleDelta().y();
        if (delta > 0) {
            nodeSpacing = qMin(nodeSpacing + 4, MaxNodeSpacing);
        }
        else if (delta < 0) {
            nodeSpacing = qMax(nodeSpacing - 4, MinNodeSpacing);
        }
        update();
        event->accept();
        return;
    }

    // Horizontal scroll
    int delta = event->angleDelta().y();
    int count = filterProxy ? filterProxy->rowCount()
                            : (histModel ? histModel->rowCount() : 0);
    int totalWidth = LeftMargin * 2 + count * nodeSpacing;
    int maxScroll = qMax(0, totalWidth - width());

    scrollOffset = qBound(0, scrollOffset - delta, maxScroll);
    update();
    event->accept();
}

void TimelineBar::resizeEvent(QResizeEvent* event)
{
    QWidget::resizeEvent(event);
    // Clamp scroll offset
    int count = filterProxy ? filterProxy->rowCount()
                            : (histModel ? histModel->rowCount() : 0);
    int totalWidth = LeftMargin * 2 + count * nodeSpacing;
    int maxScroll = qMax(0, totalWidth - width());
    scrollOffset = qMin(scrollOffset, maxScroll);
}

bool TimelineBar::event(QEvent* event)
{
    if (event->type() == QEvent::ToolTip) {
        auto helpEvent = static_cast<QHelpEvent*>(event);
        int node = nodeAtPos(helpEvent->pos());
        if (node >= 0) {
            QModelIndex idx = filterProxy
                ? filterProxy->index(node, 0)
                : histModel->index(node, 0);
            QString tip = idx.data(Qt::ToolTipRole).toString();
            QToolTip::showText(helpEvent->globalPos(), tip, this);
        }
        else {
            QToolTip::hideText();
        }
        return true;
    }
    return QWidget::event(event);
}


// ============================================================================
// HistoryFilterProxy
// ============================================================================

HistoryFilterProxy::HistoryFilterProxy(QObject* parent)
    : QSortFilterProxyModel(parent)
{
    for (int i = 0; i <= static_cast<int>(EntryType::RollbackMarker); ++i) {
        visibleTypes.insert(i);
    }
}

void HistoryFilterProxy::setVisibleTypes(const QSet<int>& types)
{
    visibleTypes = types;
    invalidateFilter();
}

void HistoryFilterProxy::setShowUndone(bool show)
{
    showUndone = show;
    invalidateFilter();
}

void HistoryFilterProxy::setFilterText(const QString& text)
{
    filterText = text;
    invalidateFilter();
}

bool HistoryFilterProxy::filterAcceptsRow(int sourceRow,
                                           const QModelIndex& sourceParent) const
{
    QModelIndex idx = sourceModel()->index(sourceRow, 0, sourceParent);

    int entryType = idx.data(EntryTypeRole).toInt();
    if (!visibleTypes.contains(entryType)) {
        return false;
    }

    if (!showUndone && idx.data(IsUndoneRole).toBool()) {
        return false;
    }

    if (!filterText.isEmpty()) {
        QString desc = idx.data(DescriptionRole).toString();
        if (!desc.contains(filterText, Qt::CaseInsensitive)) {
            return false;
        }
    }

    return true;
}


// ============================================================================
// HistoryPanel — Main Fusion 360-style timeline widget
// ============================================================================

HistoryPanel::HistoryPanel(QWidget* parent)
    : QWidget(parent)
{
    model = new HistoryModel(this);
    filterProxy = new HistoryFilterProxy(this);
    filterProxy->setSourceModel(model);

    setupUi();
    setupToolbar();
    setupConnections();

    // NOLINTBEGIN
    conActive = Application::Instance->signalActiveDocument.connect(
        std::bind(&HistoryPanel::onActiveDocument, this, sp::_1));
    conDelete = Application::Instance->signalDeleteDocument.connect(
        std::bind(&HistoryPanel::onDeleteDocument, this, sp::_1));
    // NOLINTEND

    auto guiDoc = Application::Instance->activeDocument();
    if (guiDoc && guiDoc->getDocument()) {
        setDocument(guiDoc->getDocument(), guiDoc);
    }
}

HistoryPanel::~HistoryPanel() = default;

void HistoryPanel::setupUi()
{
    auto layout = new QVBoxLayout(this);
    layout->setContentsMargins(0, 0, 0, 0);
    layout->setSpacing(0);

    // --- Toolbar area ---
    toolbar = new QToolBar(this);
    toolbar->setIconSize(QSize(16, 16));
    toolbar->setMovable(false);

    // Search box
    searchBox = new QLineEdit(this);
    searchBox->setPlaceholderText(tr("Search history..."));
    searchBox->setClearButtonEnabled(true);
    searchBox->setMaximumWidth(200);
    toolbar->addWidget(searchBox);
    toolbar->addSeparator();

    // Filter combo
    filterCombo = new QComboBox(this);
    filterCombo->addItem(tr("All Events"), -1);
    filterCombo->addItem(tr("Operations Only"), static_cast<int>(EntryType::Transaction));
    filterCombo->addItem(tr("Object Changes"), static_cast<int>(EntryType::ObjectCreated));
    filterCombo->addItem(tr("Undo/Redo"), static_cast<int>(EntryType::Undo));
    filterCombo->setMaximumWidth(140);
    toolbar->addWidget(filterCombo);
    toolbar->addSeparator();

    // Show undone checkbox
    showUndoneCheck = new QCheckBox(tr("Show undone"), this);
    showUndoneCheck->setChecked(true);
    toolbar->addWidget(showUndoneCheck);
    toolbar->addSeparator();

    // Toggle detail list visibility
    toggleListBtn = new QToolButton(this);
    toggleListBtn->setText(tr("Details"));
    toggleListBtn->setCheckable(true);
    toggleListBtn->setChecked(true);
    toggleListBtn->setToolTip(tr("Show/hide detail list view"));
    toolbar->addWidget(toggleListBtn);
    toolbar->addSeparator();

    // Export & Clear buttons
    exportBtn = new QPushButton(tr("Export"), this);
    exportBtn->setToolTip(tr("Export modification history to text file"));
    toolbar->addWidget(exportBtn);

    clearBtn = new QPushButton(tr("Clear"), this);
    clearBtn->setToolTip(tr("Clear modification history"));
    toolbar->addWidget(clearBtn);

    layout->addWidget(toolbar);

    // --- Horizontal Timeline Bar (Fusion 360 style) ---
    timelineBar = new TimelineBar(this);
    timelineBar->setModel(model);
    timelineBar->setFilterProxy(filterProxy);
    layout->addWidget(timelineBar);

    // --- Separator ---
    auto separator = new QFrame(this);
    separator->setFrameShape(QFrame::HLine);
    separator->setFrameShadow(QFrame::Sunken);
    layout->addWidget(separator);

    // --- Detail List view ---
    listView = new QListView(this);
    listView->setModel(filterProxy);
    listView->setItemDelegate(new HistoryDelegate(listView));
    listView->setSelectionMode(QAbstractItemView::SingleSelection);
    listView->setContextMenuPolicy(Qt::CustomContextMenu);
    listView->setMouseTracking(true);
    listView->setVerticalScrollMode(QAbstractItemView::ScrollPerPixel);
    listView->setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOff);

    listView->setStyleSheet(QStringLiteral(
        "QListView {"
        "  border: none;"
        "  background: palette(base);"
        "}"
        "QListView::item:hover {"
        "  background: palette(midlight);"
        "}"
        "QListView::item:selected {"
        "  background: palette(highlight);"
        "}"
    ));

    layout->addWidget(listView, 1);

    // --- Status bar ---
    statusLabel = new QLabel(this);
    statusLabel->setContentsMargins(8, 4, 8, 4);
    statusLabel->setStyleSheet(QStringLiteral(
        "QLabel {"
        "  color: palette(mid);"
        "  font-size: 10px;"
        "  border-top: 1px solid palette(mid);"
        "  background: palette(window);"
        "}"
    ));
    statusLabel->setText(tr("No document — Fusion 360-style Design History Timeline"));
    layout->addWidget(statusLabel);

    setLayout(layout);
}

void HistoryPanel::setupToolbar()
{
    // Already done in setupUi
}

void HistoryPanel::setupConnections()
{
    // Search
    connect(searchBox, &QLineEdit::textChanged,
            this, &HistoryPanel::onSearchChanged);

    // Filter combo
    connect(filterCombo, QOverload<int>::of(&QComboBox::currentIndexChanged),
            this, &HistoryPanel::onFilterChanged);

    // Show undone
    connect(showUndoneCheck, &QCheckBox::toggled, this, [this](bool checked) {
        filterProxy->setShowUndone(checked);
        updateStatus();
    });

    // Toggle detail list
    connect(toggleListBtn, &QToolButton::toggled, this, [this](bool checked) {
        listView->setVisible(checked);
        listViewVisible = checked;
    });

    // Export
    connect(exportBtn, &QPushButton::clicked, this, &HistoryPanel::onExportClicked);

    // Clear
    connect(clearBtn, &QPushButton::clicked, this, &HistoryPanel::onClearClicked);

    // List view double-click
    connect(listView, &QListView::doubleClicked,
            this, &HistoryPanel::onEntryDoubleClicked);

    // List view single-click — highlight object in 3D view
    connect(listView, &QListView::clicked,
            this, &HistoryPanel::onEntryClicked);

    // List view context menu
    connect(listView, &QListView::customContextMenuRequested,
            this, &HistoryPanel::onEntryContextMenu);

    // Timeline bar signals
    connect(timelineBar, &TimelineBar::featureClicked,
            this, &HistoryPanel::onTimelineClicked);
    connect(timelineBar, &TimelineBar::featureDoubleClicked,
            this, &HistoryPanel::onTimelineDoubleClicked);
    connect(timelineBar, &TimelineBar::featureContextMenu,
            this, &HistoryPanel::onTimelineContextMenu);
    connect(timelineBar, &TimelineBar::rollbackDragged,
            this, &HistoryPanel::onTimelineRollbackDragged);

    // Entry added — auto-scroll to bottom
    connect(model, &HistoryModel::entryAdded,
            this, &HistoryPanel::onEntryAdded);

    // Model changes — update status
    connect(model, &QAbstractItemModel::rowsInserted, this, [this]() {
        updateStatus();
    });
    connect(model, &QAbstractItemModel::modelReset, this, [this]() {
        updateStatus();
    });
}

void HistoryPanel::setDocument(const App::Document* doc, const Gui::Document* guiDoc)
{
    model->setDocument(doc, guiDoc);
    updateStatus();
}

void HistoryPanel::updateStatus()
{
    int total = model->rowCount();
    int shown = filterProxy->rowCount();
    QString docName;
    if (model->document()) {
        docName = QString::fromUtf8(model->document()->Label.getValue());
    }

    if (docName.isEmpty()) {
        statusLabel->setText(tr("No document — Fusion 360-style Design History Timeline"));
    }
    else if (total == shown) {
        statusLabel->setText(tr("📋 %1 — %2 entries | Scroll: mouse wheel | Zoom: Ctrl+wheel | Edit: double-click")
                                 .arg(docName).arg(total));
    }
    else {
        statusLabel->setText(tr("📋 %1 — %2 of %3 entries shown")
                                 .arg(docName).arg(shown).arg(total));
    }
}

// ============================================================================
// Slots
// ============================================================================

void HistoryPanel::onActiveDocument(const Gui::Document& doc)
{
    auto appDoc = doc.getDocument();
    if (appDoc != model->document()) {
        setDocument(appDoc, &doc);
    }
}

void HistoryPanel::onDeleteDocument(const Gui::Document& doc)
{
    if (doc.getDocument() == model->document()) {
        model->detachDocument();
        updateStatus();
    }
}

void HistoryPanel::onEntryClicked(const QModelIndex& proxyIndex)
{
    QModelIndex srcIndex = filterProxy->mapToSource(proxyIndex);
    QString objName = model->data(srcIndex, ObjectNameRole).toString();
    highlightObjectInView(objName);
}

void HistoryPanel::onTimelineClicked(int sourceIndex)
{
    if (sourceIndex < 0 || sourceIndex >= model->rowCount()) {
        return;
    }
    QModelIndex idx = model->index(sourceIndex, 0);
    QString objName = model->data(idx, ObjectNameRole).toString();
    highlightObjectInView(objName);
}

void HistoryPanel::highlightObjectInView(const QString& objectName)
{
    if (objectName.isEmpty()) {
        return;
    }

    const App::Document* appDoc = model->document();
    if (!appDoc) {
        return;
    }

    auto obj = appDoc->getObject(objectName.toLatin1().constData());
    if (!obj) {
        return;
    }

    // Clear previous selection and select this object
    const char* docName = appDoc->getName();
    Gui::Selection().clearSelection(docName);
    Gui::Selection().addSelection(docName, obj->getNameInDocument());

    // Zoom the 3D view to fit the selected object
    auto* guiApp = Gui::Application::Instance;
    if (guiApp) {
        auto* mdiView = guiApp->activeView();
        auto* view3d = qobject_cast<Gui::View3DInventor*>(mdiView);
        if (view3d) {
            auto* viewer = view3d->getViewer();
            if (viewer) {
                viewer->viewSelection();
            }
        }
    }
}

void HistoryPanel::onEntryDoubleClicked(const QModelIndex& proxyIndex)
{
    QModelIndex srcIndex = filterProxy->mapToSource(proxyIndex);
    int srcRow = srcIndex.row();

    // Try to edit the feature first (Fusion 360 primary action)
    QString objName = model->data(srcIndex, ObjectNameRole).toString();
    if (!objName.isEmpty()) {
        if (model->editFeature(srcRow)) {
            return;  // Successfully opened edit dialog
        }
    }

    // Fallback: rollback
    int transId = model->data(srcIndex, TransactionIdRole).toInt();
    if (transId <= 0) {
        return;
    }

    int reply = QMessageBox::question(
        this,
        tr("Rollback to this point?"),
        tr("This will undo all operations after this point.\n"
           "Are you sure you want to rollback to:\n\n%1")
            .arg(model->data(srcIndex, DescriptionRole).toString()),
        QMessageBox::Yes | QMessageBox::No,
        QMessageBox::No);

    if (reply == QMessageBox::Yes) {
        model->rollbackTo(srcRow);
    }
}

void HistoryPanel::onTimelineDoubleClicked(int sourceIndex)
{
    // Try edit feature first (Fusion 360 behavior)
    if (model->editFeature(sourceIndex)) {
        return;
    }

    // Fallback to rollback
    if (sourceIndex >= 0 && sourceIndex < model->rowCount()) {
        int transId = model->entries()[sourceIndex].transactionId;
        if (transId > 0) {
            model->rollbackTo(sourceIndex);
        }
    }
}

void HistoryPanel::onTimelineContextMenu(int sourceIndex, const QPoint& globalPos)
{
    showContextMenu(sourceIndex, globalPos);
}

void HistoryPanel::onTimelineRollbackDragged(int sourceIndex)
{
    // Draggable rollback marker — Fusion 360's key interaction
    if (sourceIndex >= 0 && sourceIndex < model->rowCount()) {
        const auto& entry = model->entries()[sourceIndex];
        if (entry.transactionId > 0) {
            model->rollbackTo(sourceIndex);
        }
    }
}

void HistoryPanel::onEntryContextMenu(const QPoint& pos)
{
    QModelIndex proxyIndex = listView->indexAt(pos);
    if (!proxyIndex.isValid()) {
        return;
    }

    QModelIndex srcIndex = filterProxy->mapToSource(proxyIndex);
    showContextMenu(srcIndex.row(), listView->viewport()->mapToGlobal(pos));
}

void HistoryPanel::showContextMenu(int sourceRow, const QPoint& globalPos)
{
    if (sourceRow < 0 || sourceRow >= model->rowCount()) {
        return;
    }

    QModelIndex srcIndex = model->index(sourceRow, 0);
    QString description = model->data(srcIndex, DescriptionRole).toString();
    QString objName = model->data(srcIndex, ObjectNameRole).toString();
    int transId = model->data(srcIndex, TransactionIdRole).toInt();
    bool isSuppressed = model->data(srcIndex, IsSuppressedRole).toBool();

    QMenu menu(this);

    // --- Edit Feature (Fusion 360 primary action) ---
    if (!objName.isEmpty() && model->document()) {
        auto obj = model->document()->getObject(objName.toLatin1().constData());
        if (obj) {
            auto editAction = menu.addAction(tr("✏️ Edit Feature"));
            editAction->setToolTip(tr("Open the feature's parameter dialog"));
            connect(editAction, &QAction::triggered, this, [this, sourceRow]() {
                model->editFeature(sourceRow);
            });

            menu.addSeparator();

            // --- Suppress/Unsuppress (Fusion 360 key feature) ---
            auto ext = obj->getExtensionByType<App::SuppressibleExtension>(true);
            if (ext) {
                QString suppressText = isSuppressed
                    ? tr("✅ Unsuppress Feature")
                    : tr("⊘ Suppress Feature");
                auto suppressAction = menu.addAction(suppressText);
                connect(suppressAction, &QAction::triggered, this, [this, sourceRow]() {
                    model->toggleSuppressed(sourceRow);
                });
            }

            // --- Select in Tree ---
            auto selectAction = menu.addAction(tr("🔍 Find in Model Tree"));
            connect(selectAction, &QAction::triggered, this, [obj]() {
                Gui::Selection().clearSelection();
                Gui::Selection().addSelection(obj->getDocument()->getName(),
                                              obj->getNameInDocument());
            });

            menu.addSeparator();
        }
    }

    // --- Copy description ---
    auto copyAction = menu.addAction(tr("📋 Copy Description"));
    connect(copyAction, &QAction::triggered, this, [description]() {
        QApplication::clipboard()->setText(description);
    });

    // --- Rollback ---
    if (transId > 0) {
        menu.addSeparator();
        auto rollbackAction = menu.addAction(tr("⏪ Rollback to this point"));
        connect(rollbackAction, &QAction::triggered, this, [this, sourceRow]() {
            int reply = QMessageBox::question(
                this,
                tr("Rollback to this point?"),
                tr("This will undo all operations after this point.\nContinue?"),
                QMessageBox::Yes | QMessageBox::No, QMessageBox::No);
            if (reply == QMessageBox::Yes) {
                model->rollbackTo(sourceRow);
            }
        });
    }

    // --- Grouping ---
    int groupId = model->data(srcIndex, GroupIdRole).toInt();
    menu.addSeparator();
    if (groupId >= 0) {
        auto ungroupAction = menu.addAction(tr("📂 Ungroup"));
        connect(ungroupAction, &QAction::triggered, this, [this, groupId]() {
            model->removeGroup(groupId);
        });
    }
    else {
        auto groupAction = menu.addAction(tr("📁 Create Group..."));
        groupAction->setToolTip(tr("Group this and adjacent entries together"));
        connect(groupAction, &QAction::triggered, this, [this, sourceRow]() {
            bool ok;
            QString name = QInputDialog::getText(
                this, tr("Group Name"),
                tr("Enter a name for the feature group:"),
                QLineEdit::Normal, tr("Feature Group"), &ok);
            if (ok && !name.isEmpty()) {
                // Group a range of 3 entries centered on this one
                int start = qMax(0, sourceRow - 1);
                int end = qMin(model->rowCount() - 1, sourceRow + 1);
                model->createGroup(name, start, end);
            }
        });
    }

    menu.exec(globalPos);
}

void HistoryPanel::onEntryAdded(int /*index*/)
{
    QScrollBar* sb = listView->verticalScrollBar();
    if (sb) {
        int maxVal = sb->maximum();
        if (sb->value() >= maxVal - 50) {
            listView->scrollToBottom();
        }
    }
}

void HistoryPanel::onFilterChanged()
{
    int filterType = filterCombo->currentData().toInt();

    QSet<int> types;
    if (filterType == -1) {
        for (int i = 0; i <= static_cast<int>(EntryType::RollbackMarker); ++i) {
            types.insert(i);
        }
    }
    else if (filterType == static_cast<int>(EntryType::Transaction)) {
        types.insert(static_cast<int>(EntryType::Transaction));
    }
    else if (filterType == static_cast<int>(EntryType::ObjectCreated)) {
        types.insert(static_cast<int>(EntryType::ObjectCreated));
        types.insert(static_cast<int>(EntryType::ObjectDeleted));
        types.insert(static_cast<int>(EntryType::ObjectModified));
    }
    else if (filterType == static_cast<int>(EntryType::Undo)) {
        types.insert(static_cast<int>(EntryType::Undo));
        types.insert(static_cast<int>(EntryType::Redo));
    }

    filterProxy->setVisibleTypes(types);
    updateStatus();
}

void HistoryPanel::onSearchChanged(const QString& text)
{
    filterProxy->setFilterText(text);
    updateStatus();
}

void HistoryPanel::onExportClicked()
{
    QString text = model->exportToText();
    if (text.isEmpty()) {
        return;
    }

    QString filePath = QFileDialog::getSaveFileName(
        this,
        tr("Export Modification History"),
        QStringLiteral("freecad_history.txt"),
        tr("Text files (*.txt);;All files (*.*)"));

    if (filePath.isEmpty()) {
        return;
    }

    QFile file(filePath);
    if (file.open(QIODevice::WriteOnly | QIODevice::Text)) {
        QTextStream stream(&file);
        stream << text;
        file.close();
        statusLabel->setText(tr("History exported to %1").arg(filePath));
    }
    else {
        QMessageBox::warning(this, tr("Export Failed"),
                             tr("Could not write to file:\n%1").arg(filePath));
    }
}

void HistoryPanel::onClearClicked()
{
    int reply = QMessageBox::question(
        this,
        tr("Clear History?"),
        tr("This will clear the modification history display.\n"
           "It does NOT affect the undo/redo stack.\n\n"
           "Continue?"),
        QMessageBox::Yes | QMessageBox::No,
        QMessageBox::No);

    if (reply == QMessageBox::Yes) {
        model->clear();
        updateStatus();
    }
}


// ============================================================================
// DockWindow
// ============================================================================

DockWindow::DockWindow(Gui::Document* gDocumentIn, QWidget* parent)
    : Gui::DockWindow(gDocumentIn, parent)
{
    panel = new HistoryPanel(this);
    auto layout = new QVBoxLayout();
    layout->setContentsMargins(0, 0, 0, 0);
    layout->addWidget(panel);
    this->setLayout(layout);
}
