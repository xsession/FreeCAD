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

#pragma once

#include <functional>
#include <mutex>
#include <vector>
#include <FCGlobal.h>

namespace Base
{

/// Thread-safe queue for deferring signal/callback emission.
///
/// During parallel recompute, signals that must fire on the main thread
/// (GUI updates, Python observer callbacks) are enqueued here instead of
/// being emitted immediately.  After the parallel batch completes, the
/// main thread calls flush() to emit all queued signals in order.
class BaseExport SignalQueue
{
public:
    SignalQueue() = default;

    /// Enqueue a callable to be executed later on the main thread.
    void enqueue(std::function<void()> fn)
    {
        std::lock_guard lock(mutex_);
        pending_.push_back(std::move(fn));
    }

    /// Execute all queued callables on the calling thread, then clear the queue.
    /// This must be called from the main thread.
    void flush()
    {
        std::vector<std::function<void()>> batch;
        {
            std::lock_guard lock(mutex_);
            batch.swap(pending_);
        }
        for (auto& fn : batch) {
            fn();
        }
    }

    /// Discard all queued callables without executing them.
    void clear()
    {
        std::lock_guard lock(mutex_);
        pending_.clear();
    }

    /// Return the number of queued callables.
    std::size_t size() const
    {
        std::lock_guard lock(mutex_);
        return pending_.size();
    }

    /// Check if the queue is empty.
    bool empty() const
    {
        std::lock_guard lock(mutex_);
        return pending_.empty();
    }

private:
    mutable std::mutex mutex_;
    std::vector<std::function<void()>> pending_;
};

}  // namespace Base
