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

#include <atomic>
#include <functional>
#include <set>
#include <vector>

#include <FCGlobal.h>

namespace App
{

class Document;
class DocumentObject;

/// Level-parallel DAG-based recompute engine.
///
/// Builds topological "levels" from the dependency graph where all objects in
/// the same level are independent and can execute concurrently.  Python features
/// are serialised via the GIL within each level.
///
/// Usage:
///   RecomputeEngine engine;
///   engine.setCancelToken(&cancelFlag);
///   int count = engine.parallelRecompute(doc, topoSorted, filter, hasError);
///
class AppExport RecomputeEngine
{
public:
    /// A level is a set of objects that can be executed in parallel.
    using Level = std::vector<DocumentObject*>;

    /// Callback used to execute a single feature (calls Document::_recomputeFeature).
    /// Returns 0 on success, 1 on error, -1 on abort.
    using ExecFunc = std::function<int(DocumentObject*)>;

    /// Callback fired after a feature is successfully recomputed.
    using PostExecFunc = std::function<void(DocumentObject*, bool didRecompute)>;

    RecomputeEngine() = default;

    /// Set the cancellation token.  The engine checks this between levels
    /// and aborts if the flag becomes true.
    void setCancelToken(std::atomic<bool>* token) { _cancel = token; }

    /// Build topological levels from a dependency-sorted list.
    ///
    /// @param topoSorted  Objects in topological (dependency) order.
    /// @return  Vector of levels.  Level 0 has no dependencies; level N
    ///          depends only on objects in levels 0..N-1.
    static std::vector<Level> buildLevels(const std::vector<DocumentObject*>& topoSorted);

    /// Execute a parallel recompute over the given levels.
    ///
    /// @param levels       Dependency levels from buildLevels().
    /// @param filter       Objects to skip (e.g. dependents of failed features).
    /// @param execFunc     Callback to execute a single feature.
    /// @param postExec     Callback after a feature succeeds (for signal queuing, purge, etc.).
    /// @param canAbort     Whether the user can abort via SequencerLauncher.
    /// @return  Number of objects that were actually recomputed.
    int execute(const std::vector<Level>& levels,
                std::set<DocumentObject*>& filter,
                const ExecFunc& execFunc,
                const PostExecFunc& postExec,
                bool canAbort);

    /// Check if a DocumentObject delegates its execute() to Python.
    static bool isPythonFeature(const DocumentObject* obj);

    /// Query whether parallel recompute is enabled in user preferences.
    static bool isEnabled();

    /// Maximum number of worker threads.  0 = hardware_concurrency.
    void setMaxThreads(unsigned int n) { _maxThreads = n; }

private:
    bool isCancelled() const { return _cancel && _cancel->load(std::memory_order_relaxed); }

    std::atomic<bool>* _cancel = nullptr;
    unsigned int _maxThreads = 0;
};

}  // namespace App
