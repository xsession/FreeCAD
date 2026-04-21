use axum::{
    extract::{Path, State},
    http::StatusCode,
    routing::{get, post},
    Json, Router,
};
use tracing::info;

use crate::domain::{
    BackendEvent, CommandCatalogResponse, DiagnosticsResponse, DocumentSummary,
    FeatureHistoryResponse, JobStatusResponse, ObjectNode, PreselectionStateResponse, PropertyResponse,
    SelectionStateResponse, TaskPanelResponse, ViewportResponse,
};

use super::state::{
    AppState, BootPayload, CommandExecutionRequest, CommandExecutionResponse, SelectionRequest,
    PreselectionRequest, SelectionModeRequest, SelectionResponse,
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
    Json(state.boot_payload().await)
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
    state
        .set_selection(request)
        .await
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

async fn set_selection_mode(
    State(state): State<AppState>,
    Json(request): Json<SelectionModeRequest>,
) -> Result<Json<SelectionStateResponse>, StatusCode> {
    state
        .set_selection_mode(request)
        .await
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

async fn set_preselection(
    State(state): State<AppState>,
    Json(request): Json<PreselectionRequest>,
) -> Result<Json<PreselectionStateResponse>, StatusCode> {
    state
        .set_preselection(request)
        .await
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

async fn fetch_object_tree(
    Path(document_id): Path<String>,
    State(state): State<AppState>,
) -> Result<Json<Vec<ObjectNode>>, StatusCode> {
    state
        .object_tree(&document_id)
        .await
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

async fn fetch_properties(
    Path((document_id, object_id)): Path<(String, String)>,
    State(state): State<AppState>,
) -> Result<Json<PropertyResponse>, StatusCode> {
    state
        .properties(&document_id, &object_id)
        .await
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

async fn fetch_events(
    Path(document_id): Path<String>,
    State(state): State<AppState>,
) -> Result<Json<Vec<BackendEvent>>, StatusCode> {
    state.events(&document_id).await.map(Json).ok_or(StatusCode::NOT_FOUND)
}

async fn fetch_commands(
    Path(document_id): Path<String>,
    State(state): State<AppState>,
) -> Result<Json<CommandCatalogResponse>, StatusCode> {
    state
        .command_catalog(&document_id)
        .await
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

async fn fetch_history(
    Path(document_id): Path<String>,
    State(state): State<AppState>,
) -> Result<Json<FeatureHistoryResponse>, StatusCode> {
    state
        .feature_history(&document_id)
        .await
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

async fn fetch_task_panel(
    Path(document_id): Path<String>,
    State(state): State<AppState>,
) -> Result<Json<TaskPanelResponse>, StatusCode> {
    state
        .task_panel(&document_id)
        .await
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

async fn fetch_diagnostics(
    Path(document_id): Path<String>,
    State(state): State<AppState>,
) -> Result<Json<DiagnosticsResponse>, StatusCode> {
    state
        .diagnostics(&document_id)
        .await
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

async fn fetch_selection_state(
    Path(document_id): Path<String>,
    State(state): State<AppState>,
) -> Result<Json<SelectionStateResponse>, StatusCode> {
    state
        .selection_state(&document_id)
        .await
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

async fn fetch_preselection_state(
    Path(document_id): Path<String>,
    State(state): State<AppState>,
) -> Result<Json<PreselectionStateResponse>, StatusCode> {
    state
        .preselection_state(&document_id)
        .await
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

async fn fetch_jobs(
    Path(document_id): Path<String>,
    State(state): State<AppState>,
) -> Result<Json<JobStatusResponse>, StatusCode> {
    state
        .jobs(&document_id)
        .await
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

async fn fetch_viewport(
    Path(document_id): Path<String>,
    State(state): State<AppState>,
) -> Result<Json<ViewportResponse>, StatusCode> {
    state
        .viewport(&document_id)
        .await
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

async fn run_command(
    State(state): State<AppState>,
    Json(request): Json<CommandExecutionRequest>,
) -> Result<Json<CommandExecutionResponse>, StatusCode> {
    let response = state
        .run_command(request)
        .await
        .ok_or(StatusCode::NOT_FOUND)?;

    info!(command_id = %response.command_id, accepted = response.accepted, "command executed");
    Ok(Json(response))
}
