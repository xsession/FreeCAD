# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Study-specific workflow recipes layered on top of domain workflow profiles."""

from dataclasses import dataclass


_FLOWSTUDIO_EXAMPLES_REFERENCE = "https://github.com/xsession/FreeCAD/tree/main/src/Mod/FlowStudio/docs"


def apply_pipe_flow_defaults(
    analysis,
    *,
    physics_model=None,
    fluid_material=None,
    solver=None,
    initial_conditions=None,
    mesh=None,
    post_pipeline=None,
):
    """Apply a generic internal pipe-flow baseline setup."""
    if analysis is not None:
        if hasattr(analysis, "PhysicsDomain"):
            analysis.PhysicsDomain = "CFD"
        if hasattr(analysis, "AnalysisType"):
            analysis.AnalysisType = "Internal Flow"
        if hasattr(analysis, "StudyRecipeKey"):
            analysis.StudyRecipeKey = "cfd-pipe-flow"
        if hasattr(analysis, "Label"):
            analysis.Label = "Pipe Flow Study"

    if physics_model is not None:
        if hasattr(physics_model, "FlowRegime"):
            physics_model.FlowRegime = "Turbulent"
        if hasattr(physics_model, "TurbulenceModel"):
            physics_model.TurbulenceModel = "kOmegaSST"
        if hasattr(physics_model, "HeatTransfer"):
            physics_model.HeatTransfer = False
        if hasattr(physics_model, "Compressibility"):
            physics_model.Compressibility = "Incompressible"
        if hasattr(physics_model, "TimeModel"):
            physics_model.TimeModel = "Steady"
        if hasattr(physics_model, "PassiveScalar"):
            physics_model.PassiveScalar = False

    if fluid_material is not None:
        if hasattr(fluid_material, "Preset"):
            fluid_material.Preset = "Water (20°C)"
        if hasattr(fluid_material, "MaterialName"):
            fluid_material.MaterialName = "Water"
        if hasattr(fluid_material, "ReferenceTemperature"):
            fluid_material.ReferenceTemperature = 293.15

    if solver is not None:
        if hasattr(solver, "SolverBackend"):
            solver.SolverBackend = "OpenFOAM"
        if hasattr(solver, "OpenFOAMSolver"):
            solver.OpenFOAMSolver = "simpleFoam"
        if hasattr(solver, "MaxIterations"):
            solver.MaxIterations = 500
        if hasattr(solver, "ConvergenceTolerance"):
            solver.ConvergenceTolerance = 1e-6
        if hasattr(solver, "ConvectionScheme"):
            solver.ConvectionScheme = "linearUpwind"

    if initial_conditions is not None:
        if hasattr(initial_conditions, "Ux"):
            initial_conditions.Ux = 1.0
        if hasattr(initial_conditions, "Uy"):
            initial_conditions.Uy = 0.0
        if hasattr(initial_conditions, "Uz"):
            initial_conditions.Uz = 0.0
        if hasattr(initial_conditions, "Pressure"):
            initial_conditions.Pressure = 0.0
        if hasattr(initial_conditions, "UsePotentialFlow"):
            initial_conditions.UsePotentialFlow = False

    if mesh is not None:
        if hasattr(mesh, "CharacteristicLength"):
            mesh.CharacteristicLength = 20.0
        if hasattr(mesh, "MinElementSize"):
            mesh.MinElementSize = 1.0
        if hasattr(mesh, "MaxElementSize"):
            mesh.MaxElementSize = 30.0
        if hasattr(mesh, "GrowthRate"):
            mesh.GrowthRate = 1.15
        if hasattr(mesh, "MeshFormat"):
            mesh.MeshFormat = "OpenFOAM (polyMesh)"

    if post_pipeline is not None and hasattr(post_pipeline, "Label"):
        post_pipeline.Label = "Pipe Flow Post"


def apply_static_mixer_defaults(
    analysis,
    *,
    physics_model=None,
    fluid_material=None,
    solver=None,
    initial_conditions=None,
    mesh=None,
    post_pipeline=None,
):
    """Apply a passive-scalar static-mixer baseline setup."""
    if analysis is not None:
        if hasattr(analysis, "PhysicsDomain"):
            analysis.PhysicsDomain = "CFD"
        if hasattr(analysis, "AnalysisType"):
            analysis.AnalysisType = "Internal Flow"
        if hasattr(analysis, "StudyRecipeKey"):
            analysis.StudyRecipeKey = "cfd-static-mixer"
        if hasattr(analysis, "Label"):
            analysis.Label = "Static Mixer Study"

    if physics_model is not None:
        if hasattr(physics_model, "FlowRegime"):
            physics_model.FlowRegime = "Turbulent"
        if hasattr(physics_model, "TurbulenceModel"):
            physics_model.TurbulenceModel = "kOmegaSST"
        if hasattr(physics_model, "HeatTransfer"):
            physics_model.HeatTransfer = False
        if hasattr(physics_model, "Compressibility"):
            physics_model.Compressibility = "Incompressible"
        if hasattr(physics_model, "TimeModel"):
            physics_model.TimeModel = "Transient"
        if hasattr(physics_model, "PassiveScalar"):
            physics_model.PassiveScalar = True

    if fluid_material is not None:
        if hasattr(fluid_material, "Preset"):
            fluid_material.Preset = "Water (20°C)"
        if hasattr(fluid_material, "MaterialName"):
            fluid_material.MaterialName = "Water"
        if hasattr(fluid_material, "ReferenceTemperature"):
            fluid_material.ReferenceTemperature = 293.15

    if solver is not None:
        if hasattr(solver, "SolverBackend"):
            solver.SolverBackend = "OpenFOAM"
        if hasattr(solver, "OpenFOAMSolver"):
            solver.OpenFOAMSolver = "pimpleFoam"
        if hasattr(solver, "MaxIterations"):
            solver.MaxIterations = 600
        if hasattr(solver, "ConvergenceTolerance"):
            solver.ConvergenceTolerance = 1e-6
        if hasattr(solver, "ConvectionScheme"):
            solver.ConvectionScheme = "linearUpwind"

    if initial_conditions is not None:
        if hasattr(initial_conditions, "Ux"):
            initial_conditions.Ux = 0.8
        if hasattr(initial_conditions, "Uy"):
            initial_conditions.Uy = 0.0
        if hasattr(initial_conditions, "Uz"):
            initial_conditions.Uz = 0.0
        if hasattr(initial_conditions, "Pressure"):
            initial_conditions.Pressure = 0.0
        if hasattr(initial_conditions, "UsePotentialFlow"):
            initial_conditions.UsePotentialFlow = False

    if mesh is not None:
        if hasattr(mesh, "CharacteristicLength"):
            mesh.CharacteristicLength = 10.0
        if hasattr(mesh, "MinElementSize"):
            mesh.MinElementSize = 0.5
        if hasattr(mesh, "MaxElementSize"):
            mesh.MaxElementSize = 15.0
        if hasattr(mesh, "GrowthRate"):
            mesh.GrowthRate = 1.12
        if hasattr(mesh, "MeshFormat"):
            mesh.MeshFormat = "OpenFOAM (polyMesh)"

    if post_pipeline is not None and hasattr(post_pipeline, "Label"):
        post_pipeline.Label = "Static Mixer Post"


def apply_tesla_valve_defaults(
    analysis,
    *,
    physics_model=None,
    fluid_material=None,
    solver=None,
    initial_conditions=None,
    mesh=None,
    post_pipeline=None,
    result_plot=None,
):
    """Apply a Tesla-valve-focused internal-flow starter setup."""
    apply_pipe_flow_defaults(
        analysis,
        physics_model=physics_model,
        fluid_material=fluid_material,
        solver=solver,
        initial_conditions=initial_conditions,
        mesh=mesh,
        post_pipeline=post_pipeline,
    )

    if analysis is not None:
        if hasattr(analysis, "StudyRecipeKey"):
            analysis.StudyRecipeKey = "cfd-tesla-valve"
        if hasattr(analysis, "Label"):
            analysis.Label = "Tesla Valve Study"

    if physics_model is not None:
        if hasattr(physics_model, "TurbulenceModel"):
            physics_model.TurbulenceModel = "kOmegaSST"

    if solver is not None:
        if hasattr(solver, "MaxIterations"):
            solver.MaxIterations = 700

    if initial_conditions is not None:
        if hasattr(initial_conditions, "Ux"):
            initial_conditions.Ux = 1.5
        if hasattr(initial_conditions, "Pressure"):
            initial_conditions.Pressure = 0.0

    if mesh is not None:
        if hasattr(mesh, "CharacteristicLength"):
            mesh.CharacteristicLength = 4.0
        if hasattr(mesh, "MinElementSize"):
            mesh.MinElementSize = 0.2
        if hasattr(mesh, "MaxElementSize"):
            mesh.MaxElementSize = 8.0
        if hasattr(mesh, "GrowthRate"):
            mesh.GrowthRate = 1.08

    if post_pipeline is not None:
        if hasattr(post_pipeline, "Label"):
            post_pipeline.Label = "Tesla Valve Post"
        if hasattr(post_pipeline, "AvailableFields"):
            post_pipeline.AvailableFields = ["Velocity Magnitude", "Pressure", "Pressure Drop"]
        if hasattr(post_pipeline, "ActiveField"):
            post_pipeline.ActiveField = "Pressure"
        if hasattr(post_pipeline, "VisualizationType"):
            post_pipeline.VisualizationType = "Contour (Slice)"

    if result_plot is not None:
        if hasattr(result_plot, "Label"):
            result_plot.Label = "TeslaValvePressurePlot"
        if hasattr(result_plot, "PlotKind"):
            result_plot.PlotKind = "Cut Plot"
        if hasattr(result_plot, "Field"):
            result_plot.Field = "Pressure"
        if hasattr(result_plot, "CutPlane"):
            result_plot.CutPlane = "XY Plane"
        if hasattr(result_plot, "Contours"):
            result_plot.Contours = True


