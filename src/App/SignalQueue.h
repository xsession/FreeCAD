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

namespace App
{

class DocumentObject;

/// A thread-safe queue that batches signal emissions for later main-thread delivery.
///
/// During parallel recompute, worker threads cannot safely emit signals that
/// trigger GUI updates (selection highlights, tree-view refresh, property panel
/// updates).  Instead they enqueue signal payloads here and the recompute
/// coordinator calls flush() on the main thread when a batch of work completes.
///
/// Usage from worker thread:
///   SignalQueue::instance().enqueue([&doc, obj]() {
///       doc.signalRecomputedObject(*obj);
///   });
///
/// Usage from main thread (after parallel batch):
///   SignalQueue::instance().flush();
///
class AppExport SignalQueue
{
public:
    /// Get the global SignalQueue singleton.
    static SignalQueue& instance();

    /// Enqueue a signal emission to be fired later on the main thread.
    /// Can be called from any thread.  The callable should capture all
    /// needed data by value or by safe reference.
    void enqueue(std::function<void()> signal);

    /// Fire all queued signals on the calling thread (must be main thread)
    /// and clear the queue.  This is a no-op if the queue is empty.
    void flush();

    /// Discard all queued signals without firing them.
    void clear();

    /// Return the number of queued signals.
    size_t size() const;

    /// Return true if there are no queued signals.
    bool empty() const;

    /// Enable or disable queueing mode.
    /// When disabled (default), enqueue() fires the signal immediately
    /// instead of batching it.  Call setEnabled(true) before entering
    /// a parallel recompute section and setEnabled(false) after flush().
    void setEnabled(bool enabled);

    /// Return whether queueing mode is active.
    bool isEnabled() const;

private:
    SignalQueue() = default;
    SignalQueue(const SignalQueue&) = delete;
    SignalQueue& operator=(const SignalQueue&) = delete;

    mutable std::mutex _mutex;
    std::vector<std::function<void()>> _queue;
    bool _enabled = false;
};

}  // namespace App
