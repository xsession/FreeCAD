# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Optical solver adapter.

This adapter is intentionally a manifest-first backend. It exports a complete
case description that can be consumed by open-source optical engines while we
incrementally add native launchers for Raysect, Meep, openEMS, and Optiland.
"""

import importlib.util
import json
import os
import shutil

import FreeCAD

from flow_studio.solvers.base_solver import BaseSolverRunner


class OpticalRunner(BaseSolverRunner):
    """Manifest writer and dependency checker for optical simulation backends."""

    name = "Optical"

    _PYTHON_BACKENDS = {
        "Raysect": "raysect",
        "Meep": "meep",
        "Optiland": "optiland",
    }

    def _backend(self):
        return getattr(self.solver_obj, "SolverBackend", "Raysect")

    def check(self):
        backend = self._backend()
        module_name = self._PYTHON_BACKENDS.get(backend)
        if module_name:
            return importlib.util.find_spec(module_name) is not None
        if backend == "openEMS":
            return shutil.which("openEMS") is not None or importlib.util.find_spec("openEMS") is not None
        if backend in ("Astree", "OpenRayTrace", "OpenRT"):
            return False
        return True

    def _children(self):
        try:
            return list(self.analysis.Group)
        except Exception:
            return []

    @staticmethod
    def _props(obj, names):
        data = {"Name": getattr(obj, "Name", ""), "Label": getattr(obj, "Label", "")}
        for name in names:
            if name in getattr(obj, "PropertiesList", []):
                value = getattr(obj, name)
                if isinstance(value, (str, int, float, bool)):
                    data[name] = value
                else:
                    data[name] = str(value)
        return data

    def write_case(self):
        os.makedirs(self.case_dir, exist_ok=True)
        children = self._children()
        manifest = {
            "project": getattr(FreeCAD.ActiveDocument, "Name", "FlowStudio"),
            "analysis": getattr(self.analysis, "Name", "OpticalAnalysis"),
            "domain": getattr(self.analysis, "PhysicsDomain", "Optical"),
            "backend": self._backend(),
            "physics": [],
            "materials": [],
            "sources": [],
            "detectors": [],
            "boundaries": [],
        }
        for obj in children:
            flow_type = getattr(obj, "FlowType", "")
            if flow_type == "FlowStudio::OpticalPhysicsModel":
                manifest["physics"].append(self._props(obj, [
                    "OpticalModel", "Wavelength", "WavelengthMin", "WavelengthMax",
                    "RayCount", "PmlThickness", "Resolution",
                ]))
            elif flow_type == "FlowStudio::OpticalMaterial":
                manifest["materials"].append(self._props(obj, [
                    "MaterialName", "MaterialPreset", "RefractiveIndex", "AbbeNumber",
                    "ExtinctionCoefficient", "Transmission", "Reflectivity",
                    "ReferenceWavelength", "WavelengthMin", "WavelengthMax",
                ]))
            elif flow_type == "FlowStudio::BCOpticalSource":
                manifest["sources"].append(self._props(obj, [
                    "SourceType", "Power", "Wavelength", "BeamRadius", "DivergenceAngle", "RayCount",
                ]))
            elif flow_type == "FlowStudio::BCOpticalDetector":
                manifest["detectors"].append(self._props(obj, [
                    "DetectorType", "PixelsX", "PixelsY", "Width", "Height",
                ]))
            elif flow_type == "FlowStudio::BCOpticalBoundary":
                manifest["boundaries"].append(self._props(obj, [
                    "BoundaryType", "Reflectivity", "Transmission", "Scatter",
                ]))

        path = os.path.join(self.case_dir, "optical_case.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=2, sort_keys=True)
        FreeCAD.Console.PrintMessage(f"FlowStudio Optical: wrote {path}\n")
        return path

    def run(self):
        self.write_case()
        FreeCAD.Console.PrintMessage(
            "FlowStudio Optical: case manifest generated. Native solver launch is staged next.\n"
        )
        return 0

    def read_results(self):
        FreeCAD.Console.PrintMessage("FlowStudio Optical: result import is not implemented yet.\n")
        return None

