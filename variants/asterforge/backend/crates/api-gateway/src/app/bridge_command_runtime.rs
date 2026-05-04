use asterforge_command_core::{
    execute_bridge_command, execute_history_command, CommandExecutionRequest,
    CommandExecutionResponse, COMMAND_DOCUMENT_REDO, COMMAND_DOCUMENT_UNDO,
};

use super::services::AppServices;
use super::state_types::AppModel;

pub(super) fn handle_undo_redo_command(
    services: &AppServices,
    correlation_id: &str,
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> Option<CommandExecutionResponse> {
    match request.command_id.as_str() {
        COMMAND_DOCUMENT_UNDO => Some(handle_undo(services, correlation_id, model, request)),
        COMMAND_DOCUMENT_REDO => Some(handle_redo(services, correlation_id, model, request)),
        _ => None,
    }
}

pub(super) fn run_bridge_vertical_slice_command(
    services: &AppServices,
    correlation_id: &str,
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> CommandExecutionResponse {
    let session_id = model.active_session_id();
    let bridge_outcome = execute_bridge_command(
        &services.bridge,
        correlation_id,
        &session_id,
        Some(&model.selected_object_id),
        request,
    );

    if let Some(updated_snapshot) = bridge_outcome.updated_snapshot {
        model.bridge_snapshot = updated_snapshot;
        model.sync_from_snapshot(services, correlation_id);
    }

    let mut response = bridge_outcome.response;
    if !response.accepted {
        tracing::warn!(
            correlation_id,
            command_id = %request.command_id,
            "bridge vertical slice returned rejected response"
        );
    }
    response.document_dirty = model.document.dirty;
    response
}

fn handle_undo(
    services: &AppServices,
    correlation_id: &str,
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> CommandExecutionResponse {
    let outcome = execute_history_command(
        &services.history,
        correlation_id,
        request,
        &mut model.undo_stack,
        &model.bridge_snapshot,
    );

    if let Some(previous) = outcome.updated_snapshot {
        model.bridge_snapshot = previous;
        model.sync_from_snapshot(services, correlation_id);
    }

    let mut response = outcome.response;
    response.document_dirty = model.document.dirty;
    response
}

fn handle_redo(
    services: &AppServices,
    correlation_id: &str,
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> CommandExecutionResponse {
    let outcome = execute_history_command(
        &services.history,
        correlation_id,
        request,
        &mut model.undo_stack,
        &model.bridge_snapshot,
    );

    if let Some(next) = outcome.updated_snapshot {
        model.bridge_snapshot = next;
        model.sync_from_snapshot(services, correlation_id);
    }

    let mut response = outcome.response;
    response.document_dirty = model.document.dirty;
    response
}