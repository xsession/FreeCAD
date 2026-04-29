# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Desktop adapter for FlowStudio taskpanel selection capture."""

from __future__ import annotations

import FreeCAD
import FreeCADGui


class FreeCADSelectionDesktopAdapter:
    """Desktop adapter that converts FreeCAD GUI selection into reference tuples."""

    def get_selected_references(self, mode="any"):
        refs = []
        try:
            selection = FreeCADGui.Selection.getSelectionEx()
        except Exception:
            selection = []

        converted_faces = False
        skipped_items = False
        for item in selection:
            obj = getattr(item, "Object", None)
            if obj is None:
                continue
            flow_type = getattr(obj, "FlowType", "")
            if isinstance(flow_type, str) and flow_type.startswith("FlowStudio::"):
                continue

            sub_names = list(getattr(item, "SubElementNames", []) or [])
            if mode == "volumes":
                volume_names, converted, skipped = self._volume_sub_names(obj, sub_names)
                converted_faces = converted_faces or converted
                skipped_items = skipped_items or skipped
                if not volume_names:
                    continue
                refs.append((obj, volume_names))
                continue

            refs.append((obj, sub_names))

        refs = self._deduplicate_refs(refs)

        if mode == "volumes":
            if converted_faces:
                FreeCAD.Console.PrintMessage(
                    "FlowStudio: Converted selected faces to owning solid regions for material assignment.\n"
                )
            if skipped_items:
                FreeCAD.Console.PrintWarning(
                    "FlowStudio: Material assignment only accepts solid or volume geometry. "
                    "Some selected items were ignored.\n"
                )
        return refs

    @staticmethod
    def _deduplicate_refs(refs):
        merged = {}
        for obj, sub_names in refs:
            if obj is None:
                continue
            key = getattr(obj, "Name", None)
            names = list(sub_names or [])
            if key not in merged:
                merged[key] = [obj, []]
            bucket = merged[key][1]
            for name in names:
                if name not in bucket:
                    bucket.append(name)
        return [(obj, names) for obj, names in merged.values()]

    @staticmethod
    def _volume_sub_names(obj, sub_names):
        shape = getattr(obj, "Shape", None)
        solids = list(getattr(shape, "Solids", []) or []) if shape is not None else []
        solid_names = [f"Solid{index + 1}" for index in range(len(solids))]
        if not solid_names:
            return [], False, True

        if not sub_names:
            return solid_names, False, False

        selected_solids = [name for name in sub_names if isinstance(name, str) and name.startswith("Solid")]
        if selected_solids:
            return selected_solids, False, False

        if len(solid_names) == 1:
            return solid_names, True, False

        return [], False, True