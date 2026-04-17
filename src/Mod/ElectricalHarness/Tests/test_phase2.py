"""Tests for Phase 2: cables, shields, twisted pairs, coverings, wire numbering,
change tracking, incremental validation, new validation rules, and enhanced reports."""

import unittest

from App.entities import (
    BundleSegment,
    Cable,
    ClipClampSupport,
    ConnectorInstance,
    Covering,
    NetSignal,
    PinCavity,
    Project,
    ShieldedGroup,
    Splice,
    TwistedPair,
    Wire,
)
from App.model import ElectricalProjectModel
from App.validation import ValidationEngine
from App.reports import ReportService
from App.serialization import ProjectSerializer
from App.flattening import FlatteningEngine


def _base_model():
    """Model with 2 connectors (2 pins each), 1 net, 2 wires."""
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


# ═════════════════════════════════════════════════════════════════
#  Cable / Shield / Twisted Pair
# ═════════════════════════════════════════════════════════════════


class TestCableCreation(unittest.TestCase):
    def test_create_cable_links_wires(self):
        model = _base_model()
        cable = model.create_cable("CAN Bus Cable", wire_ids=["W1", "W2"])
        self.assertEqual(cable.cable_id, "CBL1")
        self.assertEqual(len(cable.conductor_ids), 2)
        self.assertEqual(model.wires["W1"].cable_id, "CBL1")
        self.assertEqual(model.wires["W2"].cable_id, "CBL1")

    def test_wires_in_cable_query(self):
        model = _base_model()
        model.create_cable("Cable A", wire_ids=["W1"])
        wires = model.wires_in_cable("CBL1")
        self.assertEqual(len(wires), 1)
        self.assertEqual(wires[0].wire_id, "W1")

    def test_cable_with_shield_and_jacket(self):
        model = _base_model()
        cable = model.create_cable(
            "Shielded Cable",
            wire_ids=["W1", "W2"],
            shield_type="braided",
            jacket_material="PVC",
        )
        self.assertEqual(cable.shield_type, "braided")
        self.assertEqual(cable.jacket_material, "PVC")

    def test_next_cable_id_increments(self):
        model = _base_model()
        model.create_cable("A")
        model.create_cable("B")
        self.assertIn("CBL1", model.cables)
        self.assertIn("CBL2", model.cables)


class TestTwistedPairCreation(unittest.TestCase):
    def test_create_twisted_pair(self):
        model = _base_model()
        tp = model.create_twisted_pair("W1", "W2", twist_pitch_mm=30.0)
        self.assertEqual(tp.twisted_pair_id, "TP1")
        self.assertEqual(tp.wire_id_a, "W1")
        self.assertEqual(tp.wire_id_b, "W2")
        self.assertEqual(tp.twist_pitch_mm, 30.0)

    def test_twisted_pair_in_cable(self):
        model = _base_model()
        cable = model.create_cable("TP Cable", wire_ids=["W1", "W2"])
        tp = model.create_twisted_pair("W1", "W2", cable_id=cable.cable_id)
        self.assertEqual(tp.cable_id, "CBL1")


class TestShieldCreation(unittest.TestCase):
    def test_create_shield(self):
        model = _base_model()
        shield = model.create_shield("EMI Shield", member_wire_ids=["W1", "W2"])
        self.assertEqual(shield.shield_id, "SHD1")
        self.assertEqual(len(shield.member_wire_ids), 2)

    def test_shield_with_drain_wire(self):
        model = _base_model()
        # Make a drain wire
        model.add_pin(PinCavity(pin_id="D1", connector_instance_id="J1", cavity_name="D"))
        model.add_pin(PinCavity(pin_id="D2", connector_instance_id="J2", cavity_name="D"))
        model.add_wire(Wire(
            wire_id="W_DRAIN", net_id="N1", from_pin_id="D1", to_pin_id="D2",
            gauge="26AWG", color="GN",
        ))
        shield = model.create_shield(
            "Shield with Drain",
            member_wire_ids=["W1", "W2"],
            drain_wire_id="W_DRAIN",
        )
        self.assertEqual(shield.drain_wire_id, "W_DRAIN")

    def test_shields_for_wire_query(self):
        model = _base_model()
        model.create_shield("S1", member_wire_ids=["W1"])
        model.create_shield("S2", member_wire_ids=["W1", "W2"])
        shields = model.shields_for_wire("W1")
        self.assertEqual(len(shields), 2)


