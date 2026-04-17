"""Active project store for GUI commands and panels."""

from __future__ import annotations

from typing import Callable, Dict, List

import FreeCAD

from .entities import Project
from .model import ElectricalProjectModel

_MODELS_BY_DOC: Dict[str, ElectricalProjectModel] = {}
_OBSERVERS: List[Callable[[], None]] = []


def _active_doc_name() -> str:
    if FreeCAD.ActiveDocument:
        return FreeCAD.ActiveDocument.Name
    return "__session__"


def get_active_model(create_if_missing: bool = True) -> ElectricalProjectModel:
    doc_name = _active_doc_name()
    model = _MODELS_BY_DOC.get(doc_name)
    if model is None and create_if_missing:
        model = ElectricalProjectModel(Project(project_id=doc_name, name=doc_name))
        _MODELS_BY_DOC[doc_name] = model
    if model is None:
        raise RuntimeError("No active Electrical Harness model")
    return model


def set_active_model(model: ElectricalProjectModel) -> None:
    _MODELS_BY_DOC[_active_doc_name()] = model
    notify_changed()


def register_observer(callback: Callable[[], None]) -> None:
    if callback not in _OBSERVERS:
        _OBSERVERS.append(callback)


def unregister_observer(callback: Callable[[], None]) -> None:
    if callback in _OBSERVERS:
        _OBSERVERS.remove(callback)


def notify_changed() -> None:
    stale: List[Callable[[], None]] = []
    for callback in _OBSERVERS:
        try:
            callback()
        except RuntimeError:
            stale.append(callback)
    for callback in stale:
        unregister_observer(callback)


def sample_library_rows() -> List[dict]:
    return [
        {"category": "Connector", "name": "CONN-2PIN", "pins": 2, "favorite": "yes"},
        {"category": "Connector", "name": "CONN-8PIN", "pins": 8, "favorite": "no"},
        {"category": "Wire", "name": "22AWG-RD", "pins": "-", "favorite": "yes"},
        {"category": "Covering", "name": "Braided Sleeve 6mm", "pins": "-", "favorite": "no"},
    ]