def apply_von_karman_defaults(
    analysis,
    *,
    physics_model=None,
    fluid_material=None,
    solver=None,
    initial_conditions=None,
    mesh=None,
    post_pipeline=None,
    result_plot=None,
):
    """Apply a Von-Karman-focused transient validation starter setup."""
    apply_external_aero_defaults(
        analysis,
        physics_model=physics_model,
        fluid_material=fluid_material,
        solver=solver,
        initial_conditions=initial_conditions,
        mesh=mesh,
        post_pipeline=post_pipeline,
    )

    if analysis is not None:
        if hasattr(analysis, "StudyRecipeKey"):
            analysis.StudyRecipeKey = "cfd-von-karman-vortex-street"
        if hasattr(analysis, "Label"):
            analysis.Label = "Von Karman Vortex Study"

    if physics_model is not None:
        if hasattr(physics_model, "TimeModel"):
            physics_model.TimeModel = "Transient"
        if hasattr(physics_model, "TurbulenceModel"):
            physics_model.TurbulenceModel = "kOmegaSST"

    if solver is not None:
        if hasattr(solver, "OpenFOAMSolver"):
            solver.OpenFOAMSolver = "pimpleFoam"
        if hasattr(solver, "MaxIterations"):
            solver.MaxIterations = 1200

    if initial_conditions is not None:
        if hasattr(initial_conditions, "UsePotentialFlow"):
            initial_conditions.UsePotentialFlow = False
        if hasattr(initial_conditions, "Ux"):
            initial_conditions.Ux = 2.0

    if mesh is not None:
        if hasattr(mesh, "CharacteristicLength"):
            mesh.CharacteristicLength = 8.0
        if hasattr(mesh, "MinElementSize"):
            mesh.MinElementSize = 0.15
        if hasattr(mesh, "MaxElementSize"):
            mesh.MaxElementSize = 16.0
        if hasattr(mesh, "GrowthRate"):
            mesh.GrowthRate = 1.08

    if post_pipeline is not None:
        if hasattr(post_pipeline, "Label"):
            post_pipeline.Label = "Von Karman Post"
        if hasattr(post_pipeline, "AvailableFields"):
            post_pipeline.AvailableFields = ["Velocity Magnitude", "Vorticity", "Pressure"]
        if hasattr(post_pipeline, "ActiveField"):
            post_pipeline.ActiveField = "Vorticity"
        if hasattr(post_pipeline, "VisualizationType"):
            post_pipeline.VisualizationType = "Contour (Slice)"

    if result_plot is not None:
        if hasattr(result_plot, "Label"):
            result_plot.Label = "VonKarmanVorticityPlot"
        if hasattr(result_plot, "PlotKind"):
            result_plot.PlotKind = "Cut Plot"
        if hasattr(result_plot, "Field"):
            result_plot.Field = "Vorticity"
        if hasattr(result_plot, "CutPlane"):
            result_plot.CutPlane = "YZ Plane"
        if hasattr(result_plot, "Contours"):
            result_plot.Contours = True


def apply_external_aero_defaults(
    analysis,
    *,
    physics_model=None,
    fluid_material=None,
    solver=None,
    initial_conditions=None,
    mesh=None,
    post_pipeline=None,
):
    """Apply a generic external-aerodynamics baseline setup."""
    if analysis is not None:
        if hasattr(analysis, "PhysicsDomain"):
            analysis.PhysicsDomain = "CFD"
        if hasattr(analysis, "AnalysisType"):
            analysis.AnalysisType = "External Flow"
        if hasattr(analysis, "StudyRecipeKey"):
            analysis.StudyRecipeKey = "cfd-external-aero"
        if hasattr(analysis, "Label"):
            analysis.Label = "External Aerodynamics Study"

    if physics_model is not None:
        if hasattr(physics_model, "FlowRegime"):
            physics_model.FlowRegime = "Turbulent"
        if hasattr(physics_model, "TurbulenceModel"):
            physics_model.TurbulenceModel = "kOmegaSST"
        if hasattr(physics_model, "HeatTransfer"):
            physics_model.HeatTransfer = False
        if hasattr(physics_model, "Compressibility"):
            physics_model.Compressibility = "Incompressible"
        if hasattr(physics_model, "TimeModel"):
            physics_model.TimeModel = "Steady"

    if fluid_material is not None:
        if hasattr(fluid_material, "Preset"):
            fluid_material.Preset = "Air (20°C, 1atm)"
        if hasattr(fluid_material, "MaterialName"):
            fluid_material.MaterialName = "Air"
        if hasattr(fluid_material, "ReferenceTemperature"):
            fluid_material.ReferenceTemperature = 293.15

    if solver is not None:
        if hasattr(solver, "SolverBackend"):
            solver.SolverBackend = "OpenFOAM"
        if hasattr(solver, "OpenFOAMSolver"):
            solver.OpenFOAMSolver = "simpleFoam"
        if hasattr(solver, "MaxIterations"):
            solver.MaxIterations = 300
        if hasattr(solver, "ConvergenceTolerance"):
            solver.ConvergenceTolerance = 1e-6
        if hasattr(solver, "ConvectionScheme"):
            solver.ConvectionScheme = "linearUpwind"

    if initial_conditions is not None:
        if hasattr(initial_conditions, "UsePotentialFlow"):
            initial_conditions.UsePotentialFlow = True
        if hasattr(initial_conditions, "Ux"):
            initial_conditions.Ux = 20.0
        if hasattr(initial_conditions, "Uy"):
            initial_conditions.Uy = 0.0
        if hasattr(initial_conditions, "Uz"):
            initial_conditions.Uz = 0.0

    if mesh is not None:
        if hasattr(mesh, "CharacteristicLength"):
            mesh.CharacteristicLength = 100.0
        if hasattr(mesh, "MinElementSize"):
            mesh.MinElementSize = 5.0
        if hasattr(mesh, "MaxElementSize"):
            mesh.MaxElementSize = 200.0
        if hasattr(mesh, "GrowthRate"):
            mesh.GrowthRate = 1.15
        if hasattr(mesh, "MeshFormat"):
            mesh.MeshFormat = "OpenFOAM (polyMesh)"

    if post_pipeline is not None and hasattr(post_pipeline, "Label"):
        post_pipeline.Label = "External Aero Post"


def apply_buildings_defaults(
    analysis,
    *,
    physics_model=None,
    fluid_material=None,
    solver=None,
    initial_conditions=None,
    mesh=None,
    post_pipeline=None,
    result_plot=None,
):
    """Apply a buildings-focused atmospheric external-flow starter setup."""
    apply_external_aero_defaults(
        analysis,
        physics_model=physics_model,
        fluid_material=fluid_material,
        solver=solver,
        initial_conditions=initial_conditions,
        mesh=mesh,
        post_pipeline=post_pipeline,
    )

    if analysis is not None:
        if hasattr(analysis, "StudyRecipeKey"):
            analysis.StudyRecipeKey = "cfd-buildings"
        if hasattr(analysis, "Label"):
            analysis.Label = "Wind Around Buildings Study"

    if physics_model is not None:
        if hasattr(physics_model, "TurbulenceModel"):
            physics_model.TurbulenceModel = "kEpsilon"

    if solver is not None:
        if hasattr(solver, "MaxIterations"):
            solver.MaxIterations = 400

    if initial_conditions is not None:
        if hasattr(initial_conditions, "Ux"):
            initial_conditions.Ux = 8.0
        if hasattr(initial_conditions, "Uy"):
            initial_conditions.Uy = 0.0
        if hasattr(initial_conditions, "Uz"):
            initial_conditions.Uz = 0.0

    if mesh is not None:
        if hasattr(mesh, "CharacteristicLength"):
            mesh.CharacteristicLength = 150.0
        if hasattr(mesh, "MinElementSize"):
            mesh.MinElementSize = 10.0
        if hasattr(mesh, "MaxElementSize"):
            mesh.MaxElementSize = 250.0

    if post_pipeline is not None:
        if hasattr(post_pipeline, "Label"):
            post_pipeline.Label = "Buildings Wind Post"
        if hasattr(post_pipeline, "AvailableFields"):
            post_pipeline.AvailableFields = ["Velocity Magnitude", "Pressure", "Turbulent Kinetic Energy"]
        if hasattr(post_pipeline, "ActiveField"):
            post_pipeline.ActiveField = "Velocity Magnitude"
        if hasattr(post_pipeline, "VisualizationType"):
            post_pipeline.VisualizationType = "Contour (Slice)"

    if result_plot is not None:
        if hasattr(result_plot, "Label"):
            result_plot.Label = "WindSpeedClipPlot"
        if hasattr(result_plot, "PlotKind"):
            result_plot.PlotKind = "Cut Plot"
        if hasattr(result_plot, "Field"):
            result_plot.Field = "Velocity Magnitude"
        if hasattr(result_plot, "CutPlane"):
            result_plot.CutPlane = "YZ Plane"
        if hasattr(result_plot, "Contours"):
            result_plot.Contours = True


