# FlowStudio Electronics Cooling Workflow Plan

## Goal

Replicate the core user workflow from the SimFlow electronics-cooling tutorial inside FlowStudio as a guided, product-native CFD study instead of leaving it as an external benchmark users must translate by hand.

## Current Status

The original electronics-cooling pilot is now implemented and has since become the template for broader FlowStudio study-family work.

Completed in code:

- study-recipe selection for `CFD + Conjugate Heat Transfer`
- recipe-aware workflow guide and Project Cockpit integration
- dedicated `New Electronics Cooling Study` scaffold command
- benchmark-oriented default child objects including solver, mesh, post pipeline, fan, heat source, and placeholder BC objects
- stable `StudyRecipeKey` routing so recipe selection does not rely on `AnalysisType` alone
- regression coverage for recipe selection and cockpit / taskpanel wiring

Completed as follow-on architecture built from this pilot:

- additional CFD study-family starters for external aerodynamics, pipe flow, and static mixer
- starter examples for all built-in physics domains
- metadata-driven example surfacing in the workbench and cockpit
- grouped example toolbars / menus by domain instead of one flat starter list
- non-CFD study recipes for Structural, Electrostatic, Electromagnetic, Thermal, and Optical examples
- non-CFD result scaffolds so example starters also create a `PostPipeline` and primary `ResultPlot`

This document remains the benchmark-specific plan for the electronics-cooling family, but it should now be read as the pilot pattern that informed the broader study-family system.

Reference tutorial:

- https://help.sim-flow.com/tutorials/electronics-cooling

## Target Product Outcome

FlowStudio should guide a user through an electronics-cooling conjugate heat transfer study with a recognizable sequence:

1. import board, CPU, and pins geometry
2. create helper geometry for the fan and extracted outlet
3. configure a steady conjugate heat transfer study
4. define separate solid and fluid regions
5. create inlet, outlet, wall, and interface boundaries
6. generate solid and fluid meshes in the correct order
7. configure turbulence, heat source, solver controls, and radiation readiness
8. run the baseline case, then continue with radiation enabled
9. inspect temperature and radiative heat-flux results

## Mapping From SimFlow To FlowStudio

### Geometry

- SimFlow imports `board.stl`, `cpu.stl`, `pins.stl` and creates two helper boxes.
- FlowStudio should treat these as the canonical benchmark geometry set for the recipe.
- The workflow guidance should explicitly call out the fan box and outlet-tool box dimensions from the benchmark.

### Meshing

- SimFlow meshes the solid first, converts it into a sub-region, then remeshes the fluid.
- FlowStudio should guide users through the same two-pass region strategy because it is the most important conceptual step in the tutorial.

### Physics

- The benchmark is a steady CFD study with conjugate heat transfer and a later radiation comparison.
- FlowStudio should surface this recipe when the active analysis is `CFD` with `AnalysisType = Conjugate Heat Transfer`.

### Controls

- The benchmark uses Realizable k-epsilon, a solid enthalpy tolerance of `1e-08`, two non-orthogonal correctors, temperature limits, a volumetric CPU heat source of `1.25e6 W/m^3`, a baseline run of `800` iterations, and a follow-up radiation run to about `2000` iterations.
- FlowStudio should expose these as guided reference values in the workflow cockpit and workflow guide.

### Post-processing

- The benchmark compares baseline and radiation-enabled temperature fields and then visualizes `qr(partial)`.
- FlowStudio should describe those result checks explicitly in the final guided step.

## Implementation Strategy

### Phase 1. Guided workflow recipe

- add a study-recipe layer on top of the existing domain workflow profiles
- select the recipe automatically for `CFD + Conjugate Heat Transfer`
- override the generic CFD step names, descriptions, and hints with electronics-cooling-specific guidance

### Phase 2. Cockpit and guide integration

- show the study recipe in the Project Cockpit
- show milestones and reference values in the workflow guide task panel and console output
- keep the generic CFD workflow unchanged for other analysis types

### Phase 2B. One-click study scaffold

- add a dedicated `New Electronics Cooling Study` command in the FlowStudio analysis surfaces
- create a `CFD` analysis with `AnalysisType = Conjugate Heat Transfer`
- add benchmark-oriented child objects for fluid material, solid material, initial conditions, solver, mesh, post pipeline, fan, heat source, and placeholder BC objects
- apply safe defaults that do not require geometry references yet

### Phase 3. Validation coverage

- add pure-Python tests that verify the recipe exists
- verify the workflow context applies the recipe only for the matching analysis type
- verify generic CFD flows stay generic

## Pilot Outcome

The electronics-cooling plan succeeded as a pilot in three ways:

1. it proved that benchmark guidance belongs in a recipe layer on top of domain workflow profiles rather than in one-off task panels
2. it established the pattern of using a stable `StudyRecipeKey` on analyses so scaffold commands can select specific workflow overlays deterministically
3. it showed that benchmark defaults, cockpit guidance, and starter result objects should be centralized and testable rather than duplicated in command code

## Initial Implementation Scope

This implementation pass focuses on guided workflow replication, not full automatic case authoring.

Implemented behavior should include:

- study recipe selection for the benchmark analysis type
- recipe-aware step names and hints
- recipe summary, milestones, and key reference values in the cockpit and workflow guide
- tests covering recipe selection and workflow override behavior
- one-click study scaffold command with CHT benchmark defaults and placeholder setup objects

Deferred items:

- automatic generation of the benchmark geometry primitives
- automatic creation of region interfaces and extracted patches
- automatic application of all solver property values to analysis objects
- one-click benchmark case creation from downloaded STL assets

## Remaining Electronics-Cooling Work

The pilot scaffold is complete, but the benchmark still has meaningful follow-on work before it reaches full workflow parity with the external tutorial.

### Phase 4. Benchmark authoring helpers

- create helper geometry commands or guided primitives for the fan box and outlet extraction box
- add benchmark-aware named-patch extraction helpers for `fan_inlet`, `outlet`, and the CHT interface surfaces
- guide the user through the solid-first, fluid-second region decomposition workflow with more than descriptive text alone

### Phase 5. Benchmark comparison workflow

- add explicit run-to-run support for baseline vs radiation-enabled comparison
- surface recommended monitors and report views for board, CPU, fan, inlet, and outlet temperatures
- expose `qr(partial)` and related radiative output checks in a more direct post-processing template

### Phase 6. Benchmark execution validation

- add runtime smoke coverage that executes the study scaffold in a fresh document
- verify the expected object graph, study recipe key, and starter post objects
- eventually add a reproducible benchmark harness once geometry assets and solver-side parity are stable

## Next Natural Extension

The next electronics-cooling-specific extension is no longer the basic scaffold command, because that already exists.

The next concrete benchmark step should be:

1. helper geometry authoring for the fan and outlet tools
2. region / interface creation helpers for the CHT workflow
3. baseline-vs-radiation comparison templates in post-processing