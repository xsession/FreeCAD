# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Unit tests for the frontend-neutral surface-measurement presenter."""

import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestMeasurementSurfacePresenter(unittest.TestCase):
    def test_validation_covers_sampling_and_surface_definition_rules(self):
        from flow_studio.ui.measurement_surface_presenter import MeasurementSurfacePresenter, MeasurementSurfaceSettings

        presenter = MeasurementSurfacePresenter(service=object())

        level, title, detail = presenter.build_validation(
            MeasurementSurfaceSettings("", "Cut Plane", (0.0, 0.0, 0.0), "X", (0.0, 0.0, 0.0), "", 0.0, (), True, False, False, False, (0.0, 0.0, 0.0), False, False, False, ())
        )
        self.assertEqual(level, "incomplete")
        self.assertEqual(title, "Select sampled fields")

        refs = ((types.SimpleNamespace(Label="FaceSet"), ("Face1",)),)
        level, title, detail = presenter.build_validation(
            MeasurementSurfaceSettings("", "Iso-Surface", (0.0, 0.0, 0.0), "X", (0.0, 0.0, 0.0), "", 0.0, ("U",), True, False, False, False, (0.0, 0.0, 0.0), False, False, False, refs)
        )
        self.assertEqual(title, "Iso field required")

        level, title, detail = presenter.build_validation(
            MeasurementSurfaceSettings("", "Geometry Faces", (0.0, 0.0, 0.0), "X", (0.0, 0.0, 0.0), "p", 0.0, ("U",), True, False, False, False, (0.0, 0.0, 0.0), False, False, False, ())
        )
        self.assertEqual(title, "Assign geometry faces")

        level, title, detail = presenter.build_validation(
            MeasurementSurfaceSettings("", "Cut Plane", (0.0, 0.0, 0.0), "Custom", (0.0, 0.0, 0.0), "p", 0.0, ("U",), True, False, False, False, (0.0, 0.0, 0.0), False, False, False, refs)
        )
        self.assertEqual(title, "Custom normal cannot be zero")

        level, title, detail = presenter.build_validation(
            MeasurementSurfaceSettings("", "Cut Plane", (0.0, 0.0, 0.0), "X", (1.0, 0.0, 0.0), "p", 0.0, ("U",), False, False, False, False, (0.0, 0.0, 0.0), False, False, False, refs)
        )
        self.assertEqual(title, "Select an evaluation output")

    def test_persist_settings_round_trips_service_payload(self):
        from flow_studio.ui.measurement_surface_presenter import MeasurementSurfacePresenter, MeasurementSurfaceSettings

        persisted = []
        obj = types.SimpleNamespace()

        class FakeService:
            def persist_settings(self, current_obj, settings, vector_factory):
                persisted.append((current_obj, settings, vector_factory(1.0, 2.0, 3.0)))

        presenter = MeasurementSurfacePresenter(service=FakeService())
        settings = MeasurementSurfaceSettings("Surf", "Cut Plane", (0.0, 0.0, 0.0), "Y", (0.0, 1.0, 0.0), "p", 1.0, ("U",), True, True, False, False, (4.0, 5.0, 6.0), True, False, True, ())

        presenter.persist_settings(obj, settings, lambda x, y, z: (x, y, z))

        self.assertEqual(len(persisted), 1)
        self.assertEqual(persisted[0][1]["PlaneNormal"], "Y")
        self.assertEqual(persisted[0][1]["ForceRefPoint"], (4.0, 5.0, 6.0))
        self.assertEqual(persisted[0][2], (1.0, 2.0, 3.0))

    def test_default_service_constructor_reads_object_state(self):
        from flow_studio.ui.measurement_surface_presenter import MeasurementSurfacePresenter

        vector = lambda x, y, z: types.SimpleNamespace(x=x, y=y, z=z)
        obj = types.SimpleNamespace(
            Label2="Surf",
            SurfaceType="Cut Plane",
            PlaneOrigin=vector(1.0, 2.0, 3.0),
            PlaneNormal="Z",
            CustomNormal=vector(0.0, 0.0, 1.0),
            IsoField="T",
            IsoValue=300.0,
            SampleFields=["U", "p"],
            ComputeAverage=True,
            ComputeIntegral=False,
            ComputeMassFlow=False,
            ComputeForce=False,
            ForceRefPoint=vector(0.0, 0.0, 0.0),
            ExportCSV=True,
            ExportVTK=False,
            TimeSeries=False,
            FaceRefs=[],
        )

        settings = MeasurementSurfacePresenter().read_settings(obj)

        self.assertEqual(settings.surface_type, "Cut Plane")
        self.assertEqual(settings.plane_origin, (1.0, 2.0, 3.0))
        self.assertEqual(settings.sample_fields, ("U", "p"))


if __name__ == "__main__":
    unittest.main()