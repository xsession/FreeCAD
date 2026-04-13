# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Post-processing utilities for FlowStudio.

Provides VTK-based result loading, field extraction, and
force/moment computation on surfaces.
"""

import os
import FreeCAD

try:
    import vtk
    from vtk.util.numpy_support import vtk_to_numpy
    HAS_VTK = True
except ImportError:
    HAS_VTK = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


def check_vtk():
    return HAS_VTK


def load_vtk_result(filepath):
    """Load a VTK/VTU/foam result file and return the vtkDataSet.

    Supported formats: .vtk, .vtu, .vtp, .foam (OpenFOAM reader).
    """
    if not HAS_VTK:
        raise RuntimeError("VTK Python module not found.")

    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".vtu":
        reader = vtk.vtkXMLUnstructuredGridReader()
    elif ext == ".vtp":
        reader = vtk.vtkXMLPolyDataReader()
    elif ext == ".vtk":
        reader = vtk.vtkUnstructuredGridReader()
    elif ext == ".foam":
        reader = vtk.vtkOpenFOAMReader()
        reader.SetCreateCellToPoint(True)
        reader.SetDecomposePolyhedra(True)
    else:
        raise ValueError(f"Unsupported result format: {ext}")

    reader.SetFileName(filepath)
    reader.Update()
    return reader.GetOutput()


def get_available_fields(dataset):
    """Return dict of {name: num_components} for point and cell data."""
    fields = {}
    if dataset is None:
        return fields
    for i in range(dataset.GetPointData().GetNumberOfArrays()):
        arr = dataset.GetPointData().GetArray(i)
        fields[arr.GetName()] = arr.GetNumberOfComponents()
    for i in range(dataset.GetCellData().GetNumberOfArrays()):
        arr = dataset.GetCellData().GetArray(i)
        if arr.GetName() not in fields:
            fields[arr.GetName()] = arr.GetNumberOfComponents()
    return fields


def extract_field(dataset, field_name):
    """Extract a named field as a numpy array.

    Returns
    -------
    numpy.ndarray of shape (N,) or (N, 3)
    """
    if not HAS_NUMPY:
        raise RuntimeError("NumPy not found.")

    arr = dataset.GetPointData().GetArray(field_name)
    if arr is None:
        arr = dataset.GetCellData().GetArray(field_name)
    if arr is None:
        raise KeyError(f"Field '{field_name}' not found in dataset.")
    return vtk_to_numpy(arr)


def compute_field_range(dataset, field_name):
    """Return (min, max) of a scalar field or magnitude of a vector field."""
    data = extract_field(dataset, field_name)
    if data.ndim == 2:
        # Vector – compute magnitude
        mag = np.sqrt(np.sum(data ** 2, axis=1))
        return float(mag.min()), float(mag.max())
    return float(data.min()), float(data.max())


def slice_plane(dataset, origin, normal):
    """Cut the dataset with a plane and return the slice polydata."""
    if not HAS_VTK:
        raise RuntimeError("VTK not found.")
    plane = vtk.vtkPlane()
    plane.SetOrigin(*origin)
    plane.SetNormal(*normal)
    cutter = vtk.vtkCutter()
    cutter.SetInputData(dataset)
    cutter.SetCutFunction(plane)
    cutter.Update()
    return cutter.GetOutput()


def streamlines(dataset, seed_center, seed_radius, num_seeds=50,
                max_length=1000.0, field_name="U"):
    """Compute streamlines from a spherical seed region.

    Returns vtkPolyData with streamline geometry.
    """
    if not HAS_VTK:
        raise RuntimeError("VTK not found.")

    # Seed source
    seed = vtk.vtkPointSource()
    seed.SetCenter(*seed_center)
    seed.SetRadius(seed_radius)
    seed.SetNumberOfPoints(num_seeds)

    tracer = vtk.vtkStreamTracer()
    tracer.SetInputData(dataset)
    tracer.SetSourceConnection(seed.GetOutputPort())
    tracer.SetMaximumPropagation(max_length)
    tracer.SetIntegrationDirectionToForward()
    tracer.SetComputeVorticity(True)

    # Use the velocity field
    dataset.GetPointData().SetActiveVectors(field_name)
    tracer.Update()
    return tracer.GetOutput()


def compute_surface_force(dataset, surface_ids=None, rho=1.225,
                          p_field="p", u_field="U", nu=1.48e-5):
    """Compute force vector on selected surface patches.

    For OpenFOAM results: integrates pressure + viscous forces.
    Returns dict with keys ``force`` [Fx, Fy, Fz], ``moment`` [Mx, My, Mz].
    """
    if not HAS_VTK or not HAS_NUMPY:
        raise RuntimeError("VTK + NumPy required for force computation.")

    # Extract surface
    if surface_ids is not None:
        extract = vtk.vtkExtractSelection()
        sel = vtk.vtkSelection()
        sel_node = vtk.vtkSelectionNode()
        sel_node.SetFieldType(vtk.vtkSelectionNode.CELL)
        sel_node.SetContentType(vtk.vtkSelectionNode.INDICES)
        ids = vtk.vtkIdTypeArray()
        for sid in surface_ids:
            ids.InsertNextValue(sid)
        sel_node.SetSelectionList(ids)
        sel.AddNode(sel_node)
        extract.SetInputData(0, dataset)
        extract.SetInputData(1, sel)
        extract.Update()
        surf_data = extract.GetOutput()
    else:
        # Use geometry filter to get the surface
        geom = vtk.vtkGeometryFilter()
        geom.SetInputData(dataset)
        geom.Update()
        surf_data = geom.GetOutput()

    normals_filter = vtk.vtkPolyDataNormals()
    normals_filter.SetInputData(surf_data)
    normals_filter.ComputeCellNormalsOn()
    normals_filter.Update()
    surface = normals_filter.GetOutput()

    # Pressure contribution
    p_arr = surface.GetCellData().GetArray(p_field)
    n_arr = surface.GetCellData().GetArray("Normals")

    force = np.zeros(3)
    if p_arr is not None and n_arr is not None:
        pressures = vtk_to_numpy(p_arr)
        normals = vtk_to_numpy(n_arr)

        # Cell areas
        for i in range(surface.GetNumberOfCells()):
            cell = surface.GetCell(i)
            area = _cell_area(cell)
            force += pressures[i] * normals[i] * area * rho

    return {
        "force": force.tolist(),
        "moment": [0.0, 0.0, 0.0],  # simplified – full moment needs ref point
    }


def _cell_area(cell):
    """Compute the area of a VTK cell (triangle or quad)."""
    pts = cell.GetPoints()
    n = pts.GetNumberOfPoints()
    if n == 3:
        p0 = np.array(pts.GetPoint(0))
        p1 = np.array(pts.GetPoint(1))
        p2 = np.array(pts.GetPoint(2))
        return 0.5 * np.linalg.norm(np.cross(p1 - p0, p2 - p0))
    elif n == 4:
        p0 = np.array(pts.GetPoint(0))
        p1 = np.array(pts.GetPoint(1))
        p2 = np.array(pts.GetPoint(2))
        p3 = np.array(pts.GetPoint(3))
        a1 = 0.5 * np.linalg.norm(np.cross(p1 - p0, p2 - p0))
        a2 = 0.5 * np.linalg.norm(np.cross(p2 - p0, p3 - p0))
        return a1 + a2
    return 0.0