# ═════════════════════════════════════════════════════════════════
#  Coverings and Clips
# ═════════════════════════════════════════════════════════════════


class TestCoveringManagement(unittest.TestCase):
    def test_add_covering_to_segment(self):
        model = _base_model()
        model.add_bundle_segment(BundleSegment(
            segment_id="S1", bundle_id="B1", from_node_id="N1", to_node_id="N2",
        ))
        cov = model.add_covering_to_segment("S1", "PVC Tape", covering_type="tape")
        self.assertEqual(cov.covering_id, "COV1")
        self.assertEqual(cov.segment_id, "S1")
        self.assertEqual(cov.material, "PVC Tape")

    def test_coverings_on_segment_query(self):
        model = _base_model()
        model.add_bundle_segment(BundleSegment(
            segment_id="S1", bundle_id="B1", from_node_id="N1", to_node_id="N2",
        ))
        model.add_covering_to_segment("S1", "Tape", start_ratio=0.0, end_ratio=0.5)
        model.add_covering_to_segment("S1", "Sleeve", start_ratio=0.5, end_ratio=1.0)
        covs = model.coverings_on_segment("S1")
        self.assertEqual(len(covs), 2)


class TestClipManagement(unittest.TestCase):
    def test_add_clip(self):
        model = _base_model()
        model.add_bundle_segment(BundleSegment(
            segment_id="S1", bundle_id="B1", from_node_id="N1", to_node_id="N2",
        ))
        clip = ClipClampSupport(
            support_id="CLP1", support_type="P-Clamp", host_path="/body",
            segment_id="S1", position_ratio=0.5,
        )
        model.add_clip(clip)
        self.assertIn("CLP1", model.clips)


# ═════════════════════════════════════════════════════════════════
#  Wire Numbering
# ═════════════════════════════════════════════════════════════════


class TestWireNumbering(unittest.TestCase):
    def test_default_numbering(self):
        model = _base_model()
        count = model.auto_number_wires()
        self.assertEqual(count, 2)
        numbers = sorted(w.wire_number for w in model.wires.values())
        self.assertEqual(numbers, ["W001", "W002"])

    def test_custom_numbering(self):
        model = _base_model()
        model.configure_wire_numbering(
            prefix="WIRE-", suffix="", start_number=100, zero_pad=4,
        )
        model.auto_number_wires()
        numbers = sorted(w.wire_number for w in model.wires.values())
        self.assertEqual(numbers, ["WIRE-0100", "WIRE-0101"])

    def test_numbering_with_net_name(self):
        model = _base_model()
        model.configure_wire_numbering(
            prefix="", suffix="", start_number=1, zero_pad=2,
            separator="-", include_net_name=True,
        )
        model.auto_number_wires()
        for wire in model.wires.values():
            self.assertIn("VBAT", wire.wire_number)

    def test_numbering_config_roundtrip(self):
        model = _base_model()
        model.configure_wire_numbering(prefix="WN", start_number=10, zero_pad=5)
        cfg = model.wire_numbering_config
        self.assertEqual(cfg.prefix, "WN")
        self.assertEqual(cfg.start_number, 10)
        self.assertEqual(cfg.zero_pad, 5)


# ═════════════════════════════════════════════════════════════════
#  Change Tracking
# ═════════════════════════════════════════════════════════════════


class TestChangeTracking(unittest.TestCase):
    def test_new_model_is_dirty(self):
        model = _base_model()
        self.assertTrue(model.needs_validation)
        self.assertGreater(model.change_generation, 0)

    def test_mark_validated_clears_dirty(self):
        model = _base_model()
        model.mark_validated()
        self.assertFalse(model.needs_validation)
        self.assertEqual(len(model.dirty_entities), 0)

    def test_add_wire_marks_dirty(self):
        model = _base_model()
        model.mark_validated()
        model.add_wire(Wire(
            wire_id="W3", net_id="N1", from_pin_id="J1-1", to_pin_id="J2-1",
            gauge="20AWG", color="BL",
        ))
        self.assertTrue(model.needs_validation)
        self.assertIn("W3", model.dirty_entities)

    def test_dependent_entity_ids(self):
        model = _base_model()
        deps = model.dependent_entity_ids("J1-1")
        # W1 and W2 reference J1-1 as from_pin
        self.assertIn("W1", deps)

    def test_remove_wire_marks_dirty(self):
        model = _base_model()
        model.mark_validated()
        model.remove_wire("W1")
        self.assertTrue(model.needs_validation)
        self.assertIn("W1", model.dirty_entities)

    def test_remove_connector(self):
        model = _base_model()
        result = model.remove_connector("J1")
        self.assertTrue(result)
        self.assertNotIn("J1", model.connectors)

    def test_remove_nonexistent_returns_false(self):
        model = _base_model()
        self.assertFalse(model.remove_wire("NONEXIST"))
        self.assertFalse(model.remove_connector("NONEXIST"))


