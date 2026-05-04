use crate::domain::{
    normalize_workbench_id, workbench_display_name, DocumentSummary,
    ExtensionCompatibilityLane, ExtensionCompatibilityState, Menu, MenuBarState, MenuItem,
    RecentDocumentEntry, ShellInspectionState, ShellLayoutState, ShellPanelState,
    ShellSnapshot, StepAssemblyNode, StepSceneBundle, Toolbar, ToolbarBand, ToolbarBandState,
    ToolbarItem, WorkbenchCatalog, WorkbenchCatalogEntry, WorkspaceSessionEntry,
};
use asterforge_freecad_bridge::BridgeDocumentSnapshot;

pub fn shell_snapshot_from_bridge(
    snapshot: &BridgeDocumentSnapshot,
    document: &DocumentSummary,
    extension_compatibility: &ExtensionCompatibilityState,
    selected_object_id: Option<&str>,
    can_undo: bool,
    can_redo: bool,
    recent_documents: &[RecentDocumentEntry],
    workspace_sessions: &[WorkspaceSessionEntry],
    combo_view_tab: &str,
    bottom_dock_tab: &str,
    combo_view_visible: bool,
    report_dock_visible: bool,
    combo_view_size_hint: f32,
    report_dock_size_hint: f32,
) -> ShellSnapshot {
    let workbench_catalog = workbench_catalog_from_bridge(snapshot);
    ShellSnapshot {
        document: document.clone(),
        workbench_catalog: workbench_catalog.clone(),
        menu_bar: menu_bar_state_from_bridge(
            snapshot,
            selected_object_id,
            can_undo,
            can_redo,
            combo_view_visible,
            report_dock_visible,
            combo_view_tab,
            bottom_dock_tab,
        ),
        toolbar_bands: toolbar_band_state_from_bridge(
            snapshot,
            selected_object_id,
            can_undo,
            can_redo,
        ),
        layout: shell_layout_state_from_bridge(
            document,
            combo_view_tab,
            bottom_dock_tab,
            combo_view_visible,
            report_dock_visible,
            combo_view_size_hint,
            report_dock_size_hint,
        ),
        recent_documents: recent_documents.to_vec(),
        workspace_sessions: workspace_sessions.to_vec(),
        inspection: None,
        extension_compatibility: extension_compatibility.clone(),
        status_bar: None,
    }
}

pub fn step_shell_snapshot(
    document: &DocumentSummary,
    extension_compatibility: &ExtensionCompatibilityState,
    selected_object_id: Option<&str>,
    recent_documents: &[RecentDocumentEntry],
    workspace_sessions: &[WorkspaceSessionEntry],
    combo_view_tab: &str,
    bottom_dock_tab: &str,
    combo_view_visible: bool,
    report_dock_visible: bool,
    combo_view_size_hint: f32,
    report_dock_size_hint: f32,
    scene: &StepSceneBundle,
    can_hide_selection: bool,
    can_isolate_selection: bool,
    can_show_all: bool,
    can_measure_selection: bool,
    inspection: Option<ShellInspectionState>,
) -> ShellSnapshot {
    ShellSnapshot {
        document: document.clone(),
        workbench_catalog: step_workbench_catalog(),
        menu_bar: step_menu_bar_state(
            selected_object_id,
            bottom_dock_tab,
            combo_view_visible,
            report_dock_visible,
            scene,
            can_hide_selection,
            can_isolate_selection,
            can_show_all,
            can_measure_selection,
        ),
        toolbar_bands: step_toolbar_band_state(
            selected_object_id,
            scene,
            can_hide_selection,
            can_isolate_selection,
            can_show_all,
            can_measure_selection,
        ),
        layout: shell_layout_state_from_bridge(
            document,
            combo_view_tab,
            bottom_dock_tab,
            combo_view_visible,
            report_dock_visible,
            combo_view_size_hint,
            report_dock_size_hint,
        ),
        recent_documents: recent_documents.to_vec(),
        workspace_sessions: workspace_sessions.to_vec(),
        inspection,
        extension_compatibility: extension_compatibility.clone(),
        status_bar: None,
    }
}

