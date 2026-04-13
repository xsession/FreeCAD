# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Electromagnetic boundary conditions – potentials, currents, flux density."""

from flow_studio.objects.base_bc import BaseBoundaryCondition


class BCMagneticPotential(BaseBoundaryCondition):
    """Fixed magnetic vector potential on selected faces."""

    Type = "FlowStudio::BCMagneticPotential"

    def __init__(self, obj):
        super().__init__(obj)
        obj.BCLabel = "Magnetic Potential"

        obj.addProperty(
            "App::PropertyFloat", "MagneticVectorPotential", "Electromagnetic",
            "Magnetic vector potential value [Wb/m]"
        )
        obj.MagneticVectorPotential = 0.0

        obj.addProperty(
            "App::PropertyBool", "ZeroPotential", "Electromagnetic",
            "Set AV = 0 (perfect magnetic conductor / far field)"
        )
        obj.ZeroPotential = True


class BCCurrentDensity(BaseBoundaryCondition):
    """Applied current density (source) on selected bodies/faces."""

    Type = "FlowStudio::BCCurrentDensity"

    def __init__(self, obj):
        super().__init__(obj)
        obj.BCLabel = "Current Density"

        obj.addProperty(
            "App::PropertyFloat", "CurrentDensityX", "Electromagnetic",
            "Current density Jx [A/m²]"
        )
        obj.CurrentDensityX = 0.0

        obj.addProperty(
            "App::PropertyFloat", "CurrentDensityY", "Electromagnetic",
            "Current density Jy [A/m²]"
        )
        obj.CurrentDensityY = 0.0

        obj.addProperty(
            "App::PropertyFloat", "CurrentDensityZ", "Electromagnetic",
            "Current density Jz [A/m²]"
        )
        obj.CurrentDensityZ = 1e6


class BCMagneticFluxDensity(BaseBoundaryCondition):
    """Applied magnetic flux density on selected faces."""

    Type = "FlowStudio::BCMagneticFluxDensity"

    def __init__(self, obj):
        super().__init__(obj)
        obj.BCLabel = "Magnetic Flux Density"

        obj.addProperty(
            "App::PropertyFloat", "FluxDensityX", "Electromagnetic",
            "Magnetic flux density Bx [T]"
        )
        obj.FluxDensityX = 0.0

        obj.addProperty(
            "App::PropertyFloat", "FluxDensityY", "Electromagnetic",
            "Magnetic flux density By [T]"
        )
        obj.FluxDensityY = 0.0

        obj.addProperty(
            "App::PropertyFloat", "FluxDensityZ", "Electromagnetic",
            "Magnetic flux density Bz [T]"
        )
        obj.FluxDensityZ = 0.0


class BCMagneticSymmetry(BaseBoundaryCondition):
    """Magnetic symmetry boundary (tangential field = 0)."""

    Type = "FlowStudio::BCMagneticSymmetry"

    def __init__(self, obj):
        super().__init__(obj)
        obj.BCLabel = "Magnetic Symmetry"
