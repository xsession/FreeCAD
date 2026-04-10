# ***************************************************************************
# *   Copyright (c) 2026 FreeCAD contributors                              *
# *                                                                         *
# *   This file is part of the FreeCAD CAx development system.              *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

"""ParaView bridge for FreeCAD FEM module.

Provides functionality to:
- Find ParaView installation on the system
- Export FEM results and meshes to VTK format for ParaView
- Launch ParaView with exported data
- Generate ParaView Python state files for automated visualization
- Create pvpython batch scripts for headless post-processing
"""

__title__ = "FreeCAD FEM ParaView Bridge"
__author__ = "FreeCAD contributors"
__url__ = "https://www.freecad.org"

import os
import sys
import shutil
import subprocess
import tempfile

import FreeCAD
from FreeCAD import Console


# --- ParaView discovery ---

_PARAVIEW_PATHS_WINDOWS = [
    r"C:\Program Files\ParaView*\bin\paraview.exe",
    r"C:\Program Files (x86)\ParaView*\bin\paraview.exe",
]

_PARAVIEW_PATHS_LINUX = [
    "/usr/bin/paraview",
    "/usr/local/bin/paraview",
    "/opt/ParaView*/bin/paraview",
    "/snap/bin/paraview",
]

_PARAVIEW_PATHS_MACOS = [
    "/Applications/ParaView*.app/Contents/MacOS/paraview",
    "/usr/local/bin/paraview",
]

_PVPYTHON_NAMES = ["pvpython", "pvpython.exe"]


def _get_pref_group():
    """Get the FEM ParaView preferences parameter group."""
    return FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Fem/ParaView")


def _glob_first(pattern):
    """Return the first file matching a glob pattern, or None."""
    import glob
    matches = sorted(glob.glob(pattern), reverse=True)  # newest version first
    return matches[0] if matches else None


def find_paraview_binary():
    """Find the ParaView executable on the system.

    Returns the path to the paraview binary, or empty string if not found.
    Checks user preference first, then searches standard install locations.
    """
    # Check user preference
    prefs = _get_pref_group()
    custom_path = prefs.GetString("ParaViewBinary", "")
    if custom_path and os.path.isfile(custom_path):
        return custom_path

    # Check PATH
    pv = shutil.which("paraview")
    if pv:
        return pv

    # Platform-specific search
    if sys.platform == "win32":
        candidates = _PARAVIEW_PATHS_WINDOWS
    elif sys.platform == "darwin":
        candidates = _PARAVIEW_PATHS_MACOS
    else:
        candidates = _PARAVIEW_PATHS_LINUX

    for pattern in candidates:
        found = _glob_first(pattern)
        if found:
            return found

    return ""


def find_pvpython_binary():
    """Find the pvpython executable (ParaView's Python interpreter).

    Returns the path to pvpython, or empty string if not found.
    """
    prefs = _get_pref_group()
    custom = prefs.GetString("PvPythonBinary", "")
    if custom and os.path.isfile(custom):
        return custom

    # Check PATH
    for name in _PVPYTHON_NAMES:
        pv = shutil.which(name)
        if pv:
            return pv

    # Try to find it next to paraview binary
    pv_bin = find_paraview_binary()
    if pv_bin:
        pv_dir = os.path.dirname(pv_bin)
        for name in _PVPYTHON_NAMES:
            candidate = os.path.join(pv_dir, name)
            if os.path.isfile(candidate):
                return candidate

    return ""


def is_paraview_available():
    """Check if ParaView is installed and available."""
    return bool(find_paraview_binary())


