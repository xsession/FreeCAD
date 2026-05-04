use std::{collections::HashMap, path::{Path, PathBuf}, sync::Arc};

use anyhow::Context;
use asterforge_command_core::command_spec;
pub use asterforge_command_core::CommandExecutionRequest;
use asterforge_document_core::{DocumentState, DocumentSummary};
use asterforge_freecad_bridge::{open_document_snapshot, BridgeDocumentSnapshot, BridgeStatus, UndoStack};
use asterforge_protocol_types::asterforge::protocol::v1::{
    BootPayload as ProtoBootPayload, CommandCatalogResponse as ProtoCommandCatalogResponse,
    CommandInvocation, CommandReply, DiagnosticsResponse as ProtoDiagnosticsResponse,
    DocumentRef as ProtoDocumentRef,
    EventEnvelope as ProtoEventEnvelope,
    FeatureHistoryResponse as ProtoFeatureHistoryResponse, JobStatusResponse as ProtoJobStatusResponse,
    ObjectTreeResponse as ProtoObjectTreeResponse,
    PreselectionRequest as ProtoPreselectionRequest,
    PreselectionState as ProtoPreselectionState,
    ShellPanelMutationRequest as ProtoShellPanelMutationRequest,
    ShellSessionMutationRequest as ProtoShellSessionMutationRequest,
    SelectionModeRequest as ProtoSelectionModeRequest, SelectionRef, SelectionReply,
    ShellSnapshot as ProtoShellSnapshot,
    WorkbenchActivationRequest as ProtoWorkbenchActivationRequest,
    SelectionState as ProtoSelectionState, PropertyResponse as ProtoPropertyResponse,
    TaskPanelResponse as ProtoTaskPanelResponse, ViewportResponse as ProtoViewportResponse,
};
use asterforge_step_core::{
    ClosedShell as StepClosedShell, ManifoldSolidBrep as StepManifoldSolidBrep, StepMappedFile,
};
use tokio::sync::RwLock;

use super::protocol::{
    boot_payload_proto_from_http, command_reply_from_http, preselection_state_proto_from_http,
    proto_command_catalog_from_http, proto_diagnostics_from_http, proto_document_ref_from_http,
    proto_event_from_http, proto_feature_history_from_http, proto_jobs_from_http,
    proto_object_node_from_http, proto_properties_from_http, proto_task_panel_from_http,
    proto_shell_snapshot_from_http, proto_viewport_from_http, selection_reply_from_http,
    selection_state_proto_from_http,
};
use super::command_runtime;

use crate::domain::{
    bridge_object_state, document_evaluation_state_from_bridge, document_graph_from_bridge,
    document_summary_from_bridge, feature_history_from_bridge,
    extension_compatibility_state,
    find_bridge_child, find_pad_length_mm, object_tree_from_bridge, sample_boot_report, sample_bridge_status,
    preselection_state_from_bridge, selectable_object_ids_for_mode, selection_state_from_bridge,
    sketch_constraint_summary,
    shell_snapshot_from_bridge, step_shell_snapshot,
    normalize_workbench_id, workbench_display_name,
    command_catalog_from_bridge, sample_event_stream, sample_property_groups, task_panel_from_bridge,
    viewport_from_bridge, BackendEvent, BootReport, CommandCatalogResponse,
    DiagnosticsResponse, FeatureHistoryResponse, ObjectNode, PropertyGroup,
    JobStageEntry, JobStatusEntry, JobStatusResponse, PreselectionStateResponse,
    PropertyResponse, RecentDocumentEntry, SelectionModeOption, SelectionStateResponse, ShellSnapshot,
    StepDocumentIndex, StepSceneBundle, step_document_index_from_parsed, step_scene_bundle_from_parsed,
    TaskPanelResponse, WorkspaceSessionEntry,
    ViewportDiffResponse, ViewportResponse, diagnostics_from_bridge,
};

const STEP_OBJECT_MODE: &str = "object";
const STEP_WORKBENCH_ID: &str = "step";
const STEP_WORKBENCH_DISPLAY_NAME: &str = "STEP Inspection";
const STEP_DEFAULT_CAMERA_EYE: [f32; 3] = [2.6, 2.2, 3.1];
const STEP_DEFAULT_CAMERA_TARGET: [f32; 3] = [0.8, 0.7, 0.4];

#[derive(Clone)]
pub struct AppState {
    inner: Arc<RwLock<AppModel>>,
    persistence_path: Option<PathBuf>,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
#[serde(default)]
struct PersistedWorkspaceState {
    active_document_path: Option<String>,
    active_workbench_id: Option<String>,
    selected_object_id: Option<String>,
    selection_mode: Option<String>,
    recent_documents: Vec<RecentDocumentEntry>,
    workspace_sessions: Vec<WorkspaceSessionEntry>,
    combo_view_tab: String,
    bottom_dock_tab: String,
    combo_view_visible: bool,
    report_dock_visible: bool,
    combo_view_size_hint: f32,
    report_dock_size_hint: f32,
}

#[derive(Debug, Clone)]
pub(super) struct AppModel {
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
    pub(super) annotations: Vec<crate::domain::StepPmiAnnotation>,
}

#[derive(Debug, Clone)]
pub(super) struct StepViewportCameraState {
    pub(super) eye: [f32; 3],
    pub(super) target: [f32; 3],
}

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

#[derive(Debug, Clone, serde::Deserialize)]
pub struct OpenDocumentHttpRequest {
    pub file_path: String,
}

#[derive(Debug, Clone, serde::Deserialize)]
pub struct SelectionRequest {
    pub document_id: String,
    pub object_id: String,
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct SelectionResponse {
    pub selected_object_id: String,
}

#[derive(Debug, Clone, serde::Deserialize)]
pub struct SelectionModeRequest {
    pub document_id: String,
    pub mode_id: String,
}

#[derive(Debug, Clone, serde::Deserialize)]
pub struct ActivateWorkbenchRequest {
    pub document_id: String,
    pub workbench_id: String,
}

#[derive(Debug, Clone, serde::Deserialize)]
pub struct PreselectionRequest {
    pub document_id: String,
    pub object_id: Option<String>,
}

#[derive(Debug, Clone, serde::Deserialize)]
pub struct ShellPanelMutationRequest {
    pub document_id: String,
    pub panel_id: String,
    pub active_tab: Option<String>,
    pub visible: Option<bool>,
    pub size_hint: Option<f32>,
}

#[derive(Debug, Clone, serde::Deserialize)]
pub struct ShellSessionMutationRequest {
    pub document_id: String,
    pub remove_workspace_session_id: Option<String>,
    pub clear_recent_documents: bool,
    pub clear_inactive_workspace_sessions: bool,
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct HttpCommandExecutionResponse {
    pub command_id: String,
    pub accepted: bool,
    pub status_message: String,
    pub document_dirty: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub viewport_diff: Option<ViewportDiffResponse>,
}

impl AppState {
    pub fn new() -> Self {
        Self::with_persistence_path(default_persistence_path())
    }

    fn with_persistence_path(persistence_path: Option<PathBuf>) -> Self {
        let persisted_workspace = persistence_path
            .as_deref()
            .and_then(load_persisted_workspace_state);
        let snapshot = open_document_snapshot(
            persisted_workspace
                .as_ref()
                .and_then(|state| state.active_document_path.as_deref()),
        );
        let bridge_status = sample_bridge_status();
        let document = document_state_from_bridge(&snapshot, &bridge_status);
        let object_tree = object_tree_from_bridge(&snapshot);
        let selected_object_id = snapshot.selected_object_id.clone();
        let properties_by_object = build_property_map(&snapshot, &object_tree);

        let mut model = AppModel {
            boot_report: sample_boot_report(),
            bridge_status,
            bridge_snapshot: snapshot,
            document,
            object_tree,
            selection_mode: "object".into(),
            preselected_object_id: None,
            selected_object_id,
            jobs: vec![],
            properties_by_object,
            events: sample_event_stream(),
            undo_stack: UndoStack::new(50),
            recent_documents: vec![],
            workspace_sessions: vec![],
            combo_view_tab: "model".into(),
            bottom_dock_tab: "report".into(),
            combo_view_visible: true,
            report_dock_visible: true,
            combo_view_size_hint: 0.28,
            report_dock_size_hint: 0.24,
        };

        if let Some(persisted_workspace) = persisted_workspace.as_ref() {
            model.apply_persisted_workspace_state(persisted_workspace);
        } else {
            model.remember_current_document();
        }

        Self {
            inner: Arc::new(RwLock::new(AppModel {
                boot_report: sample_boot_report(),
                bridge_status,
                bridge_snapshot: snapshot,
                document,
                object_tree,
                selection_mode: "object".into(),
                preselected_object_id: None,
                selected_object_id,
                jobs: vec![],
                properties_by_object,
                events: sample_event_stream(),
                undo_stack: UndoStack::new(50),
                recent_documents,
                workspace_sessions,
                combo_view_tab: "model".into(),
                bottom_dock_tab: "report".into(),
                combo_view_visible: true,
                report_dock_visible: true,
                combo_view_size_hint: 0.28,
                report_dock_size_hint: 0.24,
                extension_compatibility: extension_compatibility_state(),
                step_cache_by_document: HashMap::new(),
                step_pmi_inspection_by_document: HashMap::new(),
                step_measurement_by_document: HashMap::new(),
                step_viewport_camera_by_document: HashMap::new(),
            })),
        }
    }

    #[cfg(test)]
    fn new_with_persistence_path(persistence_path: PathBuf) -> Self {
        Self::with_persistence_path(Some(persistence_path))
    }

    pub async fn snapshot(&self) -> AppSnapshot {
        let model = self.inner.read().await;
        AppSnapshot {
            boot_report: model.boot_report.clone(),
            document: model.document.summary().clone(),
            object_tree: model.object_tree.clone(),
            events: model.events.clone(),
        }
    }

    pub async fn boot_payload(&self) -> BootPayload {
        let model = self.inner.read().await;
        let selected_object_id = model.selected_object_id.clone();

        BootPayload {
            boot_report: model.boot_report.clone(),
            bridge_status: model.bridge_status.clone(),
            document: model.document.summary().clone(),
            shell_snapshot: model.shell_snapshot(),
            object_tree: model.object_tree.clone(),
            selected_object_id: selected_object_id.clone(),
            selection_state: model.selection_state(),
            preselection_state: model.preselection_state(),
            jobs: model.jobs(),
            properties: PropertyResponse {
                object_id: selected_object_id.clone(),
                groups: model
                    .properties_by_object
                    .get(&selected_object_id)
                    .cloned()
                    .unwrap_or_default(),
            },
            viewport: model.viewport(),
            feature_history: model.feature_history(),
            command_catalog: model.command_catalog(),
            task_panel: model.task_panel(),
            diagnostics: model.diagnostics(),
            events: model.events.clone(),
        }
    }

    pub async fn boot_payload_proto(&self) -> ProtoBootPayload {
        boot_payload_proto_from_http(self.boot_payload().await)
    }

    pub async fn open_document(&self, file_path: String) -> DocumentSummary {
        let snapshot = open_document_snapshot(Some(&file_path));

        let mut model = self.inner.write().await;
        model.bridge_snapshot = snapshot;
        model.preselected_object_id = None;
        model.step_cache_by_document.clear();
        model.step_pmi_inspection_by_document.clear();
        model.step_measurement_by_document.clear();
        model.step_viewport_camera_by_document.clear();
        model.extension_compatibility = extension_compatibility_state();
        model.sync_from_snapshot();
        let document_id = model.document.document_id.clone();
        model.apply_step_projection_for_active_document(&document_id);
        model.remember_current_document();
        let next_job_id = format!("job-{}-document.open", model.jobs.len() + 1);
        let load_label = if model.is_step_document() {
            "Read STEP Part 21 payload"
        } else {
            "Read FCStd payload"
        };
        let open_stages = vec![
            JobStageEntry {
                stage_id: "queued".into(),
                label: "Queued by shell".into(),
                state: "completed".into(),
                progress_percent: 15,
            },
            JobStageEntry {
                stage_id: "read_document".into(),
                label: load_label.into(),
                state: "completed".into(),
                progress_percent: 55,
            },
            JobStageEntry {
                stage_id: "hydrate_backend".into(),
                label: "Hydrate backend state".into(),
                state: "completed".into(),
                progress_percent: 82,
            },
            JobStageEntry {
                stage_id: "completed".into(),
                label: "Document ready".into(),
                state: "completed".into(),
                progress_percent: 100,
            },
        ];
        model.jobs.insert(
            0,
            JobStatusEntry {
                job_id: next_job_id,
                title: "Open document".into(),
                command_id: "document.open".into(),
                state: "completed".into(),
                progress_percent: 100,
                detail: format!("Opened {}", file_path),
                object_id: None,
                stages: open_stages.clone(),
            },
        );
        model.jobs.truncate(8);
        for stage in open_stages {
            model.events.insert(
                0,
                BackendEvent {
                    topic: if stage.progress_percent < 100 {
                        "worker_lifecycle".into()
                    } else {
                        "document_changed".into()
                    },
                    level: "info".into(),
                    message: format!("document.open: {}", stage.label),
                    document_id: document_id.clone(),
                    object_id: None,
                },
            );
        }
        model.events.insert(
            0,
            BackendEvent {
                topic: "document_changed".into(),
                level: "info".into(),
                message: format!("Opened {}", file_path),
                document_id,
                object_id: None,
            },
        );

        self.persist_model(&model);

        model.document.summary().clone()
    }

    pub async fn set_selection(&self, request: SelectionRequest) -> Option<SelectionResponse> {
        let mut model = self.inner.write().await;
        if model.document.document_id != request.document_id {
            return None;
        }
        let next_selection =
            model.normalize_selection_for_mode(&request.object_id, &model.selection_mode)?;
        if !model.properties_by_object.contains_key(&next_selection) {
            return None;
        }

        if !model.is_step_document() {
            model.bridge_snapshot.selected_object_id = next_selection.clone();
        }
        model.selected_object_id = next_selection.clone();
        model.preselected_object_id = None;
        if model.is_step_document() {
            model.remember_current_document();
        } else {
            model.sync_from_snapshot();
        }
        let document_id = model.document.document_id.clone();
        let selection_mode = model.selection_mode.clone();
        let selection_message = if next_selection == request.object_id {
            format!("Selected {}", next_selection)
        } else {
            format!(
                "Selection mode {} retargeted {} to {}",
                selection_mode, request.object_id, next_selection
            )
        };
        model.events.insert(
            0,
            BackendEvent {
                topic: "selection_changed".into(),
                level: "info".into(),
                message: selection_message,
                document_id: document_id.clone(),
                object_id: Some(next_selection.clone()),
            },
        );
        model.events.insert(
            1,
            BackendEvent {
                topic: "viewport_updated".into(),
                level: "info".into(),
                message: "Viewport synchronized to backend-owned selection".into(),
                document_id,
                object_id: Some(next_selection.clone()),
            },
        );

        self.persist_model(&model);

        Some(SelectionResponse {
            selected_object_id: next_selection,
        })
    }

    pub async fn set_selection_proto(&self, request: SelectionRef) -> Option<SelectionReply> {
        self.set_selection(SelectionRequest {
            document_id: request.document_id,
            object_id: request.object_id,
        })
        .await
        .map(selection_reply_from_http)
    }

    pub async fn set_selection_mode(
        &self,
        request: SelectionModeRequest,
    ) -> Option<SelectionStateResponse> {
        let mut model = self.inner.write().await;
        if model.document.document_id != request.document_id {
            return None;
        }

        if !["object", "body", "sketch", "feature"].contains(&request.mode_id.as_str()) {
            return None;
        }

        if model.is_step_document() && request.mode_id != STEP_OBJECT_MODE {
            return None;
        }

        let next_selection =
            model.normalize_selection_for_mode(&model.selected_object_id, &request.mode_id)?;

        model.selection_mode = request.mode_id;
        if !model.is_step_document() {
            model.bridge_snapshot.selected_object_id = next_selection.clone();
        }
        model.selected_object_id = next_selection.clone();
        model.preselected_object_id = None;
        if model.is_step_document() {
            model.remember_current_document();
        } else {
            model.sync_from_snapshot();
        }
        let document_id = model.document.document_id.clone();
        let selection_mode = model.selection_mode.clone();
        let mode_message = format!(
            "Selection mode set to {} with {} active",
            selection_mode, next_selection
        );
        model.events.insert(
            0,
            BackendEvent {
                topic: "selection_mode_changed".into(),
                level: "info".into(),
                message: mode_message,
                document_id,
                object_id: Some(next_selection),
            },
        );

        self.persist_model(&model);

        Some(model.selection_state())
    }

    pub async fn set_selection_mode_proto(
        &self,
        request: ProtoSelectionModeRequest,
    ) -> Option<ProtoSelectionState> {
        self.set_selection_mode(SelectionModeRequest {
            document_id: request.document_id,
            mode_id: request.mode_id,
        })
        .await
        .map(selection_state_proto_from_http)
    }

    pub async fn activate_workbench(
        &self,
        request: ActivateWorkbenchRequest,
    ) -> Option<DocumentSummary> {
        let mut model = self.inner.write().await;
        if model.document.document_id != request.document_id {
            return None;
        }

        let workbench_id = normalize_workbench_id(&request.workbench_id);
        let next_workbench = if model.is_step_document() {
            if workbench_id != STEP_WORKBENCH_ID {
                return None;
            }
            STEP_WORKBENCH_DISPLAY_NAME.to_string()
        } else {
            if !["partdesign", "part", "sketcher", "mesh"].contains(&workbench_id.as_str()) {
                return None;
            }
            workbench_display_name(&workbench_id)
        };
        let document_id = model.document.document_id.clone();
        let selected_object_id = model.selected_object_id.clone();
        model.bridge_snapshot.workbench = next_workbench.clone();
        model.document.summary.workbench = next_workbench.clone();
        model.preselected_object_id = None;
        model.remember_current_document();
        model.events.insert(
            0,
            BackendEvent {
                topic: "workbench_changed".into(),
                level: "info".into(),
                message: format!("Activated {} workbench", next_workbench),
                document_id,
                object_id: Some(selected_object_id),
            },
        );

        self.persist_model(&model);

        Some(model.document.summary().clone())
    }

    #[allow(dead_code)]
    pub async fn activate_workbench_proto(
        &self,
        request: ProtoWorkbenchActivationRequest,
    ) -> Option<ProtoDocumentRef> {
        self.activate_workbench(ActivateWorkbenchRequest {
            document_id: request.document_id,
            workbench_id: request.workbench_id,
        })
        .await
        .map(proto_document_ref_from_http)
    }

    pub async fn object_tree_proto(&self, document_id: &str) -> Option<ProtoObjectTreeResponse> {
        let model = self.inner.read().await;
        model.document.matches_document(document_id).then(|| ProtoObjectTreeResponse {
            document: Some(proto_document_ref_from_http(model.document.summary().clone())),
            roots: model
                .object_tree
                .clone()
                .into_iter()
                .map(proto_object_node_from_http)
                .collect(),
        })
    }

