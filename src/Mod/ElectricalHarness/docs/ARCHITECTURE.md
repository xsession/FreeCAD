# Electrical Harness & Schematics Workbench Architecture

## 1. Executive Design Summary
Electrical Harness & Schematics Workbench is designed as a domain-first FreeCAD module where a canonical connectivity model drives synchronized outputs: 2D schematics, 3D routed harness representation, and manufacturing deliverables. The initial implementation is Python-first with explicit service boundaries around route solving, flattening, and heavy graph operations so targeted C++ migration can happen without UI rewrites.

Design intent:
- Source of truth: normalized electrical model with stable IDs.
- Representations: schematic, 3D, and manufacturing are projections of the same model.
- Determinism: reproducible route and report generation with lock/freeze regions.
- Enterprise UX: dockable browsers, validation panel, table-centric bulk edits.
- Integratability: import/export and adapter interfaces for ERP/PLM/PDM evolution.

## 2. Competitor Analysis
| Platform | What It Does Well | Data-Model Strengths | Schematic-3D Continuity | Manufacturing/Formboard | Library & Variant Strategy | Collaboration Notes | Emulate | Avoid |
|---|---|---|---|---|---|---|---|---|
| Creo Schematics + Routed Systems | Tight MCAD route context, disciplined harness flow | Robust object identities and route context linkage | Schematic intent drives route guides and bundle realization | Strong downstream harness docs and route consumables | Reusable symbols and parameterized components | Strong in enterprise PLM contexts | Deterministic schematic-driven 3D pipeline | Over-coupling workflows to single CAD assumptions |
| Siemens Capital / VeSys | End-to-end electrical to manufacturing continuity | Deep wiring semantics, manufacturability fields | Back-annotation between logical and physical | Excellent harness manufacturing datasets | Mature reusable libraries and product-line variants | Multi-user and process-ready | Manufacturing-grade traceability in each entity | Excessive process overhead for mid-size teams |
| Zuken E3.series | Object-oriented electrical design rigor | Strong class-like object model and lifecycle | Strong synchronized object references across views | Good nailboard and harness manufacturing outputs | Enterprise library governance | Team-ready with controlled data governance | Object model discipline and schema clarity | Monolithic UX patterns that are hard to adapt |
| Eplan Electric P8 / Harness proD | Device-driven engineering and automation | Strong device and terminal semantics | Solid project-wide consistency checks | Very strong reports and device-centric BOM outputs | Template and macro heavy reuse | Integrates well into enterprise automation | Auto-numbering, cross references, and report automation | UI complexity that obscures model intent |
| SOLIDWORKS Electrical | Accessible 2D/3D synchronization for mixed teams | Practical mapping between schematic and 3D components | Bidirectional links with route updates | Reliable cut lists and harness documentation | Reusable symbols, manufacturer parts, and macros | Team workflows available, varies by deployment | Fast cross-probing and practical sync loops | Inconsistent rigor on very large projects |
| Autodesk-style electromechanical flows | Broad ecosystem and exchange patterns | Flexible but heterogeneous schemas | Varies by product combination and connector quality | Good with customization, uneven defaults | Scriptable and extensible catalogs | Cloud and collaboration options available | Open integration posture and API-first mindset | Fragmented workflows without strong canonical model |

## 3. Proposed Software Architecture
Layered architecture:
- App layer: canonical entities, connectivity graph, routing interfaces, flattening core, validation rules, reporting and serialization.
- GUI layer: command system, workbench orchestration, dockable panels, 2D editor widget integration, 3D tools, selection bridge.
- Integration layer: import/export adapters and future ERP/PLM/PDM hooks.

Core architectural decisions:
- Stable IDs exist for all first-class entities.
- Logical and physical relationships are explicit, not inferred from GUI state.
- Route solver and flattening are strategy interfaces, currently deterministic placeholders.
- Validation runs against canonical model and publishes issue IDs for cross-probing.
- Document objects are FreeCAD FeaturePython proxies pointing back to canonical IDs.

## 4. FreeCAD Workbench Module/File Tree
```
src/Mod/ElectricalHarness/
  Init.py
  InitGui.py
  CMakeLists.txt
  App/
    __init__.py
    document_objects.py
    entities.py
    flattening.py
    ids.py
    import_export.py
    model.py
    reports.py
    routing.py
    serialization.py
    services.py
    validation.py
  Gui/
    __init__.py
    editor2d.py
    panels.py
    routing3d_tools.py
    selection_bridge.py
    workbench.py
  Commands/
    __init__.py
    command_registry.py
    object_factory.py
  Resources/
    icons/
      ElectricalHarnessGeneric.svg
      ElectricalHarnessWorkbench.svg
    ui/
    translations/
  Tests/
    __init__.py
    TestElectricalHarness.py
    test_model.py
    test_reports.py
    test_serialization.py
    test_validation.py
  docs/
    ARCHITECTURE.md
    BACKLOG.md
  examples/
    sample_project.ehproj.json
```

