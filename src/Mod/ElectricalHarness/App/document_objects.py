"""FreeCAD document object proxies for electrical harness artifacts.

Each proxy adds domain-specific properties to FeaturePython objects so that
users can inspect and edit harness data in the standard FreeCAD property panel.
"""

from __future__ import annotations

from typing import Callable

import FreeCAD


# ── helpers ──────────────────────────────────────────────────────


def _add_prop(obj, ptype: str, name: str, group: str, tip: str) -> None:
    if not hasattr(obj, name):
        obj.addProperty(ptype, name, group, tip)


# ── base proxy ───────────────────────────────────────────────────


class _BaseProxy:
    type_name = "ElectricalHarness::Base"

    def __init__(self, obj) -> None:
        obj.Proxy = self
        self.attach(obj)

    def attach(self, obj) -> None:
        _add_prop(obj, "App::PropertyString", "StableId", "Electrical", "Stable identifier")
        _add_prop(obj, "App::PropertyString", "RevisionTag", "Electrical", "Revision marker")

    def execute(self, obj) -> None:
        return


# ── concrete proxies ─────────────────────────────────────────────


class HarnessProjectProxy(_BaseProxy):
    type_name = "ElectricalHarness::Project"

    def attach(self, obj) -> None:
        super().attach(obj)
        _add_prop(obj, "App::PropertyString", "ProjectName", "Project", "Human-readable project name")
        _add_prop(obj, "App::PropertyString", "UnitSystem", "Project", "SI or Imperial")
        _add_prop(obj, "App::PropertyInteger", "ConnectorCount", "Project", "Number of connectors")
        _add_prop(obj, "App::PropertyInteger", "WireCount", "Project", "Number of wires")
        _add_prop(obj, "App::PropertyInteger", "NetCount", "Project", "Number of nets")


class ConnectorInstanceProxy(_BaseProxy):
    type_name = "ElectricalHarness::ConnectorInstance"

    def attach(self, obj) -> None:
        super().attach(obj)
        _add_prop(obj, "App::PropertyString", "Reference", "Connector", "Harness reference designator")
        _add_prop(obj, "App::PropertyString", "DefinitionId", "Connector", "Connector definition part ID")
        _add_prop(obj, "App::PropertyInteger", "PinCount", "Connector", "Number of pin cavities")
        _add_prop(obj, "App::PropertyString", "PlacementPath", "Connector", "3-D placement path in assembly")


class RoutePathProxy(_BaseProxy):
    type_name = "ElectricalHarness::RoutePath"

    def attach(self, obj) -> None:
        super().attach(obj)
        _add_prop(obj, "App::PropertyString", "FromNode", "Route", "Starting route node")
        _add_prop(obj, "App::PropertyString", "ToNode", "Route", "Ending route node")
        _add_prop(obj, "App::PropertyFloat", "MinBendRadius", "Route", "Minimum bend radius (mm)")
        _add_prop(obj, "App::PropertyBool", "IsLocked", "Route", "Whether route segment is locked")


class BundleSegmentProxy(_BaseProxy):
    type_name = "ElectricalHarness::BundleSegment"

    def attach(self, obj) -> None:
        super().attach(obj)
        _add_prop(obj, "App::PropertyString", "BundleId", "Bundle", "Parent bundle ID")
        _add_prop(obj, "App::PropertyString", "FromNode", "Bundle", "Starting route node")
        _add_prop(obj, "App::PropertyString", "ToNode", "Bundle", "Ending route node")
        _add_prop(obj, "App::PropertyFloat", "NominalDiameter", "Bundle", "Nominal outer diameter (mm)")


class SpliceProxy(_BaseProxy):
    type_name = "ElectricalHarness::Splice"

    def attach(self, obj) -> None:
        super().attach(obj)
        _add_prop(obj, "App::PropertyString", "SpliceType", "Splice", "inline / branched")
        _add_prop(obj, "App::PropertyInteger", "MemberCount", "Splice", "Number of joined pins")


class CoveringSegmentProxy(_BaseProxy):
    type_name = "ElectricalHarness::CoveringSegment"

    def attach(self, obj) -> None:
        super().attach(obj)
        _add_prop(obj, "App::PropertyString", "Material", "Covering", "Covering material")
        _add_prop(obj, "App::PropertyString", "SegmentId", "Covering", "Target bundle segment")
        _add_prop(obj, "App::PropertyFloat", "StartRatio", "Covering", "Start coverage ratio (0-1)")
        _add_prop(obj, "App::PropertyFloat", "EndRatio", "Covering", "End coverage ratio (0-1)")


class FormboardOutputProxy(_BaseProxy):
    type_name = "ElectricalHarness::FormboardOutput"

    def attach(self, obj) -> None:
        super().attach(obj)
        _add_prop(obj, "App::PropertyInteger", "SegmentCount", "Formboard", "Flattened segment count")
        _add_prop(obj, "App::PropertyFloat", "TotalLength", "Formboard", "Total harness length (mm)")
        _add_prop(obj, "App::PropertyInteger", "BreakoutCount", "Formboard", "Connector breakout count")


class ReportProxy(_BaseProxy):
    type_name = "ElectricalHarness::Report"

    def attach(self, obj) -> None:
        super().attach(obj)
        _add_prop(obj, "App::PropertyString", "ReportType", "Report", "Report type (from_to, bom, wire_list)")
        _add_prop(obj, "App::PropertyString", "OutputFormat", "Report", "csv / json")
        _add_prop(obj, "App::PropertyInteger", "RowCount", "Report", "Number of report rows")


# ── factory functions ────────────────────────────────────────────


def _make_object(doc, object_name: str, constructor: Callable) -> object:
    obj = doc.addObject("App::FeaturePython", object_name)
    constructor(obj)
    return obj


def make_harness_project(doc, name: str = "HarnessProject"):
    return _make_object(doc, name, HarnessProjectProxy)


def make_connector_instance(doc, name: str = "ConnectorInstance"):
    return _make_object(doc, name, ConnectorInstanceProxy)


def make_route_path(doc, name: str = "RoutePath"):
    return _make_object(doc, name, RoutePathProxy)


def make_bundle_segment(doc, name: str = "BundleSegment"):
    return _make_object(doc, name, BundleSegmentProxy)


def make_splice(doc, name: str = "Splice"):
    return _make_object(doc, name, SpliceProxy)


def make_covering_segment(doc, name: str = "CoveringSegment"):
    return _make_object(doc, name, CoveringSegmentProxy)


def make_formboard_output(doc, name: str = "FormboardOutput"):
    return _make_object(doc, name, FormboardOutputProxy)


def make_report_object(doc, name: str = "HarnessReport"):
    return _make_object(doc, name, ReportProxy)


def register_default_objects() -> None:
    FreeCAD.Console.PrintLog("ElectricalHarness: document object proxies ready\n")
