"""Tests for the topology-preserving flattening engine."""

import unittest

from App.entities import (
    BundleSegment,
    ConnectorInstance,
    NetSignal,
    PinCavity,
    Project,
    Wire,
)
from App.flattening import FlatteningEngine
from App.model import ElectricalProjectModel


def _routed_model():
    """Model with 2 connectors, 1 wire, and 3 bundle segments forming a tree."""
    model = ElectricalProjectModel(Project(project_id="P1", name="Harness"))
    model.add_connector(ConnectorInstance(
        connector_instance_id="J1", connector_definition_id="CONN-2", reference="J1",
    ))
    model.add_pin(PinCavity(pin_id="J1-1", connector_instance_id="J1", cavity_name="1"))
    model.add_connector(ConnectorInstance(
        connector_instance_id="J2", connector_definition_id="CONN-2", reference="J2",
    ))
    model.add_pin(PinCavity(pin_id="J2-1", connector_instance_id="J2", cavity_name="1"))
    model.add_net(NetSignal(net_id="N1", name="VBAT"))
    model.add_wire(Wire(
        wire_id="W1", net_id="N1", from_pin_id="J1-1", to_pin_id="J2-1",
        gauge="22AWG", color="RD",
    ))
    model.add_bundle_segment(BundleSegment(
        segment_id="S1", bundle_id="B1", from_node_id="A", to_node_id="B",
        nominal_diameter_mm=8.0,
    ))
    model.add_bundle_segment(BundleSegment(
        segment_id="S2", bundle_id="B1", from_node_id="B", to_node_id="C",
        nominal_diameter_mm=6.0,
    ))
    model.add_bundle_segment(BundleSegment(
        segment_id="S3", bundle_id="B1", from_node_id="B", to_node_id="D",
        nominal_diameter_mm=4.0,
    ))
    return model


class TestFlatteningEngine(unittest.TestCase):
    def test_empty_model_no_segments(self):
        model = ElectricalProjectModel(Project(project_id="P1", name="H"))
        result = FlatteningEngine().flatten(model)
        self.assertEqual(len(result.segments), 0)
        self.assertEqual(result.total_harness_length_mm, 0.0)

    def test_bfs_orders_all_segments(self):
        model = _routed_model()
        result = FlatteningEngine().flatten(model)
        self.assertEqual(len(result.segments), 3)
        ids = {seg.source_segment_id for seg in result.segments}
        self.assertEqual(ids, {"S1", "S2", "S3"})

    def test_branch_order_is_sequential(self):
        model = _routed_model()
        result = FlatteningEngine().flatten(model)
        orders = [seg.branch_order for seg in result.segments]
        self.assertEqual(orders, sorted(orders))
        self.assertEqual(len(set(orders)), len(orders))

    def test_total_length_is_sum_of_segments(self):
        model = _routed_model()
        result = FlatteningEngine().flatten(model)
        computed = sum(seg.flattened_length_mm for seg in result.segments)
        self.assertAlmostEqual(result.total_harness_length_mm, computed)
        self.assertGreater(result.total_harness_length_mm, 0)

    def test_connector_breakouts_generated(self):
        model = _routed_model()
        result = FlatteningEngine().flatten(model)
        self.assertEqual(len(result.connector_breakouts), 2)
        refs = {b.reference for b in result.connector_breakouts}
        self.assertEqual(refs, {"J1", "J2"})

    def test_breakout_wire_attachment(self):
        model = _routed_model()
        result = FlatteningEngine().flatten(model)
        for bo in result.connector_breakouts:
            self.assertGreater(len(bo.attached_wire_ids), 0)
            self.assertTrue(all(wid in model.wires for wid in bo.attached_wire_ids))

    def test_wire_lengths_computed(self):
        model = _routed_model()
        result = FlatteningEngine().flatten(model)
        self.assertEqual(len(result.wire_lengths), 1)  # one wire
        entry = result.wire_lengths[0]
        self.assertEqual(entry.wire_id, "W1")
        self.assertGreater(entry.cut_length_mm, 0)

    def test_no_wires_still_flattens_segments(self):
        model = ElectricalProjectModel(Project(project_id="P1", name="H"))
        model.add_bundle_segment(BundleSegment(
            segment_id="S1", bundle_id="B1", from_node_id="A", to_node_id="B",
        ))
        result = FlatteningEngine().flatten(model)
        self.assertEqual(len(result.segments), 1)
        self.assertEqual(len(result.wire_lengths), 0)

    def test_from_to_nodes_populated(self):
        model = _routed_model()
        result = FlatteningEngine().flatten(model)
        for seg in result.segments:
            self.assertTrue(seg.from_node_id or seg.to_node_id)


if __name__ == "__main__":
    unittest.main()
