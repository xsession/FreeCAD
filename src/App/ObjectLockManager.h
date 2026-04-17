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

#pragma once

#include <FCGlobal.h>

#include <chrono>
#include <mutex>
#include <shared_mutex>
#include <string>
#include <unordered_map>

namespace App
{

class Document;
class DocumentObject;

/// Per-object lock metadata for multi-user collaboration.
struct AppExport ObjectLock
{
    std::string objectName;   ///< Name of the locked object
    std::string owner;        ///< Username holding the lock
    std::string timestamp;    ///< ISO 8601 timestamp when lock was acquired
    bool        exclusive{true}; ///< true = write lock, false = read lock

    bool isValid() const { return !objectName.empty() && !owner.empty(); }
};

/// Manages per-object read/write locks within a Document.
///
/// Two lock levels:
///   1. **Local locks** – in-process shared_mutex per object for thread safety
///   2. **Collaborative locks** – persistent metadata locks for multi-user
///      editing (backed by PdmProvider when available)
///
/// Collaborative locks are stored in Document.xml under `<ObjectLocks>`.
/// Local locks are ephemeral (process lifetime only).
class AppExport ObjectLockManager
{
public:
    ObjectLockManager();
    ~ObjectLockManager();

    // ── Collaborative (persistent) locks ────────────────────────────

    /// Acquire a collaborative write lock on an object.
    /// @param objectName  The name of the DocumentObject.
    /// @param userName    Who is acquiring the lock.
    /// @return true if lock was acquired (or already held by same user).
    bool lockObject(const std::string& objectName, const std::string& userName);

    /// Release a collaborative lock.
    /// Only the lock owner (or an admin override) can release.
    bool unlockObject(const std::string& objectName, const std::string& userName);

    /// Query who holds the lock.  Returns empty string if unlocked.
    std::string lockedBy(const std::string& objectName) const;

    /// Is the object locked by anyone?
    bool isLocked(const std::string& objectName) const;

    /// Is the object locked by a *different* user?
    bool isLockedByOther(const std::string& objectName,
                         const std::string& currentUser) const;

    /// Get all current collaborative locks.
    std::vector<ObjectLock> allLocks() const;

    /// Remove all locks (e.g., on document close).
    void clearAll();

    // ── Local (in-process) locks for thread safety ──────────────────

    /// Acquire a shared (read) lock on an object.  Blocks until available.
    void acquireRead(const std::string& objectName);

    /// Release a shared (read) lock.
    void releaseRead(const std::string& objectName);

    /// Acquire an exclusive (write) lock on an object.  Blocks until available.
    void acquireWrite(const std::string& objectName);

    /// Release an exclusive (write) lock.
    void releaseWrite(const std::string& objectName);

    // ── Serialization ───────────────────────────────────────────────

    /// Save collaborative locks to an XML writer.
    void saveLocks(std::ostream& os) const;

    /// Load collaborative locks from XML content.
    void loadLocks(const std::string& xmlContent);

private:
    /// Get or create the shared_mutex for a given object name.
    std::shared_mutex& getMutex(const std::string& objectName);

    /// Collaborative lock table
    std::unordered_map<std::string, ObjectLock> locks;
    mutable std::mutex                           lockTableMutex;

    /// Per-object mutexes for in-process thread safety
    std::unordered_map<std::string, std::unique_ptr<std::shared_mutex>> objectMutexes;
    std::mutex                                                          mutexTableMutex;
};

}  // namespace App
