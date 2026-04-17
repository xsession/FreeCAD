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
#include <FCGlobal.h>

class QPainter;
class QMouseEvent;
class QRect;

namespace App {
class DocumentObject;
}

namespace Gui {

class TreeWidget;

/// RollbackBar — a draggable horizontal bar rendered inside the model-tree
/// that represents the PartDesign::Body Tip position.  Dragging the bar
/// up/down calls Body::setTip() to roll the parametric history forward or
/// backward, providing instant visual feedback of the model at any stage.
class GuiExport RollbackBar : public QObject
{
    Q_OBJECT

public:
    explicit RollbackBar(TreeWidget* tree);

    /// Set the active body (any object with Tip + Group properties, e.g. PartDesign::Body)
    void setBody(App::DocumentObject* body);

    /// Returns the currently tracked body (may be nullptr)
    App::DocumentObject* body() const { return _body; }

    /// Paint the rollback bar on top of the tree delegate.
    /// Called from TreeWidget::drawRow().
    void paintBar(QPainter* painter, const QRect& rowRect, App::DocumentObject* rowObj) const;

    /// Returns true if the bar is currently being dragged
    bool isDragging() const { return _dragging; }

    /// Handle mouse events forwarded from the TreeWidget
    bool handleMousePress(QMouseEvent* event, App::DocumentObject* rowObj, const QRect& rowRect);
    bool handleMouseMove(QMouseEvent* event, App::DocumentObject* rowObj);
    bool handleMouseRelease(QMouseEvent* event);

Q_SIGNALS:
    /// Emitted whenever the Tip changes due to dragging
    void tipChanged(App::DocumentObject* newTip);

private:
    /// Move the Tip to the given feature (calls Body::insertObject and setTip)
    void moveTipTo(App::DocumentObject* feature);

    /// Returns the ordered list of features in the body
    std::vector<App::DocumentObject*> orderedFeatures() const;

    TreeWidget* _tree = nullptr;
    App::DocumentObject* _body = nullptr;
    bool _dragging = false;
    App::DocumentObject* _hoverFeature = nullptr;
};

} // namespace Gui
