# Electrical Harness Backlog

## Completed
- ✅ Canonical model with stable IDs, editing helpers, pin graph, snapshot
- ✅ Project store with observer pattern and per-document models
- ✅ 8 UI-driven commands (NewProject, CreateConnector, CreateWire, RenameNet, CreateRoutePath, Validate, FromToReport, OpenArchitectureDoc)
- ✅ Filterable dock panels with cross-probing, status, row highlighting
- ✅ Selection bridge pub/sub for bidirectional selection sync
- ✅ Validation engine with 10 rules (data integrity, connectivity, splice, manufacturing, structural, routing)
- ✅ Topology-preserving flattening with BFS ordering, connector breakouts, wire-length computation
- ✅ Reports: connector table, pin connection, from-to, wire list, BOM, spool consumption, project summary, wire cut-list, formboard table
- ✅ CSV and JSON export for all report types
- ✅ Document object proxies with domain-specific properties (project stats, connector refs, route params, splice info, covering, formboard, report metadata)
- ✅ Import/export bridge: open/insert/export .ehproj.json with project_store integration and doc object population
- ✅ Schematic editor canvas with connector symbols, draggable placement, pin endpoints, interactive wire drawing, grid/snap, zoom
- ✅ JSON round-trip serialization with format versioning
- ✅ 40+ unit tests covering model, validation, flattening, reports, serialization, project store

## P0 (Foundational)
- Canonical model transaction system (undo/redo via TransactionLog).
- Library database and browser with preview and favorite tags.
- 3D route guide placement and bundle segment editing tools.

## P1 (Workflow Depth)
- Auto wire numbering, cross-references, and table generation.
- Route regeneration after connector movement with lock regions.
- Connector template import from vendor catalogs.
- Rule packs for bend radius, cavity compatibility, and shielding.

## P2 (Production Hardening)
- Performance profiling and targeted C++ migration plan.
- Multi-user change-set merge and revision differencing.
- PLM/ERP adapter contracts and metadata mapping templates.
- Golden-file regression packs for reports and flattening outputs.
- UI polish for large projects: filters, bookmarks, and bulk editors.
