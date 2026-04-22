# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Bridge legacy Flow Studio document objects into the enterprise model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from flow_studio.enterprise.core.domain import (
    MaterialAssignment,
    MeshRecipe,
    PhysicsDefinition,
    ProjectManifest,
    StudyDefinition,
)


def _safe_getattr(obj, name: str, default=None):
    """Return an attribute value from a FreeCAD object or test double."""

    try:
        return getattr(obj, name)
    except Exception:
        return default


def _group_items(obj) -> Sequence[object]:
    """Return grouped child objects from a Flow Studio analysis-like object."""

    group = _safe_getattr(obj, "Group", ())
    return tuple(group or ())


def _serialize_references(obj: object) -> tuple[str, ...]:
    refs = _safe_getattr(obj, "References", ()) or ()
    targets: list[str] = []
    for ref_obj, sub_elements in refs:
        obj_name = _safe_getattr(ref_obj, "Name", None) or _safe_getattr(ref_obj, "Label", None)
        base_ref = f"Document/{obj_name or 'LinkedObject'}"
        if isinstance(sub_elements, str):
            sub_names = (sub_elements,)
        else:
            sub_names = tuple(sub_elements or ())
        if sub_names:
            targets.extend(f"{base_ref}/{sub_name}" for sub_name in sub_names)
        else:
            targets.append(base_ref)
    return tuple(dict.fromkeys(targets))


def _reference_targets(obj: object, fallback: str) -> tuple[str, ...]:
    """Return stable document target refs from a FreeCAD References property."""

    refs = _safe_getattr(obj, "References", ()) or ()
    targets: list[str] = []
    for ref_obj, sub_elements in refs:
        obj_name = _safe_getattr(ref_obj, "Name", None) or _safe_getattr(ref_obj, "Label", None)
        base_ref = f"Document/{obj_name or 'LinkedObject'}"
        if isinstance(sub_elements, str):
            sub_names = (sub_elements,)
        else:
            sub_names = tuple(sub_elements or ())
        if sub_names:
            targets.extend(f"{base_ref}/{sub_name}" for sub_name in sub_names)
        else:
            targets.append(base_ref)
    return tuple(dict.fromkeys(targets)) or (fallback,)