pub fn extension_compatibility_state() -> ExtensionCompatibilityState {
    ExtensionCompatibilityState {
        title: "Extension Compatibility".into(),
        summary: "Backend-owned staging lane for macros, AddonManager flows, and external workbench compatibility while Qt-era assumptions are retired incrementally.".into(),
        lanes: vec![
            ExtensionCompatibilityLane {
                lane_id: "macros".into(),
                label: "Macro execution and management".into(),
                status: "staging".into(),
                owner: "Shell and command runtime".into(),
                summary: "The Macro menu now routes into the TypeScript shell so macro discovery, execution, and review can move behind backend-owned state instead of a disabled placeholder.".into(),
                next_steps: vec![
                    "Add backend macro inventory and command metadata.".into(),
                    "Expose execution and trust boundaries without reviving Qt dialogs.".into(),
                ],
                command_ids: vec!["extensions.refresh_inventory".into()],
                inventory_entries: vec![],
            },
            ExtensionCompatibilityLane {
                lane_id: "addon-manager".into(),
                label: "AddonManager and package flows".into(),
                status: "planned".into(),
                owner: "Extension services".into(),
                summary: "Addon installation, update, and compatibility review still depend on Qt and PySide-era assumptions, but this shell snapshot now reserves an API-backed landing surface for that work.".into(),
                next_steps: vec![
                    "Publish addon inventory, provenance, and compatibility diagnostics.".into(),
                    "Add install, update, and disable workflows through backend services.".into(),
                ],
                command_ids: vec!["extensions.review_addon_catalog".into()],
                inventory_entries: vec![],
            },
            ExtensionCompatibilityLane {
                lane_id: "external-workbenches".into(),
                label: "External workbench registration".into(),
                status: "planned".into(),
                owner: "Workbench platform".into(),
                summary: "InitGui.py discovery and external workbench registration need an explicit compatibility lane so plugins can surface commands, chrome, and onboarding without assuming Qt widgets.".into(),
                next_steps: vec![
                    "Model external workbench manifests and command registration contracts.".into(),
                    "Define shell-safe fallbacks for Qt-bound task panels and dialogs.".into(),
                ],
                command_ids: vec!["extensions.review_external_workbenches".into()],
                inventory_entries: vec![],
            },
        ],
    }
}

pub(super) fn step_workbench_catalog() -> WorkbenchCatalog {
    let mut workbenches = vec![make_workbench_catalog_entry("step", true)];
    workbenches.extend(default_workbench_catalog_entries());

    WorkbenchCatalog {
        active_workbench_id: "step".into(),
        workbenches,
    }
}