# ═════════════════════════════════════════════════════════════════
#  Incremental Validation
# ═════════════════════════════════════════════════════════════════


class TestIncrementalValidation(unittest.TestCase):
    def test_incremental_returns_previous_when_clean(self):
        model = _base_model()
        engine = ValidationEngine()
        full_issues = engine.run(model)
        # Model is now validated, not dirty
        incremental = engine.run_incremental(model, previous_issues=full_issues)
        self.assertEqual(len(incremental), len(full_issues))

    def test_incremental_after_change(self):
        model = _base_model()
        engine = ValidationEngine()
        engine.run(model)
        # Make a change
        model.add_wire(Wire(
            wire_id="W3", net_id="N1", from_pin_id="J1-1", to_pin_id="J2-1",
            gauge="22AWG", color="RD",
        ))
        issues = engine.run_incremental(model)
        # Should detect the duplicate wire
        codes = [i.code for i in issues]
        self.assertIn("DUPLICATE_WIRE", codes)


# ═════════════════════════════════════════════════════════════════
#  New Validation Rules (Phase 2)
# ═════════════════════════════════════════════════════════════════


class TestBendRadiusValidation(unittest.TestCase):
    def test_segment_below_min_bend_radius(self):
        model = _base_model()
        model.add_bundle_segment(BundleSegment(
            segment_id="S1", bundle_id="B1", from_node_id="N1", to_node_id="N2",
            min_bend_radius_mm=1.0,  # Way too tight for 22AWG
        ))
        issues = ValidationEngine().run(model)
        self.assertTrue(any(i.code == "BEND_RADIUS_VIOLATION" for i in issues))

    def test_segment_no_bend_radius_no_issue(self):
        model = _base_model()
        model.add_bundle_segment(BundleSegment(
            segment_id="S1", bundle_id="B1", from_node_id="N1", to_node_id="N2",
            min_bend_radius_mm=0.0,  # Not specified
        ))
        issues = ValidationEngine().run(model)
        self.assertFalse(any(i.code == "BEND_RADIUS_VIOLATION" for i in issues))


class TestFillRatioValidation(unittest.TestCase):
    def test_segment_exceeding_fill_ratio(self):
        model = _base_model()
        # Very small conduit with max_fill_ratio
        model.add_bundle_segment(BundleSegment(
            segment_id="S1", bundle_id="B1", from_node_id="N1", to_node_id="N2",
            nominal_diameter_mm=0.5, max_fill_ratio=0.01,  # Tiny conduit
        ))
        issues = ValidationEngine().run(model)
        self.assertTrue(any(i.code == "FILL_RATIO_EXCEEDED" for i in issues))

    def test_fill_ratio_computation(self):
        model = _base_model()
        model.add_bundle_segment(BundleSegment(
            segment_id="S1", bundle_id="B1", from_node_id="N1", to_node_id="N2",
            nominal_diameter_mm=10.0,
        ))
        ratio = model.segment_fill_ratio("S1")
        self.assertGreater(ratio, 0.0)
        self.assertLess(ratio, 1.0)


class TestShieldingContinuityValidation(unittest.TestCase):
    def test_empty_shield_error(self):
        model = _base_model()
        model.add_shield(ShieldedGroup(
            shield_id="SHD1", display_name="Empty", member_wire_ids=[],
        ))
        issues = ValidationEngine().run(model)
        self.assertTrue(any(i.code == "SHIELD_EMPTY" for i in issues))

    def test_shield_dangling_wire(self):
        model = _base_model()
        model.add_shield(ShieldedGroup(
            shield_id="SHD1", display_name="Bad", member_wire_ids=["NONEXIST"],
        ))
        issues = ValidationEngine().run(model)
        self.assertTrue(any(i.code == "SHIELD_DANGLING_WIRE" for i in issues))

    def test_shield_dangling_drain(self):
        model = _base_model()
        model.add_shield(ShieldedGroup(
            shield_id="SHD1", display_name="Bad Drain",
            member_wire_ids=["W1"], drain_wire_id="NONEXIST",
        ))
        issues = ValidationEngine().run(model)
        self.assertTrue(any(i.code == "SHIELD_DANGLING_DRAIN" for i in issues))

    def test_shield_invalid_coverage(self):
        model = _base_model()
        model.add_shield(ShieldedGroup(
            shield_id="SHD1", display_name="Over",
            member_wire_ids=["W1"], coverage_percent=150.0,
        ))
        issues = ValidationEngine().run(model)
        self.assertTrue(any(i.code == "SHIELD_COVERAGE_INVALID" for i in issues))

    def test_valid_shield_no_issue(self):
        model = _base_model()
        model.add_shield(ShieldedGroup(
            shield_id="SHD1", display_name="Good",
            member_wire_ids=["W1", "W2"], coverage_percent=85.0,
        ))
        issues = ValidationEngine().run(model)
        shield_issues = [i for i in issues if i.entity_id == "SHD1"]
        self.assertEqual(len(shield_issues), 0)


