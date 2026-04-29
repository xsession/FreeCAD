# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Application services for FloEFD-style FlowStudio feature task panels."""

from __future__ import annotations


def _vector_tuple(vector):
    return (float(vector.x), float(vector.y), float(vector.z))


class FlowStudioVolumeSourceService:
    def read_settings(self, obj):
        return {
            "References": tuple(getattr(obj, "References", []) or []),
            "SourceType": getattr(obj, "SourceType", "Heat Generation"),
            "HeatPowerDensity": float(getattr(obj, "HeatPowerDensity", 0.0)),
            "MassSource": float(getattr(obj, "MassSource", 0.0)),
            "CreateAssociatedGoals": bool(getattr(obj, "CreateAssociatedGoals", False)),
        }

    def persist_settings(self, obj, settings):
        obj.SourceType = settings["SourceType"]
        obj.HeatPowerDensity = settings["HeatPowerDensity"]
        obj.MassSource = settings["MassSource"]
        obj.CreateAssociatedGoals = settings["CreateAssociatedGoals"]


class FlowStudioFanService:
    def read_settings(self, obj):
        return {
            "References": tuple(getattr(obj, "References", []) or []),
            "FanType": getattr(obj, "FanType", "Internal Fan"),
            "FanCurvePreset": getattr(obj, "FanCurvePreset", "User Defined"),
            "ReferencePressure": float(getattr(obj, "ReferencePressure", 0.0)),
            "CreateAssociatedGoals": bool(getattr(obj, "CreateAssociatedGoals", False)),
        }

    def persist_settings(self, obj, settings):
        obj.FanType = settings["FanType"]
        obj.FanCurvePreset = settings["FanCurvePreset"]
        obj.ReferencePressure = settings["ReferencePressure"]
        obj.CreateAssociatedGoals = settings["CreateAssociatedGoals"]


class FlowStudioResultPlotService:
    def read_settings(self, obj):
        return {
            "References": tuple(getattr(obj, "References", []) or []),
            "PlotKind": getattr(obj, "PlotKind", "Surface Plot"),
            "Field": getattr(obj, "Field", "Pressure"),
            "ContourCount": int(getattr(obj, "ContourCount", 10)),
            "Contours": bool(getattr(obj, "Contours", False)),
            "Isolines": bool(getattr(obj, "Isolines", False)),
            "Vectors": bool(getattr(obj, "Vectors", False)),
            "Streamlines": bool(getattr(obj, "Streamlines", False)),
            "CutPlane": getattr(obj, "CutPlane", "XY Plane"),
            "PlaneOffset": float(getattr(obj, "PlaneOffset", 0.0)),
            "UseCADGeometry": bool(getattr(obj, "UseCADGeometry", False)),
            "Interpolate": bool(getattr(obj, "Interpolate", False)),
            "ExportExcel": bool(getattr(obj, "ExportExcel", False)),
        }

    def persist_settings(self, obj, settings):
        obj.PlotKind = settings["PlotKind"]
        obj.Field = settings["Field"]
        obj.ContourCount = settings["ContourCount"]
        obj.Contours = settings["Contours"]
        obj.Isolines = settings["Isolines"]
        obj.Vectors = settings["Vectors"]
        obj.Streamlines = settings["Streamlines"]
        obj.CutPlane = settings["CutPlane"]
        obj.PlaneOffset = settings["PlaneOffset"]
        obj.UseCADGeometry = settings["UseCADGeometry"]
        obj.Interpolate = settings["Interpolate"]
        obj.ExportExcel = settings["ExportExcel"]


class FlowStudioParticleStudyService:
    def read_settings(self, obj):
        return {
            "Injections": tuple(getattr(obj, "Injections", []) or []),
            "Accretion": bool(getattr(obj, "Accretion", False)),
            "Erosion": bool(getattr(obj, "Erosion", False)),
            "Gravity": bool(getattr(obj, "Gravity", False)),
            "GravityVector": _vector_tuple(getattr(obj, "GravityVector")),
            "ParticleShape": getattr(obj, "ParticleShape", "Spheres"),
            "ParticleDiameter": float(getattr(obj, "ParticleDiameter", 0.0)),
            "ColorByField": getattr(obj, "ColorByField", "Pressure"),
            "TrackLength": float(getattr(obj, "TrackLength", 0.0)),
            "TrackTime": float(getattr(obj, "TrackTime", 0.0)),
            "MaxParticles": int(getattr(obj, "MaxParticles", 1)),
        }

    def persist_settings(self, obj, settings, vector_factory):
        obj.Accretion = settings["Accretion"]
        obj.Erosion = settings["Erosion"]
        obj.Gravity = settings["Gravity"]
        obj.GravityVector = vector_factory(*settings["GravityVector"])
        obj.ParticleShape = settings["ParticleShape"]
        obj.ParticleDiameter = settings["ParticleDiameter"]
        obj.ColorByField = settings["ColorByField"]
        obj.TrackLength = settings["TrackLength"]
        obj.TrackTime = settings["TrackTime"]
        obj.MaxParticles = settings["MaxParticles"]