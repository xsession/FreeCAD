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
#include <QLinearGradient>
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
// TimelineBar — Autodesk Inventor-style horizontal timeline
// ============================================================================

TimelineBar::TimelineBar(QWidget* parent)
    : QWidget(parent)
{
    setMinimumHeight(BarHeight);
    setMaximumHeight(BarHeight);
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
    return QSize(600, BarHeight);
}

QSize TimelineBar::minimumSizeHint() const
{
    return QSize(100, BarHeight);
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

QRect TimelineBar::cellRect(int visibleIndex) const
{
    int cx = LeftMargin + visibleIndex * cellSpacing - scrollOffset;
    return QRect(cx - cellSize / 2, CellY, cellSize, cellSize);
}

QRect TimelineBar::endOfPartRect() const
{
    int rbIdx = rollbackVisibleIndex();
    if (rbIdx < 0) {
        return {};
    }
    // End-of-Part marker sits right after the rollback cell
    int x = LeftMargin + rbIdx * cellSpacing - scrollOffset + cellSize / 2 + 6;
    return QRect(x - MarkerWidth / 2, 2, MarkerWidth, BarHeight - 4);
}

int TimelineBar::cellAtPos(const QPoint& pos) const
{
    int count = filterProxy ? filterProxy->rowCount() : (histModel ? histModel->rowCount() : 0);
    for (int i = 0; i < count; ++i) {
        QRect r = cellRect(i);
        r.adjust(-4, -4, 4, 4);  // expand hit area slightly
        if (r.contains(pos)) {
            return i;
        }
    }
    return -1;
}

void TimelineBar::scrollToEnd()
{
    int count = filterProxy ? filterProxy->rowCount() : (histModel ? histModel->rowCount() : 0);
    int totalWidth = LeftMargin * 2 + count * cellSpacing;
    int maxScroll = qMax(0, totalWidth - width());
    scrollOffset = maxScroll;
}

void TimelineBar::paintEvent(QPaintEvent* /*event*/)
{
    QPainter p(this);
    p.setRenderHint(QPainter::Antialiasing, true);

    int w = width();

    // --- Background: Inventor-style warm gray gradient ---
    QLinearGradient bgGrad(0, 0, 0, BarHeight);
    bgGrad.setColorAt(0.0, QColor(0xEA, 0xEA, 0xEA));
    bgGrad.setColorAt(0.3, QColor(0xE0, 0xE0, 0xE0));
    bgGrad.setColorAt(1.0, QColor(0xD0, 0xD0, 0xD0));
    p.fillRect(rect(), bgGrad);

    // Top edge highlight + bottom edge shadow (toolbar feel)
    p.setPen(QPen(QColor(0xF4, 0xF4, 0xF4), 1));
    p.drawLine(0, 0, w, 0);
    p.setPen(QPen(QColor(0xA0, 0xA0, 0xA0), 1));
    p.drawLine(0, BarHeight - 1, w, BarHeight - 1);

    int count = filterProxy ? filterProxy->rowCount() : (histModel ? histModel->rowCount() : 0);
    if (count == 0) {
        p.setPen(QColor(0x80, 0x80, 0x80));
        QFont f = font();
        f.setItalic(true);
        p.setFont(f);
        p.drawText(rect(), Qt::AlignCenter, tr("No history — Inventor Timeline"));
        return;
    }

    // --- Horizontal rail/track ---
    int rbVisIdx = rollbackVisibleIndex();
    int railStartX = LeftMargin - scrollOffset - cellSpacing / 2;
    int railEndX = LeftMargin + (count - 1) * cellSpacing - scrollOffset + cellSpacing / 2;

    // Active portion (before End-of-Part)
    int activeEndX = (rbVisIdx >= 0)
        ? LeftMargin + rbVisIdx * cellSpacing - scrollOffset + cellSize / 2 + 4
        : railEndX;

    p.setPen(QPen(QColor(0x90, 0x90, 0x90), 2));
    p.drawLine(qMax(0, railStartX), RailY, qMin(w, activeEndX), RailY);

    // Inactive portion (past End-of-Part) — dashed
    if (rbVisIdx >= 0 && rbVisIdx < count - 1) {
        QPen dashPen(QColor(0xA8, 0xA8, 0xA8), 1, Qt::DashLine);
        p.setPen(dashPen);
        p.drawLine(qMin(w, activeEndX), RailY,
                   qMin(w, railEndX), RailY);
    }

    // --- Group brackets ---
    if (histModel) {
        const auto& groups = histModel->groups();
        for (const auto& group : groups) {
            if (group.collapsed) {
                continue;
            }
            int startVis = sourceToVisible(group.startIndex);
            int endVis = sourceToVisible(group.endIndex);
            if (startVis < 0 || endVis < 0) {
                continue;
            }

            int gx1 = LeftMargin + startVis * cellSpacing - scrollOffset - cellSize / 2 - 2;
            int gx2 = LeftMargin + endVis * cellSpacing - scrollOffset + cellSize / 2 + 2;
            int gy = CellY - 3;

            // Bracket line
            p.setPen(QPen(QColor(0x60, 0x60, 0x60), 1));
            p.drawLine(gx1, gy, gx2, gy);
            p.drawLine(gx1, gy, gx1, gy + 4);
            p.drawLine(gx2, gy, gx2, gy + 4);

            // Group name label centered above bracket
            QFont gf = font();
            gf.setPointSize(gf.pointSize() - 3);
            gf.setBold(true);
            p.setFont(gf);
            p.setPen(QColor(0x50, 0x50, 0x50));
            // no room above; skip if cramped
        }
    }

    // --- Feature cells ---
    for (int i = 0; i < count; ++i) {
        QRect cr = cellRect(i);

        // Skip if off-screen
        if (cr.right() < -cellSize || cr.left() > w + cellSize) {
            continue;
        }

        QModelIndex idx = filterProxy
            ? filterProxy->index(i, 0)
            : histModel->index(i, 0);

        bool isUndone = idx.data(IsUndoneRole).toBool();
        bool isRollbackTarget = idx.data(IsRollbackTargetRole).toBool();
        bool isSuppressed = idx.data(IsSuppressedRole).toBool();
        bool isCheckpoint = idx.data(IsCheckpointRole).toBool();
        QColor familyColor = idx.data(ColorRole).value<QColor>();
        QIcon icon = idx.data(Qt::DecorationRole).value<QIcon>();

        // --- Cell background ---
        QColor cellBg(0xF8, 0xF8, 0xF8);
        if (i == selectedCell) {
            cellBg = QColor(0xD6, 0xE8, 0xFF);  // light blue selection
        }
        else if (i == hoveredCell) {
            cellBg = QColor(0xEE, 0xEE, 0xEE);
        }
        if (isUndone) {
            cellBg.setAlpha(120);
        }
        if (isCheckpoint) {
            cellBg = QColor(0xE8, 0xF5, 0xE9); // faint green
        }

        // --- Cell border ---
        QPen borderPen(familyColor, 1.5);
        if (i == selectedCell) {
            borderPen = QPen(QColor(0x21, 0x96, 0xF3), 2.5);  // blue selected
        }
        else if (i == hoveredCell) {
            borderPen = QPen(familyColor.lighter(120), 2.0);
        }
        if (isUndone) {
            borderPen.setColor(QColor(0xB0, 0xB0, 0xB0));
        }
        if (isSuppressed) {
            borderPen.setColor(QColor(0xF4, 0x43, 0x36));
            borderPen.setStyle(Qt::DashLine);
        }

        // Hover glow effect (Inventor highlight)
        if (i == hoveredCell && !isUndone) {
            QColor glow = familyColor;
            glow.setAlpha(30);
            QRect glowR = cr.adjusted(-3, -3, 3, 3);
            p.setPen(Qt::NoPen);
            p.setBrush(glow);
            p.drawRoundedRect(glowR, 5, 5);
        }

        // Selected glow
        if (i == selectedCell && !isUndone) {
            QColor selGlow(0x21, 0x96, 0xF3, 40);
            QRect selR = cr.adjusted(-4, -4, 4, 4);
            p.setPen(Qt::NoPen);
            p.setBrush(selGlow);
            p.drawRoundedRect(selR, 6, 6);
        }

        // Draw cell rectangle
        p.setPen(borderPen);
        p.setBrush(cellBg);
        if (isCheckpoint) {
            // Checkpoint: render as rotated diamond
            p.save();
            p.translate(cr.center());
            p.rotate(45);
            int sz = cellSize * 2 / 3;
            QRect dRect(-sz / 2, -sz / 2, sz, sz);
            p.drawRect(dRect);
            p.restore();
        }
        else {
            p.drawRoundedRect(cr, 4, 4);
        }

        // Color tint strip at bottom of cell (2px, family color)
        if (!isCheckpoint) {
            QRect tintR(cr.left() + 1, cr.bottom() - 2, cr.width() - 2, 2);
            QColor tint = familyColor;
            if (isUndone) {
                tint.setAlpha(60);
            }
            p.setPen(Qt::NoPen);
            p.setBrush(tint);
            p.drawRect(tintR);
        }

        // --- Icon centered in cell ---
        if (!icon.isNull()) {
            QIcon::Mode mode = isUndone ? QIcon::Disabled : QIcon::Normal;
            QRect iconR = cr.adjusted(5, 5, -5, -5);
            icon.paint(&p, iconR, Qt::AlignCenter, mode);
        }

        // --- Suppressed X overlay ---
        if (isSuppressed) {
            p.setPen(QPen(QColor(0xF4, 0x43, 0x36, 200), 2));
            p.drawLine(cr.topLeft() + QPoint(4, 4),
                       cr.bottomRight() - QPoint(4, 4));
            p.drawLine(cr.topRight() + QPoint(-4, 4),
                       cr.bottomLeft() + QPoint(4, -4));
        }

        // --- Connection tick from cell to rail ---
        int cx = cr.center().x();
        if (!isCheckpoint) {
            QColor tickColor = isUndone ? QColor(0xB0, 0xB0, 0xB0)
                                        : QColor(0x90, 0x90, 0x90);
            p.setPen(QPen(tickColor, 1));
            // small vertical tick from cell bottom to rail
            if (cr.bottom() < RailY) {
                p.drawLine(cx, cr.bottom(), cx, RailY);
            }
        }

        // --- Feature label below the rail ---
        QString featureLabel = idx.data(FeatureLabelRole).toString();
        if (!featureLabel.isEmpty()) {
            QFont lf = font();
            lf.setPointSize(lf.pointSize() - 2);
            if (isRollbackTarget || i == selectedCell) {
                lf.setBold(true);
            }
            if (isSuppressed || isUndone) {
                lf.setStrikeOut(true);
            }
            p.setFont(lf);

            QColor textCol = isUndone ? QColor(0x90, 0x90, 0x90)
                           : isSuppressed ? QColor(0xA0, 0x60, 0x60)
                           : QColor(0x40, 0x40, 0x40);
            p.setPen(textCol);

            QFontMetrics fm(lf);
            QString elided = fm.elidedText(featureLabel, Qt::ElideRight, cellSpacing - 6);
            QRect textRect(cx - cellSpacing / 2, LabelY, cellSpacing, 16);
            p.drawText(textRect, Qt::AlignHCenter | Qt::AlignTop, elided);
        }
    }

    // --- End-of-Part marker (Inventor gold vertical bar) ---
    int markerVisIdx = (draggingMarker && dragTargetCell >= 0)
                           ? dragTargetCell
                           : rollbackVisibleIndex();
    if (markerVisIdx >= 0) {
        int mx = LeftMargin + markerVisIdx * cellSpacing - scrollOffset + cellSize / 2 + 6;

        // Vertical bar
        QLinearGradient markerGrad(mx - MarkerWidth / 2, 0, mx + MarkerWidth / 2, 0);
        QColor markerBase = draggingMarker ? QColor(0xFF, 0x80, 0x00) : QColor(0xFF, 0xA0, 0x00);
        markerGrad.setColorAt(0.0, markerBase.lighter(130));
        markerGrad.setColorAt(0.5, markerBase);
        markerGrad.setColorAt(1.0, markerBase.darker(115));
        p.setPen(QPen(markerBase.darker(130), 1));
        p.setBrush(markerGrad);

        QRect barR(mx - MarkerWidth / 2, 4, MarkerWidth, BarHeight - 8);
        p.drawRoundedRect(barR, 2, 2);

        // Small triangle handle at top
        QPainterPath tri;
        tri.moveTo(mx, 0);
        tri.lineTo(mx - 6, -1);
        tri.lineTo(mx + 6, -1);
        tri.closeSubpath();
        // Actually draw it pointing down at the top of bar
        QPainterPath topTri;
        topTri.moveTo(mx, 4);
        topTri.lineTo(mx - 5, 0);
        topTri.lineTo(mx + 5, 0);
        topTri.closeSubpath();
        p.setPen(Qt::NoPen);
        p.setBrush(markerBase);
        p.drawPath(topTri);

        // Bottom triangle handle
        QPainterPath botTri;
        botTri.moveTo(mx, BarHeight - 4);
        botTri.lineTo(mx - 5, BarHeight);
        botTri.lineTo(mx + 5, BarHeight);
        botTri.closeSubpath();
        p.drawPath(botTri);

        // "End of Part" label
        QFont mf = font();
        mf.setPointSize(mf.pointSize() - 3);
        mf.setItalic(true);
        p.setFont(mf);
        p.setPen(markerBase.darker(140));
        QRect labelR(mx - 30, BarHeight - 14, 60, 12);
        // Only draw if there's space (not overlapping cells)
        if (markerVisIdx == count - 1 || cellSpacing > 55) {
            // skip label to avoid clutter in tight layouts
        }
    }

    // --- Scroll indicators (left / right arrows) ---
    if (scrollOffset > 0) {
        // Left fade + arrow
        QLinearGradient leftFade(0, 0, 24, 0);
        leftFade.setColorAt(0.0, QColor(0xD0, 0xD0, 0xD0, 200));
        leftFade.setColorAt(1.0, QColor(0xD0, 0xD0, 0xD0, 0));
        p.fillRect(0, 0, 24, BarHeight, leftFade);

        p.setPen(Qt::NoPen);
        p.setBrush(QColor(0x60, 0x60, 0x60));
        QPainterPath leftArr;
        leftArr.moveTo(10, RailY);
        leftArr.lineTo(4, RailY - 5);
        leftArr.lineTo(4, RailY + 5);
        leftArr.closeSubpath();
        p.drawPath(leftArr);
    }

    int totalWidth = LeftMargin * 2 + count * cellSpacing;
    if (scrollOffset < totalWidth - w) {
        // Right fade + arrow
        QLinearGradient rightFade(w - 24, 0, w, 0);
        rightFade.setColorAt(0.0, QColor(0xD0, 0xD0, 0xD0, 0));
        rightFade.setColorAt(1.0, QColor(0xD0, 0xD0, 0xD0, 200));
        p.fillRect(w - 24, 0, 24, BarHeight, rightFade);

        p.setPen(Qt::NoPen);
        p.setBrush(QColor(0x60, 0x60, 0x60));
        QPainterPath rightArr;
        rightArr.moveTo(w - 10, RailY);
        rightArr.lineTo(w - 4, RailY - 5);
        rightArr.lineTo(w - 4, RailY + 5);
        rightArr.closeSubpath();
        p.drawPath(rightArr);
    }
}


// ============================================================================
// TimelineBar — Mouse interaction
// ============================================================================

void TimelineBar::mousePressEvent(QMouseEvent* event)
{
    if (event->button() == Qt::LeftButton) {
        // Check if pressing on End-of-Part marker
        QRect eopRect = endOfPartRect();
        if (eopRect.isValid() && eopRect.adjusted(-4, 0, 4, 0).contains(event->pos())) {
            draggingMarker = true;
            dragTargetCell = rollbackVisibleIndex();
            setCursor(Qt::SizeHorCursor);
            event->accept();
            return;
        }

        int cell = cellAtPos(event->pos());
        if (cell >= 0) {
            selectedCell = cell;
            update();
            int srcIdx = visibleToSource(cell);
            Q_EMIT featureClicked(srcIdx);
        }
    }
    else if (event->button() == Qt::RightButton) {
        int cell = cellAtPos(event->pos());
        if (cell >= 0) {
            selectedCell = cell;
            update();
            int srcIdx = visibleToSource(cell);
            Q_EMIT featureContextMenu(srcIdx, event->globalPos());
        }
    }
    QWidget::mousePressEvent(event);
}

void TimelineBar::mouseMoveEvent(QMouseEvent* event)
{
    if (draggingMarker) {
        // Find nearest cell to cursor X
        int count = filterProxy ? filterProxy->rowCount()
                                : (histModel ? histModel->rowCount() : 0);
        int bestDist = INT_MAX;
        int bestCell = -1;
        for (int i = 0; i < count; ++i) {
            QRect r = cellRect(i);
            int dist = qAbs(r.center().x() - event->pos().x());
            if (dist < bestDist) {
                bestDist = dist;
                bestCell = i;
            }
        }
        if (bestCell >= 0 && bestCell != dragTargetCell) {
            dragTargetCell = bestCell;
            update();
        }
        event->accept();
        return;
    }

    int cell = cellAtPos(event->pos());
    if (cell != hoveredCell) {
        hoveredCell = cell;
        update();
    }

    // Change cursor for End-of-Part marker
    QRect eopRect = endOfPartRect();
    if (eopRect.isValid() && eopRect.adjusted(-4, 0, 4, 0).contains(event->pos())) {
        setCursor(Qt::SizeHorCursor);
    }
    else {
        setCursor(Qt::ArrowCursor);
    }

    QWidget::mouseMoveEvent(event);
}

void TimelineBar::mouseReleaseEvent(QMouseEvent* event)
{
    if (draggingMarker && event->button() == Qt::LeftButton) {
        draggingMarker = false;
        setCursor(Qt::ArrowCursor);

        if (dragTargetCell >= 0) {
            int srcIdx = visibleToSource(dragTargetCell);
            Q_EMIT rollbackDragged(srcIdx);
        }
        dragTargetCell = -1;
        update();
        event->accept();
        return;
    }
    QWidget::mouseReleaseEvent(event);
}

void TimelineBar::mouseDoubleClickEvent(QMouseEvent* event)
{
    if (event->button() == Qt::LeftButton) {
        int cell = cellAtPos(event->pos());
        if (cell >= 0) {
            int srcIdx = visibleToSource(cell);
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
        // Zoom: adjust cell spacing
        int delta = event->angleDelta().y();
        if (delta > 0) {
            cellSpacing = qMin(cellSpacing + 4, MaxCellSpacing);
        }
        else if (delta < 0) {
            cellSpacing = qMax(cellSpacing - 4, MinCellSpacing);
        }
        update();
        event->accept();
        return;
    }

    // Horizontal scroll
    int delta = event->angleDelta().y();
    int count = filterProxy ? filterProxy->rowCount()
                            : (histModel ? histModel->rowCount() : 0);
    int totalWidth = LeftMargin * 2 + count * cellSpacing;
    int maxScroll = qMax(0, totalWidth - width());

    scrollOffset = qBound(0, scrollOffset - delta, maxScroll);
    update();
    event->accept();
}

void TimelineBar::resizeEvent(QResizeEvent* event)
{
    QWidget::resizeEvent(event);
    int count = filterProxy ? filterProxy->rowCount()
                            : (histModel ? histModel->rowCount() : 0);
    int totalWidth = LeftMargin * 2 + count * cellSpacing;
    int maxScroll = qMax(0, totalWidth - width());
    scrollOffset = qMin(scrollOffset, maxScroll);
}

bool TimelineBar::event(QEvent* event)
{
    if (event->type() == QEvent::ToolTip) {
        auto helpEvent = static_cast<QHelpEvent*>(event);
        int cell = cellAtPos(helpEvent->pos());
        if (cell >= 0) {
            QModelIndex idx = filterProxy
                ? filterProxy->index(cell, 0)
                : histModel->index(cell, 0);
            QString tip = idx.data(Qt::ToolTipRole).toString();
            QToolTip::showText(helpEvent->globalPos(), tip, this);
        }
        else {
            // Check if over End-of-Part marker
            QRect eopRect = endOfPartRect();
            if (eopRect.isValid() && eopRect.adjusted(-4, 0, 4, 0).contains(helpEvent->pos())) {
                QToolTip::showText(helpEvent->globalPos(),
                                   tr("End of Part — drag to rollback/roll-forward"), this);
            }
            else {
                QToolTip::hideText();
            }
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
    for (int i = 0; i <= static_cast<int>(EntryType::Checkpoint); ++i) {
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
// HistoryPanel — Inventor-style compact timeline panel
// ============================================================================

HistoryPanel::HistoryPanel(QWidget* parent)
    : QWidget(parent)
{
    model = new HistoryModel(this);
    filterProxy = new HistoryFilterProxy(this);
    filterProxy->setSourceModel(model);

    setupUi();
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

    // Inventor Timeline is just the horizontal bar — no toolbar, no list
    timelineBar = new TimelineBar(this);
    timelineBar->setModel(model);
    timelineBar->setFilterProxy(filterProxy);
    layout->addWidget(timelineBar);

    setLayout(layout);
}

void HistoryPanel::setupConnections()
{
    // Timeline bar signals
    connect(timelineBar, &TimelineBar::featureClicked,
            this, &HistoryPanel::onTimelineClicked);
    connect(timelineBar, &TimelineBar::featureDoubleClicked,
            this, &HistoryPanel::onTimelineDoubleClicked);
    connect(timelineBar, &TimelineBar::featureContextMenu,
            this, &HistoryPanel::onTimelineContextMenu);
    connect(timelineBar, &TimelineBar::rollbackDragged,
            this, &HistoryPanel::onTimelineRollbackDragged);
}

void HistoryPanel::setDocument(const App::Document* doc, const Gui::Document* guiDoc)
{
    model->setDocument(doc, guiDoc);
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
    }
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

    const char* docName = appDoc->getName();
    Gui::Selection().clearSelection(docName);
    Gui::Selection().addSelection(docName, obj->getNameInDocument());

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

void HistoryPanel::onTimelineDoubleClicked(int sourceIndex)
{
    // Check if this is a checkpoint — restore it
    if (sourceIndex >= 0 && sourceIndex < model->rowCount()) {
        const auto& entry = model->entries()[sourceIndex];
        if (entry.type == EntryType::Checkpoint && entry.checkpointId >= 0) {
            int reply = QMessageBox::question(
                this,
                tr("Restore Checkpoint?"),
                tr("Restore document to checkpoint:\n\n%1\n\n"
                   "This will replace the current document state.")
                    .arg(entry.transactionName),
                QMessageBox::Yes | QMessageBox::No,
                QMessageBox::No);
            if (reply == QMessageBox::Yes) {
                model->restoreCheckpoint(sourceIndex);
            }
            return;
        }
    }

    // Try edit feature (Inventor: double-click opens edit dialog)
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
    // Draggable End-of-Part marker — Inventor's key timeline interaction
    if (sourceIndex >= 0 && sourceIndex < model->rowCount()) {
        const auto& entry = model->entries()[sourceIndex];
        if (entry.transactionId > 0) {
            model->rollbackTo(sourceIndex);
        }
    }
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

    // --- Checkpoint-specific actions ---
    bool isCheckpoint = model->data(srcIndex, IsCheckpointRole).toBool();
    int checkpointId = model->data(srcIndex, CheckpointIdRole).toInt();
    if (isCheckpoint && checkpointId >= 0) {
        auto restoreAction = menu.addAction(tr("Restore Checkpoint"));
        connect(restoreAction, &QAction::triggered, this, [this, sourceRow]() {
            int reply = QMessageBox::question(
                this, tr("Restore Checkpoint?"),
                tr("Restore document to this checkpoint?\n\n"
                   "Current unsaved changes will be lost."),
                QMessageBox::Yes | QMessageBox::No, QMessageBox::No);
            if (reply == QMessageBox::Yes) {
                model->restoreCheckpoint(sourceRow);
            }
        });

        auto renameAction = menu.addAction(tr("Rename Checkpoint..."));
        connect(renameAction, &QAction::triggered, this, [this, sourceRow, description]() {
            bool ok;
            QString newName = QInputDialog::getText(
                this, tr("Rename Checkpoint"),
                tr("Enter new name:"),
                QLineEdit::Normal, description, &ok);
            if (ok && !newName.isEmpty()) {
                model->renameCheckpoint(sourceRow, newName);
            }
        });

        auto deleteAction = menu.addAction(tr("Delete Checkpoint"));
        connect(deleteAction, &QAction::triggered, this, [this, sourceRow]() {
            int reply = QMessageBox::question(
                this, tr("Delete Checkpoint?"),
                tr("This will permanently delete this checkpoint.\nContinue?"),
                QMessageBox::Yes | QMessageBox::No, QMessageBox::No);
            if (reply == QMessageBox::Yes) {
                model->deleteCheckpoint(sourceRow);
            }
        });

        menu.addSeparator();
    }

    // --- Edit Feature (Inventor primary action) ---
    if (!objName.isEmpty() && model->document()) {
        auto obj = model->document()->getObject(objName.toLatin1().constData());
        if (obj) {
            auto editAction = menu.addAction(tr("Edit Feature"));
            connect(editAction, &QAction::triggered, this, [this, sourceRow]() {
                model->editFeature(sourceRow);
            });

            menu.addSeparator();

            // --- Suppress/Unsuppress ---
            auto ext = obj->getExtensionByType<App::SuppressibleExtension>(true);
            if (ext) {
                QString suppressText = isSuppressed
                    ? tr("Unsuppress Feature")
                    : tr("Suppress Feature");
                auto suppressAction = menu.addAction(suppressText);
                connect(suppressAction, &QAction::triggered, this, [this, sourceRow]() {
                    model->toggleSuppressed(sourceRow);
                });
            }

            // --- Find in Tree ---
            auto selectAction = menu.addAction(tr("Find in Model Tree"));
            connect(selectAction, &QAction::triggered, this, [obj]() {
                Gui::Selection().clearSelection();
                Gui::Selection().addSelection(obj->getDocument()->getName(),
                                              obj->getNameInDocument());
            });

            menu.addSeparator();
        }
    }

    // --- Copy ---
    auto copyAction = menu.addAction(tr("Copy Description"));
    connect(copyAction, &QAction::triggered, this, [description]() {
        QApplication::clipboard()->setText(description);
    });

    // --- Rollback ---
    if (transId > 0) {
        menu.addSeparator();
        auto rollbackAction = menu.addAction(tr("Rollback to Here"));
        connect(rollbackAction, &QAction::triggered, this, [this, sourceRow]() {
            int reply = QMessageBox::question(
                this, tr("Rollback?"),
                tr("Undo all operations after this point?\nContinue?"),
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
        auto ungroupAction = menu.addAction(tr("Ungroup"));
        connect(ungroupAction, &QAction::triggered, this, [this, groupId]() {
            model->removeGroup(groupId);
        });
    }
    else {
        auto groupAction = menu.addAction(tr("Create Group..."));
        connect(groupAction, &QAction::triggered, this, [this, sourceRow]() {
            bool ok;
            QString name = QInputDialog::getText(
                this, tr("Group Name"),
                tr("Enter a name for the feature group:"),
                QLineEdit::Normal, tr("Feature Group"), &ok);
            if (ok && !name.isEmpty()) {
                int start = qMax(0, sourceRow - 1);
                int end = qMin(model->rowCount() - 1, sourceRow + 1);
                model->createGroup(name, start, end);
            }
        });
    }

    // --- Checkpoint ---
    menu.addSeparator();
    auto cpAction = menu.addAction(tr("Create Checkpoint..."));
    connect(cpAction, &QAction::triggered, this, [this]() {
        if (!model->document()) {
            return;
        }
        bool ok;
        QString name = QInputDialog::getText(
            this, tr("Create Checkpoint"),
            tr("Checkpoint name:"),
            QLineEdit::Normal,
            tr("Checkpoint %1").arg(model->checkpointCount() + 1),
            &ok);
        if (ok && !name.isEmpty()) {
            model->createCheckpoint(name);
        }
    });

    // --- Export / Clear ---
    menu.addSeparator();
    auto exportAction = menu.addAction(tr("Export History..."));
    connect(exportAction, &QAction::triggered, this, [this]() {
        QString text = model->exportToText();
        if (text.isEmpty()) {
            return;
        }
        QString filePath = QFileDialog::getSaveFileName(
            this, tr("Export History"),
            QStringLiteral("freecad_history.txt"),
            tr("Text files (*.txt);;All files (*.*)"));
        if (!filePath.isEmpty()) {
            QFile file(filePath);
            if (file.open(QIODevice::WriteOnly | QIODevice::Text)) {
                QTextStream stream(&file);
                stream << text;
                file.close();
            }
        }
    });

    auto clearAction = menu.addAction(tr("Clear History"));
    connect(clearAction, &QAction::triggered, this, [this]() {
        int reply = QMessageBox::question(
            this, tr("Clear History?"),
            tr("Clear the timeline display?\n"
               "This does NOT affect undo/redo."),
            QMessageBox::Yes | QMessageBox::No, QMessageBox::No);
        if (reply == QMessageBox::Yes) {
            model->clear();
        }
    });

    menu.exec(globalPos);
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
