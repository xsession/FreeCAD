use std::{collections::HashMap, sync::Arc};

pub use asterforge_command_core::CommandExecutionRequest;
use asterforge_document_core::{DocumentState, DocumentSummary};
use asterforge_freecad_bridge::{open_document_snapshot, BridgeDocumentSnapshot, BridgeStatus, UndoStack};
use asterforge_protocol_types::asterforge::protocol::v1::{
    BootPayload as ProtoBootPayload, CommandCatalogResponse as ProtoCommandCatalogResponse,
    CommandInvocation, CommandReply, DiagnosticsResponse as ProtoDiagnosticsResponse,
    EventEnvelope as ProtoEventEnvelope,
    FeatureHistoryResponse as ProtoFeatureHistoryResponse, JobStatusResponse as ProtoJobStatusResponse,
    ObjectTreeResponse as ProtoObjectTreeResponse,
    PreselectionRequest as ProtoPreselectionRequest,
    PreselectionState as ProtoPreselectionState,
    SelectionModeRequest as ProtoSelectionModeRequest, SelectionRef, SelectionReply,
    SelectionState as ProtoSelectionState, PropertyResponse as ProtoPropertyResponse,
    TaskPanelResponse as ProtoTaskPanelResponse, ViewportResponse as ProtoViewportResponse,
};
use tokio::sync::RwLock;

use super::protocol::{
    boot_payload_proto_from_http, command_reply_from_http, preselection_state_proto_from_http,
    proto_command_catalog_from_http, proto_diagnostics_from_http, proto_document_ref_from_http,
    proto_event_from_http, proto_feature_history_from_http, proto_jobs_from_http,
    proto_object_node_from_http, proto_properties_from_http, proto_task_panel_from_http,
    proto_viewport_from_http, selection_reply_from_http, selection_state_proto_from_http,
};
use super::command_runtime;

use crate::domain::{
    bridge_object_state, document_evaluation_state_from_bridge, document_graph_from_bridge,
    document_summary_from_bridge, feature_history_from_bridge,
    find_bridge_child, find_pad_length_mm, object_tree_from_bridge, sample_boot_report, sample_bridge_status,
    preselection_state_from_bridge, selectable_object_ids_for_mode, selection_state_from_bridge,
    sketch_constraint_summary,
    command_catalog_from_bridge, sample_event_stream, sample_property_groups, task_panel_from_bridge,
    viewport_from_bridge, BackendEvent, BootReport, CommandCatalogResponse,
    DiagnosticsResponse, FeatureHistoryResponse, ObjectNode, PropertyGroup,
    JobStageEntry, JobStatusEntry, JobStatusResponse, PreselectionStateResponse,
    PropertyResponse, SelectionStateResponse, TaskPanelResponse,
    ViewportDiffResponse, ViewportResponse, diagnostics_from_bridge,
};

#[derive(Clone)]
pub struct AppState {
    inner: Arc<RwLock<AppModel>>,
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
        let snapshot = open_document_snapshot(None);
        let bridge_status = sample_bridge_status();
        let document = document_state_from_bridge(&snapshot, &bridge_status);
        let object_tree = object_tree_from_bridge(&snapshot);
        let selected_object_id = snapshot.selected_object_id.clone();
        let properties_by_object = build_property_map(&snapshot, &object_tree);

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
            })),
        }
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
        self.document.history().clone()
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
    }

    fn normalize_selection_for_mode(
        &self,
        requested_object_id: &str,
        selection_mode: &str,
    ) -> Option<String> {
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
