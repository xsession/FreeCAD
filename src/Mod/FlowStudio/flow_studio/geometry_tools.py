# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Geometry checking helpers for FlowStudio.

These routines intentionally stay lightweight and FreeCAD-native. They provide
the first FloEFD-style workflow surface for checking model closure, previewing a
fluid-volume envelope, and tracing possible leaks from selected faces.

The STEP-oriented helpers below use a single-pass topology index with a small
fingerprint cache so large imported models can be inspected and manipulated
without repeatedly rescanning the whole face/edge graph.
"""

from collections import OrderedDict
from dataclasses import dataclass, field
import os

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
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    solid_volume: float = 0.0
    bounding_volume: float = 0.0
    fluid_volume: float = 0.0
    bound_box: object = None
    mesh_ready: bool = False


@dataclass
class MeshGenerationResult:
    status: str = "SUCCESSFUL"
    mesh_file: str = ""
    num_cells: int = 0
    num_faces: int = 0
    num_points: int = 0
    source_objects: tuple = ()
    issues: list = field(default_factory=list)


@dataclass
class BoundaryLoop:
    edge_count: int = 0
    is_closed: bool = False
    edge_hashes: tuple = ()
    vertex_hashes: tuple = ()


@dataclass
class ShapeTopologyIndex:
    face_count: int = 0
    edge_count: int = 0
    vertex_count: int = 0
    shell_count: int = 0
    solid_count: int = 0
    free_edge_count: int = 0
    non_manifold_edge_count: int = 0
    closed_shell_count: int = 0
    boundary_loops: tuple = ()
    boundary_edges: tuple = ()
    is_closed: bool = False


@dataclass
class StepImportResult:
    path: str
    object_name: str
    shape: object
    topology: ShapeTopologyIndex
    repair_applied: bool = False
    created_lids: int = 0
    issues: list = field(default_factory=list)


_TOPOLOGY_CACHE_MAX = 16
_topology_cache = OrderedDict()


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


def _topology_cache_get(key):
    if key is None:
        return None
    cached = _topology_cache.get(key)
    if cached is None:
        return None
    _topology_cache.move_to_end(key)
    return cached


def _topology_cache_put(key, value):
    if key is None:
        return value
    _topology_cache[key] = value
    _topology_cache.move_to_end(key)
    while len(_topology_cache) > _TOPOLOGY_CACHE_MAX:
        _topology_cache.popitem(last=False)
    return value


def clear_topology_cache():
    """Clear cached shape topology analysis results."""
    _topology_cache.clear()


def _bound_box_fingerprint(shape):
    try:
        box = shape.BoundBox
    except Exception:
        return None
    return (
        round(_safe_float(getattr(box, "XMin", 0.0)), 6),
        round(_safe_float(getattr(box, "YMin", 0.0)), 6),
        round(_safe_float(getattr(box, "ZMin", 0.0)), 6),
        round(_safe_float(getattr(box, "XMax", 0.0)), 6),
        round(_safe_float(getattr(box, "YMax", 0.0)), 6),
        round(_safe_float(getattr(box, "ZMax", 0.0)), 6),
    )


def shape_fingerprint(shape):
    """Return a lightweight fingerprint suitable for topology result caching."""
    if shape is None or _shape_is_null(shape):
        return None
    return (
        _safe_len(getattr(shape, "Faces", [])),
        _safe_len(getattr(shape, "Edges", [])),
        _safe_len(getattr(shape, "Vertexes", [])),
        _safe_len(getattr(shape, "Shells", [])),
        _safe_len(getattr(shape, "Solids", [])),
        round(_safe_float(getattr(shape, "Area", 0.0)), 6),
        round(_safe_float(getattr(shape, "Volume", 0.0)), 6),
        _bound_box_fingerprint(shape),
    )


def _hash_topology_item(item, fallback):
    try:
        return int(item.hashCode())
    except Exception:
        return int(fallback)


def _vertex_hash(vertex, fallback):
    return _hash_topology_item(vertex, fallback)


def _edge_vertices(edge):
    vertexes = list(getattr(edge, "Vertexes", []) or [])
    if not vertexes:
        return ()
    return tuple(_vertex_hash(vertex, index) for index, vertex in enumerate(vertexes))


def _edge_hash(edge, fallback):
    return _hash_topology_item(edge, fallback)


def _walk_boundary_component(start_key, edge_by_key, edge_vertices, vertex_to_edges, visited):
    pending = [start_key]
    component = []
    vertex_hashes = set()
    while pending:
        edge_key = pending.pop()
        if edge_key in visited:
            continue
        visited.add(edge_key)
        component.append(edge_key)
        vertices = edge_vertices.get(edge_key, ())
        vertex_hashes.update(vertices)
        for vertex_key in vertices:
            for neighbor in vertex_to_edges.get(vertex_key, ()):
                if neighbor not in visited:
                    pending.append(neighbor)
    degrees = {}
    for edge_key in component:
        for vertex_key in edge_vertices.get(edge_key, ()):
            degrees[vertex_key] = degrees.get(vertex_key, 0) + 1
    is_closed = bool(component) and all(degree == 2 for degree in degrees.values())
    return BoundaryLoop(
        edge_count=len(component),
        is_closed=is_closed,
        edge_hashes=tuple(component),
        vertex_hashes=tuple(sorted(vertex_hashes)),
    )


def analyze_shape_topology(shape, use_cache=True):
    """Build a single-pass topology index for a FreeCAD shape."""
    if shape is None or _shape_is_null(shape):
        return ShapeTopologyIndex()

    cache_key = shape_fingerprint(shape) if use_cache else None
    cached = _topology_cache_get(cache_key) if use_cache else None
    if cached is not None:
        return cached

    faces = list(getattr(shape, "Faces", []) or [])
    shells = list(getattr(shape, "Shells", []) or [])
    solids = list(getattr(shape, "Solids", []) or [])
    edges = list(getattr(shape, "Edges", []) or [])
    vertexes = list(getattr(shape, "Vertexes", []) or [])

    edge_face_count = {}
    edge_by_key = {}
    edge_vertices = {}
    vertex_to_edges = {}

    for face_index, face in enumerate(faces):
        for local_index, edge in enumerate(getattr(face, "Edges", []) or []):
            edge_key = _edge_hash(edge, face_index * 100000 + local_index)
            edge_by_key[edge_key] = edge
            edge_face_count[edge_key] = edge_face_count.get(edge_key, 0) + 1
            if edge_key not in edge_vertices:
                vertices_for_edge = _edge_vertices(edge)
                edge_vertices[edge_key] = vertices_for_edge
                for vertex_key in vertices_for_edge:
                    vertex_to_edges.setdefault(vertex_key, []).append(edge_key)

    boundary_keys = tuple(edge_key for edge_key, count in edge_face_count.items() if count == 1)
    non_manifold_edge_count = sum(1 for count in edge_face_count.values() if count > 2)

    visited = set()
    boundary_loops = []
    for edge_key in boundary_keys:
        if edge_key in visited:
            continue
        boundary_loops.append(
            _walk_boundary_component(edge_key, edge_by_key, edge_vertices, vertex_to_edges, visited)
        )

    closed_shell_count = 0
    for shell in shells:
        try:
            if shell.isClosed():
                closed_shell_count += 1
        except Exception:
            pass

    index = ShapeTopologyIndex(
        face_count=len(faces),
        edge_count=len(edges),
        vertex_count=len(vertexes),
        shell_count=len(shells),
        solid_count=len(solids),
        free_edge_count=len(boundary_keys),
        non_manifold_edge_count=non_manifold_edge_count,
        closed_shell_count=closed_shell_count,
        boundary_loops=tuple(boundary_loops),
        boundary_edges=tuple(edge_by_key[edge_key] for edge_key in boundary_keys),
        is_closed=(len(boundary_keys) == 0 and non_manifold_edge_count == 0),
    )
    return _topology_cache_put(cache_key, index) if use_cache else index


def repair_shape_gaps(shape, max_boundary_edges=4096):
    """Try to cap planar boundary loops on an imported shell/compound shape."""
    topology = analyze_shape_topology(shape, use_cache=False)
    if topology.free_edge_count == 0:
        return shape, topology, []
    if topology.free_edge_count > max_boundary_edges:
        return shape, topology, []

    try:
        import Part
    except Exception:
        return shape, topology, []

    try:
        sorted_edge_groups = Part.sortEdges(list(topology.boundary_edges))
    except Exception:
        sorted_edge_groups = []

    lids = []
    for edge_group in sorted_edge_groups:
        try:
            wire = Part.Wire(edge_group)
            if not wire.isClosed():
                continue
            lids.append(Part.Face(wire))
        except Exception:
            continue

    if not lids:
        return shape, topology, []

    all_faces = list(getattr(shape, "Faces", []) or []) + lids
    try:
        shell = Part.makeShell(all_faces)
    except Exception:
        return shape, topology, lids

    try:
        repaired = Part.makeSolid(shell)
        if repaired is not None and repaired.isValid():
            return repaired, analyze_shape_topology(repaired, use_cache=False), lids
    except Exception:
        pass
    return shell, analyze_shape_topology(shell, use_cache=False), lids


def import_step_optimized(path, document=None, object_name=None, repair=False):
    """Import a STEP file and immediately build a reusable topology index."""
    import Part

    shape = Part.Shape()
    shape.read(path)
    topology = analyze_shape_topology(shape)
    issues = []
    created_lids = 0
    repair_applied = False

    if repair and topology.free_edge_count:
        repaired_shape, repaired_topology, lids = repair_shape_gaps(shape)
        if lids:
            shape = repaired_shape
            topology = repaired_topology
            created_lids = len(lids)
            repair_applied = True
        elif topology.free_edge_count:
            issues.append("boundary gaps detected but automatic lid generation could not close them")

    document = document or FreeCAD.ActiveDocument
    object_name = object_name or os.path.splitext(os.path.basename(path))[0] or "ImportedSTEP"
    obj = None
    if document is not None:
        obj = document.addObject("Part::Feature", object_name)
        obj.Label = object_name
        obj.Shape = shape
        recompute = getattr(document, "recompute", None)
        if callable(recompute):
            recompute()

    return StepImportResult(
        path=path,
        object_name=getattr(obj, "Name", object_name),
        shape=shape,
        topology=topology,
        repair_applied=repair_applied,
        created_lids=created_lids,
        issues=issues,
    )


def collect_shape_info(obj):
    shape = getattr(obj, "Shape", None)
    label = getattr(obj, "Label", getattr(obj, "Name", "Object"))
    info = ShapeInfo(object_name=getattr(obj, "Name", label), label=label)
    if shape is None or _shape_is_null(shape):
        info.issues.append("empty shape")
        return info

    topology = analyze_shape_topology(shape)
    info.faces = topology.face_count
    info.shells = topology.shell_count
    info.solids = topology.solid_count
    info.volume = _safe_float(getattr(shape, "Volume", 0.0))
    info.area = _safe_float(getattr(shape, "Area", 0.0))

    info.is_closed = info.solids > 0 or topology.is_closed
    if info.faces == 0:
        info.issues.append("no faces")
    if info.solids == 0:
        info.issues.append("no solid body")
    if topology.free_edge_count:
        info.issues.append(f"{topology.free_edge_count} free edges")
    if topology.non_manifold_edge_count:
        info.issues.append(f"{topology.non_manifold_edge_count} non-manifold edges")
    if info.shells > 0 and topology.closed_shell_count < info.shells:
        info.issues.append("open shell")
    return info


def _severity_for_issue(issue_text):
    lowered = str(issue_text).lower()
    if any(token in lowered for token in ("empty", "non-manifold", "open shell", "no faces")):
        return "error"
    if any(token in lowered for token in ("free edges", "no solid body")):
        return "warning"
    return "info"


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
            full_issue = f"{info.label}: {issue}"
            result.issues.append(full_issue)
            severity = _severity_for_issue(issue)
            if severity == "error":
                result.errors.append(full_issue)
            elif severity == "warning":
                result.warnings.append(full_issue)

    result.fluid_volume = max(0.0, result.bounding_volume - result.solid_volume)
    result.mesh_ready = not bool(result.errors)
    if result.errors:
        result.status = "WARNING"
    elif result.warnings:
        result.status = "WARNING"
    else:
        result.status = "SUCCESSFUL"
    return result


def detect_geometry_errors(objects=None, options=None):
    """Return structured geometry error and warning lists for meshing/readiness checks."""
    result = check_geometry(objects=objects, options=options)
    return {
        "status": result.status,
        "mesh_ready": result.mesh_ready,
        "errors": list(result.errors),
        "warnings": list(result.warnings),
        "issues": list(result.issues),
        "result": result,
    }


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


def _box_axis_gap(min_a, max_a, min_b, max_b):
    if max_a < min_b:
        return min_b - max_a
    if max_b < min_a:
        return min_a - max_b
    return 0.0


def _bound_box_gap(box_a, box_b):
    if box_a is None or box_b is None:
        return float("inf")
    dx = _box_axis_gap(box_a.XMin, box_a.XMax, box_b.XMin, box_b.XMax)
    dy = _box_axis_gap(box_a.YMin, box_a.YMax, box_b.YMin, box_b.YMax)
    dz = _box_axis_gap(box_a.ZMin, box_a.ZMax, box_b.ZMin, box_b.ZMax)
    return max(dx, dy, dz)


def _get_bound_box(shape):
    try:
        return shape.BoundBox
    except Exception:
        return None


def _objects_connected(obj_a, obj_b, tolerance=1e-5):
    shape_a = getattr(obj_a, "Shape", None)
    shape_b = getattr(obj_b, "Shape", None)
    if shape_a is None or shape_b is None:
        return False
    gap = _bound_box_gap(_get_bound_box(shape_a), _get_bound_box(shape_b))
    return gap <= tolerance


def _build_connectivity_graph(objects, tolerance=1e-5):
    graph = {getattr(obj, "Name", str(index)): set() for index, obj in enumerate(objects)}
    for index, obj_a in enumerate(objects):
        for obj_b in objects[index + 1:]:
            if _objects_connected(obj_a, obj_b, tolerance=tolerance):
                graph[obj_a.Name].add(obj_b.Name)
                graph[obj_b.Name].add(obj_a.Name)
    return graph


def _connected_component(graph, start_name):
    if start_name not in graph:
        return set()
    visited = set()
    pending = [start_name]
    while pending:
        current = pending.pop()
        if current in visited:
            continue
        visited.add(current)
        pending.extend(neighbor for neighbor in graph.get(current, ()) if neighbor not in visited)
    return visited


def _lookup_object(document_objects, object_name):
    for obj in document_objects:
        if getattr(obj, "Name", None) == object_name:
            return obj
    return None


def resolve_mesh_objects(mesh_obj=None, geometry_objects=None, document=None):
    """Resolve the geometry bodies that should be sent to the mesher."""
    if geometry_objects:
        return [obj for obj in geometry_objects if obj is not None]
    if mesh_obj is not None:
        linked = getattr(mesh_obj, "Part", None)
        if linked is not None:
            return [linked]
    return list(iter_geometry_objects(document=document))


def generate_mesh_from_geometry(mesh_obj, geometry_objects=None, output_dir=None, options=None):
    """Validate geometry and run the existing GMSH export pipeline."""
    from flow_studio.utils import mesh_utils

    geometry_objects = resolve_mesh_objects(mesh_obj=mesh_obj, geometry_objects=geometry_objects)
    diagnostics = detect_geometry_errors(objects=geometry_objects, options=options)
    issues = list(diagnostics["issues"])
    if not geometry_objects:
        return MeshGenerationResult(
            status="ERROR",
            source_objects=(),
            issues=["No geometry objects selected for mesh generation."],
        )
    if not diagnostics["mesh_ready"]:
        return MeshGenerationResult(
            status="ERROR",
            source_objects=tuple(getattr(obj, "Name", "") for obj in geometry_objects),
            issues=issues,
        )

    mesh_data = mesh_utils.generate_mesh(mesh_obj, geometry_objects, output_dir=output_dir)
    mesh_file = str(mesh_data.get("mesh_file", ""))
    try:
        mesh_obj.MeshPath = mesh_file
    except Exception:
        pass
    return MeshGenerationResult(
        status="SUCCESSFUL",
        mesh_file=mesh_file,
        num_cells=int(mesh_data.get("num_cells", 0) or 0),
        num_faces=int(mesh_data.get("num_faces", 0) or 0),
        num_points=int(mesh_data.get("num_points", 0) or 0),
        source_objects=tuple(getattr(obj, "Name", "") for obj in geometry_objects),
        issues=issues,
    )


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
    topology_a = analyze_shape_topology(getattr(obj_a, "Shape", None))
    topology_b = analyze_shape_topology(getattr(obj_b, "Shape", None))

    if obj_a.Name == obj_b.Name:
        if info_a.is_closed and topology_a.free_edge_count == 0:
            messages.append("Faces are on the same closed body. No obvious leak path detected.")
            status = "CONNECTED_SOLID"
        else:
            messages.append(
                "Faces are on the same object, and the body contains openings or topology defects."
            )
            if topology_a.boundary_loops:
                messages.append(
                    f"Detected {len(topology_a.boundary_loops)} boundary loop(s) across "
                    f"{topology_a.free_edge_count} free edge(s)."
                )
            status = "POSSIBLE_LEAK"
    else:
        document_objects = list(iter_geometry_objects())
        graph = _build_connectivity_graph(document_objects)
        component_a = _connected_component(graph, obj_a.Name)
        component_b = _connected_component(graph, obj_b.Name)
        if not component_a or obj_b.Name not in component_a:
            messages.append("Faces belong to disconnected bodies. No direct leak path was detected.")
            status = "NO_CONNECTION"
        else:
            component_names = sorted(component_a | component_b)
            leaking_names = []
            for object_name in component_names:
                obj = _lookup_object(document_objects, object_name)
                if obj is None:
                    continue
                if not collect_shape_info(obj).is_closed:
                    leaking_names.append(getattr(obj, "Label", object_name))
            messages.append(
                f"Faces belong to the same contact-connected assembly component ({len(component_names)} bodies)."
            )
            if leaking_names:
                messages.append(
                    "Possible leak path crosses bodies with unresolved openings: " + ", ".join(leaking_names)
                )
                status = "POSSIBLE_LEAK"
            else:
                messages.append("Connected assembly appears closed within simple contact-gap tolerance.")
                status = "CHECK_ASSEMBLY"

    for info in (info_a, info_b):
        for issue in info.issues:
            messages.append(f"{info.label}: {issue}")
    return {"status": status, "messages": messages}
