# Electrical Harness Workbench — Competitive Deep-Dive & Target Specification

> **Purpose**: Define the feature set, quality bar, performance targets, and UX
> standards required for the FreeCAD Electrical Harness Workbench to match or
> surpass the commercial state of the art.
>
> **Research date**: April 2026
>
> **Sources surveyed**: Siemens Capital (Formboard Designer, Wiring Harness
> Designer, Wiring Harness Analyzer), Zuken E3.series (E3.schematic, E3.cable,
> E3.formboard), Dassault CATIA Electrical & Fluid Engineering, Altium Designer
> Harness Design, RapidHarness by Highlight Labs, EPLAN Harness proD, VEC
> (Vehicle Electric Container) v2.2.0, KBL (Kabelbaum Liste) v2.5, SAE AS50881H.

---

## 1. Competitive Landscape Summary

### 1.1 Siemens Capital (formerly Mentor Graphics)

| Module | Key Differentiators |
|---|---|
| **Capital Wiring Harness Designer** | Full digital thread from E/E architecture to production. Topology-driven routing with constraint propagation. Cross-domain integration (AUTOSAR, network, embedded). |
| **Capital Formboard Designer** | True 1:1 scale formboard generation with automatic branch layout, connector breakout positioning, nail/peg placement, coverings annotation. |
| **Capital Formboard Manager** | Multi-formboard management for variant-heavy programs (automotive 150 % schematics). |
| **Capital Wiring Harness Analyzer** | DRC engine: bend radius, fill ratio, shielding continuity, splice rules, connector cavity compatibility. Real-time incremental checking during authoring. |
| **Capital EE Insight / Publisher** | Interactive HTML/PDF harness documentation for service manuals. Cross-probing from 3D model via SVG overlays. |
| **Capital Enterprise Management** | PLM-grade revision control, BOM synchronization, ECO workflow. |
| **Capital Connectors** | Vendor-neutral component library with automated cavity mapping, pin assignment, and terminal selection. |

**Takeaways for our workbench**:
- Formboard must be 1:1 scale-capable with printable tiled output.
- Validation must run incrementally, not just batch.
- PLM integration (ECO, revision diff) is table-stakes for enterprise adoption.
- Variant/effectivity management (150 % schematics) is P1.

### 1.2 Zuken E3.series (E3.schematic + E3.cable)

| Capability | Detail |
|---|---|
| **Object-oriented schematic** | Symbols carry electrical semantics; changes propagate bi-directionally to cable plans. |
| **150 % variant schematics** | A single project encodes all option combinations; filtering produces customer-specific outputs in minutes vs. hours. |
| **Automated operations** | Auto wire numbering, cross-reference generation, terminal strip documentation. |
| **Cable plan + harness layout** | Combine wires into cables, assign connectors with pin/cavity mapping, add shielding, twisted pairs, and coverings. |
| **Manufacturing outputs** | Single-line diagrams, wiring diagrams, cable plans, BOM, cut lists, connection tables, terminal strip tables. |
| **Component Cloud** | 3-tier certified library (Basic/Certified/Premium) with eCl@ss attributes and 3D shapes from leading manufacturers. |

**Takeaways**:
- Auto wire numbering and cross-reference generation are expected.
- Library must support multi-tier certification and cloud sync.
- Cable (multi-conductor) and twisted-pair structures are first-class.

### 1.3 Dassault CATIA (Electrical & Fluid Engineering)

| Capability | Detail |
|---|---|
| **3D harness routing** | Bundle routing along guide curves in CATIA 3D, with clash detection against mechanical product structure. |
| **Electrical schematic ↔ 3D sync** | Schematic connectivity drives 3D routing; changes in either domain propagate. |
| **Flatten / formboard** | 3D harness is flattened to 2D formboard preserving branch topology and wire lengths. |
| **Integrated simulation** | Electromagnetic compatibility (EMC) proximity checks, thermal de-rating rules. |
| **PLM backbone** | 3DEXPERIENCE platform provides change management, configuration, and multi-site collaboration. |

