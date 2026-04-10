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
#include <QListView>
#include <QStyledItemDelegate>
#include <QPushButton>
#include <QLabel>
#include <QCheckBox>
#include <QComboBox>
#include <QLineEdit>
#include <QToolBar>
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
 * @brief Custom delegate that renders Fusion 360-style timeline entries.
 *
 * Each entry shows:
 *  - A colored left-edge indicator (based on feature family)
 *  - A feature-type-specific icon
 *  - The description text
 *  - A timestamp in the right margin
 *  - Undone entries are rendered with strikethrough and reduced opacity
 *  - Suppressed entries show a red X overlay
 *  - The current rollback position gets a special gold marker
 *  - Feature family color-coded badges
 */
class HistoryDelegate : public QStyledItemDelegate
{
    Q_OBJECT

public:
    explicit HistoryDelegate(QObject* parent = nullptr);

    void paint(QPainter* painter,
               const QStyleOptionViewItem& option,
               const QModelIndex& index) const override;

    QSize sizeHint(const QStyleOptionViewItem& option,
                   const QModelIndex& index) const override;
};


/**
 * @brief Horizontal timeline widget — Fusion 360-style.
 *
 * Renders feature nodes as icons on a horizontal connecting line.
 * Supports:
 *  - Feature-type-specific icons with family color coding
 *  - Draggable rollback marker
 *  - Hover tooltips
 *  - Double-click to edit feature
 *  - Right-click context menu
 *  - Mouse wheel horizontal scrolling
 *  - Ctrl+wheel zoom (node spacing)
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
    int nodeAtPos(const QPoint& pos) const;
    QRect nodeRect(int visibleIndex) const;
    QRect rollbackMarkerRect() const;
    void updateGeometry();
    void scrollToEnd();
    int visibleToSource(int visibleIdx) const;
    int sourceToVisible(int sourceIdx) const;
    int rollbackVisibleIndex() const;

    HistoryModel* histModel{nullptr};
    QSortFilterProxyModel* filterProxy{nullptr};

    // Layout
    int nodeSize{32};           ///< Icon size
    int nodeSpacing{52};        ///< Distance between node centers
    int scrollOffset{0};        ///< Horizontal scroll offset
    int hoveredNode{-1};        ///< Currently hovered node (visible index)
    int selectedNode{-1};       ///< Currently selected node (visible index)

    // Dragging rollback marker
    bool draggingRollback{false};
    int dragTargetNode{-1};     ///< Node the marker would snap to

    // Constants
    static constexpr int TimelineHeight = 64;
    static constexpr int LineY = 40;         ///< Y position of connecting line
    static constexpr int NodeY = 8;          ///< Y position of node icons
    static constexpr int MarkerTriangleSize = 10;
    static constexpr int LeftMargin = 16;
    static constexpr int MinNodeSpacing = 36;
    static constexpr int MaxNodeSpacing = 96;
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
 * @brief The main History Timeline widget — Fusion 360 "Design History" panel.
 *
 * Contains both the horizontal TimelineBar and a detail list view,
 * with toolbar controls for filtering, search, and export.
 *
 * Layout:
 *  ┌─────────────────────────────────────────────┐
 *  │ [Toolbar: search | filter | options]         │
 *  ├─────────────────────────────────────────────┤
 *  │ ◄ [icon][icon][icon]▲[icon][icon] ►        │ ← TimelineBar
 *  ├─────────────────────────────────────────────┤
 *  │ Detailed list view (vertical)                │
 *  ├─────────────────────────────────────────────┤
 *  │ Status bar                                   │
 *  └─────────────────────────────────────────────┘
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
    void onEntryClicked(const QModelIndex& index);
    void onEntryDoubleClicked(const QModelIndex& index);
    void onTimelineClicked(int sourceIndex);
    void onTimelineDoubleClicked(int sourceIndex);
    void onTimelineContextMenu(int sourceIndex, const QPoint& globalPos);
    void onTimelineRollbackDragged(int sourceIndex);
    void onEntryContextMenu(const QPoint& pos);
    void onEntryAdded(int index);
    void onFilterChanged();
    void onSearchChanged(const QString& text);
    void onExportClicked();
    void onClearClicked();
    void onCheckpointClicked();
    void updateStatus();

private:
    void setupUi();
    void setupToolbar();
    void setupConnections();
    void showContextMenu(int sourceRow, const QPoint& globalPos);
    void highlightObjectInView(const QString& objectName);

    // Widgets
    QToolBar*     toolbar{nullptr};
    TimelineBar*  timelineBar{nullptr};
    QListView*    listView{nullptr};
    QLabel*       statusLabel{nullptr};
    QLineEdit*    searchBox{nullptr};
    QComboBox*    filterCombo{nullptr};
    QPushButton*  exportBtn{nullptr};
    QPushButton*  clearBtn{nullptr};
    QPushButton*  checkpointBtn{nullptr};
    QCheckBox*    showUndoneCheck{nullptr};
    QToolButton*  toggleListBtn{nullptr};

    // Model
    HistoryModel*       model{nullptr};
    HistoryFilterProxy* filterProxy{nullptr};

    // State
    bool listViewVisible{true};

    // Signal connections
    fastsignals::scoped_connection conActive;
    fastsignals::scoped_connection conDelete;
};


/**
 * @brief Dock window wrapper for the History Timeline panel.
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
