# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Unit tests for the frontend-neutral point-measurement presenter."""

import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestMeasurementPointPresenter(unittest.TestCase):
    def test_validation_covers_missing_fields_and_line_endpoint_rules(self):
        from flow_studio.ui.measurement_point_presenter import MeasurementPointPresenter, MeasurementPointSettings

        presenter = MeasurementPointPresenter(service=object())

        level, title, detail = presenter.build_validation(
            MeasurementPointSettings("", (0.0, 0.0, 0.0), False, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 2, (), False, False)
        )
        self.assertEqual(level, "incomplete")
        self.assertEqual(title, "Select sampled fields")

        level, title, detail = presenter.build_validation(
            MeasurementPointSettings("", (0.0, 0.0, 0.0), True, (1.0, 2.0, 3.0), (1.0, 2.0, 3.0), 10, ("U",), False, False)
        )
        self.assertEqual(level, "warning")
        self.assertEqual(title, "Line probe needs distinct endpoints")

    def test_persist_settings_round_trips_service_payload(self):
        from flow_studio.ui.measurement_point_presenter import MeasurementPointPresenter, MeasurementPointSettings

        persisted = []
        obj = types.SimpleNamespace()

        class FakeService:
            def persist_settings(self, current_obj, settings, vector_factory):
                persisted.append((current_obj, settings, vector_factory(1.0, 2.0, 3.0)))

        presenter = MeasurementPointPresenter(service=FakeService())
        settings = MeasurementPointSettings("Probe", (0.0, 0.0, 0.0), True, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 20, ("U", "p"), True, False)

        presenter.persist_settings(obj, settings, lambda x, y, z: (x, y, z))

        self.assertEqual(len(persisted), 1)
        self.assertIs(persisted[0][0], obj)
        self.assertEqual(persisted[0][1]["LineResolution"], 20)
        self.assertEqual(persisted[0][1]["SampleFields"], ("U", "p"))
        self.assertEqual(persisted[0][2], (1.0, 2.0, 3.0))

    def test_default_service_constructor_reads_object_state(self):
        from flow_studio.ui.measurement_point_presenter import MeasurementPointPresenter

        vector = lambda x, y, z: types.SimpleNamespace(x=x, y=y, z=z)
        obj = types.SimpleNamespace(
            Label2="Probe",
            ProbeLocation=vector(1.0, 2.0, 3.0),
            UseLine=False,
            LineStart=vector(0.0, 0.0, 0.0),
            LineEnd=vector(1.0, 0.0, 0.0),
            LineResolution=10,
            SampleFields=["U"],
            ExportCSV=True,
            TimeSeries=False,
        )

        settings = MeasurementPointPresenter().read_settings(obj)

        self.assertEqual(settings.label2, "Probe")
        self.assertEqual(settings.probe_location, (1.0, 2.0, 3.0))
        self.assertEqual(settings.sample_fields, ("U",))


if __name__ == "__main__":
    unittest.main()