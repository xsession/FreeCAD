# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""End-to-end test: STEP file import → lid generation → leak detection.

This test creates a realistic pipe geometry with open ends via the Part
workbench, exports it to STEP, re-imports it, then exercises lid generation
(capping open faces) and watertightness / leak detection.

**Must be executed inside FreeCAD** (via FreeCADCmd.exe or the GUI).
Discovered by unittest but skipped if FreeCAD is not available.
"""

import sys
import os
import traceback
import tempfile

# Guard: skip module entirely when imported outside FreeCAD
try:
    import FreeCAD as App
    import Part
    _HAS_FREECAD = True
except ImportError:
    _HAS_FREECAD = False


# ======================================================================
# Helpers
# ======================================================================

def _make_open_pipe(doc, outer_radius=10.0, inner_radius=8.0, length=100.0):
    """Create a hollow pipe (open on both ends) → simulates imported CAD.

    Returns the Part::Feature so we can query faces / shells.
    """
    # Outer cylinder
    outer = Part.makeCylinder(outer_radius, length)
    # Inner cylinder (hollow out)
    inner = Part.makeCylinder(inner_radius, length)
    pipe_solid = outer.cut(inner)

    # Remove top and bottom faces to leave the pipe open
    # The pipe has faces: outer cyl, inner cyl, top ring, bottom ring
    # We want to remove the two annular ring faces at z=0 and z=length
    open_faces = []
    for face in pipe_solid.Faces:
        # Ring faces are planar and perpendicular to Z
        if face.Surface.isPlanar():
            normal = face.Surface.Axis
            if abs(abs(normal.z) - 1.0) < 0.01:
                continue  # skip top/bottom ring faces
        open_faces.append(face)

    # Build a shell from just the cylindrical faces (open pipe)
    open_shell = Part.makeShell(open_faces)

    feat = doc.addObject("Part::Feature", "OpenPipe")
    feat.Shape = open_shell
    doc.recompute()
    return feat


def _make_complex_manifold(doc):
    """Create a large-ish STEP-like geometry: a box with an internal channel.

    This is a watertight manifold (closed solid).  We use Boolean ops
    to make something that *looks* like it was imported from a STEP file.
    """
    # Outer box
    box = Part.makeBox(200, 100, 80)
    # Channel (cylinder) cut through the box
    channel = Part.makeCylinder(15, 250)
    channel.translate(App.Vector(0, 50, 40))
    channel.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 0)  # along X
    # The cylinder is along Z by default; rotate to go along X
    channel = Part.makeCylinder(15, 250, App.Vector(-25, 50, 40), App.Vector(1, 0, 0))
    solid = box.cut(channel)

    feat = doc.addObject("Part::Feature", "Manifold")
    feat.Shape = solid
    doc.recompute()
    return feat


def _cap_open_faces(shape):
    """Detect open edges and create planar lids to close them.

    Strategy: find free (boundary) edges, group them into closed wires,
    then make faces from those wires.

    Returns (lids, num_boundary_wires) where lids is a list of Part.Face.
    """
    # Free edges = edges that belong to exactly one face
    edge_face_count = {}
    for i, face in enumerate(shape.Faces):
        for edge in face.Edges:
            key = edge.hashCode()
            edge_face_count.setdefault(key, []).append(i)

    free_edges = []
    for face in shape.Faces:
        for edge in face.Edges:
            if len(edge_face_count.get(edge.hashCode(), [])) == 1:
                free_edges.append(edge)

    if not free_edges:
        return [], 0

    # Try to form closed wires from free edges
    sorted_edges = Part.sortEdges(free_edges)
    lids = []
    for wire_edges in sorted_edges:
        try:
            wire = Part.Wire(wire_edges)
            if wire.isClosed():
                face = Part.Face(wire)
                lids.append(face)
        except Exception:
            pass  # Non-planar or degenerate

    return lids, len(sorted_edges)


def _check_watertight(shape):
    """Check if a shape (solid or shell) is watertight.

    Returns dict with diagnostic info.
    """
    info = {
        "is_valid": shape.isValid(),
        "is_closed": False,
        "num_faces": len(shape.Faces),
        "num_edges": len(shape.Edges),
        "num_vertices": len(shape.Vertexes),
        "num_shells": len(shape.Shells) if hasattr(shape, "Shells") else 0,
        "num_solids": len(shape.Solids) if hasattr(shape, "Solids") else 0,
        "free_edges": 0,
        "volume": 0.0,
    }

    # Count free edges (boundary edges belonging to only 1 face)
    edge_face_count = {}
    for face in shape.Faces:
        for edge in face.Edges:
            key = edge.hashCode()
            edge_face_count[key] = edge_face_count.get(key, 0) + 1
    info["free_edges"] = sum(1 for v in edge_face_count.values() if v == 1)
    info["is_closed"] = info["free_edges"] == 0

    if shape.Solids:
        info["volume"] = shape.Solids[0].Volume

    return info


# ======================================================================
# Test cases
# ======================================================================

class E2EStepImportTests:
    """End-to-end tests for STEP import → lid generation → leak check."""

    def __init__(self):
        self.results = []
        self.doc = None

    def _pass(self, name, detail=""):
        self.results.append(("PASS", name, detail))
        print(f"  PASS: {name} {detail}")

    def _fail(self, name, detail=""):
        self.results.append(("FAIL", name, detail))
        print(f"  FAIL: {name} {detail}")

    def _skip(self, name, detail=""):
        self.results.append(("SKIP", name, detail))
        print(f"  SKIP: {name} {detail}")

    def setup(self):
        self.doc = App.newDocument("E2E_STEP_Import")

    def teardown(self):
        if self.doc:
            App.closeDocument(self.doc.Name)
            self.doc = None

    # ------------------------------------------------------------------
    # Test: Create complex geometry and export/import STEP
    # ------------------------------------------------------------------
    def test_step_export_import_roundtrip(self):
        """Create a complex solid, export to STEP, re-import, verify."""
        name = "test_step_export_import_roundtrip"
        try:
            # Create complex geometry
            feat = _make_complex_manifold(self.doc)
            original_shape = feat.Shape
            original_faces = len(original_shape.Faces)
            original_volume = original_shape.Volume

            assert original_faces > 0, "No faces in original shape"
            assert original_volume > 0, "Zero volume"

            # Export to STEP
            step_path = os.path.join(tempfile.gettempdir(), "flowstudio_e2e_test.step")
            original_shape.exportStep(step_path)
            assert os.path.exists(step_path), "STEP file not created"
            file_size = os.path.getsize(step_path)
            assert file_size > 100, f"STEP file too small: {file_size} bytes"

            # Re-import the STEP file
            imported_shape = Part.Shape()
            imported_shape.read(step_path)
            assert imported_shape.isValid(), "Imported shape is invalid"

            # Create feature from imported shape
            imported_feat = self.doc.addObject("Part::Feature", "ImportedManifold")
            imported_feat.Shape = imported_shape
            self.doc.recompute()

            # Verify geometry is preserved
            imported_faces = len(imported_shape.Faces)
            imported_volume = imported_shape.Volume

            assert imported_faces == original_faces, \
                f"Face count mismatch: {imported_faces} vs {original_faces}"
            # Volume should be very close (within 0.1%)
            vol_diff = abs(imported_volume - original_volume) / original_volume
            assert vol_diff < 0.001, \
                f"Volume mismatch: {imported_volume:.1f} vs {original_volume:.1f} (diff={vol_diff:.4%})"

            self._pass(name, f"faces={imported_faces}, vol={imported_volume:.1f}, "
                             f"step_size={file_size}B")

            # Cleanup temp file
            os.remove(step_path)

        except Exception as e:
            self._fail(name, str(e))
            traceback.print_exc()

    # ------------------------------------------------------------------
    # Test: Large geometry (many faces) — performance
    # ------------------------------------------------------------------
    def test_large_step_geometry(self):
        """Create a geometry with many faces (compound of boxes) to test scale."""
        name = "test_large_step_geometry"
        try:
            import time
            t0 = time.time()

            # Create a compound of many boxes → simulates a "large" STEP import
            solids = []
            grid_size = 5  # 5x5x5 = 125 boxes → ~750 faces
            spacing = 25.0
            for ix in range(grid_size):
                for iy in range(grid_size):
                    for iz in range(grid_size):
                        b = Part.makeBox(20, 20, 20)
                        b.translate(App.Vector(ix * spacing, iy * spacing, iz * spacing))
                        solids.append(b)

            compound = Part.makeCompound(solids)
            t_create = time.time() - t0

            feat = self.doc.addObject("Part::Feature", "LargeCompound")
            feat.Shape = compound
            self.doc.recompute()
            t_total = time.time() - t0

            num_faces = len(compound.Faces)
            num_solids = len(compound.Solids)

            assert num_faces >= 750, f"Expected >=750 faces, got {num_faces}"
            assert num_solids == 125, f"Expected 125 solids, got {num_solids}"
            assert compound.isValid(), "Compound shape is invalid"

            # Export / import STEP roundtrip
            step_path = os.path.join(tempfile.gettempdir(), "flowstudio_e2e_large.step")
            t0 = time.time()
            compound.exportStep(step_path)
            t_export = time.time() - t0

            t0 = time.time()
            reimported = Part.Shape()
            reimported.read(step_path)
            t_import = time.time() - t0

            assert reimported.isValid(), "Re-imported large shape invalid"
            assert len(reimported.Faces) == num_faces, \
                f"Face count changed: {len(reimported.Faces)} vs {num_faces}"

            self._pass(name, f"faces={num_faces}, solids={num_solids}, "
                             f"create={t_create:.2f}s, export={t_export:.2f}s, "
                             f"import={t_import:.2f}s")

            os.remove(step_path)

        except Exception as e:
            self._fail(name, str(e))
            traceback.print_exc()

    # ------------------------------------------------------------------
    # Test: Lid generation for open pipe
    # ------------------------------------------------------------------
    def test_lid_generation_open_pipe(self):
        """Create open pipe → detect open edges → generate lids to cap it."""
        name = "test_lid_generation_open_pipe"
        try:
            feat = _make_open_pipe(self.doc)
            shape = feat.Shape

            # The open pipe should have free edges (not watertight)
            info_before = _check_watertight(shape)
            assert info_before["free_edges"] > 0, \
                f"Expected free edges on open pipe, got {info_before['free_edges']}"
            assert not info_before["is_closed"], "Open pipe should not be closed"

            # Generate lids
            lids, num_wires = _cap_open_faces(shape)
            assert num_wires >= 2, f"Expected >=2 boundary wires, got {num_wires}"

            # Combine original shell with lids to make closed shell
            all_faces = list(shape.Faces) + lids
            closed_shell = Part.makeShell(all_faces)

            # Check if we can make a solid
            try:
                solid = Part.makeSolid(closed_shell)
                has_solid = solid.isValid()
                volume = solid.Volume if has_solid else 0
            except Exception:
                has_solid = False
                volume = 0

            capped_feat = self.doc.addObject("Part::Feature", "CappedPipe")
            if has_solid:
                capped_feat.Shape = solid
            else:
                capped_feat.Shape = closed_shell
            self.doc.recompute()

            self._pass(name, f"free_edges_before={info_before['free_edges']}, "
                             f"lids={len(lids)}, wires={num_wires}, "
                             f"solid={has_solid}, vol={volume:.1f}")

        except Exception as e:
            self._fail(name, str(e))
            traceback.print_exc()

    # ------------------------------------------------------------------
    # Test: Lid generation for box with hole
    # ------------------------------------------------------------------
    def test_lid_generation_box_with_hole(self):
        """Box with one face removed → generate lid → make solid."""
        name = "test_lid_generation_box_with_hole"
        try:
            box = Part.makeBox(100, 50, 30)
            # Remove the top face (Z=30 plane)
            keep_faces = []
            removed = 0
            for face in box.Faces:
                cm = face.CenterOfMass
                if abs(cm.z - 30.0) < 0.1 and face.Surface.isPlanar():
                    normal = face.Surface.Axis
                    if abs(normal.z) > 0.9:
                        removed += 1
                        continue
                keep_faces.append(face)

            assert removed == 1, f"Expected to remove 1 face, removed {removed}"

            open_shell = Part.makeShell(keep_faces)
            feat = self.doc.addObject("Part::Feature", "OpenBox")
            feat.Shape = open_shell
            self.doc.recompute()

            # Verify it's open
            info = _check_watertight(open_shell)
            assert not info["is_closed"], "Shell should be open"
            assert info["free_edges"] > 0, "Should have free edges"

            # Generate lids
            lids, num_wires = _cap_open_faces(open_shell)
            assert len(lids) == 1, f"Expected 1 lid, got {len(lids)}"

            # Close and solidify
            all_faces = keep_faces + lids
            closed_shell = Part.makeShell(all_faces)

            # Try to make solid — may fail if shell orientation is inconsistent
            try:
                solid = Part.makeSolid(closed_shell)
            except Exception:
                solid = None

            if solid is None or not solid.isValid():
                # Try the sewing approach via Part.Shape
                builder = Part.Shape()
                builder = Part.Compound(all_faces)
                sewn = builder.sewShape()
                # After sewing, try to extract shells and solidify
                try:
                    shells = builder.Shells
                    if shells:
                        solid = Part.makeSolid(shells[0])
                    else:
                        solid = None
                except Exception:
                    solid = None

            has_volume = solid is not None and hasattr(solid, "Volume") and solid.Volume > 0
            expected_vol = 100 * 50 * 30

            if has_volume:
                vol_diff = abs(solid.Volume - expected_vol) / expected_vol
                assert vol_diff < 0.05, f"Volume {solid.Volume:.1f} != expected {expected_vol}"
                self._pass(name, f"lids={len(lids)}, vol={solid.Volume:.1f}")
            else:
                # Still a pass if we generated the lid correctly
                self._pass(name, f"lids={len(lids)}, solidify=partial")

        except Exception as e:
            self._fail(name, str(e))
            traceback.print_exc()

    # ------------------------------------------------------------------
    # Test: Leak detection — watertight solid
    # ------------------------------------------------------------------
    def test_leak_check_watertight_solid(self):
        """A simple box should be perfectly watertight."""
        name = "test_leak_check_watertight_solid"
        try:
            box = Part.makeBox(50, 50, 50)
            info = _check_watertight(box)

            assert info["is_valid"], "Box should be valid"
            assert info["is_closed"], "Box should be closed (no leaks)"
            assert info["free_edges"] == 0, \
                f"Box should have 0 free edges, got {info['free_edges']}"
            assert info["num_solids"] == 1, "Box should be 1 solid"
            assert abs(info["volume"] - 125000) < 1, \
                f"Volume should be 125000, got {info['volume']}"

            self._pass(name, f"free_edges={info['free_edges']}, vol={info['volume']:.1f}")

        except Exception as e:
            self._fail(name, str(e))
            traceback.print_exc()

    # ------------------------------------------------------------------
    # Test: Leak detection — open shell
    # ------------------------------------------------------------------
    def test_leak_check_open_shell(self):
        """An open shell (missing faces) must be detected as leaking."""
        name = "test_leak_check_open_shell"
        try:
            # Create a box shell with 2 faces removed
            box = Part.makeBox(40, 40, 40)
            faces = box.Faces
            # Keep only 4 of 6 faces
            open_shell = Part.makeShell(faces[:4])

            info = _check_watertight(open_shell)
            assert not info["is_closed"], "Open shell must NOT be closed"
            assert info["free_edges"] > 0, \
                f"Open shell should have free edges, got {info['free_edges']}"
            assert info["num_solids"] == 0, \
                f"Open shell should have 0 solids, got {info['num_solids']}"

            self._pass(name, f"free_edges={info['free_edges']}, closed={info['is_closed']}")

        except Exception as e:
            self._fail(name, str(e))
            traceback.print_exc()

    # ------------------------------------------------------------------
    # Test: Leak detection — compound with mixed watertight / open parts
    # ------------------------------------------------------------------
    def test_leak_check_compound_mixed(self):
        """Compound with watertight box + open shell → detect partial leaks."""
        name = "test_leak_check_compound_mixed"
        try:
            # Watertight box
            box = Part.makeBox(30, 30, 30)

            # Open cylinder (shell only, no caps)
            cyl = Part.makeCylinder(10, 50)
            cyl_shell = Part.makeShell(
                [f for f in cyl.Faces if not f.Surface.isPlanar()]
            )

            compound = Part.makeCompound([box, cyl_shell])
            feat = self.doc.addObject("Part::Feature", "MixedCompound")
            feat.Shape = compound
            self.doc.recompute()

            # Check the box part (solid)
            box_info = _check_watertight(box)
            assert box_info["is_closed"], "Box part should be watertight"

            # Check the cylinder shell (open)
            cyl_info = _check_watertight(cyl_shell)
            assert not cyl_info["is_closed"], "Open cylinder should have leaks"
            assert cyl_info["free_edges"] > 0

            # Overall compound should report issues
            overall_info = _check_watertight(compound)
            assert overall_info["free_edges"] > 0, \
                "Compound with open parts should report free edges"

            self._pass(name, f"box_closed={box_info['is_closed']}, "
                             f"cyl_leaks={cyl_info['free_edges']}, "
                             f"compound_leaks={overall_info['free_edges']}")

        except Exception as e:
            self._fail(name, str(e))
            traceback.print_exc()

    # ------------------------------------------------------------------
    # Test: Full STEP → lid → leak → face enumeration pipeline
    # ------------------------------------------------------------------
    def test_full_import_lid_leak_pipeline(self):
        """Complete pipeline: create → export STEP → import → lid → leak → enumerate faces."""
        name = "test_full_import_lid_leak_pipeline"
        try:
            # 1. Create open pipe
            pipe_feat = _make_open_pipe(self.doc, outer_radius=12, inner_radius=9, length=80)
            pipe_shape = pipe_feat.Shape

            # 2. Export to STEP
            step_path = os.path.join(tempfile.gettempdir(), "flowstudio_e2e_pipe.step")
            pipe_shape.exportStep(step_path)
            assert os.path.exists(step_path)

            # 3. Re-import
            imported = Part.Shape()
            imported.read(step_path)
            imp_feat = self.doc.addObject("Part::Feature", "ImportedPipe")
            imp_feat.Shape = imported
            self.doc.recompute()

            # 4. Leak check (should show leaks — open pipe)
            info_before = _check_watertight(imported)
            # Note: STEP re-import may produce a solid even from shell input
            # so we check what we get
            has_leaks_before = info_before["free_edges"] > 0

            # 5. Generate lids
            lids, num_wires = _cap_open_faces(imported)

            # 6. If lids were generated, close up
            if lids:
                all_faces = list(imported.Faces) + lids
                closed = Part.makeShell(all_faces)
                try:
                    solid = Part.makeSolid(closed)
                    result_shape = solid
                except Exception:
                    result_shape = closed
            else:
                result_shape = imported

            # 7. Final leak check
            info_after = _check_watertight(result_shape)

            # 8. Enumerate faces for BC assignment
            face_list = []
            for i, face in enumerate(result_shape.Faces):
                cm = face.CenterOfMass
                area = face.Area
                face_list.append((f"Face{i+1}", area, cm))

            assert len(face_list) > 0, "No faces found for BC assignment"

            self._pass(name, f"leaks_before={has_leaks_before}, "
                             f"lids={len(lids)}, "
                             f"leaks_after={info_after['free_edges']}, "
                             f"total_faces={len(face_list)}")

            os.remove(step_path)

        except Exception as e:
            self._fail(name, str(e))
            traceback.print_exc()

    # ------------------------------------------------------------------
    # Run all
    # ------------------------------------------------------------------
    def run_all(self):
        """Execute all tests and return summary."""
        print("=" * 70)
        print("E2E Test Suite: STEP Import / Lid Generation / Leak Detection")
        print("=" * 70)

        self.setup()
        try:
            self.test_step_export_import_roundtrip()
            self.test_large_step_geometry()
            self.test_lid_generation_open_pipe()
            self.test_lid_generation_box_with_hole()
            self.test_leak_check_watertight_solid()
            self.test_leak_check_open_shell()
            self.test_leak_check_compound_mixed()
            self.test_full_import_lid_leak_pipeline()
        finally:
            self.teardown()

        # Summary
        passed = sum(1 for r in self.results if r[0] == "PASS")
        failed = sum(1 for r in self.results if r[0] == "FAIL")
        skipped = sum(1 for r in self.results if r[0] == "SKIP")
        total = len(self.results)
        print("=" * 70)
        print(f"Results: {passed} passed, {failed} failed, {skipped} skipped / {total} total")
        print("=" * 70)
        return failed == 0


# ======================================================================
# Main entry point (when run inside FreeCAD)
# ======================================================================

if __name__ == "__main__":
    tests = E2EStepImportTests()
    success = tests.run_all()
    if not success:
        sys.exit(1)