def get_paraview_version():
    """Get the ParaView version string, or None if not available."""
    pv_bin = find_paraview_binary()
    if not pv_bin:
        return None
    try:
        result = subprocess.run(
            [pv_bin, "--version"],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.strip().splitlines():
            if "paraview" in line.lower() or line.strip():
                return line.strip()
        return result.stdout.strip() or None
    except (subprocess.SubprocessError, OSError):
        return None


# --- VTK export helpers ---

def _get_export_dir(analysis=None):
    """Get or create the export directory for ParaView data.

    Uses the analysis's working directory if available, otherwise a temp dir.
    """
    prefs = _get_pref_group()
    custom_dir = prefs.GetString("ExportDirectory", "")
    if custom_dir and os.path.isdir(custom_dir):
        return custom_dir

    if analysis:
        # Try to use the solver working directory
        for obj in analysis.Group:
            if obj.isDerivedFrom("Fem::FemSolverObject"):
                if hasattr(obj, "WorkingDir") and obj.WorkingDir:
                    wdir = obj.WorkingDir
                    if os.path.isdir(wdir):
                        pv_dir = os.path.join(wdir, "paraview_export")
                        os.makedirs(pv_dir, exist_ok=True)
                        return pv_dir

    # Use document directory
    doc = FreeCAD.ActiveDocument
    if doc and doc.FileName:
        doc_dir = os.path.dirname(doc.FileName)
        pv_dir = os.path.join(doc_dir, "paraview_export")
        os.makedirs(pv_dir, exist_ok=True)
        return pv_dir

    # Fallback to temp
    pv_dir = os.path.join(tempfile.gettempdir(), "freecad_paraview")
    os.makedirs(pv_dir, exist_ok=True)
    return pv_dir


def export_result_vtk(result_obj, export_dir=None):
    """Export a FEM result object to VTK format.

    Args:
        result_obj: A Fem::FemResultObject or Fem::FemPostPipeline
        export_dir: Directory for export (auto-detected if None)

    Returns:
        Path to the exported .vtk file, or None on failure.
    """
    import Fem

    if export_dir is None:
        export_dir = _get_export_dir()

    name = result_obj.Name
    vtk_path = os.path.join(export_dir, f"{name}.vtk")

    try:
        if result_obj.isDerivedFrom("Fem::FemPostObject"):
            result_obj.writeVTK(vtk_path)
        elif result_obj.isDerivedFrom("Fem::FemResultObject"):
            Fem.writeResult(vtk_path, result_obj)
        else:
            Console.PrintError(
                f"ParaView export: unsupported object type {result_obj.TypeId}\n"
            )
            return None
        Console.PrintMessage(f"ParaView export: wrote {vtk_path}\n")
        return vtk_path
    except Exception as e:
        Console.PrintError(f"ParaView export failed: {e}\n")
        return None


def export_mesh_vtk(mesh_obj, export_dir=None):
    """Export a FEM mesh object to VTK format.

    Args:
        mesh_obj: A Fem::FemMeshObject
        export_dir: Directory for export (auto-detected if None)

    Returns:
        Path to the exported .vtk file, or None on failure.
    """
    import Fem

    if export_dir is None:
        export_dir = _get_export_dir()

    name = mesh_obj.Name
    vtk_path = os.path.join(export_dir, f"{name}.vtk")

    try:
        Fem.FemMesh.write(mesh_obj.FemMesh, vtk_path)
        Console.PrintMessage(f"ParaView export: wrote {vtk_path}\n")
        return vtk_path
    except Exception as e:
        Console.PrintError(f"ParaView mesh export failed: {e}\n")
        return None


def export_analysis_vtk(analysis, export_dir=None):
    """Export all results and mesh from an analysis to VTK.

    Returns a list of exported file paths.
    """
    if export_dir is None:
        export_dir = _get_export_dir(analysis)

    exported = []

    for obj in analysis.Group:
        if obj.isDerivedFrom("Fem::FemPostPipeline") or \
           obj.isDerivedFrom("Fem::FemResultObject"):
            path = export_result_vtk(obj, export_dir)
            if path:
                exported.append(path)
        elif obj.isDerivedFrom("Fem::FemMeshObject"):
            path = export_mesh_vtk(obj, export_dir)
            if path:
                exported.append(path)

    return exported


# --- ParaView launch ---

def launch_paraview(vtk_files=None, state_file=None):
    """Launch ParaView, optionally opening VTK files or a state file.

    Args:
        vtk_files: List of VTK file paths to open
        state_file: Path to a ParaView .pvsm state file

    Returns:
        subprocess.Popen object, or None on failure.
    """
    pv_bin = find_paraview_binary()
    if not pv_bin:
        Console.PrintError(
            "ParaView not found. Install ParaView or set the path in "
            "FEM preferences (Edit > Preferences > FEM > ParaView).\n"
        )
        return None

    cmd = [pv_bin]

    if state_file and os.path.isfile(state_file):
        cmd.extend(["--state", state_file])
    elif vtk_files:
        for f in vtk_files:
            if os.path.isfile(f):
                cmd.append(f)

    Console.PrintMessage(f"Launching ParaView: {' '.join(cmd)}\n")

    try:
        proc = subprocess.Popen(cmd)
        return proc
    except OSError as e:
        Console.PrintError(f"Failed to launch ParaView: {e}\n")
        return None


def open_in_paraview(result_obj, analysis=None):
    """Export a result object and open it in ParaView.

    Args:
        result_obj: FEM result or post pipeline object
        analysis: Optional analysis container

    Returns:
        True if ParaView was launched successfully.
    """
    export_dir = _get_export_dir(analysis)
    vtk_path = export_result_vtk(result_obj, export_dir)
    if not vtk_path:
        return False

    # Generate a ParaView state file with sensible defaults
    state_path = _generate_state_file(vtk_path, export_dir)

    if state_path:
        proc = launch_paraview(state_file=state_path)
    else:
        proc = launch_paraview(vtk_files=[vtk_path])

    return proc is not None


def open_analysis_in_paraview(analysis):
    """Export all analysis results and open in ParaView.

    Returns True if ParaView was launched successfully.
    """
    export_dir = _get_export_dir(analysis)
    vtk_files = export_analysis_vtk(analysis, export_dir)

    if not vtk_files:
        Console.PrintWarning("ParaView: no results to export from analysis.\n")
        return False

    return launch_paraview(vtk_files=vtk_files) is not None


# --- ParaView state file generation ---

def _generate_state_file(vtk_path, export_dir):
    """Generate a ParaView Python script for initializing visualization.

    Creates a .py script that ParaView can execute to set up proper
    visualization of the FEM results (color map, warp, etc.).

    Returns path to generated script, or None.
    """
    script_path = os.path.join(export_dir, "paraview_init.py")

    # Use os.path.normpath to handle path separators properly
    vtk_path_escaped = vtk_path.replace("\\", "/")

    script = f'''# ParaView initialization script generated by FreeCAD
# This script sets up visualization of FEM results

from paraview.simple import *

# --- Load data ---
reader = OpenDataFile("{vtk_path_escaped}")
if reader is None:
    raise RuntimeError("Failed to open: {vtk_path_escaped}")

# Enable all point arrays
reader.UpdatePipeline()

# --- Setup view ---
renderView = GetActiveViewOrCreate("RenderView")
renderView.ResetCamera()

# Set background
renderView.Background = [0.32, 0.34, 0.43]  # FreeCAD-like dark background

# --- Display data ---
display = Show(reader, renderView)

# Try to color by von Mises stress or displacement magnitude
pd = reader.GetPointDataInformation()
array_names = [pd.GetArray(i).GetName() for i in range(pd.GetNumberOfArrays())]

# Priority order for coloring
color_candidates = [
    "von Mises Stress",
    "vonMises",
    "Stress",
    "DisplacementVectors",
    "Displacement",
    "Temperature",
]

colored = False
for name in color_candidates:
    for arr_name in array_names:
        if name.lower() in arr_name.lower():
            ColorBy(display, ("POINTS", arr_name))
            display.RescaleTransferFunctionToDataRange(True, False)
            colored = True
            break
    if colored:
        break

if not colored and array_names:
    # Color by first available array
    ColorBy(display, ("POINTS", array_names[0]))
    display.RescaleTransferFunctionToDataRange(True, False)

# Show color legend
display.SetScalarBarVisibility(renderView, True)

# Set representation
display.SetRepresentationType("Surface")

# --- Warp by vector if displacement data exists ---
disp_arrays = [n for n in array_names if "displacement" in n.lower() or "disp" in n.lower()]
if disp_arrays:
    warp = WarpByVector(Input=reader)
    warp.Vectors = ["POINTS", disp_arrays[0]]
    warp.ScaleFactor = 1.0  # User can adjust

    warp_display = Show(warp, renderView)
    warp_display.Opacity = 0.6
    warp_display.SetRepresentationType("Surface With Edges")
    Hide(reader, renderView)

    # Color the warped display
    if colored:
        for name in color_candidates:
            for arr_name in array_names:
                if name.lower() in arr_name.lower():
                    ColorBy(warp_display, ("POINTS", arr_name))
                    warp_display.RescaleTransferFunctionToDataRange(True, False)
                    break
            break

    warp_display.SetScalarBarVisibility(renderView, True)

renderView.ResetCamera()
Render()

print("FreeCAD FEM results loaded in ParaView successfully.")
'''

    try:
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)
        return script_path
    except OSError as e:
        Console.PrintError(f"Failed to write ParaView script: {e}\n")
        return None


