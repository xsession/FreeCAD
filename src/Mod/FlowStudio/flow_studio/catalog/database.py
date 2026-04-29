# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Engineering database for FlowStudio materials, fans, and components."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path

try:
	import FreeCAD
except Exception:  # pragma: no cover - allows non-FreeCAD tests/imports
	FreeCAD = None


DEFAULT_UNIT_MATRIX = {
	"Density": {"SI (m-kg-s)": "kg/m^3", "SI (mm-kg-s)": "kg/mm^3"},
	"DynamicViscosity": {"SI (m-kg-s)": "Pa*s", "SI (mm-kg-s)": "Pa*s"},
	"KinematicViscosity": {"SI (m-kg-s)": "m^2/s", "SI (mm-kg-s)": "mm^2/s"},
	"SpecificHeat": {"SI (m-kg-s)": "J/(kg*K)", "SI (mm-kg-s)": "J/(kg*K)"},
	"ThermalConductivity": {"SI (m-kg-s)": "W/(m*K)", "SI (mm-kg-s)": "W/(mm*K)"},
	"PrandtlNumber": {"SI (m-kg-s)": "-", "SI (mm-kg-s)": "-"},
	"YoungsModulus": {"SI (m-kg-s)": "Pa", "SI (mm-kg-s)": "Pa"},
	"PoissonRatio": {"SI (m-kg-s)": "-", "SI (mm-kg-s)": "-"},
	"ThermalExpansionCoeff": {"SI (m-kg-s)": "1/K", "SI (mm-kg-s)": "1/K"},
	"YieldStrength": {"SI (m-kg-s)": "Pa", "SI (mm-kg-s)": "Pa"},
	"Emissivity": {"SI (m-kg-s)": "-", "SI (mm-kg-s)": "-"},
	"RelativePermittivity": {"SI (m-kg-s)": "-", "SI (mm-kg-s)": "-"},
	"RelativePermeability": {"SI (m-kg-s)": "-", "SI (mm-kg-s)": "-"},
	"ElectricConductivity": {"SI (m-kg-s)": "S/m", "SI (mm-kg-s)": "S/mm"},
	"RefractiveIndex": {"SI (m-kg-s)": "-", "SI (mm-kg-s)": "-"},
	"AbbeNumber": {"SI (m-kg-s)": "-", "SI (mm-kg-s)": "-"},
	"ExtinctionCoefficient": {"SI (m-kg-s)": "-", "SI (mm-kg-s)": "-"},
	"Transmission": {"SI (m-kg-s)": "-", "SI (mm-kg-s)": "-"},
	"Reflectivity": {"SI (m-kg-s)": "-", "SI (mm-kg-s)": "-"},
	"ReferenceWavelength": {"SI (m-kg-s)": "nm", "SI (mm-kg-s)": "nm"},
	"WavelengthMin": {"SI (m-kg-s)": "nm", "SI (mm-kg-s)": "nm"},
	"WavelengthMax": {"SI (m-kg-s)": "nm", "SI (mm-kg-s)": "nm"},
	"AbsorptionLength": {"SI (m-kg-s)": "mm", "SI (mm-kg-s)": "mm"},
	"SurfaceRoughness": {"SI (m-kg-s)": "um", "SI (mm-kg-s)": "um"},
	"SellmeierB1": {"SI (m-kg-s)": "-", "SI (mm-kg-s)": "-"},
	"SellmeierB2": {"SI (m-kg-s)": "-", "SI (mm-kg-s)": "-"},
	"SellmeierB3": {"SI (m-kg-s)": "-", "SI (mm-kg-s)": "-"},
	"SellmeierC1": {"SI (m-kg-s)": "um^2", "SI (mm-kg-s)": "um^2"},
	"SellmeierC2": {"SI (m-kg-s)": "um^2", "SI (mm-kg-s)": "um^2"},
	"SellmeierC3": {"SI (m-kg-s)": "um^2", "SI (mm-kg-s)": "um^2"},
}

