import unittest

from App.entities import NetSignal, PinCavity, Project, Wire
from App.model import ElectricalProjectModel


class TestModel(unittest.TestCase):
    def test_pin_graph_connects_wires(self):
        model = ElectricalProjectModel(Project(project_id="P1", name="Demo"))
        model.add_pin(PinCavity(pin_id="A1", connector_instance_id="J1", cavity_name="1"))
        model.add_pin(PinCavity(pin_id="B1", connector_instance_id="J2", cavity_name="1"))
        model.add_net(NetSignal(net_id="N1", name="VBAT"))
        model.add_wire(
            Wire(
                wire_id="W1",
                net_id="N1",
                from_pin_id="A1",
                to_pin_id="B1",
                gauge="22AWG",
                color="RD",
            )
        )

        graph = model.build_pin_graph()
        self.assertIn("B1", graph["A1"])

    def test_add_connector_with_pins_and_wire_link(self):
        model = ElectricalProjectModel(Project(project_id="P1", name="Demo"))
        connector = model.add_connector_with_pins("J10", 2)
        pin_ids = sorted(model.connector_pin_ids(connector.connector_instance_id))

        self.assertEqual(len(pin_ids), 2)

        wire = model.connect_pins(pin_ids[0], pin_ids[1], "NET_CAN_H")
        self.assertEqual(wire.net_id, next(iter(model.nets.values())).net_id)
        self.assertEqual(len(model.wires), 1)

    def test_rename_net(self):
        model = ElectricalProjectModel(Project(project_id="P1", name="Demo"))
        model.create_or_get_net("NET_OLD")
        updated = model.rename_net("NET_OLD", "NET_NEW")

        self.assertEqual(updated, 1)
        self.assertEqual(next(iter(model.nets.values())).name, "NET_NEW")


if __name__ == "__main__":
    unittest.main()