fn step_menu_bar_state(
    selected_object_id: Option<&str>,
    bottom_dock_tab: &str,
    combo_view_visible: bool,
    report_dock_visible: bool,
    scene: &StepSceneBundle,
    can_hide_selection: bool,
    can_isolate_selection: bool,
    can_show_all: bool,
    can_measure_selection: bool,
) -> MenuBarState {
    let has_parent = selected_object_id
        .and_then(|object_id| step_parent_entity_id(selected_step_entity_id(object_id)?, &scene.assemblies))
        .is_some();
    let has_child = selected_object_id
        .and_then(|object_id| step_first_child_entity_id(selected_step_entity_id(object_id)?, &scene.assemblies))
        .is_some();
    let has_pmi = selected_object_id
        .and_then(selected_step_entity_id)
        .map(|entity_id| {
            scene
                .semantic_pmi
                .iter()
                .any(|annotation| annotation.target_entity_ids.contains(&entity_id))
        })
        .unwrap_or(false);

    MenuBarState {
        workbench_id: "step".into(),
        menus: vec![
            Menu {
                menu_id: "file".into(),
                label: "File".into(),
                visible: true,
                items: vec![
                    command_menu_item("Open...", "document.open", true),
                    command_menu_item("Save", "document.save", true),
                ],
            },
            Menu {
                menu_id: "edit".into(),
                label: "Edit".into(),
                visible: true,
                items: vec![command_menu_item(
                    "Focus Selection",
                    "selection.focus",
                    selected_object_id.is_some(),
                )],
            },
            Menu {
                menu_id: "view".into(),
                label: "View".into(),
                visible: true,
                items: vec![
                    command_menu_item("Live", "step.view_reset", true),
                    command_menu_item("Fit All", "step.view_fit_all", true),
                    command_menu_item("Isometric", "step.view_iso", true),
                    command_menu_item("Front", "step.view_front", true),
                    command_menu_item("Back", "step.view_back", true),
                    command_menu_item("Right", "step.view_right", true),
                    command_menu_item("Left", "step.view_left", true),
                    command_menu_item("Top", "step.view_top", true),
                    command_menu_item("Bottom", "step.view_bottom", true),
                    toggle_menu_item("Combo View", combo_view_visible, Some("shell.toggle_combo_view")),
                    toggle_menu_item(
                        "Report View",
                        report_dock_visible && bottom_dock_tab == "report",
                        Some("shell.show_report_view"),
                    ),
                ],
            },
            Menu {
                menu_id: "step".into(),
                label: "STEP".into(),
                visible: true,
                items: vec![
                    command_menu_item("Select Parent", "step.select_parent", has_parent),
                    command_menu_item("Select Child", "step.select_first_child", has_child),
                    command_menu_item("Inspect PMI", "step.inspect_pmi", has_pmi),
                    command_menu_item(
                        "Measure Selection",
                        "step.measure_selection",
                        can_measure_selection,
                    ),
                    command_menu_item("Hide Selection", "step.hide_selection", can_hide_selection),
                    command_menu_item(
                        "Isolate Selection",
                        "step.isolate_selection",
                        can_isolate_selection,
                    ),
                    command_menu_item("Show All", "step.show_all", can_show_all),
                ],
            },
            Menu {
                menu_id: "window".into(),
                label: "Window".into(),
                visible: true,
                items: vec![
                    toggle_menu_item("Model tree", combo_view_visible, Some("shell.show_model_stack")),
                    toggle_menu_item("Bottom dock", report_dock_visible, Some("shell.toggle_bottom_dock")),
                ],
            },
        ],
    }
}

