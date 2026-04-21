# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""OpticalPhysicsModel - optical simulation settings."""

from flow_studio.objects.base_object import BaseFlowObject


class OpticalPhysicsModel(BaseFlowObject):
    """Defines ray-optics / wave-optics simulation parameters."""

    Type = "FlowStudio::OpticalPhysicsModel"

    def __init__(self, obj):
        super().__init__(obj)

        obj.addProperty("App::PropertyEnumeration", "OpticalModel", "Physics", "Optical simulation model")
        obj.OpticalModel = [
            "Sequential Ray Trace",
            "Non-Sequential Ray Trace",
            "Illumination",
            "Wave Optics FDTD",
            "Photonic Crystal",
        ]
        obj.OpticalModel = "Non-Sequential Ray Trace"

        obj.addProperty("App::PropertyFloat", "Wavelength", "Physics", "Primary wavelength [nm]")
        obj.Wavelength = 550.0

        obj.addProperty("App::PropertyFloat", "WavelengthMin", "Physics", "Spectrum minimum [nm]")
        obj.WavelengthMin = 380.0

        obj.addProperty("App::PropertyFloat", "WavelengthMax", "Physics", "Spectrum maximum [nm]")
        obj.WavelengthMax = 780.0

        obj.addProperty("App::PropertyInteger", "RayCount", "Physics", "Number of rays for ray-tracing backends")
        obj.RayCount = 10000

        obj.addProperty("App::PropertyFloat", "PmlThickness", "Wave Optics", "PML thickness for FDTD wave optics [model units]")
        obj.PmlThickness = 1.0

        obj.addProperty("App::PropertyFloat", "Resolution", "Wave Optics", "FDTD resolution [pixels / model unit]")
        obj.Resolution = 20.0

        obj.addProperty("App::PropertyBool", "CalculateIrradiance", "Results", "Calculate irradiance / optical power density")
        obj.CalculateIrradiance = True

        obj.addProperty("App::PropertyBool", "CalculateOpticalPath", "Results", "Calculate optical path length and phase")
        obj.CalculateOpticalPath = True

        obj.addProperty("App::PropertyBool", "CalculateSpotDiagram", "Results", "Calculate detector spot diagrams")
        obj.CalculateSpotDiagram = True

