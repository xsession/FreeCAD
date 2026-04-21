use std::{collections::HashMap, sync::Arc};

use asterforge_freecad_bridge::{
    compute_viewport_diff, create_pad_from_selected_sketch, create_pocket_from_selected_sketch,
    create_sketch_in_body, open_document_snapshot, resume_full_history,
    rollback_history_to_selected, update_selected_pad_profile,
    update_selected_pocket_profile, BridgeDocumentSnapshot, BridgeStatus,
    toggle_selected_suppression, UndoStack,
};
use tokio::sync::RwLock;

use crate::domain::{
    bridge_object_state, document_summary_from_bridge, feature_history_from_bridge,
    find_bridge_child, find_pad_length_mm, object_tree_from_bridge, sample_boot_report, sample_bridge_status,
    preselection_state_from_bridge, selectable_object_ids_for_mode, selection_state_from_bridge,
    sketch_constraint_summary,
    command_catalog_from_bridge, sample_event_stream, sample_property_groups, task_panel_from_bridge,
    viewport_from_bridge, viewport_diff_response, BackendEvent, BootReport, CommandCatalogResponse,
    DiagnosticsResponse, DocumentSummary, FeatureHistoryResponse, ObjectNode, PropertyGroup,
    JobStageEntry, JobStatusEntry, JobStatusResponse, PreselectionStateResponse,
    PropertyResponse, SelectionStateResponse, TaskPanelResponse, ViewportDiffResponse,
    ViewportResponse, diagnostics_from_bridge,
};

#[derive(Clone)]
pub struct AppState {
    inner: Arc<RwLock<AppModel>>,
}

#[derive(Debug, Clone)]
struct AppModel {
    boot_report: BootReport,
    bridge_status: BridgeStatus,
    bridge_snapshot: BridgeDocumentSnapshot,
    document: DocumentSummary,
    object_tree: Vec<ObjectNode>,
    selection_mode: String,
    preselected_object_id: Option<String>,
    selected_object_id: String,
    jobs: Vec<JobStatusEntry>,
    properties_by_object: HashMap<String, Vec<PropertyGroup>>,
    events: Vec<BackendEvent>,
    undo_stack: UndoStack,
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
pub struct PreselectionRequest {
    pub document_id: String,
    pub object_id: Option<String>,
}

#[derive(Debug, Clone, serde::Deserialize)]
pub struct CommandExecutionRequest {
    pub command_id: String,
    pub document_id: String,
    pub target_object_id: Option<String>,
    pub arguments: HashMap<String, String>,
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct CommandExecutionResponse {
    pub command_id: String,
    pub accepted: bool,
    pub status_message: String,
    pub document_dirty: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub viewport_diff: Option<ViewportDiffResponse>,
}

impl AppState {
    pub fn new() -> Self {
        let snapshot = open_document_snapshot(None);
        let document = document_summary_from_bridge(&snapshot);
        let object_tree = object_tree_from_bridge(&snapshot);
        let selected_object_id = snapshot.selected_object_id.clone();
        let properties_by_object = build_property_map(&snapshot, &object_tree);

        Self {
            inner: Arc::new(RwLock::new(AppModel {
                boot_report: sample_boot_report(),
                bridge_status: sample_bridge_status(),
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
            })),
        }
    }