## 5. Data Model
Normalized entity classes include:
- Project, Sheet, SymbolDefinition, DeviceDefinition, DeviceInstance.
- ConnectorDefinition, ConnectorInstance, PinCavity, NetSignal.
- Wire, Cable, CoreConductor, Splice.
- Bundle, BundleSegment, RouteNode, RouteGuide.
- Covering, ClipClampSupport, BackshellAccessory.
- ManufacturingView, ReportDefinition, ValidationIssue, RevisionInfo.

Relationship model:
- Logical: NetSignal links wire-level connectivity across PinCavity nodes.
- Physical: BundleSegment and RouteNode represent routed realization.
- Manufacturing: Flattened segments maintain source segment traceability.
- Reporting: report rows are generated from canonical IDs with deterministic ordering.

## 6. UI/UX Specification
Primary work areas:
- Left: project browser and library browser dock widgets.
- Center: schematic canvas or 3D route context.
- Right: property editor (FreeCAD native + task panels).
- Bottom: validation and report output panels.

Interaction standards:
- Selection bridge supports cross-probing and synchronized highlights.
- Command set maps to task-centric actions (new project, connector, route, validate, report).
- Workbench initialization sets predictable menu/toolbar grouping.
- Future work: command palette actions, batch table editing, and persistent layouts.

## 7. Implementation Roadmap
Phase 1 (Completed in this scaffold):
- Architecture docs, feature map, competitor comparison, FreeCAD integration plan.
- Canonical model skeleton and module tree.

Phase 2 (In progress through scaffold):
- Workbench registration, command registration, object proxy factories.
- Basic library/project/validation/report panel placeholders.
- Serialization format and sample project.

Phase 3:
- Validation expansion (cavity, shielding, bend radius, attribute completeness).
- Flattening/formboard geometry and branch breakout semantics.
- Cross-probing across schematic entities and 3D route entities.

Phase 4:
- Performance profiling, hotspot extraction to C++ adapters.
- Packaging, production test datasets, user/developer docs.
- Multi-user and integration adapter hardening.

## 8. Risk Register
| Risk | Impact | Mitigation |
|---|---|---|
| Python-only routing for large harnesses is too slow | High | Keep solver interface stable and migrate internals to C++ incrementally |
| Incomplete 2D editor capability delays adoption | High | Implement table-driven editing and netlist-first workflows early |
| Mismatch between FreeCAD document objects and canonical model | High | Treat FeaturePython as view adapters; preserve canonical IDs in properties |
| Library schema drift across projects | Medium | Versioned schemas and migration hooks in serializer |
| Collision and clearance checks expensive in dense assemblies | Medium | Cache geometry queries and isolate geometry-intensive services |
| Back-annotation ambiguity from 3D edits | Medium | Enforce explicit override/lock semantics and change provenance |

## 9. Suggested Libraries and Technologies
- Python stdlib dataclasses/json/csv for deterministic baseline.
- NetworkX optional for large graph analytics (deferred dependency).
- pydantic or msgspec optional for strict schema validation at integration boundaries.
- FreeCAD FeaturePython objects for document-level persistence and undo integration.
- Qt/PySide dock widgets and scene-based 2D editor scaffolding.

## 10. Starter Code Skeleton
Starter scaffolding includes:
- App services: model, validation, routing, flattening, reports, serialization.
- Gui services: workbench, panel stubs, selection bridge, schematic widget entry point.
- Commands: object creation, validation trigger, report trigger, architecture quick-open.
- Tests: model, serialization, validation, report smoke coverage.

## 11. First-Pass Implementation Notes
Implemented scope is intentionally architecture-heavy and production-oriented:
- Canonical model exists and can serialize/deserialize deterministically.
- Validation and reporting pipelines are operational with test coverage.
- Workbench menus/toolbars and dock panel placeholders are wired.
- Required document object types are present as stable FeaturePython proxies.

Next implementation slice should prioritize:
- Net-aware schematic editing commands.
- Route corridor definition and branch editor in 3D context.
- Formboard generation with connector breakout and accessory annotation.
