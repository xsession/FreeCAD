# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Geant4 source, detector, and scoring objects."""

from flow_studio.objects.base_bc import BaseBoundaryCondition


class BCGeant4Source(BaseBoundaryCondition):
    """Particle source assigned to selected geometry or reference surfaces."""

    Type = "FlowStudio::BCGeant4Source"

    def __init__(self, obj):
        super().__init__(obj)
        obj.BCLabel = "Geant4 Source"

        obj.addProperty("App::PropertyEnumeration", "SourceType", "Geant4 Source", "Primary source model")
        obj.SourceType = ["Beam", "Point Source", "Surface Source", "Volume Source"]
        obj.SourceType = "Beam"

        obj.addProperty("App::PropertyEnumeration", "ParticleType", "Geant4 Source", "Primary particle species")
        obj.ParticleType = ["gamma", "e-", "e+", "proton", "neutron", "mu-", "alpha", "ion"]
        obj.ParticleType = "gamma"

        obj.addProperty("App::PropertyFloat", "EnergyMeV", "Geant4 Source", "Primary energy [MeV]")
        obj.EnergyMeV = 1.0

        obj.addProperty("App::PropertyFloat", "BeamRadius", "Geant4 Source", "Beam or source radius [mm]")
        obj.BeamRadius = 1.0

        obj.addProperty("App::PropertyFloat", "DirectionX", "Geant4 Source", "Primary direction X component")
        obj.DirectionX = 0.0

        obj.addProperty("App::PropertyFloat", "DirectionY", "Geant4 Source", "Primary direction Y component")
        obj.DirectionY = 0.0

        obj.addProperty("App::PropertyFloat", "DirectionZ", "Geant4 Source", "Primary direction Z component")
        obj.DirectionZ = 1.0

        obj.addProperty("App::PropertyInteger", "Events", "Geant4 Source", "Requested events contributed by this source")
        obj.Events = 1000


class BCGeant4Detector(BaseBoundaryCondition):
    """Sensitive detector or readout region for Geant4 studies."""

    Type = "FlowStudio::BCGeant4Detector"

    def __init__(self, obj):
        super().__init__(obj)
        obj.BCLabel = "Geant4 Detector"

        obj.addProperty("App::PropertyEnumeration", "DetectorType", "Geant4 Detector", "Detector or readout role")
        obj.DetectorType = ["Sensitive Detector", "Calorimeter", "Tracker", "Dose Plane", "Hits Collection"]
        obj.DetectorType = "Sensitive Detector"

        obj.addProperty("App::PropertyString", "CollectionName", "Geant4 Detector", "Logical collection name written by the detector")
        obj.CollectionName = "detectorHits"

        obj.addProperty("App::PropertyFloat", "ThresholdKeV", "Geant4 Detector", "Energy threshold [keV]")
        obj.ThresholdKeV = 0.0

        obj.addProperty("App::PropertyInteger", "PixelsX", "Geant4 Detector", "Detector bins or pixels in X")
        obj.PixelsX = 64

        obj.addProperty("App::PropertyInteger", "PixelsY", "Geant4 Detector", "Detector bins or pixels in Y")
        obj.PixelsY = 64


class BCGeant4Scoring(BaseBoundaryCondition):
    """Scoring mesh or derived quantity request for Geant4 studies."""

    Type = "FlowStudio::BCGeant4Scoring"

    def __init__(self, obj):
        super().__init__(obj)
        obj.BCLabel = "Geant4 Scoring"

        obj.addProperty("App::PropertyEnumeration", "ScoreQuantity", "Geant4 Scoring", "Quantity to accumulate")
        obj.ScoreQuantity = ["DoseDeposit", "EnergyDeposit", "TrackLength", "Flux", "CellHits"]
        obj.ScoreQuantity = "DoseDeposit"

        obj.addProperty("App::PropertyEnumeration", "ScoringType", "Geant4 Scoring", "Scoring geometry representation")
        obj.ScoringType = ["Cell", "Surface", "Mesh"]
        obj.ScoringType = "Mesh"

        obj.addProperty("App::PropertyInteger", "BinsX", "Geant4 Scoring", "Number of scoring bins in X")
        obj.BinsX = 16

        obj.addProperty("App::PropertyInteger", "BinsY", "Geant4 Scoring", "Number of scoring bins in Y")
        obj.BinsY = 16

        obj.addProperty("App::PropertyInteger", "BinsZ", "Geant4 Scoring", "Number of scoring bins in Z")
        obj.BinsZ = 16

        obj.addProperty("App::PropertyBool", "NormalizePerEvent", "Geant4 Scoring", "Normalize scoring by the number of events")
        obj.NormalizePerEvent = True