MATERIAL_CATEGORY_FIELDS = {
	"Gases": ["MaterialName", "Density", "DynamicViscosity", "KinematicViscosity", "SpecificHeat", "ThermalConductivity", "PrandtlNumber", "Comment"],
	"Liquids": ["MaterialName", "Density", "DynamicViscosity", "KinematicViscosity", "SpecificHeat", "ThermalConductivity", "PrandtlNumber", "Comment"],
	"Solids": ["MaterialName", "Density", "YoungsModulus", "PoissonRatio", "ThermalExpansionCoeff", "YieldStrength", "ThermalConductivity", "SpecificHeat", "Emissivity", "RelativePermittivity", "RelativePermeability", "ElectricConductivity", "Comment"],
	"Dielectrics": ["MaterialName", "RelativePermittivity", "RelativePermeability", "ElectricConductivity", "Density", "Comment"],
	"Magnetic": ["MaterialName", "RelativePermeability", "RelativePermittivity", "ElectricConductivity", "Density", "Comment"],
	"Optical Glasses": ["MaterialName", "RefractiveIndex", "AbbeNumber", "ExtinctionCoefficient", "Transmission", "Reflectivity", "ReferenceWavelength", "WavelengthMin", "WavelengthMax", "AbsorptionLength", "SurfaceRoughness", "SellmeierB1", "SellmeierB2", "SellmeierB3", "SellmeierC1", "SellmeierC2", "SellmeierC3", "Comment"],
	"Optical Coatings": ["MaterialName", "RefractiveIndex", "ExtinctionCoefficient", "Transmission", "Reflectivity", "ReferenceWavelength", "Comment"],
}

MATERIAL_FIELD_DEFAULTS = {
	"MaterialName": "New Material",
	"Density": 1.0,
	"DynamicViscosity": 1.0e-3,
	"KinematicViscosity": 1.0e-6,
	"SpecificHeat": 1000.0,
	"ThermalConductivity": 1.0,
	"PrandtlNumber": 1.0,
	"YoungsModulus": 1.0e9,
	"PoissonRatio": 0.3,
	"ThermalExpansionCoeff": 1.0e-5,
	"YieldStrength": 1.0e7,
	"Emissivity": 0.5,
	"RelativePermittivity": 1.0,
	"RelativePermeability": 1.0,
	"ElectricConductivity": 0.0,
	"RefractiveIndex": 1.0,
	"AbbeNumber": 0.0,
	"ExtinctionCoefficient": 0.0,
	"Transmission": 1.0,
	"Reflectivity": 0.0,
	"ReferenceWavelength": 550.0,
	"WavelengthMin": 350.0,
	"WavelengthMax": 2000.0,
	"AbsorptionLength": 1000.0,
	"SurfaceRoughness": 0.01,
	"SellmeierB1": 0.0,
	"SellmeierB2": 0.0,
	"SellmeierB3": 0.0,
	"SellmeierC1": 0.0,
	"SellmeierC2": 0.0,
	"SellmeierC3": 0.0,
	"Comment": "User-defined database item",
}

FLOW_TYPE_TO_DATABASE_CATEGORIES = {
	"FlowStudio::FluidMaterial": ("Gases", "Liquids"),
	"FlowStudio::SolidMaterial": ("Solids",),
	"FlowStudio::ThermalMaterial": ("Solids", "Liquids", "Gases"),
	"FlowStudio::ElectrostaticMaterial": ("Dielectrics", "Solids", "Liquids", "Gases"),
	"FlowStudio::ElectromagneticMaterial": ("Magnetic", "Dielectrics", "Solids"),
	"FlowStudio::OpticalMaterial": ("Optical Glasses", "Optical Coatings", "Dielectrics"),
}


