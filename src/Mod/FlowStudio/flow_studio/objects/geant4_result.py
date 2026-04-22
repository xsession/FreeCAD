# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Native FlowStudio result container for Geant4 imports."""

from flow_studio.objects.base_object import BaseFlowObject


class Geant4Result(BaseFlowObject):
    """Imported Geant4 result metadata and artifact references."""

    Type = "FlowStudio::Geant4Result"

    def __init__(self, obj):
        super().__init__(obj)

        obj.addProperty(
            "App::PropertyLink", "Analysis", "Result",
            "Link to the owning Geant4 analysis"
        )
        obj.addProperty(
            "App::PropertyPath", "ResultFile", "Result",
            "Primary imported Geant4 result artifact"
        )
        obj.addProperty(
            "App::PropertyPath", "SummaryFile", "Result",
            "Structured FlowStudio summary for imported Geant4 artifacts"
        )
        obj.addProperty(
            "App::PropertyEnumeration", "ResultFormat", "Result",
            "Detected Geant4 result format"
        )
        obj.ResultFormat = ["Geant4-JSON", "Geant4-CSV", "Geant4-TXT"]
        obj.ResultFormat = "Geant4-JSON"
        obj.addProperty(
            "App::PropertyStringList", "AvailableFields", "Result",
            "Parsed Geant4 result fields available for inspection"
        )
        obj.addProperty(
            "App::PropertyString", "ActiveField", "Result",
            "Currently selected Geant4 field"
        )
        obj.ActiveField = "dose"
        obj.addProperty(
            "App::PropertyStringList", "MonitorNames", "Result",
            "Monitors inferred from imported Geant4 artifacts"
        )
        obj.addProperty(
            "App::PropertyStringList", "ArtifactFiles", "Result",
            "All discovered Geant4 result artifacts"
        )
        obj.addProperty(
            "App::PropertyLinkList", "ScoringResults", "Result",
            "Typed child scoring results derived from the Geant4 import"
        )
        obj.addProperty(
            "App::PropertyLinkList", "DetectorResults", "Result",
            "Typed child detector results derived from the Geant4 import"
        )
        obj.addProperty(
            "App::PropertyString", "PrimaryQuantity", "Result",
            "Primary scoring quantity associated with this import"
        )
        obj.PrimaryQuantity = "DoseDeposit"
        obj.addProperty(
            "App::PropertyString", "ImportNotes", "Result",
            "Human-readable import summary"
        )
        obj.ImportNotes = "Geant4 result import pending."