    pub async fn properties(&self, document_id: &str, object_id: &str) -> Option<PropertyResponse> {
        let model = self.inner.read().await;
        if model.document.document_id != document_id {
            return None;
        }

        model
            .properties_by_object
            .get(object_id)
            .cloned()
            .map(|groups| PropertyResponse {
                object_id: object_id.to_string(),
                groups,
            })
    }

    pub async fn properties_proto(
        &self,
        document_id: &str,
        object_id: &str,
    ) -> Option<ProtoPropertyResponse> {
        self.properties(document_id, object_id)
            .await
            .map(proto_properties_from_http)
    }

    pub async fn events(&self, document_id: &str) -> Option<Vec<BackendEvent>> {
        let model = self.inner.read().await;
        (model.document.document_id == document_id).then(|| model.events.clone())
    }

    pub async fn events_proto(&self, document_id: &str) -> Option<Vec<ProtoEventEnvelope>> {
        self.events(document_id)
            .await
            .map(|events| events.into_iter().map(proto_event_from_http).collect())
    }

    pub async fn viewport(&self, document_id: &str) -> Option<ViewportResponse> {
        let model = self.inner.read().await;
        (model.document.document_id == document_id).then(|| model.viewport())
    }

    pub async fn viewport_proto(&self, document_id: &str) -> Option<ProtoViewportResponse> {
        self.viewport(document_id).await.map(proto_viewport_from_http)
    }

    pub async fn command_catalog(&self, document_id: &str) -> Option<CommandCatalogResponse> {
        let model = self.inner.read().await;
        (model.document.document_id == document_id).then(|| model.command_catalog())
    }

    pub async fn shell_snapshot(&self, document_id: &str) -> Option<ShellSnapshot> {
        let model = self.inner.read().await;
        (model.document.document_id == document_id).then(|| model.shell_snapshot())
    }

    pub async fn shell_snapshot_proto(&self, document_id: &str) -> Option<ProtoShellSnapshot> {
        self.shell_snapshot(document_id)
            .await
            .map(proto_shell_snapshot_from_http)
    }

    pub async fn update_shell_panel(
        &self,
        request: ShellPanelMutationRequest,
    ) -> Option<ShellSnapshot> {
        let mut model = self.inner.write().await;
        if model.document.document_id != request.document_id {
            return None;
        }

        match request.panel_id.as_str() {
            "combo_view" => {
                if let Some(active_tab) = request.active_tab.as_deref() {
                    if !["model", "tasks"].contains(&active_tab) {
                        return None;
                    }
                    model.combo_view_tab = active_tab.to_string();
                }
                if let Some(visible) = request.visible {
                    model.combo_view_visible = visible;
                }
                if let Some(size_hint) = request.size_hint {
                    model.combo_view_size_hint = size_hint.clamp(0.22, 0.42);
                }
            }
            "report_dock" => {
                if let Some(active_tab) = request.active_tab.as_deref() {
                    if !["report", "python", "jobs", "diagnostics", "history", "commands"]
                        .contains(&active_tab)
                    {
                        return None;
                    }
                    model.bottom_dock_tab = active_tab.to_string();
                }
                if let Some(visible) = request.visible {
                    model.report_dock_visible = visible;
                }
                if let Some(size_hint) = request.size_hint {
                    model.report_dock_size_hint = size_hint.clamp(0.18, 0.4);
                }
            }
            _ => return None,
        }

        model.remember_current_document();

        let document_id = model.document.document_id.clone();
        let selected_object_id = model.selected_object_id.clone();
        let detail = request
            .active_tab
            .clone()
            .or_else(|| request.visible.map(|visible| if visible { "visible".into() } else { "hidden".into() }))
            .or_else(|| request.size_hint.map(|value| format!("size {:.2}", value)))
            .unwrap_or_else(|| "updated".into());

        model.events.insert(
            0,
            BackendEvent {
                topic: "shell_layout_changed".into(),
                level: "info".into(),
                message: format!("{} -> {}", request.panel_id, detail),
                document_id,
                object_id: Some(selected_object_id),
            },
        );

        self.persist_model(&model);

        Some(model.shell_snapshot())
    }

    #[allow(dead_code)]
    pub async fn update_shell_panel_proto(
        &self,
        request: ProtoShellPanelMutationRequest,
    ) -> Option<ProtoShellSnapshot> {
        self.update_shell_panel(ShellPanelMutationRequest {
            document_id: request.document_id,
            panel_id: request.panel_id,
            active_tab: request.active_tab,
            visible: request.visible,
            size_hint: request.size_hint,
        })
        .await
        .map(proto_shell_snapshot_from_http)
    }

    pub async fn update_shell_sessions(
        &self,
        request: ShellSessionMutationRequest,
    ) -> Option<ShellSnapshot> {
        let mut model = self.inner.write().await;
        if model.document.document_id != request.document_id {
            return None;
        }

        let active_session_id = model.active_session_id();
        let mut changed = false;

        if request.clear_recent_documents {
            model.recent_documents.clear();
            changed = true;
        }

        if request.clear_inactive_workspace_sessions {
            model.workspace_sessions
                .retain(|entry| entry.session_id == active_session_id);
            changed = true;
        }

        if let Some(session_id) = request.remove_workspace_session_id.as_deref() {
            if session_id == active_session_id {
                return None;
            }
            let previous_len = model.workspace_sessions.len();
            model
                .workspace_sessions
                .retain(|entry| entry.session_id != session_id);
            changed |= model.workspace_sessions.len() != previous_len;
        }

        if !changed {
            return Some(model.shell_snapshot());
        }

        let document_id = model.document.document_id.clone();
        let selected_object_id = model.selected_object_id.clone();
        let detail = if request.clear_recent_documents && request.clear_inactive_workspace_sessions {
            "cleared recent documents and inactive sessions".to_string()
        } else if request.clear_recent_documents {
            "cleared recent documents".to_string()
        } else if request.clear_inactive_workspace_sessions {
            "cleared inactive workspace sessions".to_string()
        } else if let Some(session_id) = request.remove_workspace_session_id {
            format!("dismissed workspace session {session_id}")
        } else {
            "updated shell session state".to_string()
        };

        model.events.insert(
            0,
            BackendEvent {
                topic: "shell_session_changed".into(),
                level: "info".into(),
                message: detail,
                document_id,
                object_id: Some(selected_object_id),
            },
        );

        self.persist_model(&model);
        Some(model.shell_snapshot())
    }

    #[allow(dead_code)]
    pub async fn update_shell_sessions_proto(
        &self,
        request: ProtoShellSessionMutationRequest,
    ) -> Option<ProtoShellSnapshot> {
        self.update_shell_sessions(ShellSessionMutationRequest {
            document_id: request.document_id,
            remove_workspace_session_id: request.remove_workspace_session_id,
            clear_recent_documents: request.clear_recent_documents,
            clear_inactive_workspace_sessions: request.clear_inactive_workspace_sessions,
        })
        .await
        .map(proto_shell_snapshot_from_http)
    }

    pub async fn command_catalog_proto(
        &self,
        document_id: &str,
    ) -> Option<ProtoCommandCatalogResponse> {
        self.command_catalog(document_id)
            .await
            .map(proto_command_catalog_from_http)
    }

    pub async fn feature_history(&self, document_id: &str) -> Option<FeatureHistoryResponse> {
        let model = self.inner.read().await;
        (model.document.document_id == document_id).then(|| model.feature_history())
    }

    pub async fn feature_history_proto(
        &self,
        document_id: &str,
    ) -> Option<ProtoFeatureHistoryResponse> {
        self.feature_history(document_id)
            .await
            .map(proto_feature_history_from_http)
    }

    pub async fn task_panel(&self, document_id: &str) -> Option<TaskPanelResponse> {
        let model = self.inner.read().await;
        (model.document.document_id == document_id).then(|| model.task_panel())
    }

    pub async fn task_panel_proto(&self, document_id: &str) -> Option<ProtoTaskPanelResponse> {
        self.task_panel(document_id)
            .await
            .map(proto_task_panel_from_http)
    }

    pub async fn diagnostics(&self, document_id: &str) -> Option<DiagnosticsResponse> {
        let model = self.inner.read().await;
        (model.document.document_id == document_id).then(|| model.diagnostics())
    }

    pub async fn diagnostics_proto(
        &self,
        document_id: &str,
    ) -> Option<ProtoDiagnosticsResponse> {
        self.diagnostics(document_id)
            .await
            .map(proto_diagnostics_from_http)
    }

    pub async fn selection_state(&self, document_id: &str) -> Option<SelectionStateResponse> {
        let model = self.inner.read().await;
        (model.document.document_id == document_id).then(|| model.selection_state())
    }

    pub async fn selection_state_proto(&self, document_id: &str) -> Option<ProtoSelectionState> {
        self.selection_state(document_id)
            .await
            .map(selection_state_proto_from_http)
    }

    pub async fn preselection_state(
        &self,
        document_id: &str,
    ) -> Option<PreselectionStateResponse> {
        let model = self.inner.read().await;
        (model.document.document_id == document_id).then(|| model.preselection_state())
    }

    pub async fn preselection_state_proto(
        &self,
        document_id: &str,
    ) -> Option<ProtoPreselectionState> {
        self.preselection_state(document_id)
            .await
            .map(preselection_state_proto_from_http)
    }

    pub async fn set_preselection(
        &self,
        request: PreselectionRequest,
    ) -> Option<PreselectionStateResponse> {
        let mut model = self.inner.write().await;
        if model.document.document_id != request.document_id {
            return None;
        }

        let next_preselection = request.object_id.as_deref().and_then(|object_id| {
            let selectable_ids = model.selectable_object_ids_for_active_mode();
            selectable_ids
                .into_iter()
                .find(|candidate| candidate == object_id)
        });

        model.preselected_object_id = next_preselection.clone();
        let document_id = model.document.document_id.clone();
        let message = match next_preselection.as_ref() {
            Some(object_id) => format!("Preselection tracking {}", object_id),
            None => "Preselection cleared".into(),
        };
        model.events.insert(
            0,
            BackendEvent {
                topic: "preselection_changed".into(),
                level: "info".into(),
                message,
                document_id,
                object_id: next_preselection,
            },
        );

        Some(model.preselection_state())
    }

    pub async fn set_preselection_proto(
        &self,
        request: ProtoPreselectionRequest,
    ) -> Option<ProtoPreselectionState> {
        self.set_preselection(PreselectionRequest {
            document_id: request.document_id,
            object_id: request.object_id,
        })
        .await
        .map(preselection_state_proto_from_http)
    }

    pub async fn jobs(&self, document_id: &str) -> Option<JobStatusResponse> {
        let model = self.inner.read().await;
        (model.document.document_id == document_id).then(|| model.jobs())
    }

    pub async fn jobs_proto(&self, document_id: &str) -> Option<ProtoJobStatusResponse> {
        self.jobs(document_id).await.map(proto_jobs_from_http)
    }

    pub async fn run_command(
        &self,
        request: CommandExecutionRequest,
    ) -> Option<HttpCommandExecutionResponse> {
        let mut model = self.inner.write().await;
        if model.document.document_id != request.document_id {
            return None;
        }

        Some(command_runtime::run_command(&mut model, request))
            .map(|response| {
                self.persist_model(&model);
                response
            })
    }

    pub async fn run_command_proto(&self, request: CommandInvocation) -> Option<CommandReply> {
        let http_request = CommandExecutionRequest {
            command_id: request.command_id,
            document_id: request.document_id,
            target_object_id: request.target_object_id,
            arguments: request.arguments,
        };

        self.run_command(http_request)
            .await
            .map(command_reply_from_http)
    }

    pub async fn step_document_index(
        &self,
        document_id: &str,
    ) -> anyhow::Result<Option<StepDocumentIndex>> {
        let mut model = self.inner.write().await;
        model
            .resolve_step_cache(document_id)
            .map(|entry| entry.map(|entry| entry.document_index))
    }

    pub async fn step_scene_bundle(
        &self,
        document_id: &str,
    ) -> anyhow::Result<Option<StepSceneBundle>> {
        let mut model = self.inner.write().await;
        model
            .resolve_step_cache(document_id)
            .map(|entry| entry.map(|entry| entry.scene_bundle))
    }
}

impl AppState {
    fn persist_model(&self, model: &AppModel) {
        if let Some(path) = self.persistence_path.as_deref() {
            save_persisted_workspace_state(path, &model.persisted_workspace_state());
        }
    }
}


impl AppModel {
    fn resolve_step_cache(&mut self, document_id: &str) -> anyhow::Result<Option<StepCacheEntry>> {
        if self.document.document_id != document_id {
            return Ok(None);
        }

        let Some(source_path) = step_source_path(&self.document) else {
            self.step_cache_by_document.remove(document_id);
            return Ok(None);
        };

        if let Some(cached) = self.step_cache_by_document.get(document_id) {
            if cached.source_path == source_path {
                return Ok(Some(cached.clone()));
            }
        }

        let cache_entry = load_step_bundle_from_path(&source_path)?;
        self.step_cache_by_document
            .insert(document_id.to_string(), cache_entry.clone());
        Ok(Some(cache_entry))
    }

    fn active_step_cache(&self) -> Option<&StepCacheEntry> {
        self.step_cache_by_document.get(&self.document.document_id)
    }

    fn is_step_document(&self) -> bool {
        step_source_path(&self.document).is_some()
    }

    fn selectable_object_ids_for_active_mode(&self) -> Vec<String> {
        if self.active_step_cache().is_some() {
            step_selectable_object_ids_for_mode(&self.object_tree, &self.selection_mode)
        } else {
            selectable_object_ids_for_mode(&self.bridge_snapshot, &self.selection_mode)
        }
    }

    fn apply_step_projection_for_active_document(&mut self, document_id: &str) {
        let Ok(Some(cache)) = self.resolve_step_cache(document_id) else {
            return;
        };

        self.selection_mode = STEP_OBJECT_MODE.into();
        self.object_tree = step_object_tree_from_cache(&cache);
        self.properties_by_object = step_property_map_from_cache(&cache, &self.object_tree);

        if !self.properties_by_object.contains_key(&self.selected_object_id) {
            if let Some(first_node) = flatten_object_nodes(&self.object_tree).first() {
                self.selected_object_id = first_node.object_id.clone();
            }
        }
    }

    fn viewport(&self) -> ViewportResponse {
        self.active_step_cache()
            .map(|cache| {
                step_viewport_response(
                    &self.document.document_id,
                    &self.selected_object_id,
                    cache,
                    &self.object_tree,
                    self.step_viewport_camera_by_document.get(&self.document.document_id),
                )
            })
            .unwrap_or_else(|| viewport_from_bridge(&self.bridge_snapshot, &self.selected_object_id))
    }

    fn command_catalog(&self) -> CommandCatalogResponse {
        self.active_step_cache()
            .map(|cache| {
                step_command_catalog_response(
                    &self.document.document_id,
                    &self.selected_object_id,
                    cache,
                    &self.object_tree,
                    self.step_measurement_by_document.get(&self.document.document_id),
                )
            })
            .unwrap_or_else(|| {
                command_catalog_from_bridge(
                    &self.bridge_snapshot,
                    &self.document.document_id,
                    Some(&self.selected_object_id),
                    self.undo_stack.can_undo(),
                    self.undo_stack.can_redo(),
                )
            })
    }

    pub(super) fn shell_snapshot(&self) -> ShellSnapshot {
        self.active_step_cache()
            .map(|cache| {
                step_shell_snapshot(
                    self.document.summary(),
                    &self.extension_compatibility,
                    Some(&self.selected_object_id),
                    &self.recent_documents,
                    &self.workspace_sessions,
                    &self.combo_view_tab,
                    &self.bottom_dock_tab,
                    self.combo_view_visible,
                    self.report_dock_visible,
                    self.combo_view_size_hint,
                    self.report_dock_size_hint,
                    &cache.scene_bundle,
                    step_selected_object_is_visible(&self.object_tree, &self.selected_object_id),
                    flatten_object_nodes(&self.object_tree).len() > 1,
                    hidden_step_object_count(&self.object_tree) > 0,
                    step_measurement_for_selection(&self.selected_object_id, cache).is_some(),
                    step_shell_inspection_state(
                        &self.selected_object_id,
                        self.step_pmi_inspection_by_document.get(&self.document.document_id),
                        self.step_measurement_by_document.get(&self.document.document_id),
                    ),
                )
            })
            .unwrap_or_else(|| {
                shell_snapshot_from_bridge(
                    &self.bridge_snapshot,
                    self.document.summary(),
                    &self.extension_compatibility,
                    Some(&self.selected_object_id),
                    self.undo_stack.can_undo(),
                    self.undo_stack.can_redo(),
                    &self.recent_documents,
                    &self.workspace_sessions,
                    &self.combo_view_tab,
                    &self.bottom_dock_tab,
                    self.combo_view_visible,
                    self.report_dock_visible,
                    self.combo_view_size_hint,
                    self.report_dock_size_hint,
                )
            })
    }

    fn feature_history(&self) -> FeatureHistoryResponse {
        self.document.history().clone()
    }

    fn task_panel(&self) -> TaskPanelResponse {
        self.active_step_cache()
            .map(|cache| {
                step_task_panel_response(
                    &self.document.document_id,
                    &self.selected_object_id,
                    cache,
                    &self.object_tree,
                    self.step_pmi_inspection_by_document.get(&self.document.document_id),
                    self.step_measurement_by_document.get(&self.document.document_id),
                )
            })
            .unwrap_or_else(|| {
                task_panel_from_bridge(
                    &self.bridge_snapshot,
                    &self.document.document_id,
                    Some(&self.selected_object_id),
                    find_pad_length_mm(&self.bridge_snapshot, &self.selected_object_id),
                    self.undo_stack.can_undo(),
                    self.undo_stack.can_redo(),
                )
            })
    }

    fn diagnostics(&self) -> DiagnosticsResponse {
        self.active_step_cache()
            .map(|cache| {
                step_diagnostics_response(
                    &self.document.document_id,
                    &self.selected_object_id,
                    &self.events,
                    &self.bridge_status.worker_mode,
                    cache,
                    &self.object_tree,
                )
            })
            .unwrap_or_else(|| {
                let mut diagnostics = diagnostics_from_bridge(
                    &self.bridge_snapshot,
                    Some(&self.selected_object_id),
                    &self.events,
                    &self.bridge_status,
                );
                diagnostics.summary.total_features = self.document.evaluation().total_features;
                diagnostics.summary.suppressed_count = self.document.evaluation().suppressed_count;
                diagnostics.summary.inactive_count = self.document.evaluation().inactive_count;
                diagnostics.summary.rolled_back_count = self.document.evaluation().rolled_back_count;
                diagnostics.summary.history_marker_active = self.document.evaluation().history_marker_active;
                diagnostics.summary.worker_mode = self.document.evaluation().worker_mode.clone();
                diagnostics
            })
    }