DEFAULT_DATABASE = {
	"schema_version": 1,
	"units": "SI (m-kg-s)",
	"unit_matrix": copy.deepcopy(DEFAULT_UNIT_MATRIX),
	"materials": {
		"Gases": {
			"Air (20C, 1atm)": {
				"MaterialName": "Air",
				"Density": 1.225,
				"DynamicViscosity": 1.81e-5,
				"KinematicViscosity": 1.48e-5,
				"SpecificHeat": 1005.0,
				"ThermalConductivity": 0.0257,
				"PrandtlNumber": 0.707,
				"Comment": "Dry air at 20C and 1 atm.",
			},
			"Nitrogen": {
				"MaterialName": "Nitrogen",
				"Density": 1.165,
				"DynamicViscosity": 1.76e-5,
				"KinematicViscosity": 1.51e-5,
				"SpecificHeat": 1040.0,
				"ThermalConductivity": 0.0258,
				"PrandtlNumber": 0.71,
			},
			"Oxygen": {
				"MaterialName": "Oxygen",
				"Density": 1.331,
				"DynamicViscosity": 2.05e-5,
				"KinematicViscosity": 1.54e-5,
				"SpecificHeat": 918.0,
				"ThermalConductivity": 0.0263,
				"PrandtlNumber": 0.72,
			},
			"Carbon dioxide": {
				"MaterialName": "Carbon dioxide",
				"Density": 1.842,
				"DynamicViscosity": 1.47e-5,
				"KinematicViscosity": 7.98e-6,
				"SpecificHeat": 844.0,
				"ThermalConductivity": 0.0168,
				"PrandtlNumber": 0.74,
			},
		},
		"Liquids": {
			"Water (20C)": {
				"MaterialName": "Water",
				"Density": 998.2,
				"DynamicViscosity": 1.002e-3,
				"KinematicViscosity": 1.004e-6,
				"SpecificHeat": 4182.0,
				"ThermalConductivity": 0.6,
				"PrandtlNumber": 7.01,
			},
			"Glycerin": {
				"MaterialName": "Glycerin",
				"Density": 1261.0,
				"DynamicViscosity": 1.412,
				"KinematicViscosity": 1.12e-3,
				"SpecificHeat": 2427.0,
				"ThermalConductivity": 0.286,
				"PrandtlNumber": 11970.0,
			},
			"Oil (SAE 30)": {
				"MaterialName": "Oil SAE 30",
				"Density": 891.0,
				"DynamicViscosity": 0.29,
				"KinematicViscosity": 3.25e-4,
				"SpecificHeat": 1900.0,
				"ThermalConductivity": 0.145,
				"PrandtlNumber": 3800.0,
			},
		},
		"Solids": {
			"Steel (Structural)": {
				"MaterialName": "Steel",
				"Density": 7850.0,
				"YoungsModulus": 2.1e11,
				"PoissonRatio": 0.3,
				"ThermalExpansionCoeff": 1.2e-5,
				"YieldStrength": 2.5e8,
				"ThermalConductivity": 50.0,
				"SpecificHeat": 500.0,
				"Emissivity": 0.3,
			},
			"Aluminum 6061-T6": {
				"MaterialName": "Aluminum 6061-T6",
				"Density": 2700.0,
				"YoungsModulus": 6.9e10,
				"PoissonRatio": 0.33,
				"ThermalExpansionCoeff": 2.36e-5,
				"YieldStrength": 2.75e8,
				"ThermalConductivity": 167.0,
				"SpecificHeat": 896.0,
				"Emissivity": 0.09,
			},
			"Copper": {
				"MaterialName": "Copper",
				"Density": 8960.0,
				"YoungsModulus": 1.1e11,
				"PoissonRatio": 0.34,
				"ThermalExpansionCoeff": 1.65e-5,
				"YieldStrength": 7.0e7,
				"ThermalConductivity": 385.0,
				"SpecificHeat": 385.0,
				"Emissivity": 0.03,
				"ElectricConductivity": 5.96e7,
				"RelativePermeability": 0.999994,
				"RelativePermittivity": 1.0,
			},
			"Glass": {
				"MaterialName": "Glass",
				"Density": 2500.0,
				"ThermalConductivity": 1.05,
				"SpecificHeat": 750.0,
				"Emissivity": 0.92,
				"RelativePermittivity": 5.5,
				"ElectricConductivity": 1e-12,
			},
			"FR-4 (PCB)": {
				"MaterialName": "FR-4",
				"Density": 1850.0,
				"ThermalConductivity": 0.3,
				"SpecificHeat": 1100.0,
				"RelativePermittivity": 4.4,
				"ElectricConductivity": 1e-14,
			},
		},
		"Dielectrics": {
			"Vacuum": {
				"MaterialName": "Vacuum",
				"RelativePermittivity": 1.0,
				"ElectricConductivity": 0.0,
			},
			"Air": {
				"MaterialName": "Air",
				"RelativePermittivity": 1.0006,
				"RelativePermeability": 1.0,
				"ElectricConductivity": 0.0,
				"Density": 1.225,
			},
			"PTFE (Teflon)": {
				"MaterialName": "PTFE",
				"RelativePermittivity": 2.1,
				"ElectricConductivity": 1e-18,
			},
		},
		"Magnetic": {
			"Soft Iron": {
				"MaterialName": "Soft Iron",
				"RelativePermeability": 5000.0,
				"RelativePermittivity": 1.0,
				"ElectricConductivity": 1.0e7,
				"Density": 7870.0,
			},
			"Ferrite (MnZn)": {
				"MaterialName": "Ferrite MnZn",
				"RelativePermeability": 2000.0,
				"RelativePermittivity": 15.0,
				"ElectricConductivity": 1.0,
				"Density": 4800.0,
			},
		},
		"Optical Glasses": {
			"BK7": {
				"MaterialName": "BK7",
				"RefractiveIndex": 1.5168,
				"AbbeNumber": 64.17,
				"ExtinctionCoefficient": 0.0,
				"Transmission": 0.92,
				"Reflectivity": 0.04,
				"ReferenceWavelength": 587.6,
				"WavelengthMin": 350.0,
				"WavelengthMax": 2000.0,
				"Comment": "Common borosilicate crown glass approximation.",
			},
			"Fused Silica": {
				"MaterialName": "Fused Silica",
				"RefractiveIndex": 1.4585,
				"AbbeNumber": 67.82,
				"ExtinctionCoefficient": 0.0,
				"Transmission": 0.94,
				"Reflectivity": 0.035,
				"ReferenceWavelength": 587.6,
				"WavelengthMin": 180.0,
				"WavelengthMax": 3500.0,
			},
			"Sapphire": {
				"MaterialName": "Sapphire",
				"RefractiveIndex": 1.7682,
				"AbbeNumber": 72.2,
				"ExtinctionCoefficient": 0.0,
				"Transmission": 0.86,
				"Reflectivity": 0.076,
				"ReferenceWavelength": 587.6,
				"WavelengthMin": 150.0,
				"WavelengthMax": 5500.0,
			},
			"Polycarbonate": {
				"MaterialName": "Polycarbonate",
				"RefractiveIndex": 1.586,
				"AbbeNumber": 30.0,
				"ExtinctionCoefficient": 0.0,
				"Transmission": 0.88,
				"Reflectivity": 0.05,
				"ReferenceWavelength": 587.6,
				"WavelengthMin": 380.0,
				"WavelengthMax": 1100.0,
			},
		},
		"Optical Coatings": {
			"Aluminum Mirror": {
				"MaterialName": "Aluminum Mirror",
				"RefractiveIndex": 0.65,
				"AbbeNumber": 0.0,
				"ExtinctionCoefficient": 5.3,
				"Transmission": 0.0,
				"Reflectivity": 0.88,
				"ReferenceWavelength": 550.0,
			},
			"Ideal Absorber": {
				"MaterialName": "Ideal Absorber",
				"RefractiveIndex": 1.0,
				"Transmission": 0.0,
				"Reflectivity": 0.0,
				"ExtinctionCoefficient": 1.0,
				"ReferenceWavelength": 550.0,
			},
			"Ideal AR Coating": {
				"MaterialName": "Ideal AR Coating",
				"RefractiveIndex": 1.38,
				"Transmission": 0.995,
				"Reflectivity": 0.005,
				"ExtinctionCoefficient": 0.0,
				"ReferenceWavelength": 550.0,
			},
		},
	},
	"optics": {
		"Light Sources": {
			"Collimated 550nm 1W": {
				"SourceType": "Collimated Beam",
				"Power": 1.0,
				"Wavelength": 550.0,
				"BeamRadius": 1.0,
				"DivergenceAngle": 0.0,
				"RayCount": 10000,
			},
			"White Lambertian LED": {
				"SourceType": "Lambertian LED",
				"Power": 1.0,
				"Wavelength": 560.0,
				"BeamRadius": 1.5,
				"DivergenceAngle": 120.0,
				"RayCount": 20000,
			},
		},
		"Detectors": {
			"Irradiance Sensor 10mm": {
				"DetectorType": "Irradiance",
				"PixelsX": 512,
				"PixelsY": 512,
				"Width": 10.0,
				"Height": 10.0,
			},
			"Spot Diagram Plane": {
				"DetectorType": "Spot Diagram",
				"PixelsX": 1024,
				"PixelsY": 1024,
				"Width": 5.0,
				"Height": 5.0,
			},
		},
		"Solver Recommendations": {
			"Raysect": {
				"Backend": "Raysect",
				"BestFor": "Geometrical optics, illumination, non-sequential ray tracing",
				"License": "Open source",
				"PythonPackage": "raysect",
			},
			"Meep": {
				"Backend": "Meep",
				"BestFor": "Wave optics, FDTD, photonic crystals, nanophotonics",
				"License": "GPL",
				"PythonPackage": "meep",
			},
			"openEMS": {
				"Backend": "openEMS",
				"BestFor": "Full-wave FDTD, RF/microwave/EM structures, CSXCAD geometry",
				"License": "GPL",
				"PythonPackage": "openEMS",
			},
		},
	},
	"fans": {
		"Pre-Defined": {
			"Axial": {
				"Generic Axial 40mm": {
					"FanType": "External Inlet Fan",
					"ReferencePressure": 101325.0,
					"curve": [
						[0.0, 45.0],
						[0.0004, 37.0],
						[0.0008, 28.0],
						[0.0012, 20.0],
						[0.0016, 12.0],
						[0.0021, 0.0],
					],
					"Comment": "Generic small axial fan, volume flow [m^3/s], pressure [Pa].",
				},
				"Noctua_NF-A6x25_5V_PWM": {
					"FanType": "External Inlet Fan",
					"ReferencePressure": 101325.0,
					"curve": [
						[0.0, 38.0],
						[0.00030, 33.0],
						[0.00055, 27.0],
						[0.00080, 20.0],
						[0.00105, 12.0],
						[0.00125, 0.0],
					],
				},
			},
			"Radial": {
				"Generic Blower": {
					"FanType": "Internal Fan",
					"ReferencePressure": 101325.0,
					"curve": [
						[0.0, 120.0],
						[0.0005, 105.0],
						[0.0010, 80.0],
						[0.0015, 45.0],
						[0.0020, 0.0],
					],
				}
			},
		},
		"User Defined": {},
	},
	"heat_sinks": {"Pre-Defined": {}, "User Defined": {}},
	"units": {
		"SI (m-kg-s)": {"length": "m", "mass": "kg", "time": "s", "temperature": "K"},
		"SI (mm-kg-s)": {"length": "mm", "mass": "kg", "time": "s", "temperature": "K"},
	},
}


