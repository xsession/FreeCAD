import unittest

from App.entities import Project
from App.model import ElectricalProjectModel
from App.reports import ReportService


class TestReports(unittest.TestCase):
    def test_empty_csv_is_empty_string(self):
        csv_out = ReportService().to_csv([])
        self.assertEqual(csv_out, "")

    def test_json_export_is_valid(self):
        model = ElectricalProjectModel(Project(project_id="P1", name="Harness"))
        rows = ReportService().from_to_table(model)
        payload = ReportService().to_json(rows)
        self.assertIn("[", payload)


if __name__ == "__main__":
    unittest.main()