    fn selection_state(&self) -> SelectionStateResponse {
        self.active_step_cache()
            .map(|_| {
                step_selection_state_response(
                    &self.document.document_id,
                    &self.selected_object_id,
                    &self.selection_mode,
                    &self.object_tree,
                )
            })
            .unwrap_or_else(|| {
                selection_state_from_bridge(
                    &self.bridge_snapshot,
                    &self.selected_object_id,
                    &self.selection_mode,
                )
            })
    }

    fn preselection_state(&self) -> PreselectionStateResponse {
        self.active_step_cache()
            .map(|cache| {
                step_preselection_state_response(
                    &self.document.document_id,
                    self.preselected_object_id.as_deref(),
                    &self.selection_mode,
                    cache,
                    &self.object_tree,
                )
            })
            .unwrap_or_else(|| {
                preselection_state_from_bridge(
                    &self.bridge_snapshot,
                    self.preselected_object_id.as_deref(),
                    &self.selection_mode,
                    self.undo_stack.can_undo(),
                    self.undo_stack.can_redo(),
                )
            })
    }

    fn jobs(&self) -> JobStatusResponse {
        JobStatusResponse {
            document_id: self.document.document_id.clone(),
            jobs: self.jobs.clone(),
        }
    }

    pub(super) fn sync_from_snapshot(&mut self) {
        self.document.sync(
            document_summary_from_bridge(&self.bridge_snapshot),
            feature_history_from_bridge(&self.bridge_snapshot),
            document_evaluation_state_from_bridge(
                &self.bridge_snapshot,
                &self.bridge_status.worker_mode,
            ),
        );
        self.document
            .set_graph(document_graph_from_bridge(&self.bridge_snapshot));
        self.object_tree = object_tree_from_bridge(&self.bridge_snapshot);
        self.selected_object_id = self.bridge_snapshot.selected_object_id.clone();
        self.properties_by_object = build_property_map(&self.bridge_snapshot, &self.object_tree);
        self.remember_current_document();
    }

    pub(super) fn apply_command_target(&mut self, target_object_id: Option<&str>) -> bool {
        let Some(target_object_id) = target_object_id.filter(|value| !value.is_empty()) else {
            return true;
        };

        let Some(next_selection) = self.normalize_selection_for_mode(target_object_id, &self.selection_mode) else {
            return false;
        };
        if next_selection != target_object_id {
            return false;
        }

        self.preselected_object_id = None;
        if self.active_step_cache().is_some() {
            self.selected_object_id = next_selection;
            self.remember_current_document();
        } else {
            self.bridge_snapshot.selected_object_id = next_selection;
            self.sync_from_snapshot();
        }

        true
    }

    fn remember_current_document(&mut self) {
        let file_path = self
            .document
            .file_path
            .clone()
            .unwrap_or_else(|| format!("C:/models/{}.FCStd", self.document.display_name));
        let recent_entry = RecentDocumentEntry {
            file_path: file_path.clone(),
            display_name: self.document.display_name.clone(),
            workbench: self.document.workbench.clone(),
            dirty: self.document.dirty,
        };
        self.recent_documents.retain(|entry| entry.file_path != file_path);
        self.recent_documents.insert(0, recent_entry);
        self.recent_documents.truncate(8);

        let session_id = format!("{}:{}", self.document.document_id, file_path);
        let session_entry = WorkspaceSessionEntry {
            session_id,
            document_id: self.document.document_id.clone(),
            display_name: self.document.display_name.clone(),
            file_path: file_path.clone(),
            workbench: self.document.workbench.clone(),
            dirty: self.document.dirty,
            selected_object_id: Some(self.selected_object_id.clone()),
            selection_mode: Some(self.selection_mode.clone()),
            combo_view_tab: Some(self.combo_view_tab.clone()),
            bottom_dock_tab: Some(self.bottom_dock_tab.clone()),
            combo_view_visible: Some(self.combo_view_visible),
            report_dock_visible: Some(self.report_dock_visible),
            combo_view_size_hint: Some(self.combo_view_size_hint),
            report_dock_size_hint: Some(self.report_dock_size_hint),
        };
        self.workspace_sessions
            .retain(|entry| entry.file_path != file_path);
        self.workspace_sessions.insert(0, session_entry);
        self.workspace_sessions.truncate(8);
    }

    fn active_session_id(&self) -> String {
        let file_path = self
            .document
            .file_path
            .clone()
            .unwrap_or_else(|| format!("C:/models/{}.FCStd", self.document.display_name));
        format!("{}:{}", self.document.document_id, file_path)
    }

