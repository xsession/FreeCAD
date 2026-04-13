# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Paraview script generator for FlowStudio measurement objects.

Generates standalone ``pvpython``-compatible Python scripts that:
  - Load OpenFOAM / VTK results
  - Create probes, cut-planes, iso-surfaces, threshold regions
  - Extract field values and compute statistics
  - Export CSV / VTK / screenshots

Usage from FlowStudio:
    from flow_studio.utils.paraview_script import ParaviewScriptBuilder
    builder = ParaviewScriptBuilder(analysis)
    script = builder.build()
    builder.write("evaluate.py")

Usage standalone:
    pvpython evaluate.py
"""

import os
import textwrap
import FreeCAD


# =====================================================================
# Helpers
# =====================================================================

def _mm_to_m(vec):
    """Convert FreeCAD mm vector to metres (OpenFOAM convention)."""
    return (vec.x / 1000.0, vec.y / 1000.0, vec.z / 1000.0)


def _vec_str(vec_tuple):
    """Format a 3-tuple as a Python list literal."""
    return f"[{vec_tuple[0]}, {vec_tuple[1]}, {vec_tuple[2]}]"


def _indent(text, n=4):
    return textwrap.indent(textwrap.dedent(text), " " * n)


# =====================================================================
# Script fragments
# =====================================================================

_HEADER = '''\
#!/usr/bin/env pvpython
# -*- coding: utf-8 -*-
# =========================================================================
#  FlowStudio – Auto-generated Paraview evaluation script
#  Generated from FreeCAD analysis: {analysis_label}
#  Date: {date}
# =========================================================================
#
#  Run with:   pvpython {script_name}
#  Or open in Paraview: Tools → Python Shell → Run Script
#
# =========================================================================

from paraview.simple import *
import os, csv, sys

paraview.simple._DisableFirstRenderCameraReset()

# ----- Configuration -----
CASE_DIR  = r"{case_dir}"
FOAM_FILE = os.path.join(CASE_DIR, "{foam_file}")
OUTPUT_DIR = os.path.join(CASE_DIR, "FlowStudio_Evaluation")
os.makedirs(OUTPUT_DIR, exist_ok=True)

TIME_SERIES = {time_series}   # True = evaluate all time steps
'''

_LOAD_OPENFOAM = '''\
# =========================================================================
# Load OpenFOAM case
# =========================================================================
print("Loading OpenFOAM case:", FOAM_FILE)
foam = OpenFOAMReader(registrationName="foam_case", FileName=FOAM_FILE)
foam.MeshRegions = ['internalMesh']
foam.CellArrays = {cell_arrays}

# Get available time steps
animationScene = GetAnimationScene()
animationScene.UpdateAnimationUsingDataTimeSteps()
time_steps = foam.TimestepValues if hasattr(foam, 'TimestepValues') else [0]
if not TIME_SERIES:
    time_steps = [time_steps[-1]]  # Only last time step

print(f"  Time steps to evaluate: {{len(time_steps)}}")
'''

_LOAD_VTK = '''\
# =========================================================================
# Load VTK result
# =========================================================================
print("Loading VTK results:", FOAM_FILE)
reader = LegacyVTKReader(registrationName="vtk_result", FileNames=[FOAM_FILE])
time_steps = [0]
'''


# =====================================================================
# Builder class
# =====================================================================

class ParaviewScriptBuilder:
    """Build a Paraview Python script from the analysis measurement objects."""

    def __init__(self, analysis):
        self.analysis = analysis
        self._sections = []

    # -----------------------------------------------------------------
    # Collect measurement objects from the analysis
    # -----------------------------------------------------------------

    def _get_objects(self, flow_type):
        results = []
        for obj in getattr(self.analysis, "Group", []):
            if getattr(obj, "FlowType", "") == flow_type:
                results.append(obj)
        return results

    @property
    def point_probes(self):
        return self._get_objects("FlowStudio::MeasurementPoint")

    @property
    def surface_measurements(self):
        return self._get_objects("FlowStudio::MeasurementSurface")

    @property
    def volume_measurements(self):
        return self._get_objects("FlowStudio::MeasurementVolume")

    # -----------------------------------------------------------------
    # Determine all referenced fields
    # -----------------------------------------------------------------

    def _all_fields(self):
        fields = set()
        for obj in (self.point_probes + self.surface_measurements
                    + self.volume_measurements):
            for f in getattr(obj, "SampleFields", []):
                fields.add(f)
        if not fields:
            fields = {"U", "p"}
        return sorted(fields)

    # -----------------------------------------------------------------
    # Header
    # -----------------------------------------------------------------

    def _build_header(self):
        import datetime
        case_dir = getattr(self.analysis, "CaseDir", "")
        if not case_dir:
            case_dir = os.path.join(os.path.expanduser("~"),
                                    "FlowStudio_Case")

        # Determine foam file
        result_fmt = "OpenFOAM"
        for obj in getattr(self.analysis, "Group", []):
            if getattr(obj, "FlowType", "") == "FlowStudio::PostPipeline":
                result_fmt = getattr(obj, "ResultFormat", "OpenFOAM")
                break

        foam_file = "case.foam" if result_fmt == "OpenFOAM" else "result.vtk"

        # Check if any measurement wants time series
        ts = False
        for obj in (self.point_probes + self.surface_measurements
                    + self.volume_measurements):
            if getattr(obj, "TimeSeries", False):
                ts = True
                break

        return _HEADER.format(
            analysis_label=self.analysis.Label,
            date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            script_name="evaluate.py",
            case_dir=case_dir.replace("\\", "\\\\"),
            foam_file=foam_file,
            time_series=str(ts),
        )

    # -----------------------------------------------------------------
    # Loader
    # -----------------------------------------------------------------

    def _build_loader(self):
        fields = self._all_fields()
        arr_str = repr(fields)
        return _LOAD_OPENFOAM.format(cell_arrays=arr_str)

    # -----------------------------------------------------------------
    # Point probes
    # -----------------------------------------------------------------

    def _build_point_probes(self):
        probes = self.point_probes
        if not probes:
            return ""

        lines = [
            "",
            "# =========================================================================",
            "# Point Probes",
            "# =========================================================================",
            "",
        ]

        for i, obj in enumerate(probes):
            name = obj.Label.replace(" ", "_")
            fields = list(obj.SampleFields) if obj.SampleFields else ["U", "p"]
            export_csv = getattr(obj, "ExportCSV", True)

            if getattr(obj, "UseLine", False):
                # Line probe (Plot Over Line)
                start = _mm_to_m(obj.LineStart)
                end = _mm_to_m(obj.LineEnd)
                res = getattr(obj, "LineResolution", 50)
                lines.append(f"# --- Line Probe: {obj.Label} ---")
                lines.append(f"print('Evaluating line probe: {obj.Label}')")
                lines.append(f"line_{name} = PlotOverLine(registrationName='{name}', Input=foam)")
                lines.append(f"line_{name}.Point1 = {_vec_str(start)}")
                lines.append(f"line_{name}.Point2 = {_vec_str(end)}")
                lines.append(f"line_{name}.Resolution = {res}")
                lines.append(f"line_{name}.UpdatePipeline()")
                lines.append("")

                if export_csv:
                    lines.append(f"# Export line probe data")
                    lines.append(f"csv_path = os.path.join(OUTPUT_DIR, '{name}_line.csv')")
                    lines.append(f"writer = CreateWriter(csv_path, line_{name})")
                    lines.append(f"writer.FieldAssociation = 'Point Data'")
                    lines.append(f"writer.UpdatePipeline()")
                    lines.append(f"del writer")
                    lines.append(f"print(f'  Saved: {{csv_path}}')")
                    lines.append("")
            else:
                # Single point probe
                loc = _mm_to_m(obj.ProbeLocation)
                lines.append(f"# --- Point Probe: {obj.Label} ---")
                lines.append(f"print('Evaluating point probe: {obj.Label}')")
                lines.append(f"probe_{name} = ProbeLocation(registrationName='{name}', Input=foam)")
                lines.append(f"probe_{name}.ProbeType = 'Fixed Radius Point Source'")
                lines.append(f"probe_{name}.ProbeType.Center = {_vec_str(loc)}")
                lines.append(f"probe_{name}.UpdatePipeline()")
                lines.append("")
                lines.append(f"# Read probed values")
                lines.append(f"probe_data_{name} = servermanager.Fetch(probe_{name})")
                lines.append(f"if probe_data_{name}.GetNumberOfPoints() > 0:")

                for f in fields:
                    lines.append(f"    arr = probe_data_{name}.GetPointData().GetArray('{f}')")
                    lines.append(f"    if arr:")
                    lines.append(f"        val = [arr.GetValue(c) for c in range(arr.GetNumberOfComponents())]")
                    lines.append(f"        print(f'  {obj.Label} / {f} = {{val}}')")

                if export_csv:
                    lines.append(f"")
                    lines.append(f"csv_path = os.path.join(OUTPUT_DIR, '{name}_point.csv')")
                    lines.append(f"writer = CreateWriter(csv_path, probe_{name})")
                    lines.append(f"writer.FieldAssociation = 'Point Data'")
                    lines.append(f"writer.UpdatePipeline()")
                    lines.append(f"del writer")
                    lines.append(f"print(f'  Saved: {{csv_path}}')")

                lines.append("")

        return "\n".join(lines)

    # -----------------------------------------------------------------
    # Surface measurements
    # -----------------------------------------------------------------

    def _build_surface_measurements(self):
        surfaces = self.surface_measurements
        if not surfaces:
            return ""

        lines = [
            "",
            "# =========================================================================",
            "# Surface Measurements",
            "# =========================================================================",
            "",
        ]

        for i, obj in enumerate(surfaces):
            name = obj.Label.replace(" ", "_")
            stype = obj.SurfaceType
            fields = list(obj.SampleFields) if obj.SampleFields else ["U", "p"]

            lines.append(f"# --- Surface: {obj.Label} ({stype}) ---")
            lines.append(f"print('Evaluating surface: {obj.Label}')")

            if stype == "Cut Plane":
                origin = _mm_to_m(obj.PlaneOrigin)
                norm_axis = getattr(obj, "PlaneNormal", "X")
                if norm_axis == "X":
                    normal = (1, 0, 0)
                elif norm_axis == "Y":
                    normal = (0, 1, 0)
                elif norm_axis == "Z":
                    normal = (0, 0, 1)
                else:
                    cn = obj.CustomNormal
                    normal = (cn.x, cn.y, cn.z)

                lines.append(f"slice_{name} = Slice(registrationName='{name}', Input=foam)")
                lines.append(f"slice_{name}.SliceType = 'Plane'")
                lines.append(f"slice_{name}.SliceType.Origin = {_vec_str(origin)}")
                lines.append(f"slice_{name}.SliceType.Normal = {_vec_str(normal)}")
                lines.append(f"slice_{name}.UpdatePipeline()")
                src_var = f"slice_{name}"

            elif stype == "Iso-Surface":
                iso_field = getattr(obj, "IsoField", "p")
                iso_val = getattr(obj, "IsoValue", 0.0)
                lines.append(f"iso_{name} = Contour(registrationName='{name}', Input=foam)")
                lines.append(f"iso_{name}.ContourBy = ['POINTS', '{iso_field}']")
                lines.append(f"iso_{name}.Isosurfaces = [{iso_val}]")
                lines.append(f"iso_{name}.UpdatePipeline()")
                src_var = f"iso_{name}"

            elif stype == "Clip (Half-Space)":
                origin = _mm_to_m(obj.PlaneOrigin)
                norm_axis = getattr(obj, "PlaneNormal", "X")
                if norm_axis == "X":
                    normal = (1, 0, 0)
                elif norm_axis == "Y":
                    normal = (0, 1, 0)
                elif norm_axis == "Z":
                    normal = (0, 0, 1)
                else:
                    cn = obj.CustomNormal
                    normal = (cn.x, cn.y, cn.z)

                lines.append(f"clip_{name} = Clip(registrationName='{name}', Input=foam)")
                lines.append(f"clip_{name}.ClipType = 'Plane'")
                lines.append(f"clip_{name}.ClipType.Origin = {_vec_str(origin)}")
                lines.append(f"clip_{name}.ClipType.Normal = {_vec_str(normal)}")
                lines.append(f"clip_{name}.UpdatePipeline()")
                src_var = f"clip_{name}"

            else:
                # Geometry Faces – use ExtractBlock or similar
                lines.append(f"# Geometry face selection not yet automated")
                lines.append(f"# Select faces manually in Paraview")
                src_var = "foam"

            lines.append("")

            # --- Compute averages / integrals ---
            if getattr(obj, "ComputeAverage", False):
                lines.append(f"# Area-weighted average")
                lines.append(f"integ_{name} = IntegrateVariables(registrationName='{name}_integ', Input={src_var})")
                lines.append(f"integ_{name}.UpdatePipeline()")
                lines.append(f"integ_data_{name} = servermanager.Fetch(integ_{name})")
                lines.append(f"if integ_data_{name}.GetNumberOfPoints() > 0:")
                lines.append(f"    # Area is in the CellData 'Area' array")
                lines.append(f"    area_arr = integ_data_{name}.GetCellData().GetArray('Area')")
                lines.append(f"    area = area_arr.GetValue(0) if area_arr else 1.0")
                for f in fields:
                    lines.append(f"    arr = integ_data_{name}.GetPointData().GetArray('{f}')")
                    lines.append(f"    if arr and area > 0:")
                    lines.append(f"        avg = [arr.GetValue(c) / area for c in range(arr.GetNumberOfComponents())]")
                    lines.append(f"        print(f'  {obj.Label} / avg({f}) = {{avg}}')")
                lines.append("")

            if getattr(obj, "ComputeIntegral", False):
                lines.append(f"# Surface integral")
                lines.append(f"integ2_{name} = IntegrateVariables(registrationName='{name}_surfint', Input={src_var})")
                lines.append(f"integ2_{name}.UpdatePipeline()")
                lines.append(f"integ2_data_{name} = servermanager.Fetch(integ2_{name})")
                lines.append(f"if integ2_data_{name}.GetNumberOfPoints() > 0:")
                for f in fields:
                    lines.append(f"    arr = integ2_data_{name}.GetPointData().GetArray('{f}')")
                    lines.append(f"    if arr:")
                    lines.append(f"        intval = [arr.GetValue(c) for c in range(arr.GetNumberOfComponents())]")
                    lines.append(f"        print(f'  {obj.Label} / integral({f}) = {{intval}}')")
                lines.append("")

            if getattr(obj, "ComputeMassFlow", False):
                lines.append(f"# Mass flow rate computation")
                lines.append(f"# Uses rho * dot(U, n) * dA  integrated over the surface")
                lines.append(f"calc_{name} = Calculator(registrationName='{name}_mdot_calc', Input={src_var})")
                lines.append(f"calc_{name}.AttributeType = 'Point Data'")
                lines.append(f"calc_{name}.ResultArrayName = 'massFlowDensity'")
                lines.append(f"calc_{name}.Function = 'U_X*Normals_X + U_Y*Normals_Y + U_Z*Normals_Z'")
                lines.append(f"genNormals_{name} = GenerateSurfaceNormals(Input={src_var})")
                lines.append(f"calc_{name}.Input = genNormals_{name}")
                lines.append(f"integ_mf_{name} = IntegrateVariables(Input=calc_{name})")
                lines.append(f"integ_mf_{name}.UpdatePipeline()")
                lines.append(f"mf_data_{name} = servermanager.Fetch(integ_mf_{name})")
                lines.append(f"if mf_data_{name}.GetNumberOfPoints() > 0:")
                lines.append(f"    mdot_arr = mf_data_{name}.GetPointData().GetArray('massFlowDensity')")
                lines.append(f"    if mdot_arr:")
                lines.append(f"        print(f'  {obj.Label} / mass_flow_rate = {{mdot_arr.GetValue(0)}}')")
                lines.append("")

            if getattr(obj, "ComputeForce", False):
                ref = _mm_to_m(obj.ForceRefPoint)
                lines.append(f"# Force & moment computation")
                lines.append(f"# Reference point: {_vec_str(ref)}")
                lines.append(f"# Note: For accurate forces, use OpenFOAM functionObjects")
                lines.append(f"# This is an approximation using pressure integration")
                lines.append(f"genN_{name} = GenerateSurfaceNormals(Input={src_var})")
                lines.append(f"calc_f_{name} = Calculator(registrationName='{name}_force', Input=genN_{name})")
                lines.append(f"calc_f_{name}.AttributeType = 'Point Data'")
                lines.append(f"calc_f_{name}.ResultArrayName = 'pForce'")
                lines.append(f"calc_f_{name}.Function = '-p*Normals'")
                lines.append(f"integ_f_{name} = IntegrateVariables(Input=calc_f_{name})")
                lines.append(f"integ_f_{name}.UpdatePipeline()")
                lines.append(f"f_data_{name} = servermanager.Fetch(integ_f_{name})")
                lines.append(f"if f_data_{name}.GetNumberOfPoints() > 0:")
                lines.append(f"    f_arr = f_data_{name}.GetPointData().GetArray('pForce')")
                lines.append(f"    if f_arr:")
                lines.append(f"        force = [f_arr.GetValue(c) for c in range(3)]")
                lines.append(f"        print(f'  {obj.Label} / force = {{force}}')")
                lines.append("")

            # Export surface data
            if getattr(obj, "ExportCSV", False):
                lines.append(f"csv_path = os.path.join(OUTPUT_DIR, '{name}_surface.csv')")
                lines.append(f"writer = CreateWriter(csv_path, {src_var})")
                lines.append(f"writer.FieldAssociation = 'Point Data'")
                lines.append(f"writer.UpdatePipeline()")
                lines.append(f"del writer")
                lines.append(f"print(f'  Saved: {{csv_path}}')")
                lines.append("")

            if getattr(obj, "ExportVTK", False):
                lines.append(f"vtk_path = os.path.join(OUTPUT_DIR, '{name}_surface.vtp')")
                lines.append(f"writer = CreateWriter(vtk_path, {src_var})")
                lines.append(f"writer.UpdatePipeline()")
                lines.append(f"del writer")
                lines.append(f"print(f'  Saved VTK: {{vtk_path}}')")
                lines.append("")

        return "\n".join(lines)

    # -----------------------------------------------------------------
    # Volume measurements
    # -----------------------------------------------------------------

    def _build_volume_measurements(self):
        volumes = self.volume_measurements
        if not volumes:
            return ""

        lines = [
            "",
            "# =========================================================================",
            "# Volume Measurements",
            "# =========================================================================",
            "",
        ]

        for i, obj in enumerate(volumes):
            name = obj.Label.replace(" ", "_")
            vtype = obj.VolumeType
            fields = list(obj.SampleFields) if obj.SampleFields else ["U", "p"]

            lines.append(f"# --- Volume: {obj.Label} ({vtype}) ---")
            lines.append(f"print('Evaluating volume: {obj.Label}')")

            if vtype == "Box":
                bmin = _mm_to_m(obj.BoxMin)
                bmax = _mm_to_m(obj.BoxMax)
                lines.append(f"clip1_{name} = Clip(registrationName='{name}_box', Input=foam)")
                lines.append(f"clip1_{name}.ClipType = 'Box'")
                lines.append(f"clip1_{name}.ClipType.Position = {_vec_str(bmin)}")
                lines.append(f"clip1_{name}.ClipType.Length = {_vec_str(tuple(bmax[j] - bmin[j] for j in range(3)))}")
                lines.append(f"clip1_{name}.UpdatePipeline()")
                src_var = f"clip1_{name}"

            elif vtype == "Sphere":
                center = _mm_to_m(obj.SphereCenter)
                radius = obj.SphereRadius / 1000.0
                lines.append(f"clip1_{name} = Clip(registrationName='{name}_sphere', Input=foam)")
                lines.append(f"clip1_{name}.ClipType = 'Sphere'")
                lines.append(f"clip1_{name}.ClipType.Center = {_vec_str(center)}")
                lines.append(f"clip1_{name}.ClipType.Radius = {radius}")
                lines.append(f"clip1_{name}.InsideOut = 1  # Keep inside")
                lines.append(f"clip1_{name}.UpdatePipeline()")
                src_var = f"clip1_{name}"

            elif vtype == "Cylinder":
                center = _mm_to_m(obj.CylinderCenter)
                axis = (obj.CylinderAxis.x, obj.CylinderAxis.y, obj.CylinderAxis.z)
                radius = obj.CylinderRadius / 1000.0
                height = obj.CylinderHeight / 1000.0
                lines.append(f"clip1_{name} = Clip(registrationName='{name}_cyl', Input=foam)")
                lines.append(f"clip1_{name}.ClipType = 'Cylinder'")
                lines.append(f"clip1_{name}.ClipType.Center = {_vec_str(center)}")
                lines.append(f"clip1_{name}.ClipType.Axis = {_vec_str(axis)}")
                lines.append(f"clip1_{name}.ClipType.Radius = {radius}")
                lines.append(f"clip1_{name}.InsideOut = 1")
                lines.append(f"clip1_{name}.UpdatePipeline()")
                src_var = f"clip1_{name}"

            elif vtype == "Threshold (field-based)":
                tf = getattr(obj, "ThresholdField", "p")
                tmin = getattr(obj, "ThresholdMin", 0.0)
                tmax = getattr(obj, "ThresholdMax", 1.0)
                lines.append(f"thresh_{name} = Threshold(registrationName='{name}_thresh', Input=foam)")
                lines.append(f"thresh_{name}.Scalars = ['POINTS', '{tf}']")
                lines.append(f"thresh_{name}.LowerThreshold = {tmin}")
                lines.append(f"thresh_{name}.UpperThreshold = {tmax}")
                lines.append(f"thresh_{name}.UpdatePipeline()")
                src_var = f"thresh_{name}"

            else:  # Entire Domain
                src_var = "foam"

            lines.append("")

            # --- Statistics ---
            if getattr(obj, "ComputeMinMax", False):
                lines.append(f"# Min/Max statistics")
                lines.append(f"desc_{name} = DescriptiveStatistics(registrationName='{name}_stats', Input={src_var})")
                lines.append(f"desc_{name}.UpdatePipeline()")
                for f in fields:
                    lines.append(f"print('  {obj.Label} / {f}: computing min/max...')")
                    lines.append(f"# Use data range from the array")
                    lines.append(f"data_{name}_{f} = servermanager.Fetch({src_var})")
                    lines.append(f"arr_{name}_{f} = data_{name}_{f}.GetPointData().GetArray('{f}')")
                    lines.append(f"if arr_{name}_{f} is None:")
                    lines.append(f"    arr_{name}_{f} = data_{name}_{f}.GetCellData().GetArray('{f}')")
                    lines.append(f"if arr_{name}_{f}:")
                    lines.append(f"    rng = arr_{name}_{f}.GetRange()")
                    lines.append(f"    print(f'    min = {{rng[0]:.6g}}, max = {{rng[1]:.6g}}')")
                lines.append("")

            if getattr(obj, "ComputeAverage", False):
                lines.append(f"# Volume-weighted average")
                lines.append(f"integ_{name} = IntegrateVariables(registrationName='{name}_integ', Input={src_var})")
                lines.append(f"integ_{name}.UpdatePipeline()")
                lines.append(f"integ_d_{name} = servermanager.Fetch(integ_{name})")
                lines.append(f"if integ_d_{name}.GetNumberOfCells() > 0:")
                lines.append(f"    vol_arr = integ_d_{name}.GetCellData().GetArray('Volume')")
                lines.append(f"    vol = vol_arr.GetValue(0) if vol_arr else 1.0")
                for f in fields:
                    lines.append(f"    arr = integ_d_{name}.GetPointData().GetArray('{f}')")
                    lines.append(f"    if arr and vol > 0:")
                    lines.append(f"        avg = [arr.GetValue(c) / vol for c in range(arr.GetNumberOfComponents())]")
                    lines.append(f"        print(f'  {obj.Label} / vol_avg({f}) = {{avg}}')")
                lines.append("")

            if getattr(obj, "ComputeIntegral", False):
                lines.append(f"# Volume integral")
                lines.append(f"integ2_{name} = IntegrateVariables(registrationName='{name}_volint', Input={src_var})")
                lines.append(f"integ2_{name}.UpdatePipeline()")
                lines.append(f"integ2_d_{name} = servermanager.Fetch(integ2_{name})")
                lines.append(f"if integ2_d_{name}.GetNumberOfPoints() > 0:")
                for f in fields:
                    lines.append(f"    arr = integ2_d_{name}.GetPointData().GetArray('{f}')")
                    lines.append(f"    if arr:")
                    lines.append(f"        intval = [arr.GetValue(c) for c in range(arr.GetNumberOfComponents())]")
                    lines.append(f"        print(f'  {obj.Label} / vol_integral({f}) = {{intval}}')")
                lines.append("")

            # Export
            if getattr(obj, "ExportCSV", False):
                lines.append(f"csv_path = os.path.join(OUTPUT_DIR, '{name}_volume.csv')")
                lines.append(f"writer = CreateWriter(csv_path, {src_var})")
                lines.append(f"writer.FieldAssociation = 'Point Data'")
                lines.append(f"writer.UpdatePipeline()")
                lines.append(f"del writer")
                lines.append(f"print(f'  Saved: {{csv_path}}')")
                lines.append("")

        return "\n".join(lines)

    # -----------------------------------------------------------------
    # Time-series loop wrapper
    # -----------------------------------------------------------------

    def _build_time_loop(self):
        return textwrap.dedent("""\

        # =========================================================================
        # Time-series evaluation loop
        # =========================================================================
        if TIME_SERIES and len(time_steps) > 1:
            summary_path = os.path.join(OUTPUT_DIR, 'time_series_summary.csv')
            print(f"\\nTime-series mode: evaluating {len(time_steps)} steps")
            print(f"Results will be appended to: {summary_path}")
            # For full time-series, re-run the script logic per time step
            # by calling animationScene.AnimationTime = t for each t
            for t in time_steps:
                animationScene.AnimationTime = t
                print(f"  t = {t}")
                # Pipelines update automatically
        """)

    # -----------------------------------------------------------------
    # Footer
    # -----------------------------------------------------------------

    def _build_footer(self):
        return textwrap.dedent("""\

        # =========================================================================
        # Done
        # =========================================================================
        print("")
        print("=" * 60)
        print("FlowStudio evaluation complete.")
        print(f"Results saved to: {OUTPUT_DIR}")
        print("=" * 60)
        """)

    # -----------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------

    def build(self):
        """Return the full Paraview Python script as a string."""
        parts = [
            self._build_header(),
            self._build_loader(),
            self._build_point_probes(),
            self._build_surface_measurements(),
            self._build_volume_measurements(),
            self._build_time_loop(),
            self._build_footer(),
        ]
        return "\n".join(p for p in parts if p)

    def write(self, filename="evaluate.py", directory=None):
        """Write the script to disk.

        Parameters
        ----------
        filename : str
            Script filename.
        directory : str or None
            Output directory.  Defaults to the analysis CaseDir.

        Returns
        -------
        str
            Absolute path to the written script.
        """
        if directory is None:
            directory = getattr(self.analysis, "CaseDir", "")
            if not directory:
                directory = os.path.join(os.path.expanduser("~"),
                                         "FlowStudio_Case")

        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, filename)

        script = self.build()
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(script)

        FreeCAD.Console.PrintMessage(
            f"FlowStudio: Paraview script written to {path}\n"
        )
        return path

    def has_measurements(self):
        """True if the analysis contains at least one measurement object."""
        return bool(self.point_probes or self.surface_measurements
                    or self.volume_measurements)
