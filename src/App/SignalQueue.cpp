// SPDX-License-Identifier: LGPL-2.1-or-later

/***************************************************************************
 *   Copyright (c) 2026 FreeCAD contributors                              *
 *                                                                         *
 *   This file is part of FreeCAD.                                         *
 *                                                                         *
 *   FreeCAD is free software: you can redistribute it and/or modify it    *
 *   under the terms of the GNU Lesser General Public License as           *
 *   published by the Free Software Foundation, either version 2.1 of the  *
 *   License, or (at your option) any later version.                       *
 *                                                                         *
 *   FreeCAD is distributed in the hope that it will be useful, but        *
 *   WITHOUT ANY WARRANTY; without even the implied warranty of            *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU      *
 *   Lesser General Public License for more details.                       *
 *                                                                         *
 *   You should have received a copy of the GNU Lesser General Public      *
 *   License along with FreeCAD. If not, see                               *
 *   <https://www.gnu.org/licenses/>.                                      *
 *                                                                         *
 **************************************************************************/

#include "PreCompiled.h"

#include "SignalQueue.h"

#include <Base/Console.h>
#include <Base/Exception.h>

using namespace App;

SignalQueue& SignalQueue::instance()
{
    static SignalQueue queue;
    return queue;
}

void SignalQueue::enqueue(std::function<void()> signal)
{
    if (!_enabled) {
        // When not in queueing mode, fire immediately (legacy behavior)
        signal();
        return;
    }
    std::lock_guard lock(_mutex);
    _queue.push_back(std::move(signal));
}

void SignalQueue::flush()
{
    // Swap out the queue under the lock, then fire outside the lock.
    // This avoids holding the mutex during signal emission (which may
    // trigger re-entrant enqueue calls).
    std::vector<std::function<void()>> pending;
    {
        std::lock_guard lock(_mutex);
        pending.swap(_queue);
    }

    for (auto& signal : pending) {
        try {
            signal();
        }
        catch (const Base::Exception& e) {
            e.reportException();
            Base::Console().error("SignalQueue::flush: exception in queued signal: %s\n",
                                  e.what());
        }
        catch (const std::exception& e) {
            Base::Console().error("SignalQueue::flush: exception in queued signal: %s\n",
                                  e.what());
        }
    }
}

void SignalQueue::clear()
{
    std::lock_guard lock(_mutex);
    _queue.clear();
}

size_t SignalQueue::size() const
{
    std::lock_guard lock(_mutex);
    return _queue.size();
}

bool SignalQueue::empty() const
{
    std::lock_guard lock(_mutex);
    return _queue.empty();
}

void SignalQueue::setEnabled(bool enabled)
{
    _enabled = enabled;
}

bool SignalQueue::isEnabled() const
{
    return _enabled;
}