def apply_airfoil_defaults(
    analysis,
    *,
    physics_model=None,
    fluid_material=None,
    solver=None,
    initial_conditions=None,
    mesh=None,
    post_pipeline=None,
    result_plot=None,
):
    """Apply an airfoil-focused external-flow starter setup."""
    apply_external_aero_defaults(
        analysis,
        physics_model=physics_model,
        fluid_material=fluid_material,
        solver=solver,
        initial_conditions=initial_conditions,
        mesh=mesh,
        post_pipeline=post_pipeline,
    )

    if analysis is not None:
        if hasattr(analysis, "StudyRecipeKey"):
            analysis.StudyRecipeKey = "cfd-airfoil-naca-0012"
        if hasattr(analysis, "Label"):
            analysis.Label = "NACA 0012 Airfoil Study"

    if physics_model is not None:
        if hasattr(physics_model, "TurbulenceModel"):
            physics_model.TurbulenceModel = "kOmegaSST"

    if solver is not None:
        if hasattr(solver, "MaxIterations"):
            solver.MaxIterations = 500

    if initial_conditions is not None:
        if hasattr(initial_conditions, "Ux"):
            initial_conditions.Ux = 30.0
        if hasattr(initial_conditions, "Uy"):
            initial_conditions.Uy = 0.0
        if hasattr(initial_conditions, "Uz"):
            initial_conditions.Uz = 0.0

    if mesh is not None:
        if hasattr(mesh, "CharacteristicLength"):
            mesh.CharacteristicLength = 40.0
        if hasattr(mesh, "MinElementSize"):
            mesh.MinElementSize = 0.5
        if hasattr(mesh, "MaxElementSize"):
            mesh.MaxElementSize = 80.0
        if hasattr(mesh, "GrowthRate"):
            mesh.GrowthRate = 1.1

    if post_pipeline is not None:
        if hasattr(post_pipeline, "Label"):
            post_pipeline.Label = "Airfoil Pressure Post"
        if hasattr(post_pipeline, "AvailableFields"):
            post_pipeline.AvailableFields = ["Pressure Coefficient", "Velocity Magnitude", "Wall Shear Stress"]
        if hasattr(post_pipeline, "ActiveField"):
            post_pipeline.ActiveField = "Pressure Coefficient"
        if hasattr(post_pipeline, "VisualizationType"):
            post_pipeline.VisualizationType = "Contour (Surface)"

    if result_plot is not None:
        if hasattr(result_plot, "Label"):
            result_plot.Label = "AirfoilCpPlot"
        if hasattr(result_plot, "PlotKind"):
            result_plot.PlotKind = "Surface Plot"
        if hasattr(result_plot, "Field"):
            result_plot.Field = "Pressure Coefficient"
        if hasattr(result_plot, "Contours"):
            result_plot.Contours = True


def apply_electronics_cooling_defaults(
    analysis,
    *,
    physics_model=None,
    fluid_material=None,
    solid_material=None,
    solver=None,
    initial_conditions=None,
    fan=None,
    volume_source=None,
    mesh=None,
    post_pipeline=None,
):
    """Apply benchmark defaults for the electronics-cooling CHT study."""
    if analysis is not None:
        if hasattr(analysis, "PhysicsDomain"):
            analysis.PhysicsDomain = "CFD"
        if hasattr(analysis, "AnalysisType"):
            analysis.AnalysisType = "Conjugate Heat Transfer"
        if hasattr(analysis, "StudyRecipeKey"):
            analysis.StudyRecipeKey = "cfd-electronics-cooling"
        if hasattr(analysis, "Label"):
            analysis.Label = "Electronics Cooling Study"

    if physics_model is not None:
        if hasattr(physics_model, "FlowRegime"):
            physics_model.FlowRegime = "Turbulent"
        if hasattr(physics_model, "TurbulenceModel"):
            physics_model.TurbulenceModel = "kEpsilon"
        if hasattr(physics_model, "HeatTransfer"):
            physics_model.HeatTransfer = True
        if hasattr(physics_model, "Compressibility"):
            physics_model.Compressibility = "Incompressible"
        if hasattr(physics_model, "TimeModel"):
            physics_model.TimeModel = "Steady"

    if fluid_material is not None:
        if hasattr(fluid_material, "Preset"):
            fluid_material.Preset = "Air (20°C, 1atm)"
        if hasattr(fluid_material, "MaterialName"):
            fluid_material.MaterialName = "Air"
        if hasattr(fluid_material, "ReferenceTemperature"):
            fluid_material.ReferenceTemperature = 293.15

    if solid_material is not None:
        if hasattr(solid_material, "MaterialPreset"):
            solid_material.MaterialPreset = "Aluminum 6061-T6"
        if hasattr(solid_material, "MaterialName"):
            solid_material.MaterialName = "Aluminum 6061-T6"

    if solver is not None:
        if hasattr(solver, "SolverBackend"):
            solver.SolverBackend = "OpenFOAM"
        if hasattr(solver, "OpenFOAMSolver"):
            solver.OpenFOAMSolver = "simpleFoam"
        if hasattr(solver, "MaxIterations"):
            solver.MaxIterations = 800
        if hasattr(solver, "ConvergenceTolerance"):
            solver.ConvergenceTolerance = 1e-8
        if hasattr(solver, "RelaxationFactorP"):
            solver.RelaxationFactorP = 0.3
        if hasattr(solver, "RelaxationFactorU"):
            solver.RelaxationFactorU = 0.4
        if hasattr(solver, "ConvectionScheme"):
            solver.ConvectionScheme = "linearUpwind"

    if initial_conditions is not None:
        if hasattr(initial_conditions, "Temperature"):
            initial_conditions.Temperature = 293.15
        if hasattr(initial_conditions, "UsePotentialFlow"):
            initial_conditions.UsePotentialFlow = False

    if fan is not None:
        if hasattr(fan, "Label"):
            fan.Label = "Benchmark Fan"
        if hasattr(fan, "FanType"):
            fan.FanType = "External Inlet Fan"
        if hasattr(fan, "ReferencePressure"):
            fan.ReferencePressure = 101325.0

    if volume_source is not None:
        if hasattr(volume_source, "Label"):
            volume_source.Label = "CPU Heat Source"
        if hasattr(volume_source, "SourceType"):
            volume_source.SourceType = "Heat Generation"
        if hasattr(volume_source, "HeatPowerDensity"):
            volume_source.HeatPowerDensity = 1250000.0

    if mesh is not None:
        if hasattr(mesh, "CharacteristicLength"):
            mesh.CharacteristicLength = 5.0
        if hasattr(mesh, "MinElementSize"):
            mesh.MinElementSize = 0.5
        if hasattr(mesh, "MaxElementSize"):
            mesh.MaxElementSize = 8.0
        if hasattr(mesh, "GrowthRate"):
            mesh.GrowthRate = 1.2
        if hasattr(mesh, "MeshFormat"):
            mesh.MeshFormat = "OpenFOAM (polyMesh)"

    if post_pipeline is not None and hasattr(post_pipeline, "Label"):
        post_pipeline.Label = "Electronics Cooling Post"


def apply_cooling_channel_defaults(
    analysis,
    *,
    physics_model=None,
    fluid_material=None,
    solid_material=None,
    solver=None,
    initial_conditions=None,
    mesh=None,
    inlet_bc=None,
    outlet_bc=None,
    wall_bc=None,
    post_pipeline=None,
    result_plot=None,
):
    """Apply a cooling-channel-focused steady CHT starter setup."""
    apply_electronics_cooling_defaults(
        analysis,
        physics_model=physics_model,
        fluid_material=fluid_material,
        solid_material=solid_material,
        solver=solver,
        initial_conditions=initial_conditions,
        mesh=mesh,
        post_pipeline=post_pipeline,
    )

    if analysis is not None:
        if hasattr(analysis, "StudyRecipeKey"):
            analysis.StudyRecipeKey = "cfd-cooling-channel"
        if hasattr(analysis, "Label"):
            analysis.Label = "Cooling Channel Study"

    if physics_model is not None:
        if hasattr(physics_model, "TurbulenceModel"):
            physics_model.TurbulenceModel = "kOmegaSST"

    if solid_material is not None:
        if hasattr(solid_material, "MaterialPreset"):
            solid_material.MaterialPreset = "Aluminum 6061-T6"

    if solver is not None:
        if hasattr(solver, "OpenFOAMSolver"):
            solver.OpenFOAMSolver = "chtMultiRegionSimpleFoam"
        if hasattr(solver, "MaxIterations"):
            solver.MaxIterations = 900

    if initial_conditions is not None:
        if hasattr(initial_conditions, "Temperature"):
            initial_conditions.Temperature = 300.15
        if hasattr(initial_conditions, "UsePotentialFlow"):
            initial_conditions.UsePotentialFlow = False

    if mesh is not None:
        if hasattr(mesh, "CharacteristicLength"):
            mesh.CharacteristicLength = 4.0
        if hasattr(mesh, "MinElementSize"):
            mesh.MinElementSize = 0.25
        if hasattr(mesh, "MaxElementSize"):
            mesh.MaxElementSize = 6.0
        if hasattr(mesh, "GrowthRate"):
            mesh.GrowthRate = 1.12

    if inlet_bc is not None:
        if hasattr(inlet_bc, "BCLabel"):
            inlet_bc.BCLabel = "channel_inlet"
        if hasattr(inlet_bc, "VelocityMagnitude"):
            inlet_bc.VelocityMagnitude = 1.2
        if hasattr(inlet_bc, "InletTemperature"):
            inlet_bc.InletTemperature = 300.15

    if outlet_bc is not None:
        if hasattr(outlet_bc, "BCLabel"):
            outlet_bc.BCLabel = "channel_outlet"
        if hasattr(outlet_bc, "StaticPressure"):
            outlet_bc.StaticPressure = 0.0

    if wall_bc is not None:
        if hasattr(wall_bc, "BCLabel"):
            wall_bc.BCLabel = "channel_walls"
        if hasattr(wall_bc, "ThermalType"):
            wall_bc.ThermalType = "Convection"

    if post_pipeline is not None:
        if hasattr(post_pipeline, "Label"):
            post_pipeline.Label = "Cooling Channel Post"
        if hasattr(post_pipeline, "AvailableFields"):
            post_pipeline.AvailableFields = ["Temperature", "Velocity Magnitude", "Heat Flux"]
        if hasattr(post_pipeline, "ActiveField"):
            post_pipeline.ActiveField = "Temperature"
        if hasattr(post_pipeline, "VisualizationType"):
            post_pipeline.VisualizationType = "Contour (Slice)"

    if result_plot is not None:
        if hasattr(result_plot, "Label"):
            result_plot.Label = "CoolingChannelTemperaturePlot"
        if hasattr(result_plot, "PlotKind"):
            result_plot.PlotKind = "Cut Plot"
        if hasattr(result_plot, "Field"):
            result_plot.Field = "Temperature"
        if hasattr(result_plot, "CutPlane"):
            result_plot.CutPlane = "YZ Plane"
        if hasattr(result_plot, "Contours"):
            result_plot.Contours = True


