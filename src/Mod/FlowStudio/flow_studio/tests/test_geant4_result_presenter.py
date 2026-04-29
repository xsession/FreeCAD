# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Unit tests for frontend-neutral Geant4 result presenters."""

import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestGeant4ResultPresenter(unittest.TestCase):
    def test_validation_covers_missing_result_invalid_field_and_ready_state(self):
        from flow_studio.ui.geant4_result_presenter import Geant4ResultPresenter, Geant4ResultSettings

        presenter = Geant4ResultPresenter(service=object())

        level, title, detail = presenter.build_validation(Geant4ResultSettings("", (), (), "dose"))
        self.assertEqual(title, "Import a Geant4 result")

        level, title, detail = presenter.build_validation(
            Geant4ResultSettings("C:/tmp/result.json", (), ("dose", "energy"), "fluence")
        )
        self.assertEqual(title, "Selected field is unavailable")

        level, title, detail = presenter.build_validation(
            Geant4ResultSettings("C:/tmp/result.json", (), ("dose", "energy"), "dose")
        )
        self.assertEqual(title, "Geant4 result ready")

    def test_persist_settings_round_trips_payload(self):
        from flow_studio.ui.geant4_result_presenter import Geant4ResultPresenter, Geant4ResultSettings

        persisted = []

        class FakeService:
            def persist_settings(self, obj, settings):
                persisted.append((obj, settings))

        obj = types.SimpleNamespace()
        presenter = Geant4ResultPresenter(service=FakeService())
        presenter.persist_settings(obj, Geant4ResultSettings("", (), (), "energy"))

        self.assertEqual(persisted[0][1]["ActiveField"], "energy")


class TestGeant4ResultComponentPresenter(unittest.TestCase):
    def test_validation_covers_parent_fields_artifacts_and_ready_state(self):
        from flow_studio.ui.geant4_result_presenter import Geant4ResultComponentPresenter, Geant4ResultComponentSettings

        presenter = Geant4ResultComponentPresenter(service=object())

        level, title, detail = presenter.build_validation(
            Geant4ResultComponentSettings(None, "FlowStudio::Geant4ScoringResult", (), "dose", ())
        )
        self.assertEqual(title, "Parent Geant4 result missing")

        parent = types.SimpleNamespace(Label="Parent")
        level, title, detail = presenter.build_validation(
            Geant4ResultComponentSettings(parent, "FlowStudio::Geant4ScoringResult", (), "dose", ())
        )
        self.assertEqual(title, "No scoring fields available")

        level, title, detail = presenter.build_validation(
            Geant4ResultComponentSettings(parent, "FlowStudio::Geant4ScoringResult", ("dose", "energy"), "fluence", ())
        )
        self.assertEqual(title, "Selected field is unavailable")

        level, title, detail = presenter.build_validation(
            Geant4ResultComponentSettings(parent, "FlowStudio::Geant4ScoringResult", ("dose",), "dose", ("dose.csv",))
        )
        self.assertEqual(title, "Geant4 component ready")

    def test_persist_settings_round_trips_payload(self):
        from flow_studio.ui.geant4_result_presenter import Geant4ResultComponentPresenter, Geant4ResultComponentSettings

        persisted = []

        class FakeService:
            def persist_settings(self, obj, settings):
                persisted.append((obj, settings))

        obj = types.SimpleNamespace()
        presenter = Geant4ResultComponentPresenter(service=FakeService())
        presenter.persist_settings(
            obj,
            Geant4ResultComponentSettings(types.SimpleNamespace(), "FlowStudio::Geant4ScoringResult", ("dose",), "energy", ("dose.csv",)),
        )

        self.assertEqual(persisted[0][1]["ActiveField"], "energy")


if __name__ == "__main__":
    unittest.main()