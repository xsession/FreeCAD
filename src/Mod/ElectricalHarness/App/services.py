"""Application services orchestrating model, routing, flattening, and validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

from .flattening import FlattenedHarness, FlatteningEngine
from .model import ElectricalProjectModel
from .routing import DeterministicGuideSolver, RouteConstraintSet, RoutedSegment
from .validation import ValidationEngine


@dataclass
class SyncResult:
    routed_segments: Dict[str, RoutedSegment]
    flattened_harness: FlattenedHarness
    validation_issue_count: int


class HarnessSyncService:
    """Coordinates bidirectional synchronization between logical and physical views."""

    def __init__(self) -> None:
        self._solver = DeterministicGuideSolver()
        self._flattening = FlatteningEngine()
        self._validation = ValidationEngine()

    def synchronize(
        self,
        model: ElectricalProjectModel,
        changed_segment_ids: Iterable[str],
        constraints: RouteConstraintSet | None = None,
    ) -> SyncResult:
        constraint_set = constraints or RouteConstraintSet()
        routed = self._solver.solve(model, changed_segment_ids, constraint_set)
        flattened = self._flattening.flatten(model)
        issues = self._validation.run(model)
        return SyncResult(
            routed_segments=routed,
            flattened_harness=flattened,
            validation_issue_count=len(issues),
        )


class TransactionLog:
    """Captures domain-level undo/redo checkpoints for future command integration."""

    def __init__(self) -> None:
        self._events: List[str] = []

    def push(self, message: str) -> None:
        self._events.append(message)

    def tail(self, count: int = 20) -> List[str]:
        return self._events[-count:]
