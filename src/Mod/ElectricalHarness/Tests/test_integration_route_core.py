"""Tests for Route Core integration adapter.

All tests are self-contained and use mock HTTP responses so they run
without a live Route Core server.
"""

from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock, patch

from App.integration_route_core import (
    RouteCoreAdapter,
    RouteCoreConfig,
    model_to_route_core,
    pull_parts_library,
    push_parts_library,
    route_core_to_model,
)
from App.library import ComponentLibrary
from App.entities import (
    ConnectorInstance, LibraryEntry, NetSignal, PinCavity, Project, Wire,
)
from App.model import ElectricalProjectModel


# ── Helpers ──────────────────────────────────────────────────────


def _make_model() -> ElectricalProjectModel:
    """Build a small but complete harness model for testing."""
    m = ElectricalProjectModel(Project(project_id="P1", name="Test"))
    m.add_connector(ConnectorInstance(
        connector_instance_id="J1", connector_definition_id="CONN-2P", reference="J1",
    ))
    m.add_pin(PinCavity(pin_id="J1-1", connector_instance_id="J1", cavity_name="1"))
    m.add_pin(PinCavity(pin_id="J1-2", connector_instance_id="J1", cavity_name="2"))
    m.add_connector(ConnectorInstance(
        connector_instance_id="J2", connector_definition_id="CONN-2P", reference="J2",
    ))
    m.add_pin(PinCavity(pin_id="J2-1", connector_instance_id="J2", cavity_name="1"))
    m.add_pin(PinCavity(pin_id="J2-2", connector_instance_id="J2", cavity_name="2"))
    m.add_net(NetSignal(net_id="N1", name="VCC", signal_type="power"))
    m.add_net(NetSignal(net_id="N2", name="GND", signal_type="ground"))
    m.add_wire(Wire(
        wire_id="W1", net_id="N1", from_pin_id="J1-1", to_pin_id="J2-1",
        gauge="18AWG", color="RED",
    ))
    m.add_wire(Wire(
        wire_id="W2", net_id="N2", from_pin_id="J1-2", to_pin_id="J2-2",
        gauge="18AWG", color="BLK",
    ))
    # Cable wrapping both wires
    m.create_cable("Power Cable", ["W1", "W2"], shield_type="braided", jacket_material="PVC")
    return m


def _make_rc_harness() -> dict:
    """Minimal Route Core harness payload for import tests."""
    return {
        "id": "test-harness",
        "name": "Test Harness",
        "version": 1,
        "nodes": [
            {
                "id": "n1",
                "componentId": "comp-2p",
                "component": {
                    "id": "comp-2p",
                    "name": "2-Pin Header",
                    "category": "connector",
                    "type": "inline",
                    "pins": [
                        {"id": "p1", "label": "1", "position": {"x": 0, "y": 0},
                         "direction": "right", "signalType": "power", "gender": "male"},
                        {"id": "p2", "label": "2", "position": {"x": 0, "y": 10},
                         "direction": "right", "signalType": "ground", "gender": "male"},
                    ],
                    "footprint": {"width": 30, "height": 20, "pinLayout": "single_row"},
                },
                "position": {"x": 0, "y": 0},
                "rotation": 0,
                "label": "J1",
                "locked": False,
            },
            {
                "id": "n2",
                "componentId": "comp-2p",
                "component": {
                    "id": "comp-2p",
                    "name": "2-Pin Header",
                    "category": "connector",
                    "type": "inline",
                    "pins": [
                        {"id": "p3", "label": "1", "position": {"x": 0, "y": 0},
                         "direction": "left", "signalType": "power", "gender": "female"},
                        {"id": "p4", "label": "2", "position": {"x": 0, "y": 10},
                         "direction": "left", "signalType": "ground", "gender": "female"},
                    ],
                    "footprint": {"width": 30, "height": 20, "pinLayout": "single_row"},
                },
                "position": {"x": 200, "y": 0},
                "rotation": 0,
                "label": "J2",
                "locked": False,
            },
        ],
        "connections": [
            {
                "id": "w1",
                "from": {"componentId": "n1", "pinId": "p1"},
                "to": {"componentId": "n2", "pinId": "p3"},
                "wireRef": "wire1",
                "signalLabel": "+12V",
                "colorCode": "RED",
            },
            {
                "id": "w2",
                "from": {"componentId": "n1", "pinId": "p2"},
                "to": {"componentId": "n2", "pinId": "p4"},
                "wireRef": "wire2",
                "signalLabel": "GND",
                "colorCode": "BLK",
            },
        ],
        "wires": [
            {"id": "wire1", "gauge": 18, "color": "RED", "material": "copper",
             "insulationType": "PVC", "currentRating": 7, "voltageRating": 600,
             "temperatureRating": 105},
            {"id": "wire2", "gauge": 18, "color": "BLK", "material": "copper",
             "insulationType": "PVC", "currentRating": 7, "voltageRating": 600,
             "temperatureRating": 105},
        ],
        "cables": [],
        "splices": [],
        "canvas": {},
    }


# ── Export tests ─────────────────────────────────────────────────


class TestModelToRouteCore(unittest.TestCase):
    def test_export_has_nodes_and_connections(self):
        m = _make_model()
        rc = model_to_route_core(m, "Test")
        self.assertEqual(len(rc["nodes"]), 2)
        self.assertEqual(len(rc["connections"]), 2)
        self.assertEqual(rc["name"], "Test")

    def test_export_cables(self):
        m = _make_model()
        rc = model_to_route_core(m)
        self.assertEqual(len(rc["cables"]), 1)
        cable = rc["cables"][0]
        self.assertEqual(len(cable["conductors"]), 2)
        self.assertIn("shielding", cable)

    def test_export_wire_specs(self):
        m = _make_model()
        rc = model_to_route_core(m)
        self.assertEqual(len(rc["wires"]), 2)
        self.assertEqual(rc["wires"][0]["gauge"], 18)

    def test_export_canvas_defaults(self):
        m = _make_model()
        rc = model_to_route_core(m)
        self.assertIn("canvas", rc)
        self.assertTrue(rc["canvas"]["showGrid"])

    def test_node_pins_match_model(self):
        m = _make_model()
        rc = model_to_route_core(m)
        total_pins = sum(len(n["component"]["pins"]) for n in rc["nodes"])
        self.assertEqual(total_pins, len(m.pins))


