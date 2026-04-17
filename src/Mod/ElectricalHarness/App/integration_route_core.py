"""Route Core integration adapter.

Bidirectional sync between the ElectricalHarness model and a Route Core
server (REST API).  Supports:

  * Push harness → Route Core (connectors, wires, cables, validation)
  * Pull Route Core harness → ElectricalHarness model
  * Part library synchronisation
  * BOM / export proxying
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .entities import (
    Cable,
    ConnectorDefinition,
    ConnectorInstance,
    Covering,
    LibraryEntry,
    NetSignal,
    PinCavity,
    Project,
    ShieldedGroup,
    Splice,
    Wire,
)
from .library import ComponentLibrary
from .model import ElectricalProjectModel
from .reports import ReportService

log = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────


@dataclass
class RouteCoreConfig:
    base_url: str = "http://localhost:3000"
    timeout_s: int = 30
    harness_id: str = ""


# ── Low-level HTTP helpers ───────────────────────────────────────


def _request(
    method: str,
    url: str,
    *,
    body: Optional[dict] = None,
    timeout: int = 30,
) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    return json.loads(raw) if raw else {}


def _get(url: str, timeout: int = 30) -> Any:
    return _request("GET", url, timeout=timeout)


def _post(url: str, body: dict, timeout: int = 30) -> Any:
    return _request("POST", url, body=body, timeout=timeout)


def _put(url: str, body: dict, timeout: int = 30) -> Any:
    return _request("PUT", url, body=body, timeout=timeout)


def _delete(url: str, timeout: int = 30) -> Any:
    return _request("DELETE", url, timeout=timeout)


# ── Data-mapping helpers ─────────────────────────────────────────


_SIGNAL_MAP = {
    "power": "power",
    "signal": "signal",
    "ground": "ground",
    "data": "data",
    "analog": "analog",
    "digital": "digital",
}


def _map_signal(sig_type: str) -> str:
    return _SIGNAL_MAP.get(sig_type, "signal")


_AWG_CURRENT = {
    "30": 0.5, "28": 0.7, "26": 1.0, "24": 2.0, "22": 3.0,
    "20": 5.0, "18": 7.0, "16": 10.0, "14": 15.0, "12": 20.0,
    "10": 30.0, "8": 40.0, "6": 55.0, "4": 70.0,
}


def _gauge_to_current(gauge: str) -> float:
    return _AWG_CURRENT.get(gauge.replace("AWG", "").strip(), 5.0)


# ── Export: ElectricalHarness → Route Core ───────────────────────


def model_to_route_core(
    model: ElectricalProjectModel,
    harness_name: str = "FreeCAD Harness",
) -> dict:
    """Convert an ElectricalProjectModel to a Route Core Harness payload."""
    nodes: List[dict] = []
    connections: List[dict] = []
    rc_cables: List[dict] = []
    rc_wires: List[dict] = []
    splice_points: List[dict] = []

    # Connectors → HarnessNodes
    x_offset = 0
    for conn in model.connectors.values():
        pins = []
        pin_ids = model.connector_pin_ids(conn.connector_instance_id)
        for idx, pid in enumerate(pin_ids):
            pin = model.pins.get(pid)
            if not pin:
                continue
            nets = model.nets_touching_pin(pid)
            sig = "signal"
            for nid in nets:
                net = model.nets.get(nid)
                if net:
                    sig = _map_signal(net.signal_type)
                    break
            pins.append({
                "id": pid,
                "label": pin.cavity_name,
                "position": {"x": 0, "y": idx * 10},
                "direction": "right",
                "signalType": sig,
                "gender": "female",
            })

        component = {
            "id": conn.connector_definition_id,
            "name": conn.reference,
            "manufacturer": "",
            "partNumber": "",
            "category": "connector",
            "type": "inline",
            "shape": "rectangular",
            "pins": pins,
            "footprint": {
                "width": 30,
                "height": max(20, len(pins) * 10),
                "pinLayout": "single_row",
            },
            "description": conn.connector_definition_id,
            "tags": ["freecad-import"],
            "custom": True,
        }

        nodes.append({
            "id": conn.connector_instance_id,
            "componentId": conn.connector_definition_id,
            "component": component,
            "position": {"x": x_offset, "y": 0},
            "rotation": 0,
            "label": conn.reference,
            "locked": False,
        })
        x_offset += 200

    # Wires → Connections + Wire specs
    for wire in model.wires.values():
        from_pin = model.pins.get(wire.from_pin_id)
        to_pin = model.pins.get(wire.to_pin_id)
        if not from_pin or not to_pin:
            continue
        net = model.nets.get(wire.net_id)

        connections.append({
            "id": wire.wire_id,
            "from": {
                "componentId": from_pin.connector_instance_id,
                "pinId": wire.from_pin_id,
            },
            "to": {
                "componentId": to_pin.connector_instance_id,
                "pinId": wire.to_pin_id,
            },
            "wireRef": wire.wire_id,
            "cableRef": wire.cable_id or None,
            "signalLabel": net.name if net else "",
            "colorCode": wire.color,
        })

        gauge_num = wire.gauge.replace("AWG", "").strip()
        rc_wires.append({
            "id": wire.wire_id,
            "gauge": int(gauge_num) if gauge_num.isdigit() else 18,
            "color": wire.color,
            "material": "copper",
            "insulationType": "PVC",
            "currentRating": _gauge_to_current(wire.gauge),
            "voltageRating": 600,
            "temperatureRating": 105,
        })

    # Cables → RC Cables
    for cable in model.cables.values():
        conductors = []
        for idx, wid in enumerate(cable.conductor_ids):
            w = model.wires.get(wid)
            if not w:
                continue
            gauge_num = w.gauge.replace("AWG", "").strip()
            conductors.append({
                "position": idx,
                "wire": {
                    "id": wid,
                    "gauge": int(gauge_num) if gauge_num.isdigit() else 18,
                    "color": w.color,
                    "material": "copper",
                    "insulationType": "PVC",
                    "currentRating": _gauge_to_current(w.gauge),
                    "voltageRating": 600,
                    "temperatureRating": 105,
                },
            })

        shielding = None
        # Check ShieldedGroup entities first
        for shield in model.shields.values():
            if shield.cable_id == cable.cable_id:
                shielding = {
                    "type": shield.shield_type if shield.shield_type in (
                        "braid", "foil", "spiral", "combination",
                    ) else "braid",
                    "coverage": shield.coverage_percent,
                    "material": "tinned copper",
                    "drainWire": bool(shield.drain_wire_id),
                }
                break
        # Fallback: use cable.shield_type if no ShieldedGroup exists
        if not shielding and cable.shield_type:
            shielding = {
                "type": cable.shield_type if cable.shield_type in (
                    "braid", "foil", "spiral", "combination",
                ) else "braid",
                "coverage": 85.0,
                "material": "tinned copper",
                "drainWire": False,
            }

        rc_cable: dict = {
            "id": cable.cable_id,
            "name": cable.display_name,
            "conductors": conductors,
            "jacket": {
                "material": cable.jacket_material or "PVC",
                "color": "black",
                "outerDiameter": cable.outer_diameter_mm or 8.0,
            },
            "outerDiameter": cable.outer_diameter_mm or 8.0,
            "bendRadius": 40.0,
            "weightPerMeter": 50.0,
            "temperatureRange": {"min": -20, "max": 105},
            "description": cable.display_name,
            "custom": True,
        }
        if shielding:
            rc_cable["shielding"] = shielding
        rc_cables.append(rc_cable)

    # Splices → SplicePoints
    for splice in model.splices.values():
        method_map = {
            "inline": "butt_splice", "solder": "solder",
            "crimp": "crimp", "ultrasonic": "butt_splice",
        }
        splice_points.append({
            "id": splice.splice_id,
            "position": {"x": 400, "y": 200},
            "connectionIds": [],
            "method": method_map.get(splice.splice_type, "butt_splice"),
            "label": splice.splice_id,
        })

    return {
        "id": harness_name.lower().replace(" ", "-"),
        "name": harness_name,
        "description": f"Exported from FreeCAD ElectricalHarness",
        "version": 1,
        "author": "FreeCAD",
        "nodes": nodes,
        "connections": connections,
        "splices": splice_points,
        "cables": rc_cables,
        "wires": rc_wires,
        "canvas": {
            "width": 2000,
            "height": 1200,
            "zoom": 1.0,
            "panX": 0,
            "panY": 0,
            "gridSize": 10,
            "snapToGrid": True,
            "showGrid": True,
            "showLabels": True,
            "showPinNumbers": True,
            "showWireInfo": True,
            "wireUnits": "awg",
            "lengthUnits": "metric",
        },
        "revisions": [],
        "createdAt": "",
        "updatedAt": "",
    }


# ── Import: Route Core → ElectricalHarness ──────────────────────


def route_core_to_model(
    rc_harness: dict,
    model: Optional[ElectricalProjectModel] = None,
) -> ElectricalProjectModel:
    """Populate an ElectricalProjectModel from a Route Core Harness payload."""
    if model is None:
        name = rc_harness.get("name", "Imported Harness")
        model = ElectricalProjectModel(
            Project(project_id=rc_harness.get("id", "imported"), name=name)
        )

    node_map: Dict[str, str] = {}  # RC node id → connector_instance_id

    # Import nodes as connectors
    for node in rc_harness.get("nodes", []):
        comp = node.get("component", {})
        pins = comp.get("pins", [])
        cid = model.add_connector_with_pins(
            reference=node.get("label", node["id"]),
            pin_count=len(pins),
            connector_definition_id=comp.get("id", node["id"]),
        )
        node_map[node["id"]] = cid.connector_instance_id

        # Rename cavity labels to match RC pin labels
        eh_pins = model.connector_pin_ids(cid.connector_instance_id)
        for eh_pid, rc_pin in zip(eh_pins, pins):
            pin = model.pins.get(eh_pid)
            if pin:
                pin.cavity_name = rc_pin.get("label", pin.cavity_name)

    # Import connections as wires
    for conn in rc_harness.get("connections", []):
        from_ep = conn.get("from", {})
        to_ep = conn.get("to", {})
        from_conn_id = node_map.get(from_ep.get("componentId", ""))
        to_conn_id = node_map.get(to_ep.get("componentId", ""))
        if not from_conn_id or not to_conn_id:
            continue

        from_pins = model.connector_pin_ids(from_conn_id)
        to_pins = model.connector_pin_ids(to_conn_id)

        from_pin_id = _find_pin_by_label(
            model, from_pins, from_ep.get("pinId", ""),
        )
        to_pin_id = _find_pin_by_label(
            model, to_pins, to_ep.get("pinId", ""),
        )
        if not from_pin_id or not to_pin_id:
            from_pin_id = from_pins[0] if from_pins else None
            to_pin_id = to_pins[0] if to_pins else None
        if not from_pin_id or not to_pin_id:
            continue

        # Determine wire properties from RC wire spec
        wire_spec = _find_wire_spec(rc_harness, conn.get("wireRef", ""))
        gauge = str(wire_spec.get("gauge", 18)) + "AWG" if wire_spec else "18AWG"
        color = wire_spec.get("color", conn.get("colorCode", "")) if wire_spec else "BLK"
        signal_label = conn.get("signalLabel", "NET")

        model.connect_pins(
            from_pin_id=from_pin_id,
            to_pin_id=to_pin_id,
            net_name=signal_label,
            gauge=gauge,
            color=color or "BLK",
        )

    # Import cables
    for rc_cable in rc_harness.get("cables", []):
        conductor_wire_ids: List[str] = []
        for cond in rc_cable.get("conductors", []):
            rc_wire = cond.get("wire", {})
            wire_id = rc_wire.get("id", "")
            if wire_id and wire_id in model.wires:
                conductor_wire_ids.append(wire_id)

        if conductor_wire_ids:
            shield_type = ""
            jacket = rc_cable.get("jacket", {})
            shielding = rc_cable.get("shielding")
            if shielding:
                shield_type = shielding.get("type", "braid")

            model.create_cable(
                display_name=rc_cable.get("name", rc_cable["id"]),
                wire_ids=conductor_wire_ids,
                shield_type=shield_type,
                jacket_material=jacket.get("material", ""),
            )

    return model


def _find_pin_by_label(
    model: ElectricalProjectModel, pin_ids: List[str], target_id: str,
) -> Optional[str]:
    for pid in pin_ids:
        pin = model.pins.get(pid)
        if pin and (pid == target_id or pin.cavity_name == target_id):
            return pid
    return None


def _find_wire_spec(rc_harness: dict, wire_ref: str) -> Optional[dict]:
    if not wire_ref:
        return None
    for w in rc_harness.get("wires", []):
        if w.get("id") == wire_ref:
            return w
    return None


# ── Parts library sync ───────────────────────────────────────────


def pull_parts_library(
    cfg: RouteCoreConfig,
    library: Optional[ComponentLibrary] = None,
) -> ComponentLibrary:
    """Pull the Route Core parts catalog into a ComponentLibrary."""
    if library is None:
        library = ComponentLibrary()

    url = f"{cfg.base_url}/api/parts"
    try:
        parts = _get(url, timeout=cfg.timeout_s)
    except (urllib.error.URLError, OSError) as exc:
        log.warning("Failed to fetch Route Core parts: %s", exc)
        return library

    if not isinstance(parts, list):
        return library

    for part in parts:
        data = part.get("data", {})
        entry = LibraryEntry(
            entry_id=f"rc-{part.get('id', '')}",
            category=part.get("category", "Connector").capitalize(),
            name=part.get("name", ""),
            manufacturer=part.get("manufacturer", ""),
            part_number=part.get("part_number", ""),
            description=data.get("description", ""),
            is_generic=False,
            attributes={
                "source": "route_core",
                "rc_id": part.get("id", ""),
                "type": data.get("type", ""),
                "shape": data.get("shape", ""),
            },
        )
        library.add_entry(entry)

    return library


def push_parts_library(
    cfg: RouteCoreConfig,
    library: ComponentLibrary,
) -> int:
    """Push ComponentLibrary entries to Route Core as custom parts.

    Returns the number of parts successfully pushed.
    """
    count = 0
    for entry in library.all_entries():
        rc_id = entry.attributes.get("rc_id", "")
        if rc_id:
            continue  # already from Route Core

        payload = {
            "id": entry.entry_id,
            "name": entry.name,
            "manufacturer": entry.manufacturer,
            "part_number": entry.part_number,
            "category": entry.category.lower(),
            "type": "inline",
            "data": {
                "id": entry.entry_id,
                "name": entry.name,
                "manufacturer": entry.manufacturer,
                "partNumber": entry.part_number,
                "category": entry.category.lower(),
                "type": "inline",
                "shape": "rectangular",
                "pins": [],
                "footprint": {"width": 30, "height": 20, "pinLayout": "single_row"},
                "description": entry.description,
                "tags": ["freecad-library"],
                "custom": True,
            },
            "custom": True,
        }
        try:
            _post(f"{cfg.base_url}/api/parts", payload, timeout=cfg.timeout_s)
            count += 1
        except (urllib.error.URLError, OSError) as exc:
            log.warning("Failed to push part %s: %s", entry.entry_id, exc)
    return count


# ── High-level sync façade ───────────────────────────────────────


class RouteCoreAdapter:
    """High-level adapter for Route Core integration."""

    def __init__(self, cfg: RouteCoreConfig):
        self.cfg = cfg
        self._report = ReportService()

    # ── push ─────────────────────────────────────────────────────

    def push_harness(
        self,
        model: ElectricalProjectModel,
        harness_name: str = "FreeCAD Harness",
    ) -> str:
        """Export model to Route Core. Returns the RC harness id."""
        payload = model_to_route_core(model, harness_name=harness_name)
        harness_id = payload["id"]

        wrapper = {
            "id": harness_id,
            "name": harness_name,
            "description": payload.get("description", ""),
            "data": payload,
        }

        url = f"{self.cfg.base_url}/api/harnesses"
        if self.cfg.harness_id:
            _put(f"{url}/{self.cfg.harness_id}", wrapper, timeout=self.cfg.timeout_s)
            return self.cfg.harness_id

        result = _post(url, wrapper, timeout=self.cfg.timeout_s)
        created_id = result.get("id", harness_id) if isinstance(result, dict) else harness_id
        self.cfg.harness_id = str(created_id)
        return self.cfg.harness_id

    # ── pull ─────────────────────────────────────────────────────

    def pull_harness(
        self,
        harness_id: Optional[str] = None,
        model: Optional[ElectricalProjectModel] = None,
    ) -> ElectricalProjectModel:
        """Pull a Route Core harness into an ElectricalProjectModel."""
        hid = harness_id or self.cfg.harness_id
        if not hid:
            raise ValueError("No harness_id specified")

        url = f"{self.cfg.base_url}/api/harnesses/{hid}"
        resp = _get(url, timeout=self.cfg.timeout_s)
        rc_harness = resp.get("data", resp) if isinstance(resp, dict) else resp
        return route_core_to_model(rc_harness, model=model)

    # ── validate via RC ──────────────────────────────────────────

    def validate_remote(self, model: ElectricalProjectModel) -> List[dict]:
        """Run Route Core validation and return issues."""
        payload = model_to_route_core(model)
        url = f"{self.cfg.base_url}/api/export/validate"
        resp = _post(url, payload, timeout=self.cfg.timeout_s)
        return resp.get("issues", []) if isinstance(resp, dict) else []

    # ── BOM proxy ────────────────────────────────────────────────

    def push_bom(self, model: ElectricalProjectModel) -> dict:
        """Generate BOM locally and push to Route Core for enrichment."""
        payload = model_to_route_core(model)
        url = f"{self.cfg.base_url}/api/export/bom"
        return _post(url, payload, timeout=self.cfg.timeout_s)

    # ── parts ────────────────────────────────────────────────────

    def pull_parts(self, library: Optional[ComponentLibrary] = None) -> ComponentLibrary:
        return pull_parts_library(self.cfg, library=library)

    def push_parts(self, library: ComponentLibrary) -> int:
        return push_parts_library(self.cfg, library)

    # ── list harnesses ───────────────────────────────────────────

    def list_harnesses(self) -> List[dict]:
        url = f"{self.cfg.base_url}/api/harnesses"
        resp = _get(url, timeout=self.cfg.timeout_s)
        return resp if isinstance(resp, list) else []

    # ── delete ───────────────────────────────────────────────────

    def delete_harness(self, harness_id: str) -> bool:
        url = f"{self.cfg.base_url}/api/harnesses/{harness_id}"
        try:
            _delete(url, timeout=self.cfg.timeout_s)
            return True
        except (urllib.error.URLError, OSError):
            return False
