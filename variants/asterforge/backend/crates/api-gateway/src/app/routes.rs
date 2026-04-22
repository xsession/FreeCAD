use axum::{
    extract::{Path, State},
    http::StatusCode,
    routing::{get, post},
    Json, Router,
};
use asterforge_command_core::CommandExecutionRequest;
use asterforge_protocol_types::asterforge::protocol::v1::{
    CommandInvocation, PreselectionRequest as ProtoPreselectionRequest,
    SelectionModeRequest as ProtoSelectionModeRequest, SelectionRef,
};
use tracing::info;

use crate::domain::{
    BackendEvent, CommandCatalogResponse, DiagnosticsResponse, DocumentSummary,
    FeatureHistoryResponse, JobStatusResponse, ObjectNode, PreselectionStateResponse, PropertyResponse,
    SelectionStateResponse, TaskPanelResponse, ViewportResponse,
};

use super::protocol::{
    http_boot_payload_from_proto, http_command_catalog_from_proto,
    http_command_response_from_proto, http_diagnostics_from_proto, http_events_from_proto,
    http_feature_history_from_proto, http_jobs_from_proto, http_object_tree_from_proto,
    http_preselection_state_from_proto, http_properties_from_proto,
    http_selection_response_from_proto, http_selection_state_from_proto,
    http_task_panel_from_proto, http_viewport_from_proto,
};
use super::state::{
    AppState, BootPayload, HttpCommandExecutionResponse, PreselectionRequest,
    SelectionModeRequest, SelectionRequest, SelectionResponse,
};

pub fn build_router(state: AppState) -> Router {
    Router::new()
        .route("/api/health", get(health))
        .route("/api/bootstrap", get(bootstrap))
        .route("/api/documents/open", post(open_document))
        .route("/api/selection", post(set_selection))
        .route("/api/selection/mode", post(set_selection_mode))
        .route("/api/preselection", post(set_preselection))
        .route("/api/documents/{document_id}/tree", get(fetch_object_tree))
        .route(
            "/api/documents/{document_id}/properties/{object_id}",
            get(fetch_properties),
        )
        .route("/api/documents/{document_id}/commands", get(fetch_commands))
        .route("/api/documents/{document_id}/history", get(fetch_history))
        .route("/api/documents/{document_id}/task-panel", get(fetch_task_panel))
        .route("/api/documents/{document_id}/diagnostics", get(fetch_diagnostics))
        .route("/api/documents/{document_id}/selection-state", get(fetch_selection_state))
        .route("/api/documents/{document_id}/preselection-state", get(fetch_preselection_state))
        .route("/api/documents/{document_id}/jobs", get(fetch_jobs))
        .route("/api/documents/{document_id}/viewport", get(fetch_viewport))
        .route("/api/documents/{document_id}/events", get(fetch_events))
        .route("/api/commands/run", post(run_command))
        .with_state(state)
}

async fn health() -> Json<serde_json::Value> {
    Json(serde_json::json!({
        "status": "ok",
        "program": "asterforge-api-gateway"
    }))
}

async fn bootstrap(State(state): State<AppState>) -> Json<BootPayload> {
    Json(http_boot_payload_from_proto(state.boot_payload_proto().await))
}

async fn open_document(
    State(state): State<AppState>,
    Json(request): Json<super::state::OpenDocumentHttpRequest>,
) -> Json<DocumentSummary> {
    Json(state.open_document(request.file_path).await)
}

