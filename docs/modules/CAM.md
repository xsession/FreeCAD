# CAM Module — Computer-Aided Manufacturing

> **Library**: `Path.dll` / `libPath.so`  
> **Source**: `src/Mod/CAM/`  
> **Files**: ~76 .cpp · ~59 .h · ~379 .py  
> **Dependencies**: FreeCADApp, Part  
> **Architecture SVG**: [cam_architecture.svg](../svg/cam_architecture.svg)

---

## 📋 Overview

The **CAM** module (formerly "Path") generates **CNC toolpaths** from 3D geometry and exports **G-code** for machining:

- **Operations** — Profile, Pocket, Drilling, Surface, Adaptive (HSM), Engrave, Waterline
- **Tool system** — ToolBit (shape definition), ToolController (feeds/speeds), ToolLibrary
- **Post-processors** — grbl, linuxcnc, mach3, centroid, FANUC, and more
- **Path simulator** — 3D material removal preview
- **C++ core** — `Path::Command` (G-code), `FeatureArea` (libarea), `Voronoi`

CAM is heavily Python-based (~379 .py files), with a lean C++ core for performance-critical path operations.

---

## 🏗️ Architecture

### Job Container

```
CAM Job
  ├── Stock (raw material definition)
  │    ├── CreateBox / CreateCylinder / CreateFromBase
  │    └── Bounding box + offset
  ├── ToolController (tool + feeds/speeds)
  │    └── ToolBit (shape: endmill, drill, ballnose, etc.)
  ├── Operations[]
  │    ├── Profile (contour cutting)
  │    ├── Pocket (area clearing)
  │    ├── Drilling (hole cycles)
  │    ├── Surface (3D surfacing)
  │    ├── Adaptive (HSM clearing)
  │    ├── Engrave (V-carving)
  │    ├── Waterline (Z-level contouring)
  │    ├── Slot (slot milling)
  │    ├── Helix (helical boring)
  │    ├── Deburr (edge chamfering)
  │    └── ThreadMilling
  ├── DressUp (modifications)
  │    ├── DressupDogbone (corner relief)
  │    ├── DressupTag (holding tabs)
  │    ├── DressupRampEntry (ramp plunge)
  │    └── DressupLeadInOut (approach/retract)
  └── Post-Processor → G-code file
```

### C++ Core (libPath)

| Class | Purpose |
|---|---|
| `Path::Command` | Single G-code command (G0, G1, G2, G3, etc.) |
| `Path::Toolpath` | Ordered sequence of Commands |
| `Path::FeaturePath` | DocumentObject containing a Toolpath |
| `Path::FeatureArea` | 2D area operations (libarea) |
| `Path::FeatureAreaView` | Area visualization |
| `Path::Voronoi` | Voronoi diagram for medial axis |

### Tool System

```
ToolBit (JSON shape definition)
  ├── endmill, ballnose, bullnose
  ├── drill, chamfer, engraver
  ├── probe, slittingsaw
  └── thread_mill, form_mill

ToolController
  ├── references a ToolBit
  ├── SpindleSpeed (RPM)
  ├── HorizFeed (mm/min)
  ├── VertFeed (mm/min)
  └── HorizRapid, VertRapid
```

### Post-Processors

| Post-Processor | Target CNC |
|---|---|
| `grbl_post` | GRBL controllers |
| `linuxcnc_post` | LinuxCNC |
| `mach3_mach4_post` | Mach3/Mach4 |
| `centroid_post` | Centroid CNC |
| `refactored_*` | Modernized post-processors |

Post-processors transform internal `Path::Command` sequences into machine-specific G-code dialects.

### Path Simulator

3D visualization of material removal:
- Voxel-based stock subtraction
- Step-through playback
- Speed control
- Tool visualization

---

## 🐍 Python API

```python
import FreeCAD as App
import CAM

doc = App.newDocument()
# Create a Job from a body
job = doc.addObject("CAM::Job", "Job")
job.Model = my_body

# Operations are added via GUI or scripting
# Post-process to G-code
import CAMPost
CAMPost.export(job, "/path/to/output.gcode", "grbl")
```

---

## 📅 Historical Timeline

| Year | Milestone |
|---|---|
| 2014 | Path workbench created (initial toolpath support) |
| 2016 | Basic operations (Profile, Pocket, Drilling) |
| 2017 | Tool library system |
| 2018 | ToolBit system (shape-based tools) |
| 2019 | Surface/3D operations |
| 2020 | Adaptive clearing (HSM), improved pocket |
| 2022 | **Renamed Path → CAM** |
| 2023 | Refactored post-processors |
| 2024 | Thread milling, improved simulator |
| 2025 | Simulator enhancements, DressUp improvements |

---

## 📂 Key Files

| File | Purpose |
|---|---|
| `App/Command.h/cpp` | G-code command class |
| `App/Path.h/cpp` | Toolpath container |
| `App/FeaturePath.h/cpp` | Path document object |
| `App/FeatureArea.h/cpp` | 2D area operations |
| `App/Voronoi.h/cpp` | Voronoi diagram |
| `App/libarea/` | Area offset/pocket library |
| `Path/Op/Profile.py` | Profile operation |
| `Path/Op/Pocket.py` | Pocket operation |
| `Path/Op/Drilling.py` | Drilling operation |
| `Path/Op/Surface.py` | 3D surface operation |
| `Path/Op/Adaptive.py` | HSM adaptive clearing |
| `Path/Post/` | Post-processor scripts |
| `Path/Tool/Bit.py` | ToolBit definition |
| `Path/Tool/Controller.py` | ToolController |

---

## 🔗 Dependency Graph

```
CAM depends on:
  ├── Part (TopoShape for geometry)
  ├── App (Document, Property)
  └── libarea (2D offset/pocket algorithms)

Used by:
  └── CNC machining workflows
```

---

*Part of the [FreeCAD Documentation Hub](../README.md)*