# ── Import tests ─────────────────────────────────────────────────


class TestRouteCoreToModel(unittest.TestCase):
    def test_import_connectors(self):
        rc = _make_rc_harness()
        m = route_core_to_model(rc)
        self.assertEqual(len(m.connectors), 2)

    def test_import_wires(self):
        rc = _make_rc_harness()
        m = route_core_to_model(rc)
        self.assertEqual(len(m.wires), 2)

    def test_import_nets(self):
        rc = _make_rc_harness()
        m = route_core_to_model(rc)
        net_names = {n.name for n in m.nets.values()}
        self.assertIn("+12V", net_names)
        self.assertIn("GND", net_names)

    def test_import_into_existing_model(self):
        existing = ElectricalProjectModel(Project(project_id="P2", name="Existing"))
        existing.add_connector_with_pins("X1", 1)
        rc = _make_rc_harness()
        m = route_core_to_model(rc, model=existing)
        self.assertEqual(len(m.connectors), 3)


# ── Round-trip tests ─────────────────────────────────────────────


class TestRoundTrip(unittest.TestCase):
    def test_export_import_preserves_structure(self):
        original = _make_model()
        rc = model_to_route_core(original, "Roundtrip")
        imported = route_core_to_model(rc)
        self.assertEqual(len(imported.connectors), len(original.connectors))
        self.assertEqual(len(imported.wires), len(original.wires))


# ── Parts library sync ───────────────────────────────────────────


class TestPartsSync(unittest.TestCase):
    @patch("App.integration_route_core._get")
    def test_pull_parts(self, mock_get):
        mock_get.return_value = [
            {
                "id": "molex-4pin",
                "name": "Molex 4-Pin",
                "manufacturer": "Molex",
                "part_number": "43045-0412",
                "category": "connector",
                "data": {"description": "4-pin power", "type": "panel_mount", "shape": "rectangular"},
            },
        ]
        lib = pull_parts_library(RouteCoreConfig())
        self.assertEqual(lib.size, 1)
        entry = lib.all_entries()[0]
        self.assertEqual(entry.entry_id, "rc-molex-4pin")
        self.assertEqual(entry.manufacturer, "Molex")
        self.assertEqual(entry.attributes["source"], "route_core")

    @patch("App.integration_route_core._post")
    def test_push_parts(self, mock_post):
        mock_post.return_value = {"id": "test"}
        lib = ComponentLibrary()
        lib.add_entry(LibraryEntry(
            entry_id="LOCAL-1", category="Connector", name="My Conn",
            manufacturer="Custom", is_generic=False,
        ))
        count = push_parts_library(RouteCoreConfig(), lib)
        self.assertEqual(count, 1)
        mock_post.assert_called_once()

    @patch("App.integration_route_core._post")
    def test_push_skips_rc_entries(self, mock_post):
        lib = ComponentLibrary()
        lib.add_entry(LibraryEntry(
            entry_id="RC-1", category="Connector", name="From RC",
            attributes={"rc_id": "existing-id", "source": "route_core"},
            is_generic=False,
        ))
        count = push_parts_library(RouteCoreConfig(), lib)
        self.assertEqual(count, 0)
        mock_post.assert_not_called()


# ── Adapter high-level tests ────────────────────────────────────


class TestRouteCoreAdapter(unittest.TestCase):
    @patch("App.integration_route_core._post")
    def test_push_harness(self, mock_post):
        mock_post.return_value = {"id": "harn-1"}
        adapter = RouteCoreAdapter(RouteCoreConfig())
        m = _make_model()
        hid = adapter.push_harness(m, "Test Push")
        self.assertEqual(hid, "harn-1")
        self.assertEqual(adapter.cfg.harness_id, "harn-1")

    @patch("App.integration_route_core._get")
    def test_pull_harness(self, mock_get):
        mock_get.return_value = {"data": _make_rc_harness()}
        adapter = RouteCoreAdapter(RouteCoreConfig(harness_id="h1"))
        m = adapter.pull_harness()
        self.assertEqual(len(m.connectors), 2)

    @patch("App.integration_route_core._post")
    def test_validate_remote(self, mock_post):
        mock_post.return_value = {
            "valid": False,
            "issues": [{"severity": "warning", "message": "Unconnected pin", "code": "UNCONNECTED_PIN"}],
        }
        adapter = RouteCoreAdapter(RouteCoreConfig())
        issues = adapter.validate_remote(_make_model())
        self.assertEqual(len(issues), 1)

    @patch("App.integration_route_core._get")
    def test_list_harnesses(self, mock_get):
        mock_get.return_value = [
            {"id": "h1", "name": "Harness 1"},
            {"id": "h2", "name": "Harness 2"},
        ]
        adapter = RouteCoreAdapter(RouteCoreConfig())
        result = adapter.list_harnesses()
        self.assertEqual(len(result), 2)

    @patch("App.integration_route_core._delete")
    def test_delete_harness(self, mock_delete):
        mock_delete.return_value = {}
        adapter = RouteCoreAdapter(RouteCoreConfig())
        self.assertTrue(adapter.delete_harness("h1"))


if __name__ == "__main__":
    unittest.main()
