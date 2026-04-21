# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Geometry checking helpers for FlowStudio.

These routines intentionally stay lightweight and FreeCAD-native. They provide
the first FloEFD-style workflow surface for checking model closure, previewing a
fluid-volume envelope, and tracing possible leaks from selected faces.
"""

from dataclasses import dataclass, field

import FreeCAD


FLOW_VOLUME_NAME = "FlowStudio_FluidVolume"


@dataclass
class GeometryCheckOptions:
    exclude_cavities_without_flow_conditions: bool = False
    improved_geometry_handling: bool = False
    advanced_materials_check: bool = False
    create_solid_body_assembly: bool = True
    create_fluid_body_assembly: bool = True


@dataclass
class ShapeInfo:
    object_name: str
    label: str
    faces: int = 0
    shells: int = 0
    solids: int = 0
    volume: float = 0.0
    area: float = 0.0
    is_closed: bool = False
    issues: list = field(default_factory=list)


@dataclass
class GeometryCheckResult:
    status: str = "SUCCESSFUL"
    analysis_type: str = "Internal"
    objects: list = field(default_factory=list)
    issues: list = field(default_factory=list)
    solid_volume: float = 0.0
    bounding_volume: float = 0.0
    fluid_volume: float = 0.0
    bound_box: object = None


def _is_flowstudio_object(obj):
    flow_type = getattr(obj, "FlowType", "")
    if isinstance(flow_type, str) and flow_type.startswith("FlowStudio::"):
        return True
    return getattr(obj, "Name", "") == FLOW_VOLUME_NAME


def iter_geometry_objects(document=None, include_hidden=True):
    """Return document Part-like geometry objects, excluding FlowStudio helpers."""
    document = document or FreeCAD.ActiveDocument
    if document is None:
        return []

    objects = []
    for obj in getattr(document, "Objects", []):
        if _is_flowstudio_object(obj) or not hasattr(obj, "Shape"):
            continue
        try:
            if not obj.isDerivedFrom("Part::Feature"):
                continue
        except Exception:
            pass
        if not include_hidden:
            view = getattr(obj, "ViewObject", None)
            if view is not None and not getattr(view, "Visibility", True):
                continue
        shape = getattr(obj, "Shape", None)
        if shape is None:
            continue
        objects.append(obj)
    return objects


def selected_geometry_objects():
    """Return non-FlowStudio geometry objects from the current GUI selection."""
    try:
        import FreeCADGui

        selection = FreeCADGui.Selection.getSelectionEx()
    except Exception:
        return []

    objects = []
    seen = set()
    for item in selection:
        obj = getattr(item, "Object", None)
        if obj is None or _is_flowstudio_object(obj) or not hasattr(obj, "Shape"):
            continue
        if obj.Name in seen:
            continue
        seen.add(obj.Name)
        objects.append(obj)
    return objects


def _safe_len(value):
    try:
        return len(value)
    except Exception:
        return 0


def _safe_float(value):
    try:
        return float(value)
    except Exception:
        return 0.0


def _shape_is_null(shape):
    try:
        return bool(shape.isNull())
    except Exception:
        return False


def collect_shape_info(obj):
    shape = getattr(obj, "Shape", None)
    label = getattr(obj, "Label", getattr(obj, "Name", "Object"))
    info = ShapeInfo(object_name=getattr(obj, "Name", label), label=label)
    if shape is None or _shape_is_null(shape):
        info.issues.append("empty shape")
        return info

    info.faces = _safe_len(getattr(shape, "Faces", []))
    info.shells = _safe_len(getattr(shape, "Shells", []))
    info.solids = _safe_len(getattr(shape, "Solids", []))
    info.volume = _safe_float(getattr(shape, "Volume", 0.0))
    info.area = _safe_float(getattr(shape, "Area", 0.0))

    closed_shells = 0
    for shell in getattr(shape, "Shells", []) or []:
        try:
            if shell.isClosed():
                closed_shells += 1
        except Exception:
            pass

    info.is_closed = info.solids > 0 or (info.shells > 0 and closed_shells == info.shells)
    if info.faces == 0:
        info.issues.append("no faces")
    if info.solids == 0:
        info.issues.append("no solid body")
    if info.shells > 0 and closed_shells < info.shells:
        info.issues.append("open shell")
    return info


def _united_bound_box(objects):
    bound_box = None
    for obj in objects:
        shape = getattr(obj, "Shape", None)
        if shape is None or _shape_is_null(shape):
            continue
        try:
            box = shape.BoundBox
        except Exception:
            continue
        if bound_box is None:
            bound_box = box
        else:
            bound_box.add(box)
    return bound_box


def _box_volume(bound_box):
    if bound_box is None:
        return 0.0
    return max(0.0, bound_box.XLength) * max(0.0, bound_box.YLength) * max(0.0, bound_box.ZLength)


def check_geometry(objects=None, options=None):
    """Check selected/all geometry and return a summary result."""
    options = options or GeometryCheckOptions()
    objects = list(objects or selected_geometry_objects() or iter_geometry_objects())
    result = GeometryCheckResult()
    result.bound_box = _united_bound_box(objects)
    result.bounding_volume = _box_volume(result.bound_box)

    for obj in objects:
        info = collect_shape_info(obj)
        result.objects.append(info)
        result.solid_volume += max(0.0, info.volume)
        for issue in info.issues:
            result.issues.append(f"{info.label}: {issue}")

    result.fluid_volume = max(0.0, result.bounding_volume - result.solid_volume)
    critical = [issue for issue in result.issues if "empty" in issue or "open shell" in issue]
    result.status = "SUCCESSFUL" if not critical else "WARNING"
    return result


def create_or_update_fluid_volume(result=None, document=None):
    """Create a translucent bounding fluid-volume preview object."""
    document = document or FreeCAD.ActiveDocument
    if document is None:
        return None
    result = result or check_geometry()
    box = result.bound_box
    if box is None or _box_volume(box) <= 0:
        return None

    import Part

    obj = document.getObject(FLOW_VOLUME_NAME)
    if obj is None:
        obj = document.addObject("Part::Feature", FLOW_VOLUME_NAME)
        obj.Label = "FlowStudio Fluid Volume"

    corner = FreeCAD.Vector(box.XMin, box.YMin, box.ZMin)
    obj.Shape = Part.makeBox(box.XLength, box.YLength, box.ZLength, corner)
    try:
        obj.addProperty("App::PropertyFloat", "EstimatedFluidVolume", "FlowStudio", "Estimated fluid volume")
    except Exception:
        pass
    try:
        obj.EstimatedFluidVolume = result.fluid_volume
    except Exception:
        pass
    view = getattr(obj, "ViewObject", None)
    if view is not None:
        view.Visibility = True
        view.ShapeColor = (0.16, 0.72, 1.0)
        view.Transparency = 72
        view.DisplayMode = "Shaded"
    document.recompute()
    return obj


def hide_fluid_volume(document=None):
    document = document or FreeCAD.ActiveDocument
    if document is None:
        return False
    obj = document.getObject(FLOW_VOLUME_NAME)
    if obj is None:
        return False
    view = getattr(obj, "ViewObject", None)
    if view is not None:
        view.Visibility = False
    return True


def show_fluid_volume(document=None):
    return create_or_update_fluid_volume(check_geometry(), document=document)


def fluid_volume_is_visible(document=None):
    document = document or FreeCAD.ActiveDocument
    if document is None:
        return False
    obj = document.getObject(FLOW_VOLUME_NAME)
    view = getattr(obj, "ViewObject", None) if obj is not None else None
    return bool(view is not None and getattr(view, "Visibility", False))


def selected_face_refs():
    """Return selected face references as tuples: object, subelement name, face."""
    try:
        import FreeCADGui

        selection = FreeCADGui.Selection.getSelectionEx()
    except Exception:
        return []

    refs = []
    for item in selection:
        obj = getattr(item, "Object", None)
        if obj is None or not hasattr(obj, "Shape"):
            continue
        names = list(getattr(item, "SubElementNames", []) or [])
        subs = list(getattr(item, "SubObjects", []) or [])
        for index, name in enumerate(names):
            if not str(name).startswith("Face"):
                continue
            face = subs[index] if index < len(subs) else None
            refs.append((obj, name, face))
    return refs


def describe_face_ref(ref):
    obj, sub_name, _face = ref
    return f"{getattr(obj, 'Label', obj.Name)}:{sub_name}"


def run_leak_tracking(face_a=None, face_b=None):
    """Best-effort leak/connection report for two selected faces."""
    refs = selected_face_refs()
    if face_a is None and refs:
        face_a = refs[0]
    if face_b is None and len(refs) > 1:
        face_b = refs[1]

    messages = []
    if face_a is None or face_b is None:
        return {
            "status": "NEEDS_SELECTION",
            "messages": ["Select one internal face and one external face, then run Find Connection."],
        }

    obj_a = face_a[0]
    obj_b = face_b[0]
    info_a = collect_shape_info(obj_a)
    info_b = collect_shape_info(obj_b)
    messages.append(f"Internal face: {describe_face_ref(face_a)}")
    messages.append(f"External face: {describe_face_ref(face_b)}")

    if obj_a.Name == obj_b.Name:
        if info_a.is_closed:
            messages.append("Faces are on the same closed body. No obvious leak path detected.")
            status = "CONNECTED_SOLID"
        else:
            messages.append("Faces are on the same object, but the body is not closed. Leak path is possible.")
            status = "POSSIBLE_LEAK"
    else:
        messages.append("Faces are on different bodies. Check contact/assembly closure between these components.")
        status = "CHECK_ASSEMBLY"

    for info in (info_a, info_b):
        for issue in info.issues:
            messages.append(f"{info.label}: {issue}")
    return {"status": status, "messages": messages}

