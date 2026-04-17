// SPDX-License-Identifier: LGPL-2.1-or-later
/****************************************************************************
 *                                                                          *
 *   Copyright (c) 2026 FreeCAD contributors                                *
 *                                                                          *
 *   This file is part of FreeCAD.                                          *
 *                                                                          *
 *   FreeCAD is free software: you can redistribute it and/or modify it     *
 *   under the terms of the GNU Lesser General Public License as            *
 *   published by the Free Software Foundation, either version 2.1 of the   *
 *   License, or (at your option) any later version.                        *
 *                                                                          *
 *   FreeCAD is distributed in the hope that it will be useful, but         *
 *   WITHOUT ANY WARRANTY; without even the implied warranty of             *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU       *
 *   Lesser General Public License for more details.                        *
 *                                                                          *
 *   You should have received a copy of the GNU Lesser General Public       *
 *   License along with FreeCAD. If not, see                                *
 *   <https://www.gnu.org/licenses/>.                                       *
 *                                                                          *
 ****************************************************************************/

#include "PreCompiled.h"

#include "SelectionCountBadge.h"

#include <QStringList>

#include <App/DocumentObject.h>

using namespace Gui;

namespace
{

enum class SelectionKind
{
    Vertex,
    Edge,
    Face,
    Solid,
    Other
};

SelectionKind classifySubElement(const std::string& subName)
{
    if (subName.rfind("Vertex", 0) == 0) {
        return SelectionKind::Vertex;
    }
    if (subName.rfind("Edge", 0) == 0) {
        return SelectionKind::Edge;
    }
    if (subName.rfind("Face", 0) == 0) {
        return SelectionKind::Face;
    }
    if (subName.rfind("Solid", 0) == 0) {
        return SelectionKind::Solid;
    }
    return SelectionKind::Other;
}

QString selectionLabel(const QObject* context, SelectionKind kind, int count)
{
    switch (kind) {
        case SelectionKind::Vertex:
            return context->tr("%n vertex selected", nullptr, count);
        case SelectionKind::Edge:
            return context->tr("%n edge selected", nullptr, count);
        case SelectionKind::Face:
            return context->tr("%n face selected", nullptr, count);
        case SelectionKind::Solid:
            return context->tr("%n solid selected", nullptr, count);
        case SelectionKind::Other:
            return context->tr("%n subelement selected", nullptr, count);
    }

    return context->tr("%n item selected", nullptr, count);
}

}  // namespace

SelectionCountBadge::SelectionCountBadge(QWidget* parent)
    : StatusBarLabel(parent, "SelectionCountEnabled")
    , SelectionObserver(true, ResolveMode::NoResolve)
{
    setObjectName(QStringLiteral("selectionCountBadge"));
    setWindowTitle(tr("Selection Count"));
    setMinimumWidth(120);
    setAlignment(Qt::AlignRight | Qt::AlignVCenter);
    setToolTip(tr("Shows the current selection count"));
    updateBadge();
}

void SelectionCountBadge::onSelectionChanged(const SelectionChanges&)
{
    updateBadge();
}

void SelectionCountBadge::updateBadge()
{
    const auto selection
        = Selection().getSelectionEx("*", App::DocumentObject::getClassTypeId(), ResolveMode::NoResolve);

    int objectCount = 0;
    int subElementCount = 0;
    SelectionKind subKind = SelectionKind::Other;
    bool hasSingleKind = true;

    for (const auto& selectedObject : selection) {
        const auto& subNames = selectedObject.getSubNames();
        if (subNames.empty()) {
            ++objectCount;
            continue;
        }

        for (const auto& subName : subNames) {
            const auto currentKind = classifySubElement(subName);
            if (subElementCount == 0) {
                subKind = currentKind;
            }
            else if (subKind != currentKind) {
                hasSingleKind = false;
            }

            ++subElementCount;
        }
    }

    QString text;
    QStringList parts;

    if (objectCount == 0 && subElementCount == 0) {
        text = tr("0 selected");
    }
    else if (objectCount == 0) {
        text = selectionLabel(this,
                              hasSingleKind ? subKind : SelectionKind::Other,
                              subElementCount);
    }
    else if (subElementCount == 0) {
        text = tr("%n object selected", nullptr, objectCount);
    }
    else {
        parts << tr("%n object selected", nullptr, objectCount);
        parts << selectionLabel(this,
                                hasSingleKind ? subKind : SelectionKind::Other,
                                subElementCount);
        text = parts.join(QStringLiteral(", "));
    }

    setText(text);
    setToolTip(text);
}