def apply_structural_bracket_defaults(
    analysis,
    *,
    physics_model=None,
    solid_material=None,
    solver=None,
    fixed_constraint=None,
    force_constraint=None,
    post_pipeline=None,
    result_plot=None,
):
    """Apply a structural bracket starter setup with result defaults."""
    if analysis is not None:
        if hasattr(analysis, "PhysicsDomain"):
            analysis.PhysicsDomain = "Structural"
        if hasattr(analysis, "AnalysisType"):
            analysis.AnalysisType = "Static Linear Elastic"
        if hasattr(analysis, "StudyRecipeKey"):
            analysis.StudyRecipeKey = "structural-bracket-example"
        if hasattr(analysis, "Label"):
            analysis.Label = "Structural Bracket Example"

    if physics_model is not None:
        if hasattr(physics_model, "AnalysisModel"):
            physics_model.AnalysisModel = "Linear Elastic"
        if hasattr(physics_model, "TimeModel"):
            physics_model.TimeModel = "Steady"
        if hasattr(physics_model, "Gravity"):
            physics_model.Gravity = False

    if solid_material is not None:
        if hasattr(solid_material, "MaterialPreset"):
            solid_material.MaterialPreset = "Aluminum 6061-T6"
        if hasattr(solid_material, "MaterialName"):
            solid_material.MaterialName = "Aluminum 6061-T6"

    if solver is not None:
        if hasattr(solver, "SolverBackend"):
            solver.SolverBackend = "Elmer"

    if fixed_constraint is not None and hasattr(fixed_constraint, "BCLabel"):
        fixed_constraint.BCLabel = "support_face"

    if force_constraint is not None:
        if hasattr(force_constraint, "BCLabel"):
            force_constraint.BCLabel = "tip_load"
        if hasattr(force_constraint, "ForceZ"):
            force_constraint.ForceZ = -1500.0

    if post_pipeline is not None:
        if hasattr(post_pipeline, "Label"):
            post_pipeline.Label = "Structural Bracket Results"
        if hasattr(post_pipeline, "AvailableFields"):
            post_pipeline.AvailableFields = ["Von Mises Stress", "Displacement", "Safety Factor"]
        if hasattr(post_pipeline, "ActiveField"):
            post_pipeline.ActiveField = "Von Mises Stress"
        if hasattr(post_pipeline, "VisualizationType"):
            post_pipeline.VisualizationType = "Contour (Surface)"

    if result_plot is not None:
        if hasattr(result_plot, "Label"):
            result_plot.Label = "Bracket Stress Plot"
        if hasattr(result_plot, "PlotKind"):
            result_plot.PlotKind = "Surface Plot"
        if hasattr(result_plot, "Field"):
            result_plot.Field = "Von Mises Stress"
        if hasattr(result_plot, "Contours"):
            result_plot.Contours = True
        if hasattr(result_plot, "Vectors"):
            result_plot.Vectors = False


def apply_electrostatic_capacitor_defaults(
    analysis,
    *,
    physics_model=None,
    material=None,
    solver=None,
    positive_bc=None,
    ground_bc=None,
    post_pipeline=None,
    result_plot=None,
):
    """Apply an electrostatic capacitor starter setup with result defaults."""
    if analysis is not None:
        if hasattr(analysis, "PhysicsDomain"):
            analysis.PhysicsDomain = "Electrostatic"
        if hasattr(analysis, "AnalysisType"):
            analysis.AnalysisType = "Capacitance Matrix"
        if hasattr(analysis, "StudyRecipeKey"):
            analysis.StudyRecipeKey = "electrostatic-capacitor-example"
        if hasattr(analysis, "Label"):
            analysis.Label = "Electrostatic Capacitor Example"

    if physics_model is not None and hasattr(physics_model, "CalculateCapacitanceMatrix"):
        physics_model.CalculateCapacitanceMatrix = True

    if material is not None:
        if hasattr(material, "MaterialPreset"):
            material.MaterialPreset = "PTFE (Teflon)"
        if hasattr(material, "MaterialName"):
            material.MaterialName = "PTFE"

    if solver is not None and hasattr(solver, "SolverBackend"):
        solver.SolverBackend = "Elmer"

    if positive_bc is not None:
        if hasattr(positive_bc, "BCLabel"):
            positive_bc.BCLabel = "anode"
        if hasattr(positive_bc, "Potential"):
            positive_bc.Potential = 5.0

    if ground_bc is not None:
        if hasattr(ground_bc, "BCLabel"):
            ground_bc.BCLabel = "cathode"
        if hasattr(ground_bc, "Potential"):
            ground_bc.Potential = 0.0

    if post_pipeline is not None:
        if hasattr(post_pipeline, "Label"):
            post_pipeline.Label = "Electrostatic Capacitor Results"
        if hasattr(post_pipeline, "AvailableFields"):
            post_pipeline.AvailableFields = ["Electric Potential", "Electric Field Magnitude", "Charge Density"]
        if hasattr(post_pipeline, "ActiveField"):
            post_pipeline.ActiveField = "Electric Potential"
        if hasattr(post_pipeline, "VisualizationType"):
            post_pipeline.VisualizationType = "Contour (Slice)"

    if result_plot is not None:
        if hasattr(result_plot, "Label"):
            result_plot.Label = "Potential Cut Plot"
        if hasattr(result_plot, "PlotKind"):
            result_plot.PlotKind = "Cut Plot"
        if hasattr(result_plot, "Field"):
            result_plot.Field = "Electric Potential"
        if hasattr(result_plot, "CutPlane"):
            result_plot.CutPlane = "YZ Plane"
        if hasattr(result_plot, "Contours"):
            result_plot.Contours = True


def apply_electromagnetic_coil_defaults(
    analysis,
    *,
    physics_model=None,
    material=None,
    solver=None,
    current_bc=None,
    boundary_bc=None,
    post_pipeline=None,
    result_plot=None,
):
    """Apply an electromagnetic coil starter setup with result defaults."""
    if analysis is not None:
        if hasattr(analysis, "PhysicsDomain"):
            analysis.PhysicsDomain = "Electromagnetic"
        if hasattr(analysis, "AnalysisType"):
            analysis.AnalysisType = "Magnetostatic"
        if hasattr(analysis, "StudyRecipeKey"):
            analysis.StudyRecipeKey = "electromagnetic-coil-example"
        if hasattr(analysis, "Label"):
            analysis.Label = "Electromagnetic Coil Example"

    if physics_model is not None:
        if hasattr(physics_model, "EMModel"):
            physics_model.EMModel = "Magnetostatic"
        if hasattr(physics_model, "TimeModel"):
            physics_model.TimeModel = "Steady"

    if material is not None:
        if hasattr(material, "MaterialPreset"):
            material.MaterialPreset = "Copper"
        if hasattr(material, "MaterialName"):
            material.MaterialName = "Copper"

    if solver is not None and hasattr(solver, "SolverBackend"):
        solver.SolverBackend = "Elmer"

    if current_bc is not None:
        if hasattr(current_bc, "BCLabel"):
            current_bc.BCLabel = "coil_current"
        if hasattr(current_bc, "CurrentDensityZ"):
            current_bc.CurrentDensityZ = 2000000.0

    if boundary_bc is not None:
        if hasattr(boundary_bc, "BCLabel"):
            boundary_bc.BCLabel = "far_field"
        if hasattr(boundary_bc, "ZeroPotential"):
            boundary_bc.ZeroPotential = True

    if post_pipeline is not None:
        if hasattr(post_pipeline, "Label"):
            post_pipeline.Label = "Electromagnetic Coil Results"
        if hasattr(post_pipeline, "AvailableFields"):
            post_pipeline.AvailableFields = ["Magnetic Flux Density", "Magnetic Vector Potential", "Current Density"]
        if hasattr(post_pipeline, "ActiveField"):
            post_pipeline.ActiveField = "Magnetic Flux Density"
        if hasattr(post_pipeline, "VisualizationType"):
            post_pipeline.VisualizationType = "Contour (Surface)"

    if result_plot is not None:
        if hasattr(result_plot, "Label"):
            result_plot.Label = "Magnetic Flux Plot"
        if hasattr(result_plot, "PlotKind"):
            result_plot.PlotKind = "Surface Plot"
        if hasattr(result_plot, "Field"):
            result_plot.Field = "Magnetic Flux Density"
        if hasattr(result_plot, "Contours"):
            result_plot.Contours = True


