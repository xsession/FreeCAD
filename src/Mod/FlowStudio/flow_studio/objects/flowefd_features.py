# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""FloEFD-style setup and result feature objects.

These objects store high-level simulation intent that can later be consumed by
solver adapters, post-processing exporters, and workflow validation.
"""

from flow_studio.objects.base_object import BaseFlowObject


class VolumeSource(BaseFlowObject):
    """Volumetric heat/source term assigned to selected parts or volumes."""

    Type = "FlowStudio::VolumeSource"

    def __init__(self, obj):
        super().__init__(obj)
        self.add_reference_property(obj, "Selection", "Parts or volumes receiving this source")
        obj.addProperty("App::PropertyEnumeration", "SourceType", "Source", "Source type")
        obj.SourceType = ["Heat Generation", "Mass Source", "Momentum Source", "Species Source"]
        obj.SourceType = "Heat Generation"
        obj.addProperty("App::PropertyFloat", "HeatPowerDensity", "Parameters", "Heat generation [W/m^3]")
        obj.HeatPowerDensity = 0.0
        obj.addProperty("App::PropertyFloat", "MassSource", "Parameters", "Mass source [kg/(m^3 s)]")
        obj.MassSource = 0.0
        obj.addProperty("App::PropertyVector", "MomentumSource", "Parameters", "Momentum source vector")
        obj.MomentumSource = (0.0, 0.0, 0.0)
        obj.addProperty("App::PropertyBool", "CreateAssociatedGoals", "Options", "Create matching goals")
        obj.CreateAssociatedGoals = False


class FanFeature(BaseFlowObject):
    """Internal/external fan boundary assigned to selected faces."""

    Type = "FlowStudio::Fan"

    def __init__(self, obj):
        super().__init__(obj)
        self.add_reference_property(obj, "Faces", "Faces where fluid enters or exits the fan")
        obj.addProperty("App::PropertyEnumeration", "FanType", "Fan", "Fan placement/type")
        obj.FanType = ["Internal Fan", "External Inlet Fan", "External Outlet Fan"]
        obj.FanType = "External Inlet Fan"
        obj.addProperty("App::PropertyEnumeration", "FanCurvePreset", "Fan", "Fan curve preset")
        obj.FanCurvePreset = [
            "User Defined",
            "Axial",
            "Radial",
            "Noctua_NF-A6x25_5V_PWM",
            "9A0824H4001",
        ]
        obj.FanCurvePreset = "User Defined"
        obj.addProperty("App::PropertyFloat", "ReferencePressure", "Thermodynamic Parameters", "Reference pressure [Pa]")
        obj.ReferencePressure = 101325.0
        obj.addProperty("App::PropertyBool", "CreateAssociatedGoals", "Options", "Create matching fan goals")
        obj.CreateAssociatedGoals = False


class ResultPlot(BaseFlowObject):
    """Post-processing plot definition."""

    Type = "FlowStudio::ResultPlot"

    def __init__(self, obj):
        super().__init__(obj)
        self.add_reference_property(obj, "Selection", "Selected faces, parts, or seed locations")
        obj.addProperty("App::PropertyEnumeration", "PlotKind", "Plot", "Plot kind")
        obj.PlotKind = ["Surface Plot", "Cut Plot", "XY Plot", "Flow Trajectories", "Point Parameters"]
        obj.PlotKind = "Surface Plot"
        obj.addProperty("App::PropertyString", "Field", "Display", "Result field to visualize")
        obj.Field = "Pressure"
        obj.addProperty("App::PropertyBool", "Contours", "Display", "Show contours")
        obj.Contours = True
        obj.addProperty("App::PropertyBool", "Isolines", "Display", "Show isolines")
        obj.Isolines = False
        obj.addProperty("App::PropertyBool", "Vectors", "Display", "Show vectors")
        obj.Vectors = False
        obj.addProperty("App::PropertyBool", "Streamlines", "Display", "Show streamlines")
        obj.Streamlines = False
        obj.addProperty("App::PropertyInteger", "ContourCount", "Display", "Number of contour levels")
        obj.ContourCount = 10
        obj.addProperty("App::PropertyEnumeration", "CutPlane", "Cut Plot", "Cut plane")
        obj.CutPlane = ["XY Plane", "XZ Plane", "YZ Plane", "Custom"]
        obj.CutPlane = "XY Plane"
        obj.addProperty("App::PropertyFloat", "PlaneOffset", "Cut Plot", "Cut plane offset")
        obj.PlaneOffset = 0.0
        obj.addProperty("App::PropertyBool", "UseCADGeometry", "Options", "Use CAD geometry for projection")
        obj.UseCADGeometry = True
        obj.addProperty("App::PropertyBool", "Interpolate", "Options", "Interpolate result values")
        obj.Interpolate = True
        obj.addProperty("App::PropertyBool", "ExportExcel", "Export", "Export plot data to Excel/CSV")
        obj.ExportExcel = False


class ParticleStudy(BaseFlowObject):
    """Particle tracing study driven by result fields."""

    Type = "FlowStudio::ParticleStudy"

    def __init__(self, obj):
        super().__init__(obj)
        self.add_reference_property(obj, "Injections", "Injection faces, edges, or seed regions")
        obj.addProperty("App::PropertyBool", "Accretion", "Physical Features", "Enable accretion")
        obj.Accretion = False
        obj.addProperty("App::PropertyBool", "Erosion", "Physical Features", "Enable erosion")
        obj.Erosion = False
        obj.addProperty("App::PropertyBool", "Gravity", "Physical Features", "Enable gravity")
        obj.Gravity = True
        obj.addProperty("App::PropertyVector", "GravityVector", "Physical Features", "Gravity vector [m/s^2]")
        obj.GravityVector = (0.0, -9.81, 0.0)
        obj.addProperty("App::PropertyEnumeration", "ParticleShape", "Appearance", "Particle glyph shape")
        obj.ParticleShape = ["Spheres", "Dots", "Arrows"]
        obj.ParticleShape = "Spheres"
        obj.addProperty("App::PropertyFloat", "ParticleDiameter", "Appearance", "Particle diameter [m]")
        obj.ParticleDiameter = 0.004
        obj.addProperty("App::PropertyString", "ColorByField", "Appearance", "Field used for particle color")
        obj.ColorByField = "Pressure"
        obj.addProperty("App::PropertyFloat", "TrackLength", "Constraints", "Maximum tracking length [m]")
        obj.TrackLength = 10.0
        obj.addProperty("App::PropertyFloat", "TrackTime", "Constraints", "Maximum tracking time [s]")
        obj.TrackTime = 3600.0
        obj.addProperty("App::PropertyInteger", "MaxParticles", "Constraints", "Maximum particle count")
        obj.MaxParticles = 50000
