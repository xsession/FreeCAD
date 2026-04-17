"""Report generation services for engineering and manufacturing outputs.

Provides connector tables, from-to lists, wire lists, BOM (with coverings,
clips, cables), spool consumption, strip lengths, and formboard/flattening
tables with CSV, JSON, and (future) Excel export.
"""

from __future__ import annotations

import csv
import io
import json
from collections import Counter, defaultdict
from dataclasses import asdict
from typing import Dict, Iterable, List

from .flattening import FlattenedHarness, FlatteningEngine
from .model import ElectricalProjectModel


class ReportService:

    # ── Connector table ──────────────────────────────────────────

    def connector_table(self, model: ElectricalProjectModel) -> List[Dict[str, str]]:
        rows: List[Dict[str, str]] = []
        for connector in model.connectors.values():
            pin_count = len(model.connector_pin_ids(connector.connector_instance_id))
            rows.append({
                "connector_instance_id": connector.connector_instance_id,
                "reference": connector.reference,
                "connector_definition_id": connector.connector_definition_id,
                "pin_count": str(pin_count),
                "placement": connector.placement_path or "-",
            })
        return rows

    # ── Pin connection table ─────────────────────────────────────

    def pin_connection_table(self, model: ElectricalProjectModel) -> List[Dict[str, str]]:
        rows: List[Dict[str, str]] = []
        for pin in model.pins.values():
            nets = model.nets_touching_pin(pin.pin_id)
            net_names = ", ".join(
                model.nets[nid].name for nid in nets if nid in model.nets
            ) or "-"
            rows.append({
                "pin_id": pin.pin_id,
                "connector_instance_id": pin.connector_instance_id,
                "cavity_name": pin.cavity_name,
                "nets": net_names,
            })
        return rows

    # ── From-to table ────────────────────────────────────────────

    def from_to_table(self, model: ElectricalProjectModel) -> List[Dict[str, str]]:
        rows: List[Dict[str, str]] = []
        for wire in model.wires.values():
            net_name = model.nets.get(wire.net_id)
            rows.append({
                "wire_id": wire.wire_id,
                "wire_number": wire.wire_number or "-",
                "net_id": wire.net_id,
                "net_name": net_name.name if net_name else "-",
                "from_pin_id": wire.from_pin_id,
                "to_pin_id": wire.to_pin_id,
                "gauge": wire.gauge,
                "color": wire.color,
                "cable_id": wire.cable_id or "-",
            })
        return rows

    # ── Wire list ────────────────────────────────────────────────

    def wire_list(self, model: ElectricalProjectModel) -> List[Dict[str, str]]:
        rows: List[Dict[str, str]] = []
        for wire in model.wires.values():
            net = model.nets.get(wire.net_id)
            from_pin = model.pins.get(wire.from_pin_id)
            to_pin = model.pins.get(wire.to_pin_id)
            shields = model.shields_for_wire(wire.wire_id)
            rows.append({
                "wire_id": wire.wire_id,
                "wire_number": wire.wire_number or "-",
                "net_name": net.name if net else "-",
                "from_connector": from_pin.connector_instance_id if from_pin else "-",
                "from_cavity": from_pin.cavity_name if from_pin else "-",
                "to_connector": to_pin.connector_instance_id if to_pin else "-",
                "to_cavity": to_pin.cavity_name if to_pin else "-",
                "gauge": wire.gauge,
                "color": wire.color,
                "cable_id": wire.cable_id or "-",
                "shield_ids": ", ".join(s.shield_id for s in shields) or "-",
                "strip_length_mm": f"{wire.strip_length_mm:.1f}" if wire.strip_length_mm else "-",
            })
        return rows

    # ── BOM ──────────────────────────────────────────────────────

    def bom(self, model: ElectricalProjectModel) -> List[Dict[str, str]]:
        """Bill of materials: connectors, wires, splices, coverings, clips, cables."""
        rows: List[Dict[str, str]] = []
        item_num = 1

        # Connectors
        conn_counts: Counter = Counter()
        for conn in model.connectors.values():
            conn_counts[conn.connector_definition_id] += 1
        for defn_id, qty in conn_counts.most_common():
            rows.append({
                "item": str(item_num),
                "category": "Connector",
                "part_id": defn_id,
                "description": defn_id,
                "quantity": str(qty),
                "unit": "EA",
            })
            item_num += 1

        # Wires grouped by gauge+color
        wire_groups: Dict[str, int] = defaultdict(int)
        for wire in model.wires.values():
            key = f"{wire.gauge}/{wire.color}"
            wire_groups[key] += 1
        for key, qty in sorted(wire_groups.items()):
            rows.append({
                "item": str(item_num),
                "category": "Wire",
                "part_id": key,
                "description": f"Wire {key}",
                "quantity": str(qty),
                "unit": "EA",
            })
            item_num += 1

        # Splices
        splice_counts: Counter = Counter()
        for splice in model.splices.values():
            splice_counts[splice.splice_type] += 1
        for stype, qty in splice_counts.most_common():
            rows.append({
                "item": str(item_num),
                "category": "Splice",
                "part_id": stype,
                "description": f"Splice ({stype})",
                "quantity": str(qty),
                "unit": "EA",
            })
            item_num += 1

        # Coverings
        covering_groups: Dict[str, int] = defaultdict(int)
        for cov in model.coverings.values():
            key = f"{cov.material}/{cov.covering_type}"
            covering_groups[key] += 1
        for key, qty in sorted(covering_groups.items()):
            rows.append({
                "item": str(item_num),
                "category": "Covering",
                "part_id": key,
                "description": f"Covering {key}",
                "quantity": str(qty),
                "unit": "EA",
            })
            item_num += 1

        # Clips
        clip_counts: Counter = Counter()
        for clip in model.clips.values():
            clip_counts[clip.support_type] += 1
        for ctype, qty in clip_counts.most_common():
            rows.append({
                "item": str(item_num),
                "category": "Clip",
                "part_id": ctype,
                "description": f"Clip ({ctype})",
                "quantity": str(qty),
                "unit": "EA",
            })
            item_num += 1

        # Cables
        for cable in model.cables.values():
            rows.append({
                "item": str(item_num),
                "category": "Cable",
                "part_id": cable.cable_id,
                "description": cable.display_name,
                "quantity": "1",
                "unit": "EA",
            })
            item_num += 1

        return rows

    # ── Spool consumption ────────────────────────────────────────

    def spool_consumption(self, model: ElectricalProjectModel) -> List[Dict[str, str]]:
        """Wire spool consumption summary grouped by gauge and color."""
        spool: Dict[str, float] = defaultdict(float)
        # Use flattening engine for length data
        flattened = FlatteningEngine().flatten(model)
        for entry in flattened.wire_lengths:
            key = f"{entry.gauge}/{entry.color}"
            spool[key] += entry.cut_length_mm

        rows: List[Dict[str, str]] = []
        for key in sorted(spool.keys()):
            gauge, color = key.split("/", 1)
            rows.append({
                "gauge": gauge,
                "color": color,
                "total_length_mm": f"{spool[key]:.1f}",
                "total_length_m": f"{spool[key] / 1000.0:.2f}",
            })
        return rows

    # ── Flattening / formboard table ─────────────────────────────

    def flattening_table(self, flattened: FlattenedHarness) -> List[Dict[str, object]]:
        rows: List[Dict[str, object]] = []
        for seg in flattened.segments:
            rows.append({
                "source_segment_id": seg.source_segment_id,
                "branch_order": seg.branch_order,
                "flattened_length_mm": seg.flattened_length_mm,
                "from_node": seg.from_node_id,
                "to_node": seg.to_node_id,
                "wire_count": len(seg.wire_ids),
                "covering_count": len(seg.covering_ids),
            })
        return rows

    # ── Wire length cut-list ─────────────────────────────────────

    def wire_cut_list(self, flattened: FlattenedHarness) -> List[Dict[str, str]]:
        rows: List[Dict[str, str]] = []
        for entry in flattened.wire_lengths:
            rows.append({
                "wire_id": entry.wire_id,
                "net_id": entry.net_id,
                "gauge": entry.gauge,
                "color": entry.color,
                "cut_length_mm": f"{entry.cut_length_mm:.1f}",
                "segment_count": str(len(entry.segment_ids)),
            })
        return rows

    # ── Cable summary ────────────────────────────────────────────

    def cable_summary(self, model: ElectricalProjectModel) -> List[Dict[str, str]]:
        rows: List[Dict[str, str]] = []
        for cable in model.cables.values():
            wires = model.wires_in_cable(cable.cable_id)
            rows.append({
                "cable_id": cable.cable_id,
                "display_name": cable.display_name,
                "conductor_count": str(len(cable.conductor_ids)),
                "shield_type": cable.shield_type or "-",
                "jacket_material": cable.jacket_material or "-",
                "outer_diameter_mm": f"{cable.outer_diameter_mm:.1f}" if cable.outer_diameter_mm else "-",
                "wire_gauges": ", ".join(sorted({w.gauge for w in wires})) or "-",
            })
        return rows

    # ── Shield summary ───────────────────────────────────────────

    def shield_summary(self, model: ElectricalProjectModel) -> List[Dict[str, str]]:
        rows: List[Dict[str, str]] = []
        for shield in model.shields.values():
            rows.append({
                "shield_id": shield.shield_id,
                "display_name": shield.display_name,
                "shield_type": shield.shield_type,
                "coverage_percent": f"{shield.coverage_percent:.0f}",
                "member_count": str(len(shield.member_wire_ids)),
                "drain_wire": shield.drain_wire_id or "-",
            })
        return rows

    # ── Covering summary ─────────────────────────────────────────

    def covering_summary(self, model: ElectricalProjectModel) -> List[Dict[str, str]]:
        rows: List[Dict[str, str]] = []
        for cov in model.coverings.values():
            seg = model.bundle_segments.get(cov.segment_id)
            rows.append({
                "covering_id": cov.covering_id,
                "segment_id": cov.segment_id,
                "material": cov.material,
                "covering_type": cov.covering_type,
                "start_ratio": f"{cov.start_ratio:.2f}",
                "end_ratio": f"{cov.end_ratio:.2f}",
                "segment_exists": "yes" if seg else "no",
            })
        return rows

    # ── Project summary / health ─────────────────────────────────

    def project_summary(self, model: ElectricalProjectModel) -> Dict[str, object]:
        return {
            "project_id": model.project.project_id,
            "project_name": model.project.name,
            "connector_count": len(model.connectors),
            "pin_count": len(model.pins),
            "net_count": len(model.nets),
            "wire_count": len(model.wires),
            "splice_count": len(model.splices),
            "bundle_segment_count": len(model.bundle_segments),
            "locked_segment_count": len(model.locked_route_segments),
            "cable_count": len(model.cables),
            "shield_count": len(model.shields),
            "twisted_pair_count": len(model.twisted_pairs),
            "covering_count": len(model.coverings),
            "clip_count": len(model.clips),
        }

    # ── Export helpers ────────────────────────────────────────────

    def to_csv(self, rows: Iterable[Dict[str, object]]) -> str:
        row_list = list(rows)
        if not row_list:
            return ""
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=list(row_list[0].keys()))
        writer.writeheader()
        writer.writerows(row_list)
        return buffer.getvalue()

    def to_json(self, rows: Iterable[Dict[str, object]]) -> str:
        return json.dumps(list(rows), indent=2, sort_keys=True)
