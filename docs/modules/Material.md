# Material Module

> **Library**: `Material.dll` / `libMaterial.so`  
> **Source**: `src/Mod/Material/`  
> **Files**: ~63 .cpp · ~52 .h · ~18 .py  
> **Dependencies**: FreeCADApp, FreeCADBase

---

## 📋 Overview

The **Material** module manages **material properties** across FreeCAD:

- **MaterialManager** — central material database
- **MaterialLoader** — loads materials from card files
- **ModelManager** — material model definitions
- **MaterialLibrary** — collections of materials (built-in + user-defined)
- **Material cards** — YAML-based material definitions

Materials are used by FEM (structural/thermal analysis), rendering, and Part (appearance).

---

## 🏗️ Architecture

| Class | Purpose |
|---|---|
| `MaterialManager` | Singleton managing all available materials |
| `MaterialLoader` | Reads material cards from disk |
| `Material` | Material data object with properties |
| `ModelManager` | Manages material model schemas |
| `MaterialLibrary` | Collection of materials |

### Material Card Format

```yaml
General:
  Name: Steel-S235JR
  Description: Structural steel
Mechanical:
  YoungsModulus: 210000 MPa
  PoissonRatio: 0.3
  Density: 7800 kg/m^3
  UltimateTensileStrength: 360 MPa
  YieldStrength: 235 MPa
Thermal:
  ThermalConductivity: 50 W/m/K
  SpecificHeat: 460 J/kg/K
  ThermalExpansionCoefficient: 1.2e-5 1/K
```

### Built-in Material Library

Pre-configured materials for:
- **Metals** — Steel (various grades), Aluminum, Copper, Titanium, Brass
- **Polymers** — ABS, PLA, PETG, Nylon, Polycarbonate
- **Composites** — Carbon fiber, Fiberglass
- **Concrete** — Various grades
- **Wood** — Various species

---

## 📅 Timeline

| Year | Milestone |
|---|---|
| 2014 | Initial material system (simple card files) |
| 2018 | Material model framework |
| 2022 | MaterialManager overhaul |
| 2024 | YAML-based cards, expanded library |
| 2025 | ModelManager, improved UI |

---

*Part of the [FreeCAD Documentation Hub](../README.md)*
