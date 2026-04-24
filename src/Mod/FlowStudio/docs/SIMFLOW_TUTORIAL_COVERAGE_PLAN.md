# FlowStudio SimFlow Tutorial Coverage Plan

## Goal

Replicate the full public SimFlow tutorial catalog as FlowStudio-native guided workflows, scaffold commands, and capability-driven setup paths, without cloning SimFlow's UI literally.

The target is intent parity:

- the same engineering example should be discoverable in FlowStudio
- the same core setup path should be achievable with FreeCAD-native document objects
- the same benchmark result checks should be expressible through FlowStudio workflow guidance, templates, and post-processing

This plan treats the SimFlow catalog as a capability map, not a page-by-page UI imitation exercise.

## Inventory Snapshot

The current SimFlow tutorial index exposes 28 examples:

1. Airfoil (NACA 0012)
2. Blood Flow
3. Wind around Buildings
4. Car
5. Catalytic Converter
6. Clean Room Ventilation
7. Cooling Channel
8. Cyclone Separator
9. Cylinder Cooling
10. Dam Break
11. Droplet
12. Electronics Cooling
13. Garage Ventilation
14. Gas & Pollutant Dispersion
15. Heat Exchanger
16. Injection Molding
17. Mixing Tank
18. Oblique Shock
19. Internal Pipe Flow
20. Marine Propeller
21. Ship Hull
22. Sloshing Tank
23. Spray Combustion
24. Static Mixer
25. Tesla Valve
26. Turbidity Current
27. Von Karman Vortex Street
28. Wing

## Planning Principles

- Build reusable capability packages first, then bind tutorials to them.
- Prefer one FlowStudio study family to many one-off tutorial commands.
- Keep the document model authoritative: analyses, materials, BCs, sources, regions, monitors, solver settings, and post objects should remain normal FreeCAD objects.
- Use tutorial-specific study recipes only where generic workflow steps are not sufficient.
- Track parity in three layers: workflow guidance, setup automation, and solver/export backend support.

## Current Starting Point

Verified current advantages in the repo:

- generic domain workflow profiles already exist
- `CFD + Conjugate Heat Transfer` already selects an electronics-cooling recipe
- electronics cooling already has a one-click scaffold command and benchmark defaults
- FlowStudio already exposes fans, volume sources, radiation BCs, materials, CFD BCs, mesh objects, and workflow cockpit surfaces
- Phase 0 family scaffolds already exist for external aero, pipe flow, and static mixer
- starter examples already exist for Structural, Electrostatic, Electromagnetic, Thermal, and Optical
- example starters are now registry-driven and grouped by domain in workbench and cockpit surfaces
- non-CFD example starters now also stamp stable `StudyRecipeKey` values and create starter result scaffolds

Verified current gaps:

- no master tutorial catalog exists in-product yet
- no broad study-recipe coverage beyond the electronics-cooling pilot
- no comprehensive family-level scaffold layer yet for rotating machinery, free-surface, or reacting-flow examples, and deeper helper automation is still pending for several CFD tutorial families
- advanced solver-specific backends such as dynamic mesh, MRF orchestration, multiphase region conversion, species transport, spray, MPPIC, and density-based compressible export still need deliberate implementation work

Updated gap assessment after recent implementation:

- the machine-readable catalog now exists, but it still acts mainly as a planning registry rather than an interactive in-product launcher
- study-recipe coverage now extends beyond electronics cooling into multiple CFD families, a dedicated Cooling Channel CHT starter, Buildings/Airfoil/Tesla/Von-Karman starters, and all non-CFD example starters, but more tutorial-family coverage is still needed
- starter examples now have runtime smoke coverage for the built-in non-CFD domains, and cockpit/results surfaces now prefer starter primary result objects before falling back to the generic post-pipeline entry point
- results scaffolding exists for all built-in-domain starters, but benchmark-grade report templates and comparison tooling remain largely future work

## Capability Families

### Phase 0. Foundation CFD Tutorials

Target tutorials:

- Internal Pipe Flow
- Wing
- Car
- Wind around Buildings
- Airfoil (NACA 0012)
- Static Mixer
- Tesla Valve
- Von Karman Vortex Street

Reusable capability package:

- generic internal and external CFD analysis creation
- primitive geometry helpers and import workflow
- 2D plate and external-domain workflows
- force monitors, slices, streamlines, and result scenes
- periodic / arbitrary interface support for Tesla Valve
- parameter-driven setup for airfoil and von Karman validation cases
- passive scalar setup for Static Mixer
- atmospheric inlet support for Buildings

Outcome:

