use std::{collections::HashMap, path::PathBuf};

use asterforge_document_core::DocumentState;
use asterforge_freecad_bridge::{BridgeDocumentSnapshot, BridgeStatus, UndoStack};

use crate::domain::{
    BackendEvent, BootReport, JobStatusEntry, ObjectNode, PropertyGroup, RecentDocumentEntry,
    StepPmiAnnotation, WorkspaceSessionEntry,
};
use crate::domain::{StepDocumentIndex, StepSceneBundle};

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
#[serde(default)]
pub(super) struct PersistedWorkspaceState {
    pub(super) active_document_path: Option<String>,
    pub(super) active_workbench_id: Option<String>,
    pub(super) selected_object_id: Option<String>,
    pub(super) selection_mode: Option<String>,
    pub(super) recent_documents: Vec<RecentDocumentEntry>,
    pub(super) workspace_sessions: Vec<WorkspaceSessionEntry>,
    pub(super) combo_view_tab: String,
    pub(super) bottom_dock_tab: String,
    pub(super) combo_view_visible: bool,
    pub(super) report_dock_visible: bool,
    pub(super) combo_view_size_hint: f32,
    pub(super) report_dock_size_hint: f32,
}

#[derive(Debug, Clone)]
pub(super) struct AppModel {
    pub(super) session_namespace: String,
    pub(super) boot_report: BootReport,
    pub(super) bridge_status: BridgeStatus,
    pub(super) bridge_snapshot: BridgeDocumentSnapshot,
    pub(super) document: DocumentState,
    pub(super) object_tree: Vec<ObjectNode>,
    pub(super) selection_mode: String,
    pub(super) preselected_object_id: Option<String>,
    pub(super) selected_object_id: String,
    pub(super) jobs: Vec<JobStatusEntry>,
    pub(super) properties_by_object: HashMap<String, Vec<PropertyGroup>>,
    pub(super) events: Vec<BackendEvent>,
    pub(super) undo_stack: UndoStack,
    pub(super) recent_documents: Vec<RecentDocumentEntry>,
    pub(super) workspace_sessions: Vec<WorkspaceSessionEntry>,
    pub(super) combo_view_tab: String,
    pub(super) bottom_dock_tab: String,
    pub(super) combo_view_visible: bool,
    pub(super) report_dock_visible: bool,
    pub(super) combo_view_size_hint: f32,
    pub(super) report_dock_size_hint: f32,
    pub(super) extension_compatibility: crate::domain::ExtensionCompatibilityState,
    pub(super) step_cache_by_document: HashMap<String, StepCacheEntry>,
    pub(super) step_pmi_inspection_by_document: HashMap<String, StepPmiInspectionSummary>,
    pub(super) step_measurement_by_document: HashMap<String, StepMeasurementSummary>,
    pub(super) step_viewport_camera_by_document: HashMap<String, StepViewportCameraState>,
}

#[derive(Debug, Clone)]
pub(super) struct StepCacheEntry {
    pub(super) source_path: PathBuf,
    pub(super) document_index: StepDocumentIndex,
    pub(super) scene_bundle: StepSceneBundle,
}

#[derive(Debug, Clone)]
pub(super) struct StepMeasurementSummary {
    pub(super) object_id: String,
    pub(super) label: String,
    pub(super) span_x: f32,
    pub(super) span_y: f32,
    pub(super) span_z: f32,
    pub(super) representation_count: usize,
    pub(super) annotation_count: usize,
}

#[derive(Debug, Clone)]
pub(super) struct StepPmiInspectionSummary {
    pub(super) object_id: String,
    pub(super) label: String,
    pub(super) entity_id: u64,
    pub(super) annotations: Vec<StepPmiAnnotation>,
}

#[derive(Debug, Clone)]
pub(super) struct StepViewportCameraState {
    pub(super) eye: [f32; 3],
    pub(super) target: [f32; 3],
}