**Takeaways**:
- 3D routing with clash detection against the FreeCAD assembly is a killer feature.
- Schematic ↔ 3D bidirectional sync is the gold standard.
- EMC/thermal rule packs are differentiators for aerospace/automotive.

### 1.4 Altium Designer (Harness Design module)

| Capability | Detail |
|---|---|
| **Wiring diagram** (`.WirDoc`) | Place wires, cables, splices, connectors with pin-level connectivity. Supports multi-board harness projects. |
| **Layout drawing** (`.LdrDoc`) | Physical arrangement: bundles, coverings, labels, dimensional annotations. |
| **Manufacturing drawing** (`.HarDwf`) | Draftsman document with read-only views of wiring + layout + BOM + additional manufacturing callouts. |
| **ActiveBOM** | Live bill of materials with connector parts, cavities, coverings, wire lengths, splice parts. Length is BOM-aware. |
| **Output Job** | Pre-configured output sets (PDF, Excel) for repeatable release. Automated one-touch release with snapshot + validation + output generation. |
| **Multi-board integration** | Harness project connects to PCB designs within the same multi-board project; logical PCB-to-PCB connections define harness connectivity. |
| **Version control + Workspace** | Altium 365 cloud workspace with design review, commenting, and release management. |

**Takeaways**:
- Three-document structure (wiring → layout → manufacturing) is clean.
- One-touch release (snapshot → validate → generate → release) should be replicated.
- BOM must be wire-length-aware.
- Multi-board / multi-domain integration (PCB ↔ harness) is emerging standard.

### 1.5 RapidHarness (Highlight Labs)

| Capability | Detail |
|---|---|
| **Instant automatic drawing** | Real-time schematic auto-layout as components are placed. |
| **Formboard to scale** | 1:1 formboards ready for production. |
| **Manufacturing documents** | Auto-generated: Top-Level Drawing (PDF), BOM (Excel), Wiring Tables, Cut Lists, Notes, Labels, Netlists. |
| **Parts library** | 80M+ component database with generic→specific progression. |
| **Team collaboration** | Shared library, partnerships with external orgs, per-item permissions. |
| **Version control** | Integrated versioning, immutable releases, design cloning, subdesign updates. |
| **Power tools** | Rule Checker, Design Configurations, Bundle Inspection, Connection Remapping, Terminal Type Switching, BOM editing/sorting. |
| **System-level design** | Hierarchical subassemblies, signal propagation through networks of harnesses. |
| **Additional features** | Strip lengths, wire twisting, cable shielding, internal part numbers, customizable tables, revision details, build notes, harness coverings, bundle labels. |

**Takeaways**:
- Real-time auto-layout is a major UX differentiator.
- Strip lengths, wire twisting, and cable shielding are specific manufacturing features.
- System-level decomposition with signal propagation is important for complex vehicles.
- Connection remapping on design change is essential.

### 1.6 EPLAN Harness proD

| Capability | Detail |
|---|---|
| **3D MCAD integration** | Import 3D assemblies (STEP, CATIA, NX) and route harness inside mechanical envelope. |
| **Automatic nailboard** | Flatten 3D harness to 2D nailboard/formboard with accurate branch angles and wire lengths. |
| **DRC** | Bend radius, bundle diameter, connector clearance rules. |
| **KBL/VEC export** | Native support for automotive data exchange standards. |

**Takeaways**:
- STEP import for mechanical context is non-negotiable for 3D routing.
- Automatic nailboard generation from 3D is the expected workflow.
- KBL and VEC export must be supported.

---

## 2. Industry Standards & Data Formats

### 2.1 VEC — Vehicle Electric Container (VDA 4968 / PSI 21)

