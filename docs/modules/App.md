# App Module (FreeCADApp)

> **Library**: `FreeCADApp.dll` / `libFreeCADApp.so`  
> **Source**: `src/App/`  
> **Files**: ~90 .cpp · ~80 .h  
> **Dependencies**: FreeCADBase, OpenCASCADE (partial), Boost  
> **Architecture SVG**: [app_architecture.svg](../svg/app_architecture.svg)

---

## 📋 Overview

The **App** module is FreeCAD's **core application framework**. It manages the document model, property system, expression engine, element maps (Topological Naming Problem), link system, and extension framework. It runs **headlessly** — no GUI dependency — enabling batch processing and scripting.

Key responsibilities:
- **Application singleton** — module registration, document management
- **Document/DocumentObject** — the document tree model
- **Property system** — ~50+ property types for parametric data
- **Expression engine** — spreadsheet-like formulas binding properties
- **Element maps** — topological naming stabilization (TNP)
- **Link system** — lightweight referencing without deep copies
- **Extension framework** — mix-in capabilities for objects

---

## 🏗️ Architecture

### Document System

```
Application (singleton)
  └── Document (one per .FCStd file)
       ├── DocumentObject (features/parts)
       │    ├── PropertyContainer
       │    │    └── Property instances
       │    └── Extensions[]
       ├── Transaction stack (undo/redo)
       └── Dependency graph (recomputation order)
```

- **Application**: Global singleton, manages open documents, module registry, path resolution
- **Document**: Container for all objects in one file. Handles save/load (ZIP of XML + binary), undo/redo via `Transaction`, and dependency-based recomputation
- **DocumentObject**: Base for all features. Has a `Label`, properties, and participates in the dependency graph

### Property System

The property system is FreeCAD's fundamental data model:

| Category | Types |
|---|---|
| **Scalar** | PropertyBool, PropertyInteger, PropertyFloat, PropertyString |
| **Geometric** | PropertyVector, PropertyMatrix, PropertyPlacement |
| **Links** | PropertyLink, PropertyLinkSub, PropertyLinkList, PropertyXLink |
| **Shapes** | PropertyPartShape, PropertyMeshKernel, PropertyComplexGeoData |
| **Collections** | PropertyStringList, PropertyFloatList, PropertyIntegerList |
| **Enums** | PropertyEnumeration |
| **Files** | PropertyFile, PropertyFileIncluded, PropertyPath |
| **Colors** | PropertyColor, PropertyColorList, PropertyMaterial |

Each property:
- Has a name, type, documentation string
- Can be serialized/deserialized (XML + binary)
- Fires change notifications → triggers recomputation
- Can be bound to expressions

### Element Map / TNP System

The **Topological Naming Problem (TNP)** solution is FreeCAD's largest architectural addition (merged 2023):

```
Shape operation (e.g., Fillet)
  → generates new edges/faces
  → ElementMap records:
       old_name → new_name mapping
       hashed via StringHasher for compact storage
  → ComplexGeoData stores element map alongside geometry
  → MappedName / IndexedName for stable references
```

Key classes:
- `ElementMap` — maps old topological names to new ones across operations
- `StringHasher` — compresses element name strings into integer IDs
- `ComplexGeoData` — base for geometry with element maps
- `MappedElement`, `MappedName`, `IndexedName` — name abstractions

### Expression Engine

Allows spreadsheet-like formulas to bind properties:

```
Pad.Length = Spreadsheet.B2 * 2 + 5mm
```

- `Expression` — AST node base class
- `ExpressionParser` — parses formula strings into AST
- `ObjectIdentifier` — resolves `Document.Object.Property` paths
- `OperatorExpression`, `FunctionExpression` — arithmetic & functions
- `VariableExpression`, `NumberExpression` — leaf nodes

### Link System

Added by realthunder (~2019), enables lightweight referencing:

- `Link` — references another object without copying geometry
- `LinkElement` — references a sub-element
- `LinkGroup` — groups links together
- `PropertyLink*` — link property variants with shadow sub-element support

### Extension Framework

Mix-in system for adding capabilities to objects:

```
DocumentObject + GroupExtension → can contain children
DocumentObject + OriginGroupExtension → has origin planes/axes
DocumentObject + GeoFeatureGroupExtension → has local coordinate system
```

- `Extension` — base interface
- `ExtensionContainer` — stores extensions on an object
- Registered via type system, attached at construction

---

## 📅 Historical Timeline

| Year | Milestone |
|---|---|
| 2002 | Document system — Jürgen Riegel's initial framework |
| 2008 | Property framework stabilized |
| 2014 | Expression engine added (spreadsheet binding) |
| 2016 | Expression parser improvements |
| 2019 | Link system (realthunder's Assembly3 branch) |
| 2023 | TNP merge — ElementMap integrated into main branch |
| 2025 | Extension cleanup, dynamic property improvements |
| 2026 | TNP fixes (DressUp fallback, element naming utils) |

---

## 📂 Key Files

| File | Purpose |
|---|---|
| `Application.h/cpp` | Global singleton, module registry |
| `Document.h/cpp` | Document model, save/load, transactions |
| `DocumentObject.h/cpp` | Base feature class |
| `Property.h/cpp` | Property base + container |
| `PropertyStandard.h/cpp` | Scalar property types |
| `PropertyLinks.h/cpp` | Link properties (with TNP support) |
| `PropertyGeo.h/cpp` | Geometric properties |
| `Expression.h/cpp` | Expression AST |
| `ExpressionParser.h/cpp` | Formula parser |
| `ElementMap.h/cpp` | TNP element mapping |
| `ComplexGeoData.h/cpp` | Geometry + element maps |
| `Link.h/cpp` | Link system |
| `Extension.h/cpp` | Extension framework |
| `GeoFeature.h/cpp` | Positioned feature base |
| `Origin.h/cpp` | XY/XZ/YZ planes + X/Y/Z axes |

---

## 🔗 Dependency Graph

```
App depends on:
  ├── Base (everything)
  ├── OpenCASCADE (partial — for ComplexGeoData/shapes)
  └── Boost (graph, signals2)

Used by:
  ├── Gui (view providers, commands)
  └── All Mod/* modules (features extend DocumentObject)
```

---

*Part of the [FreeCAD Documentation Hub](../README.md)*
