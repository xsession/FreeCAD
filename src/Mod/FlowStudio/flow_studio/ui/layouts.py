# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""CST-inspired workspace layout metadata for FlowStudio domains."""

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkspaceLayout:
    key: str
    name: str
    description: str
    left_panes: tuple[str, ...]
    center_focus: tuple[str, ...]
    right_panes: tuple[str, ...]
    bottom_panes: tuple[str, ...]
    primary_workflows: tuple[str, ...]


_DEFAULT_LAYOUT = WorkspaceLayout(
    key="default",
    name="Engineering Cockpit",
    description="Project tree, 3D scene, contextual properties, and jobs/results panes.",
    left_panes=("Project Tree", "Navigation", "Selections"),
    center_focus=("3D Viewport", "Scene Presets", "Model Overlays"),
    right_panes=("Properties", "Task Panel", "Validation"),
    bottom_panes=("Jobs", "Logs", "Monitors", "Results"),
    primary_workflows=("Guided setup", "Validation-rich edits", "Run and compare"),
)

_LAYOUTS = {
    "CFD": WorkspaceLayout(
        key="cfd",
        name="CFD Project Cockpit",
        description="CST-style study cockpit adapted for geometry, mesh, BCs, monitors, and CFD runs.",
        left_panes=("Project Tree", "Domains", "Boundary Groups"),
        center_focus=("3D Viewport", "Flow Regions", "Mesh Preview"),
        right_panes=("Physics", "Boundary Properties", "Workflow Tasks"),
        bottom_panes=("Residuals", "Run Console", "Jobs", "Results"),
        primary_workflows=("Internal flow", "External aero", "Electronics cooling"),
    ),
    "Thermal": WorkspaceLayout(
        key="thermal",
        name="Thermal Study Layout",
        description="Heat-path oriented layout with material, source, and report focus.",
        left_panes=("Project Tree", "Parts", "Thermal Interfaces"),
        center_focus=("3D Viewport", "Heat Sources", "Temperature Scenes"),
        right_panes=("Material Properties", "Loads", "Workflow Tasks"),
        bottom_panes=("Solver Logs", "KPIs", "Reports", "Results"),
        primary_workflows=("Conduction", "Convection", "Radiation"),
    ),
    "Structural": WorkspaceLayout(
        key="structural",
        name="Structural Analysis Layout",
        description="Constraint, load, and deformation oriented workspace for structural studies.",
        left_panes=("Project Tree", "Bodies", "Load Cases"),
        center_focus=("3D Viewport", "Constraint Glyphs", "Mesh Preview"),
        right_panes=("Materials", "Loads", "Solver Controls"),
        bottom_panes=("Jobs", "Logs", "Plots", "Results"),
        primary_workflows=("Static stress", "Displacement", "Thermo-mechanical prep"),
    ),
    "Electrostatic": WorkspaceLayout(
        key="electrostatic",
        name="Electrostatic Layout",
        description="Field setup workspace centered on dielectrics, potentials, and field monitors.",
        left_panes=("Project Tree", "Bodies", "Excitations"),
        center_focus=("3D Viewport", "Field Regions", "Sensor Preview"),
        right_panes=("Materials", "Potentials", "Workflow Tasks"),
        bottom_panes=("Jobs", "Logs", "Field Probes", "Results"),
        primary_workflows=("Capacitance", "Potential maps", "Dielectric studies"),
    ),
    "Electromagnetic": WorkspaceLayout(
        key="electromagnetic",
        name="EM Project Layout",
        description="Excitation-first workspace for sources, ports, field probes, and solver settings.",
        left_panes=("Project Tree", "Components", "Excitations"),
        center_focus=("3D Viewport", "Field Monitors", "Region Preview"),
        right_panes=("Materials", "Sources", "Frequency Setup"),
        bottom_panes=("Jobs", "Logs", "Monitors", "Results"),
        primary_workflows=("Magnetostatics", "Low-frequency EM", "Device studies"),
    ),
    "Optical": WorkspaceLayout(
        key="optical",
        name="Optical Lab Layout",
        description="CST-inspired optical project workspace with components, excitations, detectors, and result planes.",
        left_panes=("Project Tree", "Optical Components", "Sources and Detectors"),
        center_focus=("3D Viewport", "Ray/Field Preview", "Detector Planes"),
        right_panes=("Material Optics", "Study Controls", "Workflow Tasks"),
        bottom_panes=("Jobs", "Logs", "Detector Outputs", "Results"),
        primary_workflows=("Non-sequential ray tracing", "Illumination", "Wave optics setup"),
    ),
}


def get_workspace_layout(domain_key: str | None = None) -> WorkspaceLayout:
    """Return the recommended workspace layout for one FlowStudio domain."""
    if not domain_key:
        return _DEFAULT_LAYOUT
    return _LAYOUTS.get(domain_key, _DEFAULT_LAYOUT)