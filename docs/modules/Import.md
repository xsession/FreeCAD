# Import Module

> **Library**: `Import.dll` / `libImport.so`  
> **Source**: `src/Mod/Import/`  
> **Files**: ~29 .cpp · ~25 .h · ~24 .py  
> **Dependencies**: FreeCADApp, Part, OpenCASCADE

---

## 📋 Overview

The **Import** module handles **STEP and IGES file interchange** using OpenCASCADE translation:

- **STEP import/export** — AP203, AP214, AP242 support via `ImportOCAF` / `ExportOCAF`
- **IGES import/export** — legacy CAD interchange
- **OCAF integration** — preserves colors, names, assemblies from STEP files
- **StepShape** — shape reader with element map support

This module is critical for CAD interoperability — STEP is the primary format for exchanging geometry between CAD systems.

---

## 🏗️ Architecture

| Class | Purpose |
|---|---|
| `ImportOCAF` | STEP/IGES import using OCC XCAF framework |
| `ExportOCAF` | STEP/IGES export using OCC XCAF framework |
| `StepShape` | Shape reading with element map/TNP support |
| `ImportOCAF2` | Enhanced import with Link support |
| `ExportOCAF2` | Enhanced export preserving Link structure |

### STEP Import Pipeline

```
.step file
  → XSControl_Reader (OCC)
  → XDE Document (XCAF)
  → ImportOCAF traverses shape tree
  → Creates FreeCAD DocumentObjects
  → Preserves: colors, names, assembly structure
  → ElementMap generation for TNP
```

### Supported Formats

| Format | Standard | Description |
|---|---|---|
| STEP | ISO 10303 | Standard for Exchange of Product Data |
| IGES | ANSI Y14.26M | Initial Graphics Exchange Specification |

---

## 📅 Timeline

| Year | Milestone |
|---|---|
| 2004 | Initial STEP/IGES support via OCC |
| 2010 | XCAF/OCAF integration (colors, names) |
| 2015 | Assembly structure preservation |
| 2019 | ImportOCAF2 with Link support |
| 2023 | TNP element map generation on import |
| 2025 | AP242 improvements |

---

*Part of the [FreeCAD Documentation Hub](../README.md)*
