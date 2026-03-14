# Spreadsheet Module

> **Library**: `Spreadsheet.dll` / `libSpreadsheet.so`  
> **Source**: `src/Mod/Spreadsheet/`  
> **Files**: ~29 .cpp · ~25 .h · ~6 .py  
> **Dependencies**: FreeCADApp, FreeCADBase

---

## 📋 Overview

The **Spreadsheet** module provides an **Excel-like spreadsheet** inside FreeCAD:

- **Cell grid** — standard A1/B2/C3 addressing
- **Expressions** — formulas binding to model properties (`=Pad.Length * 2`)
- **Data types** — numbers, strings, quantities (with units), dates
- **Formatting** — alignment, colors, borders, font styles
- **Import/Export** — XLSX import via `importXLSX`
- **Alias** — human-readable names for cells (`Spreadsheet.my_length` instead of `Spreadsheet.B2`)

Spreadsheets are essential for **parametric design** — driving model dimensions from a single data source.

---

## 🏗️ Architecture

| Class | Purpose |
|---|---|
| `Sheet` | Main spreadsheet DocumentObject |
| `Cell` | Individual cell (value, expression, formatting) |
| `SpreadsheetView` | Qt table widget for editing |
| `PropertySheet` | Custom property storing cell data |
| `importXLSX` | Excel .xlsx file reader |

### Expression Integration

```
Spreadsheet.B2 = 25.0
Pad.Length = Spreadsheet.B2     ← expression binding
Pocket.Depth = Spreadsheet.B2 / 2
```

Aliases make this cleaner:
```
Spreadsheet.setAlias("B2", "wall_thickness")
Pad.Length = Spreadsheet.wall_thickness
```

---

## 📅 Timeline

| Year | Milestone |
|---|---|
| 2014 | Initial Spreadsheet module |
| 2016 | Expression engine integration |
| 2018 | XLSX import |
| 2020 | Alias system, formatting improvements |
| 2025 | Performance, large spreadsheet handling |

---

*Part of the [FreeCAD Documentation Hub](../README.md)*