class TestCoveringOverlapValidation(unittest.TestCase):
    def test_overlapping_coverings(self):
        model = _base_model()
        model.add_bundle_segment(BundleSegment(
            segment_id="S1", bundle_id="B1", from_node_id="N1", to_node_id="N2",
        ))
        model.add_covering(Covering(
            covering_id="COV1", segment_id="S1", material="Tape",
            start_ratio=0.0, end_ratio=0.6,
        ))
        model.add_covering(Covering(
            covering_id="COV2", segment_id="S1", material="Sleeve",
            start_ratio=0.5, end_ratio=1.0,
        ))
        issues = ValidationEngine().run(model)
        self.assertTrue(any(i.code == "COVERING_OVERLAP" for i in issues))

    def test_non_overlapping_ok(self):
        model = _base_model()
        model.add_bundle_segment(BundleSegment(
            segment_id="S1", bundle_id="B1", from_node_id="N1", to_node_id="N2",
        ))
        model.add_covering(Covering(
            covering_id="COV1", segment_id="S1", material="Tape",
            start_ratio=0.0, end_ratio=0.5,
        ))
        model.add_covering(Covering(
            covering_id="COV2", segment_id="S1", material="Sleeve",
            start_ratio=0.5, end_ratio=1.0,
        ))
        issues = ValidationEngine().run(model)
        self.assertFalse(any(i.code == "COVERING_OVERLAP" for i in issues))

    def test_covering_invalid_range(self):
        model = _base_model()
        model.add_bundle_segment(BundleSegment(
            segment_id="S1", bundle_id="B1", from_node_id="N1", to_node_id="N2",
        ))
        model.add_covering(Covering(
            covering_id="COV1", segment_id="S1", material="Tape",
            start_ratio=0.7, end_ratio=0.3,
        ))
        issues = ValidationEngine().run(model)
        self.assertTrue(any(i.code == "COVERING_INVALID_RANGE" for i in issues))

    def test_covering_dangling_segment(self):
        model = _base_model()
        model.add_covering(Covering(
            covering_id="COV1", segment_id="NONEXIST", material="Tape",
        ))
        issues = ValidationEngine().run(model)
        self.assertTrue(any(i.code == "COVERING_DANGLING_SEGMENT" for i in issues))


class TestCableIntegrityValidation(unittest.TestCase):
    def test_empty_cable_warning(self):
        model = _base_model()
        model.add_cable(Cable(cable_id="CBL1", display_name="Empty"))
        issues = ValidationEngine().run(model)
        self.assertTrue(any(i.code == "CABLE_EMPTY" for i in issues))

    def test_cable_dangling_wire(self):
        model = _base_model()
        model.add_cable(Cable(
            cable_id="CBL1", display_name="Bad",
            conductor_ids=["NONEXIST"],
        ))
        issues = ValidationEngine().run(model)
        self.assertTrue(any(i.code == "CABLE_DANGLING_WIRE" for i in issues))

    def test_valid_cable_no_issue(self):
        model = _base_model()
        model.add_cable(Cable(
            cable_id="CBL1", display_name="Good",
            conductor_ids=["W1", "W2"],
        ))
        issues = ValidationEngine().run(model)
        cable_issues = [i for i in issues if i.entity_id == "CBL1"]
        self.assertEqual(len(cable_issues), 0)


