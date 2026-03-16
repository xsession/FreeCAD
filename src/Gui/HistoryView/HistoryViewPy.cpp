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

#include <App/Application.h>
#include <Gui/Application.h>
#include <Gui/DockWindowManager.h>

#include "HistoryViewPy.h"
#include "HistoryView.h"
#include "HistoryModel.h"


using namespace Gui::HistoryView;

// Helper: find the active HistoryPanel's model
static HistoryModel* getActiveModel()
{
    auto pDockMgr = Gui::DockWindowManager::instance();
    auto widget = pDockMgr->findRegisteredDockWindow("Std_HistoryView");
    if (!widget) {
        return nullptr;
    }

    auto dockWin = qobject_cast<Gui::HistoryView::DockWindow*>(widget);
    if (!dockWin) {
        return nullptr;
    }

    auto panel = dockWin->findChild<HistoryPanel*>();
    if (!panel) {
        return nullptr;
    }

    return panel->historyModel();
}


HistoryViewPy::HistoryViewPy()
    : Py::ExtensionModule<HistoryViewPy>("HistoryView")
{
    add_varargs_method("getEntries", &HistoryViewPy::getEntries,
        "getEntries() -> list of dicts\n"
        "Get all modification history entries for the active document.\n"
        "Each dict contains: type, description, objectName, objectLabel,\n"
        "objectType, propertyName, transactionName, transactionId,\n"
        "timestamp, isUndone, isRollbackTarget, isSuppressed,\n"
        "featureFamily, featureLabel, groupId");

    add_varargs_method("getEntryCount", &HistoryViewPy::getEntryCount,
        "getEntryCount() -> int\n"
        "Get the number of history entries.");

    add_varargs_method("exportToText", &HistoryViewPy::exportToText,
        "exportToText() -> str\n"
        "Export the modification history as a human-readable string.");

    add_varargs_method("clear", &HistoryViewPy::clear,
        "clear()\n"
        "Clear the modification history display (does not affect undo).");

    add_varargs_method("rollbackTo", &HistoryViewPy::rollbackTo,
        "rollbackTo(index) -> bool\n"
        "Rollback the document to the specified history entry index.");

    add_varargs_method("editFeature", &HistoryViewPy::editFeature,
        "editFeature(index) -> bool\n"
        "Open the feature's edit dialog (like double-click in Fusion 360).");

    add_varargs_method("toggleSuppressed", &HistoryViewPy::toggleSuppressed,
        "toggleSuppressed(index) -> bool\n"
        "Toggle suppress/unsuppress for a feature at the given index.");

    add_varargs_method("createGroup", &HistoryViewPy::createGroup,
        "createGroup(name, startIndex, endIndex) -> int\n"
        "Create a named group from entries [startIndex, endIndex].\n"
        "Returns the group ID, or -1 on failure.");

    add_varargs_method("removeGroup", &HistoryViewPy::removeGroup,
        "removeGroup(groupId)\n"
        "Remove a feature group (ungroup).");

    add_varargs_method("isEnabled", &HistoryViewPy::isEnabled,
        "isEnabled() -> bool\n"
        "Check whether the History View panel is enabled.");

    add_varargs_method("setEnabled", &HistoryViewPy::setEnabled,
        "setEnabled(enabled)\n"
        "Enable or disable the History View panel.");

    initialize("FreeCAD Modification History Timeline API.\n"
               "\n"
               "Provides access to the Fusion 360-style modification history\n"
               "that tracks all document changes, transactions, and undo/redo\n"
               "operations. Supports feature editing, suppress/unsuppress,\n"
               "grouping, and rollback.\n"
               "\n"
               "Usage:\n"
               "  import FreeCADGui\n"
               "  entries = FreeCADGui.HistoryView.getEntries()\n"
               "  FreeCADGui.HistoryView.editFeature(5)\n"
               "  FreeCADGui.HistoryView.toggleSuppressed(3)\n"
               "  print(FreeCADGui.HistoryView.exportToText())\n");
}

Py::Object HistoryViewPy::getEntries(const Py::Tuple& args)
{
    if (!PyArg_ParseTuple(args.ptr(), "")) {
        throw Py::Exception();
    }

    auto model = getActiveModel();
    if (!model) {
        return Py::List();
    }

    const auto& entries = model->entries();
    Py::List result;

    for (const auto& entry : entries) {
        Py::Dict dict;
        dict.setItem("type", Py::String(entry.typeLabel().toStdString()));
        dict.setItem("typeId", Py::Long(static_cast<int>(entry.type)));
        dict.setItem("description", Py::String(entry.description.toStdString()));
        dict.setItem("objectName", Py::String(entry.objectName.toStdString()));
        dict.setItem("objectLabel", Py::String(entry.objectLabel.toStdString()));
        dict.setItem("objectType", Py::String(entry.objectType.toStdString()));
        dict.setItem("propertyName", Py::String(entry.propertyName.toStdString()));
        dict.setItem("transactionName", Py::String(entry.transactionName.toStdString()));
        dict.setItem("transactionId", Py::Long(entry.transactionId));
        dict.setItem("timestamp", Py::String(
            entry.timestamp.toString(Qt::ISODate).toStdString()));
        dict.setItem("isUndone", Py::Boolean(entry.isUndone));
        dict.setItem("isRollbackTarget", Py::Boolean(entry.isRollbackTarget));
        dict.setItem("isSuppressed", Py::Boolean(entry.isSuppressed));
        dict.setItem("featureFamily", Py::Long(static_cast<int>(entry.family)));
        dict.setItem("featureLabel", Py::String(entry.featureLabel().toStdString()));
        dict.setItem("groupId", Py::Long(entry.groupId));

        result.append(dict);
    }

    return result;
}