def user_database_path() -> Path:
	if FreeCAD is not None:
		try:
			root = FreeCAD.getUserAppDataDir()
		except Exception:
			root = os.path.expanduser("~")
	else:
		root = os.path.expanduser("~")
	return Path(root) / "FlowStudio" / "engineering_database.json"


def load_database() -> dict:
	path = user_database_path()
	if not path.exists():
		return copy.deepcopy(DEFAULT_DATABASE)
	try:
		with path.open("r", encoding="utf-8") as handle:
			loaded = json.load(handle)
	except Exception:
		return copy.deepcopy(DEFAULT_DATABASE)
	return merge_database(copy.deepcopy(DEFAULT_DATABASE), loaded)


def save_database(database: dict) -> Path:
	path = user_database_path()
	path.parent.mkdir(parents=True, exist_ok=True)
	with path.open("w", encoding="utf-8") as handle:
		json.dump(database, handle, indent=2, sort_keys=True)
		handle.write("\n")
	return path


def reset_user_database() -> Path:
	database = copy.deepcopy(DEFAULT_DATABASE)
	return save_database(database)


def merge_database(base: dict, override: dict) -> dict:
	for key, value in (override or {}).items():
		if isinstance(value, dict) and isinstance(base.get(key), dict):
			merge_database(base[key], value)
		else:
			base[key] = value
	return base