    fn normalize_selection_for_mode(
        &self,
        requested_object_id: &str,
        selection_mode: &str,
    ) -> Option<String> {
        if self.active_step_cache().is_some() {
            return (selection_mode == STEP_OBJECT_MODE
                && self.properties_by_object.contains_key(requested_object_id))
                .then(|| requested_object_id.to_string())
                .or_else(|| self.properties_by_object.keys().next().cloned());
        }

        if selection_mode == "object" {
            return self
                .properties_by_object
                .contains_key(requested_object_id)
                .then(|| requested_object_id.to_string());
        }

        let selectable_ids = selectable_object_ids_for_mode(&self.bridge_snapshot, selection_mode);
        if selectable_ids.is_empty() {
            return None;
        }

        if selectable_ids.iter().any(|object_id| object_id == requested_object_id) {
            Some(requested_object_id.to_string())
        } else {
            selectable_ids.into_iter().next()
        }
    }
}

fn default_persistence_path() -> Option<PathBuf> {
    #[cfg(test)]
    {
        return None;
    }

    #[cfg(not(test))]
    {
        if let Some(explicit) = std::env::var_os("ASTERFORGE_SHELL_STATE_FILE") {
            return Some(PathBuf::from(explicit));
        }

        if let Some(appdata) = std::env::var_os("APPDATA") {
            return Some(PathBuf::from(appdata).join("AsterForge").join("shell-state.json"));
        }

        if let Some(state_home) = std::env::var_os("XDG_STATE_HOME") {
            return Some(PathBuf::from(state_home).join("asterforge").join("shell-state.json"));
        }

        return std::env::var_os("HOME")
            .map(|home| PathBuf::from(home).join(".asterforge").join("shell-state.json"));
    }
}

fn load_persisted_workspace_state(path: &Path) -> Option<PersistedWorkspaceState> {
    let contents = match fs::read_to_string(path) {
        Ok(contents) => contents,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return None,
        Err(error) => {
            tracing::warn!(path = %path.display(), ?error, "failed to read persisted shell state");
            return None;
        }
    };

    match serde_json::from_str::<PersistedWorkspaceState>(&contents) {
        Ok(state) => Some(state),
        Err(error) => {
            tracing::warn!(path = %path.display(), ?error, "failed to parse persisted shell state");
            None
        }
    }
}

fn save_persisted_workspace_state(path: &Path, state: &PersistedWorkspaceState) {
    if let Some(parent) = path.parent() {
        if let Err(error) = fs::create_dir_all(parent) {
            tracing::warn!(path = %path.display(), ?error, "failed to create shell state directory");
            return;
        }
    }

    let contents = match serde_json::to_vec_pretty(state) {
        Ok(contents) => contents,
        Err(error) => {
            tracing::warn!(path = %path.display(), ?error, "failed to serialize persisted shell state");
            return;
        }
    };

    if let Err(error) = fs::write(path, contents) {
        tracing::warn!(path = %path.display(), ?error, "failed to write persisted shell state");
    }
}

fn document_state_from_bridge(
    snapshot: &BridgeDocumentSnapshot,
    bridge_status: &BridgeStatus,
) -> DocumentState {
    DocumentState::new(
        document_summary_from_bridge(snapshot),
        feature_history_from_bridge(snapshot),
        document_evaluation_state_from_bridge(snapshot, &bridge_status.worker_mode),
    )
    .with_graph(document_graph_from_bridge(snapshot))
}

fn build_property_map(
    snapshot: &BridgeDocumentSnapshot,
    object_tree: &[ObjectNode],
) -> HashMap<String, Vec<PropertyGroup>> {
    let mut map = HashMap::new();
    collect_properties(snapshot, object_tree, &mut map);
    map
}

fn collect_properties(
    snapshot: &BridgeDocumentSnapshot,
    nodes: &[ObjectNode],
    map: &mut HashMap<String, Vec<PropertyGroup>>,
) {
    for node in nodes {
        let mut groups = sample_property_groups();
        if let Some(first_group) = groups.first_mut() {
            if let Some(label_property) = first_group
                .properties
                .iter_mut()
                .find(|property| property.property_id == "label")
            {
                label_property.value_preview = node.label.clone();
            }
        }

        if let Some(second_group) = groups.get_mut(1) {
            if let Some(length_property) = second_group.properties.first_mut() {
                length_property.value_preview = match node.object_type.as_str() {
                    "PartDesign::Pad" => format!(
                        "{:.2} mm",
                        find_pad_length_mm(snapshot, &node.object_id).unwrap_or(12.0)
                    ),
                    "PartDesign::Pocket" => format!(
                        "{:.2} mm",
                        find_pad_length_mm(snapshot, &node.object_id).unwrap_or(8.0)
                    ),
                    "Sketcher::SketchObject" => find_bridge_child(snapshot, &node.object_id)
                        .map(sketch_constraint_summary)
                        .unwrap_or_else(|| "Unknown sketch state".into()),
                    _ => "Inherited".into(),
                };
                if node.object_type == "Sketcher::SketchObject" {
                    length_property.property_id = "constraint_count".into();
                    length_property.display_name = "Constraint state".into();
                    length_property.property_type = "App::PropertyString".into();
                    length_property.value_kind = "string".into();
                    length_property.read_only = true;
                    length_property.unit = None;
                    length_property.expression_capable = false;
                }
            }
        }

        groups.push(PropertyGroup {
            group_id: "dependency".into(),
            title: "Dependency".into(),
            properties: dependency_properties(snapshot, node),
        });

        if let Some(definition_group) = definition_property_group(snapshot, node) {
            groups.push(definition_group);
        }

        map.insert(node.object_id.clone(), groups);
        collect_properties(snapshot, &node.children, map);
    }
}

fn definition_property_group(
    snapshot: &BridgeDocumentSnapshot,
    node: &ObjectNode,
) -> Option<PropertyGroup> {
    let bridge_node = find_bridge_child(snapshot, &node.object_id)?;
    let mut properties = Vec::new();

    if let Some(reference_plane) = bridge_node.reference_plane.as_ref() {
        properties.push(crate::domain::PropertyMetadata {
            property_id: "reference_plane".into(),
            display_name: "Reference plane".into(),
            property_type: "App::PropertyEnumeration".into(),
            value_kind: "string".into(),
            read_only: true,
            unit: None,
            expression_capable: false,
            value_preview: reference_plane.clone(),
        });
    }

    if let Some(extent_mode) = bridge_node.extent_mode.as_ref() {
        properties.push(crate::domain::PropertyMetadata {
            property_id: "extent_mode".into(),
            display_name: "Extent mode".into(),
            property_type: "App::PropertyEnumeration".into(),
            value_kind: "string".into(),
            read_only: true,
            unit: None,
            expression_capable: false,
            value_preview: extent_mode.clone(),
        });
    }

    if node.object_type == "PartDesign::Pad" {
        properties.push(crate::domain::PropertyMetadata {
            property_id: "midplane".into(),
            display_name: "Symmetric to plane".into(),
            property_type: "App::PropertyBool".into(),
            value_kind: "boolean".into(),
            read_only: true,
            unit: None,
            expression_capable: false,
            value_preview: bridge_node.midplane.to_string(),
        });
    }

    (!properties.is_empty()).then(|| PropertyGroup {
        group_id: "definition".into(),
        title: "Definition".into(),
        properties,
    })
}

fn dependency_properties(
    snapshot: &BridgeDocumentSnapshot,
    node: &ObjectNode,
) -> Vec<crate::domain::PropertyMetadata> {
    let bridge_node = snapshot
        .roots
        .iter()
        .flat_map(|root| std::iter::once(root).chain(root.children.iter()))
        .find(|candidate| candidate.object_id == node.object_id);
    let state = bridge_node.map(|candidate| bridge_object_state(snapshot, candidate));

    vec![
        crate::domain::PropertyMetadata {
            property_id: "model_state".into(),
            display_name: "Model state".into(),
            property_type: "App::PropertyEnumeration".into(),
            value_kind: "string".into(),
            read_only: true,
            unit: None,
            expression_capable: false,
            value_preview: state
                .as_ref()
                .map(|dependency| {
                    if dependency.suppressed {
                        "Suppressed".into()
                    } else if dependency.active {
                        "Active".into()
                    } else {
                        "Inactive".into()
                    }
                })
                .unwrap_or_else(|| "Unknown".into()),
        },
        crate::domain::PropertyMetadata {
            property_id: "inactive_reason".into(),
            display_name: "Dependency note".into(),
            property_type: "App::PropertyString".into(),
            value_kind: "string".into(),
            read_only: true,
            unit: None,
            expression_capable: false,
            value_preview: state
                .and_then(|dependency| dependency.inactive_reason)
                .unwrap_or_else(|| "Resolved".into()),
        },
    ]
}

fn load_step_bundle_from_path(source_path: &Path) -> anyhow::Result<StepCacheEntry> {
    let mapped = StepMappedFile::open(source_path)
        .with_context(|| format!("failed to open STEP source {}", source_path.display()))?;
    let model_index = mapped
        .build_index(96)
        .with_context(|| format!("failed to index STEP source {}", source_path.display()))?;
    let dto = model_index.to_dto();
    let mut shells = Vec::new();
    let mut breps = Vec::new();

    for entity_id in model_index.entities.keys().copied() {
        let entity = model_index
            .load_entity(entity_id)
            .with_context(|| format!("failed to load STEP entity #{entity_id}"))?;
        if let Ok(shell) = StepClosedShell::try_from(&entity) {
            shells.push(shell);
            continue;
        }
        if let Ok(brep) = StepManifoldSolidBrep::try_from(&entity) {
            breps.push(brep);
        }
    }

    Ok(StepCacheEntry {
        source_path: source_path.to_path_buf(),
        document_index: step_document_index_from_parsed(&dto, &breps, &shells),
        scene_bundle: step_scene_bundle_from_parsed(&dto, &breps, &shells),
    })
}

fn step_source_path(document: &DocumentState) -> Option<PathBuf> {
    let file_path = document.file_path.as_ref()?;
    let candidate = PathBuf::from(file_path);
    let extension = candidate
        .extension()
        .and_then(|value| value.to_str())
        .map(|value| value.to_ascii_lowercase())?;

    ["stp", "step", "p21"].contains(&extension.as_str()).then_some(candidate)
}

fn step_entity_object_id(entity_id: u64) -> String {
    format!("step-entity-{entity_id}")
}

pub(super) fn step_entity_id_from_object_id(object_id: &str) -> Option<u64> {
    object_id.strip_prefix("step-entity-")?.parse::<u64>().ok()
}

pub(super) fn step_parent_object_id(
    object_id: &str,
    assemblies: &[crate::domain::StepAssemblyNode],
) -> Option<String> {
    let entity_id = step_entity_id_from_object_id(object_id)?;
    find_step_parent_entity_id(entity_id, assemblies).map(step_entity_object_id)
}

pub(super) fn step_first_child_object_id(
    object_id: &str,
    assemblies: &[crate::domain::StepAssemblyNode],
) -> Option<String> {
    let entity_id = step_entity_id_from_object_id(object_id)?;
    find_step_assembly(entity_id, assemblies)
        .and_then(|assembly| assembly.children.first())
        .map(|child| step_entity_object_id(child.entity_id))
}

fn step_object_tree_from_cache(cache: &StepCacheEntry) -> Vec<ObjectNode> {
    cache
        .scene_bundle
        .assemblies
        .iter()
        .map(step_object_node_from_assembly)
        .collect()
}

fn step_object_node_from_assembly(assembly: &crate::domain::StepAssemblyNode) -> ObjectNode {
    ObjectNode {
        object_id: step_entity_object_id(assembly.entity_id),
        label: assembly.label.clone(),
        object_type: if assembly.children.is_empty() {
            "STEP::MANIFOLD_SOLID_BREP".into()
        } else {
            "STEP::ASSEMBLY_NODE".into()
        },
        visibility: crate::domain::VisibilityState::Visible,
        children: assembly.children.iter().map(step_object_node_from_assembly).collect(),
    }
}

fn step_property_map_from_cache(
    cache: &StepCacheEntry,
    object_tree: &[ObjectNode],
) -> HashMap<String, Vec<PropertyGroup>> {
    let entity_by_id: HashMap<u64, &crate::domain::StepEntitySpan> = cache
        .document_index
        .entities
        .iter()
        .map(|entity| (entity.entity_id, entity))
        .collect();
    let assembly_by_id: HashMap<u64, &crate::domain::StepAssemblyNode> = flatten_step_assemblies(&cache.scene_bundle.assemblies)
        .into_iter()
        .map(|assembly| (assembly.entity_id, assembly))
        .collect();

    flatten_object_nodes(object_tree)
        .into_iter()
        .filter_map(|node| {
            let entity_id = step_entity_id_from_object_id(&node.object_id)?;
            Some((
                node.object_id.clone(),
                step_property_groups_for_node(
                    node,
                    entity_id,
                    entity_by_id.get(&entity_id).copied(),
                    assembly_by_id.get(&entity_id).copied(),
                ),
            ))
        })
        .collect()
}

fn step_property_groups_for_node(
    node: &ObjectNode,
    entity_id: u64,
    entity: Option<&crate::domain::StepEntitySpan>,
    assembly: Option<&crate::domain::StepAssemblyNode>,
) -> Vec<PropertyGroup> {
    let mut groups = vec![PropertyGroup {
        group_id: "base".into(),
        title: "Base".into(),
        properties: vec![
            crate::domain::PropertyMetadata {
                property_id: "label".into(),
                display_name: "Label".into(),
                property_type: "App::PropertyString".into(),
                value_kind: "string".into(),
                read_only: true,
                unit: None,
                expression_capable: false,
                value_preview: node.label.clone(),
            },
            crate::domain::PropertyMetadata {
                property_id: "entity_id".into(),
                display_name: "Entity Id".into(),
                property_type: "Step::EntityId".into(),
                value_kind: "integer".into(),
                read_only: true,
                unit: None,
                expression_capable: false,
                value_preview: format!("#{entity_id}"),
            },
        ],
    }];

    if let Some(entity) = entity {
        groups.push(PropertyGroup {
            group_id: "step_record".into(),
            title: "STEP Record".into(),
            properties: vec![
                crate::domain::PropertyMetadata {
                    property_id: "keyword".into(),
                    display_name: "Keyword".into(),
                    property_type: "Step::Keyword".into(),
                    value_kind: "string".into(),
                    read_only: true,
                    unit: None,
                    expression_capable: false,
                    value_preview: entity.keyword.clone(),
                },
                crate::domain::PropertyMetadata {
                    property_id: "references".into(),
                    display_name: "Reference count".into(),
                    property_type: "Step::ReferenceList".into(),
                    value_kind: "integer".into(),
                    read_only: true,
                    unit: None,
                    expression_capable: false,
                    value_preview: entity.references.len().to_string(),
                },
                crate::domain::PropertyMetadata {
                    property_id: "byte_range".into(),
                    display_name: "Byte range".into(),
                    property_type: "Step::ByteRange".into(),
                    value_kind: "string".into(),
                    read_only: true,
                    unit: None,
                    expression_capable: false,
                    value_preview: format!("{}..{}", entity.byte_range.start, entity.byte_range.end),
                },
            ],
        });
    }

    if let Some(assembly) = assembly {
        groups.push(PropertyGroup {
            group_id: "topology".into(),
            title: "Topology".into(),
            properties: vec![
                crate::domain::PropertyMetadata {
                    property_id: "child_count".into(),
                    display_name: "Child count".into(),
                    property_type: "App::PropertyInteger".into(),
                    value_kind: "integer".into(),
                    read_only: true,
                    unit: None,
                    expression_capable: false,
                    value_preview: assembly.children.len().to_string(),
                },
                crate::domain::PropertyMetadata {
                    property_id: "brep_count".into(),
                    display_name: "BREP count".into(),
                    property_type: "App::PropertyInteger".into(),
                    value_kind: "integer".into(),
                    read_only: true,
                    unit: None,
                    expression_capable: false,
                    value_preview: assembly.brep_ids.len().to_string(),
                },
                crate::domain::PropertyMetadata {
                    property_id: "pmi_count".into(),
                    display_name: "PMI annotations".into(),
                    property_type: "App::PropertyInteger".into(),
                    value_kind: "integer".into(),
                    read_only: true,
                    unit: None,
                    expression_capable: false,
                    value_preview: assembly.pmi_annotation_ids.len().to_string(),
                },
            ],
        });
    }

    groups
}

fn step_selection_state_response(
    document_id: &str,
    selected_object_id: &str,
    current_mode: &str,
    object_tree: &[ObjectNode],
) -> SelectionStateResponse {
    let nodes = flatten_object_nodes(object_tree);
    let selected_node = nodes
        .iter()
        .find(|node| node.object_id == selected_object_id)
        .copied()
        .or_else(|| nodes.first().copied())
        .expect("STEP tree should contain at least one node");
    let object_count = nodes.len() as u32;

    SelectionStateResponse {
        document_id: document_id.into(),
        current_mode: current_mode.into(),
        selected_object_id: selected_node.object_id.clone(),
        selected_object_label: selected_node.label.clone(),
        selected_object_type: selected_node.object_type.clone(),
        available_modes: vec![
            SelectionModeOption {
                mode_id: "object".into(),
                label: "Object".into(),
                description: "Select parsed STEP entities and assembly nodes.".into(),
                enabled: object_count > 0,
                object_count,
            },
            SelectionModeOption {
                mode_id: "body".into(),
                label: "Bodies".into(),
                description: "Not available for imported STEP topology.".into(),
                enabled: false,
                object_count: 0,
            },
            SelectionModeOption {
                mode_id: "sketch".into(),
                label: "Sketches".into(),
                description: "Not available for imported STEP topology.".into(),
                enabled: false,
                object_count: 0,
            },
            SelectionModeOption {
                mode_id: "feature".into(),
                label: "Features".into(),
                description: "Not available for imported STEP topology.".into(),
                enabled: false,
                object_count: 0,
            },
        ],
    }
}

fn step_preselection_state_response(
    document_id: &str,
    preselected_object_id: Option<&str>,
    current_mode: &str,
    cache: &StepCacheEntry,
    object_tree: &[ObjectNode],
) -> PreselectionStateResponse {
    let nodes = flatten_object_nodes(object_tree);
    let preselected = preselected_object_id.and_then(|object_id| {
        nodes.iter().find(|node| node.object_id == object_id).copied()
    });
    let selectable = current_mode == STEP_OBJECT_MODE && preselected.is_some();
    let suggested_commands = preselected
        .and_then(|node| step_entity_id_from_object_id(&node.object_id))
        .map(|entity_id| {
            if cache
                .scene_bundle
                .semantic_pmi
                .iter()
                .any(|annotation| annotation.target_entity_ids.contains(&entity_id))
            {
                vec!["shell.show_report_view".into()]
            } else {
                vec![]
            }
        })
        .unwrap_or_default();

    PreselectionStateResponse {
        document_id: document_id.into(),
        current_mode: current_mode.into(),
        object_id: preselected.map(|node| node.object_id.clone()),
        object_label: preselected.map(|node| node.label.clone()),
        object_type: preselected.map(|node| node.object_type.clone()),
        selectable,
        model_state: if selectable { "parsed".into() } else { "none".into() },
        dependency_note: "Imported STEP topology is read-only in the current shell.".into(),
        suggested_commands,
        detail: preselected
            .map(|node| format!("Parsed STEP node {} is available for inspection.", node.label))
            .unwrap_or_else(|| "No STEP preselection candidate is currently active.".into()),
    }
}

fn step_viewport_response(
    document_id: &str,
    selected_object_id: &str,
    cache: &StepCacheEntry,
    object_tree: &[ObjectNode],
    camera: Option<&StepViewportCameraState>,
) -> ViewportResponse {
    ViewportResponse {
        document_id: document_id.into(),
        selected_object_id: selected_object_id.into(),
        scene: crate::domain::ViewportScene {
            camera_eye: camera.map(|camera| camera.eye).unwrap_or(STEP_DEFAULT_CAMERA_EYE),
            camera_target: camera.map(|camera| camera.target).unwrap_or(STEP_DEFAULT_CAMERA_TARGET),
            drawables: cache
                .scene_bundle
                .tessellated_representations
                .iter()
                .filter(|representation| {
                    step_selected_object_is_visible(
                        object_tree,
                        &step_entity_object_id(representation.entity_id),
                    )
                })
                .map(|representation| step_drawable_from_representation(representation, &cache.scene_bundle))
                .collect(),
        },
    }
}

fn step_drawable_from_representation(
    representation: &crate::domain::StepTessellatedFaceSet,
    scene: &StepSceneBundle,
) -> crate::domain::ViewportDrawable {
    let points = project_step_points(&representation.positions);
    let paths = step_paths_from_points(&points, &representation.indices);
    let (min_x, max_x, min_y, max_y) = step_bounds_from_points(&points);
    let label = flatten_step_assemblies(&scene.assemblies)
        .into_iter()
        .find(|assembly| assembly.entity_id == representation.entity_id)
        .map(|assembly| assembly.label.clone())
        .unwrap_or_else(|| format!("STEP #{}", representation.entity_id));

    crate::domain::ViewportDrawable {
        object_id: step_entity_object_id(representation.entity_id),
        label,
        kind: "step-brep".into(),
        accent: "#7bd6ff".into(),
        bounds: crate::domain::ViewportBounds {
            x: min_x,
            y: min_y,
            width: (max_x - min_x).max(1.0),
            height: (max_y - min_y).max(1.0),
        },
        paths,
    }
}

fn step_task_panel_response(
    document_id: &str,
    selected_object_id: &str,
    cache: &StepCacheEntry,
    object_tree: &[ObjectNode],
    inspection: Option<&StepPmiInspectionSummary>,
    measurement: Option<&StepMeasurementSummary>,
) -> TaskPanelResponse {
    let has_parent = step_parent_object_id(selected_object_id, &cache.scene_bundle.assemblies).is_some();
    let has_child = step_first_child_object_id(selected_object_id, &cache.scene_bundle.assemblies).is_some();
    let selected_visible = step_selected_object_is_visible(object_tree, selected_object_id);
    let hidden_count = hidden_step_object_count(object_tree);
    let has_pmi = step_entity_id_from_object_id(selected_object_id)
        .map(|entity_id| {
            cache
                .scene_bundle
                .semantic_pmi
                .iter()
                .any(|annotation| annotation.target_entity_ids.contains(&entity_id))
        })
        .unwrap_or(false);
    let selection_matches_inspection = inspection
        .map(|result| result.object_id == selected_object_id)
        .unwrap_or(false);

    let selection_matches_measurement = measurement
        .map(|result| result.object_id == selected_object_id)
        .unwrap_or(false);

    let mut sections = vec![
        crate::domain::TaskPanelSection {
            section_id: "selection".into(),
            title: "Selection".into(),
            rows: vec![crate::domain::TaskPanelRow {
                label: "Active node".into(),
                value: selected_object_id.into(),
                emphasis: true,
            }, crate::domain::TaskPanelRow {
                label: "Visibility".into(),
                value: if selected_visible { "Visible".into() } else { "Hidden".into() },
                emphasis: selected_visible,
            }],
        },
        crate::domain::TaskPanelSection {
            section_id: "pmi".into(),
            title: "PMI".into(),
            rows: if let Some(result) = inspection.filter(|_| selection_matches_inspection) {
                vec![
                    crate::domain::TaskPanelRow {
                        label: "Inspected node".into(),
                        value: result.label.clone(),
                        emphasis: true,
                    },
                    crate::domain::TaskPanelRow {
                        label: "STEP entity".into(),
                        value: format!("#{}", result.entity_id),
                        emphasis: false,
                    },
                    crate::domain::TaskPanelRow {
                        label: "Annotations".into(),
                        value: result.annotations.len().to_string(),
                        emphasis: true,
                    },
                ]
            } else if has_pmi {
                vec![crate::domain::TaskPanelRow {
                    label: "semantic_pmi".into(),
                    value: "PMI is available for this selection. Run Inspect PMI to load the drill-down.".into(),
                    emphasis: false,
                }]
            } else {
                vec![crate::domain::TaskPanelRow {
                    label: "semantic_pmi".into(),
                    value: "No PMI attached to the current selection.".into(),
                    emphasis: false,
                }]
            },
        },
    ];

    if let Some(result) = inspection.filter(|_| selection_matches_inspection) {
        for (index, annotation) in result.annotations.iter().enumerate() {
            sections.push(crate::domain::TaskPanelSection {
                section_id: format!("pmi-annotation-{}", index + 1),
                title: format!("PMI Annotation {}", index + 1),
                rows: vec![
                    crate::domain::TaskPanelRow {
                        label: "Type".into(),
                        value: annotation.semantic_type.clone(),
                        emphasis: true,
                    },
                    crate::domain::TaskPanelRow {
                        label: "Text".into(),
                        value: annotation.text.clone(),
                        emphasis: true,
                    },
                    crate::domain::TaskPanelRow {
                        label: "Targets".into(),
                        value: annotation
                            .target_entity_ids
                            .iter()
                            .map(|entity_id| format!("#{}", entity_id))
                            .collect::<Vec<_>>()
                            .join(", "),
                        emphasis: false,
                    },
                    crate::domain::TaskPanelRow {
                        label: "Presentation".into(),
                        value: if annotation.presentation_entity_ids.is_empty() {
                            "None".into()
                        } else {
                            annotation
                                .presentation_entity_ids
                                .iter()
                                .map(|entity_id| format!("#{}", entity_id))
                                .collect::<Vec<_>>()
                                .join(", ")
                        },
                        emphasis: false,
                    },
                ],
            });
        }
    }

    if let Some(result) = measurement.filter(|_| selection_matches_measurement) {
        sections.push(crate::domain::TaskPanelSection {
            section_id: "measurement".into(),
            title: "Measurement".into(),
            rows: vec![
                crate::domain::TaskPanelRow {
                    label: "Measured node".into(),
                    value: result.label.clone(),
                    emphasis: true,
                },
                crate::domain::TaskPanelRow {
                    label: "X span".into(),
                    value: format!("{:.2}", result.span_x),
                    emphasis: true,
                },
                crate::domain::TaskPanelRow {
                    label: "Y span".into(),
                    value: format!("{:.2}", result.span_y),
                    emphasis: true,
                },
                crate::domain::TaskPanelRow {
                    label: "Z span".into(),
                    value: format!("{:.2}", result.span_z),
                    emphasis: true,
                },
                crate::domain::TaskPanelRow {
                    label: "Mesh packets".into(),
                    value: result.representation_count.to_string(),
                    emphasis: false,
                },
                crate::domain::TaskPanelRow {
                    label: "PMI annotations".into(),
                    value: result.annotation_count.to_string(),
                    emphasis: false,
                },
            ],
        });
    }

    TaskPanelResponse {
        document_id: document_id.into(),
        title: "STEP Inspection".into(),
        description: "Imported STEP topology is available for inspection and standards review.".into(),
        sections,
        suggested_commands: [
            has_parent.then(|| "step.select_parent".into()),
            has_child.then(|| "step.select_first_child".into()),
            has_pmi.then(|| "step.inspect_pmi".into()),
            step_measurement_for_selection(selected_object_id, cache)
                .is_some()
                .then(|| "step.measure_selection".into()),
            selected_visible.then(|| "step.hide_selection".into()),
            (flatten_object_nodes(object_tree).len() > 1).then(|| "step.isolate_selection".into()),
            (hidden_count > 0).then(|| "step.show_all".into()),
            Some("selection.focus".into()),
        ]
        .into_iter()
        .flatten()
        .collect(),
    }
}

fn step_pmi_overlay_from_inspection(
    inspection: &StepPmiInspectionSummary,
) -> crate::domain::StepPmiInspectionOverlay {
    crate::domain::StepPmiInspectionOverlay {
        object_id: inspection.object_id.clone(),
        label: inspection.label.clone(),
        entity_id: inspection.entity_id,
        target_object_ids: inspection
            .annotations
            .iter()
            .flat_map(|annotation| annotation.target_entity_ids.iter().copied())
            .map(step_entity_object_id)
            .collect::<Vec<_>>(),
        presentation_object_ids: inspection
            .annotations
            .iter()
            .flat_map(|annotation| annotation.presentation_entity_ids.iter().copied())
            .map(step_entity_object_id)
            .collect::<Vec<_>>(),
        annotation_lines: inspection
            .annotations
            .iter()
            .map(|annotation| format!("{}: {}", annotation.semantic_type, annotation.text))
            .collect(),
    }
}

fn step_measurement_overlay_from_summary(
    measurement: &StepMeasurementSummary,
) -> crate::domain::StepMeasurementOverlay {
    crate::domain::StepMeasurementOverlay {
        object_id: measurement.object_id.clone(),
        label: measurement.label.clone(),
        span_x: measurement.span_x,
        span_y: measurement.span_y,
        span_z: measurement.span_z,
        representation_count: measurement.representation_count,
        annotation_count: measurement.annotation_count,
    }
}

fn step_shell_inspection_state(
    selected_object_id: &str,
    inspection: Option<&StepPmiInspectionSummary>,
    measurement: Option<&StepMeasurementSummary>,
) -> Option<crate::domain::ShellInspectionState> {
    let step_pmi = inspection
        .filter(|result| result.object_id == selected_object_id)
        .map(step_pmi_overlay_from_inspection);
    let step_measurement = measurement
        .filter(|result| result.object_id == selected_object_id)
        .map(step_measurement_overlay_from_summary);

    if step_pmi.is_none() && step_measurement.is_none() {
        None
    } else {
        Some(crate::domain::ShellInspectionState {
            step_pmi,
            step_measurement,
        })
    }
}

fn step_command_catalog_response(
    document_id: &str,
    selected_object_id: &str,
    cache: &StepCacheEntry,
    object_tree: &[ObjectNode],
    measurement: Option<&StepMeasurementSummary>,
) -> CommandCatalogResponse {
    let has_parent = step_parent_object_id(selected_object_id, &cache.scene_bundle.assemblies).is_some();
    let has_child = step_first_child_object_id(selected_object_id, &cache.scene_bundle.assemblies).is_some();
    let selected_visible = step_selected_object_is_visible(object_tree, selected_object_id);
    let has_pmi = step_entity_id_from_object_id(selected_object_id)
        .map(|entity_id| {
            cache
                .scene_bundle
                .semantic_pmi
                .iter()
                .any(|annotation| annotation.target_entity_ids.contains(&entity_id))
        })
        .unwrap_or(false);
    let object_count = flatten_object_nodes(object_tree).len();
    let hidden_count = hidden_step_object_count(object_tree);
    let can_measure = step_measurement_for_selection(selected_object_id, cache).is_some();
    let has_measurement = measurement
        .map(|result| result.object_id == selected_object_id)
        .unwrap_or(false);

    CommandCatalogResponse {
        document_id: document_id.into(),
        workbench: crate::domain::WorkbenchState {
            workbench_id: "step".into(),
            display_name: "STEP Inspection".into(),
            mode: if has_measurement {
                format!("{} imported nodes, live measurement", object_count)
            } else {
                format!("{} imported nodes", object_count)
            },
        },
        commands: vec![
            step_command_definition("selection.focus", true),
            step_command_definition("extensions.refresh_inventory", true),
            step_command_definition("extensions.review_external_workbenches", true),
            step_command_definition_with_arguments(
                "extensions.run_inventory_entry",
                true,
                vec![asterforge_command_core::CommandArgumentDefinition {
                    argument_id: "entry_id".into(),
                    label: "Inventory entry".into(),
                    value_type: "string".into(),
                    required: true,
                    default_value: None,
                    placeholder: Some("macro:auto_dimensioning".into()),
                    unit: None,
                    options: vec![],
                }],
            ),
            step_command_definition("step.view_iso", true),
            step_command_definition("step.view_fit_all", true),
            step_command_definition("step.view_reset", true),
            step_command_definition("step.view_front", true),
            step_command_definition("step.view_back", true),
            step_command_definition("step.view_right", true),
            step_command_definition("step.view_left", true),
            step_command_definition("step.view_top", true),
            step_command_definition("step.view_bottom", true),
            step_command_definition("step.select_parent", has_parent),
            step_command_definition("step.select_first_child", has_child),
            step_command_definition("step.inspect_pmi", has_pmi),
            step_command_definition("step.measure_selection", can_measure),
            step_command_definition("step.hide_selection", selected_visible),
            step_command_definition("step.isolate_selection", object_count > 1),
            step_command_definition("step.show_all", hidden_count > 0),
        ],
    }
}

fn step_command_definition(command_id: &str, enabled: bool) -> asterforge_command_core::CommandDefinition {
    step_command_definition_with_arguments(command_id, enabled, vec![])
}

fn step_command_definition_with_arguments(
    command_id: &str,
    enabled: bool,
    arguments: Vec<asterforge_command_core::CommandArgumentDefinition>,
) -> asterforge_command_core::CommandDefinition {
    let spec = command_spec(command_id).expect("STEP command spec should exist");
    asterforge_command_core::CommandDefinition {
        command_id: spec.command_id.into(),
        label: spec.label.into(),
        group: spec.group.into(),
        icon: spec.icon.map(str::to_string),
        shortcut: spec.shortcut.map(str::to_string),
        enabled,
        requires_selection: spec.requires_selection,
        description: spec.description.into(),
        action_label: spec.action_label.map(str::to_string),
        arguments,
    }
}

fn step_diagnostics_response(
    document_id: &str,
    selected_object_id: &str,
    events: &[BackendEvent],
    worker_mode: &str,
    cache: &StepCacheEntry,
    object_tree: &[ObjectNode],
) -> DiagnosticsResponse {
    let nodes = flatten_object_nodes(object_tree);
    let selected = nodes.iter().find(|node| node.object_id == selected_object_id).copied();

    DiagnosticsResponse {
        document_id: document_id.into(),
        summary: crate::domain::DiagnosticsSummary {
            total_features: cache.document_index.entities.len() as u32,
            suppressed_count: 0,
            inactive_count: 0,
            rolled_back_count: 0,
            viewport_drawable_count: cache.scene_bundle.tessellated_representations.len() as u32,
            warning_count: 0,
            error_count: 0,
            history_marker_active: false,
            worker_mode: worker_mode.into(),
        },
        selection: crate::domain::DiagnosticsSelection {
            object_id: selected.map(|node| node.object_id.clone()),
            object_label: selected.map(|node| node.label.clone()),
            object_type: selected.map(|node| node.object_type.clone()),
            model_state: "parsed".into(),
            dependency_note: "STEP import is read-only in the current shell runtime.".into(),
            visible_in_viewport: step_selected_object_is_visible(object_tree, selected_object_id),
        },
        recent_signals: events
            .iter()
            .take(4)
            .map(|event| crate::domain::DiagnosticSignal {
                level: event.level.clone(),
                title: event.topic.replace('_', " "),
                detail: event.message.clone(),
            })
            .collect(),
    }
}

fn step_selectable_object_ids_for_mode(object_tree: &[ObjectNode], selection_mode: &str) -> Vec<String> {
    if selection_mode != STEP_OBJECT_MODE {
        return vec![];
    }

    flatten_object_nodes(object_tree)
        .into_iter()
        .map(|node| node.object_id.clone())
        .collect()
}

pub(super) fn step_hide_object_subtree(object_tree: &mut [ObjectNode], object_id: &str) -> bool {
    set_step_subtree_visibility(object_tree, object_id, crate::domain::VisibilityState::Hidden)
}

pub(super) fn step_show_all_objects(object_tree: &mut [ObjectNode]) {
    set_step_visibility_for_all(object_tree, crate::domain::VisibilityState::Visible);
}

pub(super) fn step_isolate_object_subtree(object_tree: &mut [ObjectNode], object_id: &str) -> bool {
    isolate_step_visibility(object_tree, object_id)
}

pub(super) fn step_selected_object_is_visible(object_tree: &[ObjectNode], object_id: &str) -> bool {
    find_step_object_node(object_tree, object_id)
        .map(|node| !matches!(node.visibility, crate::domain::VisibilityState::Hidden))
        .unwrap_or(false)
}

pub(super) fn step_measurement_for_selection(
    selected_object_id: &str,
    cache: &StepCacheEntry,
) -> Option<StepMeasurementSummary> {
    let entity_id = step_entity_id_from_object_id(selected_object_id)?;
    let assembly = find_step_assembly(entity_id, &cache.scene_bundle.assemblies)?;
    let representation_ids = collect_step_representation_ids(assembly);
    let representations: Vec<&crate::domain::StepTessellatedFaceSet> = cache
        .scene_bundle
        .tessellated_representations
        .iter()
        .filter(|representation| representation_ids.iter().any(|id| id == &representation.representation_id))
        .collect();
    if representations.is_empty() {
        return None;
    }

    let mut min_x = f32::INFINITY;
    let mut min_y = f32::INFINITY;
    let mut min_z = f32::INFINITY;
    let mut max_x = f32::NEG_INFINITY;
    let mut max_y = f32::NEG_INFINITY;
    let mut max_z = f32::NEG_INFINITY;

    for representation in &representations {
        let mut index = 0usize;
        while index + 2 < representation.positions.len() {
            let x = representation.positions[index];
            let y = representation.positions[index + 1];
            let z = representation.positions[index + 2];
            min_x = min_x.min(x);
            min_y = min_y.min(y);
            min_z = min_z.min(z);
            max_x = max_x.max(x);
            max_y = max_y.max(y);
            max_z = max_z.max(z);
            index += 3;
        }
    }

    let annotation_count = cache
        .scene_bundle
        .semantic_pmi
        .iter()
        .filter(|annotation| assembly.pmi_annotation_ids.iter().any(|id| id == &annotation.annotation_id))
        .count();

    Some(StepMeasurementSummary {
        object_id: selected_object_id.into(),
        label: assembly.label.clone(),
        span_x: (max_x - min_x).max(0.0),
        span_y: (max_y - min_y).max(0.0),
        span_z: (max_z - min_z).max(0.0),
        representation_count: representations.len(),
        annotation_count,
    })
}

pub(super) fn step_focus_camera_for_selection(
    selected_object_id: &str,
    cache: &StepCacheEntry,
) -> Option<StepViewportCameraState> {
    let entity_id = step_entity_id_from_object_id(selected_object_id)?;
    let assembly = find_step_assembly(entity_id, &cache.scene_bundle.assemblies)?;
    let representation_ids = collect_step_representation_ids(assembly);
    let representations: Vec<&crate::domain::StepTessellatedFaceSet> = cache
        .scene_bundle
        .tessellated_representations
        .iter()
        .filter(|representation| representation_ids.iter().any(|id| id == &representation.representation_id))
        .collect();
    if representations.is_empty() {
        return None;
    }

    let mut min_x = f32::INFINITY;
    let mut min_y = f32::INFINITY;
    let mut min_z = f32::INFINITY;
    let mut max_x = f32::NEG_INFINITY;
    let mut max_y = f32::NEG_INFINITY;
    let mut max_z = f32::NEG_INFINITY;
    let mut point_count = 0usize;

    for representation in &representations {
        let mut index = 0usize;
        while index + 2 < representation.positions.len() {
            let x = representation.positions[index];
            let y = representation.positions[index + 1];
            let z = representation.positions[index + 2];
            min_x = min_x.min(x);
            min_y = min_y.min(y);
            min_z = min_z.min(z);
            max_x = max_x.max(x);
            max_y = max_y.max(y);
            max_z = max_z.max(z);
            point_count += 1;
            index += 3;
        }
    }

    if point_count == 0 {
        return None;
    }

    let center = [
        (min_x + max_x) / 2.0,
        (min_y + max_y) / 2.0,
        (min_z + max_z) / 2.0,
    ];
    let vector: [f32; 3] = [2.6_f32 - 0.8_f32, 2.2_f32 - 0.7_f32, 3.1_f32 - 0.4_f32];
    let vector_length = (vector[0] * vector[0] + vector[1] * vector[1] + vector[2] * vector[2]).sqrt();
    let direction = if vector_length > f32::EPSILON {
        [
            vector[0] / vector_length,
            vector[1] / vector_length,
            vector[2] / vector_length,
        ]
    } else {
        [0.51214755, 0.42678964, 0.7682213]
    };
    let half_diagonal = ((max_x - min_x).powi(2) + (max_y - min_y).powi(2) + (max_z - min_z).powi(2)).sqrt() / 2.0;
    let focus_distance = vector_length.max(half_diagonal * 2.6).max(2.0);

    Some(StepViewportCameraState {
        eye: [
            center[0] + direction[0] * focus_distance,
            center[1] + direction[1] * focus_distance,
            center[2] + direction[2] * focus_distance,
        ],
        target: center,
    })
}

pub(super) fn step_viewport_camera_for_preset(
    camera: Option<&StepViewportCameraState>,
    preset: &str,
) -> Option<StepViewportCameraState> {
    let baseline = camera.cloned().unwrap_or_else(step_default_viewport_camera_state);
    let direction = step_camera_direction_for_preset(preset)?;
    let distance = step_camera_distance(&baseline.eye, &baseline.target).max(2.0);

    Some(StepViewportCameraState {
        eye: [
            baseline.target[0] + direction[0] * distance,
            baseline.target[1] + direction[1] * distance,
            baseline.target[2] + direction[2] * distance,
        ],
        target: baseline.target,
    })
}

fn step_default_viewport_camera_state() -> StepViewportCameraState {
    StepViewportCameraState {
        eye: STEP_DEFAULT_CAMERA_EYE,
        target: STEP_DEFAULT_CAMERA_TARGET,
    }
}

pub(super) fn step_reset_viewport_camera() -> StepViewportCameraState {
    step_default_viewport_camera_state()
}

pub(super) fn step_fit_all_viewport_camera(
    cache: &StepCacheEntry,
    object_tree: &[ObjectNode],
    camera: Option<&StepViewportCameraState>,
) -> Option<StepViewportCameraState> {
    let visible_entity_ids: Vec<u64> = flatten_object_nodes(object_tree)
        .into_iter()
        .filter(|node| !matches!(node.visibility, crate::domain::VisibilityState::Hidden))
        .filter_map(|node| step_entity_id_from_object_id(&node.object_id))
        .collect();

    let representations: Vec<&crate::domain::StepTessellatedFaceSet> = cache
        .scene_bundle
        .tessellated_representations
        .iter()
        .filter(|representation| visible_entity_ids.contains(&representation.entity_id))
        .collect();
    let (center, half_diagonal) = step_camera_frame_from_representations(&representations)?;

    let baseline = camera.cloned().unwrap_or_else(step_default_viewport_camera_state);
    let vector = [
        baseline.eye[0] - baseline.target[0],
        baseline.eye[1] - baseline.target[1],
        baseline.eye[2] - baseline.target[2],
    ];
    let vector_length = (vector[0] * vector[0] + vector[1] * vector[1] + vector[2] * vector[2]).sqrt();
    let direction = if vector_length > f32::EPSILON {
        [
            vector[0] / vector_length,
            vector[1] / vector_length,
            vector[2] / vector_length,
        ]
    } else {
        [0.51214755, 0.42678964, 0.7682213]
    };
    let focus_distance = vector_length.max(half_diagonal * 2.6).max(2.0);

    Some(StepViewportCameraState {
        eye: [
            center[0] + direction[0] * focus_distance,
            center[1] + direction[1] * focus_distance,
            center[2] + direction[2] * focus_distance,
        ],
        target: center,
    })
}

fn step_camera_distance(eye: &[f32; 3], target: &[f32; 3]) -> f32 {
    let dx = eye[0] - target[0];
    let dy = eye[1] - target[1];
    let dz = eye[2] - target[2];
    (dx * dx + dy * dy + dz * dz).sqrt()
}

fn step_camera_frame_from_representations(
    representations: &[&crate::domain::StepTessellatedFaceSet],
) -> Option<([f32; 3], f32)> {
    if representations.is_empty() {
        return None;
    }

    let mut min_x = f32::INFINITY;
    let mut min_y = f32::INFINITY;
    let mut min_z = f32::INFINITY;
    let mut max_x = f32::NEG_INFINITY;
    let mut max_y = f32::NEG_INFINITY;
    let mut max_z = f32::NEG_INFINITY;
    let mut point_count = 0usize;

    for representation in representations {
        let mut index = 0usize;
        while index + 2 < representation.positions.len() {
            let x = representation.positions[index];
            let y = representation.positions[index + 1];
            let z = representation.positions[index + 2];
            min_x = min_x.min(x);
            min_y = min_y.min(y);
            min_z = min_z.min(z);
            max_x = max_x.max(x);
            max_y = max_y.max(y);
            max_z = max_z.max(z);
            point_count += 1;
            index += 3;
        }
    }

    if point_count == 0 {
        return None;
    }

    let center = [
        (min_x + max_x) / 2.0,
        (min_y + max_y) / 2.0,
        (min_z + max_z) / 2.0,
    ];
    let half_diagonal =
        ((max_x - min_x).powi(2) + (max_y - min_y).powi(2) + (max_z - min_z).powi(2)).sqrt() / 2.0;
    Some((center, half_diagonal))
}

fn step_camera_direction_for_preset(preset: &str) -> Option<[f32; 3]> {
    match preset {
        "iso" => Some(normalize_step_camera_direction([1.0, 1.0, 1.0])),
        "front" => Some([0.0, 0.0, 1.0]),
        "back" => Some([0.0, 0.0, -1.0]),
        "right" => Some([1.0, 0.0, 0.0]),
        "left" => Some([-1.0, 0.0, 0.0]),
        "top" => Some([0.0, 1.0, 0.0]),
        "bottom" => Some([0.0, -1.0, 0.0]),
        _ => None,
    }
}

fn normalize_step_camera_direction(direction: [f32; 3]) -> [f32; 3] {
    let length = (direction[0] * direction[0]
        + direction[1] * direction[1]
        + direction[2] * direction[2])
        .sqrt();
    if length <= f32::EPSILON {
        [0.0, 0.0, 1.0]
    } else {
        [
            direction[0] / length,
            direction[1] / length,
            direction[2] / length,
        ]
    }
}

pub(super) fn step_pmi_inspection_for_selection(
    selected_object_id: &str,
    cache: &StepCacheEntry,
    object_tree: &[ObjectNode],
) -> Option<StepPmiInspectionSummary> {
    let entity_id = step_entity_id_from_object_id(selected_object_id)?;
    let annotations: Vec<crate::domain::StepPmiAnnotation> = cache
        .scene_bundle
        .semantic_pmi
        .iter()
        .filter(|annotation| annotation.target_entity_ids.contains(&entity_id))
        .cloned()
        .collect();
    if annotations.is_empty() {
        return None;
    }

    let label = find_step_object_node(object_tree, selected_object_id)
        .map(|node| node.label.clone())
        .unwrap_or_else(|| selected_object_id.into());

    Some(StepPmiInspectionSummary {
        object_id: selected_object_id.into(),
        label,
        entity_id,
        annotations,
    })
}

fn hidden_step_object_count(object_tree: &[ObjectNode]) -> usize {
    flatten_object_nodes(object_tree)
        .into_iter()
        .filter(|node| matches!(node.visibility, crate::domain::VisibilityState::Hidden))
        .count()
}

fn collect_step_representation_ids(assembly: &crate::domain::StepAssemblyNode) -> Vec<String> {
    let mut ids = assembly.tessellated_representation_ids.clone();
    for child in &assembly.children {
        ids.extend(collect_step_representation_ids(child));
    }
    ids.sort();
    ids.dedup();
    ids
}

fn find_step_object_node<'a>(nodes: &'a [ObjectNode], object_id: &str) -> Option<&'a ObjectNode> {
    for node in nodes {
        if node.object_id == object_id {
            return Some(node);
        }
        if let Some(found) = find_step_object_node(&node.children, object_id) {
            return Some(found);
        }
    }
    None
}

fn set_step_visibility_for_all(nodes: &mut [ObjectNode], visibility: crate::domain::VisibilityState) {
    for node in nodes {
        node.visibility = visibility.clone();
        set_step_visibility_for_all(&mut node.children, visibility.clone());
    }
}

fn set_step_subtree_visibility(
    nodes: &mut [ObjectNode],
    object_id: &str,
    visibility: crate::domain::VisibilityState,
) -> bool {
    for node in nodes {
        if node.object_id == object_id {
            node.visibility = visibility.clone();
            set_step_visibility_for_all(&mut node.children, visibility.clone());
            return true;
        }
        if set_step_subtree_visibility(&mut node.children, object_id, visibility.clone()) {
            return true;
        }
    }
    false
}

fn isolate_step_visibility(nodes: &mut [ObjectNode], object_id: &str) -> bool {
    let mut found = false;
    for node in nodes {
        let child_contains_target = isolate_step_visibility(&mut node.children, object_id);
        if node.object_id == object_id {
            node.visibility = crate::domain::VisibilityState::Visible;
            set_step_visibility_for_all(&mut node.children, crate::domain::VisibilityState::Visible);
            found = true;
        } else if child_contains_target {
            node.visibility = crate::domain::VisibilityState::Inherited;
            found = true;
        } else {
            node.visibility = crate::domain::VisibilityState::Hidden;
            set_step_visibility_for_all(&mut node.children, crate::domain::VisibilityState::Hidden);
        }
    }
    found
}

fn flatten_object_nodes(nodes: &[ObjectNode]) -> Vec<&ObjectNode> {
    let mut flattened = Vec::new();
    for node in nodes {
        flattened.push(node);
        flattened.extend(flatten_object_nodes(&node.children));
    }
    flattened
}

fn flatten_step_assemblies(
    assemblies: &[crate::domain::StepAssemblyNode],
) -> Vec<&crate::domain::StepAssemblyNode> {
    let mut flattened = Vec::new();
    for assembly in assemblies {
        flattened.push(assembly);
        flattened.extend(flatten_step_assemblies(&assembly.children));
    }
    flattened
}

fn find_step_assembly(
    entity_id: u64,
    assemblies: &[crate::domain::StepAssemblyNode],
) -> Option<&crate::domain::StepAssemblyNode> {
    for assembly in assemblies {
        if assembly.entity_id == entity_id {
            return Some(assembly);
        }
        if let Some(found) = find_step_assembly(entity_id, &assembly.children) {
            return Some(found);
        }
    }
    None
}

fn find_step_parent_entity_id(
    entity_id: u64,
    assemblies: &[crate::domain::StepAssemblyNode],
) -> Option<u64> {
    for assembly in assemblies {
        if assembly.children.iter().any(|child| child.entity_id == entity_id) {
            return Some(assembly.entity_id);
        }
        if let Some(found) = find_step_parent_entity_id(entity_id, &assembly.children) {
            return Some(found);
        }
    }
    None
}

fn project_step_points(positions: &[f32]) -> Vec<(f32, f32)> {
    let mut points = Vec::new();
    let mut index = 0usize;
    while index + 2 < positions.len() {
        let x = positions[index];
        let y = positions[index + 1];
        let z = positions[index + 2];
        points.push((18.0 + x * 22.0 + z * 6.0, 80.0 - y * 20.0 - z * 7.0));
        index += 3;
    }
    points
}

fn step_paths_from_points(points: &[(f32, f32)], indices: &[u32]) -> Vec<String> {
    let mut paths = Vec::new();
    let mut index = 0usize;
    while index + 2 < indices.len() {
        let Some(a) = points.get(indices[index] as usize) else {
            index += 3;
            continue;
        };
        let Some(b) = points.get(indices[index + 1] as usize) else {
            index += 3;
            continue;
        };
        let Some(c) = points.get(indices[index + 2] as usize) else {
            index += 3;
            continue;
        };
        paths.push(format!(
            "M {:.2} {:.2} L {:.2} {:.2} L {:.2} {:.2} Z",
            a.0, a.1, b.0, b.1, c.0, c.1
        ));
        index += 3;
    }
    paths
}

fn step_bounds_from_points(points: &[(f32, f32)]) -> (f32, f32, f32, f32) {
    let mut min_x = 20.0;
    let mut min_y = 20.0;
    let mut max_x = 80.0;
    let mut max_y = 80.0;
    if let Some(first) = points.first() {
        min_x = first.0;
        min_y = first.1;
        max_x = first.0;
        max_y = first.1;
        for point in points.iter().skip(1) {
            min_x = min_x.min(point.0);
            min_y = min_y.min(point.1);
            max_x = max_x.max(point.0);
            max_y = max_y.max(point.1);
        }
    }
    (min_x, max_x, min_y, max_y)
}

#[cfg(test)]
mod tests {
    use std::collections::HashMap;
    use std::path::PathBuf;

