# Base Module (FreeCADBase)

> **Library**: `FreeCADBase.dll` / `libFreeCADBase.so`  
> **Source**: `src/Base/`  
> **Files**: ~72 .cpp · ~72 .h  
> **Dependencies**: Python 3.12, Boost, Xerces-C, zlib, fmt  
> **Architecture SVG**: [base_architecture.svg](../svg/base_architecture.svg)

---

## 📋 Overview

The **Base** module is FreeCAD's lowest-level library — it has **zero dependencies on any other FreeCAD module**. Every other library in the project links against `FreeCADBase`. It provides:

- **Math primitives** (Vector3d, Matrix4D, Placement, Rotation, BoundBox, Axis)
- **Unit/Quantity system** (physical quantities with dimensional analysis)
- **Type system** (RTTI replacement with `BaseClass`, `Type`, `TYPESYSTEM_HEADER` macros)
- **Serialization** (XML reader/writer, zip streams, Persistence interface)
- **Console & logging** (singleton console with observer pattern)
- **Python integration** (interpreter management, GIL helpers, PyObjectBase)
- **Exception hierarchy** (structured C++ exceptions with Python bridging)

---

## 🏗️ Architecture

### Math Primitives

| Class | Purpose |
|---|---|
| `Vector3d` | 3D vector with x/y/z components, dot/cross products |
| `Matrix4D` | 4×4 transformation matrix |
| `Placement` | Position (Vector3d) + Orientation (Rotation) |
| `Rotation` | Quaternion-based rotation |
| `BoundBox` | Axis-aligned bounding box |
| `Axis` | Line defined by point + direction |
| `CoordinateSystem` | Full local frame (origin + 3 axes) |
| `DualQuaternion` | Screw motion representation (added ~2019) |

### Unit System

```
Quantity = numerical value + Unit
Unit = dimensional signature (length, mass, time, angle, ...)
UnitsApi → selects schema → UnitsSchema* (MmGS, Imperial, etc.)
```

The quantity parser handles expressions like `"3.5 mm"`, `"1.2 kg*m/s^2"`, with full lex/parse pipeline (`QuantityLexer`, `QuantityParser`).

### Type System

FreeCAD uses its own RTTI replacement:
- `Type` — runtime type descriptor (name → Type mapping)
- `BaseClass` — root of all FreeCAD type-checked classes
- `TYPESYSTEM_HEADER()` / `TYPESYSTEM_SOURCE()` macros — declare/define type info
- `isDerivedFrom<T>()` / `freecad_cast<T>()` — safe downcasting

### Serialization & IO

- `Persistence` — interface for save/restore to XML
- `Reader` / `Writer` — XML stream abstraction over Xerces-C
- `FileInfo` — cross-platform file metadata
- `Stream` — binary/text stream helpers
- Zip support for `.FCStd` files (actually ZIP archives)

### Console & Logging

```
ConsoleSingleton::Instance()
  .Log("debug: %s", msg)    // verbose
  .Message("info: %s", msg)  // normal
  .Warning("warn: %s", msg)  // yellow
  .Error("error: %s", msg)   // red
```

Observers can attach to the console (GUI log panel, file logger, etc.).

### Parameter System

XML-based user preferences:
```
ParameterGrp → nested groups → string/int/float/bool values
```
Stored in `user.cfg` and `system.cfg`.

---

## 🐍 Python Integration

- `Interpreter` — manages Python runtime lifecycle, GIL acquisition
- `PyObjectBase` — C++ wrapper base for Python-exposed objects
- Generated via XML `.py` export templates (see `*Py.xml` patterns)

---

## ⚠️ Exception Hierarchy

```
Exception
├── RuntimeError
│   └── CADKernelError
├── ValueError
│   ├── BadFormatError
│   └── RestoreError
├── TypeError
├── AttributeError
├── NotImplementedError
└── AbortException
```

All exceptions bridge to Python equivalents.

---

## 📅 Historical Timeline

| Year | Milestone |
|---|---|
| 2002 | Initial creation — Jürgen Riegel's PhD framework |
| 2006 | Unit system foundations |
| 2014 | Quantity/UnitsApi rewrite |
| 2019 | DualQuaternion added |
| 2023 | Type system modernization, `freecad_cast<>` |
| 2025 | `#pragma once` migration, header cleanup |
| 2026 | SPDX license headers |

---

## 📂 Key Files

| File | Purpose |
|---|---|
| `Vector3D.h/cpp` | 3D vector primitives |
| `Placement.h/cpp` | Position + rotation |
| `Quantity.h/cpp` | Physical quantity with units |
| `Unit.h/cpp` | Dimensional unit system |
| `Type.h/cpp` | Runtime type descriptors |
| `BaseClass.h/cpp` | Root of type hierarchy |
| `Console.h/cpp` | Logging singleton |
| `Parameter.h/cpp` | XML preferences |
| `Persistence.h/cpp` | Serialization interface |
| `Interpreter.h/cpp` | Python runtime management |
| `PyObjectBase.h/cpp` | C++→Python bridge base |

---

## 🔗 Dependency Graph

```
Base depends on:
  ├── Python 3.12 (runtime + API)
  ├── Boost (filesystem, regex, program_options)
  ├── Xerces-C (XML parsing)
  ├── zlib (compression for .FCStd)
  └── fmt (string formatting)

Used by:
  └── Everything (App, Gui, all modules)
```

---

*Part of the [FreeCAD Documentation Hub](../README.md)*