# --- pvpython batch processing ---

def run_pvpython_script(script_path, args=None):
    """Run a Python script using pvpython (ParaView's Python).

    Args:
        script_path: Path to the .py script
        args: Additional command-line arguments

    Returns:
        subprocess.CompletedProcess, or None on failure.
    """
    pvpy = find_pvpython_binary()
    if not pvpy:
        Console.PrintError(
            "pvpython not found. Ensure ParaView is installed and on PATH.\n"
        )
        return None

    cmd = [pvpy, script_path]
    if args:
        cmd.extend(args)

    Console.PrintMessage(f"Running pvpython: {' '.join(cmd)}\n")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            Console.PrintError(f"pvpython error:\n{result.stderr}\n")
        else:
            Console.PrintMessage(f"pvpython completed:\n{result.stdout}\n")
        return result
    except subprocess.TimeoutExpired:
        Console.PrintError("pvpython script timed out after 300 seconds.\n")
        return None
    except OSError as e:
        Console.PrintError(f"Failed to run pvpython: {e}\n")
        return None


def generate_screenshot(vtk_path, output_image, width=1920, height=1080):
    """Generate a screenshot of FEM results using pvpython.

    Args:
        vtk_path: Path to VTK data file
        output_image: Path for output image (.png)
        width, height: Image dimensions

    Returns:
        Path to generated image, or None on failure.
    """
    export_dir = os.path.dirname(vtk_path)
    script_path = os.path.join(export_dir, "paraview_screenshot.py")

    vtk_escaped = vtk_path.replace("\\", "/")
    img_escaped = output_image.replace("\\", "/")

    script = f'''from paraview.simple import *

reader = OpenDataFile("{vtk_escaped}")
reader.UpdatePipeline()

renderView = GetActiveViewOrCreate("RenderView")
renderView.ViewSize = [{width}, {height}]
renderView.Background = [0.32, 0.34, 0.43]

display = Show(reader, renderView)
display.SetRepresentationType("Surface")

pd = reader.GetPointDataInformation()
if pd.GetNumberOfArrays() > 0:
    arr_name = pd.GetArray(0).GetName()
    ColorBy(display, ("POINTS", arr_name))
    display.RescaleTransferFunctionToDataRange(True, False)
    display.SetScalarBarVisibility(renderView, True)

renderView.ResetCamera()
SaveScreenshot("{img_escaped}", renderView,
               ImageResolution=[{width}, {height}])
print("Screenshot saved: {img_escaped}")
'''

    try:
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)
    except OSError as e:
        Console.PrintError(f"Failed to write screenshot script: {e}\n")
        return None

    result = run_pvpython_script(script_path)
    if result and result.returncode == 0 and os.path.isfile(output_image):
        return output_image
    return None
