# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""GMSH mesh generation utilities for FlowStudio.

Wraps the GMSH Python API to create CFD-quality meshes from FreeCAD
geometry, with boundary-layer inflation, local refinement regions,
and multiple export formats (OpenFOAM polyMesh, .msh, .vtk, .stl).
"""

import os
import math
import tempfile

from flow_studio.taskpanels.task_fluid_material import MATERIALS_DB

try:
    import gmsh
    HAS_GMSH = True
except ImportError:
    HAS_GMSH = False


FLUID_MATERIAL_PRESETS = {
    name: {
        "density": properties["Density"],
        "dynamic_viscosity": properties["DynamicViscosity"],
        "kinematic_viscosity": properties["KinematicViscosity"],
        "specific_heat": properties["SpecificHeat"],
        "thermal_conductivity": properties["ThermalConductivity"],
        "prandtl_number": properties["PrandtlNumber"],
    }
    for name, properties in MATERIALS_DB.items()
    if all(
        key in properties
        for key in (
            "Density",
            "DynamicViscosity",
            "KinematicViscosity",
            "SpecificHeat",
            "ThermalConductivity",
            "PrandtlNumber",
        )
    )
}


def check_gmsh():
    """Return True if the GMSH Python module is available."""
    return HAS_GMSH


def generate_mesh(mesh_obj, geometry_objects, output_dir=None):
    """Generate a CFD mesh from *mesh_obj* properties and geometry.

    Parameters
    ----------
    mesh_obj : FreeCAD FeaturePython
        The MeshGmsh document object with mesh settings.
    geometry_objects : list[FreeCAD.DocumentObject]
        Shape objects to mesh (bodies, compounds, etc.).
    output_dir : str or None
        Directory for output files.  Defaults to a temp directory.

    Returns
    -------
    dict with keys ``mesh_file``, ``num_cells``, ``num_faces``, ``num_points``.
    """
    import FreeCAD  # noqa: lazy import for standalone testability

    if not HAS_GMSH:
        raise RuntimeError(
            "GMSH Python API not found.  Install it via: pip install gmsh"
        )

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="FlowStudio_mesh_")

    # Export geometry to a temporary STEP file for GMSH import
    step_path = os.path.join(output_dir, "geometry.step")
    _export_step(geometry_objects, step_path)

    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.model.add("FlowStudioMesh")

    try:
        # Import STEP
        gmsh.model.occ.importShapes(step_path)
        gmsh.model.occ.synchronize()

        # Global mesh sizing
        char_len = mesh_obj.CharacteristicLength
        gmsh.option.setNumber("Mesh.CharacteristicLengthMin",
                              mesh_obj.MinElementSize)
        gmsh.option.setNumber("Mesh.CharacteristicLengthMax",
                              mesh_obj.MaxElementSize)
        gmsh.option.setNumber("Mesh.CharacteristicLengthFactor", 1.0)

        # Growth rate
        gmsh.option.setNumber("Mesh.CharacteristicLengthExtendFromBoundary",
                              1)
        # gmsh doesn't have a direct "growth rate" — approximate via field
        _setup_size_fields(mesh_obj, char_len)

        # Algorithm
        algo_map = {"Delaunay": 1, "Frontal": 4, "HXT": 10, "MMG3D": 7}
        gmsh.option.setNumber(
            "Mesh.Algorithm3D",
            algo_map.get(mesh_obj.Algorithm3D, 1),
        )

        # Element order
        order = 2 if "2nd" in mesh_obj.ElementOrder else 1
        gmsh.option.setNumber("Mesh.ElementOrder", order)

        # Generate 3-D mesh
        gmsh.model.mesh.generate(3)

        # Retrieve statistics
        node_tags, _, _ = gmsh.model.mesh.getNodes()
        elem_types, elem_tags, _ = gmsh.model.mesh.getElements(dim=3)
        num_points = len(node_tags)
        num_cells = sum(len(t) for t in elem_tags)

        # Export
        mesh_file = _export_mesh(mesh_obj, output_dir)

        # Write stats back to the document object
        mesh_obj.NumCells = num_cells
        mesh_obj.NumPoints = num_points

        return {
            "mesh_file": mesh_file,
            "num_cells": num_cells,
            "num_faces": 0,  # GMSH doesn't directly report this
            "num_points": num_points,
        }

    finally:
        gmsh.finalize()


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _export_step(objects, path):
    """Export FreeCAD shape objects to STEP."""
    import Part  # FreeCAD Part module
    shapes = []
    for obj in objects:
        if hasattr(obj, "Shape"):
            shapes.append(obj.Shape)
    if not shapes:
        raise RuntimeError("No shapes to mesh.")
    compound = Part.makeCompound(shapes)
    compound.exportStep(path)


def _setup_size_fields(mesh_obj, char_len):
    """Set up GMSH background size fields for growth rate."""
    # A MathEval field with a simple distance-based growth
    growth = mesh_obj.GrowthRate
    if growth > 1.0:
        # Create a distance field from all surfaces
        f_dist = gmsh.model.mesh.field.add("Distance")
        surfaces = gmsh.model.getEntities(dim=2)
        surf_tags = [s[1] for s in surfaces]
        gmsh.model.mesh.field.setNumbers(f_dist, "SurfacesList", surf_tags)

        # Threshold field: near surface = min size, far = max size
        f_thresh = gmsh.model.mesh.field.add("Threshold")
        gmsh.model.mesh.field.setNumber(f_thresh, "InField", f_dist)
        gmsh.model.mesh.field.setNumber(
            f_thresh, "SizeMin", mesh_obj.MinElementSize)
        gmsh.model.mesh.field.setNumber(
            f_thresh, "SizeMax", mesh_obj.MaxElementSize)
        gmsh.model.mesh.field.setNumber(
            f_thresh, "DistMin", char_len * 0.5)
        gmsh.model.mesh.field.setNumber(
            f_thresh, "DistMax", char_len * 10)

        gmsh.model.mesh.field.setAsBackgroundMesh(f_thresh)
        gmsh.option.setNumber(
            "Mesh.MeshSizeExtendFromBoundary", 0)
        gmsh.option.setNumber(
            "Mesh.MeshSizeFromPoints", 0)
        gmsh.option.setNumber(
            "Mesh.MeshSizeFromCurvature", 0)


def _export_mesh(mesh_obj, output_dir):
    """Export the generated mesh in the requested format."""
    fmt = mesh_obj.MeshFormat

    if "SU2" in fmt:
        su2_path = os.path.join(output_dir, "mesh.su2")
        gmsh.write(su2_path)
        return su2_path

    elif "OpenFOAM" in fmt:
        # Write GMSH .msh first, then convert
        msh_path = os.path.join(output_dir, "mesh.msh")
        gmsh.write(msh_path)
        # Attempt gmshToFoam conversion
        poly_dir = os.path.join(output_dir, "constant", "polyMesh")
        os.makedirs(poly_dir, exist_ok=True)
        try:
            import subprocess
            subprocess.run(
                ["gmshToFoam", msh_path, "-case", output_dir],
                check=True, capture_output=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            import FreeCAD as _fc
            _fc.Console.PrintWarning(
                f"FlowStudio: gmshToFoam conversion failed ({exc}). "
                f"Raw .msh saved at {msh_path}\n"
            )
        return msh_path

    elif "VTK" in fmt:
        vtk_path = os.path.join(output_dir, "mesh.vtk")
        gmsh.write(vtk_path)
        return vtk_path

    elif "STL" in fmt:
        stl_path = os.path.join(output_dir, "mesh.stl")
        gmsh.write(stl_path)
        return stl_path

    else:
        # Default GMSH .msh
        msh_path = os.path.join(output_dir, "mesh.msh")
        gmsh.write(msh_path)
        return msh_path


def add_boundary_layer(mesh_obj, bl_obj):
    """Insert boundary-layer (inflation) mesh using GMSH BoundaryLayer field.

    Parameters
    ----------
    mesh_obj : MeshGmsh document object
    bl_obj : BoundaryLayer document object
    """
    if not HAS_GMSH:
        return

    # Gather surface tags from bl_obj.References
    surf_tags = []
    if hasattr(bl_obj, "References") and bl_obj.References:
        # In FreeCAD, References is a list of (obj, [subname, ...])
        for ref_obj, sub_list in bl_obj.References:
            for sub in sub_list:
                if sub.startswith("Face"):
                    # Extract face index (Face1 → GMSH tag mapping TBD)
                    idx = int(sub.replace("Face", ""))
                    surf_tags.append(idx)

    if not surf_tags:
        # Apply to all surfaces
        surfaces = gmsh.model.getEntities(dim=2)
        surf_tags = [s[1] for s in surfaces]

    f_bl = gmsh.model.mesh.field.add("BoundaryLayer")
    gmsh.model.mesh.field.setNumbers(f_bl, "SurfacesList", surf_tags)
    gmsh.model.mesh.field.setNumber(
        f_bl, "Size", bl_obj.FirstLayerHeight)
    gmsh.model.mesh.field.setNumber(
        f_bl, "Ratio", bl_obj.ExpansionRatio)
    gmsh.model.mesh.field.setNumber(
        f_bl, "NbLayers", bl_obj.NumLayers)

    return f_bl


def estimate_y_plus_height(velocity, length, nu, y_plus_target=1.0):
    """Estimate first cell height for a target y+.

    Uses flat-plate turbulent BL correlation:
        Cf = 0.058 * Re_L^(-0.2)
        tau_w = 0.5 * Cf * rho * U^2
        u_tau = sqrt(tau_w / rho)
        y = y+ * nu / u_tau

    Parameters
    ----------
    velocity : float  – free-stream velocity [m/s]
    length : float    – characteristic length [m]
    nu : float        – kinematic viscosity [m²/s]
    y_plus_target : float – desired y+

    Returns
    -------
    float – first cell height [m]
    """
    Re = velocity * length / nu
    if Re < 1:
        return 1e-3  # fallback
    Cf = 0.058 * Re ** (-0.2)
    tau_w_over_rho = 0.5 * Cf * velocity ** 2
    u_tau = math.sqrt(abs(tau_w_over_rho))
    if u_tau < 1e-12:
        return 1e-3
    return y_plus_target * nu / u_tau


def estimate_first_layer_height(
    velocity, length, kinematic_viscosity, y_plus_target=1.0
):
    """Compatibility wrapper for production-readiness mesh sizing tests."""

    return estimate_y_plus_height(
        velocity=velocity,
        length=length,
        nu=kinematic_viscosity,
        y_plus_target=y_plus_target,
    )
