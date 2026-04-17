import unittest

from App.entities import Project
from App.model import ElectricalProjectModel
from App.serialization import ProjectSerializer


class TestSerialization(unittest.TestCase):
    def test_round_trip(self):
        serializer = ProjectSerializer()
        model = ElectricalProjectModel(Project(project_id="P1", name="Harness"))

        payload = serializer.dumps(model)
        restored = serializer.loads(payload)

        self.assertEqual(restored.project.project_id, "P1")


if __name__ == "__main__":
    unittest.main()