    use super::{
        ActivateWorkbenchRequest, AppState, CommandExecutionRequest, PreselectionRequest,
        SelectionModeRequest, SelectionRequest, ShellPanelMutationRequest,
        ShellSessionMutationRequest,
    };

    fn command_request(command_id: &str, target_object_id: Option<&str>) -> CommandExecutionRequest {
        CommandExecutionRequest {
            command_id: command_id.to_string(),
            document_id: "doc-demo-001".to_string(),
            target_object_id: target_object_id.map(str::to_string),
            arguments: HashMap::new(),
        }
    }

    fn temp_persistence_path(test_name: &str) -> PathBuf {
        let nonce = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("clock should be after epoch")
            .as_nanos();
        env::temp_dir().join(format!("asterforge-{test_name}-{nonce}.json"))
    }

    #[tokio::test]
    async fn rejects_unknown_selection() {
        let state = AppState::new();

        let result = state
            .set_selection(SelectionRequest {
                document_id: "doc-demo-001".to_string(),
                object_id: "does-not-exist".to_string(),
            })
            .await;

        assert!(result.is_none());
    }

    #[tokio::test]
    async fn step_data_is_not_exposed_for_non_step_document() {
        let state = AppState::new();
        let document_id = {
            let model = state.inner.read().await;
            model.document.document_id.clone()
        };

        let index = state
            .step_document_index(&document_id)
            .await
            .expect("STEP lookup should not fail");
        assert!(index.is_none());
    }