- **Current version**: 2.2.0 (2025)
- **Scope**: End-to-end harness data from architecture through manufacturing.
- **Information model layers**:
  - **Electrological**: Architectural layer, system schematic, wiring, coupling devices.
  - **Product definition**: Component descriptions (connectors, wires, splices, accessories, grommets, channels, fixings, tapes/tubes), instances, composite parts, coupling.
  - **EE-Components**: Internal connectivity, fuses, multi-fuses, relays, component boxes, pinning.
  - **Topology & geometry**: Topology zones, placements/dimensions, routing, protection requirements.
  - **Connectivity**: Net, connection, wiring specification (3 layers distinguished).
  - **External mapping**: Cross-references to external systems.
- **Serialization**: XML Schema (`.vec`), RDF/OWL ontology (`.ttl`), SHACL validation shapes.
- **Key concepts**: Stable identifiers with change tracking, usage nodes, physical properties, custom properties/extensions.
- **Compliance test suite**: Published by prostep ivip for conformance validation.

### 2.2 KBL — Kabelbaum Liste (VDA 4964 / PSI 19)

- **Current version**: 2.5 SR-1
- **Scope**: Harness description list — the physical bill of the harness.
- **Usage**: Primary exchange format between OEMs and Tier-1 harness suppliers (VW VOBES extensions, BMW, Daimler).
- **Content**: Connectors, wires, splices, coverings, clips, route nodes, segments with lengths/diameters.
- **Relationship to VEC**: KBL is the "manufacturing BOM" subset; VEC is the "full engineering" superset. Mapping guidelines exist.

### 2.3 SAE AS50881 — Wiring, Aerospace Vehicle

- **Current version**: Rev H (2023)
- **Scope**: Selection, installation of wiring and wiring devices for aircraft, helicopters, missiles.
- **Content**: Wire derating, bundling rules, separation requirements, EMI shielding, connector selection, support/clamp spacing, bend radius minimums, grounding/bonding.
- **Relevance**: Aerospace harness customers expect AS50881 rule compliance checking.

### 2.4 Other Relevant Standards

| Standard | Domain | Relevance |
|---|---|---|
| **IPC/WHMA-A-620** | Wire harness workmanship | Quality acceptance criteria for crimps, soldering, coverings |
| **SAE J1128 / J1292** | Automotive wire types | Wire specification lookup tables |
| **MIL-DTL-38999** | Military connectors | Connector cavity mapping for defense harnesses |
| **ISO 10303 AP242** | STEP CAD exchange | 3D geometry exchange for harness routing context |
| **LV 112 / LV 123** | VW/Audi cable specs | OEM-specific wire and connector qualification |

---

## 3. Target Feature Specification

### 3.1 Data Model & Architecture

| ID | Feature | Priority | Commercial Parity |
|---|---|---|---|
| DM-01 | **Canonical connectivity model** as single source of truth (net → wire → pin → connector hierarchy) | P0 | All competitors |
| DM-02 | **Stable deterministic identifiers** (UUID5 from namespace + content hash) | P0 | Capital, VEC |
| DM-03 | **Revision tracking** with author, timestamp, diff summaries per entity | P0 | All |
| DM-04 | **Three electrological layers**: architecture, schematic, wiring (per VEC) | P1 | VEC, Capital |
| DM-05 | **Variant/effectivity management** (150 % schematics) | P1 | E3.series, Capital |
| DM-06 | **Cable structure**: multi-conductor cables with shield + twist definitions | P0 | E3.cable, RapidHarness |
| DM-07 | **Signal propagation** through hierarchical harness/device networks | P1 | RapidHarness, Capital |
| DM-08 | **Pin-level internal connectivity** for EE components (relays, fuse boxes) | P1 | VEC, CATIA |
| DM-09 | **Custom properties / extension mechanism** for OEM-specific attributes | P0 | VEC |
| DM-10 | **Transaction log** with undo/redo and merge conflict resolution | P1 | Capital, Altium |

### 3.2 Schematic Editor (2D)