fn step_toolbar_band_state(
    selected_object_id: Option<&str>,
    scene: &StepSceneBundle,
    can_hide_selection: bool,
    can_isolate_selection: bool,
    can_show_all: bool,
    can_measure_selection: bool,
) -> ToolbarBandState {
    let has_parent = selected_object_id
        .and_then(|object_id| step_parent_entity_id(selected_step_entity_id(object_id)?, &scene.assemblies))
        .is_some();
    let has_child = selected_object_id
        .and_then(|object_id| step_first_child_entity_id(selected_step_entity_id(object_id)?, &scene.assemblies))
        .is_some();
    let has_pmi = selected_object_id
        .and_then(selected_step_entity_id)
        .map(|entity_id| {
            scene
                .semantic_pmi
                .iter()
                .any(|annotation| annotation.target_entity_ids.contains(&entity_id))
        })
        .unwrap_or(false);

    ToolbarBandState {
        workbench_id: "step".into(),
        bands: vec![
            ToolbarBand {
                band_id: "document".into(),
                label: "Document".into(),
                toolbars: vec![Toolbar {
                    toolbar_id: "document-standard".into(),
                    label: "Standard".into(),
                    visible: true,
                    items: vec![
                        command_toolbar_item("document.save", "Save", Some("save".into()), true),
                        command_toolbar_item(
                            "selection.focus",
                            "Focus",
                            Some("focus".into()),
                            selected_object_id.is_some(),
                        ),
                    ],
                }],
            },
            ToolbarBand {
                band_id: "step".into(),
                label: "STEP".into(),
                toolbars: vec![
                    Toolbar {
                        toolbar_id: "step-view".into(),
                        label: "View".into(),
                        visible: true,
                        items: vec![
                            command_toolbar_item("step.view_reset", "Live", Some("focus".into()), true),
                            command_toolbar_item("step.view_fit_all", "Fit", Some("focus".into()), true),
                            command_toolbar_item("step.view_iso", "Iso", Some("focus".into()), true),
                            command_toolbar_item("step.view_front", "Front", Some("focus".into()), true),
                            command_toolbar_item("step.view_back", "Back", Some("focus".into()), true),
                            command_toolbar_item("step.view_right", "Right", Some("focus".into()), true),
                            command_toolbar_item("step.view_left", "Left", Some("focus".into()), true),
                            command_toolbar_item("step.view_top", "Top", Some("focus".into()), true),
                            command_toolbar_item("step.view_bottom", "Bottom", Some("focus".into()), true),
                        ],
                    },
                    Toolbar {
                        toolbar_id: "step-inspection".into(),
                        label: "Inspection".into(),
                        visible: true,
                        items: vec![
                            command_toolbar_item(
                                "step.select_parent",
                                "Parent",
                                Some("history".into()),
                                has_parent,
                            ),
                            command_toolbar_item(
                                "step.select_first_child",
                                "Child",
                                Some("focus".into()),
                                has_child,
                            ),
                            command_toolbar_item("step.inspect_pmi", "PMI", Some("focus".into()), has_pmi),
                            command_toolbar_item(
                                "step.measure_selection",
                                "Measure",
                                Some("measure".into()),
                                can_measure_selection,
                            ),
                            command_toolbar_item("step.hide_selection", "Hide", Some("hide".into()), can_hide_selection),
                            command_toolbar_item(
                                "step.isolate_selection",
                                "Isolate",
                                Some("isolate".into()),
                                can_isolate_selection,
                            ),
                            command_toolbar_item("step.show_all", "Show All", Some("show".into()), can_show_all),
                        ],
                    },
                ],
            },
        ],
    }
}

fn selected_step_entity_id(object_id: &str) -> Option<u64> {
    object_id.strip_prefix("step-entity-")?.parse::<u64>().ok()
}

fn step_parent_entity_id(entity_id: u64, assemblies: &[StepAssemblyNode]) -> Option<u64> {
    for assembly in assemblies {
        if assembly.children.iter().any(|child| child.entity_id == entity_id) {
            return Some(assembly.entity_id);
        }
        if let Some(found) = step_parent_entity_id(entity_id, &assembly.children) {
            return Some(found);
        }
    }
    None
}

fn step_first_child_entity_id(entity_id: u64, assemblies: &[StepAssemblyNode]) -> Option<u64> {
    for assembly in assemblies {
        if assembly.entity_id == entity_id {
            return assembly.children.first().map(|child| child.entity_id);
        }
        if let Some(found) = step_first_child_entity_id(entity_id, &assembly.children) {
            return Some(found);
        }
    }
    None
}

fn workbench_category(value: &str) -> String {
    match normalize_workbench_id(value).as_str() {
        "step" => "Inspection".into(),
        "start" => "Onboarding".into(),
        "partdesign" | "part" | "sketcher" => "Core modeling".into(),
        "assembly" => "Mechanical assembly".into(),
        "draft" | "techdraw" => "Drafting".into(),
        "bim" => "Built environment".into(),
        "cam" => "Manufacturing".into(),
        "fem" | "material" | "spreadsheet" | "import" => "Support and analysis".into(),
        "mesh" | "surface" | "reverseengineering" | "robot" => "Specialist geometry".into(),
        _ => "Current context".into(),
    }
}