Py::Object HistoryViewPy::getEntryCount(const Py::Tuple& args)
{
    if (!PyArg_ParseTuple(args.ptr(), "")) {
        throw Py::Exception();
    }

    auto model = getActiveModel();
    return Py::Long(model ? model->rowCount() : 0);
}

Py::Object HistoryViewPy::exportToText(const Py::Tuple& args)
{
    if (!PyArg_ParseTuple(args.ptr(), "")) {
        throw Py::Exception();
    }

    auto model = getActiveModel();
    return Py::String(model ? model->exportToText().toStdString() : "");
}

Py::Object HistoryViewPy::clear(const Py::Tuple& args)
{
    if (!PyArg_ParseTuple(args.ptr(), "")) {
        throw Py::Exception();
    }

    auto model = getActiveModel();
    if (model) {
        model->clear();
    }
    return Py::None();
}

Py::Object HistoryViewPy::rollbackTo(const Py::Tuple& args)
{
    int index = 0;
    if (!PyArg_ParseTuple(args.ptr(), "i", &index)) {
        throw Py::Exception();
    }

    auto model = getActiveModel();
    return Py::Boolean(model ? model->rollbackTo(index) : false);
}

Py::Object HistoryViewPy::editFeature(const Py::Tuple& args)
{
    int index = 0;
    if (!PyArg_ParseTuple(args.ptr(), "i", &index)) {
        throw Py::Exception();
    }

    auto model = getActiveModel();
    return Py::Boolean(model ? model->editFeature(index) : false);
}

Py::Object HistoryViewPy::toggleSuppressed(const Py::Tuple& args)
{
    int index = 0;
    if (!PyArg_ParseTuple(args.ptr(), "i", &index)) {
        throw Py::Exception();
    }

    auto model = getActiveModel();
    return Py::Boolean(model ? model->toggleSuppressed(index) : false);
}

Py::Object HistoryViewPy::createGroup(const Py::Tuple& args)
{
    const char* name = nullptr;
    int startIndex = 0;
    int endIndex = 0;
    if (!PyArg_ParseTuple(args.ptr(), "sii", &name, &startIndex, &endIndex)) {
        throw Py::Exception();
    }

    auto model = getActiveModel();
    if (!model) {
        return Py::Long(-1);
    }
    return Py::Long(model->createGroup(QString::fromUtf8(name), startIndex, endIndex));
}

Py::Object HistoryViewPy::removeGroup(const Py::Tuple& args)
{
    int groupId = 0;
    if (!PyArg_ParseTuple(args.ptr(), "i", &groupId)) {
        throw Py::Exception();
    }

    auto model = getActiveModel();
    if (model) {
        model->removeGroup(groupId);
    }
    return Py::None();
}

Py::Object HistoryViewPy::isEnabled(const Py::Tuple& args)
{
    if (!PyArg_ParseTuple(args.ptr(), "")) {
        throw Py::Exception();
    }

    ParameterGrp::handle group = App::GetApplication()
                                     .GetUserParameter()
                                     .GetGroup("BaseApp")
                                     ->GetGroup("Preferences")
                                     ->GetGroup("DockWindows")
                                     ->GetGroup("HistoryView");

    return Py::Boolean(group->GetBool("Enabled", true));
}

Py::Object HistoryViewPy::setEnabled(const Py::Tuple& args)
{
    int enabled = 1;
    if (!PyArg_ParseTuple(args.ptr(), "i", &enabled)) {
        throw Py::Exception();
    }

    ParameterGrp::handle group = App::GetApplication()
                                     .GetUserParameter()
                                     .GetGroup("BaseApp")
                                     ->GetGroup("Preferences")
                                     ->GetGroup("DockWindows")
                                     ->GetGroup("HistoryView");

    group->SetBool("Enabled", enabled != 0);
    return Py::None();
}


// Module initialization
void Gui::HistoryView::initHistoryViewPy()
{
    static HistoryViewPy* mod = new HistoryViewPy();
    Q_UNUSED(mod);
}
