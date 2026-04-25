# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Application-layer services for frontend-neutral FlowStudio use cases."""

from __future__ import annotations

from importlib import import_module


_SERVICE_MODULES = {
	"FlowStudioOpenBoundaryService": ".bc_open_service",
    "FlowStudioFluidMaterialService": ".fluid_material_service",
	"FlowStudioInitialConditionsService": ".initial_conditions_service",
	"FlowStudioMaterialService": ".material_service",
	"FlowStudioMeshGmshService": ".mesh_gmsh_service",
    "FlowStudioPhysicsModelService": ".physics_model_service",
	"FlowStudioPostPipelineService": ".post_pipeline_service",
	"FlowStudioProjectCockpitService": ".project_cockpit_service",
	"FlowStudioSolverService": ".solver_service",
}

__all__ = [
	"FlowStudioOpenBoundaryService",
	"FlowStudioFluidMaterialService",
	"FlowStudioInitialConditionsService",
	"FlowStudioMaterialService",
	"FlowStudioMeshGmshService",
	"FlowStudioPhysicsModelService",
	"FlowStudioPostPipelineService",
	"FlowStudioProjectCockpitService",
	"FlowStudioSolverService",
]


def __getattr__(name: str):
	module_name = _SERVICE_MODULES.get(name)
	if module_name is None:
		raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
	module = import_module(module_name, __name__)
	value = getattr(module, name)
	globals()[name] = value
	return value


def __dir__():
	return sorted(set(globals()) | set(__all__))