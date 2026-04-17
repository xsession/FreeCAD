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

#include <functional>
#include <memory>
#include <string>
#include <typeindex>
#include <unordered_map>
#include <vector>

#include <fastsignals/signal.h>
#include <FCGlobal.h>

namespace App {
class Document;
class DocumentObject;
}

namespace Gui {

/// Result of a dispatched command execution
enum class DispatchResult {
    Success,
    Failed,
    Cancelled,
    InvalidTarget
};

/// Base class for all dispatchable commands.
/// Unlike Gui::Command which represents a UI action, DispatchableCmd
/// represents a data-mutation operation that can be undone/redone and
/// serialised to the macro recorder.
class GuiExport DispatchableCmd
{
public:
    virtual ~DispatchableCmd() = default;

    /// Human-readable label for undo stack
    virtual std::string label() const = 0;

    /// Execute the command (called by CommandDispatcher)
    virtual DispatchResult execute() = 0;

    /// Return the Python macro string for this operation
    virtual std::string toPython() const { return {}; }

    /// Type identifier for handler lookup
    virtual std::type_index typeId() const = 0;
};

/// A property-mutation command: dispatch(SetPropertyCmd{obj, "Length", "42"})
class GuiExport SetPropertyCmd : public DispatchableCmd
{
public:
    SetPropertyCmd(App::DocumentObject* obj,
                   const char* propertyName,
                   const char* value);

    std::string label() const override;
    DispatchResult execute() override;
    std::string toPython() const override;
    std::type_index typeId() const override { return typeid(SetPropertyCmd); }

private:
    App::DocumentObject* _obj;
    std::string _propName;
    std::string _value;
};

/// An async variant that runs the heavy work off the GUI thread
/// and emits finished() when done.
class GuiExport AsyncDispatchableCmd : public DispatchableCmd
{
public:
    /// Override to perform work. Called from a worker thread.
    virtual DispatchResult executeAsync() = 0;

    /// Final execute dispatches to worker, then signals.
    DispatchResult execute() override;

    fastsignals::signal<void(DispatchResult)> finished;
};

/// Handler callback type: receives the concrete command and returns a result
using CmdHandler = std::function<DispatchResult(DispatchableCmd&)>;

/// Central command bus. All document mutations should flow through here
/// so that undo/redo, macro recording, and audit trail are applied uniformly.
class GuiExport CommandDispatcher
{
public:
    static CommandDispatcher& instance();

    /// Dispatch a command. Opens an undo transaction, executes the command,
    /// records the macro string, and commits or aborts the transaction.
    DispatchResult dispatch(std::unique_ptr<DispatchableCmd> cmd);

    /// Convenience: dispatch an in-place-constructed command
    template <typename Cmd, typename... Args>
    DispatchResult dispatch(Args&&... args)
    {
        return dispatch(std::make_unique<Cmd>(std::forward<Args>(args)...));
    }

    /// Register a custom handler for a command type.
    /// If no handler is registered, the command's own execute() is called.
    void registerHandler(std::type_index type, CmdHandler handler);

    /// Remove a handler
    void removeHandler(std::type_index type);

    /// Signal emitted before any command executes
    fastsignals::signal<void(const DispatchableCmd&)> preDispatch;

    /// Signal emitted after a command completes
    fastsignals::signal<void(const DispatchableCmd&, DispatchResult)> postDispatch;

private:
    CommandDispatcher() = default;
    std::unordered_map<std::type_index, CmdHandler> _handlers;
};

} // namespace Gui
