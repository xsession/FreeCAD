"""Canonical project model and connectivity graph."""

from __future__ import annotations

import math
from dataclasses import asdict
from typing import Dict, Iterable, List, Optional, Set

from .entities import (
    BundleSegment,
    Cable,
    ClipClampSupport,
    ConnectorInstance,
    Covering,
    LibraryEntry,
    NetSignal,
    PinCavity,
    Project,
    ShieldedGroup,
    Splice,
    TwistedPair,
    Wire,
    WireNumberingConfig,
)


class ElectricalProjectModel:
    """Source-of-truth model shared by schematic, 3D, and reports."""

    def __init__(self, project: Project) -> None:
        self.project = project
        self.connectors: Dict[str, ConnectorInstance] = {}
        self.pins: Dict[str, PinCavity] = {}
        self.nets: Dict[str, NetSignal] = {}
        self.wires: Dict[str, Wire] = {}
        self.splices: Dict[str, Splice] = {}
        self.bundle_segments: Dict[str, BundleSegment] = {}
        self.locked_route_segments: Set[str] = set()

        # Phase 2 entity collections
        self.cables: Dict[str, Cable] = {}
        self.twisted_pairs: Dict[str, TwistedPair] = {}
        self.shields: Dict[str, ShieldedGroup] = {}
        self.coverings: Dict[str, Covering] = {}
        self.clips: Dict[str, ClipClampSupport] = {}

        # Wire numbering
        self._wire_numbering = WireNumberingConfig()
        self._wire_number_counter: int = 0

        # Change tracking for incremental validation
        self._dirty_entities: Set[str] = set()
        self._change_generation: int = 0
        self._last_validated_generation: int = -1

    # ── Phase 1 mutators (unchanged API) ─────────────────────────

    def add_connector(self, connector: ConnectorInstance) -> None:
        self.connectors[connector.connector_instance_id] = connector
        self._mark_dirty(connector.connector_instance_id)

    def add_pin(self, pin: PinCavity) -> None:
        self.pins[pin.pin_id] = pin
        self._mark_dirty(pin.pin_id)

    def add_net(self, net: NetSignal) -> None:
        self.nets[net.net_id] = net
        self._mark_dirty(net.net_id)

    def add_wire(self, wire: Wire) -> None:
        self.wires[wire.wire_id] = wire
        self._mark_dirty(wire.wire_id)
        self._mark_dirty(wire.from_pin_id)
        self._mark_dirty(wire.to_pin_id)
        self._mark_dirty(wire.net_id)

    def add_splice(self, splice: Splice) -> None:
        self.splices[splice.splice_id] = splice
        self._mark_dirty(splice.splice_id)

    def add_bundle_segment(self, segment: BundleSegment) -> None:
        self.bundle_segments[segment.segment_id] = segment
        self._mark_dirty(segment.segment_id)

    # ── Phase 2 mutators ─────────────────────────────────────────

    def add_cable(self, cable: Cable) -> None:
        self.cables[cable.cable_id] = cable
        self._mark_dirty(cable.cable_id)

    def add_twisted_pair(self, tp: TwistedPair) -> None:
        self.twisted_pairs[tp.twisted_pair_id] = tp
        self._mark_dirty(tp.twisted_pair_id)

    def add_shield(self, shield: ShieldedGroup) -> None:
        self.shields[shield.shield_id] = shield
        self._mark_dirty(shield.shield_id)

    def add_covering(self, covering: Covering) -> None:
        self.coverings[covering.covering_id] = covering
        self._mark_dirty(covering.covering_id)
        self._mark_dirty(covering.segment_id)

    def add_clip(self, clip: ClipClampSupport) -> None:
        self.clips[clip.support_id] = clip
        self._mark_dirty(clip.support_id)

    def remove_wire(self, wire_id: str) -> bool:
        wire = self.wires.pop(wire_id, None)
        if wire:
            self._mark_dirty(wire_id)
            self._mark_dirty(wire.from_pin_id)
            self._mark_dirty(wire.to_pin_id)
            return True
        return False

    def remove_connector(self, connector_id: str) -> bool:
        if connector_id in self.connectors:
            del self.connectors[connector_id]
            self._mark_dirty(connector_id)
            return True
        return False

    # ── ID generation ────────────────────────────────────────────

    def _next_id(self, prefix: str, table: Dict[str, object]) -> str:
        if not table:
            return f"{prefix}1"
        index = 1
        while f"{prefix}{index}" in table:
            index += 1
        return f"{prefix}{index}"

    def next_connector_id(self) -> str:
        return self._next_id("J", self.connectors)

    def next_pin_id(self, connector_ref: str, cavity_name: str) -> str:
        candidate = f"{connector_ref}-{cavity_name}"
        if candidate not in self.pins:
            return candidate
        index = 1
        while f"{candidate}-{index}" in self.pins:
            index += 1
        return f"{candidate}-{index}"

    def next_net_id(self) -> str:
        return self._next_id("NET", self.nets)

    def next_wire_id(self) -> str:
        return self._next_id("W", self.wires)

    def next_cable_id(self) -> str:
        return self._next_id("CBL", self.cables)

    def next_shield_id(self) -> str:
        return self._next_id("SHD", self.shields)

    def next_twisted_pair_id(self) -> str:
        return self._next_id("TP", self.twisted_pairs)

    def next_covering_id(self) -> str:
        return self._next_id("COV", self.coverings)

    def next_clip_id(self) -> str:
        return self._next_id("CLP", self.clips)

    # ── Composite operations ─────────────────────────────────────

    def add_connector_with_pins(
        self,
        reference: str,
        pin_count: int,
        connector_definition_id: str = "CONN-GENERIC",
    ) -> ConnectorInstance:
        connector_id = self.next_connector_id()
        connector = ConnectorInstance(
            connector_instance_id=connector_id,
            connector_definition_id=connector_definition_id,
            reference=reference,
        )
        self.add_connector(connector)
        for cavity_idx in range(1, max(pin_count, 0) + 1):
            cavity = str(cavity_idx)
            pin_id = self.next_pin_id(reference, cavity)
            self.add_pin(
                PinCavity(
                    pin_id=pin_id,
                    connector_instance_id=connector_id,
                    cavity_name=cavity,
                )
            )
        return connector

    def create_or_get_net(self, name: str, signal_type: str = "power") -> NetSignal:
        for net in self.nets.values():
            if net.name == name:
                return net
        net = NetSignal(net_id=self.next_net_id(), name=name, signal_type=signal_type)
        self.add_net(net)
        return net

    def connect_pins(
        self,
        from_pin_id: str,
        to_pin_id: str,
        net_name: str,
        gauge: str = "22AWG",
        color: str = "RD",
    ) -> Wire:
        net = self.create_or_get_net(net_name)
        wire = Wire(
            wire_id=self.next_wire_id(),
            net_id=net.net_id,
            from_pin_id=from_pin_id,
            to_pin_id=to_pin_id,
            gauge=gauge,
            color=color,
        )
        self.add_wire(wire)
        return wire

    def create_cable(
        self,
        display_name: str,
        wire_ids: Optional[List[str]] = None,
        shield_type: str = "",
        jacket_material: str = "",
    ) -> Cable:
        cable = Cable(
            cable_id=self.next_cable_id(),
            display_name=display_name,
            conductor_ids=list(wire_ids or []),
            shield_type=shield_type,
            jacket_material=jacket_material,
        )
        self.add_cable(cable)
        for wid in cable.conductor_ids:
            if wid in self.wires:
                self.wires[wid].cable_id = cable.cable_id
                self._mark_dirty(wid)
        return cable

    def create_twisted_pair(
        self,
        wire_id_a: str,
        wire_id_b: str,
        twist_pitch_mm: float = 25.0,
        cable_id: str = "",
    ) -> TwistedPair:
        tp = TwistedPair(
            twisted_pair_id=self.next_twisted_pair_id(),
            wire_id_a=wire_id_a,
            wire_id_b=wire_id_b,
            twist_pitch_mm=twist_pitch_mm,
            cable_id=cable_id,
        )
        self.add_twisted_pair(tp)
        return tp

    def create_shield(
        self,
        display_name: str,
        member_wire_ids: Optional[List[str]] = None,
        shield_type: str = "braided",
        coverage_percent: float = 85.0,
        drain_wire_id: str = "",
    ) -> ShieldedGroup:
        shield = ShieldedGroup(
            shield_id=self.next_shield_id(),
            display_name=display_name,
            member_wire_ids=list(member_wire_ids or []),
            shield_type=shield_type,
            coverage_percent=coverage_percent,
            drain_wire_id=drain_wire_id,
        )
        self.add_shield(shield)
        return shield

    def add_covering_to_segment(
        self,
        segment_id: str,
        material: str,
        covering_type: str = "tape",
        start_ratio: float = 0.0,
        end_ratio: float = 1.0,
    ) -> Covering:
        covering = Covering(
            covering_id=self.next_covering_id(),
            segment_id=segment_id,
            material=material,
            covering_type=covering_type,
            start_ratio=start_ratio,
            end_ratio=end_ratio,
        )
        self.add_covering(covering)
        return covering

    # ── Wire numbering ───────────────────────────────────────────

    @property
    def wire_numbering_config(self) -> WireNumberingConfig:
        return self._wire_numbering

    def configure_wire_numbering(
        self,
        prefix: str = "W",
        suffix: str = "",
        start_number: int = 1,
        zero_pad: int = 3,
        separator: str = "",
        include_net_name: bool = False,
    ) -> None:
        self._wire_numbering = WireNumberingConfig(
            prefix=prefix,
            suffix=suffix,
            start_number=start_number,
            zero_pad=zero_pad,
            separator=separator,
            include_net_name=include_net_name,
        )

    def auto_number_wires(self) -> int:
        cfg = self._wire_numbering
        count = 0
        for idx, wire in enumerate(sorted(self.wires.values(), key=lambda w: w.wire_id)):
            num = cfg.start_number + idx
            num_str = str(num).zfill(cfg.zero_pad)
            parts = [cfg.prefix, cfg.separator, num_str]
            if cfg.include_net_name:
                net = self.nets.get(wire.net_id)
                if net:
                    parts.append(cfg.separator)
                    parts.append(net.name)
            parts.append(cfg.suffix)
            wire.wire_number = "".join(parts)
            self._mark_dirty(wire.wire_id)
            count += 1
        self._wire_number_counter = count
        return count

    # ── Change tracking ──────────────────────────────────────────

    def _mark_dirty(self, entity_id: str) -> None:
        self._dirty_entities.add(entity_id)
        self._change_generation += 1

    @property
    def dirty_entities(self) -> Set[str]:
        return set(self._dirty_entities)

    @property
    def change_generation(self) -> int:
        return self._change_generation

    @property
    def needs_validation(self) -> bool:
        return self._change_generation != self._last_validated_generation

    def mark_validated(self) -> None:
        self._last_validated_generation = self._change_generation
        self._dirty_entities.clear()

    def dependent_entity_ids(self, entity_id: str) -> Set[str]:
        """Return IDs of entities that depend on the given entity."""
        deps: Set[str] = set()
        # Pin → wires that reference it
        for wire in self.wires.values():
            if wire.from_pin_id == entity_id or wire.to_pin_id == entity_id:
                deps.add(wire.wire_id)
        # Net → wires on that net
        for wire in self.wires.values():
            if wire.net_id == entity_id:
                deps.add(wire.wire_id)
        # Connector → pins belonging to it
        for pin in self.pins.values():
            if pin.connector_instance_id == entity_id:
                deps.add(pin.pin_id)
        # Segment → coverings on it
        for cov in self.coverings.values():
            if cov.segment_id == entity_id:
                deps.add(cov.covering_id)
        # Cable → wires in it
        cable = self.cables.get(entity_id)
        if cable:
            for wid in cable.conductor_ids:
                deps.add(wid)
        # Shield → member wires
        shield = self.shields.get(entity_id)
        if shield:
            for wid in shield.member_wire_ids:
                deps.add(wid)
        return deps

    # ── Queries ──────────────────────────────────────────────────

    def connector_pin_ids(self, connector_instance_id: str) -> List[str]:
        return [
            pin.pin_id
            for pin in self.pins.values()
            if pin.connector_instance_id == connector_instance_id
        ]

    def wires_in_cable(self, cable_id: str) -> List[Wire]:
        return [w for w in self.wires.values() if w.cable_id == cable_id]

    def coverings_on_segment(self, segment_id: str) -> List[Covering]:
        return [c for c in self.coverings.values() if c.segment_id == segment_id]

    def shields_for_wire(self, wire_id: str) -> List[ShieldedGroup]:
        return [s for s in self.shields.values() if wire_id in s.member_wire_ids]

    def segment_fill_ratio(self, segment_id: str) -> float:
        """Compute approximate fill ratio for a bundle segment."""
        seg = self.bundle_segments.get(segment_id)
        if not seg or seg.nominal_diameter_mm <= 0:
            return 0.0
        conduit_area = math.pi * (seg.nominal_diameter_mm / 2.0) ** 2
        wire_area = 0.0
        gauge_dia_map = {
            "30AWG": 0.254, "28AWG": 0.321, "26AWG": 0.405, "24AWG": 0.511,
            "22AWG": 0.644, "20AWG": 0.812, "18AWG": 1.024, "16AWG": 1.291,
            "14AWG": 1.628, "12AWG": 2.053, "10AWG": 2.588, "8AWG": 3.264,
        }
        for wire in self.wires.values():
            dia = gauge_dia_map.get(wire.gauge, 0.644)
            wire_area += math.pi * (dia / 2.0) ** 2
        if conduit_area <= 0:
            return 0.0
        return wire_area / conduit_area

    def rename_net(self, current_name: str, new_name: str) -> int:
        updated = 0
        for net in self.nets.values():
            if net.name == current_name:
                net.name = new_name
                self._mark_dirty(net.net_id)
                updated += 1
        return updated

    def mark_segment_locked(self, segment_id: str, locked: bool = True) -> None:
        if locked:
            self.locked_route_segments.add(segment_id)
        else:
            self.locked_route_segments.discard(segment_id)

    def build_pin_graph(self) -> Dict[str, Set[str]]:
        graph: Dict[str, Set[str]] = {pin_id: set() for pin_id in self.pins.keys()}
        for wire in self.wires.values():
            graph.setdefault(wire.from_pin_id, set()).add(wire.to_pin_id)
            graph.setdefault(wire.to_pin_id, set()).add(wire.from_pin_id)

        for splice in self.splices.values():
            members = splice.member_pin_ids
            for index, src in enumerate(members):
                for dst in members[index + 1 :]:
                    graph.setdefault(src, set()).add(dst)
                    graph.setdefault(dst, set()).add(src)
        return graph

    def nets_touching_pin(self, pin_id: str) -> List[str]:
        return [wire.net_id for wire in self.wires.values() if pin_id in (wire.from_pin_id, wire.to_pin_id)]

    def unresolved_pins(self) -> List[str]:
        pin_graph = self.build_pin_graph()
        return [pin_id for pin_id, linked in pin_graph.items() if not linked]

    # ── Snapshot ─────────────────────────────────────────────────

    def as_snapshot(self) -> Dict[str, object]:
        return {
            "project": asdict(self.project),
            "connectors": [asdict(item) for item in self.connectors.values()],
            "pins": [asdict(item) for item in self.pins.values()],
            "nets": [asdict(item) for item in self.nets.values()],
            "wires": [asdict(item) for item in self.wires.values()],
            "splices": [asdict(item) for item in self.splices.values()],
            "bundle_segments": [asdict(item) for item in self.bundle_segments.values()],
            "locked_route_segments": sorted(self.locked_route_segments),
            "cables": [asdict(item) for item in self.cables.values()],
            "twisted_pairs": [asdict(item) for item in self.twisted_pairs.values()],
            "shields": [asdict(item) for item in self.shields.values()],
            "coverings": [asdict(item) for item in self.coverings.values()],
            "clips": [asdict(item) for item in self.clips.values()],
            "wire_numbering_config": asdict(self._wire_numbering),
        }

    def iter_entity_ids(self) -> Iterable[str]:
        yield self.project.project_id
        for table in (
            self.connectors,
            self.pins,
            self.nets,
            self.wires,
            self.splices,
            self.bundle_segments,
            self.cables,
            self.twisted_pairs,
            self.shields,
            self.coverings,
            self.clips,
        ):
            yield from table.keys()
