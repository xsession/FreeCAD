# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Electrostatic boundary conditions – electric potential, surface charge."""

from flow_studio.objects.base_bc import BaseBoundaryCondition


class BCElectricPotential(BaseBoundaryCondition):
    """Fixed electric potential (voltage) on selected faces / electrodes."""

    Type = "FlowStudio::BCElectricPotential"

    def __init__(self, obj):
        super().__init__(obj)
        obj.BCLabel = "Electric Potential"

        obj.addProperty(
            "App::PropertyFloat", "Potential", "Electrostatic",
            "Electric potential [V]"
        )
        obj.Potential = 0.0

        obj.addProperty(
            "App::PropertyBool", "CalculateForce", "Electrostatic",
            "Calculate electric force on this electrode"
        )
        obj.CalculateForce = True


class BCSurfaceCharge(BaseBoundaryCondition):
    """Surface charge density on selected faces."""

    Type = "FlowStudio::BCSurfaceCharge"

    def __init__(self, obj):
        super().__init__(obj)
        obj.BCLabel = "Surface Charge"

        obj.addProperty(
            "App::PropertyFloat", "SurfaceChargeDensity", "Electrostatic",
            "Surface charge density [C/m²]"
        )
        obj.SurfaceChargeDensity = 0.0


class BCElectricSymmetry(BaseBoundaryCondition):
    """Electric field symmetry (∂V/∂n = 0) on selected faces."""

    Type = "FlowStudio::BCElectricSymmetry"

    def __init__(self, obj):
        super().__init__(obj)
        obj.BCLabel = "Electric Symmetry"


class BCElectricFlux(BaseBoundaryCondition):
    """Prescribed electric flux (normal displacement field) boundary."""

    Type = "FlowStudio::BCElectricFlux"

    def __init__(self, obj):
        super().__init__(obj)
        obj.BCLabel = "Electric Flux"

        obj.addProperty(
            "App::PropertyFloat", "FluxDensity", "Electrostatic",
            "Electric flux density normal component [C/m^2]"
        )
        obj.FluxDensity = 0.0