async fn set_selection(
    State(state): State<AppState>,
    Json(request): Json<SelectionRequest>,
) -> Result<Json<SelectionResponse>, StatusCode> {
    let proto_request = SelectionRef {
        document_id: request.document_id,
        object_id: request.object_id,
        subelement: String::new(),
        selection_mode: String::new(),
    };
    state
        .set_selection_proto(proto_request)
        .await
        .map(http_selection_response_from_proto)
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

async fn set_selection_mode(
    State(state): State<AppState>,
    Json(request): Json<SelectionModeRequest>,
) -> Result<Json<SelectionStateResponse>, StatusCode> {
    let proto_request = ProtoSelectionModeRequest {
        document_id: request.document_id,
        mode_id: request.mode_id,
    };
    state
        .set_selection_mode_proto(proto_request)
        .await
        .map(http_selection_state_from_proto)
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

async fn set_preselection(
    State(state): State<AppState>,
    Json(request): Json<PreselectionRequest>,
) -> Result<Json<PreselectionStateResponse>, StatusCode> {
    let proto_request = ProtoPreselectionRequest {
        document_id: request.document_id,
        object_id: request.object_id,
    };
    state
        .set_preselection_proto(proto_request)
        .await
        .map(http_preselection_state_from_proto)
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

async fn fetch_object_tree(
    Path(document_id): Path<String>,
    State(state): State<AppState>,
) -> Result<Json<Vec<ObjectNode>>, StatusCode> {
    state
        .object_tree_proto(&document_id)
        .await
        .map(http_object_tree_from_proto)
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

async fn fetch_properties(
    Path((document_id, object_id)): Path<(String, String)>,
    State(state): State<AppState>,
) -> Result<Json<PropertyResponse>, StatusCode> {
    state
    .properties_proto(&document_id, &object_id)
        .await
    .map(http_properties_from_proto)
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

async fn fetch_events(
    Path(document_id): Path<String>,
    State(state): State<AppState>,
) -> Result<Json<Vec<BackendEvent>>, StatusCode> {
    state
        .events_proto(&document_id)
        .await
        .map(http_events_from_proto)
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

async fn fetch_commands(
    Path(document_id): Path<String>,
    State(state): State<AppState>,
) -> Result<Json<CommandCatalogResponse>, StatusCode> {
    state
    .command_catalog_proto(&document_id)
        .await
    .map(http_command_catalog_from_proto)
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

async fn fetch_history(
    Path(document_id): Path<String>,
    State(state): State<AppState>,
) -> Result<Json<FeatureHistoryResponse>, StatusCode> {
    state
    .feature_history_proto(&document_id)
        .await
    .map(http_feature_history_from_proto)
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

async fn fetch_task_panel(
    Path(document_id): Path<String>,
    State(state): State<AppState>,
) -> Result<Json<TaskPanelResponse>, StatusCode> {
    state
    .task_panel_proto(&document_id)
        .await
    .map(http_task_panel_from_proto)
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

async fn fetch_diagnostics(
    Path(document_id): Path<String>,
    State(state): State<AppState>,
) -> Result<Json<DiagnosticsResponse>, StatusCode> {
    state
    .diagnostics_proto(&document_id)
        .await
    .map(http_diagnostics_from_proto)
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

async fn fetch_selection_state(
    Path(document_id): Path<String>,
    State(state): State<AppState>,
) -> Result<Json<SelectionStateResponse>, StatusCode> {
    state
        .selection_state_proto(&document_id)
        .await
        .map(http_selection_state_from_proto)
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

async fn fetch_preselection_state(
    Path(document_id): Path<String>,
    State(state): State<AppState>,
) -> Result<Json<PreselectionStateResponse>, StatusCode> {
    state
        .preselection_state_proto(&document_id)
        .await
        .map(http_preselection_state_from_proto)
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

async fn fetch_jobs(
    Path(document_id): Path<String>,
    State(state): State<AppState>,
) -> Result<Json<JobStatusResponse>, StatusCode> {
    state
    .jobs_proto(&document_id)
        .await
    .map(http_jobs_from_proto)
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

async fn fetch_viewport(
    Path(document_id): Path<String>,
    State(state): State<AppState>,
) -> Result<Json<ViewportResponse>, StatusCode> {
    state
    .viewport_proto(&document_id)
        .await
    .map(http_viewport_from_proto)
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

async fn run_command(
    State(state): State<AppState>,
    Json(request): Json<CommandExecutionRequest>,
) -> Result<Json<HttpCommandExecutionResponse>, StatusCode> {
    let proto_request = CommandInvocation {
        command_id: request.command_id,
        document_id: request.document_id,
        target_object_id: request.target_object_id,
        arguments: request.arguments,
    };
    let response = state
        .run_command_proto(proto_request)
        .await
        .map(http_command_response_from_proto)
        .ok_or(StatusCode::NOT_FOUND)?;

    info!(command_id = %response.command_id, accepted = response.accepted, "command executed");
    Ok(Json(response))
}