@dataclass(frozen=True)
class LegacyAnalysisBridge:
    """Translate existing analysis containers into canonical study models.

    The bridge deliberately maps only stable, solver-neutral concepts into the
    canonical model. Backend-specific knobs are preserved in
    `adapter_extensions`.
    """

    analysis_object: object
    solver_backend_override: str | None = None

    def to_study_definition(self) -> StudyDefinition:
        """Build a canonical study definition from a Flow Studio analysis."""

        analysis = self.analysis_object
        solver_object = self._find_first(("FlowStudio::Solver",))
        solver_backend = _safe_getattr(
            solver_object,
            "SolverBackend",
            _safe_getattr(analysis, "SolverBackend", "OpenFOAM"),
        )
        solver_backend = self.solver_backend_override or solver_backend
        solver_family = self._map_solver_family(solver_backend)
        mesh_object = self._find_first(("FlowStudio::MeshGmsh",))
        physics_object = self._find_first(("FlowStudio::PhysicsModel",))
        material_object = self._find_first(("FlowStudio::FluidMaterial",))

        mesh_recipe = MeshRecipe(
            generator_id=self._mesh_generator_id(mesh_object),
            global_size=self._mesh_global_size(mesh_object),
            boundary_layers_enabled=bool(self._find_first(("FlowStudio::BoundaryLayer",))),
            local_controls=(),
        )

        return StudyDefinition(
            study_id=_safe_getattr(analysis, "Name", "FlowStudy"),
            name=_safe_getattr(analysis, "Label", _safe_getattr(analysis, "Name", "Flow Study")),
            solver_family=solver_family,
            geometry_ref=self._geometry_ref(mesh_object),
            mesh_recipe=mesh_recipe,
            materials=self._materials(material_object),
            physics=self._physics(physics_object),
            parameters=self._parameters(analysis, solver_object, solver_backend),
            adapter_extensions=self._adapter_extensions(solver_backend, solver_object),
        )

    def _find_first(self, flow_types: Iterable[str]):
        for child in _group_items(self.analysis_object):
            if _safe_getattr(child, "FlowType", "") in set(flow_types):
                return child
        return None

    @staticmethod
    def _map_solver_family(solver_backend: str) -> str:
        mapping = {
            "OpenFOAM": "openfoam",
            "Elmer": "elmer",
            "FluidX3D": "fluidx3d",
            "Geant4": "geant4",
        }
        return mapping.get(solver_backend, solver_backend.lower())

    @staticmethod
    def _mesh_generator_id(mesh_object: object | None) -> str:
        if mesh_object is None:
            return "gmsh.default"
        flow_type = _safe_getattr(mesh_object, "FlowType", "")
        if flow_type == "FlowStudio::MeshGmsh":
            return "gmsh.default"
        return "mesh.unspecified"

    @staticmethod
    def _mesh_global_size(mesh_object: object | None) -> float:
        if mesh_object is None:
            return 10.0
        for candidate in ("CharacteristicLength", "MaxElementSize", "MinElementSize"):
            value = _safe_getattr(mesh_object, candidate, None)
            if value is not None:
                try:
                    return float(value)
                except (TypeError, ValueError):
                    continue
        return 10.0

    @staticmethod
    def _geometry_ref(mesh_object: object | None) -> str:
        if mesh_object is None:
            return "Document/UnassignedGeometry"
        part = _safe_getattr(mesh_object, "Part", None)
        if part is None:
            return "Document/UnassignedGeometry"
        label = _safe_getattr(part, "Name", None) or _safe_getattr(part, "Label", None)
        return f"Document/{label or 'LinkedPart'}"

    @staticmethod
    def _materials(material_object: object | None) -> tuple[MaterialAssignment, ...]:
        if material_object is None:
            return ()
        properties: Mapping[str, float | str | bool] = {
            "density": float(_safe_getattr(material_object, "Density", 0.0) or 0.0),
            "dynamic_viscosity": float(
                _safe_getattr(material_object, "DynamicViscosity", 0.0) or 0.0
            ),
            "specific_heat": float(_safe_getattr(material_object, "SpecificHeat", 0.0) or 0.0),
            "thermal_conductivity": float(
                _safe_getattr(material_object, "ThermalConductivity", 0.0) or 0.0
            ),
        }
        targets = _reference_targets(material_object, "FluidDomain")
        return tuple(
            MaterialAssignment(
                target_ref=target,
                material_id=str(_safe_getattr(material_object, "MaterialName", "fluid")),
                properties=properties,
            )
            for target in targets
        )

    @staticmethod
    def _physics(physics_object: object | None) -> tuple[PhysicsDefinition, ...]:
        if physics_object is None:
            return ()
        options: Mapping[str, str | float | bool] = {
            "flow_regime": str(_safe_getattr(physics_object, "FlowRegime", "Laminar")),
            "turbulence_model": str(
                _safe_getattr(physics_object, "TurbulenceModel", "kOmegaSST")
            ),
            "compressibility": str(
                _safe_getattr(physics_object, "Compressibility", "Incompressible")
            ),
            "time_model": str(_safe_getattr(physics_object, "TimeModel", "Steady")),
            "heat_transfer": bool(_safe_getattr(physics_object, "HeatTransfer", False)),
            "gravity": bool(_safe_getattr(physics_object, "Gravity", False)),
            "buoyancy": bool(_safe_getattr(physics_object, "Buoyancy", False)),
        }
        family = "cfd.internal"
        if options["heat_transfer"]:
            family = "cht"
        return (
            PhysicsDefinition(
                physics_id="primary",
                family=family,
                options=options,
            ),
        )

    @staticmethod
    def _parameters(
        analysis_object: object,
        solver_object: object | None,
        solver_backend: str,
    ) -> Mapping[str, str | float | bool]:
        multi_solver_backends = _safe_getattr(solver_object, "MultiSolverBackends", ()) or ()
        if isinstance(multi_solver_backends, str):
            serialized_multi_backends = multi_solver_backends
        else:
            serialized_multi_backends = ",".join(
                str(item).strip() for item in multi_solver_backends if str(item).strip()
            )
        return {
            "physics_domain": str(_safe_getattr(analysis_object, "PhysicsDomain", "CFD")),
            "analysis_type": str(_safe_getattr(analysis_object, "AnalysisType", "General")),
            "needs_mesh_rewrite": bool(_safe_getattr(analysis_object, "NeedsMeshRewrite", False)),
            "needs_case_rewrite": bool(_safe_getattr(analysis_object, "NeedsCaseRewrite", False)),
            "selected_solver_backend": str(solver_backend),
            "multi_solver_enabled": bool(_safe_getattr(solver_object, "MultiSolverEnabled", False)),
            "multi_solver_backends": serialized_multi_backends,
            "soft_runtime_warning_seconds": int(
                _safe_getattr(solver_object, "SoftRuntimeWarningSeconds", 0) or 0
            ),
            "max_runtime_seconds": int(_safe_getattr(solver_object, "MaxRuntimeSeconds", 0) or 0),
            "stall_timeout_seconds": int(_safe_getattr(solver_object, "StallTimeoutSeconds", 0) or 0),
            "min_progress_percent": float(_safe_getattr(solver_object, "MinProgressPercent", 0.0) or 0.0),
            "abort_on_threshold": bool(_safe_getattr(solver_object, "AbortOnThreshold", True)),
        }

    def _adapter_extensions(
        self, solver_backend: str, solver_object: object | None
    ) -> Mapping[str, Mapping[str, str | float | bool]]:
        if solver_backend == "OpenFOAM":
            if solver_object is None:
                return {}
            return {
                "openfoam.primary": {
                    "solver_binary": str(_safe_getattr(solver_object, "OpenFOAMSolver", "simpleFoam")),
                    "max_iterations": int(_safe_getattr(solver_object, "MaxIterations", 1000)),
                    "convergence_tolerance": float(
                        _safe_getattr(solver_object, "ConvergenceTolerance", 1e-4)
                    ),
                    "write_interval": int(_safe_getattr(solver_object, "WriteInterval", 100)),
                    "num_processors": int(_safe_getattr(solver_object, "NumProcessors", 1)),
                }
            }
        if solver_backend == "Elmer":
            if solver_object is None:
                return {}
            return {
                "elmer.primary": {
                    "solver_binary": str(
                        _safe_getattr(solver_object, "ElmerSolverBinary", "ElmerSolver")
                    ),
                    "num_processors": int(_safe_getattr(solver_object, "NumProcessors", 1)),
                    "time_step": float(_safe_getattr(solver_object, "TimeStep", 0.0)),
                    "end_time": float(_safe_getattr(solver_object, "EndTime", 1.0)),
                }
            }
        if solver_backend == "FluidX3D":
            if solver_object is None:
                return {}
            return {
                "fluidx3d.optional": {
                    "precision": str(_safe_getattr(solver_object, "FluidX3DPrecision", "FP32/FP16S")),
                    "resolution": int(_safe_getattr(solver_object, "FluidX3DResolution", 256)),
                    "multi_gpu": bool(_safe_getattr(solver_object, "FluidX3DMultiGPU", False)),
                }
            }
        if solver_backend == "Geant4":
            if solver_object is None:
                return {}
            sources = []
            detectors = []
            scoring = []
            for child in _group_items(self.analysis_object):
                flow_type = _safe_getattr(child, "FlowType", "")
                if flow_type == "FlowStudio::BCGeant4Source":
                    sources.append({
                        "name": str(_safe_getattr(child, "Name", "Geant4Source")),
                        "label": str(_safe_getattr(child, "Label", _safe_getattr(child, "Name", "Geant4Source"))),
                        "source_type": str(_safe_getattr(child, "SourceType", "Beam")),
                        "particle_type": str(_safe_getattr(child, "ParticleType", "gamma")),
                        "energy_mev": float(_safe_getattr(child, "EnergyMeV", 1.0)),
                        "beam_radius_mm": float(_safe_getattr(child, "BeamRadius", 1.0)),
                        "direction": [
                            float(_safe_getattr(child, "DirectionX", 0.0)),
                            float(_safe_getattr(child, "DirectionY", 0.0)),
                            float(_safe_getattr(child, "DirectionZ", 1.0)),
                        ],
                        "events": int(_safe_getattr(child, "Events", 1000)),
                        "reference_targets": list(_serialize_references(child)),
                    })
                elif flow_type == "FlowStudio::BCGeant4Detector":
                    detectors.append({
                        "name": str(_safe_getattr(child, "Name", "Geant4Detector")),
                        "label": str(_safe_getattr(child, "Label", _safe_getattr(child, "Name", "Geant4Detector"))),
                        "detector_type": str(_safe_getattr(child, "DetectorType", "Sensitive Detector")),
                        "collection_name": str(_safe_getattr(child, "CollectionName", "detectorHits")),
                        "threshold_kev": float(_safe_getattr(child, "ThresholdKeV", 0.0)),
                        "reference_targets": list(_serialize_references(child)),
                    })
                elif flow_type == "FlowStudio::BCGeant4Scoring":
                    scoring.append({
                        "name": str(_safe_getattr(child, "Name", "Geant4Scoring")),
                        "label": str(_safe_getattr(child, "Label", _safe_getattr(child, "Name", "Geant4Scoring"))),
                        "score_quantity": str(_safe_getattr(child, "ScoreQuantity", "DoseDeposit")),
                        "scoring_type": str(_safe_getattr(child, "ScoringType", "Mesh")),
                        "bins": [
                            int(_safe_getattr(child, "BinsX", 16)),
                            int(_safe_getattr(child, "BinsY", 16)),
                            int(_safe_getattr(child, "BinsZ", 16)),
                        ],
                        "normalize_per_event": bool(_safe_getattr(child, "NormalizePerEvent", True)),
                        "reference_targets": list(_serialize_references(child)),
                    })
            return {
                "geant4.primary": {
                    "application_executable": str(
                        _safe_getattr(solver_object, "Geant4Executable", "")
                    ),
                    "physics_list": str(
                        _safe_getattr(solver_object, "Geant4PhysicsList", "FTFP_BERT")
                    ),
                    "event_count": int(_safe_getattr(solver_object, "Geant4EventCount", 1000)),
                    "threads": int(_safe_getattr(solver_object, "Geant4Threads", 1)),
                    "macro_name": str(
                        _safe_getattr(solver_object, "Geant4MacroName", "run.mac")
                    ),
                    "visualization": bool(
                        _safe_getattr(solver_object, "Geant4EnableVisualization", False)
                    ),
                    "sources": sources,
                    "detectors": detectors,
                    "scoring": scoring,
                }
            }
        return {}


def build_project_manifest(
    project_id: str,
    analyses: Sequence[object],
    solver_backend_overrides: Sequence[str | None] | None = None,
) -> ProjectManifest:
    """Build a portable project manifest from one or more analyses."""

    overrides = tuple(solver_backend_overrides or ())
    studies = tuple(
        LegacyAnalysisBridge(
            analysis,
            solver_backend_override=overrides[index] if index < len(overrides) else None,
        ).to_study_definition()
        for index, analysis in enumerate(analyses)
    )
    return ProjectManifest(schema_version="1.0.0", project_id=project_id, studies=studies)