def apply_thermal_plate_defaults(
    analysis,
    *,
    physics_model=None,
    material=None,
    solver=None,
    heat_flux_bc=None,
    convection_bc=None,
    post_pipeline=None,
    result_plot=None,
):
    """Apply a thermal plate starter setup with result defaults."""
    if analysis is not None:
        if hasattr(analysis, "PhysicsDomain"):
            analysis.PhysicsDomain = "Thermal"
        if hasattr(analysis, "AnalysisType"):
            analysis.AnalysisType = "Steady-State Heat Transfer"
        if hasattr(analysis, "StudyRecipeKey"):
            analysis.StudyRecipeKey = "thermal-plate-example"
        if hasattr(analysis, "Label"):
            analysis.Label = "Thermal Plate Example"

    if physics_model is not None:
        if hasattr(physics_model, "TimeModel"):
            physics_model.TimeModel = "Steady"
        if hasattr(physics_model, "Convection"):
            physics_model.Convection = True
        if hasattr(physics_model, "InternalHeatGeneration"):
            physics_model.InternalHeatGeneration = False

    if material is not None:
        if hasattr(material, "MaterialPreset"):
            material.MaterialPreset = "Aluminum"
        if hasattr(material, "MaterialName"):
            material.MaterialName = "Aluminum"

    if solver is not None and hasattr(solver, "SolverBackend"):
        solver.SolverBackend = "Elmer"

    if heat_flux_bc is not None:
        if hasattr(heat_flux_bc, "BCLabel"):
            heat_flux_bc.BCLabel = "heater_pad"
        if hasattr(heat_flux_bc, "HeatFlux"):
            heat_flux_bc.HeatFlux = 5000.0

    if convection_bc is not None:
        if hasattr(convection_bc, "BCLabel"):
            convection_bc.BCLabel = "ambient_air"
        if hasattr(convection_bc, "HeatTransferCoefficient"):
            convection_bc.HeatTransferCoefficient = 25.0
        if hasattr(convection_bc, "AmbientTemperature"):
            convection_bc.AmbientTemperature = 293.15

    if post_pipeline is not None:
        if hasattr(post_pipeline, "Label"):
            post_pipeline.Label = "Thermal Plate Results"
        if hasattr(post_pipeline, "AvailableFields"):
            post_pipeline.AvailableFields = ["Temperature", "Heat Flux", "Temperature Gradient"]
        if hasattr(post_pipeline, "ActiveField"):
            post_pipeline.ActiveField = "Temperature"
        if hasattr(post_pipeline, "VisualizationType"):
            post_pipeline.VisualizationType = "Contour (Slice)"

    if result_plot is not None:
        if hasattr(result_plot, "Label"):
            result_plot.Label = "Temperature Cut Plot"
        if hasattr(result_plot, "PlotKind"):
            result_plot.PlotKind = "Cut Plot"
        if hasattr(result_plot, "Field"):
            result_plot.Field = "Temperature"
        if hasattr(result_plot, "CutPlane"):
            result_plot.CutPlane = "XY Plane"
        if hasattr(result_plot, "Contours"):
            result_plot.Contours = True


def apply_optical_lens_defaults(
    analysis,
    *,
    physics_model=None,
    material=None,
    solver=None,
    source_bc=None,
    detector_bc=None,
    boundary_bc=None,
    post_pipeline=None,
    result_plot=None,
):
    """Apply an optical lens starter setup with result defaults."""
    if analysis is not None:
        if hasattr(analysis, "PhysicsDomain"):
            analysis.PhysicsDomain = "Optical"
        if hasattr(analysis, "AnalysisType"):
            analysis.AnalysisType = "Illumination"
        if hasattr(analysis, "StudyRecipeKey"):
            analysis.StudyRecipeKey = "optical-lens-example"
        if hasattr(analysis, "Label"):
            analysis.Label = "Optical Lens Example"

    if physics_model is not None:
        if hasattr(physics_model, "OpticalModel"):
            physics_model.OpticalModel = "Non-Sequential Ray Trace"
        if hasattr(physics_model, "Wavelength"):
            physics_model.Wavelength = 550.0
        if hasattr(physics_model, "RayCount"):
            physics_model.RayCount = 20000

    if material is not None:
        if hasattr(material, "MaterialPreset"):
            material.MaterialPreset = "BK7"
        if hasattr(material, "MaterialName"):
            material.MaterialName = "BK7"
        if hasattr(material, "OpticalRole"):
            material.OpticalRole = "Glass"

    if solver is not None and hasattr(solver, "SolverBackend"):
        solver.SolverBackend = "Raysect"

    if source_bc is not None:
        if hasattr(source_bc, "BCLabel"):
            source_bc.BCLabel = "source"
        if hasattr(source_bc, "SourceType"):
            source_bc.SourceType = "Lambertian LED"
        if hasattr(source_bc, "Power"):
            source_bc.Power = 1.0
        if hasattr(source_bc, "Wavelength"):
            source_bc.Wavelength = 550.0
        if hasattr(source_bc, "RayCount"):
            source_bc.RayCount = 10000

    if detector_bc is not None:
        if hasattr(detector_bc, "BCLabel"):
            detector_bc.BCLabel = "detector"
        if hasattr(detector_bc, "DetectorType"):
            detector_bc.DetectorType = "Irradiance"

    if boundary_bc is not None:
        if hasattr(boundary_bc, "BCLabel"):
            boundary_bc.BCLabel = "housing"
        if hasattr(boundary_bc, "BoundaryType"):
            boundary_bc.BoundaryType = "Reflective"
        if hasattr(boundary_bc, "Reflectivity"):
            boundary_bc.Reflectivity = 0.95

    if post_pipeline is not None:
        if hasattr(post_pipeline, "Label"):
            post_pipeline.Label = "Optical Lens Results"
        if hasattr(post_pipeline, "AvailableFields"):
            post_pipeline.AvailableFields = ["Irradiance", "Illuminance", "Optical Path Length"]
        if hasattr(post_pipeline, "ActiveField"):
            post_pipeline.ActiveField = "Irradiance"
        if hasattr(post_pipeline, "VisualizationType"):
            post_pipeline.VisualizationType = "Contour (Surface)"

    if result_plot is not None:
        if hasattr(result_plot, "Label"):
            result_plot.Label = "Irradiance Surface Plot"
        if hasattr(result_plot, "PlotKind"):
            result_plot.PlotKind = "Surface Plot"
        if hasattr(result_plot, "Field"):
            result_plot.Field = "Irradiance"
        if hasattr(result_plot, "Contours"):
            result_plot.Contours = True


def is_electronics_cooling_analysis(analysis) -> bool:
    """Return True when one analysis is the guided electronics-cooling study."""
    if analysis is None:
        return False
    return (
        getattr(analysis, "PhysicsDomain", "") == "CFD"
        and str(getattr(analysis, "AnalysisType", "")).strip().lower() == "conjugate heat transfer"
    )


@dataclass(frozen=True)
class StudyRecipe:
    key: str
    domain_key: str
    study_keys: tuple[str, ...]
    analysis_types: tuple[str, ...]
    label: str
    summary: str
    focus_workflows: tuple[str, ...]
    milestones: tuple[str, ...]
    key_parameters: tuple[str, ...]
    reference_url: str
    step_overrides: dict[int, dict]
    auto_select: bool = False


_ELECTRONICS_COOLING_RECIPE = StudyRecipe(
    key="cfd-electronics-cooling",
    domain_key="CFD",
    study_keys=("cfd-electronics-cooling",),
    analysis_types=("Conjugate Heat Transfer",),
    label="Electronics Cooling CHT + Radiation",
    summary=(
        "Guided CFD recipe for a board + CPU + fan cooling study with separate solid and fluid "
        "regions, interface coupling, volumetric CPU heating, and a second radiation-enabled solve."
    ),
    focus_workflows=(
        "Electronics cooling",
        "CHT region coupling",
        "Radiation comparison",
    ),
    milestones=(
        "Import board, CPU, and pins geometry; create fan and outlet helper geometry.",
        "Mesh solid first, convert it to a solid sub-region, then mesh the fluid region separately.",
        "Create the CPU solid-fluid interface and keep the fan inlet and extracted outlet as named patches.",
        "Run a baseline steady CHT solution first, then continue with radiation enabled and compare temperatures.",
    ),
    key_parameters=(
        "Fan box origin 0.05, 0.016, 0.0115 m and size 0.016, 0.016, 0.004 m.",
        "Outlet tool origin 0.0845, 0.0415, 0 m and size 0.0065, 0.009, 0.008 m.",
        "Base mesh box min 0,0,0 m max 0.085,0.056,0.0155 m with divisions 15,10,5.",
        "CPU source term h explicit = 1.25e6 W/m^3, inlet velocity = 0.1 m/s.",
        "Radiation model Surface-to-Surface, max rays 3000000, iterations 800 then 2000 with radiation.",
    ),
    reference_url="https://help.sim-flow.com/tutorials/electronics-cooling",
    auto_select=True,
    step_overrides={
        2: {
            "name": "Import Geometry And Cooling Features",
            "description": "Import board, CPU, and pins geometry, then create the fan box, fan inlet face group, and outlet extraction tool.",
            "hint": "Mirror the SimFlow benchmark geometry: board.stl, cpu.stl, pins.stl, plus a fan primitive and outlet_tool box.",
        },
        3: {
            "name": "Configure CHT Physics",
            "description": "Set a steady conjugate heat transfer study with turbulence enabled and prepare radiation settings for a second pass.",
            "hint": "Use CFD with AnalysisType = Conjugate Heat Transfer; baseline run first without radiation, then enable S2S radiation for comparison.",
        },
        4: {
            "name": "Assign Fluid And Solid Materials",
            "description": "Assign air to the fluid region and aluminium-like solid material properties to the board, CPU, and fan solids.",
            "hint": "Use air for fluid and aluminium for the solid benchmark to match the tutorial reference study.",
        },
        5: {
            "name": "Define Patches And Interfaces",
            "description": "Create fan inlet, outlet, wall boundaries, and the CPU solid-fluid interface required for CHT coupling.",
            "hint": "Keep fan_inlet and outlet as named patches and create the region interface between CPU boundaries in fluid and solid regions.",
        },
        6: {
            "name": "Generate Solid And Fluid Mesh Regions",
            "description": "Mesh the solid domain first with a solid material point, convert it to a solid sub-region, then remesh the surrounding fluid domain.",
            "hint": "Use separate material points for solid and fluid, and extract the outlet patch before converting the default fluid region into a sub-region.",
        },
        7: {
            "name": "Tune Solver Controls And Heat Source",
            "description": "Set turbulence, radiation readiness, solid enthalpy tolerance, SIMPLE controls, relaxation, temperature limits, and the CPU volumetric heat source.",
            "hint": "Use Realizable k-epsilon, h(solid) tolerance 1e-08, 2 non-orthogonal correctors, Tmin/Tmax 290/600 K, and CPU source 1.25e6 W/m^3.",
        },
        8: {
            "name": "Run Baseline And Radiation Cases",
            "description": "Run the steady CHT baseline first, then enable radiation and continue the same case for the second comparison solve.",
            "hint": "Start with about 800 iterations, then enable radiation and continue toward about 2000 iterations total.",
        },
        9: {
            "name": "Compare Temperature And Radiative Flux",
            "description": "Review temperature contours for both runs and inspect qr(partial) to understand the radiation contribution.",
            "hint": "Compare the baseline and radiation-enabled temperature fields on board, CPU, fan, inlet, and outlet surfaces.",
        },
    },
)


