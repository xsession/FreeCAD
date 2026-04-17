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

#include "RecomputeEngine.h"

#include "Application.h"
#include "DocumentObject.h"

#include <Base/Console.h>
#include <Base/Exception.h>
#include <Base/Parameter.h>
#include <Base/Sequencer.h>

#include <algorithm>
#include <mutex>
#include <thread>
#include <unordered_map>
#include <unordered_set>

using namespace App;

FC_LOG_LEVEL_INIT("RecomputeEngine", true, true, true)

// ── Level Building ────────────────────────────────────────────────────

std::vector<RecomputeEngine::Level>
RecomputeEngine::buildLevels(const std::vector<DocumentObject*>& topoSorted)
{
    // Assign each object to the lowest level where all its dependencies
    // are in strictly earlier levels.
    //
    // Because topoSorted is in dependency order (dependencies first),
    // we can compute level(obj) = max(level(dep) for dep in outList) + 1
    // in a single forward pass.

    std::unordered_map<DocumentObject*, int> levelOf;
    int maxLevel = 0;

    for (auto* obj : topoSorted) {
        if (!obj || !obj->isAttachedToDocument()) {
            continue;
        }

        int myLevel = 0;
        for (auto* dep : obj->getOutList()) {
            auto it = levelOf.find(dep);
            if (it != levelOf.end()) {
                myLevel = std::max(myLevel, it->second + 1);
            }
        }
        levelOf[obj] = myLevel;
        maxLevel = std::max(maxLevel, myLevel);
    }

    std::vector<Level> levels(static_cast<size_t>(maxLevel) + 1);
    for (auto* obj : topoSorted) {
        auto it = levelOf.find(obj);
        if (it != levelOf.end()) {
            levels[static_cast<size_t>(it->second)].push_back(obj);
        }
    }

    return levels;
}

// ── Python Feature Detection ──────────────────────────────────────────

bool RecomputeEngine::isPythonFeature(const DocumentObject* obj)
{
    // FeaturePythonT adds a "Proxy" property of type App::PropertyPythonObject.
    // This is the most reliable way to detect Python-delegated features
    // without depending on the FeaturePython.h template.
    return obj->getPropertyByName("Proxy") != nullptr;
}

// ── Preference Query ──────────────────────────────────────────────────

bool RecomputeEngine::isEnabled()
{
    auto hGrp = GetApplication().GetParameterGroupByPath(
        "User parameter:BaseApp/Preferences/Document");
    return hGrp->GetBool("ParallelRecompute", false);
}

// ── Parallel Execution ────────────────────────────────────────────────

int RecomputeEngine::execute(const std::vector<Level>& levels,
                             std::set<DocumentObject*>& filter,
                             const ExecFunc& execFunc,
                             const PostExecFunc& postExec,
                             bool canAbort)
{
    int objectCount = 0;

    const unsigned int hwThreads = std::thread::hardware_concurrency();
    const unsigned int maxWorkers = (_maxThreads > 0) ? _maxThreads
                                                      : std::max(1u, hwThreads);

    // Count total objects for progress bar
    size_t totalObjects = 0;
    for (auto& level : levels) {
        totalObjects += level.size();
    }

    std::unique_ptr<Base::SequencerLauncher> seq;
    if (canAbort) {
        seq = std::make_unique<Base::SequencerLauncher>("Recompute...", totalObjects);
    }

    for (const auto& level : levels) {
        if (isCancelled()) {
            FC_LOG("RecomputeEngine: cancelled by user");
            break;
        }

        // Partition the level into C++ features (parallelisable) and
        // Python features (must acquire GIL, serialised).
        std::vector<DocumentObject*> cppFeatures;
        std::vector<DocumentObject*> pyFeatures;

        for (auto* obj : level) {
            if (!obj->isAttachedToDocument() || filter.count(obj) != 0) {
                if (seq) {
                    seq->next(true);
                }
                continue;
            }
            if (isPythonFeature(obj)) {
                pyFeatures.push_back(obj);
            }
            else {
                cppFeatures.push_back(obj);
            }
        }

        // ── Execute C++ features in parallel ──────────────────────────

        if (cppFeatures.size() > 1 && maxWorkers > 1) {
            // Shared state for the parallel region
            std::mutex resultMutex;
            std::atomic<bool> abortFlag{false};

            // Divide work among threads
            const size_t nFeatures = cppFeatures.size();
            const size_t nWorkers = std::min(static_cast<size_t>(maxWorkers), nFeatures);

            std::vector<std::thread> workers;
            workers.reserve(nWorkers);

            // Work-stealing index: each thread atomically claims the next feature
            std::atomic<size_t> nextIdx{0};

            for (size_t w = 0; w < nWorkers; ++w) {
                workers.emplace_back([&]() {
                    while (!abortFlag.load(std::memory_order_relaxed)) {
                        size_t idx = nextIdx.fetch_add(1, std::memory_order_relaxed);
                        if (idx >= nFeatures) {
                            break;
                        }
                        auto* obj = cppFeatures[idx];

                        // Lock the object for exclusive write access
                        std::unique_lock objLock(obj->writeLock());

                        int res = 0;
                        bool doRecompute = false;
                        if (obj->mustRecompute()) {
                            doRecompute = true;
                            res = execFunc(obj);
                        }

                        {
                            std::lock_guard lock(resultMutex);
                            if (res != 0) {
                                if (res < 0) {
                                    abortFlag.store(true, std::memory_order_relaxed);
                                }
                                // Mark dependents for filtering
                                obj->getInListEx(filter, true);
                                filter.insert(obj);
                            }
                            else {
                                if (doRecompute) {
                                    ++objectCount;
                                }
                                postExec(obj, doRecompute);
                            }
                        }
                    }
                });
            }

            for (auto& t : workers) {
                t.join();
            }

            if (abortFlag.load()) {
                break;  // Abort entire recompute
            }

            if (seq) {
                for (size_t i = 0; i < cppFeatures.size(); ++i) {
                    seq->next(true);
                }
            }
        }
        else {
            // Single C++ feature or single-threaded: execute serially
            for (auto* obj : cppFeatures) {
                if (isCancelled()) {
                    break;
                }

                bool doRecompute = false;
                if (obj->mustRecompute()) {
                    doRecompute = true;
                    int res = execFunc(obj);
                    if (res != 0) {
                        if (res < 0) {
                            return objectCount;  // Abort
                        }
                        obj->getInListEx(filter, true);
                        filter.insert(obj);
                        if (seq) {
                            seq->next(true);
                        }
                        continue;
                    }
                    ++objectCount;
                }
                postExec(obj, doRecompute);
                if (seq) {
                    seq->next(true);
                }
            }
        }

        // ── Execute Python features serially (GIL-bound) ─────────────

        for (auto* obj : pyFeatures) {
            if (isCancelled()) {
                break;
            }
            bool doRecompute = false;
            if (obj->mustRecompute()) {
                doRecompute = true;
                int res = execFunc(obj);
                if (res != 0) {
                    if (res < 0) {
                        return objectCount;  // Abort
                    }
                    obj->getInListEx(filter, true);
                    filter.insert(obj);
                    if (seq) {
                        seq->next(true);
                    }
                    continue;
                }
                ++objectCount;
            }
            postExec(obj, doRecompute);
            if (seq) {
                seq->next(true);
            }
        }
    }

    return objectCount;
}
