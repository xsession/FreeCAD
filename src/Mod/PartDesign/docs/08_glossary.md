# 08 — Glossary

> **Classification:** Reference · **Audience:** All stakeholders  
> **Format:** Alphabetical, with cross-references and source locations

---

## A

### Additive Feature
A PartDesign feature that **adds** material to the body (e.g., Pad, Revolution).
Inherits from `PartDesign::FeatureAddSub` with type `Additive`.

### AttachmentSupport
A property on `Sketcher::SketchObject` that defines which face or plane the sketch
is attached to. Example: `sketch.AttachmentSupport = [(pad, "Face6")]`.
- **Source:** `Part/AttachExtension.h`

---

## B

### Body
The top-level container in PartDesign that holds a chain of features. Each Body
produces a single solid shape.
- **Source:** `src/Mod/PartDesign/App/Body.h`
- **Python:** `doc.addObject("PartDesign::Body", "Body")`

### BRep (Boundary Representation)
The geometric representation used by OpenCascade where shapes are defined by
their boundary surfaces, edges, and vertices.

---

## C

### C0 Continuity
Two faces sharing an edge are C0 continuous if they meet at that edge (position
continuity only). `getContinuousEdges()` filters for C0 edges, as fillets are
applied to sharp edges.
- **Source:** `FeatureDressUp.cpp`, `BRep_Tool::Continuity()`

### Chamfer
A PartDesign DressUp feature that bevels edges at 45° (or custom angle).
Uses `getContinuousEdges()` to resolve edge references.
- **Source:** `src/Mod/PartDesign/App/FeatureChamfer.h`

### `getContinuousEdges()`
Method on `DressUp` that resolves edge references from `Base.getShadowSubs()`,
filters for C0 continuous edges, and returns them for fillet/chamfer operations.
**This is where the TNP fallback was added.**
- **Source:** `FeatureDressUp.cpp` line ~180

---

## D

### DressUp
Base class for features that modify existing geometry (Fillet, Chamfer, Thickness)
rather than adding/subtracting material.
- **Source:** `src/Mod/PartDesign/App/FeatureDressUp.h`
- **Key Property:** `Base` (PropertyLinkSub — stores object + sub-element references)

---

## E

### Element Map
A bidirectional mapping between TNP names (stable, topology-encoded) and short
names (indexed, like `Face1`, `Edge3`). Stored in every `TopoShape`.
- **Source:** `src/App/ElementMap.h`, `src/App/ElementMap.cpp`
- **Python:** `shape.ElementMap`, `shape.ElementReverseMap`, `shape.ElementMapSize`

### `ELEMENT_MAP_PREFIX`
The character `";"` that marks the beginning of a mapped element name.
- **Source:** `src/App/ElementNamingUtils.h` line 52
- **Value:** `";"`

### `ElementMapVersion`
A version string on the Body's shape that indicates whether element maps are active.
Empty string = legacy mode (no TNP). Non-empty = TNP-aware mode.
- **Python:** `body.Shape.ElementMapVersion`

### `ElementNamePair`
A struct containing `{newName, oldName}` — the TNP-encoded name and the short
indexed name for a sub-element reference.
- **Source:** `src/App/ElementNamingUtils.h` line ~25

---

## F

### Fallback (TNP Fallback)
The mechanism added in this fix: when a TNP-encoded name (`newName`) can't be
resolved, strip the `?` prefix from `oldName` and try the short indexed name.
- **Source:** `FeatureDressUp.cpp`, `getContinuousEdges()` + `getFaces()`

### `FC_WARN`
FreeCAD's warning macro. Outputs to the Report View and log files.
- **Source:** `src/Base/Console.h`
- **Example:** `FC_WARN(getFullName() << ": mapped edge name is stale")`

### Fillet
A PartDesign DressUp feature that rounds edges with a specified radius.
Uses `getContinuousEdges()` to resolve edge references.
- **Source:** `src/Mod/PartDesign/App/FeatureFillet.h`

### FlatFace
A `MapMode` for sketch attachment. The sketch is mapped flat onto a planar face.
- **Python:** `sketch.MapMode = "FlatFace"`

---

## G

### `getFaces()`
Method on `DressUp` that resolves face references from `Base.getShadowSubs()`.
Used by Thickness feature. **TNP fallback was also added here.**
- **Source:** `FeatureDressUp.cpp` line ~255

### `getSubShape()`
Method on `TopoShape` that resolves a sub-element name to a `TopoDS_Shape`.
Returns null if the name can't be resolved.
- **Source:** `src/Mod/Part/App/TopoShape.h`
- **Signature:** `TopoDS_Shape getSubShape(const char* name, bool silent = false)`

### `getShadowSubs()`
Method on `PropertyLinkSub` that returns the internal TNP-aware representation
of sub-element references as `vector<ElementNamePair>`.
- **Source:** `src/App/PropertyLinks.h`

---

## M

### `MISSING_PREFIX`
The character `"?"` prepended to `oldName` in a shadow sub when PropertyLinks
cannot resolve the TNP-encoded `newName`. This signals that the mapping is stale.
- **Source:** `src/App/ElementNamingUtils.h` line 57
- **Value:** `"?"`
- **Example:** `oldName = "?Edge1"` means `Edge1` reference may be stale