- FlowStudio can cover the most recognizable single-phase tutorial families with a small number of reusable guided workflows.

### Phase 1. Thermal and CHT Tutorials

Target tutorials:

- Electronics Cooling
- Cooling Channel
- Heat Exchanger
- Cylinder Cooling

Reusable capability package:

- fluid + solid multi-region setup
- region interface creation and thermal-contact abstractions
- heat sources, fans, radiation BCs, and material presets
- steady and transient CHT scaffolds
- report templates for temperature, heat flux, and thermal comparison

Outcome:

- FlowStudio becomes credible for the core thermal engineering examples. Electronics Cooling is the pilot and should become the template for the other three.

### Phase 2. Advanced Internal / Environmental Tutorials

Target tutorials:

- Catalytic Converter
- Clean Room Ventilation
- Garage Ventilation
- Blood Flow

Reusable capability package:

- porous regions and porous baffles
- source terms, fans, and passive scalar / residence-time workflows
- imported time-profile boundary conditions
- non-Newtonian material models such as Bird-Carreau
- validation and monitor presets for HVAC / ventilation studies

Outcome:

- FlowStudio handles realistic environmental and process-flow examples without needing full reacting-flow backends.

### Phase 3. Free-Surface and Multiphase Tutorials

Target tutorials:

- Droplet
- Dam Break
- Turbidity Current
- Injection Molding

Reusable capability package:

- VOF and multiphase initialization wizards
- geometry-based phase patching helpers
- 2D free-surface workflow presets
- three-phase support for turbidity-current-style problems
- non-Newtonian plus free-surface export path for injection molding

Outcome:

- FlowStudio can reproduce the core transient multiphase benchmark family with shared setup patterns instead of bespoke dialogs.

### Phase 4. Rotating and Moving-Mesh Tutorials

Target tutorials:

- Marine Propeller
- Mixing Tank
- Ship Hull
- Sloshing Tank

Reusable capability package:

- MRF zone objects and presets
- rotating zone / arbitrary interface helpers
- rigid dynamic mesh support
- six-degree-of-freedom constraints and moving-body setup
- run comparison tooling for multi-case motion benchmarks

Outcome:

- FlowStudio gains real rotating-machinery and moving-domain credibility rather than just static fan placeholders.

### Phase 5. Reacting, Particle, and Compressible Tutorials

Target tutorials:

- Gas & Pollutant Dispersion
- Cyclone Separator
- Spray Combustion
- Oblique Shock

Reusable capability package:

- species transport and mixture setup
- Lagrangian particle injection, parcel models, and particle post-processing
- MPPIC / discrete-phase orchestration
- spray and combustion mechanism import
- density-based compressible solver export and shock-visualization support

Outcome:

- FlowStudio reaches the most backend-heavy part of the SimFlow parity story.

## Example Coverage Matrix

