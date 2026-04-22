# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Tests for Geant4 macro generation without requiring FreeCAD runtime."""

import json
import os
import sys
import tempfile
import types
import unittest
from types import SimpleNamespace
from unittest.mock import patch


class _Console:
    def PrintMessage(self, *_args, **_kwargs):
        pass

    def PrintWarning(self, *_args, **_kwargs):
        pass

    def PrintError(self, *_args, **_kwargs):
        pass


if "FreeCAD" not in sys.modules:
    sys.modules["FreeCAD"] = types.SimpleNamespace(
        Console=_Console(),
        ActiveDocument=types.SimpleNamespace(Name="UnitTestDoc", TransientDir=tempfile.gettempdir()),
    )

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from flow_studio.solvers.geant4_runner import Geant4Runner


class TestGeant4Runner(unittest.TestCase):
    def test_write_case_uses_authored_sources_and_scoring(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source_target = SimpleNamespace(Name="BeamFace")
            score_target = SimpleNamespace(Name="DoseVolume")
            solver = SimpleNamespace(
                FlowType="FlowStudio::Solver",
                Geant4Executable="",
                Geant4PhysicsList="FTFP_BERT",
                Geant4EventCount=500,
                Geant4Threads=2,
                Geant4MacroName="run.mac",
                Geant4EnableVisualization=False,
            )
            source = SimpleNamespace(
                FlowType="FlowStudio::BCGeant4Source",
                Name="SourceA",
                Label="Primary Beam",
                SourceType="Beam",
                ParticleType="proton",
                EnergyMeV=2.5,
                BeamRadius=4.0,
                DirectionX=0.0,
                DirectionY=1.0,
                DirectionZ=0.0,
                Events=125,
                References=[(source_target, ("Face1",))],
            )
            scoring = SimpleNamespace(
                FlowType="FlowStudio::BCGeant4Scoring",
                Name="DoseScore",
                Label="Dose Grid",
                ScoreQuantity="DoseDeposit",
                ScoringType="Mesh",
                BinsX=8,
                BinsY=6,
                BinsZ=4,
                NormalizePerEvent=True,
                References=[(score_target, ("Solid1",))],
            )
            detector = SimpleNamespace(
                FlowType="FlowStudio::BCGeant4Detector",
                Name="DetectorA",
                Label="Readout Plane",
                DetectorType="Dose Plane",
                CollectionName="dosePlaneHits",
                ThresholdKeV=12.0,
                References=[(source_target, ("Face2",))],
            )
            analysis = SimpleNamespace(
                Name="Geant4Analysis",
                CaseDir=temp_dir,
                PhysicsDomain="Optical",
                Group=[solver, source, detector, scoring],
            )

            runner = Geant4Runner(analysis, solver)
            runner.write_case()

            macro_path = os.path.join(temp_dir, "run.mac")
            manifest_path = os.path.join(temp_dir, "geant4_case.json")
            with open(macro_path, "r", encoding="utf-8") as handle:
                macro = handle.read()
            with open(manifest_path, "r", encoding="utf-8") as handle:
                manifest = json.load(handle)

            self.assertIn("/gps/particle proton", macro)
            self.assertIn("/gps/ene/mono 2.5 MeV", macro)
            self.assertIn("/run/beamOn 125", macro)
            self.assertIn("/score/create/boxMesh flowstudioScore1", macro)
            self.assertIn("dosePlaneHits", macro)
            self.assertEqual(manifest["sources"][0]["particle_type"], "proton")
            self.assertEqual(manifest["scoring"][0]["bins"], [8, 6, 4])

    def test_read_results_prefers_json_and_updates_post_pipeline(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            solver = SimpleNamespace(
                FlowType="FlowStudio::Solver",
                Geant4Executable="",
                Geant4PhysicsList="FTFP_BERT",
                Geant4EventCount=500,
                Geant4Threads=2,
                Geant4MacroName="run.mac",
                Geant4EnableVisualization=False,
            )
            scoring = SimpleNamespace(
                FlowType="FlowStudio::BCGeant4Scoring",
                Name="DoseScore",
                Label="Dose Grid",
                ScoreQuantity="DoseDeposit",
                ScoringType="Mesh",
                BinsX=8,
                BinsY=6,
                BinsZ=4,
                NormalizePerEvent=True,
                References=[],
            )
            detector = SimpleNamespace(
                FlowType="FlowStudio::BCGeant4Detector",
                Name="DetectorA",
                Label="Readout Plane",
                DetectorType="Dose Plane",
                CollectionName="dosePlaneHits",
                ThresholdKeV=12.0,
                References=[],
            )
            analysis = SimpleNamespace(
                Name="Geant4Analysis",
                CaseDir=temp_dir,
                PhysicsDomain="Optical",
                Group=[solver, detector, scoring],
            )
            pipeline = SimpleNamespace(
                FlowType="FlowStudio::PostPipeline",
                Name="ExistingPost",
                Analysis=None,
                ResultFile="",
                ResultFormat="OpenFOAM",
                AvailableFields=[],
                ActiveField="",
            )
            geant4_result = SimpleNamespace(
                FlowType="FlowStudio::Geant4Result",
                Name="ExistingGeant4Result",
                Analysis=None,
                ResultFile="",
                ResultFormat="Geant4-JSON",
                AvailableFields=[],
                ActiveField="",
                MonitorNames=[],
                ArtifactFiles=[],
                ScoringResults=[],
                DetectorResults=[],
                SummaryFile="",
                PrimaryQuantity="",
                ImportNotes="",
            )
            analysis.Group.append(pipeline)
            analysis.Group.append(geant4_result)

            created_scoring = []
            created_detector = []

            def _make_scoring_result(_doc, name="Geant4ScoringResult"):
                obj = SimpleNamespace(
                    FlowType="FlowStudio::Geant4ScoringResult",
                    Name=name,
                    Label=name,
                    Analysis=None,
                    ParentResult=None,
                    ScoreQuantity="",
                    ScoringType="",
                    BinShape="",
                    ReferenceTargets=[],
                    ArtifactFiles=[],
                    AvailableFields=[],
                    ActiveField="",
                    ImportNotes="",
                )
                created_scoring.append(obj)
                return obj

            def _make_detector_result(_doc, name="Geant4DetectorResult"):
                obj = SimpleNamespace(
                    FlowType="FlowStudio::Geant4DetectorResult",
                    Name=name,
                    Label=name,
                    Analysis=None,
                    ParentResult=None,
                    CollectionName="",
                    DetectorType="",
                    ThresholdKeV=0.0,
                    ReferenceTargets=[],
                    MonitorNames=[],
                    ArtifactFiles=[],
                    ImportNotes="",
                )
                created_detector.append(obj)
                return obj

            runner = Geant4Runner(analysis, solver)
            runner.write_case()
            csv_path = os.path.join(temp_dir, "dose.csv")
            json_path = os.path.join(temp_dir, "summary.json")
            with open(csv_path, "w", encoding="utf-8") as handle:
                handle.write("DoseDeposit,TrackLength\n1.2,3.4\n")
            with open(json_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "summary": {"dose": 1.2, "event_count": 50},
                        "detectors": [{"cellHits": 10, "trackLength": 3.4}],
                    },
                    handle,
                )

            fake_objects = types.SimpleNamespace(
                makeGeant4ScoringResult=_make_scoring_result,
                makeGeant4DetectorResult=_make_detector_result,
            )
            with patch.dict(sys.modules, {"flow_studio.ObjectsFlowStudio": fake_objects}):
                result = runner.read_results()

            self.assertEqual(result["result_file"], json_path)
            self.assertEqual(result["result_format"], "Geant4-JSON")
            self.assertIn("DoseDeposit", result["available_fields"])
            self.assertIn("dose", result["available_fields"])
            self.assertIn("events", result["available_fields"])
            self.assertIn("hits", result["available_fields"])
            self.assertIn("track_length", result["available_fields"])
            self.assertIn("events", result["monitors"])
            self.assertIn("hits", result["monitors"])
            self.assertEqual(len(result["artifact_summaries"]), 2)
            self.assertEqual(result["artifact_summaries"][0]["format"], "Geant4-CSV")
            self.assertIn("dose", result["artifact_summaries"][0]["fields"])
            self.assertEqual(result["artifact_summaries"][1]["format"], "Geant4-JSON")
            self.assertIn("hits", result["artifact_summaries"][1]["fields"])
            self.assertTrue(result["summary_file"].endswith("flowstudio_geant4_result_summary.json"))
            self.assertEqual(pipeline.ResultFile, json_path)
            self.assertEqual(pipeline.ResultFormat, "Geant4-JSON")
            self.assertEqual(pipeline.ActiveField, "DoseDeposit")
            self.assertEqual(geant4_result.ResultFile, json_path)
            self.assertEqual(geant4_result.ResultFormat, "Geant4-JSON")
            self.assertEqual(geant4_result.ActiveField, "DoseDeposit")
            self.assertIn("events", geant4_result.MonitorNames)
            self.assertEqual(geant4_result.SummaryFile, result["summary_file"])
            self.assertEqual(len(geant4_result.ScoringResults), 1)
            self.assertEqual(geant4_result.ScoringResults[0].ScoreQuantity, "DoseDeposit")
            self.assertEqual(len(geant4_result.DetectorResults), 1)
            self.assertEqual(geant4_result.DetectorResults[0].CollectionName, "dosePlaneHits")
            self.assertEqual(result["geant4_result"], "ExistingGeant4Result")


class TestGeant4SummaryImport(unittest.TestCase):
    def test_open_geant4_summary_populates_native_result_object(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            summary_path = os.path.join(temp_dir, "flowstudio_geant4_result_summary.json")
            payload = {
                "result_file": os.path.join(temp_dir, "summary.json"),
                "result_format": "Geant4-JSON",
                "available_fields": ["DoseDeposit", "dose", "events"],
                "monitors": ["events"],
                "artifact_summaries": [
                    {"path": os.path.join(temp_dir, "summary.json"), "format": "Geant4-JSON", "fields": ["dose", "events"]},
                    {"path": os.path.join(temp_dir, "dose.csv"), "format": "Geant4-CSV", "fields": ["dose"]},
                ],
            }
            with open(summary_path, "w", encoding="utf-8") as handle:
                json.dump(payload, handle)

            created = []

            class _FakeDoc:
                def recompute(self):
                    pass

            def _make_geant4_result(doc):
                obj = SimpleNamespace(
                    FlowType="FlowStudio::Geant4Result",
                    Name="ImportedGeant4Result",
                    Analysis=None,
                    ResultFile="",
                    SummaryFile="",
                    ResultFormat="Geant4-JSON",
                    AvailableFields=[],
                    ActiveField="",
                    MonitorNames=[],
                    ArtifactFiles=[],
                    ScoringResults=[],
                    DetectorResults=[],
                    PrimaryQuantity="",
                    ImportNotes="",
                )
                created.append(obj)
                return obj

            created_scoring = []
            created_detector = []

            def _make_scoring_result(_doc, name="Geant4ScoringResult"):
                obj = SimpleNamespace(
                    FlowType="FlowStudio::Geant4ScoringResult",
                    Name=name,
                    Label=name,
                    Analysis=None,
                    ParentResult=None,
                    ScoreQuantity="",
                    ScoringType="",
                    BinShape="",
                    ReferenceTargets=[],
                    ArtifactFiles=[],
                    AvailableFields=[],
                    ActiveField="",
                    ImportNotes="",
                )
                created_scoring.append(obj)
                return obj

            def _make_detector_result(_doc, name="Geant4DetectorResult"):
                obj = SimpleNamespace(
                    FlowType="FlowStudio::Geant4DetectorResult",
                    Name=name,
                    Label=name,
                    Analysis=None,
                    ParentResult=None,
                    CollectionName="",
                    DetectorType="",
                    ThresholdKeV=0.0,
                    ReferenceTargets=[],
                    MonitorNames=[],
                    ArtifactFiles=[],
                    ImportNotes="",
                )
                created_detector.append(obj)
                return obj

            with patch.dict(sys.modules, {"FreeCAD": types.SimpleNamespace(ActiveDocument=_FakeDoc(), newDocument=lambda _name: _FakeDoc(), Console=_Console())}):
                fake_objects = types.SimpleNamespace(
                    makeGeant4Result=_make_geant4_result,
                    makeGeant4ScoringResult=_make_scoring_result,
                    makeGeant4DetectorResult=_make_detector_result,
                )
                with patch.dict(sys.modules, {"flow_studio.ObjectsFlowStudio": fake_objects}):
                    from flow_studio.feminout.importFlowStudio import open_geant4_summary

                    obj = open_geant4_summary(summary_path, doc=_FakeDoc(), analysis=None)

            self.assertIs(obj, created[0])
            self.assertEqual(obj.ResultFile, payload["result_file"])
            self.assertEqual(obj.SummaryFile, summary_path)
            self.assertEqual(obj.AvailableFields, payload["available_fields"])
            self.assertEqual(obj.ActiveField, "DoseDeposit")
            self.assertEqual(obj.MonitorNames, ["events"])
            self.assertEqual(len(obj.ArtifactFiles), 2)
            self.assertEqual(len(obj.ScoringResults), 2)
            self.assertEqual(len(obj.DetectorResults), 1)


class TestPostPipelineFormatDefinition(unittest.TestCase):
    def test_post_pipeline_exposes_geant4_result_formats(self):
        enum_values = []

        class _FakeObj:
            PropertiesList = []

            def addProperty(self, _prop_type, name, _group, _doc):
                if name not in self.PropertiesList:
                    self.PropertiesList.append(name)
                setattr(self, name, None)
                return self

            def setPropertyStatus(self, *_args, **_kwargs):
                pass

            def __setattr__(self, name, value):
                if name == "ResultFormat" and isinstance(value, list):
                    enum_values[:] = value
                object.__setattr__(self, name, value)

        with patch.dict(sys.modules, {"FreeCAD": types.SimpleNamespace()}):
            from flow_studio.objects.post_pipeline import PostPipeline

            PostPipeline(_FakeObj())

        self.assertIn("Geant4-JSON", enum_values)
        self.assertIn("Geant4-CSV", enum_values)
        self.assertIn("Geant4-TXT", enum_values)


if __name__ == "__main__":
    unittest.main()