fn workbench_migration_lane(value: &str) -> String {
    match normalize_workbench_id(value).as_str() {
        "step" => "In progress".into(),
        "partdesign" | "part" | "sketcher" | "assembly" => "Queued primary".into(),
        "draft" | "techdraw" | "cam" | "fem" | "spreadsheet" | "material" | "import" => {
            "Queued secondary".into()
        }
        "bim" => "Compatibility-heavy".into(),
        "mesh" | "surface" | "reverseengineering" | "robot" => "Specialist".into(),
        "start" => "Foundation".into(),
        _ => "Bridge surfaced".into(),
    }
}

fn workbench_description(value: &str) -> String {
    match normalize_workbench_id(value).as_str() {
        "step" => "Read-only STEP inspection and interchange review.".into(),
        "start" => "Startup, onboarding, templates, and entry workflows.".into(),
        "partdesign" => "Parametric feature modeling for bodies and sketches.".into(),
        "part" => "Direct solid modeling and Boolean operations.".into(),
        "sketcher" => "Constraint-driven 2D profile editing.".into(),
        "assembly" => "Joint, placement, BOM, and assembly context workflows.".into(),
        "draft" => "2D drafting, construction geometry, and annotation helpers.".into(),
        "techdraw" => "Drawing-sheet generation, dimensions, and production documentation.".into(),
        "bim" => "IFC-driven building and facility modeling workflows.".into(),
        "cam" => "Manufacturing setup, operations, tool libraries, and simulation.".into(),
        "fem" => "Meshing, solver setup, constraints, and simulation review.".into(),
        "spreadsheet" => "Parametric tabular data, expressions, and linked model values.".into(),
        "material" => "Material assignment, lookup, and property editing flows.".into(),
        "import" => "Import preferences and format-specific conversion helpers.".into(),
        "mesh" => "Mesh inspection and repair tools.".into(),
        "surface" => "Surface modeling helpers and repair-oriented geometry tools.".into(),
        "reverseengineering" => "Scanned-geometry cleanup and reverse-engineering helpers.".into(),
        "robot" => "Robot trajectory, kinematics, and cell-oriented workflows.".into(),
        _ => "Workbench surfaced from the current bridge snapshot.".into(),
    }
}

fn workbench_icon(value: &str) -> Option<String> {
    match normalize_workbench_id(value).as_str() {
        "step" | "mesh" => Some("mesh".into()),
        "partdesign" => Some("partdesign".into()),
        "part" | "assembly" => Some("part".into()),
        "sketcher" | "draft" | "techdraw" => Some("sketcher".into()),
        _ => None,
    }
}

fn make_workbench_catalog_entry(value: &str, enabled: bool) -> WorkbenchCatalogEntry {
    WorkbenchCatalogEntry {
        workbench_id: normalize_workbench_id(value),
        display_name: workbench_display_name(value),
        icon: workbench_icon(value),
        enabled,
        description: Some(workbench_description(value)),
        category: workbench_category(value),
        migration_lane: workbench_migration_lane(value),
    }
}

fn default_workbench_catalog_entries() -> Vec<WorkbenchCatalogEntry> {
    [
        "start",
        "partdesign",
        "part",
        "sketcher",
        "assembly",
        "draft",
        "techdraw",
        "bim",
        "cam",
        "fem",
        "spreadsheet",
        "material",
        "import",
        "mesh",
        "surface",
        "reverseengineering",
        "robot",
    ]
    .into_iter()
    .map(|workbench_id| {
        make_workbench_catalog_entry(
            workbench_id,
            matches!(workbench_id, "partdesign" | "part" | "sketcher" | "mesh"),
        )
    })
    .collect()
}

pub(super) fn workbench_catalog_from_bridge(snapshot: &BridgeDocumentSnapshot) -> WorkbenchCatalog {
    let active_workbench_id = normalize_workbench_id(&snapshot.workbench);
    let mut workbenches = default_workbench_catalog_entries();

    if let Some(entry) = workbenches
        .iter_mut()
        .find(|entry| entry.workbench_id == active_workbench_id)
    {
        entry.enabled = true;
    } else {
        workbenches.insert(0, make_workbench_catalog_entry(&snapshot.workbench, true));
    }

    WorkbenchCatalog {
        active_workbench_id,
        workbenches,
    }
}

