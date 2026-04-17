"""Convenience factory wrappers for document-object creation commands."""

from __future__ import annotations

import FreeCAD

from App import document_objects


def ensure_document():
    if FreeCAD.ActiveDocument:
        return FreeCAD.ActiveDocument
    return FreeCAD.newDocument("ElectricalHarness")


def create_harness_project() -> None:
    doc = ensure_document()
    document_objects.make_harness_project(doc)
    doc.recompute()


def create_connector_instance() -> None:
    doc = ensure_document()
    document_objects.make_connector_instance(doc)
    doc.recompute()


def create_route_path() -> None:
    doc = ensure_document()
    document_objects.make_route_path(doc)
    doc.recompute()


def create_bundle_segment() -> None:
    doc = ensure_document()
    document_objects.make_bundle_segment(doc)
    doc.recompute()
