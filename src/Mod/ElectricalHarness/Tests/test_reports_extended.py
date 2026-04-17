"""Tests for expanded reports: wire list, BOM, spool, cut-list, summaries."""

import json
import unittest

from App.entities import (
    ConnectorInstance,
    NetSignal,
    PinCavity,
    Project,
    Splice,
    Wire,
)
from App.flattening import FlatteningEngine
from App.model import ElectricalProjectModel
from App.reports import ReportService


def _populated_model():
    model = ElectricalProjectModel(Project(project_id="P1", name="Harness"))
    model.add_connector(ConnectorInstance(
        connector_instance_id="J1", connector_definition_id="CONN-8", reference="J1",
    ))
    model.add_pin(PinCavity(pin_id="J1-1", connector_instance_id="J1", cavity_name="1"))
    model.add_pin(PinCavity(pin_id="J1-2", connector_instance_id="J1", cavity_name="2"))
    model.add_connector(ConnectorInstance(
        connector_instance_id="J2", connector_definition_id="CONN-4", reference="J2",
    ))
    model.add_pin(PinCavity(pin_id="J2-1", connector_instance_id="J2", cavity_name="1"))
    model.add_pin(PinCavity(pin_id="J2-2", connector_instance_id="J2", cavity_name="2"))
    model.add_net(NetSignal(net_id="N1", name="VBAT"))
    model.add_net(NetSignal(net_id="N2", name="GND"))
    model.add_wire(Wire(
        wire_id="W1", net_id="N1", from_pin_id="J1-1", to_pin_id="J2-1",
        gauge="22AWG", color="RD",
    ))
    model.add_wire(Wire(
        wire_id="W2", net_id="N2", from_pin_id="J1-2", to_pin_id="J2-2",
        gauge="22AWG", color="BK",
    ))
    model.add_splice(Splice(splice_id="SP1", member_pin_ids=["J1-1", "J2-1"], splice_type="inline"))
    return model


class TestConnectorTable(unittest.TestCase):
    def test_connector_table_has_pin_count(self):
        model = _populated_model()
        rows = ReportService().connector_table(model)
        self.assertEqual(len(rows), 2)
        j1_row = next(r for r in rows if r["connector_instance_id"] == "J1")
        self.assertEqual(j1_row["pin_count"], "2")

    def test_connector_table_has_placement(self):
        model = _populated_model()
        rows = ReportService().connector_table(model)
        for row in rows:
            self.assertIn("placement", row)


class TestFromToTable(unittest.TestCase):
    def test_from_to_includes_net_name(self):
        model = _populated_model()
        rows = ReportService().from_to_table(model)
        self.assertEqual(len(rows), 2)
        self.assertTrue(any(r["net_name"] == "VBAT" for r in rows))

    def test_from_to_includes_color(self):
        model = _populated_model()
        rows = ReportService().from_to_table(model)
        colors = {r["color"] for r in rows}
        self.assertEqual(colors, {"RD", "BK"})


class TestWireList(unittest.TestCase):
    def test_wire_list_shows_connector_refs(self):
        model = _populated_model()
        rows = ReportService().wire_list(model)
        self.assertEqual(len(rows), 2)
        self.assertTrue(any(r["from_connector"] == "J1" for r in rows))
        self.assertTrue(any(r["to_connector"] == "J2" for r in rows))


class TestBom(unittest.TestCase):
    def test_bom_has_connectors_and_wires(self):
        model = _populated_model()
        rows = ReportService().bom(model)
        categories = {r["category"] for r in rows}
        self.assertIn("Connector", categories)
        self.assertIn("Wire", categories)
        self.assertIn("Splice", categories)

    def test_bom_connector_quantity(self):
        model = _populated_model()
        rows = ReportService().bom(model)
        conn_rows = [r for r in rows if r["category"] == "Connector"]
        total_qty = sum(int(r["quantity"]) for r in conn_rows)
        self.assertEqual(total_qty, 2)


class TestSpoolConsumption(unittest.TestCase):
    def test_spool_has_gauge_groups(self):
        model = _populated_model()
        rows = ReportService().spool_consumption(model)
        self.assertGreaterEqual(len(rows), 1)
        for row in rows:
            self.assertIn("gauge", row)
            self.assertIn("total_length_mm", row)


class TestPinConnectionTable(unittest.TestCase):
    def test_pin_connection_shows_nets(self):
        model = _populated_model()
        rows = ReportService().pin_connection_table(model)
        self.assertEqual(len(rows), 4)  # 4 pins total
        connected = [r for r in rows if r["nets"] != "-"]
        self.assertGreaterEqual(len(connected), 2)


class TestProjectSummary(unittest.TestCase):
    def test_summary_counts(self):
        model = _populated_model()
        summary = ReportService().project_summary(model)
        self.assertEqual(summary["connector_count"], 2)
        self.assertEqual(summary["wire_count"], 2)
        self.assertEqual(summary["net_count"], 2)
        self.assertEqual(summary["splice_count"], 1)


class TestFlatteningTable(unittest.TestCase):
    def test_flattening_table_from_engine(self):
        model = _populated_model()
        flattened = FlatteningEngine().flatten(model)
        rows = ReportService().flattening_table(flattened)
        # No bundle segments in populated model, so empty
        self.assertEqual(len(rows), 0)


class TestWireCutList(unittest.TestCase):
    def test_wire_cut_list_entries(self):
        model = _populated_model()
        flattened = FlatteningEngine().flatten(model)
        rows = ReportService().wire_cut_list(flattened)
        # 2 wires → 2 entries
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertIn("cut_length_mm", row)
            self.assertIn("gauge", row)


class TestCsvJsonExport(unittest.TestCase):
    def test_csv_has_header(self):
        model = _populated_model()
        rows = ReportService().wire_list(model)
        csv_out = ReportService().to_csv(rows)
        lines = csv_out.strip().split("\n")
        self.assertGreaterEqual(len(lines), 2)  # header + data
        self.assertIn("wire_id", lines[0])

    def test_json_is_valid(self):
        model = _populated_model()
        rows = ReportService().bom(model)
        json_out = ReportService().to_json(rows)
        parsed = json.loads(json_out)
        self.assertIsInstance(parsed, list)
        self.assertGreater(len(parsed), 0)


if __name__ == "__main__":
    unittest.main()
