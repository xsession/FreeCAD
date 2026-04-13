# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""PhysicsModel – define flow physics (like FloEFD General Settings)."""

from flow_studio.objects.base_object import BaseFlowObject


class PhysicsModel(BaseFlowObject):
    """Defines the physical model: turbulence, compressibility, etc."""

    Type = "FlowStudio::PhysicsModel"

    def __init__(self, obj):
        super().__init__(obj)

        # Flow regime
        obj.addProperty(
            "App::PropertyEnumeration", "FlowRegime", "Physics",
            "Laminar or turbulent flow"
        )
        obj.FlowRegime = ["Laminar", "Turbulent"]
        obj.FlowRegime = "Turbulent"

        # Turbulence model
        obj.addProperty(
            "App::PropertyEnumeration", "TurbulenceModel", "Physics",
            "Turbulence closure model"
        )
        obj.TurbulenceModel = [
            "kEpsilon",
            "kOmega",
            "kOmegaSST",
            "SpalartAllmaras",
            "LES-Smagorinsky",
            "LES-WALE",
            "LBM-Implicit",  # For FluidX3D (lattice Boltzmann implicit turbulence)
        ]
        obj.TurbulenceModel = "kOmegaSST"

        # Compressibility
        obj.addProperty(
            "App::PropertyEnumeration", "Compressibility", "Physics",
            "Flow compressibility assumption"
        )
        obj.Compressibility = ["Incompressible", "Compressible", "Weakly-Compressible"]
        obj.Compressibility = "Incompressible"

        # Steady / transient
        obj.addProperty(
            "App::PropertyEnumeration", "TimeModel", "Physics",
            "Steady-state or transient simulation"
        )
        obj.TimeModel = ["Steady", "Transient"]
        obj.TimeModel = "Steady"

        # Gravity
        obj.addProperty(
            "App::PropertyBool", "Gravity", "Physics",
            "Enable gravitational acceleration"
        )
        obj.Gravity = False
        obj.addProperty(
            "App::PropertyAcceleration", "GravityVector", "Physics",
            "Gravitational acceleration vector magnitude"
        )

        # Heat transfer
        obj.addProperty(
            "App::PropertyBool", "HeatTransfer", "Physics",
            "Enable heat transfer (energy equation)"
        )
        obj.HeatTransfer = False

        # Buoyancy
        obj.addProperty(
            "App::PropertyBool", "Buoyancy", "Physics",
            "Enable buoyancy-driven flow (Boussinesq approximation)"
        )
        obj.Buoyancy = False

        # Free surface (VoF)
        obj.addProperty(
            "App::PropertyBool", "FreeSurface", "Physics",
            "Enable Volume-of-Fluid free surface tracking"
        )
        obj.FreeSurface = False

        # Passive scalar
        obj.addProperty(
            "App::PropertyBool", "PassiveScalar", "Physics",
            "Enable passive scalar transport"
        )
        obj.PassiveScalar = False
