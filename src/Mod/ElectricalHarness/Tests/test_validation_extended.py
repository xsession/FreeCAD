"""Extended tests for the 10-rule validation engine."""

import unittest

from App.entities import (
    BundleSegment,
    ConnectorInstance,
    NetSignal,
    PinCavity,
    Project,
    Splice,
    Wire,
)
from App.model import ElectricalProjectModel
from App.validation import ValidationEngine


def _base_model():
    """Model with one connector (J1, 2 pins), one net, one wire."""
    model = ElectricalProjectModel(Project(project_id="P1", name="Harness"))
    model.add_connector(ConnectorInstance(
        connector_instance_id="J1", connector_definition_id="CONN-2", reference="J1",
    ))
    model.add_pin(PinCavity(pin_id="J1-1", connector_instance_id="J1", cavity_name="1"))
    model.add_pin(PinCavity(pin_id="J1-2", connector_instance_id="J1", cavity_name="2"))
    model.add_connector(ConnectorInstance(
        connector_instance_id="J2", connector_definition_id="CONN-2", reference="J2",
    ))
    model.add_pin(PinCavity(pin_id="J2-1", connector_instance_id="J2", cavity_name="1"))
    model.add_pin(PinCavity(pin_id="J2-2", connector_instance_id="J2", cavity_name="2"))
    model.add_net(NetSignal(net_id="N1", name="VBAT"))
    model.add_wire(Wire(
        wire_id="W1", net_id="N1", from_pin_id="J1-1", to_pin_id="J2-1",
        gauge="22AWG", color="RD",
    ))
    model.add_wire(Wire(
        wire_id="W2", net_id="N1", from_pin_id="J1-2", to_pin_id="J2-2",
        gauge="22AWG", color="BK",
    ))
    return model


class TestDanglingWireRefs(unittest.TestCase):
    def test_wire_referencing_missing_pin(self):
        model = ElectricalProjectModel(Project(project_id="P1", name="H"))
        model.add_net(NetSignal(net_id="N1", name="SIG"))
        model.add_wire(Wire(
            wire_id="W1", net_id="N1", from_pin_id="NONEXIST-A", to_pin_id="NONEXIST-B",
            gauge="20AWG", color="BL",
        ))
        issues = ValidationEngine().run(model)
        codes = [i.code for i in issues]
        self.assertIn("DANGLING_WIRE_PIN", codes)

    def test_wire_referencing_missing_net(self):
        model = ElectricalProjectModel(Project(project_id="P1", name="H"))
        model.add_pin(PinCavity(pin_id="A", connector_instance_id="J1", cavity_name="1"))
        model.add_pin(PinCavity(pin_id="B", connector_instance_id="J1", cavity_name="2"))
        model.add_wire(Wire(
            wire_id="W1", net_id="ORPHAN_NET", from_pin_id="A", to_pin_id="B",
            gauge="22AWG", color="RD",
        ))
        issues = ValidationEngine().run(model)
        codes = [i.code for i in issues]
        self.assertIn("DANGLING_WIRE_NET", codes)


class TestUnusedNet(unittest.TestCase):
    def test_unused_net_flagged(self):
        model = _base_model()
        model.add_net(NetSignal(net_id="N_ORPHAN", name="ORPHAN"))
        issues = ValidationEngine().run(model)
        self.assertTrue(any(i.code == "UNUSED_NET" and i.entity_id == "N_ORPHAN" for i in issues))


class TestDuplicateWire(unittest.TestCase):
    def test_duplicate_pin_pair_flagged(self):
        model = _base_model()
        model.add_wire(Wire(
            wire_id="W_DUP", net_id="N1", from_pin_id="J1-1", to_pin_id="J2-1",
            gauge="22AWG", color="RD",
        ))
        issues = ValidationEngine().run(model)
        self.assertTrue(any(i.code == "DUPLICATE_WIRE" for i in issues))


class TestSpliceBadPin(unittest.TestCase):
    def test_splice_with_nonexistent_pin(self):
        model = _base_model()
        model.add_splice(Splice(splice_id="SP1", member_pin_ids=["J1-1", "GHOST"], splice_type="inline"))
        issues = ValidationEngine().run(model)
        self.assertTrue(any(i.code == "SPLICE_BAD_PIN" for i in issues))


class TestMissingWireGaugeColor(unittest.TestCase):
    def test_missing_gauge(self):
        model = ElectricalProjectModel(Project(project_id="P1", name="H"))
        model.add_pin(PinCavity(pin_id="A", connector_instance_id="J1", cavity_name="1"))
        model.add_pin(PinCavity(pin_id="B", connector_instance_id="J1", cavity_name="2"))
        model.add_net(NetSignal(net_id="N1", name="S"))
        model.add_wire(Wire(
            wire_id="W1", net_id="N1", from_pin_id="A", to_pin_id="B",
            gauge="", color="",
        ))
        issues = ValidationEngine().run(model)
        codes = [i.code for i in issues]
        self.assertIn("MISSING_WIRE_GAUGE", codes)
        self.assertIn("MISSING_WIRE_COLOR", codes)


class TestMissingConnectorRef(unittest.TestCase):
    def test_blank_reference(self):
        model = ElectricalProjectModel(Project(project_id="P1", name="H"))
        model.add_connector(ConnectorInstance(
            connector_instance_id="J1", connector_definition_id="CONN-2", reference="",
        ))
        issues = ValidationEngine().run(model)
        self.assertTrue(any(i.code == "MISSING_CONNECTOR_REF" for i in issues))


class TestOrphanPin(unittest.TestCase):
    def test_pin_with_nonexistent_connector(self):
        model = ElectricalProjectModel(Project(project_id="P1", name="H"))
        model.add_pin(PinCavity(pin_id="X-1", connector_instance_id="NONEXIST", cavity_name="1"))
        issues = ValidationEngine().run(model)
        self.assertTrue(any(i.code == "ORPHAN_PIN" for i in issues))


class TestDisconnectedRouteNode(unittest.TestCase):
    def test_disconnected_segments(self):
        model = _base_model()
        model.add_bundle_segment(BundleSegment(
            segment_id="S1", bundle_id="B1", from_node_id="N1", to_node_id="N2",
        ))
        model.add_bundle_segment(BundleSegment(
            segment_id="S2", bundle_id="B1", from_node_id="N1", to_node_id="N3",
        ))
        model.add_bundle_segment(BundleSegment(
            segment_id="S3", bundle_id="B1", from_node_id="N4", to_node_id="N5",
        ))
        issues = ValidationEngine().run(model)
        self.assertTrue(any(i.code == "DISCONNECTED_ROUTE_NODE" for i in issues))


class TestCleanModelHasNoErrors(unittest.TestCase):
    def test_no_errors_for_clean_model(self):
        model = _base_model()
        issues = ValidationEngine().run(model)
        errors = [i for i in issues if i.severity == "error"]
        self.assertEqual(len(errors), 0, f"Unexpected errors: {[i.code for i in errors]}")


if __name__ == "__main__":
    unittest.main()
