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

#include <algorithm>

#include <QPainter>
#include <QMouseEvent>

#include <App/DocumentObject.h>
#include <App/Document.h>
#include <App/PropertyLinks.h>
#include <Base/Console.h>

#include "RollbackBar.h"
#include "Tree.h"
#include "Command.h"
#include "Application.h"
#include "Document.h"

using namespace Gui;

// ---------------------------------------------------------------------------
// RollbackBar
// ---------------------------------------------------------------------------

RollbackBar::RollbackBar(TreeWidget* tree)
    : QObject(tree)
    , _tree(tree)
{}

void RollbackBar::setBody(App::DocumentObject* body)
{
    _body = body;
}

std::vector<App::DocumentObject*> RollbackBar::orderedFeatures() const
{
    if (!_body) {
        return {};
    }
    // Access the Group property generically (works with PartDesign::Body, etc.)
    auto* groupProp = dynamic_cast<App::PropertyLinkList*>(
        _body->getPropertyByName("Group"));
    if (!groupProp) {
        return {};
    }
    return groupProp->getValues();
}

/// Helper: get the Tip property value from the body
static App::DocumentObject* getTip(App::DocumentObject* body)
{
    if (!body) {
        return nullptr;
    }
    auto* tipProp = dynamic_cast<App::PropertyLink*>(
        body->getPropertyByName("Tip"));
    return tipProp ? tipProp->getValue() : nullptr;
}

void RollbackBar::paintBar(QPainter* painter,
                            const QRect& rowRect,
                            App::DocumentObject* rowObj) const
{
    if (!_body) {
        return;
    }

    // The bar is drawn *below* the row representing the current Tip
    App::DocumentObject* tip = getTip(_body);
    if (rowObj != tip) {
        return;
    }

    painter->save();

    // Thick orange line across the full row width, at the bottom
    QPen pen(QColor(255, 140, 0), 3.0);
    pen.setStyle(Qt::SolidLine);
    painter->setPen(pen);

    int y = rowRect.bottom();
    painter->drawLine(rowRect.left(), y, rowRect.right(), y);

    // Small triangle grip at the left edge
    QPolygon grip;
    grip << QPoint(rowRect.left(), y - 4)
         << QPoint(rowRect.left() + 8, y)
         << QPoint(rowRect.left(), y + 4);
    painter->setBrush(QColor(255, 140, 0));
    painter->drawPolygon(grip);

    painter->restore();
}

bool RollbackBar::handleMousePress(
    QMouseEvent* event,
    App::DocumentObject* rowObj,
    const QRect& rowRect
)
{
    if (!_body || !rowObj || event->button() != Qt::LeftButton) {
        return false;
    }

    App::DocumentObject* tip = getTip(_body);
    if (rowObj != tip) {
        return false;
    }

    // Only start dragging when pressing near the rendered rollback line.
    const int y = rowRect.bottom();
    QRect hitRect(rowRect.left(), y - 4, rowRect.width(), 8);
    if (!hitRect.contains(event->pos())) {
        return false;
    }

    _dragging = true;
    _hoverFeature = rowObj;
    if (_tree) {
        _tree->setCursor(Qt::SizeVerCursor);
    }
    return true;
}

bool RollbackBar::handleMouseMove(QMouseEvent* event, App::DocumentObject* rowObj)
{
    Q_UNUSED(event)

    if (!_dragging) {
        return false;
    }
    if (rowObj) {
        _hoverFeature = rowObj;
    }
    if (_tree) {
        _tree->viewport()->update();
    }
    return true;
}

bool RollbackBar::handleMouseRelease(QMouseEvent* event)
{
    Q_UNUSED(event)

    if (!_dragging) {
        return false;
    }
    _dragging = false;
    if (_tree) {
        _tree->unsetCursor();
    }

    if (_hoverFeature && _hoverFeature != getTip(_body)) {
        moveTipTo(_hoverFeature);
    }
    _hoverFeature = nullptr;
    if (_tree) {
        _tree->viewport()->update();
    }
    return true;
}

void RollbackBar::moveTipTo(App::DocumentObject* feature)
{
    if (!_body || !feature) {
        return;
    }

    // Validate that feature belongs to this body
    auto features = orderedFeatures();
    auto it = std::find(features.begin(), features.end(), feature);
    if (it == features.end()) {
        return;
    }

    auto* gdoc = Application::Instance->getDocument(_body->getDocument());
    if (gdoc) {
        gdoc->openCommand("Move rollback bar");
    }

    // Set the Tip property via generic property access
    auto* tipProp = dynamic_cast<App::PropertyLink*>(
        _body->getPropertyByName("Tip"));
    if (tipProp) {
        tipProp->setValue(feature);
    }

    if (gdoc) {
        gdoc->commitCommand();
    }

    Q_EMIT tipChanged(feature);

    Base::Console().Log("RollbackBar: Tip moved to '%s'\n",
                        feature->getNameInDocument());
}
