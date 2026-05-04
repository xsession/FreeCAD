use asterforge_protocol_types::asterforge::protocol::v1::ObjectTreeResponse as ProtoObjectTreeResponse;

use super::protocol::{proto_document_ref_from_http, proto_object_node_from_http};
use super::state_payloads::{AppSnapshot, BootPayload};
use super::state_types::AppModel;
use crate::domain::{
    BackendEvent, CommandCatalogResponse, DiagnosticsResponse, FeatureHistoryResponse,
    JobStatusResponse, PreselectionStateResponse, PropertyResponse, SelectionStateResponse,
    ShellSnapshot, TaskPanelResponse, ViewportResponse,
};

pub(super) fn snapshot(model: &AppModel) -> AppSnapshot {
    AppSnapshot {
        boot_report: model.boot_report.clone(),
        document: model.document.summary().clone(),
        object_tree: model.object_tree.clone(),
        events: model.events.clone(),
    }
}

pub(super) fn boot_payload(model: &AppModel) -> BootPayload {
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

pub(super) fn object_tree_proto(
    model: &AppModel,
    document_id: &str,
) -> Option<ProtoObjectTreeResponse> {
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

pub(super) fn properties(
    model: &AppModel,
    document_id: &str,
    object_id: &str,
) -> Option<PropertyResponse> {
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

pub(super) fn events(model: &AppModel, document_id: &str) -> Option<Vec<BackendEvent>> {
    (model.document.document_id == document_id).then(|| model.events.clone())
}

pub(super) fn viewport(model: &AppModel, document_id: &str) -> Option<ViewportResponse> {
    (model.document.document_id == document_id).then(|| model.viewport())
}

pub(super) fn command_catalog(
    model: &AppModel,
    document_id: &str,
) -> Option<CommandCatalogResponse> {
    (model.document.document_id == document_id).then(|| model.command_catalog())
}

pub(super) fn shell_snapshot(model: &AppModel, document_id: &str) -> Option<ShellSnapshot> {
    (model.document.document_id == document_id).then(|| model.shell_snapshot())
}

pub(super) fn feature_history(
    model: &AppModel,
    document_id: &str,
) -> Option<FeatureHistoryResponse> {
    (model.document.document_id == document_id).then(|| model.feature_history())
}

pub(super) fn task_panel(model: &AppModel, document_id: &str) -> Option<TaskPanelResponse> {
    (model.document.document_id == document_id).then(|| model.task_panel())
}

pub(super) fn diagnostics(
    model: &AppModel,
    document_id: &str,
) -> Option<DiagnosticsResponse> {
    (model.document.document_id == document_id).then(|| model.diagnostics())
}

pub(super) fn selection_state(
    model: &AppModel,
    document_id: &str,
) -> Option<SelectionStateResponse> {
    (model.document.document_id == document_id).then(|| model.selection_state())
}

pub(super) fn preselection_state(
    model: &AppModel,
    document_id: &str,
) -> Option<PreselectionStateResponse> {
    (model.document.document_id == document_id).then(|| model.preselection_state())
}

pub(super) fn jobs(model: &AppModel, document_id: &str) -> Option<JobStatusResponse> {
    (model.document.document_id == document_id).then(|| model.jobs())
}