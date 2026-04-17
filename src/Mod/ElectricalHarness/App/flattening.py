"""Harness flattening service — topology-preserving formboard generation.

Preserves branch structure, connector breakout semantics, and manufacturing
traceability from flattened segments back to 3D source topology.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Set

from .model import ElectricalProjectModel


@dataclass
class FlattenedSegment:
    source_segment_id: str
    branch_order: int
    flattened_length_mm: float
    from_node_id: str = ""
    to_node_id: str = ""
    wire_ids: List[str] = field(default_factory=list)
    covering_ids: List[str] = field(default_factory=list)


@dataclass
class ConnectorBreakout:
    connector_instance_id: str
    reference: str
    pin_ids: List[str]
    attached_wire_ids: List[str]


@dataclass
class WireLengthEntry:
    wire_id: str
    net_id: str
    from_pin_id: str
    to_pin_id: str
    gauge: str
    color: str
    cut_length_mm: float
    segment_ids: List[str] = field(default_factory=list)


@dataclass
class FlattenedHarness:
    project_id: str
    segments: List[FlattenedSegment]
    connector_breakouts: List[ConnectorBreakout] = field(default_factory=list)
    wire_lengths: List[WireLengthEntry] = field(default_factory=list)
    total_harness_length_mm: float = 0.0


class FlatteningEngine:
    """Topology-preserving flattening with branch ordering and traceability."""

    def flatten(self, model: ElectricalProjectModel) -> FlattenedHarness:
        segments = self._flatten_segments(model)
        breakouts = self._build_connector_breakouts(model)
        wire_lengths = self._compute_wire_lengths(model, segments)
        total_length = sum(seg.flattened_length_mm for seg in segments)

        return FlattenedHarness(
            project_id=model.project.project_id,
            segments=segments,
            connector_breakouts=breakouts,
            wire_lengths=wire_lengths,
            total_harness_length_mm=total_length,
        )

    def _flatten_segments(self, model: ElectricalProjectModel) -> List[FlattenedSegment]:
        """Build topologically ordered flattened segments from bundle topology."""
        segs = list(model.bundle_segments.values())
        if not segs:
            return []

        # Build adjacency for topological ordering
        adj: Dict[str, List[str]] = defaultdict(list)
        seg_by_id: Dict[str, object] = {}
        for seg in segs:
            adj[seg.from_node_id].append(seg.segment_id)
            seg_by_id[seg.segment_id] = seg

        # BFS order from the node with most connections (trunk heuristic)
        node_degree: Dict[str, int] = defaultdict(int)
        for seg in segs:
            node_degree[seg.from_node_id] += 1
            node_degree[seg.to_node_id] += 1
        trunk_node = max(node_degree, key=node_degree.get) if node_degree else segs[0].from_node_id

        visited_segs: Set[str] = set()
        ordered: List[FlattenedSegment] = []

        # BFS through segments
        queue_nodes = [trunk_node]
        visited_nodes: Set[str] = set()
        branch_order = 0

        while queue_nodes:
            node = queue_nodes.pop(0)
            if node in visited_nodes:
                continue
            visited_nodes.add(node)

            for seg in segs:
                if seg.segment_id in visited_segs:
                    continue
                if seg.from_node_id == node or seg.to_node_id == node:
                    visited_segs.add(seg.segment_id)

                    # Collect wire IDs routed through this segment (by net matching)
                    wire_ids = self._wires_on_segment(model, seg.segment_id)

                    # Collect coverings
                    covering_ids = [
                        cov.covering_id for cov in getattr(model, 'coverings', {}).values()
                        if getattr(cov, 'segment_id', '') == seg.segment_id
                    ] if hasattr(model, 'coverings') else []

                    ordered.append(FlattenedSegment(
                        source_segment_id=seg.segment_id,
                        branch_order=branch_order,
                        flattened_length_mm=seg.nominal_diameter_mm * 10.0,  # proxy until real geometry
                        from_node_id=seg.from_node_id,
                        to_node_id=seg.to_node_id,
                        wire_ids=wire_ids,
                        covering_ids=covering_ids,
                    ))
                    branch_order += 1

                    other_node = seg.to_node_id if seg.from_node_id == node else seg.from_node_id
                    if other_node not in visited_nodes:
                        queue_nodes.append(other_node)

        return ordered

    def _build_connector_breakouts(self, model: ElectricalProjectModel) -> List[ConnectorBreakout]:
        """Generate connector breakout entries for formboard documentation."""
        breakouts: List[ConnectorBreakout] = []
        for conn in model.connectors.values():
            pin_ids = model.connector_pin_ids(conn.connector_instance_id)
            wire_ids: List[str] = []
            for pin_id in pin_ids:
                for wire in model.wires.values():
                    if wire.from_pin_id == pin_id or wire.to_pin_id == pin_id:
                        if wire.wire_id not in wire_ids:
                            wire_ids.append(wire.wire_id)
            breakouts.append(ConnectorBreakout(
                connector_instance_id=conn.connector_instance_id,
                reference=conn.reference,
                pin_ids=pin_ids,
                attached_wire_ids=wire_ids,
            ))
        return breakouts

    def _compute_wire_lengths(
        self, model: ElectricalProjectModel, segments: List[FlattenedSegment]
    ) -> List[WireLengthEntry]:
        """Compute cut lengths for each wire based on segments it traverses."""
        # Build wire->segment mapping
        wire_segments: Dict[str, List[str]] = defaultdict(list)
        wire_length: Dict[str, float] = defaultdict(float)
        for seg in segments:
            for wire_id in seg.wire_ids:
                wire_segments[wire_id].append(seg.source_segment_id)
                wire_length[wire_id] += seg.flattened_length_mm

        entries: List[WireLengthEntry] = []
        for wire in model.wires.values():
            cut = wire_length.get(wire.wire_id, 0.0)
            # Minimum: connector-to-connector terminal length estimate
            if cut < 1.0:
                cut = 100.0  # default stub length when no segments routed
            entries.append(WireLengthEntry(
                wire_id=wire.wire_id,
                net_id=wire.net_id,
                from_pin_id=wire.from_pin_id,
                to_pin_id=wire.to_pin_id,
                gauge=wire.gauge,
                color=wire.color,
                cut_length_mm=cut,
                segment_ids=wire_segments.get(wire.wire_id, []),
            ))
        return entries

    def _wires_on_segment(self, model: ElectricalProjectModel, segment_id: str) -> List[str]:
        """Heuristic: all wires are assumed to route through all segments for now.
        Real implementation would use net-to-segment routing data."""
        return list(model.wires.keys())
