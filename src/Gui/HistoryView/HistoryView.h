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
#include <QLabel>
#include <QSortFilterProxyModel>
#include <QScrollBar>
#include <QToolButton>

#include <fastsignals/signal.h>

#include <Gui/DockWindow.h>
#include <Gui/Document.h>

#include "HistoryModel.h"


namespace Gui {
namespace HistoryView {


/**
 * @brief Horizontal timeline widget — Autodesk Inventor-style.
 *
 * Renders feature nodes as icon cells on a horizontal rail/track,
 * matching the compact Inventor Timeline at the bottom of the screen.
 *
 * Visual design:
 *  - Warm gray gradient background (toolbar-like surface)
 *  - Rectangular feature cells with family-colored borders
 *  - Icons centered in cells, labels below
 *  - Horizontal connecting rail between cells
 *  - Draggable "End of Part" marker (gold vertical bar)
 *  - Group brackets above related features
 *
 * Interaction:
 *  - Click to select and highlight object in 3D
 *  - Double-click to edit feature parameters
 *  - Right-click for context menu
 *  - Mouse wheel to scroll horizontally
 *  - Ctrl+wheel to zoom (cell spacing)
 *  - Drag the End-of-Part marker to rollback/roll-forward
 */
class TimelineBar : public QWidget
{
    Q_OBJECT

public:
    explicit TimelineBar(QWidget* parent = nullptr);

    void setModel(HistoryModel* model);
    void setFilterProxy(QSortFilterProxyModel* proxy);

Q_SIGNALS:
    void featureClicked(int sourceIndex);
    void featureDoubleClicked(int sourceIndex);
    void featureContextMenu(int sourceIndex, const QPoint& globalPos);
    void rollbackDragged(int sourceIndex);

protected:
    void paintEvent(QPaintEvent* event) override;
    void mousePressEvent(QMouseEvent* event) override;
    void mouseMoveEvent(QMouseEvent* event) override;
    void mouseReleaseEvent(QMouseEvent* event) override;
    void mouseDoubleClickEvent(QMouseEvent* event) override;
    void wheelEvent(QWheelEvent* event) override;
    void resizeEvent(QResizeEvent* event) override;
    QSize sizeHint() const override;
    QSize minimumSizeHint() const override;

    bool event(QEvent* event) override;  // for tooltip

private:
    int cellAtPos(const QPoint& pos) const;
    QRect cellRect(int visibleIndex) const;
    QRect endOfPartRect() const;
    void scrollToEnd();
    int visibleToSource(int visibleIdx) const;
    int sourceToVisible(int sourceIdx) const;
    int rollbackVisibleIndex() const;

    HistoryModel* histModel{nullptr};
    QSortFilterProxyModel* filterProxy{nullptr};

    // Layout
    int cellSize{34};           ///< Cell width/height
    int cellSpacing{50};        ///< Distance between cell centers
    int scrollOffset{0};        ///< Horizontal scroll offset
    int hoveredCell{-1};        ///< Currently hovered cell (visible index)
    int selectedCell{-1};       ///< Currently selected cell (visible index)

    // Dragging End-of-Part marker
    bool draggingMarker{false};
    int dragTargetCell{-1};     ///< Cell the marker would snap to

    // Inventor Timeline constants
    static constexpr int BarHeight = 64;
    static constexpr int RailY = 24;          ///< Y position of horizontal rail
    static constexpr int CellY = 7;           ///< Y position of cell tops
    static constexpr int LabelY = 46;         ///< Y position of feature labels
    static constexpr int MarkerWidth = 6;     ///< End-of-Part marker width
    static constexpr int LeftMargin = 24;
    static constexpr int MinCellSpacing = 42;
    static constexpr int MaxCellSpacing = 88;
};


/**
 * @brief Filter proxy for the history model.
 */
class HistoryFilterProxy : public QSortFilterProxyModel
{
    Q_OBJECT

public:
    explicit HistoryFilterProxy(QObject* parent = nullptr);

    void setVisibleTypes(const QSet<int>& types);
    void setShowUndone(bool show);
    void setFilterText(const QString& text);

protected:
    bool filterAcceptsRow(int sourceRow, const QModelIndex& sourceParent) const override;

private:
    QSet<int> visibleTypes;
    bool showUndone{true};
    QString filterText;
};


/**
 * @brief Inventor-style Timeline panel — compact horizontal feature strip.
 *
 * Layout:
 *  ┌──────────────────────────────────────────────────────────────────┐
 *  │ [◀] ──[Sk1]──[Ext1]──[Fil1]──│──[Sk2]──[Ext2]── [▶]           │
 *  │        Sketch  Extrude Fillet  EoP                              │
 *  └──────────────────────────────────────────────────────────────────┘
 */
class HistoryPanel : public QWidget
{
    Q_OBJECT

public:
    explicit HistoryPanel(QWidget* parent = nullptr);
    ~HistoryPanel() override;

    void setDocument(const App::Document* doc, const Gui::Document* guiDoc);

    /// Get the model (for Python API access)
    HistoryModel* historyModel() const { return model; }

private Q_SLOTS:
    void onActiveDocument(const Gui::Document& doc);
    void onDeleteDocument(const Gui::Document& doc);
    void onTimelineClicked(int sourceIndex);
    void onTimelineDoubleClicked(int sourceIndex);
    void onTimelineContextMenu(int sourceIndex, const QPoint& globalPos);
    void onTimelineRollbackDragged(int sourceIndex);

private:
    void setupUi();
    void setupConnections();
    void showContextMenu(int sourceRow, const QPoint& globalPos);
    void highlightObjectInView(const QString& objectName);

    // Widgets
    TimelineBar*        timelineBar{nullptr};

    // Model
    HistoryModel*       model{nullptr};
    HistoryFilterProxy* filterProxy{nullptr};

    // Signal connections
    fastsignals::scoped_connection conActive;
    fastsignals::scoped_connection conDelete;
};


/**
 * @brief Dock window wrapper for the Inventor-style Timeline.
 */
class DockWindow : public Gui::DockWindow
{
    Q_OBJECT

public:
    explicit DockWindow(Gui::Document* gDocumentIn = nullptr, QWidget* parent = nullptr);
    ~DockWindow() override = default;

private:
    HistoryPanel* panel{nullptr};
};


} // namespace HistoryView
} // namespace Gui
