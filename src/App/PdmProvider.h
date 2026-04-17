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

#include <memory>
#include <string>
#include <vector>

namespace App
{

/// Revision metadata returned by PDM providers
struct AppExport PdmRevision
{
    std::string revisionId;
    std::string author;
    std::string timestamp;   ///< ISO 8601
    std::string comment;
};

/// Abstract interface for Product Data Management integration.
/// External systems (Git-based PDM, Autodesk Vault, Aras Innovator, etc.)
/// implement this interface.  FreeCAD calls it for file lifecycle operations.
///
/// Register a provider via Application::setPdmProvider().
/// Only one provider is active at a time.
class AppExport PdmProvider
{
public:
    virtual ~PdmProvider() = default;

    /// Short display name for the provider (e.g., "Git PDM", "Vault")
    virtual std::string name() const = 0;

    // ── File lifecycle ──────────────────────────────────────────────

    /// Check out a file for exclusive editing.
    /// @return true on success
    virtual bool checkOut(const std::string& filePath) = 0;

    /// Check in a file with a revision comment.
    virtual bool checkIn(const std::string& filePath,
                         const std::string& comment) = 0;

    /// Discard local edits and revert to the latest server version.
    virtual bool undoCheckOut(const std::string& filePath) = 0;

    // ── Query ───────────────────────────────────────────────────────

    /// Get the current revision string for a file.
    virtual std::string getRevision(const std::string& filePath) = 0;

    /// Get complete revision history.
    virtual std::vector<PdmRevision> getHistory(const std::string& filePath) = 0;

    /// Is this file currently checked out (by anyone)?
    virtual bool isCheckedOut(const std::string& filePath) = 0;

    /// Who holds the lock?  Returns empty string if not locked.
    virtual std::string lockedBy(const std::string& filePath) = 0;

    // ── Locking ─────────────────────────────────────────────────────

    /// Acquire an exclusive lock.
    virtual bool lock(const std::string& filePath) = 0;

    /// Release the lock.
    virtual bool unlock(const std::string& filePath) = 0;

    /// Retrieve the latest version of a file from the server.
    virtual bool getLatest(const std::string& filePath) = 0;
};

}  // namespace App