| ID | Feature | Priority | Commercial Parity |
|---|---|---|---|
| SE-01 | **Grid/snap** with configurable spacing | P0 | All |
| SE-02 | **Connector symbol placement** with pin endpoint rendering | P0 | All |
| SE-03 | **Interactive wire drawing** (click pin → click pin, rubber-band preview) | P0 | All |
| SE-04 | **Auto wire numbering** with configurable prefix/suffix rules | P0 | E3.series, Capital |
| SE-05 | **Cross-reference generation** (from/to callouts on each connector) | P0 | E3.series |
| SE-06 | **Symbol library** with parameterized symbols (pin count, orientation) | P0 | All |
| SE-07 | **Multi-sheet schematics** with inter-sheet references | P1 | E3.series, CATIA |
| SE-08 | **Splice symbol** with auto-join semantics | P0 | All |
| SE-09 | **Cable/shielding notation** (multi-conductor bus representation) | P1 | E3.cable |
| SE-10 | **Real-time DRC overlay** (red markers on violations while editing) | P1 | Capital |
| SE-11 | **Auto-layout engine** for schematic aesthetics | P2 | RapidHarness |
| SE-12 | **Copy/paste/duplicate** with net renaming and ID regeneration | P0 | All |
| SE-13 | **Undo/redo** for all editor operations | P0 | All |
| SE-14 | **Zoom to fit / zoom to selection** | P0 | All |
| SE-15 | **Print/export** schematic as PDF/SVG at configurable scale | P0 | All |

### 3.3 3D Routing & Bundle Editing

| ID | Feature | Priority | Commercial Parity |
|---|---|---|---|
| R3-01 | **Import mechanical context** (STEP AP242) for clash envelope | P0 | CATIA, EPLAN |
| R3-02 | **Route guide definition** (spline/polyline along assembly) | P0 | CATIA, Capital |
| R3-03 | **Bundle segment editing** (add/remove wires, adjust diameter) | P0 | All |
| R3-04 | **Automatic routing** with constraint satisfaction (min bend radius, clearance, max fill ratio) | P1 | Capital, CATIA |
| R3-05 | **Route locking** (freeze approved segments during ECO) | P0 | Capital |
| R3-06 | **Covering assignment** per segment (tape, conduit, braided sleeve, heat shrink) with start/end ratios | P0 | All |
| R3-07 | **Clip/clamp/support placement** along route with spacing rules | P1 | CATIA, Capital |
| R3-08 | **Wire slack / service loop** allocation per segment | P1 | Capital |
| R3-09 | **Clash detection** between harness bundle and mechanical parts | P1 | CATIA |
| R3-10 | **Schematic ↔ 3D bidirectional sync** | P1 | CATIA, Capital |
| R3-11 | **Route weight estimation** from wire gauge + covering density | P2 | Capital |

### 3.4 Flattening & Formboard

| ID | Feature | Priority | Commercial Parity |
|---|---|---|---|
| FB-01 | **Topology-preserving flattening** with BFS branch ordering | P0 | All |
| FB-02 | **Connector breakout** visualization with pin-level detail | P0 | Capital, EPLAN |
| FB-03 | **1:1 scale output** with tiled printing for large formboards | P0 | RapidHarness, Capital |
| FB-04 | **Nail/peg auto-placement** for production tooling | P1 | Capital Formboard Manager |
| FB-05 | **Branch angle control** (45°/90° snap options) | P0 | EPLAN |
| FB-06 | **Wire color stripes** along bundles | P0 | RapidHarness |
| FB-07 | **Dimension annotations** (segment lengths, overall) | P0 | All |
| FB-08 | **Covering extent markers** with material callouts | P0 | All |
| FB-09 | **Bundle label** placement with customizable format | P0 | RapidHarness |
| FB-10 | **Splice location markers** | P0 | All |
| FB-11 | **Multi-formboard management** for variant programs | P1 | Capital |
| FB-12 | **Export** as PDF, SVG, DXF for manufacturing | P0 | All |

### 3.5 Validation & Design Rule Checking