class TestTwistedPairValidation(unittest.TestCase):
    def test_same_wire_error(self):
        model = _base_model()
        model.add_twisted_pair(TwistedPair(
            twisted_pair_id="TP1", wire_id_a="W1", wire_id_b="W1",
        ))
        issues = ValidationEngine().run(model)
        self.assertTrue(any(i.code == "TWISTED_PAIR_SAME_WIRE" for i in issues))

    def test_dangling_wire_ref(self):
        model = _base_model()
        model.add_twisted_pair(TwistedPair(
            twisted_pair_id="TP1", wire_id_a="W1", wire_id_b="NONEXIST",
        ))
        issues = ValidationEngine().run(model)
        self.assertTrue(any(i.code == "TWISTED_PAIR_DANGLING" for i in issues))

    def test_invalid_pitch(self):
        model = _base_model()
        model.add_twisted_pair(TwistedPair(
            twisted_pair_id="TP1", wire_id_a="W1", wire_id_b="W2",
            twist_pitch_mm=-5.0,
        ))
        issues = ValidationEngine().run(model)
        self.assertTrue(any(i.code == "TWISTED_PAIR_PITCH" for i in issues))

    def test_valid_twisted_pair_no_issue(self):
        model = _base_model()
        model.add_twisted_pair(TwistedPair(
            twisted_pair_id="TP1", wire_id_a="W1", wire_id_b="W2",
            twist_pitch_mm=25.0,
        ))
        issues = ValidationEngine().run(model)
        tp_issues = [i for i in issues if i.entity_id == "TP1"]
        self.assertEqual(len(tp_issues), 0)


class TestCustomValidationRule(unittest.TestCase):
    def test_custom_rule_is_invoked(self):
        model = _base_model()
        engine = ValidationEngine()
        from App.entities import ValidationIssue

        def my_rule(m):
            return [ValidationIssue(
                issue_id="CUSTOM-1", severity="info",
                code="CUSTOM_CHECK", message="Custom rule fired",
                entity_id=m.project.project_id,
            )]

        engine.register_custom_rule(my_rule)
        issues = engine.run(model)
        self.assertTrue(any(i.code == "CUSTOM_CHECK" for i in issues))


# ═════════════════════════════════════════════════════════════════
#  Serialization v0.2.0
# ═════════════════════════════════════════════════════════════════


class TestSerializationV2(unittest.TestCase):
    def test_roundtrip_with_cables(self):
        model = _base_model()
        model.create_cable("Cable A", wire_ids=["W1", "W2"], shield_type="braided")
        model.create_twisted_pair("W1", "W2")
        model.create_shield("Shield A", member_wire_ids=["W1"])
        model.add_bundle_segment(BundleSegment(
            segment_id="S1", bundle_id="B1", from_node_id="N1", to_node_id="N2",
            length_mm=150.0, min_bend_radius_mm=5.0, max_fill_ratio=0.4,
        ))
        model.add_covering_to_segment("S1", "PVC Tape")
        model.add_clip(ClipClampSupport(
            support_id="CLP1", support_type="P-Clamp", host_path="/body",
            segment_id="S1",
        ))
        model.configure_wire_numbering(prefix="WN-", start_number=100, zero_pad=4)
        model.auto_number_wires()

        serializer = ProjectSerializer()
        raw = serializer.dumps(model)
        restored = serializer.loads(raw)

        self.assertEqual(len(restored.cables), 1)
        self.assertEqual(len(restored.twisted_pairs), 1)
        self.assertEqual(len(restored.shields), 1)
        self.assertEqual(len(restored.coverings), 1)
        self.assertEqual(len(restored.clips), 1)
        self.assertEqual(restored.wires["W1"].cable_id, "CBL1")
        self.assertEqual(restored.wires["W1"].wire_number, "WN-0100")
        self.assertEqual(restored.bundle_segments["S1"].length_mm, 150.0)
        self.assertEqual(restored.bundle_segments["S1"].min_bend_radius_mm, 5.0)
        self.assertEqual(restored.wire_numbering_config.prefix, "WN-")
        self.assertEqual(restored.wire_numbering_config.start_number, 100)

    def test_format_version_is_0_2_0(self):
        model = _base_model()
        serializer = ProjectSerializer()
        raw = serializer.dumps(model)
        import json
        payload = json.loads(raw)
        self.assertEqual(payload["format_version"], "0.2.0")

    def test_backward_compat_v0_1_0(self):
        """v0.1.0 payload (no cables/shields/etc.) should load without error."""
        import json
        payload = {
            "format_version": "0.1.0",
            "project": {"project_id": "P1", "name": "Old"},
            "connectors": [],
            "pins": [],
            "nets": [],
            "wires": [
                {"wire_id": "W1", "net_id": "N1", "from_pin_id": "A",
                 "to_pin_id": "B", "gauge": "22AWG", "color": "RD"},
            ],
            "splices": [],
            "bundle_segments": [],
            "locked_route_segments": [],
        }
        serializer = ProjectSerializer()
        model = serializer.loads(json.dumps(payload))
        self.assertEqual(len(model.wires), 1)
        self.assertEqual(model.wires["W1"].wire_number, "")
        self.assertEqual(model.wires["W1"].cable_id, "")
        self.assertEqual(len(model.cables), 0)


