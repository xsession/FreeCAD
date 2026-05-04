use std::path::Path;
use std::sync::Arc;

use asterforge_document_core::DocumentSummary;
use tokio::sync::RwLock;

use super::services::AppServices;
use super::state_requests::{
    ActivateWorkbenchRequest, PreselectionRequest, SelectionModeRequest, SelectionRequest,
    SelectionResponse, ShellPanelMutationRequest, ShellSessionMutationRequest,
};
use super::state_types::AppModel;
use super::{state_commands, state_open, state_selection, state_shell};
use crate::domain::{PreselectionStateResponse, SelectionStateResponse, ShellSnapshot};

pub(super) async fn open_document(
    inner: &Arc<RwLock<AppModel>>,
    services: &Arc<AppServices>,
    persistence_path: Option<&Path>,
    file_path: String,
) -> DocumentSummary {
    let correlation_id = services.next_correlation_id();
    let snapshot = {
        let model = inner.read().await;
        services
            .bridge
            .open_pending_document_snapshot(&correlation_id, &model.session_namespace, Some(&file_path))
    };
    tracing::info!(correlation_id, file_path, "opening document through app state");

    let mut model = inner.write().await;
    let summary = state_open::apply_open_document(
        services,
        &correlation_id,
        &mut model,
        &file_path,
        snapshot,
    );

    state_commands::persist_model(persistence_path, &correlation_id, &model);

    summary
}

pub(super) async fn set_selection(
    inner: &Arc<RwLock<AppModel>>,
    services: &Arc<AppServices>,
    persistence_path: Option<&Path>,
    request: SelectionRequest,
) -> Option<SelectionResponse> {
    let mut model = inner.write().await;
    let correlation_id = services.next_correlation_id();
    let response = state_selection::apply_selection(services, &correlation_id, &mut model, request)?;

    state_commands::persist_model(persistence_path, &correlation_id, &model);

    Some(response)
}

pub(super) async fn set_selection_mode(
    inner: &Arc<RwLock<AppModel>>,
    services: &Arc<AppServices>,
    persistence_path: Option<&Path>,
    request: SelectionModeRequest,
) -> Option<SelectionStateResponse> {
    let mut model = inner.write().await;
    let correlation_id = services.next_correlation_id();
    let response = state_selection::apply_selection_mode(services, &correlation_id, &mut model, request)?;

    state_commands::persist_model(persistence_path, &correlation_id, &model);

    Some(response)
}

pub(super) async fn activate_workbench(
    inner: &Arc<RwLock<AppModel>>,
    services: &Arc<AppServices>,
    persistence_path: Option<&Path>,
    request: ActivateWorkbenchRequest,
) -> Option<DocumentSummary> {
    let mut model = inner.write().await;
    let correlation_id = services.next_correlation_id();
    let summary = state_shell::apply_activate_workbench(services, &mut model, request)?;

    state_commands::persist_model(persistence_path, &correlation_id, &model);

    Some(summary)
}

pub(super) async fn update_shell_panel(
    inner: &Arc<RwLock<AppModel>>,
    services: &Arc<AppServices>,
    persistence_path: Option<&Path>,
    request: ShellPanelMutationRequest,
) -> Option<ShellSnapshot> {
    let mut model = inner.write().await;
    let correlation_id = services.next_correlation_id();
    let snapshot = state_shell::apply_shell_panel_update(services, &mut model, request)?;

    state_commands::persist_model(persistence_path, &correlation_id, &model);

    Some(snapshot)
}

pub(super) async fn update_shell_sessions(
    inner: &Arc<RwLock<AppModel>>,
    services: &Arc<AppServices>,
    persistence_path: Option<&Path>,
    request: ShellSessionMutationRequest,
) -> Option<ShellSnapshot> {
    let mut model = inner.write().await;
    let correlation_id = services.next_correlation_id();
    let snapshot = state_shell::apply_shell_session_update(services, &mut model, request)?;

    state_commands::persist_model(persistence_path, &correlation_id, &model);

    Some(snapshot)
}

pub(super) async fn set_preselection(
    inner: &Arc<RwLock<AppModel>>,
    services: &Arc<AppServices>,
    request: PreselectionRequest,
) -> Option<PreselectionStateResponse> {
    let mut model = inner.write().await;
    let correlation_id = services.next_correlation_id();
    state_selection::apply_preselection(services, &correlation_id, &mut model, request)
}