| Tutorial | Family | Core physics pattern | Current posture | Planned phase |
|---|---|---|---|---|
| Internal Pipe Flow | Foundation CFD | steady incompressible internal flow | family scaffold implemented | Phase 0 |
| Wing | Foundation CFD | steady external aero | family scaffold implemented | Phase 0 |
| Car | Foundation CFD | steady external aero with moving ground | family scaffold implemented | Phase 0 |
| Wind around Buildings | Foundation CFD | steady atmospheric external flow | starter scaffold implemented, atmospheric profile refinement still pending | Phase 0 |
| Airfoil (NACA 0012) | Foundation CFD | 2D airfoil external flow | starter scaffold implemented, richer airfoil automation still pending | Phase 0 |
| Static Mixer | Foundation CFD | transient single-phase + passive scalar | family scaffold implemented | Phase 0 |
| Tesla Valve | Foundation CFD | steady internal flow + periodic AMI | starter scaffold implemented, periodic-interface workflow still pending | Phase 0 |
| Von Karman Vortex Street | Foundation CFD | transient 2D validation case | starter scaffold implemented, richer validation automation still pending | Phase 0 |
| Electronics Cooling | Thermal / CHT | steady CHT + radiation comparison | pilot scaffold already implemented | Phase 1 |
| Cooling Channel | Thermal / CHT | steady CHT multi-zone | starter scaffold implemented, richer multi-region automation still pending | Phase 1 |
| Heat Exchanger | Thermal / CHT | steady CHT with thermal resistances | partial capability | Phase 1 |
| Cylinder Cooling | Thermal / CHT | transient CHT | partial capability | Phase 1 |
| Catalytic Converter | Advanced Internal / Environmental | porous internal flow | partial capability | Phase 2 |
| Clean Room Ventilation | Advanced Internal / Environmental | steady HVAC with porous media + residence time | partial capability | Phase 2 |
| Garage Ventilation | Advanced Internal / Environmental | transient buoyant ventilation with fire source + fan | partial capability | Phase 2 |
| Blood Flow | Advanced Internal / Environmental | transient non-Newtonian internal flow | backend gap in non-Newtonian / profile UX | Phase 2 |
| Droplet | Free-Surface / Multiphase | 2D VOF droplet + pool | partial capability | Phase 3 |
| Dam Break | Free-Surface / Multiphase | transient VOF free surface | partial capability | Phase 3 |
| Turbidity Current | Free-Surface / Multiphase | three-phase free surface | major backend gap | Phase 3 |
| Injection Molding | Free-Surface / Multiphase | non-Newtonian filling with free surface | major backend gap | Phase 3 |
| Marine Propeller | Rotating / Moving Mesh | MRF rotating machinery + periodicity | partial capability | Phase 4 |
| Mixing Tank | Rotating / Moving Mesh | rigid dynamic mesh + rotating zone + VOF | major backend gap | Phase 4 |
| Ship Hull | Rotating / Moving Mesh | free surface + dynamic mesh + 6DoF | major backend gap | Phase 4 |
| Sloshing Tank | Rotating / Moving Mesh | rigid body motion + free surface | major backend gap | Phase 4 |
| Gas & Pollutant Dispersion | Reacting / Particle / Compressible | species + particles + buoyant transient flow | major backend gap | Phase 5 |
| Cyclone Separator | Reacting / Particle / Compressible | MPPIC particles + LES | major backend gap | Phase 5 |
| Spray Combustion | Reacting / Particle / Compressible | spray combustion + Lagrangian droplets | major backend gap | Phase 5 |
| Oblique Shock | Reacting / Particle / Compressible | density-based supersonic compressible flow | major backend gap | Phase 5 |

## Cross-Cutting Workstreams

### 1. Workflow UX workstream

- expand the study-recipe layer from one pilot recipe into a catalog of named study families
- surface tutorial families in the Project Cockpit as recommended study starters
- add capability-aware validation messages that explain what is ready, partial, or unsupported for a chosen tutorial family

### 2. Geometry and meshing workstream

- domain-generation helpers for internal flow, external wind tunnel, 2D plate, and rotating zones
- named patch extraction helpers for outlets, fan inlets, porous floors, and interface surfaces
- multi-region decomposition helpers for CHT and rotating-region workflows

### 3. Physics and export workstream

- turbulence presets and solver-control presets by study family
- non-Newtonian, porous, scalar, species, particle, spray, and compressible export layers
- motion and dynamic mesh support including MRF, rigid zones, and 6DoF constraints

### 4. Results and validation workstream

- benchmark-specific monitors and scene templates
- run-to-run comparison tools for baseline vs radiation, baffles vs no-baffles, angle-of-attack sweeps, and forward vs reverse Tesla valve flow
- source-level tests that guard tutorial catalog integrity, study-family registration, and command exposure

## Immediate Continuation

The next implementation steps should be:

1. continue Phase 1 by extending the electronics-cooling pilot pattern into `Heat Exchanger` and `Cylinder Cooling`
2. deepen the new `Cooling Channel`, `Tesla Valve`, and `Von Karman Vortex Street` starters with richer multi-region automation, periodic-interface orchestration, parameterized validation geometry, and benchmark comparison tooling

## Current Execution Snapshot

Completed since the original roadmap draft:

- machine-readable tutorial coverage registry
- Phase 0 study-family recipes for `Pipe Flow`, `External Aerodynamics`, and `Static Mixer`
- dedicated Phase 0 starter scaffolds for `Wind around Buildings`, `Airfoil (NACA 0012)`, `Tesla Valve`, and `Von Karman Vortex Street`
- dedicated Phase 1 starter scaffold for `Cooling Channel`
- generic scaffold commands for those Phase 0 CFD families
- all-domain starter examples for built-in non-CFD physics domains
- grouped example UI surfaces sourced from physics-domain metadata
- non-CFD workflow recipe overlays and starter result scaffolds
- runtime smoke coverage for the built-in non-CFD starter examples

The roadmap focus has therefore shifted from proving the study-family architecture to hardening it with runtime validation and filling out the remaining tutorial families.

## Success Criteria

This roadmap is successful when:

- every SimFlow tutorial maps cleanly to a FlowStudio study family
- every study family has a documented capability owner and implementation phase
- tutorial parity is expressed through reusable workflow objects and recipes rather than one-off hacks
- benchmark-specific setup defaults remain centralized and testable