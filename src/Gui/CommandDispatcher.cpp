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

#include <sstream>

#include <App/Document.h>
#include <App/DocumentObject.h>
#include <App/Property.h>
#include <Base/Console.h>

#include "CommandDispatcher.h"
#include "Command.h"
#include "Application.h"
#include "Document.h"

using namespace Gui;

// ---------------------------------------------------------------------------
// SetPropertyCmd
// ---------------------------------------------------------------------------

SetPropertyCmd::SetPropertyCmd(App::DocumentObject* obj,
                               const char* propertyName,
                               const char* value)
    : _obj(obj)
    , _propName(propertyName ? propertyName : "")
    , _value(value ? value : "")
{}

std::string SetPropertyCmd::label() const
{
    std::string lbl = "Set ";
    lbl += _propName;
    return lbl;
}

DispatchResult SetPropertyCmd::execute()
{
    if (!_obj) {
        return DispatchResult::InvalidTarget;
    }

    auto* prop = _obj->getPropertyByName(_propName.c_str());
    if (!prop) {
        Base::Console().Error("CommandDispatcher: property '%s' not found on '%s'\n",
                              _propName.c_str(), _obj->getNameInDocument());
        return DispatchResult::Failed;
    }

    // Use Python command to set the property value, which handles all
    // property types through the Python interface
    std::string pyCmd = toPython();
    if (pyCmd.empty()) {
        return DispatchResult::Failed;
    }

    try {
        Command::runCommand(Command::Doc, "%s", pyCmd.c_str());
    }
    catch (...) {
        return DispatchResult::Failed;
    }
    return DispatchResult::Success;
}

std::string SetPropertyCmd::toPython() const
{
    if (!_obj || !_obj->getDocument()) {
        return {};
    }

    std::ostringstream ss;
    ss << "FreeCAD.getDocument('" << _obj->getDocument()->getName()
       << "').getObject('" << _obj->getNameInDocument()
       << "')." << _propName << " = " << _value;
    return ss.str();
}

// ---------------------------------------------------------------------------
// AsyncDispatchableCmd
// ---------------------------------------------------------------------------

DispatchResult AsyncDispatchableCmd::execute()
{
    // In this implementation we run synchronously but signal completion.
    // A full implementation would use QThread / QtConcurrent.
    DispatchResult result = executeAsync();
    finished(result);
    return result;
}

// ---------------------------------------------------------------------------
// CommandDispatcher (singleton)
// ---------------------------------------------------------------------------

CommandDispatcher& CommandDispatcher::instance()
{
    static CommandDispatcher inst;
    return inst;
}

DispatchResult CommandDispatcher::dispatch(std::unique_ptr<DispatchableCmd> cmd)
{
    if (!cmd) {
        return DispatchResult::Failed;
    }

    // Notify listeners
    preDispatch(*cmd);

    // Look up custom handler
    DispatchResult result = DispatchResult::Failed;
    auto it = _handlers.find(cmd->typeId());
    if (it != _handlers.end()) {
        result = it->second(*cmd);
    }
    else {
        // Open an undo transaction via the standard mechanism
        auto* gdoc = Application::Instance->activeDocument();
        bool ownTransaction = false;
        if (gdoc) {
            gdoc->openCommand(cmd->label().c_str());
            ownTransaction = true;
        }

        result = cmd->execute();

        // Record macro
        std::string macro = cmd->toPython();
        if (!macro.empty() && result == DispatchResult::Success) {
            Command::doCommand(Command::Doc, "%s", macro.c_str());
        }

        if (ownTransaction) {
            if (result == DispatchResult::Success) {
                gdoc->commitCommand();
            }
            else {
                gdoc->abortCommand();
            }
        }
    }

    // Notify listeners
    postDispatch(*cmd, result);

    return result;
}

void CommandDispatcher::registerHandler(std::type_index type, CmdHandler handler)
{
    _handlers[type] = std::move(handler);
}

void CommandDispatcher::removeHandler(std::type_index type)
{
    _handlers.erase(type);
}
