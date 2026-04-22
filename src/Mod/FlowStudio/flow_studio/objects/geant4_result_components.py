# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Typed Geant4 result child objects for scoring and detector outputs."""

from flow_studio.objects.base_object import BaseFlowObject


class Geant4ScoringResult(BaseFlowObject):
    """Imported Geant4 scoring result metadata."""

    Type = "FlowStudio::Geant4ScoringResult"

    def __init__(self, obj):
        super().__init__(obj)

        obj.addProperty("App::PropertyLink", "Analysis", "Result", "Owning FlowStudio analysis")
        obj.addProperty("App::PropertyLink", "ParentResult", "Result", "Owning Geant4 result container")
        obj.addProperty("App::PropertyString", "ScoreQuantity", "Result", "Imported Geant4 score quantity")
        obj.ScoreQuantity = "DoseDeposit"
        obj.addProperty("App::PropertyString", "ScoringType", "Result", "Imported Geant4 scoring representation")
        obj.ScoringType = "Mesh"
        obj.addProperty("App::PropertyString", "BinShape", "Result", "Serialized Geant4 bin dimensions")
        obj.BinShape = "16 x 16 x 16"
        obj.addProperty("App::PropertyStringList", "ReferenceTargets", "Result", "Referenced geometry targets for this scoring request")
        obj.addProperty("App::PropertyStringList", "ArtifactFiles", "Result", "Associated result artifacts for this scoring output")
        obj.addProperty("App::PropertyStringList", "AvailableFields", "Result", "Available imported fields for this scoring output")
        obj.addProperty("App::PropertyString", "ActiveField", "Result", "Selected imported field for inspection")
        obj.ActiveField = "dose"
        obj.addProperty("App::PropertyString", "ImportNotes", "Result", "Human-readable import summary")
        obj.ImportNotes = "Geant4 scoring import pending."


class Geant4DetectorResult(BaseFlowObject):
    """Imported Geant4 detector or hit-collection metadata."""

    Type = "FlowStudio::Geant4DetectorResult"

    def __init__(self, obj):
        super().__init__(obj)

        obj.addProperty("App::PropertyLink", "Analysis", "Result", "Owning FlowStudio analysis")
        obj.addProperty("App::PropertyLink", "ParentResult", "Result", "Owning Geant4 result container")
        obj.addProperty("App::PropertyString", "CollectionName", "Result", "Imported Geant4 detector collection name")
        obj.CollectionName = "detectorHits"
        obj.addProperty("App::PropertyString", "DetectorType", "Result", "Imported Geant4 detector role")
        obj.DetectorType = "Hits Collection"
        obj.addProperty("App::PropertyFloat", "ThresholdKeV", "Result", "Detector threshold carried from the authored Geant4 detector")
        obj.ThresholdKeV = 0.0
        obj.addProperty("App::PropertyStringList", "ReferenceTargets", "Result", "Referenced geometry targets for this detector")
        obj.addProperty("App::PropertyStringList", "MonitorNames", "Result", "Monitors inferred for this detector output")
        obj.addProperty("App::PropertyStringList", "ArtifactFiles", "Result", "Associated result artifacts relevant to this detector")
        obj.addProperty("App::PropertyString", "ImportNotes", "Result", "Human-readable import summary")
        obj.ImportNotes = "Geant4 detector import pending."