"""Tests for Dolibarr ERP integration adapter.

All tests are self-contained and use mock HTTP responses so they run
without a live Dolibarr instance.
"""

from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock, call, patch

from App.integration_dolibarr import (
    DolibarrAdapter,
    DolibarrConfig,
    _product_ref,
    create_purchase_order,
    pull_supplier_pricing,
    push_bom,
    query_stock,
)
from App.entities import (
    ConnectorInstance, LibraryEntry, NetSignal, PinCavity, Project, Wire,
)
from App.library import ComponentLibrary
from App.model import ElectricalProjectModel


# ── Helpers ──────────────────────────────────────────────────────


def _make_model() -> ElectricalProjectModel:
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
    return m


# ── Product ref ──────────────────────────────────────────────────


class TestProductRef(unittest.TestCase):
    def test_basic(self):
        ref = _product_ref("Connector", "CONN-2P")
        self.assertTrue(ref.startswith("EH-"))
        self.assertIn("Connector", ref)

    def test_slash_replaced(self):
        ref = _product_ref("Wire", "18AWG/RED")
        self.assertNotIn("/", ref)

    def test_max_length(self):
        ref = _product_ref("Category", "A" * 100)
        self.assertLessEqual(len(ref), 48)


# ── BOM push ─────────────────────────────────────────────────────


class TestPushBom(unittest.TestCase):
    @patch("App.integration_dolibarr._post")
    @patch("App.integration_dolibarr._find_product")
    def test_push_creates_assembly_and_lines(self, mock_find, mock_post):
        # _find_product returns None (products don't exist yet)
        mock_find.return_value = None
        # _post returns sequential IDs
        mock_post.side_effect = [
            # product creates: CONN-2P, 18AWG-RED, 18AWG-BLK, assembly
            10, 11, 12, 20,
            # BOM create
            {"id": 100},
            # BOM lines (one per component)
            {"id": 1}, {"id": 2}, {"id": 3},
        ]

        cfg = DolibarrConfig(base_url="http://test", api_key="key")
        m = _make_model()
        result = push_bom(cfg, m, "Test Assembly")

        self.assertEqual(result["assembly_id"], 20)
        self.assertEqual(result["bom_id"], 100)
        self.assertGreater(result["line_count"], 0)

    @patch("App.integration_dolibarr._post")
    @patch("App.integration_dolibarr._find_product")
    def test_push_reuses_existing_products(self, mock_find, mock_post):
        mock_find.return_value = {"id": 99}  # all products already exist
        mock_post.side_effect = [
            {"id": 200},  # BOM create
            {"id": 1}, {"id": 2}, {"id": 3},  # BOM lines
        ]

        cfg = DolibarrConfig(base_url="http://test", api_key="key")
        result = push_bom(cfg, _make_model())

        self.assertEqual(result["assembly_id"], 99)
        self.assertEqual(result["bom_id"], 200)


# ── Stock query ──────────────────────────────────────────────────


class TestQueryStock(unittest.TestCase):
    @patch("App.integration_dolibarr._get")
    @patch("App.integration_dolibarr._find_product")
    def test_stock_with_shortage(self, mock_find, mock_get):
        mock_find.return_value = {"id": 10}
        mock_get.return_value = [{"qty": 1}]  # only 1 in stock

        cfg = DolibarrConfig(base_url="http://test", api_key="key")
        results = query_stock(cfg, _make_model())

        self.assertTrue(len(results) > 0)
        # connectors need 2 but only 1 in stock
        shortages = [r for r in results if r["shortage"] > 0]
        self.assertTrue(len(shortages) > 0)

    @patch("App.integration_dolibarr._get")
    @patch("App.integration_dolibarr._find_product")
    def test_stock_no_product_found(self, mock_find, mock_get):
        mock_find.return_value = None  # product doesn't exist in Dolibarr

        cfg = DolibarrConfig(base_url="http://test", api_key="key")
        results = query_stock(cfg, _make_model())

        for r in results:
            self.assertEqual(r["in_stock"], 0)
            self.assertGreater(r["shortage"], 0)