    #[tokio::test]
    async fn step_document_open_exposes_parsed_index_and_scene() {
        let state = AppState::new();
        let fixture_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../../fixtures/sample-ap242-assembly.stp");
        let opened = state
            .open_document(fixture_path.to_string_lossy().into_owned())
            .await;

        let index = state
            .step_document_index(&opened.document_id)
            .await
            .expect("STEP index should build")
            .expect("opened STEP document should expose STEP index");
        assert!(index
            .header
            .application_protocols
            .iter()
            .any(|protocol| protocol == "AP242"));
        assert!(!index.assemblies.is_empty());
        assert!(!index.tessellated_representations.is_empty());

        let scene = state
            .step_scene_bundle(&opened.document_id)
            .await
            .expect("STEP scene should build")
            .expect("opened STEP document should expose STEP scene");
        assert_eq!(scene.assemblies.len(), index.assemblies.len());
        assert!(!scene.semantic_pmi.is_empty());
    }

    #[tokio::test]
    async fn step_document_projects_tree_properties_and_viewport() {
        let state = AppState::new();
        let fixture_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../../fixtures/sample-ap242-assembly.stp");
        let opened = state
            .open_document(fixture_path.to_string_lossy().into_owned())
            .await;

        let tree = state
            .object_tree_proto(&opened.document_id)
            .await
            .expect("STEP object tree should be available");
        assert!(!tree.roots.is_empty());
        assert!(tree.roots[0].object_id.starts_with("step-entity-"));

        let selection = state
            .selection_state(&opened.document_id)
            .await
            .expect("STEP selection state should be available");
        assert_eq!(selection.current_mode, "object");
        assert_eq!(selection.available_modes[0].object_count, 4);
        assert!(!selection.available_modes[1].enabled);

        let properties = state
            .properties(&opened.document_id, &selection.selected_object_id)
            .await
            .expect("STEP properties should be available");
        assert!(properties
            .groups
            .iter()
            .any(|group| group.group_id == "step_record"));

        let viewport = state
            .viewport(&opened.document_id)
            .await
            .expect("STEP viewport should be available");
        assert!(viewport
            .scene
            .drawables
            .iter()
            .all(|drawable| drawable.object_id.starts_with("step-entity-")));
    }

    #[tokio::test]
    async fn step_command_catalog_exposes_step_specific_actions() {
        let state = AppState::new();
        let fixture_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../../fixtures/sample-ap242-assembly.stp");
        let opened = state
            .open_document(fixture_path.to_string_lossy().into_owned())
            .await;

        let catalog = state
            .command_catalog(&opened.document_id)
            .await
            .expect("STEP command catalog should be available");
        assert_eq!(catalog.workbench.workbench_id, "step");
        assert!(catalog.commands.iter().any(|command| command.command_id == "step.view_fit_all"));
        assert!(catalog.commands.iter().any(|command| command.command_id == "step.select_first_child"));
        assert!(catalog.commands.iter().any(|command| command.command_id == "step.inspect_pmi"));
        assert!(catalog.commands.iter().any(|command| command.command_id == "step.measure_selection"));
        assert!(catalog.commands.iter().any(|command| command.command_id == "step.hide_selection"));
        assert!(catalog.commands.iter().any(|command| command.command_id == "step.isolate_selection"));
        assert!(catalog.commands.iter().any(|command| command.command_id == "step.show_all"));
    }

    #[tokio::test]
    async fn step_commands_navigate_tree_and_focus_pmi_report() {
        let state = AppState::new();
        let fixture_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../../fixtures/sample-ap242-assembly.stp");
        let opened = state
            .open_document(fixture_path.to_string_lossy().into_owned())
            .await;

        let child = state
            .run_command(CommandExecutionRequest {
                command_id: "step.select_first_child".into(),
                document_id: opened.document_id.clone(),
                target_object_id: Some("step-entity-20".into()),
                arguments: HashMap::new(),
            })
            .await
            .expect("STEP child selection should return a response");
        assert!(child.accepted);

        let selection = state
            .selection_state(&opened.document_id)
            .await
            .expect("STEP selection state should be available");
        assert_eq!(selection.selected_object_id, "step-entity-10");

        let parent = state
            .run_command(CommandExecutionRequest {
                command_id: "step.select_parent".into(),
                document_id: opened.document_id.clone(),
                target_object_id: Some("step-entity-10".into()),
                arguments: HashMap::new(),
            })
            .await
            .expect("STEP parent selection should return a response");
        assert!(parent.accepted);

        let inspect = state
            .run_command(CommandExecutionRequest {
                command_id: "step.inspect_pmi".into(),
                document_id: opened.document_id.clone(),
                target_object_id: Some("step-entity-20".into()),
                arguments: HashMap::new(),
            })
            .await
            .expect("STEP PMI inspect should return a response");
        assert!(inspect.accepted);

        let shell = state
            .shell_snapshot(&opened.document_id)
            .await
            .expect("STEP shell snapshot should be available");
        assert_eq!(
            shell.layout
                .panels
                .iter()
                .find(|panel| panel.panel_id == "report_dock")
                .and_then(|panel| panel.active_tab.clone())
                .as_deref(),
            Some("report")
        );

        let events = state
            .events(&opened.document_id)
            .await
            .expect("STEP event stream should be available");
        assert!(events
            .iter()
            .any(|event| event.topic == "step_pmi_inspection" && event.message.contains("Housing / #20")));
        assert!(events.iter().any(|event| {
            event.topic == "step_pmi_annotation"
                && event.message.contains("protocol_summary")
                && event.message.contains("#20")
        }));
    }

    #[tokio::test]
    async fn step_commands_apply_explicit_target_before_execution() {
        let state = AppState::new();
        let fixture_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../../fixtures/sample-ap242-assembly.stp");
        let opened = state
            .open_document(fixture_path.to_string_lossy().into_owned())
            .await;

        state
            .set_selection(SelectionRequest {
                document_id: opened.document_id.clone(),
                object_id: "step-entity-20".into(),
            })
            .await
            .expect("root STEP selection should succeed");

        let response = state
            .run_command(CommandExecutionRequest {
                command_id: "step.select_parent".into(),
                document_id: opened.document_id.clone(),
                target_object_id: Some("step-entity-10".into()),
                arguments: HashMap::new(),
            })
            .await
            .expect("STEP parent selection should return a response");
        assert!(response.accepted);

        let selection = state
            .selection_state(&opened.document_id)
            .await
            .expect("STEP selection state should be available");
        assert_eq!(selection.selected_object_id, "step-entity-20");
    }

    #[tokio::test]
    async fn step_shell_snapshot_exposes_step_workbench_and_step_menu() {
        let state = AppState::new();
        let fixture_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../../fixtures/sample-ap242-assembly.stp");
        let opened = state
            .open_document(fixture_path.to_string_lossy().into_owned())
            .await;

        let shell = state
            .shell_snapshot(&opened.document_id)
            .await
            .expect("STEP shell snapshot should be available");
        assert_eq!(shell.workbench_catalog.active_workbench_id, "step");
        assert!(shell
            .menu_bar
            .menus
            .iter()
            .any(|menu| menu.menu_id == "step"));
        let view_menu = shell
            .menu_bar
            .menus
            .iter()
            .find(|menu| menu.menu_id == "view")
            .expect("STEP shell should expose a View menu");
        for command_id in [
            "step.view_reset",
            "step.view_fit_all",
            "step.view_iso",
            "step.view_front",
            "step.view_back",
            "step.view_right",
            "step.view_left",
            "step.view_top",
            "step.view_bottom",
        ] {
            assert!(view_menu
                .items
                .iter()
                .any(|item| item.command_id.as_deref() == Some(command_id)));
        }
        assert!(shell
            .toolbar_bands
            .bands
            .iter()
            .any(|band| band.band_id == "step"));
        let step_band = shell
            .toolbar_bands
            .bands
            .iter()
            .find(|band| band.band_id == "step")
            .expect("STEP shell should expose the STEP toolbar band");
        let view_toolbar = step_band
            .toolbars
            .iter()
            .find(|toolbar| toolbar.toolbar_id == "step-view")
            .expect("STEP shell should expose the STEP view toolbar");
        for command_id in [
            "step.view_reset",
            "step.view_fit_all",
            "step.view_iso",
            "step.view_front",
            "step.view_back",
            "step.view_right",
            "step.view_left",
            "step.view_top",
            "step.view_bottom",
        ] {
            assert!(view_toolbar
                .items
                .iter()
                .any(|item| item.command_id.as_deref() == Some(command_id)));
        }
    }

    #[tokio::test]
    async fn step_document_rejects_non_object_selection_modes() {
        let state = AppState::new();
        let fixture_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../../fixtures/sample-ap242-assembly.stp");
        let opened = state
            .open_document(fixture_path.to_string_lossy().into_owned())
            .await;

        let rejected = state
            .set_selection_mode(SelectionModeRequest {
                document_id: opened.document_id.clone(),
                mode_id: "feature".into(),
            })
            .await;
        assert!(rejected.is_none());

        let selection = state
            .selection_state(&opened.document_id)
            .await
            .expect("STEP selection state should remain available");
        assert_eq!(selection.current_mode, "object");
    }

    #[tokio::test]
    async fn step_document_rejects_non_step_workbench_activation() {
        let state = AppState::new();
        let fixture_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../../fixtures/sample-ap242-assembly.stp");
        let opened = state
            .open_document(fixture_path.to_string_lossy().into_owned())
            .await;

        let rejected = state
            .activate_workbench(ActivateWorkbenchRequest {
                document_id: opened.document_id.clone(),
                workbench_id: "partdesign".into(),
            })
            .await;
        assert!(rejected.is_none());

        let accepted = state
            .activate_workbench(ActivateWorkbenchRequest {
                document_id: opened.document_id.clone(),
                workbench_id: "step".into(),
            })
            .await
            .expect("STEP workbench activation should succeed");
        assert_eq!(accepted.workbench, "STEP Inspection");

        let shell = state
            .shell_snapshot(&opened.document_id)
            .await
            .expect("STEP shell snapshot should remain available");
        assert_eq!(shell.workbench_catalog.active_workbench_id, "step");
    }

    #[tokio::test]
    async fn selection_mode_retargets_to_matching_object_kind() {
        let state = AppState::new();

        let mode = state
            .set_selection_mode(SelectionModeRequest {
                document_id: "doc-demo-001".to_string(),
                mode_id: "sketch".to_string(),
            })
            .await
            .expect("sketch selection mode should succeed");

        assert_eq!(mode.current_mode, "sketch");
        assert_eq!(mode.selected_object_id, "sketch-001");
    }

    #[tokio::test]
    async fn incompatible_selection_requests_follow_active_selection_mode() {
        let state = AppState::new();

        state
            .set_selection_mode(SelectionModeRequest {
                document_id: "doc-demo-001".to_string(),
                mode_id: "feature".to_string(),
            })
            .await
            .expect("feature selection mode should succeed");

        let selection = state
            .set_selection(SelectionRequest {
                document_id: "doc-demo-001".to_string(),
                object_id: "body-001".to_string(),
            })
            .await
            .expect("selection should be normalized");

        assert_eq!(selection.selected_object_id, "pad-001");
    }

    #[tokio::test]
    async fn preselection_tracks_only_objects_allowed_by_active_mode() {
        let state = AppState::new();

        state
            .set_selection_mode(SelectionModeRequest {
                document_id: "doc-demo-001".to_string(),
                mode_id: "sketch".to_string(),
            })
            .await
            .expect("sketch mode should succeed");

        let preselection = state
            .set_preselection(PreselectionRequest {
                document_id: "doc-demo-001".to_string(),
                object_id: Some("pad-001".to_string()),
            })
            .await
            .expect("preselection request should respond");
        assert!(preselection.object_id.is_none());

        let sketch_preselection = state
            .set_preselection(PreselectionRequest {
                document_id: "doc-demo-001".to_string(),
                object_id: Some("sketch-001".to_string()),
            })
            .await
            .expect("preselection request should respond");
        assert_eq!(sketch_preselection.object_id.as_deref(), Some("sketch-001"));
    }

    #[tokio::test]
    async fn step_visibility_commands_filter_tree_and_viewport() {
        let state = AppState::new();
        let fixture_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../../fixtures/sample-ap242-assembly.stp");
        let opened = state
            .open_document(fixture_path.to_string_lossy().into_owned())
            .await;

        let isolate = state
            .run_command(CommandExecutionRequest {
                command_id: "step.isolate_selection".into(),
                document_id: opened.document_id.clone(),
                target_object_id: Some("step-entity-20".into()),
                arguments: HashMap::new(),
            })
            .await
            .expect("STEP isolate command should return a response");
        assert!(isolate.accepted);

        {
            let model = state.inner.read().await;
            assert_eq!(model.object_tree[0].visibility, crate::domain::VisibilityState::Visible);
            assert_eq!(model.object_tree[1].visibility, crate::domain::VisibilityState::Hidden);
        }

        let isolated_viewport = state
            .viewport(&opened.document_id)
            .await
            .expect("isolated STEP viewport should be available");
        assert_eq!(isolated_viewport.scene.drawables.len(), 1);
        assert_eq!(isolated_viewport.scene.drawables[0].object_id, "step-entity-20");

        let hide = state
            .run_command(CommandExecutionRequest {
                command_id: "step.hide_selection".into(),
                document_id: opened.document_id.clone(),
                target_object_id: Some("step-entity-20".into()),
                arguments: HashMap::new(),
            })
            .await
            .expect("STEP hide command should return a response");
        assert!(hide.accepted);

        let diagnostics = state
            .diagnostics(&opened.document_id)
            .await
            .expect("STEP diagnostics should be available");
        assert!(!diagnostics.selection.visible_in_viewport);

        let hidden_catalog = state
            .command_catalog(&opened.document_id)
            .await
            .expect("STEP command catalog should remain available");
        assert!(hidden_catalog
            .commands
            .iter()
            .find(|command| command.command_id == "step.show_all")
            .expect("show all command should exist")
            .enabled);

        let restore = state
            .run_command(CommandExecutionRequest {
                command_id: "step.show_all".into(),
                document_id: opened.document_id.clone(),
                target_object_id: None,
                arguments: HashMap::new(),
            })
            .await
            .expect("STEP show all command should return a response");
        assert!(restore.accepted);

        let restored_viewport = state
            .viewport(&opened.document_id)
            .await
            .expect("restored STEP viewport should be available");
        assert_eq!(restored_viewport.scene.drawables.len(), 2);

        let task_panel = state
            .task_panel(&opened.document_id)
            .await
            .expect("STEP task panel should remain available");
        assert!(task_panel
            .suggested_commands
            .iter()
            .any(|command| command == "step.hide_selection"));
    }

    #[tokio::test]
    async fn sketch_creation_requires_body_selection() {
        let state = AppState::new();

        let response = state
            .run_command(command_request("partdesign.new_sketch", Some("pad-001")))
            .await
            .expect("command should return a response");

        assert!(!response.accepted);
        assert!(response.status_message.contains("body to be selected"));
    }

    #[tokio::test]
    async fn commands_apply_explicit_target_before_partdesign_execution() {
        let state = AppState::new();

        state
            .set_selection(SelectionRequest {
                document_id: "doc-demo-001".to_string(),
                object_id: "pad-001".to_string(),
            })
            .await
            .expect("pad selection should succeed");

        let response = state
            .run_command(CommandExecutionRequest {
                command_id: "partdesign.new_sketch".to_string(),
                document_id: "doc-demo-001".to_string(),
                target_object_id: Some("body-001".to_string()),
                arguments: HashMap::from([("sketch_label".to_string(), "TargetedSketch".to_string())]),
            })
            .await
            .expect("new sketch command should respond");
        assert!(response.accepted);

        let selection = state
            .selection_state("doc-demo-001")
            .await
            .expect("selection state should remain available");
        assert_eq!(selection.selected_object_type, "Sketcher::SketchObject");

        let history = state
            .feature_history("doc-demo-001")
            .await
            .expect("history should remain available");
        assert!(history.entries.iter().any(|entry| entry.label == "TargetedSketch"));
    }

