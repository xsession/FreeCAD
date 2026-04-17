"""Component library with search, favorites, generic→specific progression.

Provides a searchable catalog of connectors, wires, coverings, clips, and
accessories. Supports import from CSV, user-defined parts, favorites, and
the generic→specific refinement pattern.
"""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Dict, List, Optional

from .entities import LibraryEntry


class ComponentLibrary:
    """Searchable component catalog with favorites and tiered certification."""

    def __init__(self) -> None:
        self._entries: Dict[str, LibraryEntry] = {}
        self._recently_used: List[str] = []
        self._max_recent: int = 20

    @property
    def size(self) -> int:
        return len(self._entries)

    def add_entry(self, entry: LibraryEntry) -> None:
        self._entries[entry.entry_id] = entry

    def remove_entry(self, entry_id: str) -> bool:
        return self._entries.pop(entry_id, None) is not None

    def get_entry(self, entry_id: str) -> Optional[LibraryEntry]:
        return self._entries.get(entry_id)

    def all_entries(self) -> List[LibraryEntry]:
        return list(self._entries.values())

    # ── Search ───────────────────────────────────────────────────

    def search(
        self,
        query: str = "",
        category: str = "",
        manufacturer: str = "",
        favorites_only: bool = False,
        generic_only: bool = False,
    ) -> List[LibraryEntry]:
        results: List[LibraryEntry] = []
        query_lower = query.lower()
        for entry in self._entries.values():
            if favorites_only and not entry.favorite:
                continue
            if generic_only and not entry.is_generic:
                continue
            if category and entry.category.lower() != category.lower():
                continue
            if manufacturer and entry.manufacturer.lower() != manufacturer.lower():
                continue
            if query_lower:
                searchable = " ".join([
                    entry.name, entry.description, entry.manufacturer,
                    entry.part_number, entry.category,
                ]).lower()
                if query_lower not in searchable:
                    continue
            results.append(entry)
        return results

    def categories(self) -> List[str]:
        return sorted({e.category for e in self._entries.values()})

    def manufacturers(self) -> List[str]:
        return sorted({e.manufacturer for e in self._entries.values() if e.manufacturer})

    # ── Favorites ────────────────────────────────────────────────

    def set_favorite(self, entry_id: str, is_favorite: bool = True) -> bool:
        entry = self._entries.get(entry_id)
        if entry:
            entry.favorite = is_favorite
            return True
        return False

    def favorites(self) -> List[LibraryEntry]:
        return [e for e in self._entries.values() if e.favorite]

    # ── Recently used ────────────────────────────────────────────

    def mark_used(self, entry_id: str) -> None:
        if entry_id in self._entries:
            if entry_id in self._recently_used:
                self._recently_used.remove(entry_id)
            self._recently_used.insert(0, entry_id)
            if len(self._recently_used) > self._max_recent:
                self._recently_used = self._recently_used[: self._max_recent]

    def recently_used(self) -> List[LibraryEntry]:
        return [
            self._entries[eid]
            for eid in self._recently_used
            if eid in self._entries
        ]

    # ── Generic → Specific ───────────────────────────────────────

    def set_specific_part(self, generic_entry_id: str, specific_entry_id: str) -> bool:
        generic = self._entries.get(generic_entry_id)
        specific = self._entries.get(specific_entry_id)
        if generic and specific and generic.is_generic:
            generic.specific_part_id = specific_entry_id
            return True
        return False

    def resolve_specific(self, entry_id: str) -> LibraryEntry:
        entry = self._entries.get(entry_id)
        if not entry:
            raise KeyError(f"Library entry '{entry_id}' not found")
        if entry.is_generic and entry.specific_part_id:
            specific = self._entries.get(entry.specific_part_id)
            if specific:
                return specific
        return entry

    # ── Import / Export ──────────────────────────────────────────

    def import_csv(self, csv_text: str) -> int:
        reader = csv.DictReader(io.StringIO(csv_text))
        count = 0
        for row in reader:
            entry_id = row.get("entry_id", "").strip()
            if not entry_id:
                continue
            entry = LibraryEntry(
                entry_id=entry_id,
                category=row.get("category", "").strip(),
                name=row.get("name", "").strip(),
                manufacturer=row.get("manufacturer", "").strip(),
                part_number=row.get("part_number", "").strip(),
                description=row.get("description", "").strip(),
                is_generic=row.get("is_generic", "true").strip().lower() in ("true", "1", "yes"),
                favorite=row.get("favorite", "false").strip().lower() in ("true", "1", "yes"),
                certification_tier=row.get("certification_tier", "basic").strip(),
            )
            # Extra columns become attributes
            known_cols = {
                "entry_id", "category", "name", "manufacturer", "part_number",
                "description", "is_generic", "favorite", "certification_tier",
                "specific_part_id",
            }
            for key, value in row.items():
                if key not in known_cols and value and value.strip():
                    entry.attributes[key] = value.strip()
            if row.get("specific_part_id", "").strip():
                entry.specific_part_id = row["specific_part_id"].strip()
            self.add_entry(entry)
            count += 1
        return count

    def export_csv(self) -> str:
        if not self._entries:
            return ""
        buffer = io.StringIO()
        fieldnames = [
            "entry_id", "category", "name", "manufacturer", "part_number",
            "description", "is_generic", "favorite", "certification_tier",
            "specific_part_id",
        ]
        writer = csv.DictWriter(buffer, fieldnames=fieldnames)
        writer.writeheader()
        for entry in self._entries.values():
            writer.writerow({
                "entry_id": entry.entry_id,
                "category": entry.category,
                "name": entry.name,
                "manufacturer": entry.manufacturer,
                "part_number": entry.part_number,
                "description": entry.description,
                "is_generic": str(entry.is_generic),
                "favorite": str(entry.favorite),
                "certification_tier": entry.certification_tier,
                "specific_part_id": entry.specific_part_id,
            })
        return buffer.getvalue()

    def to_json(self) -> str:
        from dataclasses import asdict
        data = [asdict(e) for e in self._entries.values()]
        return json.dumps(data, indent=2, sort_keys=True)

    def from_json(self, raw: str) -> int:
        data = json.loads(raw)
        count = 0
        for item in data:
            entry = LibraryEntry(**item)
            self.add_entry(entry)
            count += 1
        return count

    # ── Built-in starter library ─────────────────────────────────

    @classmethod
    def create_starter_library(cls) -> "ComponentLibrary":
        lib = cls()
        # Generic connectors
        for pin_count in (2, 4, 6, 8, 12, 16, 24, 32, 48, 64):
            lib.add_entry(LibraryEntry(
                entry_id=f"CONN-GENERIC-{pin_count}P",
                category="Connector",
                name=f"Generic {pin_count}-Pin Connector",
                description=f"Generic connector with {pin_count} cavities",
                attributes={"pin_count": str(pin_count)},
                is_generic=True,
                favorite=pin_count <= 8,
            ))
        # Common wire gauges
        for gauge in ("30AWG", "28AWG", "26AWG", "24AWG", "22AWG", "20AWG",
                       "18AWG", "16AWG", "14AWG", "12AWG", "10AWG", "8AWG"):
            for color in ("RD", "BK", "WH", "GN", "BL", "YL", "OR", "BR"):
                lib.add_entry(LibraryEntry(
                    entry_id=f"WIRE-{gauge}-{color}",
                    category="Wire",
                    name=f"{gauge} {color}",
                    description=f"Stranded copper wire {gauge} {color}",
                    attributes={"gauge": gauge, "color": color},
                    is_generic=True,
                    favorite=(gauge == "22AWG"),
                ))
        # Coverings
        for mat in ("PVC Tape", "Kapton Tape", "Braided Sleeve", "Heat Shrink",
                     "Convoluted Tubing", "Spiral Wrap"):
            lib.add_entry(LibraryEntry(
                entry_id=f"COV-{mat.upper().replace(' ', '-')}",
                category="Covering",
                name=mat,
                description=f"{mat} wire protection",
                is_generic=True,
            ))
        # Clips
        for clip_type in ("P-Clamp", "Adhesive Mount", "Cable Tie Mount", "Edge Clip"):
            lib.add_entry(LibraryEntry(
                entry_id=f"CLIP-{clip_type.upper().replace(' ', '-')}",
                category="Clip",
                name=clip_type,
                description=f"{clip_type} for bundle support",
                is_generic=True,
            ))
        # Splices
        for stype in ("Inline Crimp", "Butt Splice", "Ring Terminal", "Ultrasonic Weld"):
            lib.add_entry(LibraryEntry(
                entry_id=f"SPLICE-{stype.upper().replace(' ', '-')}",
                category="Splice",
                name=stype,
                description=f"{stype} splice",
                is_generic=True,
            ))
        return lib
