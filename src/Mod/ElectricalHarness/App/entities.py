"""Normalized electrical harness domain entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class RevisionInfo:
    revision_id: str
    author: str
    timestamp_iso: str
    change_summary: str = ""


@dataclass
class Project:
    project_id: str
    name: str
    unit_system: str = "SI"
    metadata: Dict[str, str] = field(default_factory=dict)
    revision: Optional[RevisionInfo] = None


@dataclass
class Sheet:
    sheet_id: str
    name: str
    index: int


@dataclass
class SymbolDefinition:
    symbol_id: str
    category: str
    display_name: str
    pin_layout: Dict[str, str] = field(default_factory=dict)


@dataclass
class DeviceDefinition:
    device_definition_id: str
    manufacturer: str
    part_number: str
    default_symbol_id: str


@dataclass
class DeviceInstance:
    device_instance_id: str
    device_definition_id: str
    reference: str
    sheet_id: str


@dataclass
class ConnectorDefinition:
    connector_definition_id: str
    display_name: str
    cavity_count: int = 0
    cavity_map: Dict[str, str] = field(default_factory=dict)
    manufacturer: str = ""
    part_number: str = ""


@dataclass
class ConnectorInstance:
    connector_instance_id: str
    connector_definition_id: str
    reference: str
    device_instance_id: Optional[str] = None
    placement_path: str = ""


@dataclass
class PinCavity:
    pin_id: str
    connector_instance_id: str
    cavity_name: str


@dataclass
class NetSignal:
    net_id: str
    name: str
    signal_type: str = "power"


@dataclass
class Wire:
    wire_id: str
    net_id: str
    from_pin_id: str
    to_pin_id: str
    gauge: str
    color: str
    wire_number: str = ""
    strip_length_mm: float = 0.0
    cable_id: str = ""


@dataclass
class Cable:
    cable_id: str
    display_name: str
    conductor_ids: List[str] = field(default_factory=list)
    shield_type: str = ""
    jacket_material: str = ""
    outer_diameter_mm: float = 0.0


@dataclass
class TwistedPair:
    twisted_pair_id: str
    wire_id_a: str
    wire_id_b: str
    twist_pitch_mm: float = 25.0
    cable_id: str = ""


@dataclass
class ShieldedGroup:
    shield_id: str
    display_name: str
    member_wire_ids: List[str] = field(default_factory=list)
    shield_type: str = "braided"
    coverage_percent: float = 85.0
    drain_wire_id: str = ""
    cable_id: str = ""


@dataclass
class CoreConductor:
    conductor_id: str
    cable_id: str
    net_id: str


@dataclass
class Splice:
    splice_id: str
    member_pin_ids: List[str]
    splice_type: str = "inline"


@dataclass
class Bundle:
    bundle_id: str
    display_name: str


@dataclass
class BundleSegment:
    segment_id: str
    bundle_id: str
    from_node_id: str
    to_node_id: str
    nominal_diameter_mm: float = 6.0
    length_mm: float = 0.0
    min_bend_radius_mm: float = 0.0
    max_fill_ratio: float = 0.0


@dataclass
class RouteNode:
    route_node_id: str
    node_type: str
    reference: str


@dataclass
class RouteGuide:
    guide_id: str
    name: str
    support_node_ids: List[str] = field(default_factory=list)


@dataclass
class Covering:
    covering_id: str
    segment_id: str
    material: str
    covering_type: str = "tape"
    start_ratio: float = 0.0
    end_ratio: float = 1.0


@dataclass
class ClipClampSupport:
    support_id: str
    support_type: str
    host_path: str
    segment_id: str = ""
    position_ratio: float = 0.5


@dataclass
class BackshellAccessory:
    accessory_id: str
    connector_instance_id: str
    accessory_type: str


@dataclass
class ManufacturingView:
    view_id: str
    project_id: str
    flattened_segments: List[str] = field(default_factory=list)


@dataclass
class ReportDefinition:
    report_id: str
    name: str
    report_type: str
    fields: List[str] = field(default_factory=list)


@dataclass
class ValidationIssue:
    issue_id: str
    severity: str
    code: str
    message: str
    entity_id: str


# ── Wire numbering configuration ────────────────────────────────


@dataclass
class WireNumberingConfig:
    prefix: str = "W"
    suffix: str = ""
    start_number: int = 1
    zero_pad: int = 3
    separator: str = ""
    include_net_name: bool = False


# ── Component library ────────────────────────────────────────────


@dataclass
class LibraryEntry:
    entry_id: str
    category: str
    name: str
    manufacturer: str = ""
    part_number: str = ""
    description: str = ""
    attributes: Dict[str, str] = field(default_factory=dict)
    is_generic: bool = True
    specific_part_id: str = ""
    favorite: bool = False
    certification_tier: str = "basic"
