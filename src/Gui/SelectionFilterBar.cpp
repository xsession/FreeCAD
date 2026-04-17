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

#include "PreCompiled.h"

#include "SelectionFilterBar.h"

#include <App/Application.h>
#include <Base/Parameter.h>

#include "BitmapFactory.h"
#include "Selection/Selection.h"

#include <QHBoxLayout>
#include <QLabel>
#include <QSignalBlocker>

using namespace Gui;

namespace {

class ElementFilterGate : public SelectionGate
{
public:
    explicit ElementFilterGate(const QString& filterString)
        : filter(filterString.toStdString())
    {}

    bool allow(App::Document* /*doc*/,
               App::DocumentObject* /*obj*/,
               const char* subName) override
    {
        if (!subName || subName[0] == '\0') {
            return true;  // Object-level selection always allowed
        }

        std::string sub(subName);

        for (const auto& allowed : allowedTypes) {
            if (sub.compare(0, allowed.size(), allowed) == 0) {
                return true;
            }
        }
        return false;
    }

    void setAllowedTypes(const std::vector<std::string>& types)
    {
        allowedTypes = types;
    }

private:
    std::string filter;
    std::vector<std::string> allowedTypes;
};

}  // namespace

SelectionFilterBar::SelectionFilterBar(QWidget* parent)
    : QWidget(parent)
{
    createButtons();
}

void SelectionFilterBar::createButtons()
{
    auto* layout = new QHBoxLayout(this);
    layout->setContentsMargins(4, 0, 4, 0);
    layout->setSpacing(2);

    auto* label = new QLabel(tr("Filter:"), this);
    label->setStyleSheet(QStringLiteral("color: gray; font-size: 10px;"));
    layout->addWidget(label);

    buttons[Vertex] = makeToggle(QStringLiteral("vertex-selection"), tr("Vertices (V)"), Vertex);
    buttons[Edge] = makeToggle(QStringLiteral("edge-selection"), tr("Edges (E)"), Edge);
    buttons[Face] = makeToggle(QStringLiteral("face-selection"), tr("Faces (F)"), Face);
    buttons[Solid] = makeToggle(QStringLiteral("solid-selection"), tr("Solids (S)"), Solid);

    for (auto* btn : buttons) {
        layout->addWidget(btn);
    }

    resetButton = new QToolButton(this);
    resetButton->setAutoRaise(true);
    resetButton->setText(tr("All"));
    resetButton->setToolTip(tr("Clears the selection filter"));
    connect(resetButton, &QToolButton::clicked, this, &SelectionFilterBar::resetAll);
    layout->addWidget(resetButton);

    loadState();
    applyFilter();
    refreshUi();
}

QToolButton* SelectionFilterBar::makeToggle(const QString& iconName,
                                            const QString& tooltip,
                                            ElementType type)
{
    auto* btn = new QToolButton(this);
    btn->setCheckable(true);
    btn->setChecked(true);
    btn->setToolTip(tooltip);
    btn->setFixedSize(22, 22);

    QIcon icon = BitmapFactory().iconFromTheme(iconName.toLatin1().constData());
    if (!icon.isNull()) {
        btn->setIcon(icon);
    }
    else {
        btn->setText(QString::fromLatin1(typeNames[type]).left(1));
    }

    connect(btn, &QToolButton::toggled, this, [this](bool) {
        saveState();
        applyFilter();
        refreshUi();
        Q_EMIT filterChanged();
    });

    return btn;
}

bool SelectionFilterBar::isTypeEnabled(ElementType type) const
{
    return buttons[type] && buttons[type]->isChecked();
}

void SelectionFilterBar::setTypeEnabled(ElementType type, bool enabled)
{
    if (buttons[type]) {
        buttons[type]->setChecked(enabled);
    }
}

void SelectionFilterBar::resetAll()
{
    for (auto* btn : buttons) {
        if (btn) {
            QSignalBlocker blocker(btn);
            btn->setChecked(true);
        }
    }

    saveState();
    applyFilter();
    refreshUi();
    Q_EMIT filterChanged();
}

void SelectionFilterBar::applyFilter()
{
    if (areAllTypesEnabled()) {
        Selection().rmvSelectionGate();
        return;
    }

    std::vector<std::string> allowed;
    if (isTypeEnabled(Vertex)) {
        allowed.emplace_back("Vertex");
    }
    if (isTypeEnabled(Edge)) {
        allowed.emplace_back("Edge");
    }
    if (isTypeEnabled(Face)) {
        allowed.emplace_back("Face");
    }
    if (isTypeEnabled(Solid)) {
        allowed.emplace_back("Solid");
    }

    auto* gate = new ElementFilterGate(buildFilterString());
    gate->setAllowedTypes(allowed);
    Selection().addSelectionGate(gate);
}

QString SelectionFilterBar::buildFilterString() const
{
    QStringList parts;
    for (int i = 0; i < NumTypes; ++i) {
        if (buttons[i] && buttons[i]->isChecked()) {
            parts << QString::fromLatin1(typeNames[i]);
        }
    }
    return parts.join(QLatin1Char('|'));
}

QString SelectionFilterBar::buildSummaryText() const
{
    return areAllTypesEnabled() ? tr("All") : buildFilterString();
}

bool SelectionFilterBar::areAllTypesEnabled() const
{
    for (int i = 0; i < NumTypes; ++i) {
        if (buttons[i] && !buttons[i]->isChecked()) {
            return false;
        }
    }
    return true;
}

void SelectionFilterBar::refreshUi()
{
    const QString summary = buildSummaryText();
    const QString tooltip = areAllTypesEnabled()
        ? tr("Selection filter: all element types enabled")
        : tr("Selection filter active: %1").arg(summary);

    setToolTip(tooltip);
    for (auto* btn : buttons) {
        if (btn) {
            btn->setStatusTip(tooltip);
        }
    }

    if (resetButton) {
        resetButton->setVisible(!areAllTypesEnabled());
        resetButton->setStatusTip(tooltip);
        resetButton->setToolTip(
            areAllTypesEnabled() ? tr("All element types are enabled")
                                 : tr("Clears the selection filter (%1)").arg(summary)
        );
    }
}

void SelectionFilterBar::loadState()
{
    auto hGrp = App::GetApplication().GetParameterGroupByPath(
        "User parameter:BaseApp/Preferences/Selection"
    );

    for (int i = 0; i < NumTypes; ++i) {
        if (!buttons[i]) {
            continue;
        }

        const QString key = QStringLiteral("SelectionFilter_%1")
                                .arg(QString::fromLatin1(typeNames[i]));
        QSignalBlocker blocker(buttons[i]);
        buttons[i]->setChecked(hGrp->GetBool(key.toUtf8().constData(), true));
    }
}

void SelectionFilterBar::saveState() const
{
    auto hGrp = App::GetApplication().GetParameterGroupByPath(
        "User parameter:BaseApp/Preferences/Selection"
    );

    for (int i = 0; i < NumTypes; ++i) {
        if (!buttons[i]) {
            continue;
        }

        const QString key = QStringLiteral("SelectionFilter_%1")
                                .arg(QString::fromLatin1(typeNames[i]));
        hGrp->SetBool(key.toUtf8().constData(), buttons[i]->isChecked());
    }
}
