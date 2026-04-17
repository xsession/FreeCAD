"""Stable identifier services for electrical harness entities."""

from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class StableId:
    value: str


class StableIdProvider:
    """Generate deterministic IDs when external keys are available."""

    def __init__(self, namespace: str = "ElectricalHarness") -> None:
        self._namespace_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, namespace)

    def generate(self, kind: str, external_key: str | None = None) -> StableId:
        if external_key:
            token = f"{kind}:{external_key}"
            return StableId(str(uuid.uuid5(self._namespace_uuid, token)))
        return StableId(str(uuid.uuid4()))
