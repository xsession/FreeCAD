"""Validation and rule-engine foundation.

Enterprise-grade rule engine for electrical harness design validation.
Rules cover connectivity, manufacturing, routing, cable/shield integrity,
and data integrity. Supports both full and incremental validation modes.
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Callable, Dict, List, Optional, Set

from .entities import ValidationIssue
from .ids import StableIdProvider
from .model import ElectricalProjectModel


class ValidationEngine:
    def __init__(self) -> None:
        self._id_provider = StableIdProvider("ElectricalHarness.Validation")
        self._custom_rules: List[Callable[[ElectricalProjectModel], List[ValidationIssue]]] = []

    def register_custom_rule(
        self, rule_fn: Callable[[ElectricalProjectModel], List[ValidationIssue]]
    ) -> None:
        self._custom_rules.append(rule_fn)

    def run(self, model: ElectricalProjectModel) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        issues.extend(self._check_duplicate_entity_ids(model))
        issues.extend(self._check_unconnected_pins(model))
        issues.extend(self._check_illegal_splices(model))
        issues.extend(self._check_wire_gauge_pairing(model))
        issues.extend(self._check_dangling_wire_refs(model))
        issues.extend(self._check_net_consistency(model))
        issues.extend(self._check_connector_pin_orphans(model))
        issues.extend(self._check_bundle_segment_continuity(model))
        issues.extend(self._check_missing_connector_reference(model))
        issues.extend(self._check_duplicate_wire_connections(model))
        # Phase 2 rules
        issues.extend(self._check_bend_radius(model))
        issues.extend(self._check_fill_ratio(model))
        issues.extend(self._check_shielding_continuity(model))
        issues.extend(self._check_covering_overlap(model))
        issues.extend(self._check_cable_integrity(model))
        issues.extend(self._check_twisted_pair_validity(model))
        # Custom rules
        for rule_fn in self._custom_rules:
            issues.extend(rule_fn(model))
        model.mark_validated()
        return issues

    def run_incremental(
        self,
        model: ElectricalProjectModel,
        previous_issues: Optional[List[ValidationIssue]] = None,
    ) -> List[ValidationIssue]:
        """Re-validate only dirty entities and their dependents."""
        if not model.needs_validation:
            return list(previous_issues or [])

        dirty = set(model.dirty_entities)
        # Expand to include dependents
        expanded: Set[str] = set(dirty)
        for eid in dirty:
            expanded.update(model.dependent_entity_ids(eid))

        # Run full validation but filter to only entities in expanded set
        all_issues = self.run(model)
        return [issue for issue in all_issues if issue.entity_id in expanded or not expanded]

    def _issue(self, severity: str, code: str, message: str, entity_id: str) -> ValidationIssue:
        issue_id = self._id_provider.generate("ValidationIssue", f"{code}:{entity_id}:{message}").value
        return ValidationIssue(
            issue_id=issue_id,
            severity=severity,
            code=code,
            message=message,
            entity_id=entity_id,
        )

    # ── Data integrity ───────────────────────────────────────────

    def _check_duplicate_entity_ids(self, model: ElectricalProjectModel) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        seen: Set[str] = set()
        for entity_id in model.iter_entity_ids():
            if entity_id in seen:
                issues.append(
                    self._issue("error", "DUPLICATE_ID", "Duplicate stable identifier detected", entity_id)
                )
            seen.add(entity_id)
        return issues

    # ── Connectivity ─────────────────────────────────────────────

    def _check_unconnected_pins(self, model: ElectricalProjectModel) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        for pin_id in model.unresolved_pins():
            issues.append(
                self._issue("warning", "UNCONNECTED_PIN", "Pin is not connected to any net", pin_id)
            )
        return issues

    def _check_dangling_wire_refs(self, model: ElectricalProjectModel) -> List[ValidationIssue]:
        """Wires referencing pins or nets that don't exist."""
        issues: List[ValidationIssue] = []
        for wire in model.wires.values():
            if wire.from_pin_id not in model.pins:
                issues.append(
                    self._issue("error", "DANGLING_WIRE_PIN",
                                f"Wire from_pin '{wire.from_pin_id}' does not exist", wire.wire_id)
                )
            if wire.to_pin_id not in model.pins:
                issues.append(
                    self._issue("error", "DANGLING_WIRE_PIN",
                                f"Wire to_pin '{wire.to_pin_id}' does not exist", wire.wire_id)
                )
            if wire.net_id not in model.nets:
                issues.append(
                    self._issue("error", "DANGLING_WIRE_NET",
                                f"Wire net '{wire.net_id}' does not exist", wire.wire_id)
                )
        return issues

    def _check_net_consistency(self, model: ElectricalProjectModel) -> List[ValidationIssue]:
        """Nets with no wires attached are unused."""
        issues: List[ValidationIssue] = []
        used_nets: Set[str] = {wire.net_id for wire in model.wires.values()}
        for net_id in model.nets:
            if net_id not in used_nets:
                issues.append(
                    self._issue("info", "UNUSED_NET", "Net is defined but has no wires", net_id)
                )
        return issues

    def _check_duplicate_wire_connections(self, model: ElectricalProjectModel) -> List[ValidationIssue]:
        """Two wires connecting the exact same pin pair on the same net."""
        issues: List[ValidationIssue] = []
        seen: Set[tuple] = set()
        for wire in model.wires.values():
            key = (wire.net_id, min(wire.from_pin_id, wire.to_pin_id), max(wire.from_pin_id, wire.to_pin_id))
            if key in seen:
                issues.append(
                    self._issue("warning", "DUPLICATE_WIRE",
                                f"Duplicate wire on net connecting same pin pair", wire.wire_id)
                )
            seen.add(key)
        return issues

    # ── Splice integrity ─────────────────────────────────────────

    def _check_illegal_splices(self, model: ElectricalProjectModel) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        for splice in model.splices.values():
            if len(splice.member_pin_ids) < 2:
                issues.append(
                    self._issue("error", "ILLEGAL_SPLICE",
                                "Splice must contain at least two members", splice.splice_id)
                )
            for pin_id in splice.member_pin_ids:
                if pin_id not in model.pins:
                    issues.append(
                        self._issue("error", "SPLICE_BAD_PIN",
                                    f"Splice references non-existent pin '{pin_id}'", splice.splice_id)
                    )
        return issues

    # ── Manufacturing readiness ──────────────────────────────────

    def _check_wire_gauge_pairing(self, model: ElectricalProjectModel) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        for wire in model.wires.values():
            if not wire.gauge:
                issues.append(
                    self._issue("error", "MISSING_WIRE_GAUGE",
                                "Wire gauge is required for manufacturing output", wire.wire_id)
                )
            if not wire.color:
                issues.append(
                    self._issue("warning", "MISSING_WIRE_COLOR",
                                "Wire color is recommended for manufacturing output", wire.wire_id)
                )
        return issues

    def _check_missing_connector_reference(self, model: ElectricalProjectModel) -> List[ValidationIssue]:
        """Connectors without a user-facing reference designator."""
        issues: List[ValidationIssue] = []
        for conn in model.connectors.values():
            if not conn.reference or not conn.reference.strip():
                issues.append(
                    self._issue("warning", "MISSING_CONNECTOR_REF",
                                "Connector has no reference designator", conn.connector_instance_id)
                )
        return issues

    # ── Structural ───────────────────────────────────────────────

    def _check_connector_pin_orphans(self, model: ElectricalProjectModel) -> List[ValidationIssue]:
        """Pins referencing a connector that doesn't exist."""
        issues: List[ValidationIssue] = []
        for pin in model.pins.values():
            if pin.connector_instance_id not in model.connectors:
                issues.append(
                    self._issue("error", "ORPHAN_PIN",
                                f"Pin references non-existent connector '{pin.connector_instance_id}'",
                                pin.pin_id)
                )
        return issues

    # ── Routing topology ─────────────────────────────────────────

    def _check_bundle_segment_continuity(self, model: ElectricalProjectModel) -> List[ValidationIssue]:
        """Bundle segments whose from/to nodes don't form a connected graph."""
        issues: List[ValidationIssue] = []
        segments = list(model.bundle_segments.values())
        if len(segments) < 2:
            return issues

        adj: Dict[str, Set[str]] = {}
        for seg in segments:
            adj.setdefault(seg.from_node_id, set()).add(seg.to_node_id)
            adj.setdefault(seg.to_node_id, set()).add(seg.from_node_id)

        all_nodes = set(adj.keys())
        start = next(iter(all_nodes))
        visited: Set[str] = set()
        queue = [start]
        while queue:
            node = queue.pop()
            if node in visited:
                continue
            visited.add(node)
            for neighbor in adj.get(node, set()):
                if neighbor not in visited:
                    queue.append(neighbor)

        disconnected = all_nodes - visited
        for node_id in sorted(disconnected):
            issues.append(
                self._issue("warning", "DISCONNECTED_ROUTE_NODE",
                            f"Route node '{node_id}' is disconnected from main harness tree",
                            node_id)
            )
        return issues

    # ── Phase 2: Bend radius ─────────────────────────────────────

    def _check_bend_radius(self, model: ElectricalProjectModel) -> List[ValidationIssue]:
        """Segments with specified min bend radius less than wire gauge minimum."""
        issues: List[ValidationIssue] = []
        # Minimum bend radius per gauge (4x outer diameter rule of thumb)
        gauge_min_radius = {
            "30AWG": 1.0, "28AWG": 1.3, "26AWG": 1.6, "24AWG": 2.0,
            "22AWG": 2.6, "20AWG": 3.2, "18AWG": 4.1, "16AWG": 5.2,
            "14AWG": 6.5, "12AWG": 8.2, "10AWG": 10.4, "8AWG": 13.1,
        }
        for seg in model.bundle_segments.values():
            if seg.min_bend_radius_mm <= 0:
                continue
            # Find worst-case wire gauge routed through this segment
            max_required = 0.0
            worst_gauge = ""
            for wire in model.wires.values():
                req = gauge_min_radius.get(wire.gauge, 0.0)
                if req > max_required:
                    max_required = req
                    worst_gauge = wire.gauge
            if max_required > 0 and seg.min_bend_radius_mm < max_required:
                issues.append(
                    self._issue("warning", "BEND_RADIUS_VIOLATION",
                                f"Segment bend radius {seg.min_bend_radius_mm:.1f}mm "
                                f"< minimum {max_required:.1f}mm for {worst_gauge}",
                                seg.segment_id)
                )
        return issues

    # ── Phase 2: Fill ratio ──────────────────────────────────────

    def _check_fill_ratio(self, model: ElectricalProjectModel) -> List[ValidationIssue]:
        """Bundle segments exceeding their maximum fill ratio."""
        issues: List[ValidationIssue] = []
        for seg in model.bundle_segments.values():
            if seg.max_fill_ratio <= 0:
                continue
            actual = model.segment_fill_ratio(seg.segment_id)
            if actual > seg.max_fill_ratio:
                issues.append(
                    self._issue("warning", "FILL_RATIO_EXCEEDED",
                                f"Fill ratio {actual:.1%} exceeds maximum {seg.max_fill_ratio:.1%}",
                                seg.segment_id)
                )
        return issues

    # ── Phase 2: Shielding continuity ────────────────────────────

    def _check_shielding_continuity(self, model: ElectricalProjectModel) -> List[ValidationIssue]:
        """Shields must contain at least one wire and optionally a drain wire."""
        issues: List[ValidationIssue] = []
        for shield in model.shields.values():
            if not shield.member_wire_ids:
                issues.append(
                    self._issue("error", "SHIELD_EMPTY",
                                "Shielded group has no member wires", shield.shield_id)
                )
                continue
            for wid in shield.member_wire_ids:
                if wid not in model.wires:
                    issues.append(
                        self._issue("error", "SHIELD_DANGLING_WIRE",
                                    f"Shield references non-existent wire '{wid}'",
                                    shield.shield_id)
                    )
            if shield.drain_wire_id and shield.drain_wire_id not in model.wires:
                issues.append(
                    self._issue("error", "SHIELD_DANGLING_DRAIN",
                                f"Shield drain wire '{shield.drain_wire_id}' does not exist",
                                shield.shield_id)
                )
            if shield.coverage_percent < 0 or shield.coverage_percent > 100:
                issues.append(
                    self._issue("warning", "SHIELD_COVERAGE_INVALID",
                                f"Shield coverage {shield.coverage_percent}% is out of range [0, 100]",
                                shield.shield_id)
                )
        return issues

    # ── Phase 2: Covering overlap ────────────────────────────────

    def _check_covering_overlap(self, model: ElectricalProjectModel) -> List[ValidationIssue]:
        """Detect overlapping coverings on the same segment."""
        issues: List[ValidationIssue] = []
        by_segment: Dict[str, list] = {}
        for cov in model.coverings.values():
            by_segment.setdefault(cov.segment_id, []).append(cov)
            if cov.segment_id not in model.bundle_segments:
                issues.append(
                    self._issue("error", "COVERING_DANGLING_SEGMENT",
                                f"Covering references non-existent segment '{cov.segment_id}'",
                                cov.covering_id)
                )
            if cov.start_ratio >= cov.end_ratio:
                issues.append(
                    self._issue("error", "COVERING_INVALID_RANGE",
                                f"Covering start_ratio ({cov.start_ratio}) >= end_ratio ({cov.end_ratio})",
                                cov.covering_id)
                )
        for seg_id, covs in by_segment.items():
            sorted_covs = sorted(covs, key=lambda c: c.start_ratio)
            for i in range(len(sorted_covs) - 1):
                a = sorted_covs[i]
                b = sorted_covs[i + 1]
                if a.end_ratio > b.start_ratio:
                    issues.append(
                        self._issue("warning", "COVERING_OVERLAP",
                                    f"Coverings '{a.covering_id}' and '{b.covering_id}' overlap "
                                    f"on segment '{seg_id}'",
                                    a.covering_id)
                    )
        return issues

    # ── Phase 2: Cable integrity ─────────────────────────────────

    def _check_cable_integrity(self, model: ElectricalProjectModel) -> List[ValidationIssue]:
        """Cable conductor references must exist as wires."""
        issues: List[ValidationIssue] = []
        for cable in model.cables.values():
            if not cable.conductor_ids:
                issues.append(
                    self._issue("warning", "CABLE_EMPTY",
                                "Cable has no conductors", cable.cable_id)
                )
            for wid in cable.conductor_ids:
                if wid not in model.wires:
                    issues.append(
                        self._issue("error", "CABLE_DANGLING_WIRE",
                                    f"Cable references non-existent wire '{wid}'",
                                    cable.cable_id)
                    )
        return issues

    # ── Phase 2: Twisted pair validity ───────────────────────────

    def _check_twisted_pair_validity(self, model: ElectricalProjectModel) -> List[ValidationIssue]:
        """Twisted pair wire references must exist and be different."""
        issues: List[ValidationIssue] = []
        for tp in model.twisted_pairs.values():
            if tp.wire_id_a == tp.wire_id_b:
                issues.append(
                    self._issue("error", "TWISTED_PAIR_SAME_WIRE",
                                "Twisted pair references the same wire for both conductors",
                                tp.twisted_pair_id)
                )
            if tp.wire_id_a not in model.wires:
                issues.append(
                    self._issue("error", "TWISTED_PAIR_DANGLING",
                                f"Twisted pair wire_a '{tp.wire_id_a}' does not exist",
                                tp.twisted_pair_id)
                )
            if tp.wire_id_b not in model.wires:
                issues.append(
                    self._issue("error", "TWISTED_PAIR_DANGLING",
                                f"Twisted pair wire_b '{tp.wire_id_b}' does not exist",
                                tp.twisted_pair_id)
                )
            if tp.twist_pitch_mm <= 0:
                issues.append(
                    self._issue("warning", "TWISTED_PAIR_PITCH",
                                f"Twist pitch {tp.twist_pitch_mm}mm must be positive",
                                tp.twisted_pair_id)
                )
        return issues
