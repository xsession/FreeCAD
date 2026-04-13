# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Symmetry boundary condition."""

from flow_studio.objects.base_bc import BaseBoundaryCondition


class BCSymmetry(BaseBoundaryCondition):
    """Symmetry plane – zero normal velocity and zero normal gradients."""

    Type = "FlowStudio::BCSymmetry"

    def __init__(self, obj):
        super().__init__(obj)
        obj.BoundaryType = "symmetry"
        # Symmetry has no additional parameters – it's purely geometric
