# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

from __future__ import annotations

import importlib
import os
import sys
import types
import unittest
from unittest import mock


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class _FakeBoundBox:
    def __init__(self, xmin=0.0, ymin=0.0, zmin=0.0, xmax=1.0, ymax=1.0, zmax=1.0):
        self.XMin = xmin
        self.YMin = ymin
        self.ZMin = zmin
        self.XMax = xmax
        self.YMax = ymax
        self.ZMax = zmax
        self.XLength = xmax - xmin
        self.YLength = ymax - ymin
        self.ZLength = zmax - zmin


class _FakeVertex:
    def __init__(self, key):
        self._key = key

    def hashCode(self):
        return self._key


class _FakeEdge:
    def __init__(self, key, vertexes):
        self._key = key
        self.Vertexes = list(vertexes)

    def hashCode(self):
        return self._key


class _FakeFace:
    def __init__(self, edges):
        self.Edges = list(edges)


class _FakeShell:
    def __init__(self, closed):
        self._closed = closed

    def isClosed(self):
        return self._closed


class _FakeShape:
    def __init__(
        self,
        faces=None,
        shells=None,
        solids=None,
        edges=None,
        vertexes=None,
        area=1.0,
        volume=0.0,
        bound_box=None,
        valid=True,
    ):
        self.Faces = list(faces or [])
        self.Shells = list(shells or [])
        self.Solids = list(solids or [])
        self.Edges = list(edges if edges is not None else self._collect_edges())
        self.Vertexes = list(vertexes if vertexes is not None else self._collect_vertexes())
        self.Area = area
        self.Volume = volume
        self.BoundBox = bound_box or _FakeBoundBox()
        self._valid = valid

    def _collect_edges(self):
        edges = []
        seen = set()
        for face in self.Faces:
            for edge in getattr(face, "Edges", []):
                key = edge.hashCode()
                if key in seen:
                    continue
                seen.add(key)
                edges.append(edge)
        return edges

    def _collect_vertexes(self):
        vertexes = []
        seen = set()
        for edge in self.Edges:
            for vertex in getattr(edge, "Vertexes", []):
                key = vertex.hashCode()
                if key in seen:
                    continue
                seen.add(key)
                vertexes.append(vertex)
        return vertexes

    def isNull(self):
        return False

    def isValid(self):
        return self._valid


class _ImportedShape(_FakeShape):
    def __init__(self, source_shape):
        super().__init__(
            faces=source_shape.Faces,
            shells=source_shape.Shells,
            solids=source_shape.Solids,
            edges=source_shape.Edges,
            vertexes=source_shape.Vertexes,
            area=source_shape.Area,
            volume=source_shape.Volume,
            bound_box=source_shape.BoundBox,
            valid=source_shape.isValid(),
        )
        self.read_paths = []

    def read(self, path):
        self.read_paths.append(path)


