# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""FlowStudio – Object factory functions.

Each ``make*()`` function creates a FreeCAD document object with the
appropriate proxy and (when the GUI is up) the matching ViewProvider.
"""

import FreeCAD


# ======================================================================
# Analysis container
# ======================================================================

def makeAnalysis(doc=None, name="CFDAnalysis"):
    """Create a top-level FlowStudio CFD analysis container."""
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::DocumentObjectGroupPython", name)
    from flow_studio.objects.analysis import CFDAnalysis
    CFDAnalysis(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.vp_analysis import VPCFDAnalysis
        VPCFDAnalysis(obj.ViewObject)
    return obj


# ======================================================================
# Physics model
# ======================================================================

def makePhysicsModel(doc=None, name="PhysicsModel"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.physics_model import PhysicsModel
    PhysicsModel(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.vp_physics_model import VPPhysicsModel
        VPPhysicsModel(obj.ViewObject)
    return obj


# ======================================================================
# Fluid material
# ======================================================================

def makeFluidMaterial(doc=None, name="FluidMaterial"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.fluid_material import FluidMaterial
    FluidMaterial(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.vp_fluid_material import VPFluidMaterial
        VPFluidMaterial(obj.ViewObject)
    return obj


# ======================================================================
# Initial conditions
# ======================================================================

def makeInitialConditions(doc=None, name="InitialConditions"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.initial_conditions import InitialConditions
    InitialConditions(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.vp_initial_conditions import VPInitialConditions
        VPInitialConditions(obj.ViewObject)
    return obj


# ======================================================================
# Boundary conditions
# ======================================================================

def makeBCWall(doc=None, name="Wall"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.bc_wall import BCWall
    BCWall(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.vp_bc_wall import VPBCWall
        VPBCWall(obj.ViewObject)
    return obj


def makeBCInlet(doc=None, name="Inlet"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.bc_inlet import BCInlet
    BCInlet(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.vp_bc_inlet import VPBCInlet
        VPBCInlet(obj.ViewObject)
    return obj


def makeBCOutlet(doc=None, name="Outlet"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.bc_outlet import BCOutlet
    BCOutlet(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.vp_bc_outlet import VPBCOutlet
        VPBCOutlet(obj.ViewObject)
    return obj


def makeBCOpenBoundary(doc=None, name="OpenBoundary"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.bc_open_boundary import BCOpenBoundary
    BCOpenBoundary(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.vp_bc_open_boundary import VPBCOpenBoundary
        VPBCOpenBoundary(obj.ViewObject)
    return obj


def makeBCSymmetry(doc=None, name="Symmetry"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.bc_symmetry import BCSymmetry
    BCSymmetry(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.vp_bc_symmetry import VPBCSymmetry
        VPBCSymmetry(obj.ViewObject)
    return obj


# ======================================================================
# Mesh
# ======================================================================

def makeMeshGmsh(doc=None, name="CFDMesh"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.mesh_gmsh import MeshGmsh
    MeshGmsh(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.vp_mesh_gmsh import VPMeshGmsh
        VPMeshGmsh(obj.ViewObject)
    return obj


def makeMeshRegion(doc=None, name="MeshRegion"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.mesh_region import MeshRegion
    MeshRegion(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.vp_mesh_region import VPMeshRegion
        VPMeshRegion(obj.ViewObject)
    return obj


def makeBoundaryLayer(doc=None, name="BoundaryLayer"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.boundary_layer import BoundaryLayer
    BoundaryLayer(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.vp_boundary_layer import VPBoundaryLayer
        VPBoundaryLayer(obj.ViewObject)
    return obj


# ======================================================================
# Solver
# ======================================================================

def makeSolver(doc=None, name="CFDSolver"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.solver import Solver
    Solver(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.vp_solver import VPSolver
        VPSolver(obj.ViewObject)
    return obj


# ======================================================================
# Post-processing
# ======================================================================

def makePostPipeline(doc=None, name="PostPipeline"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.post_pipeline import PostPipeline
    PostPipeline(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.vp_post_pipeline import VPPostPipeline
        VPPostPipeline(obj.ViewObject)
    return obj


# ======================================================================
# Multi-physics domain objects
# ======================================================================

def makeDomainAnalysis(doc=None, name="Analysis", domain_key="CFD"):
    """Create a physics-domain-aware analysis container.

    Parameters
    ----------
    domain_key : str
        One of "CFD", "Structural", "Electrostatic", "Electromagnetic", "Thermal".
    """
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::DocumentObjectGroupPython", name)
    from flow_studio.objects.analysis import CFDAnalysis
    CFDAnalysis(obj, domain_key=domain_key)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.vp_analysis import VPCFDAnalysis
        VPCFDAnalysis(obj.ViewObject)
    return obj


# --- Structural ---

def makeSolidMaterial(doc=None, name="SolidMaterial"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.solid_material import SolidMaterial
    SolidMaterial(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.base_vp import BaseFlowVP
        BaseFlowVP(obj.ViewObject)
    return obj


def makeStructuralPhysicsModel(doc=None, name="StructuralPhysics"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.structural_physics_model import StructuralPhysicsModel
    StructuralPhysicsModel(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.base_vp import BaseFlowVP
        BaseFlowVP(obj.ViewObject)
    return obj


def makeBCFixedDisplacement(doc=None, name="FixedDisplacement"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.bc_structural import BCFixedDisplacement
    BCFixedDisplacement(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.base_vp import BaseFlowVP
        BaseFlowVP(obj.ViewObject)
    return obj


def makeBCForce(doc=None, name="Force"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.bc_structural import BCForce
    BCForce(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.base_vp import BaseFlowVP
        BaseFlowVP(obj.ViewObject)
    return obj


def makeBCPressureLoad(doc=None, name="PressureLoad"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.bc_structural import BCPressureLoad
    BCPressureLoad(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.base_vp import BaseFlowVP
        BaseFlowVP(obj.ViewObject)
    return obj


# --- Electrostatic ---

def makeElectrostaticMaterial(doc=None, name="ElectrostaticMaterial"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.electrostatic_material import ElectrostaticMaterial
    ElectrostaticMaterial(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.base_vp import BaseFlowVP
        BaseFlowVP(obj.ViewObject)
    return obj


def makeElectrostaticPhysicsModel(doc=None, name="ElectrostaticPhysics"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.electrostatic_physics_model import ElectrostaticPhysicsModel
    ElectrostaticPhysicsModel(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.base_vp import BaseFlowVP
        BaseFlowVP(obj.ViewObject)
    return obj


def makeBCElectricPotential(doc=None, name="ElectricPotential"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.bc_electrostatic import BCElectricPotential
    BCElectricPotential(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.base_vp import BaseFlowVP
        BaseFlowVP(obj.ViewObject)
    return obj


def makeBCSurfaceCharge(doc=None, name="SurfaceCharge"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.bc_electrostatic import BCSurfaceCharge
    BCSurfaceCharge(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.base_vp import BaseFlowVP
        BaseFlowVP(obj.ViewObject)
    return obj


# --- Electromagnetic ---

def makeElectromagneticMaterial(doc=None, name="ElectromagneticMaterial"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.electromagnetic_material import ElectromagneticMaterial
    ElectromagneticMaterial(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.base_vp import BaseFlowVP
        BaseFlowVP(obj.ViewObject)
    return obj


def makeElectromagneticPhysicsModel(doc=None, name="ElectromagneticPhysics"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.electromagnetic_physics_model import ElectromagneticPhysicsModel
    ElectromagneticPhysicsModel(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.base_vp import BaseFlowVP
        BaseFlowVP(obj.ViewObject)
    return obj


def makeBCMagneticPotential(doc=None, name="MagneticPotential"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.bc_electromagnetic import BCMagneticPotential
    BCMagneticPotential(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.base_vp import BaseFlowVP
        BaseFlowVP(obj.ViewObject)
    return obj


def makeBCCurrentDensity(doc=None, name="CurrentDensity"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.bc_electromagnetic import BCCurrentDensity
    BCCurrentDensity(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.base_vp import BaseFlowVP
        BaseFlowVP(obj.ViewObject)
    return obj


# --- Thermal ---

def makeThermalMaterial(doc=None, name="ThermalMaterial"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.thermal_material import ThermalMaterial
    ThermalMaterial(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.base_vp import BaseFlowVP
        BaseFlowVP(obj.ViewObject)
    return obj


def makeThermalPhysicsModel(doc=None, name="ThermalPhysics"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.thermal_physics_model import ThermalPhysicsModel
    ThermalPhysicsModel(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.base_vp import BaseFlowVP
        BaseFlowVP(obj.ViewObject)
    return obj


def makeBCTemperature(doc=None, name="Temperature"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.bc_thermal import BCTemperature
    BCTemperature(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.base_vp import BaseFlowVP
        BaseFlowVP(obj.ViewObject)
    return obj


def makeBCHeatFlux(doc=None, name="HeatFlux"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.bc_thermal import BCHeatFlux
    BCHeatFlux(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.base_vp import BaseFlowVP
        BaseFlowVP(obj.ViewObject)
    return obj


def makeBCConvection(doc=None, name="Convection"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.bc_thermal import BCConvection
    BCConvection(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.base_vp import BaseFlowVP
        BaseFlowVP(obj.ViewObject)
    return obj


def makeBCRadiation(doc=None, name="Radiation"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.bc_thermal import BCRadiation
    BCRadiation(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.base_vp import BaseFlowVP
        BaseFlowVP(obj.ViewObject)
    return obj


# ======================================================================
# Measurement objects (post-processing / Paraview)
# ======================================================================

def makeMeasurementPoint(doc=None, name="ProbePoint"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.measurement_point import MeasurementPoint
    MeasurementPoint(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.vp_measurement_point import VPMeasurementPoint
        VPMeasurementPoint(obj.ViewObject)
    return obj


def makeMeasurementSurface(doc=None, name="MeasureSurface"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.measurement_surface import MeasurementSurface
    MeasurementSurface(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.vp_measurement_surface import VPMeasurementSurface
        VPMeasurementSurface(obj.ViewObject)
    return obj


def makeMeasurementVolume(doc=None, name="MeasureVolume"):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    obj = doc.addObject("App::FeaturePython", name)
    from flow_studio.objects.measurement_volume import MeasurementVolume
    MeasurementVolume(obj)
    if FreeCAD.GuiUp:
        from flow_studio.viewproviders.vp_measurement_volume import VPMeasurementVolume
        VPMeasurementVolume(obj.ViewObject)
    return obj