_COOLING_CHANNEL_RECIPE = StudyRecipe(
    key="cfd-cooling-channel",
    domain_key="CFD",
    study_keys=("cfd-cooling-channel",),
    analysis_types=("Conjugate Heat Transfer",),
    label="Cooling Channel CHT Starter",
    summary=(
        "Guided steady conjugate-heat-transfer starter for a cooling-channel study with channel inlet/outlet setup, solid-wall heat transfer, "
        "and temperature-focused inspection."
    ),
    focus_workflows=("Cooling channel", "Steady CHT", "Temperature inspection"),
    milestones=(
        "Import or model the channel and surrounding solid region and keep inlet, outlet, and heated walls identifiable.",
        "Use steady conjugate heat transfer with fluid and solid materials appropriate for a channel-cooling baseline.",
        "Assign inlet, outlet, and wall thermal boundaries for the baseline cooling pass.",
        "Inspect temperature and heat-flux distributions through the channel and adjacent solid walls.",
    ),
    key_parameters=(
        "Starter inlet velocity baseline 1.2 m/s and inlet temperature 300.15 K.",
        "Use chtMultiRegionSimpleFoam as the starter solver posture for this multi-zone steady CHT workflow.",
        "Primary result surface is a temperature cut plot through the channel cross-section.",
    ),
    reference_url="https://help.sim-flow.com/tutorials/cooling-channel",
    step_overrides={
        2: {
            "name": "Prepare Channel And Solid Region",
            "description": "Import or model the coolant channel and the adjacent solid region that participates in heat transfer.",
            "hint": "Keep channel_inlet, channel_outlet, and heated wall regions easy to identify before assigning BCs.",
        },
        5: {
            "name": "Assign Channel Thermal Boundaries",
            "description": "Configure the coolant inlet/outlet and the wall heat-transfer boundaries for the baseline cooling pass.",
            "hint": "This starter stays in the steady CHT lane and avoids more advanced transient or resistance modeling.",
        },
        9: {
            "name": "Inspect Channel Temperature Field",
            "description": "Review temperature and heat-flux behavior through the cooling channel and nearby solid walls.",
            "hint": "Start with the temperature cut plot before refining wall models or channel geometry.",
        },
    },
)


_PIPE_FLOW_RECIPE = StudyRecipe(
    key="cfd-pipe-flow",
    domain_key="CFD",
    study_keys=("cfd-pipe-flow",),
    analysis_types=("Internal Flow",),
    label="Pipe Flow Internal Benchmark",
    summary=(
        "Guided internal-flow recipe for a simple T-pipe style case with two inlets, one outlet, "
        "basic turbulence, and early-stage slice/streamline validation."
    ),
    focus_workflows=("Internal flow", "Basic CFD", "Boundary-condition setup"),
    milestones=(
        "Create or import the pipe domain and name inlet1, inlet2, and outlet patches clearly.",
        "Set water material, internal-flow physics, and a steady incompressible solver.",
        "Configure one velocity inlet, one pressure-driven inlet, and one outlet for the merge region.",
        "Validate convergence on residuals and inspect a velocity slice and streamline scene.",
    ),
    key_parameters=(
        "Typical baseline: steady incompressible flow with k-omega SST and water material.",
        "Use one velocity inlet and one pressure inlet to test mixed inlet-condition handling.",
        "Target a low-friction startup workflow rather than benchmark-specific geometry automation.",
    ),
    reference_url="https://help.sim-flow.com/tutorials/pipe-flow",
    step_overrides={
        2: {
            "name": "Create Or Import Pipe Geometry",
            "description": "Build a simple T-pipe or import an existing internal-flow manifold and name its inlet and outlet face groups.",
            "hint": "Keep inlet1, inlet2, and outlet readable from the start so BC mapping stays obvious.",
        },
        5: {
            "name": "Assign Internal Flow Boundaries",
            "description": "Set one velocity inlet, one pressure inlet, and an outlet boundary for the merged pipe flow.",
            "hint": "This recipe is meant to exercise basic internal-flow BC patterns rather than advanced solver features.",
        },
        9: {
            "name": "Inspect Velocity Distribution",
            "description": "Use slices and streamlines to confirm the merged flow path and outlet behavior.",
            "hint": "A simple section plane plus stream tracer is enough for this starter benchmark.",
        },
    },
)


_EXTERNAL_AERO_RECIPE = StudyRecipe(
    key="cfd-external-aero",
    domain_key="CFD",
    study_keys=("cfd-external-aero",),
    analysis_types=("External Flow",),
    label="External Aerodynamics Baseline",
    summary=(
        "Guided external-aerodynamics recipe for wing, car, and building-style cases using a reusable far-field, "
        "force-monitor, and wake-inspection workflow."
    ),
    focus_workflows=("External aerodynamics", "Force monitoring", "Far-field setup"),
    milestones=(
        "Create or import the body and establish an external flow domain around it.",
        "Use air material, steady turbulent external-flow physics, and far-field style BC defaults.",
        "Create inlet, outlet, ground or wall, and symmetry placeholders appropriate to the case.",
        "Track forces and inspect wake structures through slices, clips, and streamlines.",
    ),
    key_parameters=(
        "Baseline flow uses air at 20°C and a steady incompressible turbulent solver.",
        "Use k-omega SST as the safe default until a more specific aero recipe overrides it.",
        "Enable potential-flow initialization and linearUpwind convection as the generic starter posture.",
    ),
    reference_url="https://help.sim-flow.com/tutorials/wing",
    step_overrides={
        2: {
            "name": "Prepare External Domain",
            "description": "Import the body or profile and create a wind-tunnel or far-field domain sized for wake development.",
            "hint": "This single recipe should cover wing, car, and buildings by changing geometry and BC detail, not the workflow skeleton.",
        },
        5: {
            "name": "Assign Far-Field Boundaries",
            "description": "Configure inlet, outlet, ground or wall, and symmetry-style patches for the external-flow case.",
            "hint": "Use slip or symmetry on non-critical far-field boundaries and preserve a clear monitored body boundary.",
        },
        7: {
            "name": "Tune Force And Wake Controls",
            "description": "Set turbulence, force monitors, and starter solver controls for a stable external-aero baseline.",
            "hint": "This is the right family for drag/lift monitoring, wake clips, and streamline-based validation.",
        },
        9: {
            "name": "Inspect Wake And Surface Loads",
            "description": "Review force stabilization, wake patterns, and body-surface result scenes.",
            "hint": "Use force reports plus one wake slice or clip before moving into higher-order refinement work.",
        },
    },
)


_BUILDINGS_RECIPE = StudyRecipe(
    key="cfd-buildings",
    domain_key="CFD",
    study_keys=("cfd-buildings",),
    analysis_types=("External Flow",),
    label="Buildings Atmospheric Wind Starter",
    summary=(
        "Guided external-flow starter for urban wind studies with atmospheric-style inlet defaults, ground/wall handling, "
        "and velocity-focused wake inspection around building clusters."
    ),
    focus_workflows=("Atmospheric flow", "Buildings wind", "Wake inspection"),
    milestones=(
        "Import the building massing and create a roomy external domain sized for the downstream wake.",
        "Use air material, steady external-flow physics, and a starter atmospheric inlet velocity baseline.",
        "Create inlet, outlet, ground, and far-field symmetry placeholders around the urban geometry.",
        "Inspect velocity acceleration, recirculation zones, and pressure loading around the building faces.",
    ),
    key_parameters=(
        "Starter inlet velocity baseline Ux = 8 m/s with a steady incompressible turbulent flow model.",
        "Use k-epsilon as the safer urban-flow default before more specific atmospheric profiles are added.",
        "Primary result surface is a velocity cut plot for wake and street-canyon inspection.",
    ),
    reference_url="https://help.sim-flow.com/tutorials/buildings",
    step_overrides={
        2: {
            "name": "Prepare Buildings And Wind Domain",
            "description": "Import the building blockout and create a surrounding external-flow domain with clear inlet, outlet, and side boundaries.",
            "hint": "Leave enough downstream length to inspect the wake behind the buildings before refining the atmospheric profile model.",
        },
        5: {
            "name": "Assign Atmospheric-Style Boundaries",
            "description": "Set the inlet, outlet, ground wall, and far-field symmetry boundaries needed for the urban wind baseline.",
            "hint": "This starter is deliberately simple: uniform inlet now, richer atmospheric profile support later.",
        },
        9: {
            "name": "Inspect Urban Wake And Surface Loading",
            "description": "Review wind-speed acceleration, recirculation, and face pressures around the building cluster.",
            "hint": "Use the primary velocity cut plot first, then inspect surface pressure on the windward faces.",
        },
    },
)


