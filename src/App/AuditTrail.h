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

#include <string>
#include <vector>
#include <chrono>
#include <mutex>
#include <functional>

namespace App
{

/// A single audit trail entry recording one atomic change to the document.
/// For regulated industries (aerospace, medical devices) that require
/// full traceability of engineering changes.
struct AppExport AuditEntry
{
    using Clock = std::chrono::system_clock;
    using TimePoint = Clock::time_point;

    TimePoint   timestamp;
    std::string username;
    std::string action;        ///< e.g., "PropertyChanged", "FeatureAdded", "Recomputed"
    std::string objectName;    ///< Name of the affected DocumentObject (empty for document-level)
    std::string propertyName;  ///< Name of the changed property (empty if N/A)
    std::string oldValue;      ///< Serialized old value (truncated to 1024 chars)
    std::string newValue;      ///< Serialized new value (truncated to 1024 chars)
    std::string documentHash;  ///< SHA-256 of document state after this change (optional)
};

/// Tracks all modifications to a Document for compliance auditing.
///
/// Enable via: User parameter:BaseApp/Preferences/Document/AuditTrailEnabled = true
///
/// The trail is stored in the Document.xml inside an `<AuditTrail>` section
/// and can be exported to CSV for external compliance systems.
class AppExport AuditTrail
{
public:
    AuditTrail();
    ~AuditTrail();

    /// Check if audit trailing is enabled globally.
    static bool isEnabled();

    /// Record a property change.
    void recordPropertyChange(const std::string& objectName,
                              const std::string& propertyName,
                              const std::string& oldValue,
                              const std::string& newValue);

    /// Record an object-level action (add, remove, rename, etc.).
    void recordAction(const std::string& objectName,
                      const std::string& action,
                      const std::string& detail = {});

    /// Record a document-level event (save, open, recompute, etc.).
    void recordDocumentEvent(const std::string& action,
                             const std::string& detail = {});

    /// Get all entries (read-only).
    const std::vector<AuditEntry>& entries() const { return trail; }

    /// Clear all entries (e.g., for a fresh document).
    void clear();

    /// Export the trail to CSV format.
    std::string exportCsv() const;

    /// Set a callback to compute document hash after each entry.
    using HashCallback = std::function<std::string()>;
    void setHashCallback(HashCallback cb) { hashCallback = std::move(cb); }

private:
    void addEntry(AuditEntry entry);
    static std::string currentUsername();
    static std::string formatTimestamp(AuditEntry::TimePoint tp);

    std::vector<AuditEntry> trail;
    HashCallback hashCallback;
    mutable std::mutex mutex;
};

}  // namespace App