| ID | Feature | Priority | Commercial Parity |
|---|---|---|---|
| VL-01 | **Data integrity**: duplicate IDs, dangling refs, orphan pins | P0 | All |
| VL-02 | **Connectivity**: unconnected pins, unused nets, duplicate wires | P0 | All |
| VL-03 | **Splice integrity**: min/max member count, referenced pins exist | P0 | All |
| VL-04 | **Manufacturing readiness**: missing gauge, missing color, missing connector ref | P0 | All |
| VL-05 | **Routing topology**: disconnected graph detection | P0 | Capital |
| VL-06 | **Bend radius** minimum per wire gauge | P1 | Capital, CATIA |
| VL-07 | **Bundle fill ratio** (max % of conduit cross-section) | P1 | Capital |
| VL-08 | **Connector cavity compatibility** (terminal vs cavity size) | P1 | Capital Connectors |
| VL-09 | **Shielding continuity** (shield must terminate at both ends) | P1 | Capital |
| VL-10 | **Wire derating** (current capacity vs bundle temperature) | P2 | AS50881 |
| VL-11 | **EMC separation** (power vs signal proximity rules) | P2 | CATIA, AS50881 |
| VL-12 | **Incremental validation** (check only changed entities + dependents) | P1 | Capital |
| VL-13 | **Custom rule packs** (pluggable Python rule functions) | P1 | — (differentiator) |
| VL-14 | **Validation dashboard** with severity filtering + cross-probing | P0 | Capital |

### 3.6 Reports & Manufacturing Outputs

| ID | Feature | Priority | Commercial Parity |
|---|---|---|---|
| RP-01 | **Connector table** (ref, definition, pin count, placement) | P0 | All |
| RP-02 | **From-to / wire list** (wire, net, from/to pin, gauge, color, connector refs) | P0 | All |
| RP-03 | **BOM** (connectors, wires by gauge/color, splices, coverings, clips — with quantities) | P0 | All |
| RP-04 | **Cut list** (wire ID, cut length with service loop, gauge, color) | P0 | RapidHarness, Altium |
| RP-05 | **Spool consumption summary** (total length per gauge/color) | P0 | Capital |
| RP-06 | **Netlist** (system-level signal propagation table) | P1 | RapidHarness |
| RP-07 | **Terminal strip table** | P1 | E3.series |
| RP-08 | **Pin connection table** (cavity → net mapping) | P0 | All |
| RP-09 | **Project health summary** (entity counts, validation pass/fail) | P0 | — |
| RP-10 | **Export formats**: CSV, JSON, Excel (.xlsx), PDF | P0 | All |
| RP-11 | **Configurable report templates** (user-defined column selection and sorting) | P1 | RapidHarness |
| RP-12 | **Harness label list** (printable labels for bundles and wires) | P1 | RapidHarness |
| RP-13 | **Build notes** (free-text annotations attached to report output) | P1 | RapidHarness |

### 3.7 Data Exchange & Interoperability

| ID | Feature | Priority | Commercial Parity |
|---|---|---|---|
| DX-01 | **Native JSON format** (`.ehproj.json`) with versioned schema | P0 | — (native) |
| DX-02 | **VEC export** (XML, schema v2.2.0 compliant) | P1 | EPLAN, Capital |
| DX-03 | **VEC import** (parse VEC XML into canonical model) | P1 | EPLAN, Capital |
| DX-04 | **KBL export** (XML, schema v2.5) | P1 | EPLAN, Capital |
| DX-05 | **KBL import** (parse KBL XML into canonical model) | P1 | EPLAN, Capital |
| DX-06 | **CSV/Excel import** (wire list, BOM tables for migration from spreadsheets) | P0 | RapidHarness |
| DX-07 | **STEP AP242 import** (3D geometry context for routing) | P1 | CATIA, EPLAN |
| DX-08 | **PDF/SVG schematic export** | P0 | All |
| DX-09 | **DXF formboard export** for CNC nailboard fabrication | P1 | EPLAN |
| DX-10 | **FreeCAD ↔ external ECAD** netlist exchange (KiCad, EAGLE) | P2 | — (differentiator) |

### 3.8 Component Library

