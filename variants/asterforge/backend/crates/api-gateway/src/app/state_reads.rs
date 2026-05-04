use std::sync::Arc;

use asterforge_freecad_bridge::BridgeRuntimeDescriptor;
use asterforge_protocol_types::asterforge::protocol::v1::{
    BootPayload as ProtoBootPayload, CommandCatalogResponse as ProtoCommandCatalogResponse,
    DiagnosticsResponse as ProtoDiagnosticsResponse, EventEnvelope as ProtoEventEnvelope,
    FeatureHistoryResponse as ProtoFeatureHistoryResponse, JobStatusResponse as ProtoJobStatusResponse,
    ObjectTreeResponse as ProtoObjectTreeResponse, PreselectionState as ProtoPreselectionState,
    ShellSnapshot as ProtoShellSnapshot, SelectionState as ProtoSelectionState,
    PropertyResponse as ProtoPropertyResponse, TaskPanelResponse as ProtoTaskPanelResponse,
    ViewportResponse as ProtoViewportResponse,
};
use tokio::sync::RwLock;

use super::protocol::{
    boot_payload_proto_from_http, preselection_state_proto_from_http,
    proto_command_catalog_from_http, proto_diagnostics_from_http, proto_event_from_http,
    proto_feature_history_from_http, proto_jobs_from_http, proto_properties_from_http,
    proto_shell_snapshot_from_http, proto_task_panel_from_http, proto_viewport_from_http,
    selection_state_proto_from_http,
};
use super::services::AppServices;
use super::state_payloads::{AppSnapshot, BootPayload};
use super::state_types::AppModel;
use super::{state_query, state_step_cache};
use crate::domain::{
    BackendEvent, CommandCatalogResponse, DiagnosticsResponse, FeatureHistoryResponse,
    JobStatusResponse, PreselectionStateResponse, PropertyResponse, SelectionStateResponse,
    ShellSnapshot, StepDocumentIndex, StepSceneBundle, TaskPanelResponse, ViewportResponse,
};

pub(super) async fn snapshot(inner: &Arc<RwLock<AppModel>>) -> AppSnapshot {
    let model = inner.read().await;
    state_query::snapshot(&model)
}

pub(super) async fn bridge_runtime_descriptor(
    inner: &Arc<RwLock<AppModel>>,
    services: &Arc<AppServices>,
) -> BridgeRuntimeDescriptor {
    let model = inner.read().await;
    let correlation_id = services.next_correlation_id();
    services
        .bridge
        .describe_runtime_with_status(&correlation_id, &model.bridge_status)
}

pub(super) async fn boot_payload(inner: &Arc<RwLock<AppModel>>) -> BootPayload {
    let model = inner.read().await;
    state_query::boot_payload(&model)
}

pub(super) async fn boot_payload_proto(inner: &Arc<RwLock<AppModel>>) -> ProtoBootPayload {
    boot_payload_proto_from_http(boot_payload(inner).await)
}

pub(super) async fn object_tree_proto(
    inner: &Arc<RwLock<AppModel>>,
    document_id: &str,
) -> Option<ProtoObjectTreeResponse> {
    let model = inner.read().await;
    state_query::object_tree_proto(&model, document_id)
}

pub(super) async fn properties(
    inner: &Arc<RwLock<AppModel>>,
    document_id: &str,
    object_id: &str,
) -> Option<PropertyResponse> {
    let model = inner.read().await;
    state_query::properties(&model, document_id, object_id)
}

pub(super) async fn properties_proto(
    inner: &Arc<RwLock<AppModel>>,
    document_id: &str,
    object_id: &str,
) -> Option<ProtoPropertyResponse> {
    properties(inner, document_id, object_id)
        .await
        .map(proto_properties_from_http)
}

pub(super) async fn events(
    inner: &Arc<RwLock<AppModel>>,
    document_id: &str,
) -> Option<Vec<BackendEvent>> {
    let model = inner.read().await;
    state_query::events(&model, document_id)
}

pub(super) async fn events_proto(
    inner: &Arc<RwLock<AppModel>>,
    document_id: &str,
) -> Option<Vec<ProtoEventEnvelope>> {
    events(inner, document_id)
        .await
        .map(|events| events.into_iter().map(proto_event_from_http).collect())
}

pub(super) async fn viewport(
    inner: &Arc<RwLock<AppModel>>,
    document_id: &str,
) -> Option<ViewportResponse> {
    let model = inner.read().await;
    state_query::viewport(&model, document_id)
}

pub(super) async fn viewport_proto(
    inner: &Arc<RwLock<AppModel>>,
    document_id: &str,
) -> Option<ProtoViewportResponse> {
    viewport(inner, document_id).await.map(proto_viewport_from_http)
}

