"""Project serialization and migration entry points."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .entities import (
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
    WireNumberingConfig,
)
from .model import ElectricalProjectModel


class ProjectSerializer:
    FORMAT_VERSION = "0.2.0"

    def dumps(self, model: ElectricalProjectModel) -> str:
        payload = model.as_snapshot()
        payload["format_version"] = self.FORMAT_VERSION
        return json.dumps(payload, indent=2, sort_keys=True)

    def dump_file(self, model: ElectricalProjectModel, path: str) -> None:
        Path(path).write_text(self.dumps(model), encoding="utf-8")

    def loads(self, raw: str) -> ElectricalProjectModel:
        payload: Dict[str, Any] = json.loads(raw)
        version = payload.get("format_version", "0.1.0")
        project = Project(**payload["project"])
        model = ElectricalProjectModel(project)

        for connector_data in payload.get("connectors", []):
            model.add_connector(ConnectorInstance(**connector_data))
        for pin_data in payload.get("pins", []):
            model.add_pin(PinCavity(**pin_data))
        for net_data in payload.get("nets", []):
            model.add_net(NetSignal(**net_data))
        for wire_data in payload.get("wires", []):
            model.add_wire(Wire(**_compat_wire(wire_data, version)))
        for splice_data in payload.get("splices", []):
            model.add_splice(Splice(**splice_data))
        for segment_data in payload.get("bundle_segments", []):
            model.add_bundle_segment(BundleSegment(**_compat_segment(segment_data, version)))
        for segment_id in payload.get("locked_route_segments", []):
            model.mark_segment_locked(segment_id, locked=True)

        # Phase 2 entities
        for cable_data in payload.get("cables", []):
            model.add_cable(Cable(**cable_data))
        for tp_data in payload.get("twisted_pairs", []):
            model.add_twisted_pair(TwistedPair(**tp_data))
        for shield_data in payload.get("shields", []):
            model.add_shield(ShieldedGroup(**shield_data))
        for cov_data in payload.get("coverings", []):
            model.add_covering(Covering(**_compat_covering(cov_data, version)))
        for clip_data in payload.get("clips", []):
            model.add_clip(ClipClampSupport(**_compat_clip(clip_data, version)))

        # Wire numbering config
        wnc = payload.get("wire_numbering_config")
        if wnc:
            model.configure_wire_numbering(**wnc)

        # Clear dirty flags from loading
        model.mark_validated()
        return model

    def load_file(self, path: str) -> ElectricalProjectModel:
        return self.loads(Path(path).read_text(encoding="utf-8"))


# ── Migration helpers ────────────────────────────────────────────


def _compat_wire(data: Dict[str, Any], version: str) -> Dict[str, Any]:
    """Ensure v0.1.0 wire dicts get default values for new fields."""
    data.setdefault("wire_number", "")
    data.setdefault("strip_length_mm", 0.0)
    data.setdefault("cable_id", "")
    return data


def _compat_segment(data: Dict[str, Any], version: str) -> Dict[str, Any]:
    """Ensure v0.1.0 segment dicts get default values for new fields."""
    data.setdefault("length_mm", 0.0)
    data.setdefault("min_bend_radius_mm", 0.0)
    data.setdefault("max_fill_ratio", 0.0)
    return data


def _compat_covering(data: Dict[str, Any], version: str) -> Dict[str, Any]:
    """Ensure earlier covering dicts get default values for new fields."""
    data.setdefault("covering_type", "tape")
    return data


def _compat_clip(data: Dict[str, Any], version: str) -> Dict[str, Any]:
    """Ensure earlier clip dicts get default values for new fields."""
    data.setdefault("segment_id", "")
    data.setdefault("position_ratio", 0.5)
    return data
