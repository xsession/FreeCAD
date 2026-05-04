use asterforge_document_core::DocumentSummary;
use asterforge_freecad_bridge::BridgeStatus;

use crate::domain::{
    BackendEvent, BootReport, CommandCatalogResponse, DiagnosticsResponse,
    FeatureHistoryResponse, JobStatusResponse, ObjectNode, PreselectionStateResponse,
    PropertyResponse, SelectionStateResponse, ShellSnapshot, TaskPanelResponse,
    ViewportResponse,
};

#[derive(Debug, Clone, serde::Serialize)]
pub struct AppSnapshot {
    pub boot_report: BootReport,
    pub document: DocumentSummary,
    pub object_tree: Vec<ObjectNode>,
    pub events: Vec<BackendEvent>,
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct BootPayload {
    pub boot_report: BootReport,
    pub bridge_status: BridgeStatus,
    pub document: DocumentSummary,
    pub shell_snapshot: ShellSnapshot,
    pub object_tree: Vec<ObjectNode>,
    pub selected_object_id: String,
    pub selection_state: SelectionStateResponse,
    pub preselection_state: PreselectionStateResponse,
    pub jobs: JobStatusResponse,
    pub properties: PropertyResponse,
    pub viewport: ViewportResponse,
    pub feature_history: FeatureHistoryResponse,
    pub command_catalog: CommandCatalogResponse,
    pub task_panel: TaskPanelResponse,
    pub diagnostics: DiagnosticsResponse,
    pub events: Vec<BackendEvent>,
}