# ── Purchase order creation ──────────────────────────────────────


class TestCreatePurchaseOrder(unittest.TestCase):
    @patch("App.integration_dolibarr._post")
    @patch("App.integration_dolibarr._find_product")
    def test_creates_order_with_lines(self, mock_find, mock_post):
        mock_find.return_value = {"id": 10}
        mock_post.side_effect = [
            {"id": 500},  # order creation
            {"id": 1},    # line 1
        ]

        cfg = DolibarrConfig(base_url="http://test", api_key="key")
        shortages = [
            {"ref": "EH-Wire-18AWG-RED", "label": "Wire 18AWG/RED", "shortage": 5},
        ]
        order_id = create_purchase_order(cfg, supplier_id=99, shortages=shortages)
        self.assertEqual(order_id, 500)

    def test_no_shortages_returns_zero(self):
        cfg = DolibarrConfig(base_url="http://test", api_key="key")
        order_id = create_purchase_order(cfg, supplier_id=99, shortages=[])
        self.assertEqual(order_id, 0)

    def test_zero_shortage_items_skipped(self):
        cfg = DolibarrConfig(base_url="http://test", api_key="key")
        shortages = [{"ref": "X", "label": "X", "shortage": 0}]
        order_id = create_purchase_order(cfg, supplier_id=99, shortages=shortages)
        self.assertEqual(order_id, 0)


# ── Supplier pricing ────────────────────────────────────────────


class TestPullPricing(unittest.TestCase):
    @patch("App.integration_dolibarr._get")
    def test_enriches_library(self, mock_get):
        mock_get.return_value = [{"id": 42, "price": "12.50"}]
        lib = ComponentLibrary()
        lib.add_entry(LibraryEntry(
            entry_id="C1", category="Connector", name="2-Pin",
            part_number="43045-0412", is_generic=False,
        ))
        count = pull_supplier_pricing(DolibarrConfig(api_key="k"), lib)
        self.assertEqual(count, 1)
        entry = lib.get_entry("C1")
        self.assertEqual(entry.attributes["unit_price"], "12.50")
        self.assertEqual(entry.attributes["dolibarr_id"], "42")

    @patch("App.integration_dolibarr._get")
    def test_skips_entries_without_part_number(self, mock_get):
        lib = ComponentLibrary()
        lib.add_entry(LibraryEntry(
            entry_id="G1", category="Wire", name="Generic", is_generic=True,
        ))
        count = pull_supplier_pricing(DolibarrConfig(api_key="k"), lib)
        self.assertEqual(count, 0)
        mock_get.assert_not_called()


# ── Adapter high-level tests ────────────────────────────────────


class TestDolibarrAdapter(unittest.TestCase):
    @patch("App.integration_dolibarr._get")
    def test_test_connection_success(self, mock_get):
        mock_get.return_value = {"success": True}
        adapter = DolibarrAdapter(DolibarrConfig(api_key="valid"))
        self.assertTrue(adapter.test_connection())

    @patch("App.integration_dolibarr._get")
    def test_test_connection_failure(self, mock_get):
        from urllib.error import URLError
        mock_get.side_effect = URLError("Connection refused")
        adapter = DolibarrAdapter(DolibarrConfig(api_key="bad"))
        self.assertFalse(adapter.test_connection())

    @patch("App.integration_dolibarr._get")
    def test_list_suppliers(self, mock_get):
        mock_get.return_value = [
            {"id": 1, "name": "Molex", "fournisseur": 1},
            {"id": 2, "name": "TE Connectivity", "fournisseur": 1},
        ]
        adapter = DolibarrAdapter(DolibarrConfig(api_key="k"))
        suppliers = adapter.list_suppliers()
        self.assertEqual(len(suppliers), 2)


if __name__ == "__main__":
    unittest.main()