    pub async fn snapshot(&self) -> AppSnapshot {
        let model = self.inner.read().await;
        AppSnapshot {
            boot_report: model.boot_report.clone(),
            document: model.document.clone(),
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
            document: model.document.clone(),
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

        model.bridge_snapshot.selected_object_id = next_selection.clone();
        model.selected_object_id = next_selection.clone();
        model.preselected_object_id = None;
        model.sync_from_snapshot();
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

        Some(SelectionResponse {
            selected_object_id: next_selection,
        })
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

        let next_selection =
            model.normalize_selection_for_mode(&model.selected_object_id, &request.mode_id)?;

        model.selection_mode = request.mode_id;
        model.bridge_snapshot.selected_object_id = next_selection.clone();
        model.selected_object_id = next_selection.clone();
        model.preselected_object_id = None;
        model.sync_from_snapshot();
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

        Some(model.selection_state())
    }

    pub async fn open_document(&self, file_path: String) -> DocumentSummary {
        let snapshot = open_document_snapshot(Some(&file_path));

        let mut model = self.inner.write().await;
        model.bridge_snapshot = snapshot;
        model.preselected_object_id = None;
        model.sync_from_snapshot();
        let document_id = model.document.document_id.clone();
        let next_job_id = format!("job-{}-document.open", model.jobs.len() + 1);
        let open_stages = vec![
            JobStageEntry {
                stage_id: "queued".into(),
                label: "Queued by shell".into(),
                state: "completed".into(),
                progress_percent: 15,
            },
            JobStageEntry {
                stage_id: "read_document".into(),
                label: "Read FCStd payload".into(),
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

        model.document.clone()
    }

    pub async fn object_tree(&self, document_id: &str) -> Option<Vec<ObjectNode>> {
        let model = self.inner.read().await;
        (model.document.document_id == document_id).then(|| model.object_tree.clone())
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

    pub async fn events(&self, document_id: &str) -> Option<Vec<BackendEvent>> {
        let model = self.inner.read().await;
        (model.document.document_id == document_id).then(|| model.events.clone())
    }

    pub async fn viewport(&self, document_id: &str) -> Option<ViewportResponse> {
        let model = self.inner.read().await;
        (model.document.document_id == document_id).then(|| model.viewport())
    }

    pub async fn command_catalog(&self, document_id: &str) -> Option<CommandCatalogResponse> {
        let model = self.inner.read().await;
        (model.document.document_id == document_id).then(|| model.command_catalog())
    }

    pub async fn feature_history(&self, document_id: &str) -> Option<FeatureHistoryResponse> {
        let model = self.inner.read().await;
        (model.document.document_id == document_id).then(|| model.feature_history())
    }

    pub async fn task_panel(&self, document_id: &str) -> Option<TaskPanelResponse> {
        let model = self.inner.read().await;
        (model.document.document_id == document_id).then(|| model.task_panel())
    }

    pub async fn diagnostics(&self, document_id: &str) -> Option<DiagnosticsResponse> {
        let model = self.inner.read().await;
        (model.document.document_id == document_id).then(|| model.diagnostics())
    }

    pub async fn selection_state(&self, document_id: &str) -> Option<SelectionStateResponse> {
        let model = self.inner.read().await;
        (model.document.document_id == document_id).then(|| model.selection_state())
    }

    pub async fn preselection_state(
        &self,
        document_id: &str,
    ) -> Option<PreselectionStateResponse> {
        let model = self.inner.read().await;
        (model.document.document_id == document_id).then(|| model.preselection_state())
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
            let selectable_ids =
                selectable_object_ids_for_mode(&model.bridge_snapshot, &model.selection_mode);
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

    pub async fn jobs(&self, document_id: &str) -> Option<JobStatusResponse> {
        let model = self.inner.read().await;
        (model.document.document_id == document_id).then(|| model.jobs())
    }

    pub async fn run_command(
        &self,
        request: CommandExecutionRequest,
    ) -> Option<CommandExecutionResponse> {
        let mut model = self.inner.write().await;
        if model.document.document_id != request.document_id {
            return None;
        }

        let viewport_before = model.bridge_snapshot.viewport.clone();
        let target_object_id = request.target_object_id.clone();

        // Push undo before mutating commands (not for read-only or undo/redo)
        let is_mutating = !matches!(
            request.command_id.as_str(),
            "document.save" | "selection.focus" | "document.undo" | "document.redo"
        );
        if is_mutating {
            let snap_clone = model.bridge_snapshot.clone();
            model.undo_stack.push(&snap_clone);
        }

        let response = match request.command_id.as_str() {
            "document.save" => {
                model.document.dirty = false;
                model.bridge_snapshot.dirty = false;
                CommandExecutionResponse {
                    command_id: request.command_id.clone(),
                    accepted: true,
                    status_message: "Document marked as saved".into(),
                    document_dirty: model.document.dirty,
                    viewport_diff: None,
                }
            }
            "document.recompute" => {
                model.document.dirty = true;
                model.bridge_snapshot.dirty = true;
                CommandExecutionResponse {
                    command_id: request.command_id.clone(),
                    accepted: true,
                    status_message: "Recompute queued through bridge-backed mock backend".into(),
                    document_dirty: model.document.dirty,
                    viewport_diff: None,
                }
            }
            "selection.focus" => CommandExecutionResponse {
                command_id: request.command_id.clone(),
                accepted: true,
                status_message: "Selection focus requested".into(),
                document_dirty: model.document.dirty,
                viewport_diff: None,
            },
            "history.rollback_here" => {
                if let Some((object_id, sequence_index)) =
                    rollback_history_to_selected(&mut model.bridge_snapshot)
                {
                    model.sync_from_snapshot();
                    CommandExecutionResponse {
                        command_id: request.command_id.clone(),
                        accepted: true,
                        status_message: format!(
                            "Rolled back model evaluation to {} at step {}",
                            object_id, sequence_index
                        ),
                        document_dirty: model.document.dirty,
                        viewport_diff: None,
                    }
                } else {
                    CommandExecutionResponse {
                        command_id: request.command_id.clone(),
                        accepted: false,
                        status_message: "Rollback requires a selected history feature".into(),
                        document_dirty: model.document.dirty,
                        viewport_diff: None,
                    }
                }
            }
            "history.resume_full" => {
                if resume_full_history(&mut model.bridge_snapshot) {
                    model.sync_from_snapshot();
                    CommandExecutionResponse {
                        command_id: request.command_id.clone(),
                        accepted: true,
                        status_message: "Restored full feature history".into(),
                        document_dirty: model.document.dirty,
                        viewport_diff: None,
                    }
                } else {
                    CommandExecutionResponse {
                        command_id: request.command_id.clone(),
                        accepted: false,
                        status_message: "Feature history is already fully resumed".into(),
                        document_dirty: model.document.dirty,
                        viewport_diff: None,
                    }
                }
            }
            "model.toggle_suppression" => {
                if let Some((object_id, suppressed)) =
                    toggle_selected_suppression(&mut model.bridge_snapshot)
                {
                    model.sync_from_snapshot();
                    CommandExecutionResponse {
                        command_id: request.command_id.clone(),
                        accepted: true,
                        status_message: if suppressed {
                            format!("Suppressed {}", object_id)
                        } else {
                            format!("Unsuppressed {}", object_id)
                        },
                        document_dirty: model.document.dirty,
                        viewport_diff: None,
                    }
                } else {
                    CommandExecutionResponse {
                        command_id: request.command_id.clone(),
                        accepted: false,
                        status_message: "Suppression requires a non-body selection".into(),
                        document_dirty: model.document.dirty,
                        viewport_diff: None,
                    }
                }
            }
            "partdesign.new_sketch" => {
                let requested_label = request.arguments.get("sketch_label").map(String::as_str);
                let reference_plane = request.arguments.get("reference_plane").map(String::as_str);
                if create_sketch_in_body(&mut model.bridge_snapshot, requested_label, reference_plane).is_some() {
                    model.sync_from_snapshot();
                    CommandExecutionResponse {
                        command_id: request.command_id.clone(),
                        accepted: true,
                        status_message: format!(
                            "Created a new sketch in the active body on {}: {}",
                            reference_plane.unwrap_or("XY"),
                            model.selected_object_id,
                        ),
                        document_dirty: model.document.dirty,
                        viewport_diff: None,
                    }
                } else {
                    CommandExecutionResponse {
                        command_id: request.command_id.clone(),
                        accepted: false,
                        status_message: "Sketch creation requires the body to be selected".into(),
                        document_dirty: model.document.dirty,
                        viewport_diff: None,
                    }
                }
            }
            "partdesign.edit_pocket" => {
                let parsed_depth = request
                    .arguments
                    .get("depth_mm")
                    .and_then(|value| value.parse::<f32>().ok());
                let parsed_extent_mode = request.arguments.get("extent_mode").map(String::as_str);
                let normalized_depth = parsed_depth.filter(|value| *value > 0.0);
                let updated = update_selected_pocket_profile(
                    &mut model.bridge_snapshot,
                    normalized_depth,
                    parsed_extent_mode,
                );

                if model.selected_object_id.starts_with("pocket-") && updated.is_some() {
                    model.sync_from_snapshot();
                    CommandExecutionResponse {
                        command_id: request.command_id.clone(),
                        accepted: true,
                        status_message: format!(
                            "Updated {} to {:.2} mm depth ({})",
                            model.selected_object_id,
                            parsed_depth.unwrap_or(0.0),
                            parsed_extent_mode.unwrap_or("dimension")
                        ),
                        document_dirty: model.document.dirty,
                        viewport_diff: None,
                    }
                } else if model.selected_object_id.starts_with("pocket-") {
                    CommandExecutionResponse {
                        command_id: request.command_id.clone(),
                        accepted: false,
                        status_message: "Pocket editing requires a positive depth_mm argument".into(),
                        document_dirty: model.document.dirty,
                        viewport_diff: None,
                    }
                } else {
                    CommandExecutionResponse {
                        command_id: request.command_id.clone(),
                        accepted: false,
                        status_message: "Pocket editing requires an active pocket selection".into(),
                        document_dirty: model.document.dirty,
                        viewport_diff: None,
                    }
                }
            }
            "partdesign.edit_pad" => {
                let parsed_length = request
                    .arguments
                    .get("length_mm")
                    .and_then(|value| value.parse::<f32>().ok());
                let parsed_midplane = request
                    .arguments
                    .get("midplane")
                    .and_then(|value| parse_bool_flag(value));
                let normalized_length = parsed_length.filter(|value| *value > 0.0);
                let updated = update_selected_pad_profile(
                    &mut model.bridge_snapshot,
                    normalized_length,
                    parsed_midplane,
                );

                if updated.is_some() {
                    model.sync_from_snapshot();
                    CommandExecutionResponse {
                        command_id: request.command_id.clone(),
                        accepted: true,
                        status_message: format!(
                            "Updated {} to {:.2} mm ({})",
                            model.selected_object_id,
                            parsed_length.unwrap_or(0.0),
                            if parsed_midplane.unwrap_or(false) {
                                "symmetric"
                            } else {
                                "one-sided"
                            }
                        ),
                        document_dirty: model.document.dirty,
                        viewport_diff: None,
                    }
                } else if model.selected_object_id.starts_with("pad-") {
                    CommandExecutionResponse {
                        command_id: request.command_id.clone(),
                        accepted: false,
                        status_message: "Pad editing requires a positive length_mm argument".into(),
                        document_dirty: model.document.dirty,
                        viewport_diff: None,
                    }
                } else {
                    CommandExecutionResponse {
                        command_id: request.command_id.clone(),
                        accepted: false,
                        status_message: "Pad editing requires an active pad selection".into(),
                        document_dirty: model.document.dirty,
                        viewport_diff: None,
                    }
                }
            }
            "partdesign.pocket" => {
                let parsed_depth = request
                    .arguments
                    .get("depth_mm")
                    .and_then(|value| value.parse::<f32>().ok());
                let parsed_extent_mode = request.arguments.get("extent_mode").map(String::as_str);
                if create_pocket_from_selected_sketch(&mut model.bridge_snapshot, parsed_depth, parsed_extent_mode)
                    .is_some()
                {
                    model.sync_from_snapshot();
                    CommandExecutionResponse {
                        command_id: request.command_id.clone(),
                        accepted: true,
                        status_message: format!(
                            "Created a new pocket feature from the selected sketch ({})",
                            parsed_extent_mode.unwrap_or("dimension")
                        ),
                        document_dirty: model.document.dirty,
                        viewport_diff: None,
                    }
                } else {
                    CommandExecutionResponse {
                        command_id: request.command_id.clone(),
                        accepted: false,
                        status_message: "Pocket creation requires an active sketch selection".into(),
                        document_dirty: model.document.dirty,
                        viewport_diff: None,
                    }
                }
            }
            "partdesign.pad" => {
                let parsed_length = request
                    .arguments
                    .get("length_mm")
                    .and_then(|value| value.parse::<f32>().ok());
                let parsed_midplane = request
                    .arguments
                    .get("midplane")
                    .and_then(|value| parse_bool_flag(value))
                    .unwrap_or(false);
                let pad_length = parsed_length.filter(|value| *value > 0.0);

                if create_pad_from_selected_sketch(&mut model.bridge_snapshot, pad_length, Some("dimension"), parsed_midplane).is_some()
                {
                    model.sync_from_snapshot();
                    CommandExecutionResponse {
                        command_id: request.command_id.clone(),
                        accepted: true,
                        status_message: format!(
                            "Created a new pad feature from the selected sketch at {:.2} mm ({})",
                            pad_length.unwrap_or(12.0),
                            if parsed_midplane { "symmetric" } else { "one-sided" }
                        ),
                        document_dirty: model.document.dirty,
                        viewport_diff: None,
                    }
                } else {
                    CommandExecutionResponse {
                        command_id: request.command_id.clone(),
                        accepted: false,
                        status_message: "Pad creation requires an active sketch selection".into(),
                        document_dirty: model.document.dirty,
                        viewport_diff: None,
                    }
                }
            }
            "document.undo" => {
                let current_snap = model.bridge_snapshot.clone();
                if let Some(previous) = model.undo_stack.undo(&current_snap) {
                    model.bridge_snapshot = previous;
                    model.sync_from_snapshot();
                    CommandExecutionResponse {
                        command_id: request.command_id.clone(),
                        accepted: true,
                        status_message: "Undo applied".into(),
                        document_dirty: model.document.dirty,
                        viewport_diff: None,
                    }
                } else {
                    CommandExecutionResponse {
                        command_id: request.command_id.clone(),
                        accepted: false,
                        status_message: "Nothing to undo".into(),
                        document_dirty: model.document.dirty,
                        viewport_diff: None,
                    }
                }
            }
            "document.redo" => {
                let current_snap = model.bridge_snapshot.clone();
                if let Some(next) = model.undo_stack.redo(&current_snap) {
                    model.bridge_snapshot = next;
                    model.sync_from_snapshot();
                    CommandExecutionResponse {
                        command_id: request.command_id.clone(),
                        accepted: true,
                        status_message: "Redo applied".into(),
                        document_dirty: model.document.dirty,
                        viewport_diff: None,
                    }
                } else {
                    CommandExecutionResponse {
                        command_id: request.command_id.clone(),
                        accepted: false,
                        status_message: "Nothing to redo".into(),
                        document_dirty: model.document.dirty,
                        viewport_diff: None,
                    }
                }
            }
            _ => CommandExecutionResponse {
                command_id: request.command_id.clone(),
                accepted: false,
                status_message: format!("Unknown command: {}", request.command_id),
                document_dirty: model.document.dirty,
                viewport_diff: None,
            },
        };

        // If the command didn't accept, pop the undo snapshot we just pushed
        if !response.accepted && is_mutating {
            let snap_clone = model.bridge_snapshot.clone();
            model.undo_stack.undo(&snap_clone);
        }

        // Compute viewport diff for accepted mutating commands
        let viewport_diff = if response.accepted && is_mutating {
            let diff = compute_viewport_diff(&viewport_before, &model.bridge_snapshot.viewport);
            if diff.is_empty() {
                None
            } else {
                Some(viewport_diff_response(
                    &model.document.document_id,
                    &model.selected_object_id,
                    diff,
                ))
            }
        } else {
            None
        };

        let mut response = response;
        response.viewport_diff = viewport_diff;
        let job_title = request
            .command_id
            .split('.')
            .next_back()
            .map(|segment| segment.replace('_', " "))
            .unwrap_or_else(|| request.command_id.clone());
        let job_stages = job_stages_for_command(
            request.command_id.as_str(),
            response.accepted,
            response.viewport_diff.is_some(),
        );
        let job_entry = JobStatusEntry {
            job_id: format!("job-{}-{}", model.jobs.len() + 1, request.command_id),
            title: job_title,
            command_id: request.command_id.clone(),
            state: if response.accepted {
                "completed".into()
            } else {
                "failed".into()
            },
            progress_percent: if response.accepted { 100 } else { 0 },
            detail: response.status_message.clone(),
            object_id: target_object_id.clone(),
            stages: job_stages.clone(),
        };
        model.jobs.insert(0, job_entry);
        model.jobs.truncate(8);

        let document_id = model.document.document_id.clone();
        if response.accepted {
            for stage in job_stages {
                model.events.insert(
                    0,
                    BackendEvent {
                        topic: if stage.progress_percent < 100 {
                            "recompute_progress".into()
                        } else {
                            "task_status".into()
                        },
                        level: "info".into(),
                        message: format!("{}: {}", request.command_id, stage.label),
                        document_id: document_id.clone(),
                        object_id: target_object_id.clone(),
                    },
                );
            }
        }
        model.events.insert(
            0,
            BackendEvent {
                topic: if response.accepted {
                    "task_status".into()
                } else {
                    "backend_warning".into()
                },
                level: if response.accepted {
                    "info".into()
                } else {
                    "warning".into()
                },
                message: format!(
                    "{}{}",
                    response.status_message,
                    request
                        .arguments
                        .get("source")
                        .map(|source| format!(" via {}", source))
                        .unwrap_or_default()
                ),
                document_id: document_id.clone(),
                object_id: target_object_id,
            },
        );

        if response.accepted {
            let selected_object_id = model.selected_object_id.clone();
            model.events.insert(
                1,
                BackendEvent {
                    topic: "viewport_updated".into(),
                    level: "info".into(),
                    message: "Viewport scene invalidated for selected feature".into(),
                    document_id,
                    object_id: Some(selected_object_id),
                },
            );
        }

        Some(response)
    }
}

fn parse_bool_flag(value: &str) -> Option<bool> {
    match value {
        "true" | "1" | "yes" | "on" => Some(true),
        "false" | "0" | "no" | "off" => Some(false),
        _ => None,
    }
}

fn job_stages_for_command(
    command_id: &str,
    accepted: bool,
    viewport_changed: bool,
) -> Vec<JobStageEntry> {
    let final_state = if accepted { "completed" } else { "failed" };
    let final_progress = if accepted { 100 } else { 0 };
    let mut stages = vec![JobStageEntry {
        stage_id: "queued".into(),
        label: "Queued by shell".into(),
        state: if accepted { "completed".into() } else { "failed".into() },
        progress_percent: if accepted { 15 } else { 0 },
    }];

    match command_id {
        "document.recompute" => stages.push(JobStageEntry {
            stage_id: "bridge_recompute".into(),
            label: "Bridge recompute pass".into(),
            state: final_state.into(),
            progress_percent: if accepted { 70 } else { 0 },
        }),
        "document.save" => stages.push(JobStageEntry {
            stage_id: "persist_document".into(),
            label: "Persist document state".into(),
            state: final_state.into(),
            progress_percent: if accepted { 75 } else { 0 },
        }),
        "partdesign.new_sketch"
        | "partdesign.pad"
        | "partdesign.pocket"
        | "partdesign.edit_pad"
        | "partdesign.edit_pocket"
        | "model.toggle_suppression"
        | "history.rollback_here"
        | "history.resume_full" => stages.push(JobStageEntry {
            stage_id: "bridge_mutation".into(),
            label: "Apply bridge-backed mutation".into(),
            state: final_state.into(),
            progress_percent: if accepted { 68 } else { 0 },
        }),
        _ => stages.push(JobStageEntry {
            stage_id: "backend_dispatch".into(),
            label: "Backend dispatch".into(),
            state: final_state.into(),
            progress_percent: if accepted { 60 } else { 0 },
        }),
    }

    if viewport_changed {
        stages.push(JobStageEntry {
            stage_id: "viewport_sync".into(),
            label: "Viewport sync".into(),
            state: final_state.into(),
            progress_percent: if accepted { 90 } else { 0 },
        });
    }

    stages.push(JobStageEntry {
        stage_id: "completed".into(),
        label: if accepted {
            "Job completed".into()
        } else {
            "Job failed".into()
        },
        state: final_state.into(),
        progress_percent: final_progress,
    });
    stages
}

impl AppModel {
    fn viewport(&self) -> ViewportResponse {
        viewport_from_bridge(&self.bridge_snapshot, &self.selected_object_id)
    }

    fn command_catalog(&self) -> CommandCatalogResponse {
        command_catalog_from_bridge(
            &self.bridge_snapshot,
            &self.document.document_id,
            Some(&self.selected_object_id),
            self.undo_stack.can_undo(),
            self.undo_stack.can_redo(),
        )
    }

    fn feature_history(&self) -> FeatureHistoryResponse {
        feature_history_from_bridge(&self.bridge_snapshot)
    }

    fn task_panel(&self) -> TaskPanelResponse {
        task_panel_from_bridge(
            &self.bridge_snapshot,
            &self.document.document_id,
            Some(&self.selected_object_id),
            find_pad_length_mm(&self.bridge_snapshot, &self.selected_object_id),
            self.undo_stack.can_undo(),
            self.undo_stack.can_redo(),
        )
    }

    fn diagnostics(&self) -> DiagnosticsResponse {
        diagnostics_from_bridge(
            &self.bridge_snapshot,
            Some(&self.selected_object_id),
            &self.events,
            &self.bridge_status,
        )
    }

    fn selection_state(&self) -> SelectionStateResponse {
        selection_state_from_bridge(
            &self.bridge_snapshot,
            &self.selected_object_id,
            &self.selection_mode,
        )
    }

    fn preselection_state(&self) -> PreselectionStateResponse {
        preselection_state_from_bridge(
            &self.bridge_snapshot,
            self.preselected_object_id.as_deref(),
            &self.selection_mode,
            self.undo_stack.can_undo(),
            self.undo_stack.can_redo(),
        )
    }

    fn jobs(&self) -> JobStatusResponse {
        JobStatusResponse {
            document_id: self.document.document_id.clone(),
            jobs: self.jobs.clone(),
        }
    }

    fn sync_from_snapshot(&mut self) {
        self.document = document_summary_from_bridge(&self.bridge_snapshot);
        self.object_tree = object_tree_from_bridge(&self.bridge_snapshot);
        self.selected_object_id = self.bridge_snapshot.selected_object_id.clone();
        self.properties_by_object = build_property_map(&self.bridge_snapshot, &self.object_tree);
    }

    fn normalize_selection_for_mode(
        &self,
        requested_object_id: &str,
        selection_mode: &str,
    ) -> Option<String> {
        if selection_mode == "object" && self.properties_by_object.contains_key(requested_object_id) {
            return Some(requested_object_id.to_string());
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

#[cfg(test)]
mod tests {
    use std::collections::HashMap;

    use super::{
        AppState, CommandExecutionRequest, PreselectionRequest, SelectionModeRequest,
        SelectionRequest,
    };

    fn command_request(command_id: &str, target_object_id: Option<&str>) -> CommandExecutionRequest {
        CommandExecutionRequest {
            command_id: command_id.to_string(),
            document_id: "doc-demo-001".to_string(),
            target_object_id: target_object_id.map(str::to_string),
            arguments: HashMap::new(),
        }
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
}
