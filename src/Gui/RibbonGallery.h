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

#pragma once

#include <QWidget>
#include <QIcon>
#include <QString>
#include <QList>
#include <QSize>

#include <FCGlobal.h>

class QGridLayout;
class QScrollArea;
class QToolButton;
class QMenu;

namespace Gui {


/// A single item inside a RibbonGallery.
struct GuiExport RibbonGalleryItem
{
    RibbonGalleryItem() = default;
    RibbonGalleryItem(const QString& id, const QIcon& icon,
                      const QString& label, const QString& toolTip = {})
        : itemId(id), icon(icon), label(label), toolTip(toolTip)
    {}

    QString itemId;              ///< Unique identifier (e.g. command name or material UUID)
    QIcon   icon;                ///< Thumbnail icon
    QString label;               ///< Display text below or beside the icon
    QString toolTip;             ///< Hover tooltip
    bool    enabled = true;      ///< Greyed-out when false
};


// ============================================================================
// RibbonGallery — Thumbnail grid widget embeddable in a RibbonPanel
//
//   Shows a horizontal row of thumbnail items that fits inside a ribbon panel.
//   A dropdown "expand" button at the right opens a full popup grid showing
//   all items, optionally grouped into categories.
//
//   Usage in a RibbonPanel:
//     auto* gallery = new RibbonGallery(this);
//     gallery->setThumbnailSize({48, 48});
//     gallery->addItem({"mat_steel", steelIcon, "Steel"});
//     gallery->addItem({"mat_alum",  alumIcon,  "Aluminum"});
//     ribbonPanel->layout()->addWidget(gallery);
//
//   §6.4 of MODERNIZATION_PLAN: "Galleries — visual previews of thread
//   types, materials.  RibbonGallery widget with thumbnail grid."
// ============================================================================

class GuiExport RibbonGallery : public QWidget
{
    Q_OBJECT

public:
    explicit RibbonGallery(QWidget* parent = nullptr);

    // ── Item management ──────────────────────────────────────────────
    void addItem(const RibbonGalleryItem& item);
    void addItems(const QList<RibbonGalleryItem>& items);
    void clear();
    int  itemCount() const { return items_.size(); }

    /// Add a category separator shown in the expanded popup.
    void addCategory(const QString& name);

    // ── Appearance ───────────────────────────────────────────────────
    void setThumbnailSize(const QSize& size);
    QSize thumbnailSize() const { return thumbSize_; }

    /// Number of visible rows in the inline strip (default 1).
    void setVisibleRows(int rows);
    int  visibleRows() const { return visibleRows_; }

    /// Number of columns shown in the inline strip before the
    /// expand button appears (0 = auto-fit to panel width).
    void setVisibleColumns(int cols);
    int  visibleColumns() const { return visibleCols_; }

    /// Current selected item id (empty if none).
    QString selectedItemId() const { return selectedId_; }
    void    setSelectedItemId(const QString& id);

Q_SIGNALS:
    /// Emitted when the user clicks a gallery item (inline or popup).
    void itemActivated(const QString& itemId);

    /// Emitted when the user hovers over an item for live preview.
    void itemHovered(const QString& itemId);

private Q_SLOTS:
    void onExpandClicked();
    void onInlineItemClicked(int index);
    void onPopupItemClicked(int index);

private:
    void rebuildInlineStrip();
    QToolButton* createThumbnailButton(const RibbonGalleryItem& item, int index,
                                       bool forPopup);

    struct CategoryMarker {
        QString name;
        int insertBeforeIndex;  ///< Items index where this category starts
    };

    QList<RibbonGalleryItem> items_;
    QList<CategoryMarker>    categories_;
    QSize    thumbSize_{48, 48};
    int      visibleRows_ = 1;
    int      visibleCols_ = 0;  ///< 0 = auto
    QString  selectedId_;

    // Inline strip widgets
    QWidget*     stripWidget_{nullptr};
    QGridLayout* stripLayout_{nullptr};
    QToolButton* expandBtn_{nullptr};
    QMenu*       popupMenu_{nullptr};
};


} // namespace Gui
