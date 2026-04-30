use asterforge_freecad_bridge::{
    body_feature_summary, body_next_step, body_workflow_description, bridge_status,
    dependency_issue_hint, dependency_status_label, dependency_workflow_description,
    open_document_snapshot, pad_inspection_hint, pad_workflow_description,
    pocket_inspection_hint, pocket_workflow_description, sketch_next_step,
    sketch_workflow_description, BridgeDocumentSnapshot, BridgeStatus, DrawableMesh, ViewportDiff,
    ViewportSnapshot,
};
use asterforge_command_core::command_spec;
pub use asterforge_command_core::{CommandArgumentDefinition, CommandDefinition};
pub use asterforge_document_core::{
    DocumentDependencyEdge, DocumentEvaluationState, DocumentGraph, DocumentObjectRecord,
    DocumentSummary, FeatureHistoryEntry, FeatureHistoryResponse,
};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BootReport {
    pub services: Vec<String>,
    pub event_streams: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ObjectNode {
    pub object_id: String,
    pub label: String,
    pub object_type: String,
    pub visibility: VisibilityState,
    pub children: Vec<ObjectNode>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum VisibilityState {
    Visible,
    Hidden,
    Inherited,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PropertyGroup {
    pub group_id: String,
    pub title: String,
    pub properties: Vec<PropertyMetadata>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PropertyResponse {
    pub object_id: String,
    pub groups: Vec<PropertyGroup>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PropertyMetadata {
    pub property_id: String,
    pub display_name: String,
    pub property_type: String,
    pub value_kind: String,
    pub read_only: bool,
    pub unit: Option<String>,
    pub expression_capable: bool,
    pub value_preview: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackendEvent {
    pub topic: String,
    pub level: String,
    pub message: String,
    pub document_id: String,
    pub object_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DiagnosticsResponse {
    pub document_id: String,
    pub summary: DiagnosticsSummary,
    pub selection: DiagnosticsSelection,
    pub recent_signals: Vec<DiagnosticSignal>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DiagnosticsSummary {
    pub total_features: u32,
    pub suppressed_count: u32,
    pub inactive_count: u32,
    pub rolled_back_count: u32,
    pub viewport_drawable_count: u32,
    pub warning_count: u32,
    pub error_count: u32,
    pub history_marker_active: bool,
    pub worker_mode: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DiagnosticsSelection {
    pub object_id: Option<String>,
    pub object_label: Option<String>,
    pub object_type: Option<String>,
    pub model_state: String,
    pub dependency_note: String,
    pub visible_in_viewport: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DiagnosticSignal {
    pub level: String,
    pub title: String,
    pub detail: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SelectionStateResponse {
    pub document_id: String,
    pub current_mode: String,
    pub selected_object_id: String,
    pub selected_object_label: String,
    pub selected_object_type: String,
    pub available_modes: Vec<SelectionModeOption>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SelectionModeOption {
    pub mode_id: String,
    pub label: String,
    pub description: String,
    pub enabled: bool,
    pub object_count: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PreselectionStateResponse {
    pub document_id: String,
    pub current_mode: String,
    pub object_id: Option<String>,
    pub object_label: Option<String>,
    pub object_type: Option<String>,
    pub selectable: bool,
    pub model_state: String,
    pub dependency_note: String,
    pub suggested_commands: Vec<String>,
    pub detail: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JobStatusResponse {
    pub document_id: String,
    pub jobs: Vec<JobStatusEntry>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JobStatusEntry {
    pub job_id: String,
    pub title: String,
    pub command_id: String,
    pub state: String,
    pub progress_percent: u32,
    pub detail: String,
    pub object_id: Option<String>,
    pub stages: Vec<JobStageEntry>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JobStageEntry {
    pub stage_id: String,
    pub label: String,
    pub state: String,
    pub progress_percent: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ViewportResponse {
    pub document_id: String,
    pub selected_object_id: String,
    pub scene: ViewportScene,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ViewportScene {
    pub camera_eye: [f32; 3],
    pub camera_target: [f32; 3],
    pub drawables: Vec<ViewportDrawable>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ViewportDrawable {
    pub object_id: String,
    pub label: String,
    pub kind: String,
    pub accent: String,
    pub bounds: ViewportBounds,
    pub paths: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ViewportBounds {
    pub x: f32,
    pub y: f32,
    pub width: f32,
    pub height: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ViewportDiffResponse {
    pub document_id: String,
    pub selected_object_id: String,
    pub added: Vec<ViewportDrawable>,
    pub removed: Vec<String>,
    pub modified: Vec<ViewportDrawable>,
    pub camera_changed: bool,
    pub camera_eye: Option<[f32; 3]>,
    pub camera_target: Option<[f32; 3]>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkbenchState {
    pub workbench_id: String,
    pub display_name: String,
    pub mode: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkbenchCatalogEntry {
    pub workbench_id: String,
    pub display_name: String,
    pub icon: Option<String>,
    pub enabled: bool,
    pub description: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkbenchCatalog {
    pub active_workbench_id: String,
    pub workbenches: Vec<WorkbenchCatalogEntry>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MenuItem {
    pub kind: String,
    pub label: Option<String>,
    pub command_id: Option<String>,
    pub enabled: Option<bool>,
    pub checked: Option<bool>,
    pub submenu: Option<Menu>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Menu {
    pub menu_id: String,
    pub label: String,
    pub visible: bool,
    pub items: Vec<MenuItem>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MenuBarState {
    pub workbench_id: String,
    pub menus: Vec<Menu>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolbarItem {
    pub kind: String,
    pub command_id: Option<String>,
    pub label: Option<String>,
    pub icon: Option<String>,
    pub enabled: Option<bool>,
    pub checked: Option<bool>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Toolbar {
    pub toolbar_id: String,
    pub label: String,
    pub visible: bool,
    pub items: Vec<ToolbarItem>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolbarBand {
    pub band_id: String,
    pub label: String,
    pub toolbars: Vec<Toolbar>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolbarBandState {
    pub workbench_id: String,
    pub bands: Vec<ToolbarBand>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ShellPanelState {
    pub panel_id: String,
    pub region: String,
    pub visible: bool,
    pub order: u32,
    pub active_tab: Option<String>,
    pub size_hint: Option<f32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ShellLayoutState {
    pub layout_id: String,
    pub panels: Vec<ShellPanelState>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RecentDocumentEntry {
    pub file_path: String,
    pub display_name: String,
    pub workbench: String,
    pub dirty: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkspaceSessionEntry {
    pub session_id: String,
    pub document_id: String,
    pub display_name: String,
    pub file_path: String,
    pub workbench: String,
    pub dirty: bool,
    pub selected_object_id: Option<String>,
    pub selection_mode: Option<String>,
    pub combo_view_tab: Option<String>,
    pub bottom_dock_tab: Option<String>,
    pub combo_view_visible: Option<bool>,
    pub report_dock_visible: Option<bool>,
    pub combo_view_size_hint: Option<f32>,
    pub report_dock_size_hint: Option<f32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ShellSnapshot {
    pub document: DocumentSummary,
    pub workbench_catalog: WorkbenchCatalog,
    pub menu_bar: MenuBarState,
    pub toolbar_bands: ToolbarBandState,
    pub layout: ShellLayoutState,
    pub recent_documents: Vec<RecentDocumentEntry>,
    pub workspace_sessions: Vec<WorkspaceSessionEntry>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CommandCatalogResponse {
    pub document_id: String,
    pub workbench: WorkbenchState,
    pub commands: Vec<CommandDefinition>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskPanelResponse {
    pub document_id: String,
    pub title: String,
    pub description: String,
    pub sections: Vec<TaskPanelSection>,
    pub suggested_commands: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskPanelSection {
    pub section_id: String,
    pub title: String,
    pub rows: Vec<TaskPanelRow>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskPanelRow {
    pub label: String,
    pub value: String,
    pub emphasis: bool,
}

pub fn sample_boot_report() -> BootReport {
    BootReport {
        services: vec![
            "SessionService".into(),
            "DocumentService".into(),
            "CommandService".into(),
            "ViewportService".into(),
            "PropertyService".into(),
            "SelectionService".into(),
            "JobService".into(),
            "PluginService".into(),
            "ImportExportService".into(),
        ],
        event_streams: vec![
            "document_changed".into(),
            "object_added".into(),
            "object_removed".into(),
            "recompute_progress".into(),
            "selection_changed".into(),
            "property_changed".into(),
            "task_status".into(),
            "worker_lifecycle".into(),
            "viewport_updated".into(),
        ],
    }
}

pub fn workbench_state_from_bridge(snapshot: &BridgeDocumentSnapshot) -> WorkbenchState {
    WorkbenchState {
        workbench_id: normalize_workbench_id(&snapshot.workbench),
        display_name: workbench_display_name(&snapshot.workbench),
        mode: "feature_modeling".into(),
    }
}

pub fn normalize_workbench_id(value: &str) -> String {
    let collapsed = value
        .chars()
        .filter(|character| character.is_ascii_alphanumeric())
        .collect::<String>()
        .to_ascii_lowercase();

    match collapsed.as_str() {
        "" | "partdesign" => "partdesign".into(),
        "part" => "part".into(),
        "sketcher" => "sketcher".into(),
        "mesh" | "meshdesign" => "mesh".into(),
        _ => collapsed,
    }
}

pub fn workbench_display_name(value: &str) -> String {
    match normalize_workbench_id(value).as_str() {
        "partdesign" => "PartDesign".into(),
        "part" => "Part".into(),
        "sketcher" => "Sketcher".into(),
        "mesh" => "Mesh".into(),
        _ if value.is_empty() => "PartDesign".into(),
        _ => value.to_string(),
    }
}

pub fn shell_snapshot_from_bridge(
    snapshot: &BridgeDocumentSnapshot,
    document: &DocumentSummary,
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
    }
}

fn workbench_catalog_from_bridge(snapshot: &BridgeDocumentSnapshot) -> WorkbenchCatalog {
    let active_workbench_id = normalize_workbench_id(&snapshot.workbench);
    let mut workbenches = vec![
        WorkbenchCatalogEntry {
            workbench_id: "partdesign".into(),
            display_name: "PartDesign".into(),
            icon: Some("partdesign".into()),
            enabled: true,
            description: Some("Parametric feature modeling for bodies and sketches.".into()),
        },
        WorkbenchCatalogEntry {
            workbench_id: "part".into(),
            display_name: "Part".into(),
            icon: Some("part".into()),
            enabled: true,
            description: Some("Direct solid modeling and Boolean operations.".into()),
        },
        WorkbenchCatalogEntry {
            workbench_id: "sketcher".into(),
            display_name: "Sketcher".into(),
            icon: Some("sketcher".into()),
            enabled: true,
            description: Some("Constraint-driven 2D profile editing.".into()),
        },
        WorkbenchCatalogEntry {
            workbench_id: "mesh".into(),
            display_name: "Mesh".into(),
            icon: Some("mesh".into()),
            enabled: true,
            description: Some("Mesh inspection and repair tools.".into()),
        },
    ];

    if !workbenches
        .iter()
        .any(|entry| entry.workbench_id == active_workbench_id)
    {
        workbenches.insert(
            0,
            WorkbenchCatalogEntry {
                workbench_id: active_workbench_id.clone(),
                display_name: workbench_display_name(&snapshot.workbench),
                icon: Some(active_workbench_id.clone()),
                enabled: true,
                description: Some("Workbench surfaced from the current bridge snapshot.".into()),
            },
        );
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
                items: vec![MenuItem {
                    kind: "action".into(),
                    label: Some("Macro manager pending backend wiring".into()),
                    command_id: None,
                    enabled: Some(false),
                    checked: None,
                    submenu: None,
                }],
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

fn command_definition(
    command_id: &str,
    enabled: bool,
    arguments: Vec<CommandArgumentDefinition>,
) -> CommandDefinition {
    let spec = command_spec(command_id).unwrap_or_else(|| panic!("missing command spec for {command_id}"));

    CommandDefinition {
        command_id: spec.command_id.into(),
        label: spec.label.into(),
        group: spec.group.into(),
        shortcut: spec.shortcut.map(str::to_string),
        enabled,
        requires_selection: spec.requires_selection,
        description: spec.description.into(),
        action_label: spec.action_label.map(str::to_string),
        arguments,
    }
}

pub fn command_catalog_from_bridge(
    snapshot: &BridgeDocumentSnapshot,
    document_id: &str,
    selected_object_id: Option<&str>,
    can_undo: bool,
    can_redo: bool,
) -> CommandCatalogResponse {
    let workbench_id = normalize_workbench_id(&snapshot.workbench);
    let selected_is_body = matches!(selected_object_id, Some("body-001"));
    let selected_node = selected_object_id.and_then(|object_id| find_bridge_object(snapshot, object_id));
    let selected_state = selected_node.map(|node| bridge_object_state(snapshot, node));
    let selected_length_mm = selected_object_id.and_then(|object_id| find_pad_length_mm(snapshot, object_id));
    let selected_plane = selected_node
        .and_then(|node| node.reference_plane.clone())
        .unwrap_or_else(|| "XY".into());
    let selected_extent_mode = selected_node
        .and_then(|node| node.extent_mode.clone())
        .unwrap_or_else(|| "dimension".into());
    let selected_midplane = selected_node.map(|node| node.midplane).unwrap_or(false);
    let selected_is_sketch = matches!(
        selected_node,
        Some(node) if node.object_id.starts_with("sketch-")
    );
    let selected_is_pad = matches!(
        selected_node,
        Some(node) if node.object_id.starts_with("pad-")
    );
    let selected_is_pocket = matches!(
        selected_node,
        Some(node) if node.object_id.starts_with("pocket-")
    );
    let selected_is_feature = matches!(
        selected_node,
        Some(node) if node.object_id != "body-001"
    );
    let history_marker_active = snapshot.history_marker.is_some();
    let selected_is_operable = selected_state
        .as_ref()
        .map(|state| state.active && !state.suppressed)
        .unwrap_or(false);
    let mut commands = vec![
        command_definition("document.recompute", true, vec![]),
        command_definition("document.save", true, vec![]),
        command_definition("selection.focus", selected_object_id.is_some(), vec![]),
    ];

    if workbench_id == "partdesign" {
        commands.extend([
            command_definition("partdesign.new_sketch", selected_is_body, vec![CommandArgumentDefinition {
                    argument_id: "sketch_label".into(),
                    label: "Sketch label".into(),
                    value_type: "string".into(),
                    required: false,
                    default_value: Some("Sketch".into()),
                    placeholder: Some("Sketch".into()),
                    unit: None,
                    options: vec![],
                }, CommandArgumentDefinition {
                    argument_id: "reference_plane".into(),
                    label: "Reference plane".into(),
                    value_type: "enum".into(),
                    required: true,
                    default_value: Some(selected_plane.clone()),
                    placeholder: None,
                    unit: None,
                    options: vec!["XY".into(), "XZ".into(), "YZ".into()],
                }]),
            command_definition("partdesign.pad", selected_is_sketch && selected_is_operable, vec![CommandArgumentDefinition {
                    argument_id: "length_mm".into(),
                    label: "Pad length".into(),
                    value_type: "quantity".into(),
                    required: false,
                    default_value: Some(format!("{:.2}", selected_length_mm.unwrap_or(12.0))),
                    placeholder: Some("12.00".into()),
                    unit: Some("mm".into()),
                    options: vec![],
                }, CommandArgumentDefinition {
                    argument_id: "midplane".into(),
                    label: "Symmetric to plane".into(),
                    value_type: "boolean".into(),
                    required: true,
                    default_value: Some(selected_midplane.to_string()),
                    placeholder: None,
                    unit: None,
                    options: vec!["false".into(), "true".into()],
                }]),
            command_definition("partdesign.pocket", selected_is_sketch && selected_is_operable, vec![CommandArgumentDefinition {
                    argument_id: "depth_mm".into(),
                    label: "Pocket depth".into(),
                    value_type: "quantity".into(),
                    required: false,
                    default_value: Some("8.00".into()),
                    placeholder: Some("8.00".into()),
                    unit: Some("mm".into()),
                    options: vec![],
                }, CommandArgumentDefinition {
                    argument_id: "extent_mode".into(),
                    label: "Extent mode".into(),
                    value_type: "enum".into(),
                    required: true,
                    default_value: Some("dimension".into()),
                    placeholder: None,
                    unit: None,
                    options: vec!["dimension".into(), "through_all".into()],
                }]),
            command_definition("partdesign.edit_pad", selected_is_pad && selected_is_operable, vec![
                    CommandArgumentDefinition {
                        argument_id: "length_mm".into(),
                        label: "Pad length".into(),
                        value_type: "quantity".into(),
                        required: true,
                        default_value: Some(format!("{:.2}", selected_length_mm.unwrap_or(12.0))),
                        placeholder: Some("12.00".into()),
                        unit: Some("mm".into()),
                        options: vec![],
                    },
                    CommandArgumentDefinition {
                        argument_id: "midplane".into(),
                        label: "Symmetric to plane".into(),
                        value_type: "boolean".into(),
                        required: true,
                        default_value: Some(selected_midplane.to_string()),
                        placeholder: None,
                        unit: None,
                        options: vec!["false".into(), "true".into()],
                    },
                ]),
            command_definition("partdesign.edit_pocket", selected_is_pocket && selected_is_operable, vec![
                    CommandArgumentDefinition {
                        argument_id: "depth_mm".into(),
                        label: "Pocket depth".into(),
                        value_type: "quantity".into(),
                        required: true,
                        default_value: Some(format!("{:.2}", selected_length_mm.unwrap_or(8.0))),
                        placeholder: Some("8.00".into()),
                        unit: Some("mm".into()),
                        options: vec![],
                    },
                    CommandArgumentDefinition {
                        argument_id: "extent_mode".into(),
                        label: "Extent mode".into(),
                        value_type: "enum".into(),
                        required: true,
                        default_value: Some(selected_extent_mode.clone()),
                        placeholder: None,
                        unit: None,
                        options: vec!["dimension".into(), "through_all".into()],
                    },
                ]),
        ]);
    }

    commands.extend([
        command_definition("history.rollback_here", selected_is_feature, vec![]),
        command_definition("history.resume_full", history_marker_active, vec![]),
        command_definition("model.toggle_suppression", selected_is_feature, vec![]),
        command_definition("document.undo", can_undo, vec![]),
        command_definition("document.redo", can_redo, vec![]),
    ]);

    CommandCatalogResponse {
        document_id: document_id.to_string(),
        workbench: workbench_state_from_bridge(snapshot),
        commands,
    }
}

pub fn task_panel_from_bridge(
    snapshot: &BridgeDocumentSnapshot,
    document_id: &str,
    selected_object_id: Option<&str>,
    selected_length_mm: Option<f32>,
    can_undo: bool,
    can_redo: bool,
) -> TaskPanelResponse {
    let workbench_id = normalize_workbench_id(&snapshot.workbench);
    let selected_node = selected_object_id.and_then(|object_id| find_bridge_object(snapshot, object_id));
    let selected_state = selected_node.map(|node| bridge_object_state(snapshot, node));
    if workbench_id != "partdesign" {
        let mut suggested_commands = vec!["document.recompute".into(), "document.save".into()];
        if selected_object_id.is_some() {
            suggested_commands.insert(0, "selection.focus".into());
        }
        if snapshot.history_marker.is_some() {
            suggested_commands.push("history.resume_full".into());
        }
        if selected_object_id
            .and_then(|object_id| find_bridge_object(snapshot, object_id))
            .map(|node| node.object_id != "body-001")
            .unwrap_or(false)
        {
            suggested_commands.push("model.toggle_suppression".into());
        }
        if can_undo {
            suggested_commands.push("document.undo".into());
        }
        if can_redo {
            suggested_commands.push("document.redo".into());
        }

        let (title, description, sections) = match workbench_id.as_str() {
            "sketcher" => {
                let sketch_node = selected_node.filter(|node| node.object_type == "Sketcher::SketchObject");
                (
                    "Sketcher Workspace".into(),
                    sketch_node
                        .map(sketch_workflow_description)
                        .unwrap_or_else(|| {
                            "Sketcher owns the current shell context. Select a sketch to inspect constraints, profile readiness, and plane setup while deeper sketch editing services are being migrated.".into()
                        }),
                    vec![
                        TaskPanelSection {
                            section_id: "sketch_session".into(),
                            title: "Sketch Session".into(),
                            rows: vec![
                                TaskPanelRow {
                                    label: "Active object".into(),
                                    value: selected_node
                                        .map(|node| node.label.clone())
                                        .unwrap_or_else(|| "No sketch selected".into()),
                                    emphasis: true,
                                },
                                TaskPanelRow {
                                    label: "Reference plane".into(),
                                    value: sketch_node
                                        .and_then(|node| node.reference_plane.clone())
                                        .unwrap_or_else(|| "Select a sketch to inspect plane alignment".into()),
                                    emphasis: false,
                                },
                                TaskPanelRow {
                                    label: "Constraint state".into(),
                                    value: sketch_node
                                        .map(sketch_constraint_summary)
                                        .unwrap_or_else(|| "Constraint analysis pending selection".into()),
                                    emphasis: false,
                                },
                                TaskPanelRow {
                                    label: "Profile readiness".into(),
                                    value: sketch_node
                                        .map(sketch_profile_readiness)
                                        .unwrap_or_else(|| "Open a sketch to evaluate profile closure".into()),
                                    emphasis: true,
                                },
                            ],
                        },
                        TaskPanelSection {
                            section_id: "workspace".into(),
                            title: "Workspace".into(),
                            rows: vec![
                                TaskPanelRow {
                                    label: "Shell mode".into(),
                                    value: "Sketch inspection and selection parity".into(),
                                    emphasis: false,
                                },
                                TaskPanelRow {
                                    label: "History".into(),
                                    value: history_marker_label(snapshot),
                                    emphasis: false,
                                },
                                TaskPanelRow {
                                    label: "Next migration focus".into(),
                                    value: "Constraint editing and solver feedback".into(),
                                    emphasis: false,
                                },
                            ],
                        },
                    ],
                )
            }
            "part" => (
                "Part Workspace".into(),
                selected_node
                    .map(|node| {
                        format!(
                            "Part shell context is active. {} is selected while direct modeling commands are still being extracted from the Qt shell.",
                            node.label
                        )
                    })
                    .unwrap_or_else(|| {
                        "Part shell context is active. Use this workspace to inspect document structure, selection state, and viewport presence while direct modeling actions migrate out of Qt.".into()
                    }),
                vec![
                    TaskPanelSection {
                        section_id: "part_workspace".into(),
                        title: "Part Workspace".into(),
                        rows: vec![
                            TaskPanelRow {
                                label: "Active object".into(),
                                value: selected_node
                                    .map(|node| node.label.clone())
                                    .unwrap_or_else(|| "Body".into()),
                                emphasis: true,
                            },
                            TaskPanelRow {
                                label: "Object type".into(),
                                value: selected_node
                                    .map(|node| node.object_type.clone())
                                    .unwrap_or_else(|| "Part::Feature".into()),
                                emphasis: false,
                            },
                            TaskPanelRow {
                                label: "Viewport focus".into(),
                                value: if selected_object_id.is_some() {
                                    "Selection can be centered from the shell".into()
                                } else {
                                    "Pick an object to drive focus".into()
                                },
                                emphasis: false,
                            },
                        ],
                    },
                    TaskPanelSection {
                        section_id: "migration_status".into(),
                        title: "Migration Status".into(),
                        rows: vec![
                            TaskPanelRow {
                                label: "Shell state".into(),
                                value: "Backend-owned sessions, layout, and workbench chrome".into(),
                                emphasis: false,
                            },
                            TaskPanelRow {
                                label: "History".into(),
                                value: history_marker_label(snapshot),
                                emphasis: false,
                            },
                            TaskPanelRow {
                                label: "Next migration focus".into(),
                                value: "Direct solid operations and Boolean command extraction".into(),
                                emphasis: false,
                            },
                        ],
                    },
                ],
            ),
            _ => (
                format!("{} Workspace", workbench_display_name(&workbench_id)),
                format!(
                    "{} owns the active shell context. Modeling commands remain backend-authoritative while dedicated {} tools are still being migrated.",
                    workbench_display_name(&workbench_id),
                    workbench_display_name(&workbench_id)
                ),
                vec![
                    TaskPanelSection {
                        section_id: "workspace".into(),
                        title: "Workspace".into(),
                        rows: vec![
                            TaskPanelRow {
                                label: "Active workbench".into(),
                                value: workbench_display_name(&workbench_id),
                                emphasis: true,
                            },
                            TaskPanelRow {
                                label: "Selection mode".into(),
                                value: "object".into(),
                                emphasis: false,
                            },
                            TaskPanelRow {
                                label: "History".into(),
                                value: history_marker_label(snapshot),
                                emphasis: false,
                            },
                        ],
                    },
                    TaskPanelSection {
                        section_id: "selection".into(),
                        title: "Selection".into(),
                        rows: vec![
                            TaskPanelRow {
                                label: "Active object".into(),
                                value: selected_node
                                    .map(|node| node.label.clone())
                                    .unwrap_or_else(|| "Body".into()),
                                emphasis: true,
                            },
                            TaskPanelRow {
                                label: "Object type".into(),
                                value: selected_node
                                    .map(|node| node.object_type.clone())
                                    .unwrap_or_else(|| "PartDesign::Body".into()),
                                emphasis: false,
                            },
                            TaskPanelRow {
                                label: "Availability".into(),
                                value: selected_state
                                    .as_ref()
                                    .map(|state| {
                                        if state.suppressed {
                                            "Suppressed".into()
                                        } else if state.active {
                                            "Active".into()
                                        } else {
                                            state
                                                .inactive_reason
                                                .clone()
                                                .unwrap_or_else(|| "Inactive".into())
                                        }
                                    })
                                    .unwrap_or_else(|| "Active".into()),
                                emphasis: false,
                            },
                        ],
                    },
                ],
            ),
        };

        return TaskPanelResponse {
            document_id: document_id.to_string(),
            title,
            description,
            sections,
            suggested_commands,
        };
    }

    let (title, description, sections, mut suggested_commands): (
        String,
        String,
        Vec<TaskPanelSection>,
        Vec<String>,
    ) = match selected_object_id {
        Some(selected)
            if selected.starts_with("sketch-")
                && selected_state
                    .as_ref()
                    .map(|state| state.active && !state.suppressed)
                    .unwrap_or(false) =>
        (
            "Sketch Workflow".into(),
            selected_node
                .map(sketch_workflow_description)
                .unwrap_or_else(|| "Sketch state unavailable.".into()),
            vec![
                TaskPanelSection {
                    section_id: "selection".into(),
                    title: "Selection".into(),
                    rows: vec![
                        TaskPanelRow {
                            label: "Active object".into(),
                            value: selected.to_uppercase(),
                            emphasis: true,
                        },
                        TaskPanelRow {
                            label: "Expected next step".into(),
                            value: selected_node
                                .map(sketch_next_step)
                                .unwrap_or_else(|| "Inspect sketch readiness".into()),
                            emphasis: false,
                        },
                        TaskPanelRow {
                            label: "Reference plane".into(),
                            value: selected_node
                                .and_then(|node| node.reference_plane.clone())
                                .unwrap_or_else(|| "XY".into()),
                            emphasis: false,
                        },
                    ],
                },
                TaskPanelSection {
                    section_id: "constraints".into(),
                    title: "Constraints".into(),
                    rows: vec![
                        TaskPanelRow {
                            label: "Constraint state".into(),
                            value: selected_node
                                .map(sketch_constraint_summary)
                                .unwrap_or_else(|| "Unknown sketch state".into()),
                            emphasis: false,
                        },
                        TaskPanelRow {
                            label: "Profile readiness".into(),
                            value: selected_node
                                .map(sketch_profile_readiness)
                                .unwrap_or_else(|| "Profile status unavailable".into()),
                            emphasis: true,
                        },
                        TaskPanelRow {
                            label: "History".into(),
                            value: history_marker_label(snapshot),
                            emphasis: false,
                        },
                    ],
                },
            ],
            vec![
                "partdesign.pad".into(),
                "partdesign.pocket".into(),
                "history.rollback_here".into(),
                "model.toggle_suppression".into(),
                "document.recompute".into(),
            ],
        ),
        Some(selected)
            if selected.starts_with("pad-")
                && selected_state
                    .as_ref()
                    .map(|state| state.active && !state.suppressed)
                    .unwrap_or(false) =>
        (
            "Pad Feature".into(),
            selected_node
                .map(pad_workflow_description)
                .unwrap_or_else(|| "Pad state unavailable.".into()),
            vec![
                TaskPanelSection {
                    section_id: "feature".into(),
                    title: "Feature State".into(),
                    rows: vec![
                        TaskPanelRow {
                            label: "Active feature".into(),
                            value: selected.to_uppercase(),
                            emphasis: true,
                        },
                        TaskPanelRow {
                            label: "Length".into(),
                            value: format!("{:.2} mm", selected_length_mm.unwrap_or(12.0)),
                            emphasis: false,
                        },
                        TaskPanelRow {
                            label: "Symmetric".into(),
                            value: if selected_node.map(|node| node.midplane).unwrap_or(false) {
                                "Enabled".into()
                            } else {
                                "Disabled".into()
                            },
                            emphasis: false,
                        },
                    ],
                },
                TaskPanelSection {
                    section_id: "actions".into(),
                    title: "Suggested Checks".into(),
                    rows: vec![
                        TaskPanelRow {
                            label: "Regeneration".into(),
                            value: "Recompute after edits".into(),
                            emphasis: false,
                        },
                        TaskPanelRow {
                            label: "View".into(),
                            value: selected_node
                                .map(pad_inspection_hint)
                                .unwrap_or_else(|| "Inspect current feature".into()),
                            emphasis: false,
                        },
                        TaskPanelRow {
                            label: "History".into(),
                            value: history_marker_label(snapshot),
                            emphasis: false,
                        },
                    ],
                },
            ],
            vec![
                "partdesign.edit_pad".into(),
                "history.rollback_here".into(),
                "model.toggle_suppression".into(),
                "document.recompute".into(),
                "selection.focus".into(),
                "document.save".into(),
            ],
        ),
        Some(selected)
            if selected.starts_with("pocket-")
                && selected_state
                    .as_ref()
                    .map(|state| state.active && !state.suppressed)
                    .unwrap_or(false) =>
        (
            "Pocket Feature".into(),
            selected_node
                .map(pocket_workflow_description)
                .unwrap_or_else(|| "Pocket state unavailable.".into()),
            vec![
                TaskPanelSection {
                    section_id: "feature".into(),
                    title: "Feature State".into(),
                    rows: vec![
                        TaskPanelRow {
                            label: "Active feature".into(),
                            value: selected.to_uppercase(),
                            emphasis: true,
                        },
                        TaskPanelRow {
                            label: "Depth".into(),
                            value: format!("{:.2} mm", selected_length_mm.unwrap_or(8.0)),
                            emphasis: false,
                        },
                        TaskPanelRow {
                            label: "Extent".into(),
                            value: selected_node
                                .and_then(|node| node.extent_mode.clone())
                                .unwrap_or_else(|| "dimension".into()),
                            emphasis: false,
                        },
                    ],
                },
                TaskPanelSection {
                    section_id: "actions".into(),
                    title: "Suggested Checks".into(),
                    rows: vec![
                        TaskPanelRow {
                            label: "Regeneration".into(),
                            value: "Recompute after cut-depth edits".into(),
                            emphasis: false,
                        },
                        TaskPanelRow {
                            label: "View".into(),
                            value: selected_node
                                .map(pocket_inspection_hint)
                                .unwrap_or_else(|| "Inspect the subtractive region".into()),
                            emphasis: false,
                        },
                        TaskPanelRow {
                            label: "History".into(),
                            value: history_marker_label(snapshot),
                            emphasis: false,
                        },
                    ],
                },
            ],
            vec![
                "partdesign.edit_pocket".into(),
                "history.rollback_here".into(),
                "model.toggle_suppression".into(),
                "document.recompute".into(),
                "selection.focus".into(),
                "document.save".into(),
            ],
        ),
        Some(selected) => {
            let state = selected_state
                .clone()
                .unwrap_or(FeatureDependencyState {
                    active: false,
                    suppressed: false,
                    inactive_reason: Some("Selected object is not available in the dependency graph.".into()),
                });
            let selected_label = selected_node
                .map(|node| node.label.clone())
                .unwrap_or_else(|| selected.to_uppercase());
            let selected_bridge_node = selected_node.cloned().unwrap_or(asterforge_freecad_bridge::BridgeObjectNode {
                object_id: selected.to_string(),
                label: selected_label.clone(),
                object_type: "App::FeaturePython".into(),
                visibility: "visible".into(),
                length_mm: None,
                constraint_count: None,
                profile_closed: None,
                fully_constrained: None,
                reference_plane: None,
                extent_mode: None,
                midplane: false,
                source_object_id: None,
                sequence_index: None,
                suppressed: state.suppressed,
                children: vec![],
            });

            (
                "Dependency State".into(),
                dependency_workflow_description(
                    &selected_bridge_node,
                    state.inactive_reason.as_deref(),
                ),
                vec![
                    TaskPanelSection {
                        section_id: "dependency".into(),
                        title: "Dependency Status".into(),
                        rows: vec![
                            TaskPanelRow {
                                label: "Selected object".into(),
                                value: selected_label,
                                emphasis: true,
                            },
                            TaskPanelRow {
                                label: "State".into(),
                                value: dependency_status_label(&selected_bridge_node),
                                emphasis: true,
                            },
                              TaskPanelRow {
                                label: "Reason".into(),
                                value: dependency_issue_hint(
                                    &selected_bridge_node,
                                    state.inactive_reason.as_deref(),
                                ),
                                emphasis: false,
                              },
                              TaskPanelRow {
                                label: "History".into(),
                                value: history_marker_label(snapshot),
                                emphasis: false,
                              },
                          ],
                      },
                  ],
                vec![
                    "history.rollback_here".into(),
                    "history.resume_full".into(),
                    "model.toggle_suppression".into(),
                    "document.recompute".into(),
                ],
              )
          }
        _ => (
            "Body Overview".into(),
            body_workflow_description(snapshot),
            vec![
                TaskPanelSection {
                    section_id: "body".into(),
                    title: "Body Status".into(),
                    rows: vec![
                        TaskPanelRow {
                            label: "Contained features".into(),
                            value: body_feature_summary(snapshot),
                            emphasis: false,
                        },
                        TaskPanelRow {
                            label: "Recommended next action".into(),
                            value: body_next_step(snapshot),
                            emphasis: true,
                        },
                        TaskPanelRow {
                            label: "History".into(),
                            value: history_marker_label(snapshot),
                            emphasis: false,
                        },
                    ],
                },
            ],
            vec![
                "partdesign.new_sketch".into(),
                "history.resume_full".into(),
                "document.recompute".into(),
                "document.save".into(),
            ],
        ),
    };

    if can_undo {
        suggested_commands.push("document.undo".into());
    }
    if can_redo {
        suggested_commands.push("document.redo".into());
    }

    TaskPanelResponse {
        document_id: document_id.to_string(),
        title,
        description,
        sections,
        suggested_commands,
    }
}

pub fn sample_bridge_status() -> BridgeStatus {
    bridge_status()
}

#[allow(dead_code)]
pub fn sample_document_summary() -> DocumentSummary {
    let snapshot = open_document_snapshot(None);
    document_summary_from_bridge(&snapshot)
}

#[allow(dead_code)]
pub fn sample_object_tree() -> Vec<ObjectNode> {
    let snapshot = open_document_snapshot(None);
    snapshot
        .roots
        .iter()
        .map(object_node_from_bridge)
        .collect()
}

#[allow(dead_code)]
pub fn sample_viewport(selected_object_id: &str) -> ViewportResponse {
    let snapshot = open_document_snapshot(None);
    viewport_from_bridge(&snapshot, selected_object_id)
}

pub fn document_summary_from_bridge(snapshot: &BridgeDocumentSnapshot) -> DocumentSummary {
    DocumentSummary {
        document_id: snapshot.document_id.clone(),
        display_name: snapshot.display_name.clone(),
        workbench: snapshot.workbench.clone(),
        file_path: snapshot.file_path.clone(),
        dirty: snapshot.dirty,
    }
}

pub fn object_tree_from_bridge(snapshot: &BridgeDocumentSnapshot) -> Vec<ObjectNode> {
    snapshot
        .roots
        .iter()
        .map(object_node_from_bridge)
        .collect()
}

pub fn viewport_from_bridge(
    snapshot: &BridgeDocumentSnapshot,
    selected_object_id: &str,
) -> ViewportResponse {
    ViewportResponse {
        document_id: snapshot.document_id.clone(),
        selected_object_id: selected_object_id.to_string(),
        scene: viewport_scene_from_bridge(&snapshot.viewport),
    }
}

pub fn viewport_diff_response(
    document_id: &str,
    selected_object_id: &str,
    diff: ViewportDiff,
) -> ViewportDiffResponse {
    ViewportDiffResponse {
        document_id: document_id.to_string(),
        selected_object_id: selected_object_id.to_string(),
        added: diff.added.iter().map(viewport_drawable_from_bridge).collect(),
        removed: diff.removed,
        modified: diff.modified.iter().map(viewport_drawable_from_bridge).collect(),
        camera_changed: diff.camera_changed,
        camera_eye: diff.camera.as_ref().map(|c| c.eye),
        camera_target: diff.camera.as_ref().map(|c| c.target),
    }
}

fn viewport_scene_from_bridge(snapshot: &ViewportSnapshot) -> ViewportScene {
    ViewportScene {
        camera_eye: snapshot.camera.eye,
        camera_target: snapshot.camera.target,
        drawables: snapshot
            .drawables
            .iter()
            .map(viewport_drawable_from_bridge)
            .collect(),
    }
}

fn viewport_drawable_from_bridge(drawable: &DrawableMesh) -> ViewportDrawable {
    ViewportDrawable {
        object_id: drawable.object_id.clone(),
        label: drawable.label.clone(),
        kind: drawable.kind.clone(),
        accent: drawable.accent.clone(),
        bounds: ViewportBounds {
            x: drawable.bounds.x,
            y: drawable.bounds.y,
            width: drawable.bounds.width,
            height: drawable.bounds.height,
        },
        paths: drawable
            .edges
            .iter()
            .map(|polyline| {
                polyline
                    .points
                    .iter()
                    .enumerate()
                    .map(|(index, point)| {
                        if index == 0 {
                            format!("M {} {}", point.x, point.y)
                        } else {
                            format!("L {} {}", point.x, point.y)
                        }
                    })
                    .collect::<Vec<_>>()
                    .join(" ")
            })
            .collect(),
    }
}

fn object_node_from_bridge(node: &asterforge_freecad_bridge::BridgeObjectNode) -> ObjectNode {
    ObjectNode {
        object_id: node.object_id.clone(),
        label: node.label.clone(),
        object_type: node.object_type.clone(),
        visibility: match node.visibility.as_str() {
            "hidden" => VisibilityState::Hidden,
            "inherited" => VisibilityState::Inherited,
            _ => VisibilityState::Visible,
        },
        children: node.children.iter().map(object_node_from_bridge).collect(),
    }
}

pub fn find_pad_length_mm(
    snapshot: &BridgeDocumentSnapshot,
    object_id: &str,
) -> Option<f32> {
    snapshot
        .roots
        .iter()
        .flat_map(|root| root.children.iter())
        .find(|child| child.object_id == object_id)
        .and_then(|child| child.length_mm)
}

pub fn find_bridge_child<'a>(
    snapshot: &'a BridgeDocumentSnapshot,
    object_id: &str,
) -> Option<&'a asterforge_freecad_bridge::BridgeObjectNode> {
    snapshot
        .roots
        .iter()
        .flat_map(|root| root.children.iter())
        .find(|child| child.object_id == object_id)
}

pub fn sketch_constraint_summary(node: &asterforge_freecad_bridge::BridgeObjectNode) -> String {
    let count = node.constraint_count.unwrap_or(0);
    if node.fully_constrained.unwrap_or(false) {
        format!("{} constraints resolved", count)
    } else {
        format!("{} constraints, solver pending", count)
    }
}

pub fn sketch_profile_readiness(node: &asterforge_freecad_bridge::BridgeObjectNode) -> String {
    match (node.profile_closed, node.fully_constrained) {
        (Some(true), Some(true)) => "Closed profile / fully constrained".into(),
        (Some(true), _) => "Closed profile".into(),
        (Some(false), _) => "Open profile".into(),
        _ => "Profile status unavailable".into(),
    }
}

pub fn feature_history_from_bridge(snapshot: &BridgeDocumentSnapshot) -> FeatureHistoryResponse {
    let mut entries = snapshot
        .roots
        .iter()
        .flat_map(|root| root.children.iter())
        .map(|child| {
            let state = bridge_object_state(snapshot, child);
            FeatureHistoryEntry {
                object_id: child.object_id.clone(),
                label: child.label.clone(),
                object_type: child.object_type.clone(),
                sequence_index: child.sequence_index.unwrap_or(0),
                source_object_id: child.source_object_id.clone(),
                role: match child.object_type.as_str() {
                    "Sketcher::SketchObject" => "sketch".into(),
                    "PartDesign::Pad" => "additive".into(),
                    "PartDesign::Pocket" => "subtractive".into(),
                    _ => "support".into(),
                },
                suppressed: child.suppressed,
                active: state.active,
                inactive_reason: state.inactive_reason,
                rolled_back: snapshot
                    .history_marker
                    .map(|marker| child.sequence_index.unwrap_or(0) > marker)
                    .unwrap_or(false),
            }
        })
        .collect::<Vec<_>>();

    entries.sort_by_key(|entry| entry.sequence_index);
    FeatureHistoryResponse {
        document_id: snapshot.document_id.clone(),
        entries,
    }
}

pub fn document_evaluation_state_from_bridge(
    snapshot: &BridgeDocumentSnapshot,
    worker_mode: &str,
) -> DocumentEvaluationState {
    let history = feature_history_from_bridge(snapshot);
    DocumentEvaluationState::from_feature_history(
        &history,
        snapshot.history_marker.is_some(),
        worker_mode,
    )
}

pub fn document_graph_from_bridge(snapshot: &BridgeDocumentSnapshot) -> DocumentGraph {
    let mut graph = DocumentGraph::default();

    for root in &snapshot.roots {
        collect_document_graph_node(&mut graph, root, None);
    }

    graph
}

fn collect_document_graph_node(
    graph: &mut DocumentGraph,
    node: &asterforge_freecad_bridge::BridgeObjectNode,
    parent_object_id: Option<&str>,
) {
    graph.objects.push(DocumentObjectRecord {
        object_id: node.object_id.clone(),
        object_type: node.object_type.clone(),
        label: node.label.clone(),
        parent_object_id: parent_object_id.map(str::to_string),
        source_object_id: node.source_object_id.clone(),
    });

    if let Some(parent_object_id) = parent_object_id {
        graph.dependencies.push(DocumentDependencyEdge {
            from_object_id: parent_object_id.to_string(),
            to_object_id: node.object_id.clone(),
            relationship: "contains".into(),
        });
    }

    if let Some(source_object_id) = node.source_object_id.as_ref() {
        graph.dependencies.push(DocumentDependencyEdge {
            from_object_id: source_object_id.clone(),
            to_object_id: node.object_id.clone(),
            relationship: "depends_on".into(),
        });
    }

    for child in &node.children {
        collect_document_graph_node(graph, child, Some(&node.object_id));
    }
}

pub fn diagnostics_from_bridge(
    snapshot: &BridgeDocumentSnapshot,
    selected_object_id: Option<&str>,
    events: &[BackendEvent],
    bridge_status: &BridgeStatus,
) -> DiagnosticsResponse {
    let history = feature_history_from_bridge(snapshot);
    let selected_node = selected_object_id.and_then(|object_id| find_bridge_object(snapshot, object_id));
    let selected_entry = selected_object_id.and_then(|object_id| {
        history
            .entries
            .iter()
            .find(|entry| entry.object_id == object_id)
    });

    DiagnosticsResponse {
        document_id: snapshot.document_id.clone(),
        summary: DiagnosticsSummary {
            total_features: history.entries.len() as u32,
            suppressed_count: history.entries.iter().filter(|entry| entry.suppressed).count() as u32,
            inactive_count: history
                .entries
                .iter()
                .filter(|entry| !entry.active && !entry.suppressed)
                .count() as u32,
            rolled_back_count: history.entries.iter().filter(|entry| entry.rolled_back).count() as u32,
            viewport_drawable_count: snapshot.viewport.drawables.len() as u32,
            warning_count: events.iter().filter(|event| event.level == "warning").count() as u32,
            error_count: events.iter().filter(|event| event.level == "error").count() as u32,
            history_marker_active: snapshot.history_marker.is_some(),
            worker_mode: bridge_status.worker_mode.clone(),
        },
        selection: DiagnosticsSelection {
            object_id: selected_object_id.map(ToOwned::to_owned),
            object_label: selected_node.map(|node| node.label.clone()),
            object_type: selected_node.map(|node| node.object_type.clone()),
            model_state: selected_entry
                .map(|entry| {
                    if entry.suppressed {
                        "suppressed".into()
                    } else if entry.rolled_back {
                        "rolled_back".into()
                    } else if entry.active {
                        "active".into()
                    } else {
                        "inactive".into()
                    }
                })
                .unwrap_or_else(|| "context".into()),
            dependency_note: selected_entry
                .and_then(|entry| entry.inactive_reason.clone())
                .unwrap_or_else(|| "Resolved".into()),
            visible_in_viewport: selected_object_id
                .map(|object_id| {
                    snapshot
                        .viewport
                        .drawables
                        .iter()
                        .any(|drawable| drawable.object_id == object_id)
                })
                .unwrap_or(false),
        },
        recent_signals: events
            .iter()
            .take(4)
            .map(|event| DiagnosticSignal {
                level: event.level.clone(),
                title: event.topic.replace('_', " "),
                detail: event.message.clone(),
            })
            .collect(),
    }
}

pub fn selection_state_from_bridge(
    snapshot: &BridgeDocumentSnapshot,
    selected_object_id: &str,
    current_mode: &str,
) -> SelectionStateResponse {
    let selected_node = find_bridge_object(snapshot, selected_object_id)
        .or_else(|| snapshot.roots.first())
        .expect("bridge snapshot should always include at least one root object");

    let selectable_modes = [
        (
            "object",
            "Object",
            "Select any backend-published object in the document tree.",
        ),
        (
            "body",
            "Bodies",
            "Focus body containers when driving high-level PartDesign workflow steps.",
        ),
        (
            "sketch",
            "Sketches",
            "Jump between sketch definitions and profile-authoring states.",
        ),
        (
            "feature",
            "Features",
            "Select downstream PartDesign features such as pads and pockets.",
        ),
    ];

    SelectionStateResponse {
        document_id: snapshot.document_id.clone(),
        current_mode: current_mode.to_string(),
        selected_object_id: selected_node.object_id.clone(),
        selected_object_label: selected_node.label.clone(),
        selected_object_type: selected_node.object_type.clone(),
        available_modes: selectable_modes
            .into_iter()
            .map(|(mode_id, label, description)| {
                let object_count = selectable_object_ids_for_mode(snapshot, mode_id).len() as u32;
                SelectionModeOption {
                    mode_id: mode_id.to_string(),
                    label: label.to_string(),
                    description: description.to_string(),
                    enabled: object_count > 0,
                    object_count,
                }
            })
            .collect(),
    }
}

pub fn preselection_state_from_bridge(
    snapshot: &BridgeDocumentSnapshot,
    preselected_object_id: Option<&str>,
    current_mode: &str,
    can_undo: bool,
    can_redo: bool,
) -> PreselectionStateResponse {
    let preselected_node =
        preselected_object_id.and_then(|object_id| find_bridge_object(snapshot, object_id));
    let selectable = preselected_node
        .map(|node| object_matches_selection_mode(node.object_type.as_str(), current_mode))
        .unwrap_or(false);
    let preselected_state = preselected_node.map(|node| bridge_object_state(snapshot, node));
    let suggested_commands = preselected_object_id
        .filter(|_| selectable)
        .map(|object_id| {
            task_panel_from_bridge(
                snapshot,
                &snapshot.document_id,
                Some(object_id),
                find_pad_length_mm(snapshot, object_id),
                can_undo,
                can_redo,
            )
            .suggested_commands
        })
        .unwrap_or_default();

    PreselectionStateResponse {
        document_id: snapshot.document_id.clone(),
        current_mode: current_mode.to_string(),
        object_id: preselected_node.map(|node| node.object_id.clone()),
        object_label: preselected_node.map(|node| node.label.clone()),
        object_type: preselected_node.map(|node| node.object_type.clone()),
        selectable,
        model_state: match preselected_state.as_ref() {
            Some(state) if state.suppressed => "suppressed".into(),
            Some(state) if state.active => "active".into(),
            Some(_) => "inactive".into(),
            None => "none".into(),
        },
        dependency_note: preselected_state
            .and_then(|state| state.inactive_reason)
            .unwrap_or_else(|| "Resolved".into()),
        suggested_commands,
        detail: match preselected_node {
            Some(node) if selectable => {
                format!("Preselection candidate {} is valid for {} mode.", node.label, current_mode)
            }
            Some(node) => format!(
                "Candidate {} is filtered out by the active {} mode.",
                node.label, current_mode
            ),
            None => "No preselection candidate is currently active.".into(),
        },
    }
}

#[derive(Debug, Clone)]
pub struct FeatureDependencyState {
    pub active: bool,
    pub suppressed: bool,
    pub inactive_reason: Option<String>,
}

pub fn bridge_object_state(
    snapshot: &BridgeDocumentSnapshot,
    node: &asterforge_freecad_bridge::BridgeObjectNode,
) -> FeatureDependencyState {
    if snapshot
        .history_marker
        .map(|marker| node.sequence_index.unwrap_or(0) > marker)
        .unwrap_or(false)
    {
        return FeatureDependencyState {
            active: false,
            suppressed: false,
            inactive_reason: Some(format!(
                "Inactive because the history marker is set before step {}.",
                node.sequence_index.unwrap_or(0)
            )),
        };
    }

    if node.suppressed {
        return FeatureDependencyState {
            active: false,
            suppressed: true,
            inactive_reason: Some("Feature is manually suppressed.".into()),
        };
    }

    let Some(source_object_id) = node.source_object_id.as_deref() else {
        return FeatureDependencyState {
            active: true,
            suppressed: false,
            inactive_reason: None,
        };
    };

    let Some(source_node) = find_bridge_object(snapshot, source_object_id) else {
        return FeatureDependencyState {
            active: false,
            suppressed: false,
            inactive_reason: Some(format!("Source object {} is missing.", source_object_id)),
        };
    };

    let source_state = bridge_object_state(snapshot, source_node);
    if source_state.suppressed {
        FeatureDependencyState {
            active: false,
            suppressed: false,
            inactive_reason: Some(format!("Blocked by suppressed source {}", source_object_id)),
        }
    } else if !source_state.active {
        FeatureDependencyState {
            active: false,
            suppressed: false,
            inactive_reason: source_state.inactive_reason,
        }
    } else {
        FeatureDependencyState {
            active: true,
            suppressed: false,
            inactive_reason: None,
        }
    }
}

fn history_marker_label(snapshot: &BridgeDocumentSnapshot) -> String {
    snapshot
        .history_marker
        .map(|marker| format!("Rolled back to step {}", marker))
        .unwrap_or_else(|| "Full history active".into())
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

#[cfg(test)]
mod tests {
    use asterforge_freecad_bridge::open_document_snapshot;

    use super::document_graph_from_bridge;

    #[test]
    fn projects_bridge_snapshot_into_document_graph() {
        let snapshot = open_document_snapshot(None);
        let graph = document_graph_from_bridge(&snapshot);

        assert!(graph.objects.iter().any(|object| object.object_id == "body-001"));
        assert!(graph.objects.iter().any(|object| object.object_id == "sketch-001"));
        assert!(graph.objects.iter().any(|object| object.object_id == "pad-001"));
        assert!(graph.dependencies.iter().any(|edge| {
            edge.from_object_id == "body-001"
                && edge.to_object_id == "sketch-001"
                && edge.relationship == "contains"
        }));
        assert!(graph.dependencies.iter().any(|edge| {
            edge.from_object_id == "sketch-001"
                && edge.to_object_id == "pad-001"
                && edge.relationship == "depends_on"
        }));
    }
}

pub fn selectable_object_ids_for_mode(
    snapshot: &BridgeDocumentSnapshot,
    selection_mode: &str,
) -> Vec<String> {
    snapshot
        .roots
        .iter()
        .flat_map(|root| std::iter::once(root).chain(root.children.iter()))
        .filter(|node| object_matches_selection_mode(node.object_type.as_str(), selection_mode))
        .map(|node| node.object_id.clone())
        .collect()
}

pub fn object_matches_selection_mode(object_type: &str, selection_mode: &str) -> bool {
    match selection_mode {
        "object" => true,
        "body" => object_type == "PartDesign::Body",
        "sketch" => object_type == "Sketcher::SketchObject",
        "feature" => matches!(object_type, "PartDesign::Pad" | "PartDesign::Pocket"),
        _ => false,
    }
}

pub fn sample_property_groups() -> Vec<PropertyGroup> {
    vec![
        PropertyGroup {
            group_id: "base".into(),
            title: "Base".into(),
            properties: vec![
                PropertyMetadata {
                    property_id: "label".into(),
                    display_name: "Label".into(),
                    property_type: "App::PropertyString".into(),
                    value_kind: "string".into(),
                    read_only: false,
                    unit: None,
                    expression_capable: false,
                    value_preview: "Pad".into(),
                },
                PropertyMetadata {
                    property_id: "visibility".into(),
                    display_name: "Visibility".into(),
                    property_type: "App::PropertyBool".into(),
                    value_kind: "boolean".into(),
                    read_only: false,
                    unit: None,
                    expression_capable: false,
                    value_preview: "true".into(),
                },
            ],
        },
        PropertyGroup {
            group_id: "constraints".into(),
            title: "Constraints".into(),
            properties: vec![PropertyMetadata {
                property_id: "length".into(),
                display_name: "Length".into(),
                property_type: "App::PropertyLength".into(),
                value_kind: "quantity".into(),
                read_only: false,
                unit: Some("mm".into()),
                expression_capable: true,
                value_preview: "12.00 mm".into(),
            }],
        },
    ]
}

pub fn sample_event_stream() -> Vec<BackendEvent> {
    vec![
        BackendEvent {
            topic: "document_changed".into(),
            level: "info".into(),
            message: "Document doc-demo-001 opened".into(),
            document_id: "doc-demo-001".into(),
            object_id: None,
        },
        BackendEvent {
            topic: "selection_changed".into(),
            level: "info".into(),
            message: "Selected pad-001".into(),
            document_id: "doc-demo-001".into(),
            object_id: Some("pad-001".into()),
        },
        BackendEvent {
            topic: "worker_lifecycle".into(),
            level: "warning".into(),
            message: "Native bridge running in mock mode".into(),
            document_id: "doc-demo-001".into(),
            object_id: None,
        },
    ]
}
