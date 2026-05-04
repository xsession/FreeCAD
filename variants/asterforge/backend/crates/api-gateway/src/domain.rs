mod bridge_views;
mod shell_views;
mod step_views;
mod viewport_views;

use asterforge_freecad_bridge::{
    bridge_status, open_document_snapshot, BridgeDocumentSnapshot, BridgeStatus,
};
use asterforge_command_core::command_definition as shared_command_definition;
pub use asterforge_command_core::{CommandArgumentDefinition, CommandDefinition};
pub use asterforge_document_core::{
    bridge_object_state, document_graph_from_bridge,
    document_summary_from_bridge, feature_history_from_bridge, find_pad_length_mm,
    object_matches_selection_mode, selectable_object_ids_for_mode, DocumentSummary,
    FeatureDependencyState, FeatureHistoryEntry, FeatureHistoryResponse, RecentDocumentEntry,
    WorkspaceSessionEntry,
};
use serde::{Deserialize, Serialize};

pub use bridge_views::{
    command_catalog_from_bridge, diagnostics_from_bridge, preselection_state_from_bridge,
    selection_state_from_bridge, task_panel_from_bridge,
};
pub use shell_views::{
    extension_compatibility_state, shell_snapshot_from_bridge, step_shell_snapshot,
};
pub use step_views::{step_document_index_from_parsed, step_scene_bundle_from_parsed};
pub use viewport_views::{
    object_tree_from_bridge, viewport_diff_response, viewport_from_bridge,
};

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

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
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
pub struct StepByteRange {
    pub start: usize,
    pub end: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StepHeaderSection {
    pub source_path: Option<String>,
    pub implementation_level: Option<String>,
    pub file_name: Option<String>,
    pub file_descriptions: Vec<String>,
    pub schema_identifiers: Vec<String>,
    pub application_protocols: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StepEntitySpan {
    pub entity_id: u64,
    pub keyword: String,
    pub byte_range: StepByteRange,
    pub references: Vec<u64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StepChunkSummary {
    pub chunk_id: usize,
    pub byte_range: StepByteRange,
    pub entity_ids: Vec<u64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StepPmiAnnotation {
    pub annotation_id: String,
    pub semantic_type: String,
    pub text: String,
    pub target_entity_ids: Vec<u64>,
    pub presentation_entity_ids: Vec<u64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StepTessellatedFaceSet {
    pub representation_id: String,
    pub entity_id: u64,
    pub positions: Vec<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub normals: Option<Vec<f32>>,
    pub indices: Vec<u32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StepAssemblyNode {
    pub entity_id: u64,
    pub label: String,
    pub children: Vec<StepAssemblyNode>,
    pub brep_ids: Vec<u64>,
    pub tessellated_representation_ids: Vec<String>,
    pub pmi_annotation_ids: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StepDocumentIndex {
    pub header: StepHeaderSection,
    pub chunks: Vec<StepChunkSummary>,
    pub entities: Vec<StepEntitySpan>,
    pub assemblies: Vec<StepAssemblyNode>,
    pub semantic_pmi: Vec<StepPmiAnnotation>,
    pub tessellated_representations: Vec<StepTessellatedFaceSet>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StepSceneBundle {
    pub assemblies: Vec<StepAssemblyNode>,
    pub semantic_pmi: Vec<StepPmiAnnotation>,
    pub tessellated_representations: Vec<StepTessellatedFaceSet>,
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
    pub category: String,
    pub migration_lane: String,
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
pub struct ShellSnapshot {
    pub document: DocumentSummary,
    pub workbench_catalog: WorkbenchCatalog,
    pub menu_bar: MenuBarState,
    pub toolbar_bands: ToolbarBandState,
    pub layout: ShellLayoutState,
    pub recent_documents: Vec<RecentDocumentEntry>,
    pub workspace_sessions: Vec<WorkspaceSessionEntry>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub inspection: Option<ShellInspectionState>,
    pub extension_compatibility: ExtensionCompatibilityState,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub status_bar: Option<ShellStatusBarState>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ShellStatusBarState {
    pub items: Vec<ShellStatusBarItem>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ShellStatusBarItem {
    pub item_id: String,
    pub label: String,
    pub value: String,
    pub tone: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ShellInspectionState {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub step_pmi: Option<StepPmiInspectionOverlay>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub step_measurement: Option<StepMeasurementOverlay>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExtensionCompatibilityState {
    pub title: String,
    pub summary: String,
    pub lanes: Vec<ExtensionCompatibilityLane>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExtensionCompatibilityLane {
    pub lane_id: String,
    pub label: String,
    pub status: String,
    pub owner: String,
    pub summary: String,
    pub next_steps: Vec<String>,
    pub command_ids: Vec<String>,
    pub inventory_entries: Vec<ExtensionInventoryEntry>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExtensionInventoryEntry {
    pub entry_id: String,
    pub label: String,
    pub origin: String,
    pub trust_state: String,
    pub compatibility: String,
    pub detail: String,
    pub action_command_id: Option<String>,
    pub action_label: Option<String>,
    pub last_run_status: Option<String>,
    pub last_run_level: Option<String>,
    pub last_run_detail: Option<String>,
    pub last_run_kind: Option<String>,
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
pub struct StepPmiInspectionOverlay {
    pub object_id: String,
    pub label: String,
    pub entity_id: u64,
    pub target_object_ids: Vec<String>,
    pub presentation_object_ids: Vec<String>,
    pub annotation_lines: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StepMeasurementOverlay {
    pub object_id: String,
    pub label: String,
    pub span_x: f32,
    pub span_y: f32,
    pub span_z: f32,
    pub representation_count: usize,
    pub annotation_count: usize,
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
        "step" => "STEP Inspection".into(),
        "start" => "Start".into(),
        "partdesign" => "PartDesign".into(),
        "part" => "Part".into(),
        "sketcher" => "Sketcher".into(),
        "assembly" => "Assembly".into(),
        "draft" => "Draft".into(),
        "techdraw" => "TechDraw".into(),
        "bim" => "BIM".into(),
        "cam" => "CAM".into(),
        "fem" => "FEM".into(),
        "spreadsheet" => "Spreadsheet".into(),
        "material" => "Material".into(),
        "import" => "Import".into(),
        "mesh" => "Mesh".into(),
        "surface" => "Surface".into(),
        "reverseengineering" => "ReverseEngineering".into(),
        "robot" => "Robot".into(),
        _ if value.is_empty() => "PartDesign".into(),
        _ => value.to_string(),
    }
}

fn command_definition(
    command_id: &str,
    enabled: bool,
    arguments: Vec<CommandArgumentDefinition>,
) -> CommandDefinition {
    shared_command_definition(command_id, enabled, arguments)
        .unwrap_or_else(|| panic!("missing command spec for {command_id}"))
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
    viewport_views::sample_object_tree()
}

#[allow(dead_code)]
pub fn sample_viewport(selected_object_id: &str) -> ViewportResponse {
    viewport_views::sample_viewport(selected_object_id)
}

fn history_marker_label(snapshot: &BridgeDocumentSnapshot) -> String {
    snapshot
        .history_marker
        .map(|marker| format!("Rolled back to step {}", marker))
        .unwrap_or_else(|| "Full history active".into())
}

#[cfg(test)]
mod tests {
    use asterforge_freecad_bridge::open_document_snapshot;

    use super::document_graph_from_bridge;
    use super::shell_views::{step_workbench_catalog, workbench_catalog_from_bridge};

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

    #[test]
    fn workbench_catalog_exposes_full_family_metadata() {
        let snapshot = open_document_snapshot(None);
        let catalog = workbench_catalog_from_bridge(&snapshot);

        let assembly = catalog
            .workbenches
            .iter()
            .find(|entry| entry.workbench_id == "assembly")
            .expect("assembly catalog entry should exist");
        assert_eq!(assembly.category, "Mechanical assembly");
        assert_eq!(assembly.migration_lane, "Queued primary");
        assert!(!assembly.enabled);

        let part_design = catalog
            .workbenches
            .iter()
            .find(|entry| entry.workbench_id == "partdesign")
            .expect("partdesign catalog entry should exist");
        assert_eq!(part_design.category, "Core modeling");
        assert_eq!(part_design.migration_lane, "Queued primary");
        assert!(part_design.enabled);
    }

    #[test]
    fn step_workbench_catalog_keeps_step_active_and_tracks_other_families() {
        let catalog = step_workbench_catalog();
        assert_eq!(catalog.active_workbench_id, "step");

        let step = catalog
            .workbenches
            .iter()
            .find(|entry| entry.workbench_id == "step")
            .expect("step catalog entry should exist");
        assert_eq!(step.category, "Inspection");
        assert_eq!(step.migration_lane, "In progress");
        assert!(step.enabled);

        assert!(catalog
            .workbenches
            .iter()
            .any(|entry| entry.workbench_id == "cam" && entry.category == "Manufacturing"));
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