# ═════════════════════════════════════════════════════════════════
#  Enhanced Reports
# ═════════════════════════════════════════════════════════════════


class TestEnhancedReports(unittest.TestCase):
    def _model_with_extras(self):
        model = _base_model()
        model.create_cable("Cable A", wire_ids=["W1", "W2"])
        model.create_shield("Shield A", member_wire_ids=["W1"])
        model.add_bundle_segment(BundleSegment(
            segment_id="S1", bundle_id="B1", from_node_id="N1", to_node_id="N2",
        ))
        model.add_covering_to_segment("S1", "PVC Tape")
        model.add_clip(ClipClampSupport(
            support_id="CLP1", support_type="P-Clamp", host_path="/body",
            segment_id="S1",
        ))
        model.auto_number_wires()
        return model

    def test_bom_includes_coverings_and_clips(self):
        model = self._model_with_extras()
        rows = ReportService().bom(model)
        categories = {r["category"] for r in rows}
        self.assertIn("Covering", categories)
        self.assertIn("Clip", categories)
        self.assertIn("Cable", categories)

    def test_wire_list_includes_new_fields(self):
        model = self._model_with_extras()
        rows = ReportService().wire_list(model)
        for row in rows:
            self.assertIn("wire_number", row)
            self.assertIn("cable_id", row)
            self.assertIn("shield_ids", row)
            self.assertIn("strip_length_mm", row)

    def test_from_to_includes_wire_number(self):
        model = self._model_with_extras()
        rows = ReportService().from_to_table(model)
        for row in rows:
            self.assertIn("wire_number", row)
            self.assertIn("cable_id", row)

    def test_cable_summary_report(self):
        model = self._model_with_extras()
        rows = ReportService().cable_summary(model)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["conductor_count"], "2")

    def test_shield_summary_report(self):
        model = self._model_with_extras()
        rows = ReportService().shield_summary(model)
        self.assertEqual(len(rows), 1)

    def test_covering_summary_report(self):
        model = self._model_with_extras()
        rows = ReportService().covering_summary(model)
        self.assertEqual(len(rows), 1)

    def test_project_summary_includes_phase2_counts(self):
        model = self._model_with_extras()
        summary = ReportService().project_summary(model)
        self.assertEqual(summary["cable_count"], 1)
        self.assertEqual(summary["shield_count"], 1)
        self.assertEqual(summary["covering_count"], 1)
        self.assertEqual(summary["clip_count"], 1)

    def test_flattening_table_includes_covering_count(self):
        model = self._model_with_extras()
        flattened = FlatteningEngine().flatten(model)
        rows = ReportService().flattening_table(flattened)
        self.assertGreaterEqual(len(rows), 1)
        for row in rows:
            self.assertIn("covering_count", row)


# ═════════════════════════════════════════════════════════════════
#  Model entity iteration includes new types
# ═════════════════════════════════════════════════════════════════


class TestEntityIteration(unittest.TestCase):
    def test_iter_includes_phase2_entities(self):
        model = _base_model()
        model.create_cable("C", wire_ids=["W1"])
        model.create_shield("S", member_wire_ids=["W1"])
        model.create_twisted_pair("W1", "W2")
        model.add_bundle_segment(BundleSegment(
            segment_id="SEG1", bundle_id="B1", from_node_id="N1", to_node_id="N2",
        ))
        model.add_covering_to_segment("SEG1", "Tape")
        model.add_clip(ClipClampSupport(
            support_id="CLP1", support_type="P-Clamp", host_path="/body",
        ))

        all_ids = set(model.iter_entity_ids())
        self.assertIn("CBL1", all_ids)
        self.assertIn("SHD1", all_ids)
        self.assertIn("TP1", all_ids)
        self.assertIn("COV1", all_ids)
        self.assertIn("CLP1", all_ids)


if __name__ == "__main__":
    unittest.main()