_AIRFOIL_RECIPE = StudyRecipe(
    key="cfd-airfoil-naca-0012",
    domain_key="CFD",
    study_keys=("cfd-airfoil-naca-0012",),
    analysis_types=("External Flow",),
    label="NACA 0012 Airfoil Starter",
    summary=(
        "Guided external-flow starter for a 2D-style NACA 0012 airfoil validation setup with pressure-coefficient inspection "
        "and angle-of-attack-ready baseline controls."
    ),
    focus_workflows=("Airfoil validation", "Pressure coefficients", "External aerodynamics"),
    milestones=(
        "Import the airfoil profile or section body and create a compact wind-tunnel domain around it.",
        "Use steady external-flow physics with air material and potential-flow initialization for robust startup.",
        "Create inlet, outlet, symmetry, and airfoil wall boundaries suitable for lift and pressure studies.",
        "Inspect pressure-coefficient distribution and wake structure before running angle-of-attack variations.",
    ),
    key_parameters=(
        "Starter inlet velocity baseline Ux = 30 m/s with steady incompressible external flow.",
        "Use k-omega SST as the airfoil-safe turbulence default and keep potential-flow initialization enabled.",
        "Primary result surface is a surface pressure-coefficient plot on the airfoil body.",
    ),
    reference_url="https://help.sim-flow.com/tutorials/airfoil-naca-0012",
    step_overrides={
        2: {
            "name": "Prepare Airfoil And Wind Tunnel",
            "description": "Import the airfoil section and size a wind-tunnel domain that preserves clean upstream and downstream spacing.",
            "hint": "This starter is meant to make lift/pressure studies straightforward, not to automate airfoil generation yet.",
        },
        5: {
            "name": "Assign Airfoil Boundary Set",
            "description": "Configure inlet, outlet, symmetry, and airfoil wall boundaries for the external-flow starter case.",
            "hint": "Keep the airfoil wall separate from the far-field boundaries so surface pressure inspection stays clean.",
        },
        9: {
            "name": "Inspect Pressure Coefficients And Wake",
            "description": "Review the starter pressure-coefficient surface and one wake view before sweeping angle of attack.",
            "hint": "This guided starter is the baseline for later angle-of-attack and lift/drag comparison tooling.",
        },
    },
)


_STATIC_MIXER_RECIPE = StudyRecipe(
    key="cfd-static-mixer",
    domain_key="CFD",
    study_keys=("cfd-static-mixer",),
    analysis_types=("Internal Flow",),
    label="Static Mixer Passive Scalar",
    summary=(
        "Guided transient internal-flow recipe for passive-scalar mixing studies where the flow remains single phase but scalar transport is the primary result."
    ),
    focus_workflows=("Passive scalar", "Internal flow", "Mixing diagnostics"),
    milestones=(
        "Create the mixer body and split the inlet into separate scalar-bearing feed patches.",
        "Set a transient internal-flow study with water-like properties and passive-scalar transport enabled.",
        "Apply distinct scalar values at the inlet patches while keeping the carrier flow single phase.",
        "Inspect scalar slices and streamlines to verify downstream mixing quality.",
    ),
    key_parameters=(
        "Use a transient incompressible single-phase flow model with passive scalar enabled.",
        "Keep the scalar transport decoupled from material-property changes to preserve the intended benchmark simplification.",
        "Prioritize inlet-splitting, scalar BCs, and mixing slices over advanced geometry automation.",
    ),
    reference_url="https://help.sim-flow.com/tutorials/static-mixer",
    step_overrides={
        2: {
            "name": "Prepare Mixer And Split Inlets",
            "description": "Import or build the mixer core and create separate inlet patches for the scalar0 and scalar1 feeds.",
            "hint": "The important setup action is splitting the inlet so each branch can carry a distinct passive scalar value.",
        },
        3: {
            "name": "Configure Transient Scalar Physics",
            "description": "Use a transient incompressible CFD study and enable passive scalar transport for mixing diagnostics.",
            "hint": "This family is still single-phase CFD; the scalar is a tracer, not a separate material region.",
        },
        9: {
            "name": "Inspect Mixing Quality",
            "description": "Visualize scalar slices and streamlines to verify how the two inlet streams mix through the static blades.",
            "hint": "Passive scalar is the main result field for this recipe, not pressure or temperature.",
        },
    },
)


_TESLA_VALVE_RECIPE = StudyRecipe(
    key="cfd-tesla-valve",
    domain_key="CFD",
    study_keys=("cfd-tesla-valve",),
    analysis_types=("Internal Flow",),
    label="Tesla Valve Starter",
    summary=(
        "Guided internal-flow starter for a Tesla valve baseline with pressure-focused post-processing and placeholder forward/reverse boundary setup "
        "before full periodic-interface automation is introduced."
    ),
    focus_workflows=("Internal flow", "Pressure drop", "Tesla valve comparison"),
    milestones=(
        "Import the Tesla valve channel and keep the forward and reverse driving faces identifiable.",
        "Use a steady incompressible internal-flow setup with water-like material and pressure/velocity baseline controls.",
        "Prepare inlet, outlet, and wall boundaries for a starter forward-flow pressure-drop run.",
        "Inspect pressure distribution and velocity guidance through the valve before adding reverse-flow comparisons.",
    ),
    key_parameters=(
        "Starter inlet velocity baseline Ux = 1.5 m/s with steady incompressible internal flow.",
        "Primary result surface is a pressure cut plot to highlight the valve pressure-drop behavior.",
        "Periodic or AMI-specific workflow automation is still pending beyond this starter scaffold.",
    ),
    reference_url="https://help.sim-flow.com/tutorials/tesla-valve",
    step_overrides={
        2: {
            "name": "Prepare Tesla Valve Channel",
            "description": "Import or model the Tesla valve channel and keep the forward-flow inlet and outlet faces identifiable.",
            "hint": "The guided starter establishes one baseline direction first; richer forward/reverse automation still comes later.",
        },
        5: {
            "name": "Assign Valve Boundary Set",
            "description": "Configure inlet, outlet, and wall conditions for a baseline Tesla-valve pressure-drop run.",
            "hint": "Treat periodic and interface-specific workflow support as future refinement, not part of the current starter.",
        },
        9: {
            "name": "Inspect Pressure Drop And Guidance",
            "description": "Review pressure and velocity behavior through the valve path before setting up comparison directions.",
            "hint": "Use the pressure plot first, then compare streamline steering through the main and side channels.",
        },
    },
)


_VON_KARMAN_RECIPE = StudyRecipe(
    key="cfd-von-karman-vortex-street",
    domain_key="CFD",
    study_keys=("cfd-von-karman-vortex-street",),
    analysis_types=("External Flow",),
    label="Von Karman Validation Starter",
    summary=(
        "Guided transient external-flow starter for a Von Karman vortex street benchmark with vorticity-focused inspection and a validation-case posture "
        "before richer parameterized geometry tooling is added."
    ),
    focus_workflows=("Transient CFD", "Vorticity inspection", "Validation case"),
    milestones=(
        "Import the cylinder or bluff-body geometry and size a wake-resolving external domain around it.",
        "Use transient external-flow controls with air material and a low-speed validation-style inlet baseline.",
        "Configure inlet, outlet, wall, and far-field boundaries appropriate for vortex shedding observation.",
        "Inspect vorticity shedding patterns and wake development before adding benchmark comparison tooling.",
    ),
    key_parameters=(
        "Starter inlet velocity baseline Ux = 2.0 m/s with transient incompressible external flow.",
        "Primary result surface is a vorticity cut plot for wake-shedding inspection.",
        "Parameterized geometry and benchmark comparison automation are still pending beyond this starter scaffold.",
    ),
    reference_url="https://help.sim-flow.com/tutorials/von-karman-vortex-street",
    step_overrides={
        2: {
            "name": "Prepare Bluff Body And Wake Domain",
            "description": "Import the cylinder or bluff-body geometry and create an external domain with enough downstream length for wake development.",
            "hint": "The starter focuses on wake inspection and transient setup, not on automating the validation geometry itself.",
        },
        5: {
            "name": "Assign Validation Boundary Set",
            "description": "Configure inlet, outlet, body wall, and far-field boundaries for the transient wake benchmark.",
            "hint": "Keep the cylinder wall separate from the far-field surfaces so wake and force analysis stay clean.",
        },
        9: {
            "name": "Inspect Vortex Shedding",
            "description": "Review vorticity and wake shedding behavior before extending into frequency or force-history comparisons.",
            "hint": "The vorticity cut plot is the primary starter result for confirming the shedding pattern.",
        },
    },
)


_STRUCTURAL_BRACKET_RECIPE = StudyRecipe(
    key="structural-bracket-example",
    domain_key="Structural",
    study_keys=("structural-bracket-example",),
    analysis_types=("Static Linear Elastic",),
    label="Structural Bracket Starter",
    summary=(
        "Guided structural starter for a cantilever-style bracket with an aluminum material, fixed support, "
        "and a single downward tip load that exercises the basic stress workflow end to end."
    ),
    focus_workflows=("Static structural", "Bracket loading", "Stress inspection"),
    milestones=(
        "Import or model the bracket and keep the support and loaded faces named clearly.",
        "Use a linear-elastic structural model with aluminum material and an Elmer structural solver.",
        "Apply one fixed support and one concentrated tip load to establish the baseline load case.",
        "Review displacement and stress hotspots before iterating on geometry or constraints.",
    ),
    key_parameters=(
        "Material preset Aluminum 6061-T6 with steady linear-elastic analysis.",
        "Support BC label support_face and load BC label tip_load.",
        "Starter load uses ForceZ = -1500 N as the benchmark baseline.",
    ),
    reference_url=_FLOWSTUDIO_EXAMPLES_REFERENCE,
    step_overrides={
        2: {
            "name": "Prepare Bracket Geometry",
            "description": "Import or model the bracket and identify the support face and the loaded tip face.",
            "hint": "Keep support_face and tip_load readable so the structural BC mapping stays obvious.",
        },
        5: {
            "name": "Apply Support And Tip Load",
            "description": "Constrain the bracket at the support face and apply the downward force at the tip loading region.",
            "hint": "This starter expects one fixed displacement BC and one downward tip load around -1500 N.",
        },
        9: {
            "name": "Inspect Stress And Deflection",
            "description": "Review von Mises stress and displacement to confirm the bracket load path and hotspot regions.",
            "hint": "Use the starter result pass to locate peak stress near the support before refining the mesh or load case.",
        },
    },
)


