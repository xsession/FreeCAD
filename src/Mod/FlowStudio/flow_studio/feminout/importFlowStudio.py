# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""FlowStudio import/export for .foam, .vtk, .stl result files.

FreeCAD requires ``open(filename)`` and optionally ``insert(filename, docname)``
functions for registered import types.
"""

import builtins
import json
import os
import FreeCAD


def _coerce_scoring_summaries(payload):
    scoring_summaries = list(payload.get("scoring_summaries", []) or [])
    if scoring_summaries:
        return scoring_summaries

    fallback = []
    for index, artifact in enumerate(payload.get("artifact_summaries", []) or [], start=1):
        if not isinstance(artifact, dict):
            continue
        fields = list(artifact.get("fields", []) or [])
        path = artifact.get("path", "")
        fallback.append({
            "name": f"ImportedScoring{index}",
            "label": os.path.basename(path) or f"Imported Scoring {index}",
            "score_quantity": fields[0] if fields else "ImportedField",
            "scoring_type": "Imported",
            "bins": [0, 0, 0],
            "reference_targets": [],
            "artifact_files": [path] if path else [],
            "available_fields": fields,
        })
    return fallback


def _coerce_detector_summaries(payload):
    detector_summaries = list(payload.get("detector_summaries", []) or [])
    if detector_summaries:
        return detector_summaries

    monitors = list(payload.get("monitors", []) or [])
    if not monitors:
        return []
    artifact_files = [
        item.get("path", "")
        for item in payload.get("artifact_summaries", []) or []
        if isinstance(item, dict) and item.get("path")
    ]
    return [{
        "name": "ImportedDetector1",
        "label": "Imported Detector Monitors",
        "collection_name": "detectorHits",
        "detector_type": "Hits Collection",
        "threshold_kev": 0.0,
        "reference_targets": [],
        "monitor_names": monitors,
        "artifact_files": artifact_files,
    }]


def _sync_geant4_children(doc, result_obj, analysis, payload):
    try:
        from flow_studio.ObjectsFlowStudio import makeGeant4DetectorResult, makeGeant4ScoringResult
    except Exception:
        result_obj.ScoringResults = []
        result_obj.DetectorResults = []
        return

    def _remove_extra(existing_objects, keep_count):
        remover = getattr(doc, "removeObject", None)
        for extra in existing_objects[keep_count:]:
            if callable(remover):
                try:
                    remover(extra.Name)
                except Exception:
                    pass

    scoring_summaries = _coerce_scoring_summaries(payload)
    detector_summaries = _coerce_detector_summaries(payload)
    existing_scoring = list(getattr(result_obj, "ScoringResults", []) or [])
    existing_detector = list(getattr(result_obj, "DetectorResults", []) or [])

    scoring_objects = []
    for index, summary in enumerate(scoring_summaries, start=1):
        if index <= len(existing_scoring):
            obj = existing_scoring[index - 1]
        else:
            obj = makeGeant4ScoringResult(doc, name=f"{getattr(result_obj, 'Name', 'Geant4Result')}_Scoring{index}")
        obj.Analysis = analysis
        obj.ParentResult = result_obj
        obj.Label = summary.get("label", getattr(obj, "Label", obj.Name))
        obj.ScoreQuantity = str(summary.get("score_quantity", "DoseDeposit"))
        obj.ScoringType = str(summary.get("scoring_type", "Mesh"))
        bins = list(summary.get("bins", [0, 0, 0]))
        obj.BinShape = " x ".join(str(value) for value in bins)
        obj.ReferenceTargets = list(summary.get("reference_targets", []) or [])
        obj.ArtifactFiles = list(summary.get("artifact_files", []) or [])
        obj.AvailableFields = list(summary.get("available_fields", []) or [])
        obj.ActiveField = obj.AvailableFields[0] if obj.AvailableFields else ""
        obj.ImportNotes = (
            f"Imported Geant4 scoring result '{obj.ScoreQuantity}' from {len(obj.ArtifactFiles)} artifacts."
        )
        scoring_objects.append(obj)

    detector_objects = []
    for index, summary in enumerate(detector_summaries, start=1):
        if index <= len(existing_detector):
            obj = existing_detector[index - 1]
        else:
            obj = makeGeant4DetectorResult(doc, name=f"{getattr(result_obj, 'Name', 'Geant4Result')}_Detector{index}")
        obj.Analysis = analysis
        obj.ParentResult = result_obj
        obj.Label = summary.get("label", getattr(obj, "Label", obj.Name))
        obj.CollectionName = str(summary.get("collection_name", "detectorHits"))
        obj.DetectorType = str(summary.get("detector_type", "Hits Collection"))
        obj.ThresholdKeV = float(summary.get("threshold_kev", 0.0) or 0.0)
        obj.ReferenceTargets = list(summary.get("reference_targets", []) or [])
        obj.MonitorNames = list(summary.get("monitor_names", []) or [])
        obj.ArtifactFiles = list(summary.get("artifact_files", []) or [])
        obj.ImportNotes = (
            f"Imported Geant4 detector result '{obj.CollectionName}' with {len(obj.MonitorNames)} monitors."
        )
        detector_objects.append(obj)

    _remove_extra(existing_scoring, len(scoring_objects))
    _remove_extra(existing_detector, len(detector_objects))
    result_obj.ScoringResults = scoring_objects
    result_obj.DetectorResults = detector_objects


def populate_geant4_result_object(result_obj, payload, doc=None, analysis=None):
    """Populate a native Geant4 result object and its typed child results."""
    if doc is None:
        doc = getattr(result_obj, "Document", None) or FreeCAD.ActiveDocument

    artifact_summaries = payload.get("artifact_summaries", []) if isinstance(payload, dict) else []
    artifact_files = [
        item.get("path", "")
        for item in artifact_summaries
        if isinstance(item, dict) and item.get("path")
    ]
    available_fields = list(payload.get("available_fields", payload.get("fields", [])))
    primary_quantity = str(payload.get("primary_quantity", available_fields[0] if available_fields else ""))
    result_obj.Analysis = analysis
    result_obj.ResultFile = str(payload.get("result_file", artifact_files[0] if artifact_files else ""))
    result_obj.SummaryFile = str(payload.get("summary_file", getattr(result_obj, "SummaryFile", "")))
    result_obj.ResultFormat = str(payload.get("result_format", "Geant4-JSON"))
    result_obj.AvailableFields = available_fields
    result_obj.ActiveField = primary_quantity or (available_fields[0] if available_fields else "")
    result_obj.MonitorNames = list(payload.get("monitors", []))
    result_obj.ArtifactFiles = artifact_files
    result_obj.PrimaryQuantity = primary_quantity
    result_obj.ImportNotes = (
        f"Imported Geant4 summary with {len(artifact_files)} artifacts, "
        f"{len(available_fields)} fields, and {len(result_obj.MonitorNames)} monitors."
    )

    if doc is not None:
        _sync_geant4_children(doc, result_obj, analysis, payload)
        recompute = getattr(doc, "recompute", None)
        if callable(recompute):
            recompute()
    return result_obj


# ---- FreeCAD import entry points ----

def open(filename):
    """Entry point called by FreeCAD when opening a .foam / .vtk file."""
    ext = os.path.splitext(filename)[1].lower()
    base = os.path.basename(filename)
    if ext == ".foam":
        return open_foam_case(filename)
    elif ext in (".vtk", ".vtu", ".vtp"):
        return open_vtk_file(filename)
    elif ext == ".json" and base.endswith("geant4_result_summary.json"):
        return open_geant4_summary(filename)
    else:
        FreeCAD.Console.PrintWarning(
            f"FlowStudio: Unsupported import format '{ext}'\n"
        )


def insert(filename, docname=None):
    """Insert results into an existing document."""
    if docname:
        doc = FreeCAD.getDocument(docname)
    else:
        doc = FreeCAD.ActiveDocument
    return open(filename)


def open_foam_case(filename):
    """Open an OpenFOAM .foam file – creates a PostPipeline."""
    doc = FreeCAD.ActiveDocument
    if doc is None:
        doc = FreeCAD.newDocument("CFDResult")

    from flow_studio.ObjectsFlowStudio import makePostPipeline
    obj = makePostPipeline(doc)
    obj.ResultFile = filename
    obj.ResultFormat = "OpenFOAM"
    doc.recompute()
    return obj


def open_vtk_file(filename):
    """Import a VTK result file."""
    doc = FreeCAD.ActiveDocument
    if doc is None:
        doc = FreeCAD.newDocument("CFDResult")

    from flow_studio.ObjectsFlowStudio import makePostPipeline
    obj = makePostPipeline(doc)
    obj.ResultFile = filename
    obj.ResultFormat = "VTK"
    doc.recompute()
    return obj


def open_geant4_summary(filename, doc=None, analysis=None):
    """Import a FlowStudio Geant4 result summary JSON."""
    if doc is None:
        doc = FreeCAD.ActiveDocument
    if doc is None:
        doc = FreeCAD.newDocument("Geant4Result")

    with builtins.open(filename, "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    from flow_studio.ObjectsFlowStudio import makeGeant4Result

    obj = makeGeant4Result(doc)
    if analysis is not None:
        add_object = getattr(analysis, "addObject", None)
        if callable(add_object):
            add_object(obj)
    payload["summary_file"] = filename
    return populate_geant4_result_object(obj, payload, doc=doc, analysis=analysis)


def export_stl(objects, filename):
    """Export FreeCAD shapes to binary STL for FluidX3D."""
    import Mesh
    meshes = []
    for obj in objects:
        if hasattr(obj, "Shape"):
            meshes.append(Mesh.Mesh(obj.Shape.tessellate(0.1)))
    if meshes:
        combined = meshes[0]
        for m in meshes[1:]:
            combined.addMesh(m)
        combined.write(filename)
        FreeCAD.Console.PrintMessage(
            f"FlowStudio: Exported STL -> {filename}\n"
        )