fn menu_bar_state_from_bridge(
    snapshot: &BridgeDocumentSnapshot,
    selected_object_id: Option<&str>,
    can_undo: bool,
    can_redo: bool,
    combo_view_visible: bool,
    report_dock_visible: bool,
    combo_view_tab: &str,
    bottom_dock_tab: &str,
) -> MenuBarState {
    let workbench_id = normalize_workbench_id(&snapshot.workbench);
    let selected_node = selected_object_id.and_then(|object_id| find_bridge_object(snapshot, object_id));
    let selected_is_body = matches!(selected_node.map(|node| node.object_type.as_str()), Some("PartDesign::Body"));
    let selected_is_sketch = matches!(selected_node.map(|node| node.object_type.as_str()), Some("Sketcher::SketchObject"));
    let selected_is_feature = matches!(
        selected_node.map(|node| node.object_type.as_str()),
        Some("PartDesign::Pad") | Some("PartDesign::Pocket")
    );
    let tools_menu_items = if workbench_id == "partdesign" {
        vec![
            command_menu_item("New Sketch", "partdesign.new_sketch", selected_is_body),
            command_menu_item("Pad", "partdesign.pad", selected_is_sketch),
            command_menu_item("Pocket", "partdesign.pocket", selected_is_sketch),
            command_menu_item("Edit Pad", "partdesign.edit_pad", selected_is_feature),
        ]
    } else {
        vec![
            command_menu_item("Focus Selection", "selection.focus", selected_object_id.is_some()),
            command_menu_item("Rollback Here", "history.rollback_here", selected_is_feature),
            command_menu_item("Toggle Suppression", "model.toggle_suppression", selected_is_feature),
            command_menu_item("Resume Full", "history.resume_full", snapshot.history_marker.is_some()),
        ]
    };

    MenuBarState {
        workbench_id,
        menus: vec![
            Menu {
                menu_id: "file".into(),
                label: "File".into(),
                visible: true,
                items: vec![
                    command_menu_item("Open...", "document.open", true),
                    command_menu_item("Save", "document.save", true),
                    separator_menu_item(),
                    command_menu_item("Recompute", "document.recompute", true),
                ],
            },
            Menu {
                menu_id: "edit".into(),
                label: "Edit".into(),
                visible: true,
                items: vec![
                    command_menu_item("Undo", "document.undo", can_undo),
                    command_menu_item("Redo", "document.redo", can_redo),
                    separator_menu_item(),
                    command_menu_item("Focus Selection", "selection.focus", selected_object_id.is_some()),
                ],
            },
            Menu {
                menu_id: "view".into(),
                label: "View".into(),
                visible: true,
                items: vec![
                    toggle_menu_item("Combo View", combo_view_visible, Some("shell.toggle_combo_view")),
                    toggle_menu_item(
                        "Report View",
                        report_dock_visible && bottom_dock_tab == "report",
                        Some("shell.show_report_view"),
                    ),
                    toggle_menu_item(
                        "Python Console",
                        report_dock_visible && bottom_dock_tab == "python",
                        Some("shell.show_python_console"),
                    ),
                    toggle_menu_item(
                        "Extensions",
                        report_dock_visible && bottom_dock_tab == "extensions",
                        Some("shell.show_extensions_manager"),
                    ),
                ],
            },
            Menu {
                menu_id: "tools".into(),
                label: "Tools".into(),
                visible: true,
                items: tools_menu_items,
            },
            Menu {
                menu_id: "macro".into(),
                label: "Macro".into(),
                visible: true,
                items: vec![toggle_menu_item(
                    "Macro and Addon Compatibility",
                    report_dock_visible && bottom_dock_tab == "extensions",
                    Some("shell.show_extensions_manager"),
                )],
            },
            Menu {
                menu_id: "window".into(),
                label: "Window".into(),
                visible: true,
                items: vec![
                    toggle_menu_item(
                        "Model tree",
                        combo_view_visible && combo_view_tab == "model",
                        Some("shell.show_model_stack"),
                    ),
                    toggle_menu_item(
                        "Task stack",
                        combo_view_visible && combo_view_tab == "tasks",
                        Some("shell.show_task_stack"),
                    ),
                    toggle_menu_item("Bottom dock", report_dock_visible, Some("shell.toggle_bottom_dock")),
                ],
            },
            Menu {
                menu_id: "help".into(),
                label: "Help".into(),
                visible: true,
                items: vec![MenuItem {
                    kind: "action".into(),
                    label: Some("AsterForge parity workspace".into()),
                    command_id: None,
                    enabled: Some(true),
                    checked: None,
                    submenu: None,
                }],
            },
        ],
    }
}

