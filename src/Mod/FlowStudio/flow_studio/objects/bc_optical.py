# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Optical source, detector, and boundary objects."""

from flow_studio.objects.base_bc import BaseBoundaryCondition


class BCOpticalSource(BaseBoundaryCondition):
    """Optical source assigned to selected faces, edges, or parts."""

    Type = "FlowStudio::BCOpticalSource"

    def __init__(self, obj):
        super().__init__(obj)
        obj.BCLabel = "Optical Source"

        obj.addProperty("App::PropertyEnumeration", "SourceType", "Optical Source", "Source model")
        obj.SourceType = ["Collimated Beam", "Point Source", "Lambertian LED", "Gaussian Beam", "Laser Diode"]
        obj.SourceType = "Collimated Beam"

        obj.addProperty("App::PropertyFloat", "Power", "Optical Source", "Optical power [W]")
        obj.Power = 1.0

        obj.addProperty("App::PropertyFloat", "Wavelength", "Optical Source", "Center wavelength [nm]")
        obj.Wavelength = 550.0

        obj.addProperty("App::PropertyFloat", "BeamRadius", "Optical Source", "Beam/source radius [mm]")
        obj.BeamRadius = 1.0

        obj.addProperty("App::PropertyFloat", "DivergenceAngle", "Optical Source", "Full divergence angle [deg]")
        obj.DivergenceAngle = 0.0

        obj.addProperty("App::PropertyInteger", "RayCount", "Optical Source", "Rays emitted by this source")
        obj.RayCount = 5000


class BCOpticalDetector(BaseBoundaryCondition):
    """Detector or sensor plane assigned to selected faces."""

    Type = "FlowStudio::BCOpticalDetector"

    def __init__(self, obj):
        super().__init__(obj)
        obj.BCLabel = "Optical Detector"

        obj.addProperty("App::PropertyEnumeration", "DetectorType", "Optical Detector", "Detector output")
        obj.DetectorType = ["Irradiance", "Spot Diagram", "Power Meter", "Phase / OPD", "Spectrum"]
        obj.DetectorType = "Irradiance"

        obj.addProperty("App::PropertyInteger", "PixelsX", "Optical Detector", "Detector horizontal pixels")
        obj.PixelsX = 512

        obj.addProperty("App::PropertyInteger", "PixelsY", "Optical Detector", "Detector vertical pixels")
        obj.PixelsY = 512

        obj.addProperty("App::PropertyFloat", "Width", "Optical Detector", "Detector width [mm]")
        obj.Width = 10.0

        obj.addProperty("App::PropertyFloat", "Height", "Optical Detector", "Detector height [mm]")
        obj.Height = 10.0


class BCOpticalBoundary(BaseBoundaryCondition):
    """Optical boundary/coating assigned to selected surfaces."""

    Type = "FlowStudio::BCOpticalBoundary"

    def __init__(self, obj):
        super().__init__(obj)
        obj.BCLabel = "Optical Boundary"

        obj.addProperty("App::PropertyEnumeration", "BoundaryType", "Optical Boundary", "Optical surface behavior")
        obj.BoundaryType = ["Refractive", "Reflective", "Absorbing", "Scattering", "Periodic", "PML"]
        obj.BoundaryType = "Refractive"

        obj.addProperty("App::PropertyFloat", "Reflectivity", "Optical Boundary", "Surface reflectivity fraction")
        obj.Reflectivity = 0.04

        obj.addProperty("App::PropertyFloat", "Transmission", "Optical Boundary", "Surface transmission fraction")
        obj.Transmission = 0.96

        obj.addProperty("App::PropertyFloat", "Scatter", "Optical Boundary", "Diffuse scatter fraction")
        obj.Scatter = 0.0

