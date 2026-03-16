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

#include <CXX/Extensions.hxx>
#include <CXX/Objects.hxx>

namespace Gui {
namespace HistoryView {

/**
 * @brief Python module for accessing the FreeCAD Modification History.
 *
 * Provides a `FreeCADGui.HistoryView` module with:
 *
 *   FreeCADGui.HistoryView.getEntries()         -> list of dicts
 *   FreeCADGui.HistoryView.getEntryCount()      -> int
 *   FreeCADGui.HistoryView.exportToText()       -> str
 *   FreeCADGui.HistoryView.clear()
 *   FreeCADGui.HistoryView.rollbackTo(index)    -> bool
 *   FreeCADGui.HistoryView.editFeature(index)   -> bool
 *   FreeCADGui.HistoryView.toggleSuppressed(index) -> bool
 *   FreeCADGui.HistoryView.createGroup(name, start, end) -> int
 *   FreeCADGui.HistoryView.removeGroup(groupId)
 *   FreeCADGui.HistoryView.isEnabled()          -> bool
 *   FreeCADGui.HistoryView.setEnabled(bool)
 */
class HistoryViewPy : public Py::ExtensionModule<HistoryViewPy>
{
public:
    HistoryViewPy();
    ~HistoryViewPy() override = default;

private:
    Py::Object getEntries(const Py::Tuple& args);
    Py::Object getEntryCount(const Py::Tuple& args);
    Py::Object exportToText(const Py::Tuple& args);
    Py::Object clear(const Py::Tuple& args);
    Py::Object rollbackTo(const Py::Tuple& args);
    Py::Object editFeature(const Py::Tuple& args);
    Py::Object toggleSuppressed(const Py::Tuple& args);
    Py::Object createGroup(const Py::Tuple& args);
    Py::Object removeGroup(const Py::Tuple& args);
    Py::Object isEnabled(const Py::Tuple& args);
    Py::Object setEnabled(const Py::Tuple& args);
};

/// Initialize the HistoryView Python module
void initHistoryViewPy();

} // namespace HistoryView
} // namespace Gui