_ELECTROSTATIC_CAPACITOR_RECIPE = StudyRecipe(
    key="electrostatic-capacitor-example",
    domain_key="Electrostatic",
    study_keys=("electrostatic-capacitor-example",),
    analysis_types=("Capacitance Matrix",),
    label="Electrostatic Capacitor Starter",
    summary=(
        "Guided electrostatic starter for a parallel-plate capacitor with a dielectric fill and paired electrode potentials "
        "focused on field-map and capacitance-matrix setup."
    ),
    focus_workflows=("Capacitance", "Potential maps", "Dielectric studies"),
    milestones=(
        "Prepare the plate and dielectric geometry and keep the positive and grounded electrodes identifiable.",
        "Enable capacitance-matrix solving with a dielectric material model and Elmer electrostatics.",
        "Drive the field with one positive electrode and one grounded electrode.",
        "Inspect potential contours and capacitance outputs before extending to more conductors.",
    ),
    key_parameters=(
        "Material preset PTFE (Teflon) with MaterialName PTFE.",
        "Positive plate BC label anode at 5 V and ground plate BC label cathode at 0 V.",
        "Capacitance matrix calculation is enabled in the starter physics model.",
    ),
    reference_url=_FLOWSTUDIO_EXAMPLES_REFERENCE,
    step_overrides={
        2: {
            "name": "Prepare Plates And Dielectric",
            "description": "Import or model the capacitor plates and the dielectric region between them.",
            "hint": "Keep anode and cathode geometry regions easy to identify before assigning voltages.",
        },
        5: {
            "name": "Assign Electrode Potentials",
            "description": "Apply the positive and grounded electrode potentials that define the capacitor field.",
            "hint": "Use the starter posture: anode at 5 V and cathode at 0 V with a dielectric between them.",
        },
        9: {
            "name": "Inspect Potential And Capacitance",
            "description": "Review electric potential distribution and the resulting capacitance matrix output.",
            "hint": "Check field concentration near plate edges before changing dielectric material or spacing.",
        },
    },
)


_ELECTROMAGNETIC_COIL_RECIPE = StudyRecipe(
    key="electromagnetic-coil-example",
    domain_key="Electromagnetic",
    study_keys=("electromagnetic-coil-example",),
    analysis_types=("Magnetostatic",),
    label="Electromagnetic Coil Starter",
    summary=(
        "Guided magnetostatic starter for a simple energized coil with copper material, current-density excitation, "
        "and a far-field magnetic potential boundary."
    ),
    focus_workflows=("Magnetostatics", "Coil excitation", "Field inspection"),
    milestones=(
        "Prepare the coil and surrounding air domain and keep the excited winding region obvious.",
        "Use a magnetostatic electromagnetic model with copper material and Elmer as the starter backend.",
        "Drive the model with a current-density source and a far-field magnetic boundary.",
        "Inspect magnetic field concentration and boundary behavior before adding more complex devices.",
    ),
    key_parameters=(
        "Material preset Copper with steady magnetostatic physics.",
        "Current BC label coil_current with CurrentDensityZ = 2.0e6 A/m^2.",
        "Far-field boundary uses BC label far_field with zero magnetic potential.",
    ),
    reference_url=_FLOWSTUDIO_EXAMPLES_REFERENCE,
    step_overrides={
        2: {
            "name": "Prepare Coil And Air Domain",
            "description": "Import or model the coil conductor and the surrounding region used for the magnetic solution.",
            "hint": "Keep the excited winding and far-field boundary regions distinct from the start.",
        },
        5: {
            "name": "Apply Coil Excitation And Far Field",
            "description": "Assign the current density source to the coil and a zero-potential boundary to the outer field region.",
            "hint": "This starter expects coil_current excitation and a far_field magnetic-potential boundary.",
        },
        9: {
            "name": "Inspect Magnetic Field Response",
            "description": "Review flux density and field concentration around the energized coil and the outer boundary.",
            "hint": "Check that the field decays cleanly toward the far-field boundary before increasing fidelity.",
        },
    },
)


_THERMAL_PLATE_RECIPE = StudyRecipe(
    key="thermal-plate-example",
    domain_key="Thermal",
    study_keys=("thermal-plate-example",),
    analysis_types=("Steady-State Heat Transfer",),
    label="Thermal Plate Starter",
    summary=(
        "Guided thermal starter for a heated aluminum plate with a localized heat-flux source and ambient convection, "
        "intended to exercise steady conduction-plus-cooling setup."
    ),
    focus_workflows=("Conduction", "Convection", "Temperature inspection"),
    milestones=(
        "Prepare the plate geometry and identify the heated patch and ambient cooling faces.",
        "Use a steady thermal model with aluminum material and Elmer as the starter solver.",
        "Apply one heat-flux source and one convection boundary for ambient cooling.",
        "Inspect temperature gradients before moving into transient or coupled studies.",
    ),
    key_parameters=(
        "Material preset Aluminum with steady-state heat transfer physics.",
        "Heat-flux BC label heater_pad with HeatFlux = 5000 W/m^2.",
        "Convection BC label ambient_air with h = 25 W/m^2-K and Tamb = 293.15 K.",
    ),
    reference_url=_FLOWSTUDIO_EXAMPLES_REFERENCE,
    step_overrides={
        2: {
            "name": "Prepare Plate And Cooling Faces",
            "description": "Import or model the plate and identify the heater patch and the faces exposed to ambient cooling.",
            "hint": "Keep heater_pad and ambient_air regions identifiable for the starter BC mapping.",
        },
        5: {
            "name": "Apply Heat Flux And Convection",
            "description": "Drive the plate with a heater flux and ambient convection boundary to establish the baseline thermal gradient.",
            "hint": "This starter uses a heater flux plus ambient convection rather than internal heat generation.",
        },
        9: {
            "name": "Inspect Temperature Distribution",
            "description": "Review the temperature field from heater patch to cooled boundaries before extending the study.",
            "hint": "Use the starter result pass to confirm the expected gradient from the heated pad into the plate.",
        },
    },
)


_OPTICAL_LENS_RECIPE = StudyRecipe(
    key="optical-lens-example",
    domain_key="Optical",
    study_keys=("optical-lens-example",),
    analysis_types=("Illumination",),
    label="Optical Lens Starter",
    summary=(
        "Guided optical starter for a non-sequential lens illumination setup with a Lambertian LED source, an irradiance detector, "
        "and a reflective housing boundary."
    ),
    focus_workflows=("Illumination", "Non-sequential ray trace", "Detector inspection"),
    milestones=(
        "Prepare the lens, source, detector, and housing geometry used by the illumination setup.",
        "Use a non-sequential optical model with BK7 lens material and a Raysect starter backend.",
        "Place the LED-like source, irradiance detector, and reflective housing boundary objects.",
        "Inspect detector illumination and housing reflections before changing source power or sampling.",
    ),
    key_parameters=(
        "Optical model Non-Sequential Ray Trace at 550 nm with starter ray counts of 20000 and 10000 at the source.",
        "Lens material preset BK7 with OpticalRole Glass.",
        "Reflective housing boundary uses Reflectivity = 0.95 and detector type Irradiance.",
    ),
    reference_url=_FLOWSTUDIO_EXAMPLES_REFERENCE,
    step_overrides={
        2: {
            "name": "Prepare Lens, Source, And Detector Geometry",
            "description": "Import or model the lens assembly, source position, detector plane, and reflective housing surfaces.",
            "hint": "Keep source, detector, and housing regions distinct so the optical BC objects stay easy to map.",
        },
        5: {
            "name": "Place Source, Detector, And Housing Boundary",
            "description": "Configure the Lambertian LED source, irradiance detector, and reflective housing boundary for the starter illumination setup.",
            "hint": "This starter expects a Lambertian LED source, an irradiance detector, and a reflective housing boundary.",
        },
        9: {
            "name": "Inspect Detector Illumination",
            "description": "Review detector irradiance and the effect of reflective housing boundaries on the illumination pattern.",
            "hint": "Use the detector output first, then inspect whether the reflective housing is shaping the beam as expected.",
        },
    },
)


_RECIPES = (
    _ELECTRONICS_COOLING_RECIPE,
    _COOLING_CHANNEL_RECIPE,
    _PIPE_FLOW_RECIPE,
    _EXTERNAL_AERO_RECIPE,
    _BUILDINGS_RECIPE,
    _AIRFOIL_RECIPE,
    _STATIC_MIXER_RECIPE,
    _TESLA_VALVE_RECIPE,
    _VON_KARMAN_RECIPE,
    _STRUCTURAL_BRACKET_RECIPE,
    _ELECTROSTATIC_CAPACITOR_RECIPE,
    _ELECTROMAGNETIC_COIL_RECIPE,
    _THERMAL_PLATE_RECIPE,
    _OPTICAL_LENS_RECIPE,
)


def get_study_recipe(
    domain_key: str | None = None,
    analysis_type: str | None = None,
    study_key: str | None = None,
) -> StudyRecipe | None:
    """Return one study recipe when the domain and analysis type match a known guided study."""
    if not domain_key:
        return None
    normalized_key = str(study_key or "").strip().lower()
    if normalized_key:
        for recipe in _RECIPES:
            if recipe.domain_key != domain_key:
                continue
            if any(normalized_key == key.strip().lower() for key in recipe.study_keys):
                return recipe

    if not analysis_type:
        return None
    normalized_type = str(analysis_type).strip().lower()
    for recipe in _RECIPES:
        if recipe.domain_key != domain_key:
            continue
        if not recipe.auto_select:
            continue
        if any(normalized_type == option.strip().lower() for option in recipe.analysis_types):
            return recipe
    return None