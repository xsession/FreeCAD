# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Unit tests for the frontend-neutral volume-measurement presenter."""

import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestMeasurementVolumePresenter(unittest.TestCase):
    def test_validation_covers_sampling_geometry_and_statistics_rules(self):
        from flow_studio.ui.measurement_volume_presenter import MeasurementVolumePresenter, MeasurementVolumeSettings

        presenter = MeasurementVolumePresenter(service=object())

        level, title, detail = presenter.build_validation(
            MeasurementVolumeSettings("", "Box", (0.0, 0.0, 0.0), (1.0, 1.0, 1.0), (0.0, 0.0, 0.0), 1.0, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), 1.0, 1.0, "", 0.0, 1.0, (), True, False, False, False, False)
        )
        self.assertEqual(level, "incomplete")
        self.assertEqual(title, "Select sampled fields")

        level, title, detail = presenter.build_validation(
            MeasurementVolumeSettings("", "Box", (1.0, 0.0, 0.0), (1.0, 1.0, 1.0), (0.0, 0.0, 0.0), 1.0, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), 1.0, 1.0, "", 0.0, 1.0, ("U",), True, False, False, False, False)
        )
        self.assertEqual(title, "Box limits are invalid")

        level, title, detail = presenter.build_validation(
            MeasurementVolumeSettings("", "Sphere", (0.0, 0.0, 0.0), (1.0, 1.0, 1.0), (0.0, 0.0, 0.0), 0.0, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), 1.0, 1.0, "", 0.0, 1.0, ("U",), True, False, False, False, False)
        )
        self.assertEqual(title, "Sphere radius required")

        level, title, detail = presenter.build_validation(
            MeasurementVolumeSettings("", "Cylinder", (0.0, 0.0, 0.0), (1.0, 1.0, 1.0), (0.0, 0.0, 0.0), 1.0, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), 1.0, 1.0, "", 0.0, 1.0, ("U",), True, False, False, False, False)
        )
        self.assertEqual(title, "Cylinder axis cannot be zero")

        level, title, detail = presenter.build_validation(
            MeasurementVolumeSettings("", "Threshold (field-based)", (0.0, 0.0, 0.0), (1.0, 1.0, 1.0), (0.0, 0.0, 0.0), 1.0, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), 1.0, 1.0, "", 0.0, 1.0, ("U",), True, False, False, False, False)
        )
        self.assertEqual(title, "Threshold field required")

        level, title, detail = presenter.build_validation(
            MeasurementVolumeSettings("", "Entire Domain", (0.0, 0.0, 0.0), (1.0, 1.0, 1.0), (0.0, 0.0, 0.0), 1.0, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), 1.0, 1.0, "Q", 0.0, 1.0, ("U",), False, False, False, False, False)
        )
        self.assertEqual(title, "Select a statistic to compute")

    def test_persist_settings_round_trips_service_payload(self):
        from flow_studio.ui.measurement_volume_presenter import MeasurementVolumePresenter, MeasurementVolumeSettings

        persisted = []
        obj = types.SimpleNamespace()

        class FakeService:
            def persist_settings(self, current_obj, settings, vector_factory):
                persisted.append((current_obj, settings, vector_factory(1.0, 2.0, 3.0)))

        presenter = MeasurementVolumePresenter(service=FakeService())
        settings = MeasurementVolumeSettings("Vol", "Sphere", (0.0, 0.0, 0.0), (1.0, 1.0, 1.0), (4.0, 5.0, 6.0), 7.0, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), 2.0, 3.0, "T", 100.0, 200.0, ("U",), True, True, False, True, False)

        presenter.persist_settings(obj, settings, lambda x, y, z: (x, y, z))

        self.assertEqual(len(persisted), 1)
        self.assertEqual(persisted[0][1]["SphereCenter"], (4.0, 5.0, 6.0))
        self.assertEqual(persisted[0][1]["SphereRadius"], 7.0)
        self.assertEqual(persisted[0][2], (1.0, 2.0, 3.0))

    def test_default_service_constructor_reads_object_state(self):
        from flow_studio.ui.measurement_volume_presenter import MeasurementVolumePresenter

        vector = lambda x, y, z: types.SimpleNamespace(x=x, y=y, z=z)
        obj = types.SimpleNamespace(
            Label2="Vol",
            VolumeType="Sphere",
            BoxMin=vector(0.0, 0.0, 0.0),
            BoxMax=vector(1.0, 1.0, 1.0),
            SphereCenter=vector(4.0, 5.0, 6.0),
            SphereRadius=7.0,
            CylinderCenter=vector(0.0, 0.0, 0.0),
            CylinderAxis=vector(0.0, 0.0, 1.0),
            CylinderRadius=2.0,
            CylinderHeight=3.0,
            ThresholdField="T",
            ThresholdMin=100.0,
            ThresholdMax=200.0,
            SampleFields=["U"],
            ComputeAverage=True,
            ComputeMinMax=False,
            ComputeIntegral=True,
            ExportCSV=False,
            TimeSeries=True,
        )

        settings = MeasurementVolumePresenter().read_settings(obj)

        self.assertEqual(settings.volume_type, "Sphere")
        self.assertEqual(settings.sphere_center, (4.0, 5.0, 6.0))
        self.assertEqual(settings.sample_fields, ("U",))


if __name__ == "__main__":
    unittest.main()