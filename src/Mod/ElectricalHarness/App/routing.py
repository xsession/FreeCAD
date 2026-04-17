"""Route solver interfaces and deterministic default implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Protocol

from .model import ElectricalProjectModel


@dataclass
class RouteConstraintSet:
    min_bend_radius_mm: float = 10.0
    clearance_mm: float = 4.0
    slack_ratio: float = 0.05


@dataclass
class RoutedSegment:
    segment_id: str
    path_node_ids: List[str]
    estimated_length_mm: float


class RouteSolver(Protocol):
    def solve(
        self,
        model: ElectricalProjectModel,
        changed_segment_ids: Iterable[str],
        constraints: RouteConstraintSet,
    ) -> Dict[str, RoutedSegment]:
        pass


class DeterministicGuideSolver:
    """Simple deterministic solver placeholder for incremental upgrades."""

    def solve(
        self,
        model: ElectricalProjectModel,
        changed_segment_ids: Iterable[str],
        constraints: RouteConstraintSet,
    ) -> Dict[str, RoutedSegment]:
        solved: Dict[str, RoutedSegment] = {}
        for segment_id in sorted(set(changed_segment_ids)):
            if segment_id in model.locked_route_segments:
                continue
            segment = model.bundle_segments.get(segment_id)
            if not segment:
                continue
            base = 100.0
            slack = base * max(constraints.slack_ratio, 0.0)
            solved[segment_id] = RoutedSegment(
                segment_id=segment_id,
                path_node_ids=[segment.from_node_id, segment.to_node_id],
                estimated_length_mm=base + slack,
            )
        return solved
