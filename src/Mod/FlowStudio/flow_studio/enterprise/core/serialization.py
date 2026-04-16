# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Serialization helpers for enterprise manifests."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
import hashlib
import json
from typing import Any


def to_primitive(value: Any) -> Any:
    """Recursively convert dataclasses and enums into JSON-safe structures."""

    if is_dataclass(value):
        return {key: to_primitive(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): to_primitive(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_primitive(item) for item in value]
    enum_value = getattr(value, "value", None)
    if enum_value is not None and type(value).__module__ != "builtins":
        return enum_value
    return value


def to_json(value: Any, *, indent: int = 2) -> str:
    """Serialize an enterprise domain object to stable JSON."""

    return json.dumps(to_primitive(value), indent=indent, sort_keys=True)


def to_sha256(value: Any) -> str:
    """Return a deterministic SHA-256 digest for a serialized value."""

    payload = json.dumps(to_primitive(value), separators=(",", ":"), sort_keys=True)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"
