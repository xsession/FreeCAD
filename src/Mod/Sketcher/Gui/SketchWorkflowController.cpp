// SPDX-License-Identifier: LGPL-2.1-or-later

/***************************************************************************
 *   Copyright (c) 2026                                                    *
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

#include <Base/Console.h>

#include <Gui/Application.h>
#include <Gui/BackstageView.h>
#include <Gui/Document.h>
#include <Gui/View3DInventor.h>
#include <Gui/ViewProviderDocumentObject.h>
#include <Mod/Sketcher/App/SketchObject.h>

#include "SketchWorkflowController.h"


FC_LOG_LEVEL_INIT("SketchWorkflow", true, true)

using namespace SketcherGui;

namespace
{

const char* entryPointName(SketchWorkflowEntryPoint entryPoint)
{
    switch (entryPoint) {
        case SketchWorkflowEntryPoint::SketcherCreateCommand:
            return "sketcher-create-command";
        case SketchWorkflowEntryPoint::SketcherEditCommand:
            return "sketcher-edit-command";
        case SketchWorkflowEntryPoint::TreeDoubleClick:
            return "tree-double-click";
        case SketchWorkflowEntryPoint::PartDesignCreateCommand:
            return "partdesign-create-command";
        case SketchWorkflowEntryPoint::PartDesignSetEdit:
            return "partdesign-set-edit";
        case SketchWorkflowEntryPoint::PythonBridge:
            return "python-bridge";
        case SketchWorkflowEntryPoint::Unknown:
        default:
            return "unknown";
    }
}

void ensureSketchWorkbenchActive()
{
    Gui::Application::Instance->activateWorkbench("SketcherWorkbench");
}

void normalizeSketchIntentViewport(Gui::Document* guiDocument)
{
    if (!guiDocument) {
        return;
    }

    if (auto* backstage = Gui::BackstageView::existingInstance(); backstage && backstage->isVisible()) {
        backstage->hide();
    }

    if (Gui::Application::Instance->activeDocument() != guiDocument) {
        Gui::Application::Instance->setActiveDocument(guiDocument);
    }

    guiDocument->setActiveView(nullptr, Gui::View3DInventor::getClassTypeId());
    Gui::Application::Instance->activateView(Gui::View3DInventor::getClassTypeId(), true);
}

}  // namespace

void SketchWorkflowController::prepareSketchEditViewport(Gui::Document* guiDocument)
{
    normalizeSketchIntentViewport(guiDocument);
}

bool SketchWorkflowController::enterSketchEdit(
    Gui::Document* guiDocument,
    App::DocumentObject* sketchObject,
    SketchWorkflowEntryPoint entryPoint
)
{
    auto* sketch = dynamic_cast<Sketcher::SketchObject*>(sketchObject);
    if (!guiDocument || !sketch) {
        FC_ERR("reject sketch edit request: invalid sketch workflow context");
        return false;
    }

    auto* viewProvider = dynamic_cast<Gui::ViewProviderDocumentObject*>(
        guiDocument->getViewProvider(sketch)
    );
    if (!viewProvider) {
        FC_ERR("reject sketch edit request: missing sketch view provider");
        return false;
    }

    FC_TRACE(
        "enter sketch workflow intent='edit' entryPoint='" << entryPointName(entryPoint)
                                                            << "' target='" << sketch->getFullName()
                                                            << "'"
    );

    normalizeSketchIntentViewport(guiDocument);
    ensureSketchWorkbenchActive();
    guiDocument->setActiveView(viewProvider, Gui::View3DInventor::getClassTypeId());
    return guiDocument->setEdit(viewProvider);
}