fn toolbar_band_state_from_bridge(
    snapshot: &BridgeDocumentSnapshot,
    selected_object_id: Option<&str>,
    can_undo: bool,
    can_redo: bool,
) -> ToolbarBandState {
    let workbench_id = normalize_workbench_id(&snapshot.workbench);
    let selected_node = selected_object_id.and_then(|object_id| find_bridge_object(snapshot, object_id));
    let selected_kind = selected_node.map(|node| node.object_type.as_str()).unwrap_or("");
    let selected_is_body = selected_kind == "PartDesign::Body";
    let selected_is_sketch = selected_kind == "Sketcher::SketchObject";
    let selected_is_feature = matches!(selected_kind, "PartDesign::Pad" | "PartDesign::Pocket");
    let workbench_band = if workbench_id == "partdesign" {
        ToolbarBand {
            band_id: "partdesign".into(),
            label: "PartDesign".into(),
            toolbars: vec![Toolbar {
                toolbar_id: "partdesign-operations".into(),
                label: "Operations".into(),
                visible: true,
                items: vec![
                    command_toolbar_item(
                        "partdesign.new_sketch",
                        "New Sketch",
                        Some("sketch".into()),
                        selected_is_body,
                    ),
                    command_toolbar_item("partdesign.pad", "Pad", Some("pad".into()), selected_is_sketch),
                    command_toolbar_item(
                        "partdesign.pocket",
                        "Pocket",
                        Some("pocket".into()),
                        selected_is_sketch,
                    ),
                    command_toolbar_item(
                        "partdesign.edit_pad",
                        "Edit",
                        Some("edit".into()),
                        selected_is_feature,
                    ),
                ],
            }],
        }
    } else {
        ToolbarBand {
            band_id: workbench_id.clone(),
            label: workbench_display_name(&workbench_id),
            toolbars: vec![Toolbar {
                toolbar_id: format!("{}-tools", workbench_id),
                label: "Workbench tools".into(),
                visible: true,
                items: vec![
                    command_toolbar_item(
                        "selection.focus",
                        "Focus",
                        Some("focus".into()),
                        selected_object_id.is_some(),
                    ),
                    command_toolbar_item(
                        "history.rollback_here",
                        "Rollback",
                        Some("history".into()),
                        selected_is_feature,
                    ),
                    command_toolbar_item(
                        "model.toggle_suppression",
                        "Toggle",
                        Some("toggle".into()),
                        selected_is_feature,
                    ),
                ],
            }],
        }
    };

    ToolbarBandState {
        workbench_id,
        bands: vec![
            ToolbarBand {
                band_id: "document".into(),
                label: "Document".into(),
                toolbars: vec![Toolbar {
                    toolbar_id: "document-standard".into(),
                    label: "Standard".into(),
                    visible: true,
                    items: vec![
                        command_toolbar_item("document.undo", "Undo", Some("undo".into()), can_undo),
                        command_toolbar_item("document.redo", "Redo", Some("redo".into()), can_redo),
                        command_toolbar_item("document.save", "Save", Some("save".into()), true),
                        command_toolbar_item(
                            "document.recompute",
                            "Recompute",
                            Some("recompute".into()),
                            true,
                        ),
                    ],
                }],
            },
            ToolbarBand {
                band_id: "selection".into(),
                label: "Selection".into(),
                toolbars: vec![Toolbar {
                    toolbar_id: "selection-tools".into(),
                    label: "Selection tools".into(),
                    visible: true,
                    items: vec![
                        command_toolbar_item(
                            "selection.focus",
                            "Focus",
                            Some("focus".into()),
                            selected_object_id.is_some(),
                        ),
                        command_toolbar_item(
                            "history.resume_full",
                            "Resume Full",
                            Some("history".into()),
                            true,
                        ),
                    ],
                }],
            },
            workbench_band,
        ],
    }
}