| ID | Feature | Priority | Commercial Parity |
|---|---|---|---|
| LB-01 | **Built-in starter library** (generic connectors 2-64 pin, common wire gauges, basic coverings) | P0 | All |
| LB-02 | **User-defined parts** with custom attributes | P0 | All |
| LB-03 | **Part search** with attribute filtering | P0 | All |
| LB-04 | **Favorites / recently used** | P0 | RapidHarness |
| LB-05 | **Generic → specific progression** (design with generic, refine to specific PN later) | P1 | RapidHarness |
| LB-06 | **3D shape association** (link connector definition to STEP/FreeCAD Part) | P1 | Zuken Component Cloud |
| LB-07 | **Multi-tier certification** tracking (basic / certified / premium) | P2 | E3.series |
| LB-08 | **Import from vendor CSV/Excel** | P0 | All |
| LB-09 | **Connector cavity map** editor (define cavity grid, assign pin functions) | P1 | Capital Connectors |

### 3.9 Collaboration & PLM Integration

| ID | Feature | Priority | Commercial Parity |
|---|---|---|---|
| CO-01 | **Version history** per project with immutable snapshots | P0 | RapidHarness, Altium |
| CO-02 | **Revision comparison** (diff two snapshots, highlight added/removed/changed) | P1 | Capital, Altium |
| CO-03 | **ECO workflow** (mark proposed changes, review, approve, apply) | P2 | Capital |
| CO-04 | **Multi-user concurrent editing** with merge resolution | P2 | Capital, CATIA |
| CO-05 | **One-touch release** (snapshot → validate → generate outputs → tag release) | P1 | Altium |
| CO-06 | **External partnership sharing** (read-only or edit per folder/design) | P2 | RapidHarness |
| CO-07 | **FreeCAD document integration** (harness data stored in `.FCStd`, version-tracked with project) | P0 | — (native) |

### 3.10 User Experience & Performance

| ID | Feature | Priority | Target |
|---|---|---|---|
| UX-01 | **Cross-probing** between schematic, 3D view, panels, and property editor | P0 | Select in one → highlight in all |
| UX-02 | **Filterable data panels** (connector browser, validation, reports) with real-time search | P0 | <100ms filter response |
| UX-03 | **Property panel** showing domain-specific attributes for selected object | P0 | Standard FreeCAD integration |
| UX-04 | **Keyboard shortcuts** for all common operations | P0 | Configurable bindings |
| UX-05 | **Dark mode support** | P1 | Follow FreeCAD theme |
| UX-06 | **Context menus** on all interactive items | P0 | Right-click everywhere |
| UX-07 | **Drag-and-drop** from library to schematic/3D | P1 | — |
| UX-08 | **Tutorial / getting-started wizard** | P2 | — |
| UX-09 | **Large project performance**: 500+ connectors, 5000+ wires, 10000+ pins | P1 | <2s full validation, <500ms panel refresh |
| UX-10 | **Lazy loading** for large reports and formboards | P1 | Virtualized tables |
| UX-11 | **Incremental recompute** (only affected entities, not full model) | P1 | <200ms for single-entity change |
| UX-12 | **Memory budget**: <500 MB for 10K wire project | P1 | — |
| UX-13 | **Offline-first**: no network required for core design workflow | P0 | — |
| UX-14 | **Localization** (i18n framework for UI strings) | P2 | English + framework |

---

## 4. Quality Standards

### 4.1 Code Quality

| Metric | Target |
|---|---|
| Unit test coverage | >80% for App/ layer |
| Integration test coverage | >60% for Gui/ + Commands/ |
| Lint clean | flake8 + mypy strict on all Python |
| Documentation | Docstring on every public class/method |
| Maximum cyclomatic complexity | ≤10 per function |

### 4.2 Data Integrity

| Guarantee | Implementation |
|---|---|
| No data loss on crash | Autosave to `.ehproj.json.bak` every 60s |
| Round-trip fidelity | `loads(dumps(model))` == `model` for all entity types |
| Forward-compatible schema | Version field; unknown keys preserved, not dropped |
| VEC/KBL compliance | Pass prostep ivip compliance test suite |

