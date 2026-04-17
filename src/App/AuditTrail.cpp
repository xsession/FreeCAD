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

#include "AuditTrail.h"

#include <App/Application.h>
#include <Base/Parameter.h>

#include <chrono>
#include <ctime>
#include <iomanip>
#include <sstream>

#ifdef _WIN32
#include <windows.h>
#include <lmcons.h>
#else
#include <unistd.h>
#include <pwd.h>
#endif

using namespace App;

namespace
{

constexpr size_t MaxValueLength = 1024;

std::string truncate(const std::string& s)
{
    if (s.size() <= MaxValueLength) {
        return s;
    }
    return s.substr(0, MaxValueLength) + "...";
}

}  // anonymous namespace


AuditTrail::AuditTrail() = default;
AuditTrail::~AuditTrail() = default;

bool AuditTrail::isEnabled()
{
    return App::GetApplication()
        .GetParameterGroupByPath("User parameter:BaseApp/Preferences/Document")
        ->GetBool("AuditTrailEnabled", false);
}

void AuditTrail::recordPropertyChange(const std::string& objectName,
                                       const std::string& propertyName,
                                       const std::string& oldValue,
                                       const std::string& newValue)
{
    if (!isEnabled()) {
        return;
    }
    AuditEntry entry;
    entry.action = "PropertyChanged";
    entry.objectName = objectName;
    entry.propertyName = propertyName;
    entry.oldValue = truncate(oldValue);
    entry.newValue = truncate(newValue);
    addEntry(std::move(entry));
}

void AuditTrail::recordAction(const std::string& objectName,
                               const std::string& action,
                               const std::string& detail)
{
    if (!isEnabled()) {
        return;
    }
    AuditEntry entry;
    entry.action = action;
    entry.objectName = objectName;
    entry.newValue = truncate(detail);
    addEntry(std::move(entry));
}

void AuditTrail::recordDocumentEvent(const std::string& action,
                                      const std::string& detail)
{
    if (!isEnabled()) {
        return;
    }
    AuditEntry entry;
    entry.action = action;
    entry.newValue = truncate(detail);
    addEntry(std::move(entry));
}

void AuditTrail::clear()
{
    std::lock_guard<std::mutex> lock(mutex);
    trail.clear();
}

void AuditTrail::addEntry(AuditEntry entry)
{
    std::lock_guard<std::mutex> lock(mutex);
    entry.timestamp = AuditEntry::Clock::now();
    entry.username = currentUsername();
    if (hashCallback) {
        entry.documentHash = hashCallback();
    }
    trail.push_back(std::move(entry));
}

std::string AuditTrail::currentUsername()
{
#ifdef _WIN32
    char buf[UNLEN + 1];
    DWORD size = UNLEN + 1;
    if (GetUserNameA(buf, &size)) {
        return std::string(buf, size - 1);
    }
    return "unknown";
#else
    const char* user = getenv("USER");
    if (user) {
        return user;
    }
    struct passwd* pw = getpwuid(getuid());
    return pw ? pw->pw_name : "unknown";
#endif
}

std::string AuditTrail::formatTimestamp(AuditEntry::TimePoint tp)
{
    auto time = AuditEntry::Clock::to_time_t(tp);
    std::tm tm{};
#ifdef _WIN32
    gmtime_s(&tm, &time);
#else
    gmtime_r(&time, &tm);
#endif
    std::ostringstream oss;
    oss << std::put_time(&tm, "%Y-%m-%dT%H:%M:%SZ");
    return oss.str();
}

std::string AuditTrail::exportCsv() const
{
    std::lock_guard<std::mutex> lock(mutex);

    std::ostringstream csv;
    csv << "Timestamp,User,Action,Object,Property,OldValue,NewValue,Hash\n";

    auto csvEscape = [](const std::string& s) -> std::string {
        if (s.find_first_of(",\"\n\r") == std::string::npos) {
            return s;
        }
        std::string escaped = "\"";
        for (char c : s) {
            if (c == '"') {
                escaped += "\"\"";
            }
            else {
                escaped += c;
            }
        }
        escaped += "\"";
        return escaped;
    };

    for (const auto& e : trail) {
        csv << formatTimestamp(e.timestamp) << ","
            << csvEscape(e.username) << ","
            << csvEscape(e.action) << ","
            << csvEscape(e.objectName) << ","
            << csvEscape(e.propertyName) << ","
            << csvEscape(e.oldValue) << ","
            << csvEscape(e.newValue) << ","
            << csvEscape(e.documentHash) << "\n";
    }

    return csv.str();
}
