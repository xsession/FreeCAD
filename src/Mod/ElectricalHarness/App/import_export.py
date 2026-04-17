"""Import/export bridge for FreeCAD and external integrations.

Handles *.ehproj.json open/insert/export, populates the project_store so that
the GUI panels, commands, and validation immediately reflect loaded data.
"""

from __future__ import annotations

import pathlib
from typing import Iterable

import FreeCAD

from . import project_store
from .document_objects import make_harness_project, make_connector_instance
from .model import ElectricalProjectModel
from .serialization import ProjectSerializer


def open(filename: str):
    """Open an .ehproj.json file as a new FreeCAD document."""
    serializer = ProjectSerializer()
    model = serializer.load_file(filename)
    doc_name = pathlib.Path(filename).stem
    doc = FreeCAD.newDocument(doc_name)

    # Populate project_store so panels and commands see the data
    project_store.set_active_model(model)

    # Create document objects for visual representation
    _populate_doc_objects(doc, model)

    doc.recompute()
    FreeCAD.Console.PrintMessage(
        f"ElectricalHarness: opened {filename} "
        f"({len(model.connectors)} connectors, {len(model.wires)} wires)\n"
    )
    return doc


def insert(filename: str, docname: str):
    """Insert (merge) an .ehproj.json file into an existing document."""
    serializer = ProjectSerializer()
    incoming = serializer.load_file(filename)
    doc = FreeCAD.getDocument(docname)

    # Get or create the active model and merge in incoming entities
    model = project_store.get_active_model(create_if_missing=True)
    for conn in incoming.connectors.values():
        if conn.connector_instance_id not in model.connectors:
            model.add_connector(conn)
    for pin in incoming.pins.values():
        if pin.pin_id not in model.pins:
            model.add_pin(pin)
    for net in incoming.nets.values():
        if net.net_id not in model.nets:
            model.add_net(net)
    for wire in incoming.wires.values():
        if wire.wire_id not in model.wires:
            model.add_wire(wire)
    for splice in incoming.splices.values():
        if splice.splice_id not in model.splices:
            model.add_splice(splice)
    for seg in incoming.bundle_segments.values():
        if seg.segment_id not in model.bundle_segments:
            model.add_bundle_segment(seg)

    project_store.notify_changed()
    _populate_doc_objects(doc, incoming)
    doc.recompute()
    FreeCAD.Console.PrintMessage(
        f"ElectricalHarness: inserted {filename} into {docname}\n"
    )
    return doc


def export(export_list: Iterable[object], filename: str) -> bool:
    """Export the active model to an .ehproj.json file."""
    model = project_store.get_active_model(create_if_missing=False)
    serializer = ProjectSerializer()
    serializer.dump_file(model, filename)
    FreeCAD.Console.PrintMessage(
        f"ElectricalHarness: exported to {filename}\n"
    )
    return True


# ── helpers ──────────────────────────────────────────────────────


def _populate_doc_objects(doc, model: ElectricalProjectModel) -> None:
    """Create FeaturePython doc objects from a loaded model."""
    project_obj = make_harness_project(doc, model.project.name or "HarnessProject")
    project_obj.StableId = model.project.project_id
    project_obj.ProjectName = model.project.name
    project_obj.UnitSystem = model.project.unit_system
    project_obj.ConnectorCount = len(model.connectors)
    project_obj.WireCount = len(model.wires)
    project_obj.NetCount = len(model.nets)

    for conn in model.connectors.values():
        obj = make_connector_instance(doc, conn.reference or "Connector")
        obj.StableId = conn.connector_instance_id
        obj.Reference = conn.reference
        obj.DefinitionId = conn.connector_definition_id
        obj.PinCount = len(model.connector_pin_ids(conn.connector_instance_id))
        obj.PlacementPath = conn.placement_path or ""