fn shell_layout_state_from_bridge(
    document: &DocumentSummary,
    combo_view_tab: &str,
    bottom_dock_tab: &str,
    combo_view_visible: bool,
    report_dock_visible: bool,
    combo_view_size_hint: f32,
    report_dock_size_hint: f32,
) -> ShellLayoutState {
    ShellLayoutState {
        layout_id: format!("{}:freecad-classic", document.document_id),
        panels: vec![
            ShellPanelState {
                panel_id: "combo_view".into(),
                region: "left".into(),
                visible: combo_view_visible,
                order: 0,
                active_tab: Some(combo_view_tab.into()),
                size_hint: Some(combo_view_size_hint),
            },
            ShellPanelState {
                panel_id: "viewport".into(),
                region: "center".into(),
                visible: true,
                order: 1,
                active_tab: Some("3d".into()),
                size_hint: Some(0.56),
            },
            ShellPanelState {
                panel_id: "report_dock".into(),
                region: "bottom".into(),
                visible: report_dock_visible,
                order: 2,
                active_tab: Some(bottom_dock_tab.into()),
                size_hint: Some(report_dock_size_hint),
            },
            ShellPanelState {
                panel_id: "status_bar".into(),
                region: "bottom".into(),
                visible: true,
                order: 3,
                active_tab: None,
                size_hint: Some(0.08),
            },
        ],
    }
}

fn command_menu_item(label: &str, command_id: &str, enabled: bool) -> MenuItem {
    MenuItem {
        kind: "command".into(),
        label: Some(label.into()),
        command_id: Some(command_id.into()),
        enabled: Some(enabled),
        checked: None,
        submenu: None,
    }
}

fn separator_menu_item() -> MenuItem {
    MenuItem {
        kind: "separator".into(),
        label: None,
        command_id: None,
        enabled: None,
        checked: None,
        submenu: None,
    }
}

fn toggle_menu_item(label: &str, checked: bool, command_id: Option<&str>) -> MenuItem {
    MenuItem {
        kind: "toggle".into(),
        label: Some(label.into()),
        command_id: command_id.map(str::to_string),
        enabled: Some(true),
        checked: Some(checked),
        submenu: None,
    }
}

fn command_toolbar_item(
    command_id: &str,
    label: &str,
    icon: Option<String>,
    enabled: bool,
) -> ToolbarItem {
    ToolbarItem {
        kind: "command".into(),
        command_id: Some(command_id.into()),
        label: Some(label.into()),
        icon,
        enabled: Some(enabled),
        checked: None,
    }
}

fn find_bridge_object<'a>(
    snapshot: &'a BridgeDocumentSnapshot,
    object_id: &str,
) -> Option<&'a asterforge_freecad_bridge::BridgeObjectNode> {
    snapshot
        .roots
        .iter()
        .flat_map(|root| std::iter::once(root).chain(root.children.iter()))
        .find(|node| node.object_id == object_id)
}
