# TechDraw Module — Technical Drawing

> **Library**: `TechDraw.dll` / `libTechDraw.so`  
> **Source**: `src/Mod/TechDraw/`  
> **Files**: ~241 .cpp · ~209 .h · ~36 .py  
> **Dependencies**: FreeCADApp, Part, OpenCASCADE (HLR)  
> **Architecture SVG**: [techdraw_architecture.svg](../svg/techdraw_architecture.svg)

---

## 📋 Overview

**TechDraw** generates **2D engineering drawings** from 3D models. It replaced the older Drawing module in 2016 and provides:

- **3D→2D projection** via OpenCASCADE Hidden Line Removal (HLR)
- **Multiple view types** — orthographic, section, detail, projection groups
- **Dimensions & annotations** — distances, angles, radii, GD&T symbols
- **Drawing standards** — ISO 128, ANSI Y14.5, 1st/3rd angle projection
- **Export** — SVG, PDF, DXF, HPGL
- **Templates** — SVG-based page templates with title blocks

---

## 🏗️ Architecture

### DrawPage Container

```
DrawPage
  ├── Template (SVG-based page frame + title block)
  ├── DrawViewPart (3D→2D projected view)
  ├── DrawViewSection (cross-section view)
  ├── DrawProjGroup (1st/3rd angle multi-view)
  ├── DrawViewDetail (magnified detail)
  ├── DrawViewDimension (dimensions)
  ├── DrawViewBalloon (BOM references)
  ├── DrawRichAnno (rich text annotations)
  ├── DrawLeaderLine (callout leaders)
  └── DrawViewSymbol (embedded SVGs)
```

### View Types

| View | Description |
|---|---|
| `DrawViewPart` | Primary 3D→2D projected view using HLR |
| `DrawViewSection` | Cross-section with hatch patterns |
| `DrawProjGroup` | Multi-view projection (Front/Top/Right/etc.) |
| `DrawProjGroupItem` | Individual view within a ProjGroup |
| `DrawViewDetail` | Magnified detail circle |
| `DrawViewSpreadsheet` | Embedded spreadsheet table |
| `DrawViewImage` | Embedded raster image |
| `DrawViewDraft` | Embedded Draft shape |
| `DrawViewClip` | Clipped region |

### Dimensions & Annotations

| Type | Description |
|---|---|
| `DrawViewDimension` | Distance, angle, radius, diameter, area |
| `DrawViewBalloon` | Part number callouts (for BOM) |
| `DrawRichAnno` | Rich text with formatting |
| `DrawLeaderLine` | Leader lines with arrow heads |
| `CosmeticEdge` | Manual construction lines |
| `CosmeticVertex` | Manual reference points |
| `CenterLine` | Automatic center lines |
| `DrawWeldingSymbol` | Welding callouts |
| `DrawTile` | Geometric tolerance frames |

### Projection Pipeline

```
TopoShape (3D solid)
  → HLRBRep_Algo (OCC Hidden Line Removal)
  → Edge classification (visible/hidden/smooth)
  → 2D edge list
  → SVG path generation
  → Rendered on DrawPage
```

### Template System

Templates are SVG files with special `freecad:editable` text fields:
```xml
<text freecad:editable="Title">Drawing Title</text>
<text freecad:editable="Author">Author Name</text>
```

Standard templates included for A0–A4, US Letter, etc.

---

## 📅 Historical Timeline

| Year | Milestone |
|---|---|
| 2016 | TechDraw created (replaces Drawing module) |
| 2017 | Section views, projection groups |
| 2018 | Improved section views, hatch patterns |
| 2019 | GD&T symbols, welding symbols |
| 2020 | Detail views, cosmetic edges |
| 2021 | Rich annotations, balloons |
| 2023 | TNP-stable geometry references |
| 2024 | Center line improvements |
| 2025 | Cosmetic enhancements, template improvements |

---

## 📂 Key Files

| File | Purpose |
|---|---|
| `App/DrawPage.h/cpp` | Drawing page container |
| `App/DrawView.h/cpp` | Base view class |
| `App/DrawViewPart.h/cpp` | 3D→2D projected view |
| `App/DrawViewSection.h/cpp` | Cross-section view |
| `App/DrawProjGroup.h/cpp` | Projection group |
| `App/DrawViewDimension.h/cpp` | Dimension annotations |
| `App/DrawViewBalloon.h/cpp` | BOM callouts |
| `App/DrawViewDetail.h/cpp` | Detail view |
| `App/Cosmetic.h/cpp` | Cosmetic edges/vertices |
| `App/GeometryObject.h/cpp` | HLR projection engine |
| `Gui/ViewProviderPage.h/cpp` | Page display widget |
| `Gui/QGVPage.h/cpp` | Qt Graphics View page |

---

## 🔗 Dependency Graph

```
TechDraw depends on:
  ├── Part (TopoShape for projection)
  ├── App (Document, Property)
  ├── OpenCASCADE (HLRBRep for hidden line removal)
  └── Qt6 (QGraphicsView for page rendering)

Used by:
  └── Drawing/documentation workflows
```

---

*Part of the [FreeCAD Documentation Hub](../README.md)*
