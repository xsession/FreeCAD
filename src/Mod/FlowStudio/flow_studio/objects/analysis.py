# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""SimulationAnalysis – top-level analysis container for any physics domain.

Replaces the old CFDAnalysis with a domain-aware container that supports
CFD, FEM/structural, electrostatic, electromagnetic, thermal, and optical analyses.
Inspired by CST Studio Suite's multi-physics project concept.
"""

import FreeCAD
from flow_studio.objects.base_object import BaseFlowObject


class CFDAnalysis(BaseFlowObject):
    """Container that groups all simulation objects for a single analysis.

    The ``PhysicsDomain`` property selects which physics discipline this
    analysis represents (CFD, Structural, Electrostatic, Electromagnetic,
    Thermal, Optical).  The ``AnalysisType`` enum is dynamically populated based on
    the chosen domain.

    Kept as ``CFDAnalysis`` class name for backward compatibility — the
    ``Type`` string now depends on the domain.
    """

    Type = "FlowStudio::CFDAnalysis"

    # Map domain key → FlowType string for the analysis
    _DOMAIN_TYPES = {
        "CFD": "FlowStudio::CFDAnalysis",
        "Structural": "FlowStudio::StructuralAnalysis",
        "Electrostatic": "FlowStudio::ElectrostaticAnalysis",
        "Electromagnetic": "FlowStudio::ElectromagneticAnalysis",
        "Thermal": "FlowStudio::ThermalAnalysis",
        "Optical": "FlowStudio::OpticalAnalysis",
    }

    def __init__(self, obj, domain_key="CFD"):
        super().__init__(obj)

        # --- Physics Domain selector ---
        from flow_studio.physics_domains import available_domains
        obj.addProperty(
            "App::PropertyEnumeration", "PhysicsDomain", "Analysis",
            "Physics discipline for this analysis"
        )
        obj.PhysicsDomain = available_domains()
        obj.PhysicsDomain = domain_key

        # Set type based on domain
        type_str = self._DOMAIN_TYPES.get(domain_key, "FlowStudio::CFDAnalysis")
        obj.FlowType = type_str
        self.Type = type_str

        # --- Solver backend ---
        obj.addProperty(
            "App::PropertyString", "SolverBackend", "Solver",
            "Active solver backend"
        )
        # Default solver depends on domain
        if domain_key == "CFD":
            obj.SolverBackend = "OpenFOAM"
        elif domain_key == "Optical":
            obj.SolverBackend = "Raysect"
        else:
            obj.SolverBackend = "Elmer"

        obj.addProperty(
            "App::PropertyPath", "CaseDir", "Solver",
            "Working directory for solver case files"
        )
        obj.addProperty(
            "App::PropertyBool", "IsSetup", "Status",
            "True when the analysis is fully configured"
        )
        obj.IsSetup = False

        # --- Dirty-tracking flags (CfdOF-inspired) ---
        obj.addProperty(
            "App::PropertyBool", "NeedsMeshRewrite", "Status",
            "Mesh parameters changed – mesh case must be rewritten"
        )
        obj.NeedsMeshRewrite = True

        obj.addProperty(
            "App::PropertyBool", "NeedsCaseRewrite", "Status",
            "Solver/physics/BCs changed – case files must be rewritten"
        )
        obj.NeedsCaseRewrite = True

        obj.addProperty(
            "App::PropertyBool", "NeedsMeshRerun", "Status",
            "Mesh files written but mesher has not run yet"
        )
        obj.NeedsMeshRerun = True

        # --- Analysis type (populated from domain) ---
        obj.addProperty(
            "App::PropertyEnumeration", "AnalysisType", "Analysis",
            "Type of simulation analysis"
        )
        self._update_analysis_types(obj, domain_key)

    def _update_analysis_types(self, obj, domain_key):
        """Populate AnalysisType enum from the physics domain."""
        if not hasattr(obj, "AnalysisType"):
            return
        from flow_studio.physics_domains import get_domain
        domain = get_domain(domain_key)
        if domain and domain.analysis_types:
            obj.AnalysisType = domain.analysis_types
        else:
            obj.AnalysisType = ["General"]

    def onChanged(self, obj, prop):
        """React to property changes."""
        if prop == "PhysicsDomain":
            domain_key = obj.PhysicsDomain
            self._update_analysis_types(obj, domain_key)
            # Update FlowType
            type_str = self._DOMAIN_TYPES.get(
                domain_key, "FlowStudio::CFDAnalysis"
            )
            try:
                if not obj.isRestoring():
                    obj.FlowType = type_str
            except AttributeError:
                # isRestoring not available during initial property setup
                pass
            self.Type = type_str