pub(super) async fn command_catalog(
    inner: &Arc<RwLock<AppModel>>,
    document_id: &str,
) -> Option<CommandCatalogResponse> {
    let model = inner.read().await;
    state_query::command_catalog(&model, document_id)
}

pub(super) async fn command_catalog_proto(
    inner: &Arc<RwLock<AppModel>>,
    document_id: &str,
) -> Option<ProtoCommandCatalogResponse> {
    command_catalog(inner, document_id)
        .await
        .map(proto_command_catalog_from_http)
}

pub(super) async fn shell_snapshot(
    inner: &Arc<RwLock<AppModel>>,
    document_id: &str,
) -> Option<ShellSnapshot> {
    let model = inner.read().await;
    state_query::shell_snapshot(&model, document_id)
}

pub(super) async fn shell_snapshot_proto(
    inner: &Arc<RwLock<AppModel>>,
    document_id: &str,
) -> Option<ProtoShellSnapshot> {
    shell_snapshot(inner, document_id)
        .await
        .map(proto_shell_snapshot_from_http)
}

pub(super) async fn feature_history(
    inner: &Arc<RwLock<AppModel>>,
    document_id: &str,
) -> Option<FeatureHistoryResponse> {
    let model = inner.read().await;
    state_query::feature_history(&model, document_id)
}

pub(super) async fn feature_history_proto(
    inner: &Arc<RwLock<AppModel>>,
    document_id: &str,
) -> Option<ProtoFeatureHistoryResponse> {
    feature_history(inner, document_id)
        .await
        .map(proto_feature_history_from_http)
}

pub(super) async fn task_panel(
    inner: &Arc<RwLock<AppModel>>,
    document_id: &str,
) -> Option<TaskPanelResponse> {
    let model = inner.read().await;
    state_query::task_panel(&model, document_id)
}

pub(super) async fn task_panel_proto(
    inner: &Arc<RwLock<AppModel>>,
    document_id: &str,
) -> Option<ProtoTaskPanelResponse> {
    task_panel(inner, document_id)
        .await
        .map(proto_task_panel_from_http)
}

pub(super) async fn diagnostics(
    inner: &Arc<RwLock<AppModel>>,
    document_id: &str,
) -> Option<DiagnosticsResponse> {
    let model = inner.read().await;
    state_query::diagnostics(&model, document_id)
}

pub(super) async fn diagnostics_proto(
    inner: &Arc<RwLock<AppModel>>,
    document_id: &str,
) -> Option<ProtoDiagnosticsResponse> {
    diagnostics(inner, document_id)
        .await
        .map(proto_diagnostics_from_http)
}

pub(super) async fn selection_state(
    inner: &Arc<RwLock<AppModel>>,
    document_id: &str,
) -> Option<SelectionStateResponse> {
    let model = inner.read().await;
    state_query::selection_state(&model, document_id)
}

pub(super) async fn selection_state_proto(
    inner: &Arc<RwLock<AppModel>>,
    document_id: &str,
) -> Option<ProtoSelectionState> {
    selection_state(inner, document_id)
        .await
        .map(selection_state_proto_from_http)
}

pub(super) async fn preselection_state(
    inner: &Arc<RwLock<AppModel>>,
    document_id: &str,
) -> Option<PreselectionStateResponse> {
    let model = inner.read().await;
    state_query::preselection_state(&model, document_id)
}

pub(super) async fn preselection_state_proto(
    inner: &Arc<RwLock<AppModel>>,
    document_id: &str,
) -> Option<ProtoPreselectionState> {
    preselection_state(inner, document_id)
        .await
        .map(preselection_state_proto_from_http)
}

pub(super) async fn jobs(
    inner: &Arc<RwLock<AppModel>>,
    document_id: &str,
) -> Option<JobStatusResponse> {
    let model = inner.read().await;
    state_query::jobs(&model, document_id)
}

pub(super) async fn jobs_proto(
    inner: &Arc<RwLock<AppModel>>,
    document_id: &str,
) -> Option<ProtoJobStatusResponse> {
    jobs(inner, document_id).await.map(proto_jobs_from_http)
}

pub(super) async fn step_document_index(
    inner: &Arc<RwLock<AppModel>>,
    document_id: &str,
) -> anyhow::Result<Option<StepDocumentIndex>> {
    let mut model = inner.write().await;
    state_step_cache::resolve_step_cache(&mut model, document_id)
        .map(|entry| entry.map(|entry| entry.document_index))
}

pub(super) async fn step_scene_bundle(
    inner: &Arc<RwLock<AppModel>>,
    document_id: &str,
) -> anyhow::Result<Option<StepSceneBundle>> {
    let mut model = inner.write().await;
    state_step_cache::resolve_step_cache(&mut model, document_id)
        .map(|entry| entry.map(|entry| entry.scene_bundle))
}