class TestGeometryToolsTopology(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._freecad_stub = types.SimpleNamespace(ActiveDocument=None)
        cls._module_patcher = mock.patch.dict(sys.modules, {"FreeCAD": cls._freecad_stub})
        cls._module_patcher.start()
        cls.geometry_tools = importlib.import_module("flow_studio.geometry_tools")

    @classmethod
    def tearDownClass(cls):
        cls._module_patcher.stop()
        sys.modules.pop("flow_studio.geometry_tools", None)

    def setUp(self):
        self.geometry_tools.clear_topology_cache()

    @staticmethod
    def _make_open_square_shape():
        vertices = [_FakeVertex(index) for index in range(1, 5)]
        edges = [
            _FakeEdge(101, (vertices[0], vertices[1])),
            _FakeEdge(102, (vertices[1], vertices[2])),
            _FakeEdge(103, (vertices[2], vertices[3])),
            _FakeEdge(104, (vertices[3], vertices[0])),
        ]
        face = _FakeFace(edges)
        return _FakeShape(
            faces=[face],
            shells=[_FakeShell(False)],
            area=4.0,
            volume=0.0,
            bound_box=_FakeBoundBox(0, 0, 0, 2, 2, 0),
        )

    @staticmethod
    def _make_closed_shape(bound_box=None, volume=8.0):
        return _FakeShape(
            faces=[_FakeFace([])],
            shells=[_FakeShell(True)],
            solids=[object()],
            area=12.0,
            volume=volume,
            bound_box=bound_box or _FakeBoundBox(0, 0, 0, 2, 2, 2),
        )

    def test_analyze_shape_topology_detects_free_edges_and_boundary_loop(self):
        shape = self._make_open_square_shape()

        topology = self.geometry_tools.analyze_shape_topology(shape)

        self.assertEqual(topology.face_count, 1)
        self.assertEqual(topology.edge_count, 4)
        self.assertEqual(topology.free_edge_count, 4)
        self.assertEqual(topology.non_manifold_edge_count, 0)
        self.assertEqual(len(topology.boundary_loops), 1)
        self.assertTrue(topology.boundary_loops[0].is_closed)
        self.assertFalse(topology.is_closed)

    def test_analyze_shape_topology_uses_fingerprint_cache(self):
        shape_a = self._make_open_square_shape()
        shape_b = self._make_open_square_shape()

        topology_a = self.geometry_tools.analyze_shape_topology(shape_a)
        topology_b = self.geometry_tools.analyze_shape_topology(shape_b)

        self.assertIs(topology_a, topology_b)

    def test_collect_shape_info_reports_topology_issues(self):
        shape = self._make_open_square_shape()
        obj = types.SimpleNamespace(Name="OpenShell001", Label="Open Shell", Shape=shape)

        info = self.geometry_tools.collect_shape_info(obj)

        self.assertEqual(info.faces, 1)
        self.assertEqual(info.shells, 1)
        self.assertEqual(info.solids, 0)
        self.assertFalse(info.is_closed)
        self.assertIn("no solid body", info.issues)
        self.assertIn("4 free edges", info.issues)
        self.assertIn("open shell", info.issues)

    def test_import_step_optimized_builds_document_object_and_repairs_shape(self):
        source_shape = self._make_open_square_shape()
        imported_shape = _ImportedShape(source_shape)
        repaired_shape = self._make_closed_shape(bound_box=_FakeBoundBox(0, 0, 0, 2, 2, 2))
        document_objects = []

        class _FakeWire:
            def isClosed(self):
                return True

        def _add_object(type_name, name):
            obj = types.SimpleNamespace(Name=name, Label=name, Shape=None)
            document_objects.append((type_name, obj))
            return obj

        fake_document = types.SimpleNamespace(addObject=_add_object, recompute=lambda: None)
        fake_part = types.SimpleNamespace(
            Shape=lambda: imported_shape,
            sortEdges=lambda edges: [list(edges)],
            Wire=lambda edge_group: _FakeWire(),
            Face=lambda wire: _FakeFace([]),
            makeShell=lambda faces: source_shape,
            makeSolid=lambda shell: repaired_shape,
        )

        with mock.patch.object(self.geometry_tools.FreeCAD, "ActiveDocument", fake_document), \
             mock.patch.dict(sys.modules, {"Part": fake_part}):
            result = self.geometry_tools.import_step_optimized(
                "C:/tmp/example.step",
                object_name="ImportedExample",
                repair=True,
            )

        self.assertEqual(imported_shape.read_paths, ["C:/tmp/example.step"])
        self.assertEqual(result.object_name, "ImportedExample")
        self.assertTrue(result.repair_applied)
        self.assertEqual(result.created_lids, 1)
        self.assertEqual(result.topology.solid_count, 1)
        self.assertEqual(len(document_objects), 1)
        self.assertEqual(document_objects[0][0], "Part::Feature")

    def test_detect_geometry_errors_marks_mesh_not_ready_for_open_shell(self):
        open_obj = types.SimpleNamespace(Name="Open001", Label="Open", Shape=self._make_open_square_shape())

        report = self.geometry_tools.detect_geometry_errors(objects=[open_obj])

        self.assertFalse(report["mesh_ready"])
        self.assertTrue(any("open shell" in item for item in report["errors"]))
        self.assertTrue(any("free edges" in item for item in report["warnings"]))

    def test_generate_mesh_from_geometry_runs_existing_mesh_pipeline(self):
        closed_obj = types.SimpleNamespace(
            Name="Closed001",
            Label="Closed",
            Shape=self._make_closed_shape(),
        )
        mesh_obj = types.SimpleNamespace(
            Part=closed_obj,
            MeshPath="",
            NumCells=0,
            NumFaces=0,
            NumPoints=0,
        )
        mesh_utils_stub = types.SimpleNamespace(
            generate_mesh=lambda mesh, objects, output_dir=None: {
                "mesh_file": "C:/tmp/generated.msh",
                "num_cells": 1200,
                "num_faces": 3400,
                "num_points": 980,
            }
        )
        flow_utils_module = types.SimpleNamespace(mesh_utils=mesh_utils_stub)

        with mock.patch.dict(sys.modules, {"flow_studio.utils": flow_utils_module}):
            result = self.geometry_tools.generate_mesh_from_geometry(mesh_obj)

        self.assertEqual(result.status, "SUCCESSFUL")
        self.assertEqual(result.mesh_file, "C:/tmp/generated.msh")
        self.assertEqual(result.num_cells, 1200)
        self.assertEqual(mesh_obj.MeshPath, "C:/tmp/generated.msh")
        self.assertEqual(result.source_objects, ("Closed001",))

    def test_generate_mesh_from_geometry_blocks_invalid_geometry(self):
        open_obj = types.SimpleNamespace(Name="Open001", Label="Open", Shape=self._make_open_square_shape())
        mesh_obj = types.SimpleNamespace(Part=open_obj, MeshPath="")

        result = self.geometry_tools.generate_mesh_from_geometry(mesh_obj)

        self.assertEqual(result.status, "ERROR")
        self.assertTrue(any("open shell" in issue for issue in result.issues))

    def test_run_leak_tracking_detects_disconnected_bodies(self):
        obj_a = types.SimpleNamespace(
            Name="A",
            Label="A",
            Shape=self._make_closed_shape(bound_box=_FakeBoundBox(0, 0, 0, 1, 1, 1)),
        )
        obj_b = types.SimpleNamespace(
            Name="B",
            Label="B",
            Shape=self._make_closed_shape(bound_box=_FakeBoundBox(10, 10, 10, 11, 11, 11)),
        )
        fake_doc = types.SimpleNamespace(Objects=[obj_a, obj_b])

        with mock.patch.object(self.geometry_tools.FreeCAD, "ActiveDocument", fake_doc):
            report = self.geometry_tools.run_leak_tracking((obj_a, "Face1", None), (obj_b, "Face2", None))

        self.assertEqual(report["status"], "NO_CONNECTION")
        self.assertTrue(any("No direct leak path" in line for line in report["messages"]))

    def test_run_leak_tracking_detects_connected_open_assembly(self):
        obj_a = types.SimpleNamespace(
            Name="A",
            Label="A",
            Shape=self._make_closed_shape(bound_box=_FakeBoundBox(0, 0, 0, 1, 1, 1)),
        )
        obj_b = types.SimpleNamespace(
            Name="B",
            Label="B",
            Shape=self._make_open_square_shape(),
        )
        obj_b.Shape.BoundBox = _FakeBoundBox(1, 0, 0, 2, 1, 1)
        fake_doc = types.SimpleNamespace(Objects=[obj_a, obj_b])

        with mock.patch.object(self.geometry_tools.FreeCAD, "ActiveDocument", fake_doc):
            report = self.geometry_tools.run_leak_tracking((obj_a, "Face1", None), (obj_b, "Face2", None))

        self.assertEqual(report["status"], "POSSIBLE_LEAK")
        self.assertTrue(any("unresolved openings" in line for line in report["messages"]))


if __name__ == "__main__":
    unittest.main()
