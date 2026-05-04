use std::path::Path;
use std::sync::Arc;

use asterforge_command_core::{CommandContext, CommandExecutionRequest};
use asterforge_protocol_types::asterforge::protocol::v1::{CommandInvocation, CommandReply};
use tokio::sync::RwLock;

use super::command_runtime;
use super::protocol::command_reply_from_http;
use super::services::AppServices;
use super::state_workspace;
use super::state_types::AppModel;
use crate::domain::ViewportDiffResponse;

#[derive(Debug, Clone, serde::Serialize)]
pub struct HttpCommandExecutionResponse {
    pub command_id: String,
    pub accepted: bool,
    pub status_message: String,
    pub document_dirty: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub viewport_diff: Option<ViewportDiffResponse>,
}

pub(super) async fn run_command(
    inner: &Arc<RwLock<AppModel>>,
    services: &Arc<AppServices>,
    persistence_path: Option<&Path>,
    request: CommandExecutionRequest,
) -> Option<HttpCommandExecutionResponse> {
    let mut model = inner.write().await;
    let correlation_id = services.next_correlation_id();
    if model.document.document_id != request.document_id {
        return None;
    }

    let command_context = CommandContext {
        document_id: model.document.document_id.clone(),
        selected_object_id: (!model.selected_object_id.is_empty())
            .then(|| model.selected_object_id.clone()),
        selectable_object_ids: model.selectable_object_ids_for_active_mode(services, &correlation_id),
    };

    if let Err(error) = services.command.validate_request(&correlation_id, &request, &command_context) {
        return Some(HttpCommandExecutionResponse {
            command_id: request.command_id,
            accepted: false,
            status_message: error.message,
            document_dirty: model.document.dirty,
            viewport_diff: None,
        });
    }

    Some(command_runtime::run_command(services, &correlation_id, &mut model, request)).map(|response| {
        persist_model(persistence_path, &correlation_id, &model);
        response
    })
}

pub(super) async fn run_command_proto(
    inner: &Arc<RwLock<AppModel>>,
    services: &Arc<AppServices>,
    persistence_path: Option<&Path>,
    request: CommandInvocation,
) -> Option<CommandReply> {
    let http_request = CommandExecutionRequest {
        command_id: request.command_id,
        document_id: request.document_id,
        target_object_id: request.target_object_id,
        arguments: request.arguments,
    };

    run_command(inner, services, persistence_path, http_request)
        .await
        .map(command_reply_from_http)
}

pub(super) fn persist_model(
    persistence_path: Option<&Path>,
    correlation_id: &str,
    model: &AppModel,
) {
    if let Some(path) = persistence_path {
        tracing::debug!(correlation_id, path = %path.display(), "persisting workspace model");
        state_workspace::save_persisted_workspace_state(
            correlation_id,
            path,
            &model.persisted_workspace_state(),
        );
    }
}