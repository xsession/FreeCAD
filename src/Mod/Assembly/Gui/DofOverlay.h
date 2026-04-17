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

#include <Mod/Assembly/AssemblyGlobal.h>

#include <Base/Placement.h>
#include <Base/Vector3D.h>

#include <vector>

class SoSeparator;
class SoSwitch;

namespace App
{
class DocumentObject;
}

namespace Assembly
{
class AssemblyObject;
}

namespace AssemblyGui
{

/// Represents one remaining degree of freedom for a part.
struct DofIndicator
{
    enum class Kind
    {
        Translation,  ///< Linear arrow along axis
        Rotation      ///< Circular arc around axis
    };

    Kind kind;
    Base::Vector3d axis;    ///< Direction (normalized) in world coordinates
    Base::Vector3d origin;  ///< Placement center of the part
};

/// Analyzes an assembly's constraint state and produces DOF indicators,
/// then builds Coin3D scene geometry to visualize them.
class AssemblyGuiExport DofOverlay
{
public:
    DofOverlay();
    ~DofOverlay();

    /// Build a Coin3D scene sub-graph for the DOF overlay.
    /// Call after each solve.  The returned SoSwitch is ref'd and
    /// should be added to the assembly's ViewProvider root.
    SoSwitch* buildOverlay(Assembly::AssemblyObject* assembly);

    /// Toggle visibility of the DOF indicators.
    void setVisible(bool visible);

    /// Clear all visualization nodes.
    void clear();

    /// Analyze which DOF directions remain free for each part.
    static std::vector<DofIndicator> analyze(Assembly::AssemblyObject* assembly);

private:
    /// Create an arrow node for a translational DOF.
    static SoSeparator* makeArrow(const DofIndicator& dof, float scale);

    /// Create a circular arc node for a rotational DOF.
    static SoSeparator* makeArc(const DofIndicator& dof, float scale);

    SoSwitch* rootSwitch{nullptr};
};

}  // namespace AssemblyGui