### 4.3 Testing Strategy

| Layer | Approach |
|---|---|
| Entities + Model | Unit tests: every add/remove/query method |
| Validation | One test per rule code, plus edge cases |
| Flattening | Topology permutations: linear, tree, forest, cycle detection |
| Reports | Golden-file regression: CSV/JSON output vs. committed reference |
| Serialization | Round-trip + forward/backward migration tests |
| Import/Export | VEC/KBL schema validation on generated XML |
| GUI Panels | PyTest-Qt: filter, sort, cross-probe, status label |
| Commands | Mock FreeCAD document: verify object creation + model mutation |
| Performance | Benchmark: 500-connector model, validate + flatten + reports < 2s |

---

## 5. Performance Targets

| Operation | 100 connectors | 500 connectors | 2000 connectors |
|---|---|---|---|
| Model load (JSON) | <100ms | <300ms | <1s |
| Full validation | <200ms | <1s | <3s |
| Incremental validation (1 wire change) | <50ms | <100ms | <200ms |
| Flattening | <100ms | <500ms | <2s |
| BOM generation | <50ms | <200ms | <500ms |
| Formboard render (Qt) | <200ms | <1s | <3s |
| Panel filter (10K rows) | <100ms | <100ms | <200ms |
| Serialization (dump) | <100ms | <300ms | <1s |
| Memory footprint | <50 MB | <150 MB | <500 MB |

---

## 6. Architecture Principles

1. **Canonical model is the single source of truth** — GUI, reports, validation,
   and import/export are all derived views of the model.
2. **Observer pattern for synchronization** — panels, 3D, schematic all subscribe
   to model change notifications; no polling.
3. **Domain-first design** — business logic in `App/` has zero Qt/FreeCAD
   dependencies; fully testable outside the runtime.
4. **Pluggable validation** — rule engine accepts user-provided Python functions
   alongside built-in rules.
5. **Standards-aligned data model** — entity hierarchy mirrors VEC/KBL concepts
   for lossless round-trip exchange.
6. **Incremental by default** — validation, recompute, and UI refresh operate on
   changed-entity deltas, not full-model scans.
7. **Offline-first** — all core workflows operate without network; cloud features
   are optional overlays.

---

## 7. Roadmap Alignment

| Phase | Features | Quality Gate |
|---|---|---|
| **Phase 1 (Current)** | Canonical model, schematic editor, validation (10 rules), flattening, reports (9 types), import/export, doc objects, 43 tests | All tests pass; basic DRC works |
| **Phase 2** | Auto wire numbering, cable/shielding structures, 3D route import (STEP), library database with search/favorites, incremental validation | 80% test coverage; 500-connector benchmark met |
| **Phase 3** | VEC/KBL import/export, formboard 1:1 PDF/DXF output, variant management, one-touch release, custom rule packs | VEC compliance tests pass; golden-file regressions |
| **Phase 4** | Schematic ↔ 3D bidirectional sync, clash detection, EMC/thermal rules, multi-user merge, PLM/ECO workflow | Full integration test suite; 2000-connector benchmark met |

---

## 8. Differentiators vs. Commercial Tools

| # | Differentiator | Rationale |
|---|---|---|
| 1 | **Open source + FreeCAD native** | No license cost; full extensibility; community contributions |
| 2 | **Python-first architecture** | Rapid prototyping; user macros; accessible to non-C++ engineers |
| 3 | **Pluggable custom validation rules** | No other tool lets users add DRC rules in Python |
| 4 | **VEC + KBL + JSON** | Triple-format interop: automotive standard + open JSON for scripting |
| 5 | **Integrated with FreeCAD FEM/CFD** | Thermal/EMC simulation via existing FreeCAD workbenches |
| 6 | **Offline-first with optional cloud** | Edge/air-gapped environments (defense, field service) |
| 7 | **FreeCAD macro/scripting API** | Batch operations, CI/CD integration, automated report generation |

---

*This specification is a living document. Update as competitive intelligence
evolves and implementation progresses.*
