// SPDX-License-Identifier: LGPL-2.1-or-later

/***************************************************************************
 *   Copyright (c) 2008 Jürgen Riegel <juergen.riegel@web.de>              *
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
#include <Base/Interpreter.h>
#include <Base/PyObjectBase.h>
#include <App/Document.h>
#include <Gui/Application.h>
#include <Gui/BitmapFactory.h>
#include <Gui/Language/Translator.h>
#include <Gui/WidgetFactory.h>

#include "PropertyConstraintListItem.h"
#include "SketchWorkflowController.h"
#include "SketcherSettings.h"
#include "SoZoomTranslation.h"
#include "ViewProviderPython.h"
#include "ViewProviderSketch.h"
#include "ViewProviderSketchGeometryExtension.h"
#include "ViewProviderSketchGeometryExtensionPy.h"
#include "Workbench.h"


// create the commands
void CreateSketcherCommands();
void CreateSketcherCommandsCreateGeo();
void CreateSketcherCommandsConstraints();
void CreateSketcherCommandsConstraintAccel();
void CreateSketcherCommandsAlterGeo();
void CreateSketcherCommandsBSpline();
void CreateSketcherCommandsOverlay();
void CreateSketcherCommandsVirtualSpace();

void loadSketcherResource()
{
    // add resources and reloads the translators
    Q_INIT_RESOURCE(Sketcher);
    Q_INIT_RESOURCE(Sketcher_translation);
    Gui::Translator::instance()->refresh();
}

namespace SketcherGui
{
class Module: public Py::ExtensionModule<Module>
{
public:
    Module()
        : Py::ExtensionModule<Module>("SketcherGui")
    {
        add_varargs_method(
            "enterSketchEdit",
            &Module::enterSketchEdit,
            "enterSketchEdit(objectName)\n"
            "-- Enter sketch edit mode through the canonical sketch workflow controller."
        );
        initialize("This module is the SketcherGui module.");  // register with Python
    }

    ~Module() override
    {}

    Py::Object enterSketchEdit(const Py::Tuple& args)
    {
        char* objectName = nullptr;
        if (!PyArg_ParseTuple(args.ptr(), "s", &objectName)) {
            throw Py::Exception();
        }

        auto* guiDocument = Gui::Application::Instance->activeDocument();
        if (!guiDocument) {
            throw Py::RuntimeError("No active GUI document");
        }

        auto* appDocument = guiDocument->getDocument();
        if (!appDocument) {
            throw Py::RuntimeError("No active application document");
        }

        auto* object = appDocument->getObject(objectName);
        if (!object) {
            throw Py::RuntimeError(std::string("No such object found in document: '") + objectName + "'");
        }

        const bool ok = SketcherGui::SketchWorkflowController::enterSketchEdit(
            guiDocument,
            object,
            SketchWorkflowEntryPoint::PythonBridge
        );
        return Py::Boolean(ok);
    }

private:
};

PyObject* initModule()
{
    return Base::Interpreter().addModule(new Module);
}

}  // namespace SketcherGui

/* Python entry */
PyMOD_INIT_FUNC(SketcherGui)
{
    if (!Gui::Application::Instance) {
        PyErr_SetString(PyExc_ImportError, "Cannot load Gui module in console application.");
        PyMOD_Return(nullptr);
    }
    try {
        Base::Interpreter().runString("import PartGui");
        Base::Interpreter().runString("import Sketcher");
    }
    catch (const Base::Exception& e) {
        PyErr_SetString(PyExc_ImportError, e.what());
        PyMOD_Return(nullptr);
    }

    PyObject* sketcherGuiModule = SketcherGui::initModule();
    Base::Console().log("Loading GUI of Sketcher module… done\n");

    Gui::BitmapFactory().addPath(QStringLiteral(":/icons/constraints"));
    Gui::BitmapFactory().addPath(QStringLiteral(":/icons/elements"));
    Gui::BitmapFactory().addPath(QStringLiteral(":/icons/general"));
    Gui::BitmapFactory().addPath(QStringLiteral(":/icons/geometry"));
    Gui::BitmapFactory().addPath(QStringLiteral(":/icons/pointers"));
    Gui::BitmapFactory().addPath(QStringLiteral(":/icons/splines"));
    Gui::BitmapFactory().addPath(QStringLiteral(":/icons/tools"));
    Gui::BitmapFactory().addPath(QStringLiteral(":/icons/overlay"));

    // instantiating the commands
    CreateSketcherCommands();
    CreateSketcherCommandsCreateGeo();
    CreateSketcherCommandsConstraints();
    CreateSketcherCommandsAlterGeo();
    CreateSketcherCommandsConstraintAccel();
    CreateSketcherCommandsBSpline();
    CreateSketcherCommandsOverlay();
    CreateSketcherCommandsVirtualSpace();
    SketcherGui::registerSketcherContextualRibbonPanels();

    SketcherGui::Workbench::init();

    // Add Types to module
    Base::Interpreter().addType(
        &SketcherGui::ViewProviderSketchGeometryExtensionPy ::Type,
        sketcherGuiModule,
        "ViewProviderSketchGeometryExtension"
    );

    // init objects
    SketcherGui::ViewProviderSketch ::init();
    SketcherGui::ViewProviderPython ::init();
    SketcherGui::ViewProviderCustom ::init();
    SketcherGui::ViewProviderCustomPython ::init();
    SketcherGui::SoZoomTranslation ::initClass();
    SketcherGui::SoSketchFaces ::initClass();
    SketcherGui::PropertyConstraintListItem ::init();
    SketcherGui::ViewProviderSketchGeometryExtension ::init();

    (void)new Gui::PrefPageProducer<SketcherGui::SketcherSettings>(
        QT_TRANSLATE_NOOP("QObject", "Sketcher")
    );
    (void)new Gui::PrefPageProducer<SketcherGui::SketcherSettingsGrid>(
        QT_TRANSLATE_NOOP("QObject", "Sketcher")
    );
    (void)new Gui::PrefPageProducer<SketcherGui::SketcherSettingsDisplay>(
        QT_TRANSLATE_NOOP("QObject", "Sketcher")
    );
    (void)new Gui::PrefPageProducer<SketcherGui::SketcherSettingsAppearance>(
        QT_TRANSLATE_NOOP("QObject", "Sketcher")
    );

    // add resources and reloads the translators
    loadSketcherResource();

    PyMOD_Return(sketcherGuiModule);
}
