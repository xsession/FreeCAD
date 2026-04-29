# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""ViewProvider for FluidMaterial."""

import FreeCAD
import FreeCADGui
from flow_studio.viewproviders.base_vp import BaseFlowVP


class _FluidMaterialSelectionObserver:
    def __init__(self):
        self._forwarding = False

    def addSelection(self, doc_name, obj_name, sub_name, _pos):
        self._forward_selection(doc_name, obj_name, sub_name)

    def setSelection(self, doc_name, obj_name, sub_name):
        self._forward_selection(doc_name, obj_name, sub_name)

    def _forward_selection(self, doc_name, obj_name, sub_name):
        if self._forwarding or sub_name:
            return

        doc = FreeCAD.getDocument(doc_name)
        if doc is None:
            return

        obj = doc.getObject(obj_name)
        if obj is None or getattr(obj, "FlowType", "") != "FlowStudio::FluidMaterial":
            return

        refs = getattr(obj, "References", []) or []
        if not refs:
            return

        self._forwarding = True
        try:
            for ref_obj, sub_names in refs:
                if ref_obj is None:
                    continue

                view_object = getattr(ref_obj, "ViewObject", None)
                if view_object is not None:
                    try:
                        view_object.Visibility = True
                    except Exception:
                        pass

                names = list(sub_names or [])
                if names:
                    for ref_name in names:
                        try:
                            FreeCADGui.Selection.addSelection(ref_obj, ref_name)
                        except TypeError:
                            FreeCADGui.Selection.addSelection(doc_name, ref_obj.Name, ref_name)
                else:
                    try:
                        FreeCADGui.Selection.addSelection(ref_obj)
                    except TypeError:
                        FreeCADGui.Selection.addSelection(doc_name, ref_obj.Name)
        finally:
            self._forwarding = False


class VPFluidMaterial(BaseFlowVP):
    icon_name = "FlowStudioMaterial.svg"

    @staticmethod
    def _ensure_selection_observer():
        observer = getattr(FreeCAD, "_FlowStudioFluidMaterialSelectionObserver", None)
        if observer is not None:
            return

        observer = _FluidMaterialSelectionObserver()
        FreeCADGui.Selection.addObserver(observer)
        FreeCAD._FlowStudioFluidMaterialSelectionObserver = observer

    @staticmethod
    def _reference_items(obj):
        items = []
        seen = set()
        for ref_obj, _sub_names in getattr(obj, "References", []) or []:
            if ref_obj is None:
                continue
            key = getattr(ref_obj, "Name", None)
            if key in seen:
                continue
            seen.add(key)
            items.append(ref_obj)
        return items

    @classmethod
    def _highlight_references(cls, obj):
        refs = getattr(obj, "References", []) or []
        if not refs:
            return

        doc_name = getattr(getattr(obj, "Document", None), "Name", "")
        try:
            FreeCADGui.Selection.clearSelection(doc_name)
        except TypeError:
            FreeCADGui.Selection.clearSelection()

        for ref_obj, sub_names in refs:
            if ref_obj is None:
                continue

            names = list(sub_names or [])
            if names:
                for sub_name in names:
                    try:
                        FreeCADGui.Selection.addSelection(ref_obj, sub_name)
                    except TypeError:
                        FreeCADGui.Selection.addSelection(doc_name, ref_obj.Name, sub_name)
            else:
                try:
                    FreeCADGui.Selection.addSelection(ref_obj)
                except TypeError:
                    FreeCADGui.Selection.addSelection(doc_name, ref_obj.Name)

    def claimChildren(self):
        if hasattr(self, "Object") and self.Object:
            return self._reference_items(self.Object)
        return []

    def attach(self, vobj):
        super().attach(vobj)
        self._ensure_selection_observer()

    def doubleClicked(self, vobj):
        self._highlight_references(vobj.Object)
        return super().doubleClicked(vobj)

    def setEdit(self, vobj, mode=0):
        self._highlight_references(vobj.Object)
        from flow_studio.taskpanels.task_fluid_material import TaskFluidMaterial
        return self.show_task_panel(TaskFluidMaterial, vobj.Object)
