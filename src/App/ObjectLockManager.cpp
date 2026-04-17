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

#include "PreCompiled.h"

#include "ObjectLockManager.h"

#include <Base/Console.h>

#include <chrono>
#include <ctime>
#include <iomanip>
#include <sstream>

using namespace App;

namespace
{
    std::string nowISO8601()
    {
        auto now  = std::chrono::system_clock::now();
        auto time = std::chrono::system_clock::to_time_t(now);
        struct tm buf {};
#ifdef _WIN32
        gmtime_s(&buf, &time);
#else
        gmtime_r(&time, &buf);
#endif
        std::ostringstream ss;
        ss << std::put_time(&buf, "%FT%TZ");
        return ss.str();
    }
}


ObjectLockManager::ObjectLockManager()  = default;
ObjectLockManager::~ObjectLockManager() = default;

// ── Collaborative locks ─────────────────────────────────────────────────

bool ObjectLockManager::lockObject(const std::string& objectName,
                                   const std::string& userName)
{
    std::lock_guard<std::mutex> guard(lockTableMutex);

    auto it = locks.find(objectName);
    if (it != locks.end()) {
        // Already locked
        if (it->second.owner == userName) {
            return true;   // Same user → idempotent
        }
        Base::Console().Warning(
            "ObjectLockManager: '%s' is already locked by '%s'\n",
            objectName.c_str(), it->second.owner.c_str());
        return false;
    }

    ObjectLock lk;
    lk.objectName = objectName;
    lk.owner      = userName;
    lk.timestamp  = nowISO8601();
    lk.exclusive  = true;
    locks[objectName] = std::move(lk);

    Base::Console().Log(
        "ObjectLockManager: '%s' locked by '%s'\n",
        objectName.c_str(), userName.c_str());
    return true;
}

bool ObjectLockManager::unlockObject(const std::string& objectName,
                                     const std::string& userName)
{
    std::lock_guard<std::mutex> guard(lockTableMutex);

    auto it = locks.find(objectName);
    if (it == locks.end()) {
        return true;  // Not locked → success (idempotent)
    }
    if (it->second.owner != userName) {
        Base::Console().Warning(
            "ObjectLockManager: Cannot unlock '%s' — owned by '%s', not '%s'\n",
            objectName.c_str(), it->second.owner.c_str(), userName.c_str());
        return false;
    }
    locks.erase(it);
    Base::Console().Log(
        "ObjectLockManager: '%s' unlocked by '%s'\n",
        objectName.c_str(), userName.c_str());
    return true;
}

std::string ObjectLockManager::lockedBy(const std::string& objectName) const
{
    std::lock_guard<std::mutex> guard(lockTableMutex);
    auto it = locks.find(objectName);
    return (it != locks.end()) ? it->second.owner : std::string{};
}

bool ObjectLockManager::isLocked(const std::string& objectName) const
{
    std::lock_guard<std::mutex> guard(lockTableMutex);
    return locks.find(objectName) != locks.end();
}

bool ObjectLockManager::isLockedByOther(const std::string& objectName,
                                        const std::string& currentUser) const
{
    std::lock_guard<std::mutex> guard(lockTableMutex);
    auto it = locks.find(objectName);
    if (it == locks.end()) {
        return false;
    }
    return it->second.owner != currentUser;
}

std::vector<ObjectLock> ObjectLockManager::allLocks() const
{
    std::lock_guard<std::mutex> guard(lockTableMutex);
    std::vector<ObjectLock> result;
    result.reserve(locks.size());
    for (const auto& kv : locks) {
        result.push_back(kv.second);
    }
    return result;
}

void ObjectLockManager::clearAll()
{
    std::lock_guard<std::mutex> guard(lockTableMutex);
    locks.clear();
}

// ── Local (in-process) locks ────────────────────────────────────────────

std::shared_mutex& ObjectLockManager::getMutex(const std::string& objectName)
{
    std::lock_guard<std::mutex> guard(mutexTableMutex);
    auto& ptr = objectMutexes[objectName];
    if (!ptr) {
        ptr = std::make_unique<std::shared_mutex>();
    }
    return *ptr;
}

void ObjectLockManager::acquireRead(const std::string& objectName)
{
    getMutex(objectName).lock_shared();
}

void ObjectLockManager::releaseRead(const std::string& objectName)
{
    getMutex(objectName).unlock_shared();
}

void ObjectLockManager::acquireWrite(const std::string& objectName)
{
    getMutex(objectName).lock();
}

void ObjectLockManager::releaseWrite(const std::string& objectName)
{
    getMutex(objectName).unlock();
}

// ── Serialization ───────────────────────────────────────────────────────

void ObjectLockManager::saveLocks(std::ostream& os) const
{
    std::lock_guard<std::mutex> guard(lockTableMutex);

    os << "  <ObjectLocks count=\"" << locks.size() << "\">\n";
    for (const auto& kv : locks) {
        const auto& lk = kv.second;
        os << "    <Lock object=\"" << lk.objectName
           << "\" owner=\"" << lk.owner
           << "\" timestamp=\"" << lk.timestamp
           << "\" exclusive=\"" << (lk.exclusive ? "true" : "false")
           << "\"/>\n";
    }
    os << "  </ObjectLocks>\n";
}

void ObjectLockManager::loadLocks(const std::string& xmlContent)
{
    std::lock_guard<std::mutex> guard(lockTableMutex);
    locks.clear();

    // Simple tag-level parsing (no full XML parser dependency needed here)
    // Look for <Lock object="..." owner="..." timestamp="..." exclusive="..."/>
    std::string::size_type pos = 0;
    while ((pos = xmlContent.find("<Lock ", pos)) != std::string::npos) {
        auto end = xmlContent.find("/>", pos);
        if (end == std::string::npos) {
            break;
        }
        std::string tag = xmlContent.substr(pos, end - pos);

        auto extractAttr = [&tag](const std::string& name) -> std::string {
            auto apos = tag.find(name + "=\"");
            if (apos == std::string::npos) {
                return {};
            }
            apos += name.size() + 2;
            auto epos = tag.find('"', apos);
            return (epos != std::string::npos) ? tag.substr(apos, epos - apos)
                                                : std::string{};
        };

        ObjectLock lk;
        lk.objectName = extractAttr("object");
        lk.owner      = extractAttr("owner");
        lk.timestamp  = extractAttr("timestamp");
        lk.exclusive  = (extractAttr("exclusive") != "false");

        if (lk.isValid()) {
            locks[lk.objectName] = std::move(lk);
        }

        pos = end + 2;
    }

    if (!locks.empty()) {
        Base::Console().Log(
            "ObjectLockManager: loaded %zu lock(s)\n", locks.size());
    }
}