### MapMode
Defines how a Sketch is mapped onto its support surface.
- `"FlatFace"` — flat onto a planar face
- `"Deactivated"` — no automatic mapping
- **Source:** `Part/AttachExtension.h`

---

## N

### `newName`
The TNP-encoded, topology-stable name in a shadow sub's `ElementNamePair`.
Example: `";#f:1;:G;XTR;:H353:7,E.Edge1"`.
When this name is stale (can't be resolved against the current element map),
the fallback mechanism tries `oldName` instead.

---

## O

### `oldName`
The short indexed name in a shadow sub's `ElementNamePair`.
Example: `"Edge1"` or `"?Edge1"` (with MISSING_PREFIX).

### OpenCascade (OCC / OCCT)
The open-source CAD kernel used by FreeCAD for geometric operations.
Provides `TopoDS_Shape`, `BRepFilletAPI_MakeFillet`, etc.
- **Website:** https://dev.opencascade.org/

---

## P

### Pad
A PartDesign feature that extrudes a sketch profile to create a solid.
- **Source:** `src/Mod/PartDesign/App/FeaturePad.h`
- **Python:** `doc.addObject("PartDesign::Pad", "Pad")`

### `POSTFIX_TAG` / `;:H`
The postfix in a TNP name that marks the history tag (feature hash).
- **Source:** `src/App/ElementNamingUtils.h` line 68
- **Example:** In `";#f:1;:G;XTR;:H353:7,E.Edge1"`, `;:H353` is the history tag

### Pocket
A PartDesign feature that cuts material by extruding a sketch profile inward.
- **Source:** `src/Mod/PartDesign/App/FeaturePocket.h`

### PropertyLinkSub
An App property type that stores a reference to a document object plus a list
of sub-element names. Used by DressUp's `Base` property.
- **Source:** `src/App/PropertyLinks.h`
- **Python:** `fillet.Base = (pad, ["Edge1"])`

---

## R

### Recompute
The process of updating a feature's shape based on its inputs. Triggered by
`doc.recompute()` or parameter changes.

### Reverse Map
`ElementReverseMap`: a dictionary mapping short names → TNP names.
The inverse of `ElementMap`.
- **Python:** `shape.ElementReverseMap`

---

## S

### Shadow Subs
The internal TNP-aware representation of sub-element references stored by
`PropertyLinkSub`. Contains `ElementNamePair` entries with both the TNP
name and the short indexed name.
- **Access:** `Base.getShadowSubs()`

### Short Name
An indexed element name like `Face1`, `Edge3`, `Vertex7`. These are
position-dependent and can shift when topology changes — the core TNP issue.

### Stale Name
A TNP-encoded name that can no longer be resolved against the current element
map because the parent shape was recomputed with different topology.

### Subtractive Feature
A PartDesign feature that **removes** material from the body (e.g., Pocket).

---

## T

### Thickness
A PartDesign DressUp feature that shells a solid, making it hollow.
Uses `getFaces()` to resolve face references.
- **Source:** `src/Mod/PartDesign/App/FeatureThickness.h`

### TNP (Topological Naming Problem)
The fundamental issue in parametric CAD where downstream features lose their
references to upstream geometry after model modifications. FreeCAD's element
map system is designed to solve this. This fix addresses a gap in the DressUp
feature family.

### TNP Name
A topology-encoded, stable element name. Example:
`";#f:1;:G;XTR;:H353:7,E.Edge1"`. See also: Element Map.

### `TopoDS_Shape`
The OpenCascade type representing any topological shape (solid, face, edge,
vertex, etc.). FreeCAD wraps this in `Part::TopoShape`.

### `TopoShape`
FreeCAD's wrapper around `TopoDS_Shape` that adds element map support,
mapper infrastructure, and Python bindings.
- **Source:** `src/Mod/Part/App/TopoShape.h`

---

## Symbols

### `?` (Question Mark Prefix)
See: MISSING_PREFIX

### `;` (Semicolon Prefix)
See: ELEMENT_MAP_PREFIX

### `;:H` (History Tag)
See: POSTFIX_TAG

---

## Quick Reference Card

```
┌──────────────────────────────────────────────────────────────┐
│                    QUICK REFERENCE CARD                        │
│                                                              │
│  TNP Name:     ";#f:1;:G;XTR;:H353:7,E.Edge1"              │
│  Short Name:   "Edge1"                                       │
│  Stale Old:    "?Edge1"  (MISSING_PREFIX + short name)       │
│                                                              │
│  Key Methods:                                                │
│  getContinuousEdges()  ← Fillet, Chamfer (edge references)  │
│  getFaces()            ← Thickness (face references)         │
│  getShadowSubs()       ← Returns [{newName, oldName}, ...]  │
│  getSubShape()         ← Resolves name to OCC shape         │
│                                                              │
│  Key Files:                                                  │
│  FeatureDressUp.cpp    ← THE FIX                            │
│  ElementNamingUtils.h  ← Constants (MISSING_PREFIX, etc.)   │
│  PropertyLinks.cpp     ← Shadow sub management              │
│  TestSketchOnFace.py   ← 30 tests                           │
│                                                              │
│  Test Command:                                               │
│  FreeCADCmd --run-test PartDesignTests.TestSketchOnFace      │
└──────────────────────────────────────────────────────────────┘
```

---

*← Back to [README](./README.md)*
