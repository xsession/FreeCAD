import unittest

from App.entities import PinCavity, Project
from App.model import ElectricalProjectModel
from App.validation import ValidationEngine


class TestValidation(unittest.TestCase):
    def test_unconnected_pin_flagged(self):
        model = ElectricalProjectModel(Project(project_id="P1", name="Harness"))
        model.add_pin(PinCavity(pin_id="A1", connector_instance_id="J1", cavity_name="1"))

        issues = ValidationEngine().run(model)

        self.assertTrue(any(item.code == "UNCONNECTED_PIN" for item in issues))


if __name__ == "__main__":
    unittest.main()