    #[tokio::test]
    async fn create_sketch_then_pad_updates_history() {
        let state = AppState::new();

        let selected = state
            .set_selection(SelectionRequest {
                document_id: "doc-demo-001".to_string(),
                object_id: "body-001".to_string(),
            })
            .await
            .expect("body selection should succeed");
        assert_eq!(selected.selected_object_id, "body-001");

        let mut sketch_args = HashMap::new();
        sketch_args.insert("sketch_label".to_string(), "SketchQA".to_string());
        let sketch_response = state
            .run_command(CommandExecutionRequest {
                command_id: "partdesign.new_sketch".to_string(),
                document_id: "doc-demo-001".to_string(),
                target_object_id: Some("body-001".to_string()),
                arguments: sketch_args,
            })
            .await
            .expect("new sketch command should respond");
        assert!(sketch_response.accepted);

        let history_after_sketch = state
            .feature_history("doc-demo-001")
            .await
            .expect("history should be available");
        let new_sketch = history_after_sketch
            .entries
            .iter()
            .find(|entry| entry.label == "SketchQA")
            .expect("new sketch should exist in history");
        assert_eq!(new_sketch.object_type, "Sketcher::SketchObject");

        let pad_response = state
            .run_command(CommandExecutionRequest {
                command_id: "partdesign.pad".to_string(),
                document_id: "doc-demo-001".to_string(),
                target_object_id: Some(new_sketch.object_id.clone()),
                arguments: HashMap::from([("length_mm".to_string(), "15.5".to_string())]),
            })
            .await
            .expect("pad command should respond");
        assert!(pad_response.accepted);

        let history_after_pad = state
            .feature_history("doc-demo-001")
            .await
            .expect("history should be available");
        assert!(history_after_pad
            .entries
            .iter()
            .any(|entry| entry.object_type == "PartDesign::Pad" && entry.source_object_id.as_deref() == Some(new_sketch.object_id.as_str())));
    }

    #[tokio::test]
    async fn undo_reverts_pad_creation() {
        let state = AppState::new();

        // Select body, create sketch, then pad
        state
            .set_selection(SelectionRequest {
                document_id: "doc-demo-001".to_string(),
                object_id: "body-001".to_string(),
            })
            .await
            .expect("body selection should succeed");

        let mut sketch_args = HashMap::new();
        sketch_args.insert("sketch_label".to_string(), "UndoSketch".to_string());
        state
            .run_command(CommandExecutionRequest {
                command_id: "partdesign.new_sketch".to_string(),
                document_id: "doc-demo-001".to_string(),
                target_object_id: None,
                arguments: sketch_args,
            })
            .await
            .expect("sketch creation should succeed");

        let pad_response = state
            .run_command(CommandExecutionRequest {
                command_id: "partdesign.pad".to_string(),
                document_id: "doc-demo-001".to_string(),
                target_object_id: None,
                arguments: HashMap::from([("length_mm".to_string(), "20.0".to_string())]),
            })
            .await
            .expect("pad creation should succeed");
        assert!(pad_response.accepted);

        // Now undo the pad
        let undo_response = state
            .run_command(command_request("document.undo", None))
            .await
            .expect("undo should return a response");
        assert!(undo_response.accepted);
        assert_eq!(undo_response.status_message, "Undo applied");

        // The pad's source sketch should still be selected (state before pad creation)
        let history = state
            .feature_history("doc-demo-001")
            .await
            .expect("history should be available");

        // After undo, the pad should no longer exist in history
        assert!(
            !history
                .entries
                .iter()
                .any(|e| e.object_type == "PartDesign::Pad" && e.source_object_id.as_deref() == Some("sketch-002")),
            "pad should be removed after undo"
        );

        // Redo should bring it back
        let redo_response = state
            .run_command(command_request("document.redo", None))
            .await
            .expect("redo should return a response");
        assert!(redo_response.accepted);

        let history_after_redo = state
            .feature_history("doc-demo-001")
            .await
            .expect("history should be available");
        assert!(
            history_after_redo
                .entries
                .iter()
                .any(|e| e.object_type == "PartDesign::Pad" && e.source_object_id.as_deref() == Some("sketch-002")),
            "pad should reappear after redo"
        );
    }

    #[tokio::test]
    async fn richer_command_arguments_persist_into_properties_and_catalog() {
        let state = AppState::new();

        state
            .set_selection(SelectionRequest {
                document_id: "doc-demo-001".to_string(),
                object_id: "body-001".to_string(),
            })
            .await
            .expect("body selection should succeed");

        let sketch_response = state
            .run_command(CommandExecutionRequest {
                command_id: "partdesign.new_sketch".to_string(),
                document_id: "doc-demo-001".to_string(),
                target_object_id: None,
                arguments: HashMap::from([
                    ("sketch_label".to_string(), "PlaneSketch".to_string()),
                    ("reference_plane".to_string(), "XZ".to_string()),
                ]),
            })
            .await
            .expect("sketch creation should succeed");
        assert!(sketch_response.accepted);

        let sketch_properties = state
            .properties("doc-demo-001", "sketch-002")
            .await
            .expect("sketch properties should exist");
        let sketch_definition = sketch_properties
            .groups
            .iter()
            .find(|group| group.group_id == "definition")
            .expect("sketch definition group should exist");
        assert!(sketch_definition
            .properties
            .iter()
            .any(|property| property.property_id == "reference_plane" && property.value_preview == "XZ"));

        let pad_response = state
            .run_command(CommandExecutionRequest {
                command_id: "partdesign.pad".to_string(),
                document_id: "doc-demo-001".to_string(),
                target_object_id: None,
                arguments: HashMap::from([
                    ("length_mm".to_string(), "18.0".to_string()),
                    ("midplane".to_string(), "true".to_string()),
                ]),
            })
            .await
            .expect("pad creation should succeed");
        assert!(pad_response.accepted);

        let pad_properties = state
            .properties("doc-demo-001", "pad-002")
            .await
            .expect("pad properties should exist");
        let pad_definition = pad_properties
            .groups
            .iter()
            .find(|group| group.group_id == "definition")
            .expect("pad definition group should exist");
        assert!(pad_definition
            .properties
            .iter()
            .any(|property| property.property_id == "midplane" && property.value_preview == "true"));

        let catalog = state
            .command_catalog("doc-demo-001")
            .await
            .expect("command catalog should exist");
        let edit_pad = catalog
            .commands
            .iter()
            .find(|command| command.command_id == "partdesign.edit_pad")
            .expect("edit pad command should exist");
        assert!(edit_pad
            .arguments
            .iter()
            .any(|argument| argument.argument_id == "midplane" && argument.default_value.as_deref() == Some("true")));
    }

    #[tokio::test]
    async fn sketch_metadata_surfaces_in_task_panel_and_properties() {
        let state = AppState::new();

        state
            .set_selection(SelectionRequest {
                document_id: "doc-demo-001".to_string(),
                object_id: "body-001".to_string(),
            })
            .await
            .expect("body selection should succeed");

        state
            .run_command(CommandExecutionRequest {
                command_id: "partdesign.new_sketch".to_string(),
                document_id: "doc-demo-001".to_string(),
                target_object_id: None,
                arguments: HashMap::from([
                    ("sketch_label".to_string(), "StatusSketch".to_string()),
                    ("reference_plane".to_string(), "YZ".to_string()),
                ]),
            })
            .await
            .expect("sketch creation should succeed");

        let task_panel = state
            .task_panel("doc-demo-001")
            .await
            .expect("task panel should exist");
        let constraint_section = task_panel
            .sections
            .iter()
            .find(|section| section.section_id == "constraints")
            .expect("constraints section should exist");
        assert!(constraint_section
            .rows
            .iter()
            .any(|row| row.label == "Constraint state" && row.value == "4 constraints, solver pending"));
        assert!(constraint_section
            .rows
            .iter()
            .any(|row| row.label == "Profile readiness" && row.value == "Open profile"));

        let properties = state
            .properties("doc-demo-001", "sketch-002")
            .await
            .expect("properties should exist");
        let sketch_group = properties
            .groups
            .iter()
            .find(|group| group.group_id == "constraints")
            .expect("constraints group should exist");
        assert!(sketch_group
            .properties
            .iter()
            .any(|property| property.property_id == "constraint_count" && property.value_preview == "4 constraints, solver pending"));
    }

    #[tokio::test]
    async fn task_panel_descriptions_follow_bridge_workflow_guidance() {
        let state = AppState::new();

        state
            .set_selection(SelectionRequest {
                document_id: "doc-demo-001".to_string(),
                object_id: "pad-001".to_string(),
            })
            .await
            .expect("pad selection should succeed");

        let pad_panel = state
            .task_panel("doc-demo-001")
            .await
            .expect("pad task panel should exist");
        assert!(pad_panel.description.contains("One-sided pad"));
        assert!(pad_panel
            .sections
            .iter()
            .flat_map(|section| section.rows.iter())
            .any(|row| row.label == "View" && row.value == "Inspect one-sided growth"));

        let suppression_response = state
            .run_command(CommandExecutionRequest {
                command_id: "model.toggle_suppression".to_string(),
                document_id: "doc-demo-001".to_string(),
                target_object_id: Some("pad-001".to_string()),
                arguments: HashMap::new(),
            })
            .await
            .expect("suppression command should respond");
        assert!(suppression_response.accepted);

        let dependency_panel = state
            .task_panel("doc-demo-001")
            .await
            .expect("dependency task panel should exist");
        assert!(dependency_panel.description.contains("manually suppressed"));
        assert!(dependency_panel
            .sections
            .iter()
            .flat_map(|section| section.rows.iter())
            .any(|row| row.label == "State" && row.value == "Suppressed"));
    }

    #[tokio::test]
    async fn step_measure_command_updates_task_panel_and_shell_focus() {
        let state = AppState::new();
        let fixture_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../../fixtures/sample-ap242-assembly.stp");
        let opened = state
            .open_document(fixture_path.to_string_lossy().into_owned())
            .await;

        let response = state
            .run_command(CommandExecutionRequest {
                command_id: "step.measure_selection".into(),
                document_id: opened.document_id.clone(),
                target_object_id: Some("step-entity-20".into()),
                arguments: HashMap::new(),
            })
            .await
            .expect("STEP measure command should return a response");
        assert!(response.accepted);
        assert!(response.status_message.contains("Measured Housing"));

        let task_panel = state
            .task_panel(&opened.document_id)
            .await
            .expect("STEP task panel should be available");
        let measurement_section = task_panel
            .sections
            .iter()
            .find(|section| section.section_id == "measurement")
            .expect("measurement section should exist");
        assert!(measurement_section
            .rows
            .iter()
            .any(|row| row.label == "Measured node" && row.value == "Housing"));
        assert!(measurement_section
            .rows
            .iter()
            .any(|row| row.label == "Z span" && row.value == "1.00"));

        let shell = state
            .shell_snapshot(&opened.document_id)
            .await
            .expect("STEP shell snapshot should be available");
        assert_eq!(
            shell.layout
                .panels
                .iter()
                .find(|panel| panel.panel_id == "combo_view")
                .and_then(|panel| panel.active_tab.clone())
                .as_deref(),
            Some("tasks")
        );
        assert_eq!(
            shell.layout
                .panels
                .iter()
                .find(|panel| panel.panel_id == "report_dock")
                .and_then(|panel| panel.active_tab.clone())
                .as_deref(),
            Some("report")
        );
        let measurement_overlay = shell
            .inspection
            .as_ref()
            .and_then(|inspection| inspection.step_measurement.as_ref())
            .expect("shell inspection measurement payload should exist");
        assert_eq!(measurement_overlay.object_id, "step-entity-20");
        assert!((measurement_overlay.span_z - 1.0).abs() < f32::EPSILON);

        let events = state
            .events(&opened.document_id)
            .await
            .expect("STEP event stream should be available");
        assert!(events.iter().any(|event| {
            event.topic == "step_measurement"
                && event.object_id.as_deref() == Some("step-entity-20")
                && event.message.contains("Measured Housing at 1.00 x 1.00 x 1.00")
        }));

        let catalog = state
            .command_catalog(&opened.document_id)
            .await
            .expect("STEP command catalog should remain available");
        assert!(catalog.workbench.mode.contains("live measurement"));
    }

    #[tokio::test]
    async fn step_selection_focus_updates_backend_viewport_camera() {
        let state = AppState::new();
        let fixture_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../../fixtures/sample-ap242-assembly.stp");
        let opened = state
            .open_document(fixture_path.to_string_lossy().into_owned())
            .await;

        let before = state
            .viewport(&opened.document_id)
            .await
            .expect("STEP viewport should be available before focus");

        let response = state
            .run_command(CommandExecutionRequest {
                command_id: "selection.focus".into(),
                document_id: opened.document_id.clone(),
                target_object_id: Some("step-entity-20".into()),
                arguments: HashMap::new(),
            })
            .await
            .expect("STEP focus command should return a response");
        assert!(response.accepted);
        assert!(response.status_message.contains("Focused STEP selection"));

        let after = state
            .viewport(&opened.document_id)
            .await
            .expect("STEP viewport should be available after focus");

        assert_eq!(after.selected_object_id, "step-entity-20");
        assert_ne!(after.scene.camera_target, before.scene.camera_target);
        assert_ne!(after.scene.camera_eye, before.scene.camera_eye);
        assert_eq!(after.scene.camera_target, [0.5, 0.5, 0.5]);
    }

    #[tokio::test]
    async fn step_view_preset_commands_update_backend_viewport_camera() {
        let state = AppState::new();
        let fixture_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../../fixtures/sample-ap242-assembly.stp");
        let opened = state
            .open_document(fixture_path.to_string_lossy().into_owned())
            .await;

        let focus_response = state
            .run_command(CommandExecutionRequest {
                command_id: "selection.focus".into(),
                document_id: opened.document_id.clone(),
                target_object_id: Some("step-entity-20".into()),
                arguments: HashMap::new(),
            })
            .await
            .expect("STEP focus command should return a response");
        assert!(focus_response.accepted);

        let focused = state
            .viewport(&opened.document_id)
            .await
            .expect("STEP viewport should be available after focus");

        let preset_response = state
            .run_command(CommandExecutionRequest {
                command_id: "step.view_front".into(),
                document_id: opened.document_id.clone(),
                target_object_id: Some("step-entity-20".into()),
                arguments: HashMap::new(),
            })
            .await
            .expect("STEP front view command should return a response");
        assert!(preset_response.accepted);

        let after = state
            .viewport(&opened.document_id)
            .await
            .expect("STEP viewport should be available after preset");

        assert_eq!(after.scene.camera_target, focused.scene.camera_target);
        assert_ne!(after.scene.camera_eye, focused.scene.camera_eye);
        assert!((after.scene.camera_eye[0] - focused.scene.camera_target[0]).abs() < 0.001);
        assert!((after.scene.camera_eye[1] - focused.scene.camera_target[1]).abs() < 0.001);
        assert!(after.scene.camera_eye[2] > focused.scene.camera_target[2]);
    }

    #[tokio::test]
    async fn step_reset_view_command_restores_default_viewport_camera() {
        let state = AppState::new();
        let fixture_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../../fixtures/sample-ap242-assembly.stp");
        let opened = state
            .open_document(fixture_path.to_string_lossy().into_owned())
            .await;

        let _ = state
            .run_command(CommandExecutionRequest {
                command_id: "selection.focus".into(),
                document_id: opened.document_id.clone(),
                target_object_id: Some("step-entity-20".into()),
                arguments: HashMap::new(),
            })
            .await
            .expect("STEP focus command should return a response");

        let response = state
            .run_command(CommandExecutionRequest {
                command_id: "step.view_reset".into(),
                document_id: opened.document_id.clone(),
                target_object_id: Some("step-entity-20".into()),
                arguments: HashMap::new(),
            })
            .await
            .expect("STEP reset view command should return a response");
        assert!(response.accepted);
        assert!(response.status_message.contains("Reset STEP view"));

        let after = state
            .viewport(&opened.document_id)
            .await
            .expect("STEP viewport should be available after reset");
        assert_eq!(after.scene.camera_eye, [2.6, 2.2, 3.1]);
        assert_eq!(after.scene.camera_target, [0.8, 0.7, 0.4]);
    }

    #[tokio::test]
    async fn step_fit_all_command_frames_visible_step_geometry() {
        let state = AppState::new();
        let fixture_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../../fixtures/sample-ap242-assembly.stp");
        let opened = state
            .open_document(fixture_path.to_string_lossy().into_owned())
            .await;

        let response = state
            .run_command(CommandExecutionRequest {
                command_id: "step.view_fit_all".into(),
                document_id: opened.document_id.clone(),
                target_object_id: Some("step-entity-20".into()),
                arguments: HashMap::new(),
            })
            .await
            .expect("STEP fit-all command should return a response");
        assert!(response.accepted);
        assert!(response.status_message.contains("Fit all visible STEP geometry"));

        let after = state
            .viewport(&opened.document_id)
            .await
            .expect("STEP viewport should be available after fit all");
        assert_eq!(after.scene.camera_target, [1.25, 0.5, 0.5]);
        assert!(after.scene.camera_eye[0] > after.scene.camera_target[0]);
        assert!(after.scene.camera_eye[1] > after.scene.camera_target[1]);
        assert!(after.scene.camera_eye[2] > after.scene.camera_target[2]);
    }

    #[tokio::test]
    async fn step_inspect_pmi_populates_task_panel_drill_down() {
        let state = AppState::new();
        let fixture_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../../fixtures/sample-ap242-assembly.stp");
        let opened = state
            .open_document(fixture_path.to_string_lossy().into_owned())
            .await;

        let response = state
            .run_command(CommandExecutionRequest {
                command_id: "step.inspect_pmi".into(),
                document_id: opened.document_id.clone(),
                target_object_id: Some("step-entity-20".into()),
                arguments: HashMap::new(),
            })
            .await
            .expect("STEP PMI inspect should return a response");
        assert!(response.accepted);
        assert!(response.status_message.contains("Loaded PMI inspection"));

        let task_panel = state
            .task_panel(&opened.document_id)
            .await
            .expect("STEP task panel should be available");
        let pmi_section = task_panel
            .sections
            .iter()
            .find(|section| section.section_id == "pmi")
            .expect("PMI section should exist");
        assert!(pmi_section
            .rows
            .iter()
            .any(|row| row.label == "Inspected node" && row.value == "Housing"));
        assert!(pmi_section
            .rows
            .iter()
            .any(|row| row.label == "Annotations" && row.value == "2"));

        let annotation_sections: Vec<_> = task_panel
            .sections
            .iter()
            .filter(|section| section.section_id.starts_with("pmi-annotation-"))
            .collect();
        assert_eq!(annotation_sections.len(), 2);
        assert!(annotation_sections.iter().any(|section| {
            section
                .rows
                .iter()
                .any(|row| row.label == "Type" && row.value == "protocol_summary")
        }));
        assert!(annotation_sections.iter().any(|section| {
            section.rows.iter().any(|row| {
                row.label == "Text"
                    && (row.value.contains("Protocols: AP242")
                        || row.value.contains("references outer shell"))
            })
        }));

        let shell = state
            .shell_snapshot(&opened.document_id)
            .await
            .expect("STEP shell snapshot should be available");
        assert_eq!(
            shell.layout
                .panels
                .iter()
                .find(|panel| panel.panel_id == "combo_view")
                .and_then(|panel| panel.active_tab.clone())
                .as_deref(),
            Some("tasks")
        );

        let shell = state
            .shell_snapshot(&opened.document_id)
            .await
            .expect("STEP shell snapshot should be available");
        let inspected_overlay = shell
            .inspection
            .as_ref()
            .and_then(|inspection| inspection.step_pmi.as_ref())
            .expect("shell inspection PMI payload should exist");
        assert_eq!(inspected_overlay.object_id, "step-entity-20");
        assert!(inspected_overlay
            .target_object_ids
            .iter()
            .any(|object_id| object_id == "step-entity-20"));
    }