def flatten_named_items(tree: dict, prefix: str = "") -> dict[str, dict]:
	items: dict[str, dict] = {}
	for name, value in (tree or {}).items():
		path = f"{prefix}/{name}" if prefix else name
		if isinstance(value, dict) and _is_leaf_item(value):
			item = copy.deepcopy(value)
			item["_path"] = path
			items[name] = item
		elif isinstance(value, dict):
			items.update(flatten_named_items(value, path))
	return items


def _is_leaf_item(value: dict) -> bool:
	return any(not isinstance(v, dict) for v in value.values()) or "curve" in value


def material_presets(*categories: str) -> dict[str, dict]:
	db = load_database()
	materials = db.get("materials", {})
	if not categories:
		return flatten_named_items(materials)
	merged: dict[str, dict] = {}
	for category in categories:
		merged.update(flatten_named_items(materials.get(category, {}), category))
	return merged


def material_categories_for_flow_type(flow_type: str) -> tuple[str, ...]:
	return tuple(FLOW_TYPE_TO_DATABASE_CATEGORIES.get(flow_type, ()))


def default_material_entry(category: str, name: str = "New Material") -> dict:
	fields = MATERIAL_CATEGORY_FIELDS.get(category, ("MaterialName", "Comment"))
	entry = {}
	for field in fields:
		value = MATERIAL_FIELD_DEFAULTS.get(field, "")
		entry[field] = name if field == "MaterialName" else copy.deepcopy(value)
	return entry


def unit_matrix() -> dict[str, dict[str, str]]:
	stored = load_database().get("unit_matrix", {})
	merged = copy.deepcopy(DEFAULT_UNIT_MATRIX)
	merge_database(merged, stored)
	return merged


def fan_presets() -> dict[str, dict]:
	return flatten_named_items(load_database().get("fans", {}))


def apply_properties(obj, values: dict) -> None:
	properties = getattr(obj, "PropertiesList", [])
	for key, value in (values or {}).items():
		if key.startswith("_") or key in {"curve", "Comment"}:
			continue
		if key in properties:
			try:
				setattr(obj, key, value)
			except Exception:
				pass
