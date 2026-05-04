use asterforge_command_core::{
    CommandDispatchRoute, CommandExecutionRequest, CommandExecutionResponse,
};

use crate::domain::{BackendEvent, JobStageEntry, JobStatusEntry, viewport_diff_response};

use super::services::AppServices;
use super::state::HttpCommandExecutionResponse;
use super::state_types::AppModel;

pub(super) fn run_command(
    services: &AppServices,
    correlation_id: &str,
    model: &mut AppModel,
    request: CommandExecutionRequest,
) -> HttpCommandExecutionResponse {
    tracing::info!(correlation_id, command_id = %request.command_id, document_id = %request.document_id, "running command through gateway runtime");
    if !model.apply_command_target(services, correlation_id, request.target_object_id.as_deref()) {
        return HttpCommandExecutionResponse {
            command_id: request.command_id,
            accepted: false,
            status_message: "Target object is not selectable in the active document context".into(),
            document_dirty: model.document.dirty,
            viewport_diff: None,
        };
    }

    let viewport_before = model.bridge_snapshot.viewport.clone();
    let target_object_id = request.target_object_id.clone();

    let behavior = services.command.behavior(&request.command_id);
    let is_mutating = behavior.opens_undo_transaction();
    if is_mutating {
        let snap_clone = model.bridge_snapshot.clone();
        model.undo_stack.push(&snap_clone);
    }

    let response = execute_command(services, correlation_id, model, &request);

    if !response.accepted && is_mutating {
        let snap_clone = model.bridge_snapshot.clone();
        model.undo_stack.undo(&snap_clone);
    }

    let viewport_diff = if response.accepted && is_mutating {
        let diff = services
            .bridge
            .diff_viewport(&viewport_before, &model.bridge_snapshot.viewport);
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

    let runtime_plan = services.command.runtime_plan(
        correlation_id,
        request.command_id.as_str(),
        &response.status_message,
        response.accepted,
        viewport_diff.is_some(),
        request.arguments.get("source").map(String::as_str),
    );
    let job_entry = JobStatusEntry {
        job_id: format!("job-{}-{}", model.jobs.len() + 1, request.command_id),
        title: runtime_plan.job_title,
        command_id: request.command_id.clone(),
        state: runtime_plan.job_state,
        progress_percent: runtime_plan.job_progress_percent,
        detail: response.status_message.clone(),
        object_id: target_object_id.clone(),
        stages: runtime_plan
            .job_stages
            .iter()
            .cloned()
            .map(|stage| JobStageEntry {
                stage_id: stage.stage_id,
                label: stage.label,
                state: stage.state,
                progress_percent: stage.progress_percent,
            })
            .collect(),
    };
    model.jobs.insert(0, job_entry);
    model.jobs.truncate(8);

    let document_id = model.document.document_id.clone();
    for event in runtime_plan.events.into_iter().rev()
    {
        model.events.insert(
            0,
            BackendEvent {
                topic: event.topic,
                level: event.level,
                message: event.message,
                document_id: document_id.clone(),
                object_id: target_object_id.clone(),
            },
        );
    }

    if response.accepted {
        let selected_object_id = model.selected_object_id.clone();
        let viewport_event = services.command.viewport_invalidated_event();
        model.events.insert(
            1,
            BackendEvent {
                topic: viewport_event.topic,
                level: viewport_event.level,
                message: viewport_event.message,
                document_id,
                object_id: Some(selected_object_id),
            },
        );
    }

    HttpCommandExecutionResponse {
        command_id: response.command_id,
        accepted: response.accepted,
        status_message: response.status_message,
        document_dirty: response.document_dirty,
        viewport_diff,
    }
}

fn execute_command(
    services: &AppServices,
    correlation_id: &str,
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> CommandExecutionResponse {
    match services.command.dispatch_route(
        request.command_id.as_str(),
        model.step_cache_by_document.contains_key(&model.document.document_id),
    ) {
        CommandDispatchRoute::Step => handle_step_command(model, request).unwrap_or_else(|| {
            super::step_runtime::rejected_step_command(model, request, "STEP cache is unavailable")
        }),
        CommandDispatchRoute::BridgeVerticalSlice => super::bridge_command_runtime::run_bridge_vertical_slice_command(services, correlation_id, model, request),
        CommandDispatchRoute::UndoRedo => super::bridge_command_runtime::handle_undo_redo_command(services, correlation_id, model, request).unwrap_or_else(|| {
            CommandExecutionResponse {
                command_id: request.command_id.clone(),
                accepted: false,
                status_message: format!("Unknown undo/redo command: {}", request.command_id),
                document_dirty: model.document.dirty,
            }
        }),
        CommandDispatchRoute::Extension => handle_extension_command(model, request).unwrap_or_else(|| {
            CommandExecutionResponse {
                command_id: request.command_id.clone(),
                accepted: false,
                status_message: format!("Unknown extension command: {}", request.command_id),
                document_dirty: model.document.dirty,
            }
        }),
        CommandDispatchRoute::Unknown => CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: false,
            status_message: format!("Unknown command: {}", request.command_id),
            document_dirty: model.document.dirty,
        },
    }
}

fn handle_extension_command(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> Option<CommandExecutionResponse> {
    super::extension_runtime::handle_extension_command(model, request)
}

fn handle_step_command(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> Option<CommandExecutionResponse> {
    super::step_runtime::handle_step_command(model, request)
}