    #[tokio::test]
    async fn command_response_includes_viewport_diff() {
        let state = AppState::new();

        // Select body, create a sketch → viewport should change
        state
            .set_selection(SelectionRequest {
                document_id: "doc-demo-001".to_string(),
                object_id: "body-001".to_string(),
            })
            .await
            .expect("body selection should succeed");

        let response = state
            .run_command(CommandExecutionRequest {
                command_id: "partdesign.new_sketch".to_string(),
                document_id: "doc-demo-001".to_string(),
                target_object_id: None,
                arguments: HashMap::from([("sketch_label".to_string(), "DiffSketch".to_string())]),
            })
            .await
            .expect("sketch creation should succeed");
        assert!(response.accepted);

        let diff = response
            .viewport_diff
            .expect("accepted mutating command should include viewport diff");
        assert!(
            !diff.added.is_empty() || !diff.modified.is_empty(),
            "diff should contain changes after sketch creation"
        );
    }

    #[tokio::test]
    async fn command_catalog_exposes_backend_argument_metadata() {
        let state = AppState::new();

        state
            .set_selection(SelectionRequest {
                document_id: "doc-demo-001".to_string(),
                object_id: "body-001".to_string(),
            })
            .await
            .expect("body selection should succeed");

        let catalog = state
            .command_catalog("doc-demo-001")
            .await
            .expect("command catalog should be available");
        let create_sketch = catalog
            .commands
            .iter()
            .find(|command| command.command_id == "partdesign.new_sketch")
            .expect("create sketch command should exist");

        assert!(create_sketch.enabled);
        assert_eq!(create_sketch.arguments.len(), 2);
        assert_eq!(create_sketch.arguments[0].argument_id, "sketch_label");
        assert_eq!(create_sketch.arguments[0].default_value.as_deref(), Some("Sketch"));
        assert_eq!(create_sketch.arguments[1].argument_id, "reference_plane");
        assert_eq!(create_sketch.arguments[1].default_value.as_deref(), Some("XY"));
    }

    #[tokio::test]
    async fn command_catalog_tracks_undo_and_redo_availability() {
        let state = AppState::new();

        let initial_catalog = state
            .command_catalog("doc-demo-001")
            .await
            .expect("initial catalog should be available");
        let initial_undo = initial_catalog
            .commands
            .iter()
            .find(|command| command.command_id == "document.undo")
            .expect("undo command should exist");
        let initial_redo = initial_catalog
            .commands
            .iter()
            .find(|command| command.command_id == "document.redo")
            .expect("redo command should exist");
        assert!(!initial_undo.enabled);
        assert!(!initial_redo.enabled);

        state
            .set_selection(SelectionRequest {
                document_id: "doc-demo-001".to_string(),
                object_id: "body-001".to_string(),
            })
            .await
            .expect("body selection should succeed");
        state
            .run_command(CommandExecutionRequest {
                command_id: "partdesign.new_sketch".to_string(),
                document_id: "doc-demo-001".to_string(),
                target_object_id: None,
                arguments: HashMap::from([("sketch_label".to_string(), "Undoable".to_string())]),
            })
            .await
            .expect("sketch creation should succeed");

        let after_change_catalog = state
            .command_catalog("doc-demo-001")
            .await
            .expect("catalog after change should be available");
        assert!(after_change_catalog
            .commands
            .iter()
            .find(|command| command.command_id == "document.undo")
            .expect("undo command should exist")
            .enabled);
        assert!(!after_change_catalog
            .commands
            .iter()
            .find(|command| command.command_id == "document.redo")
            .expect("redo command should exist")
            .enabled);
    }

    #[tokio::test]
    async fn shell_snapshot_exposes_layout_and_dynamic_command_state() {
        let state = AppState::new();

        let initial_snapshot = state
            .shell_snapshot("doc-demo-001")
            .await
            .expect("shell snapshot should be available");
        assert_eq!(initial_snapshot.workbench_catalog.active_workbench_id, "partdesign");
        assert_eq!(initial_snapshot.document.document_id, "doc-demo-001");
        assert_eq!(
            initial_snapshot
                .layout
                .panels
                .iter()
                .find(|panel| panel.panel_id == "report_dock")
                .and_then(|panel| panel.active_tab.as_deref()),
            Some("report")
        );

        let initial_undo = initial_snapshot
            .toolbar_bands
            .bands
            .iter()
            .flat_map(|band| band.toolbars.iter())
            .flat_map(|toolbar| toolbar.items.iter())
            .find(|item| item.command_id.as_deref() == Some("document.undo"))
            .expect("undo toolbar item should exist");
        assert_eq!(initial_undo.enabled, Some(false));

        state
            .set_selection(SelectionRequest {
                document_id: "doc-demo-001".to_string(),
                object_id: "body-001".to_string(),
            })
            .await
            .expect("body selection should succeed");
        state
            .run_command(CommandExecutionRequest {
                command_id: "partdesign.new_sketch".to_string(),
                document_id: "doc-demo-001".to_string(),
                target_object_id: None,
                arguments: HashMap::from([("sketch_label".to_string(), "ShellSketch".to_string())]),
            })
            .await
            .expect("sketch creation should succeed");

        let updated_snapshot = state
            .shell_snapshot("doc-demo-001")
            .await
            .expect("shell snapshot should remain available");
        let updated_undo = updated_snapshot
            .toolbar_bands
            .bands
            .iter()
            .flat_map(|band| band.toolbars.iter())
            .flat_map(|toolbar| toolbar.items.iter())
            .find(|item| item.command_id.as_deref() == Some("document.undo"))
            .expect("undo toolbar item should exist");
        assert_eq!(updated_undo.enabled, Some(true));
    }

    #[tokio::test]
    async fn activate_workbench_updates_document_and_backend_owned_shell_state() {
        let state = AppState::new();

        let updated_document = state
            .activate_workbench(ActivateWorkbenchRequest {
                document_id: "doc-demo-001".to_string(),
                workbench_id: "sketcher".to_string(),
            })
            .await
            .expect("workbench activation should succeed");

        assert_eq!(updated_document.workbench, "Sketcher");

        let shell_snapshot = state
            .shell_snapshot("doc-demo-001")
            .await
            .expect("shell snapshot should remain available");
        assert_eq!(shell_snapshot.workbench_catalog.active_workbench_id, "sketcher");

        let command_catalog = state
            .command_catalog("doc-demo-001")
            .await
            .expect("command catalog should be available");
        assert_eq!(command_catalog.workbench.display_name, "Sketcher");
        assert!(!command_catalog
            .commands
            .iter()
            .any(|command| command.command_id == "partdesign.new_sketch"));

        let task_panel = state
            .task_panel("doc-demo-001")
            .await
            .expect("task panel should be available");
        assert_eq!(task_panel.title, "Sketcher Workspace");
    }

    #[tokio::test]
    async fn shell_snapshot_tracks_recent_documents_sessions_and_panel_tabs() {
        let state = AppState::new();

        state
            .open_document("C:/models/fixture-one.FCStd".to_string())
            .await;
        state
            .update_shell_panel(ShellPanelMutationRequest {
                document_id: "doc-demo-001".to_string(),
                panel_id: "combo_view".to_string(),
                active_tab: Some("tasks".to_string()),
                visible: None,
                size_hint: None,
            })
            .await
            .expect("combo panel update should succeed");

        let shell_snapshot = state
            .shell_snapshot("doc-demo-001")
            .await
            .expect("shell snapshot should be available");
        assert_eq!(shell_snapshot.recent_documents[0].file_path, "C:/models/fixture-one.FCStd");
        assert_eq!(shell_snapshot.workspace_sessions[0].file_path, "C:/models/fixture-one.FCStd");
        assert_eq!(
            shell_snapshot.workspace_sessions[0].selection_mode.as_deref(),
            Some("object")
        );
        assert_eq!(
            shell_snapshot.workspace_sessions[0].combo_view_tab.as_deref(),
            Some("tasks")
        );
        assert_eq!(
            shell_snapshot.workspace_sessions[0].bottom_dock_tab.as_deref(),
            Some("report")
        );
        assert_eq!(shell_snapshot.workspace_sessions[0].combo_view_visible, Some(true));
        assert_eq!(shell_snapshot.workspace_sessions[0].report_dock_visible, Some(true));
        assert_eq!(shell_snapshot.workspace_sessions[0].combo_view_size_hint, Some(0.28));
        assert_eq!(shell_snapshot.workspace_sessions[0].report_dock_size_hint, Some(0.24));
        assert_eq!(
            shell_snapshot
                .layout
                .panels
                .iter()
                .find(|panel| panel.panel_id == "combo_view")
                .and_then(|panel| panel.active_tab.as_deref()),
            Some("tasks")
        );
    }

    #[tokio::test]
    async fn shell_panel_mutation_updates_visibility_and_size_hints() {
        let state = AppState::new();

        let shell_snapshot = state
            .update_shell_panel(ShellPanelMutationRequest {
                document_id: "doc-demo-001".to_string(),
                panel_id: "report_dock".to_string(),
                active_tab: None,
                visible: Some(false),
                size_hint: Some(0.31),
            })
            .await
            .expect("report dock mutation should succeed");

        let report_dock = shell_snapshot
            .layout
            .panels
            .iter()
            .find(|panel| panel.panel_id == "report_dock")
            .expect("report dock panel should exist");
        assert!(!report_dock.visible);
        assert_eq!(report_dock.size_hint, Some(0.31));
    }

    #[tokio::test]
    async fn shell_snapshot_exposes_extension_compatibility_state() {
        let state = AppState::new();

        let shell_snapshot = state
            .shell_snapshot("doc-demo-001")
            .await
            .expect("shell snapshot should be available");

        assert_eq!(shell_snapshot.extension_compatibility.title, "Extension Compatibility");
        assert!(shell_snapshot
            .extension_compatibility
            .summary
            .contains("AddonManager"));
        assert!(shell_snapshot
            .extension_compatibility
            .lanes
            .iter()
            .any(|lane| lane.lane_id == "macros" && lane.status == "staging"));
        assert_eq!(
            shell_snapshot
                .menu_bar
                .menus
                .iter()
                .find(|menu| menu.menu_id == "macro")
                .and_then(|menu| menu.items.first())
                .and_then(|item| item.command_id.as_deref()),
            Some("shell.show_extensions_manager")
        );
    }

    #[tokio::test]
    async fn command_catalog_exposes_extension_commands() {
        let state = AppState::new();

        let command_catalog = state
            .command_catalog("doc-demo-001")
            .await
            .expect("command catalog should be available");

        assert!(command_catalog
            .commands
            .iter()
            .any(|command| command.command_id == "extensions.refresh_inventory" && command.group == "Extensions"));
        assert!(command_catalog
            .commands
            .iter()
            .any(|command| command.command_id == "extensions.review_external_workbenches" && command.enabled));
        assert!(command_catalog
            .commands
            .iter()
            .any(|command| command.command_id == "extensions.run_inventory_entry" && command.enabled));
    }

    #[tokio::test]
    async fn extension_refresh_command_runs_through_backend_dispatch() {
        let state = AppState::new();

        let response = state
            .run_command(command_request("extensions.refresh_inventory", None))
            .await
            .expect("extension refresh command should return a response");

        assert!(response.accepted);
        assert!(response.status_message.contains("Refreshed extension compatibility inventory"));

        let shell_snapshot = state
            .shell_snapshot("doc-demo-001")
            .await
            .expect("shell snapshot should be available");
        assert!(shell_snapshot
            .extension_compatibility
            .summary
            .contains("Last refresh completed via backend command runtime"));
        assert!(shell_snapshot
            .extension_compatibility
            .lanes
            .iter()
            .any(|lane| lane.lane_id == "macros" && lane.status == "inventory-ready"));
        assert!(shell_snapshot
            .extension_compatibility
            .lanes
            .iter()
            .find(|lane| lane.lane_id == "macros")
            .map(|lane| lane.inventory_entries.iter().any(|entry| entry.trust_state == "reviewed"))
            .unwrap_or(false));
        assert!(shell_snapshot
            .extension_compatibility
            .lanes
            .iter()
            .find(|lane| lane.lane_id == "macros")
            .map(|lane| lane.inventory_entries.iter().any(|entry| {
                entry.entry_id == "macro:auto_dimensioning"
                    && entry.action_command_id.as_deref() == Some("extensions.run_inventory_entry")
            }))
            .unwrap_or(false));
    }

    #[tokio::test]
    async fn external_workbench_review_command_updates_extension_lane_state() {
        let state = AppState::new();

        let response = state
            .run_command(command_request("extensions.review_external_workbenches", None))
            .await
            .expect("external workbench review command should return a response");

        assert!(response.accepted);
        assert!(response
            .status_message
            .contains("Opened external workbench compatibility review lane"));

        let shell_snapshot = state
            .shell_snapshot("doc-demo-001")
            .await
            .expect("shell snapshot should be available");
        assert_eq!(
            shell_snapshot
                .layout
                .panels
                .iter()
                .find(|panel| panel.panel_id == "report_dock")
                .and_then(|panel| panel.active_tab.as_deref()),
            Some("extensions")
        );
        assert!(shell_snapshot
            .extension_compatibility
            .lanes
            .iter()
            .any(|lane| lane.lane_id == "external-workbenches" && lane.status == "reviewing"));
    }

    #[tokio::test]
    async fn extension_reviewed_inventory_entry_runs_through_backend_dispatch() {
        let state = AppState::new();

        state
            .run_command(command_request("extensions.refresh_inventory", None))
            .await
            .expect("extension refresh command should return a response");

        let response = state
            .run_command(CommandExecutionRequest {
                command_id: "extensions.run_inventory_entry".into(),
                document_id: "doc-demo-001".into(),
                target_object_id: None,
                arguments: HashMap::from([("entry_id".into(), "macro:auto_dimensioning".into())]),
            })
            .await
            .expect("reviewed inventory entry command should return a response");

        assert!(response.accepted);
        assert!(response.status_message.contains("AutoDimensioning.FCMacro"));

        let events = state
            .events("doc-demo-001")
            .await
            .expect("extension event stream should be available");
        assert!(events.iter().any(|event| {
            event.topic == "extension_inventory_execution"
                && event.message.contains("AutoDimensioning.FCMacro")
                && event.message.contains("Reviewed fixture bundle")
                && event.message.contains("test launcher success")
                && event.message.contains("ASTERFORGE_MACRO_OK:auto_dimensioning")
        }));

        let shell_snapshot = state
            .shell_snapshot("doc-demo-001")
            .await
            .expect("shell snapshot should be available");
        assert!(shell_snapshot
            .extension_compatibility
            .lanes
            .iter()
            .flat_map(|lane| lane.inventory_entries.iter())
            .any(|entry| {
                entry.entry_id == "macro:auto_dimensioning"
                    && entry.last_run_kind.as_deref() == Some("success")
                    && entry
                        .last_run_status
                        .as_deref()
                        == Some("test launcher success")
                    && entry.last_run_level.as_deref() == Some("info")
                    && entry.last_run_detail.as_deref() == Some("ASTERFORGE_MACRO_OK:auto_dimensioning")
            }));
    }

    #[tokio::test]
    async fn extension_reviewed_inventory_entry_failure_persists_status() {
        let state = AppState::new();

        state
            .run_command(command_request("extensions.refresh_inventory", None))
            .await
            .expect("extension refresh command should return a response");

        let response = state
            .run_command(CommandExecutionRequest {
                command_id: "extensions.run_inventory_entry".into(),
                document_id: "doc-demo-001".into(),
                target_object_id: None,
                arguments: HashMap::from([("entry_id".into(), "macro:broken_reviewed".into())]),
            })
            .await
            .expect("reviewed failing inventory entry command should return a response");

        assert!(!response.accepted);
        assert!(response.status_message.contains("BrokenReviewedFixture.FCMacro"));

        let events = state
            .events("doc-demo-001")
            .await
            .expect("extension event stream should be available");
        assert!(events.iter().any(|event| {
            event.topic == "extension_inventory_execution"
                && event.level == "warning"
                && event.message.contains("BrokenReviewedFixture.FCMacro")
                && event.message.contains("test launcher failure")
        }));

        let shell_snapshot = state
            .shell_snapshot("doc-demo-001")
            .await
            .expect("shell snapshot should be available");
        assert!(shell_snapshot
            .extension_compatibility
            .lanes
            .iter()
            .flat_map(|lane| lane.inventory_entries.iter())
            .any(|entry| {
                entry.entry_id == "macro:broken_reviewed"
                    && entry.last_run_kind.as_deref() == Some("launcher-failed")
                    && entry
                        .last_run_status
                        .as_deref()
                        == Some("Launcher failed")
                    && entry.last_run_level.as_deref() == Some("warning")
                    && entry.last_run_detail.as_deref() == Some("test launcher failure")
            }));
    }

    #[tokio::test]
    async fn extension_unreviewed_inventory_entry_persists_policy_rejection() {
        let state = AppState::new();

        state
            .run_command(command_request("extensions.refresh_inventory", None))
            .await
            .expect("extension refresh command should return a response");

        let response = state
            .run_command(CommandExecutionRequest {
                command_id: "extensions.run_inventory_entry".into(),
                document_id: "doc-demo-001".into(),
                target_object_id: None,
                arguments: HashMap::from([("entry_id".into(), "macro:legacy_sheetmetal".into())]),
            })
            .await
            .expect("unreviewed inventory entry command should return a response");

        assert!(!response.accepted);
        assert!(response.status_message.contains("LegacySheetMetalTools.FCMacro"));

        let events = state
            .events("doc-demo-001")
            .await
            .expect("extension event stream should be available");
        assert!(events.iter().any(|event| {
            event.topic == "extension_inventory_execution"
                && event.level == "warning"
                && event.message.contains("LegacySheetMetalTools.FCMacro")
                && event.message.contains("not reviewed and shell-ready yet")
        }));

        let shell_snapshot = state
            .shell_snapshot("doc-demo-001")
            .await
            .expect("shell snapshot should be available");
        assert!(shell_snapshot
            .extension_compatibility
            .lanes
            .iter()
            .flat_map(|lane| lane.inventory_entries.iter())
            .any(|entry| {
                entry.entry_id == "macro:legacy_sheetmetal"
                    && entry.last_run_kind.as_deref() == Some("policy-rejected")
                    && entry.last_run_status.as_deref() == Some("Blocked by trust policy")
                    && entry.last_run_level.as_deref() == Some("warning")
                    && entry.last_run_detail.as_deref()
                        == Some(
                            "Reviewed backend execution only runs shell-ready entries that have passed explicit trust review.",
                        )
            }));
    }
}
