use asterforge_command_core::{
    command_behavior, job_title_from_command_id, plan_job_stages,
    plan_command_events, viewport_invalidated_event, CommandExecutionRequest,
    CommandExecutionResponse,
    COMMAND_DOCUMENT_RECOMPUTE, COMMAND_DOCUMENT_REDO, COMMAND_DOCUMENT_SAVE,
    COMMAND_DOCUMENT_UNDO, COMMAND_HISTORY_RESUME_FULL, COMMAND_HISTORY_ROLLBACK_HERE,
    COMMAND_MODEL_TOGGLE_SUPPRESSION, COMMAND_PARTDESIGN_EDIT_PAD,
    COMMAND_PARTDESIGN_EDIT_POCKET, COMMAND_PARTDESIGN_NEW_SKETCH, COMMAND_PARTDESIGN_PAD,
    COMMAND_PARTDESIGN_POCKET, COMMAND_SELECTION_FOCUS,
};
use asterforge_freecad_bridge::{
    compute_viewport_diff, create_pad_from_selected_sketch, create_pocket_from_selected_sketch,
    create_sketch_in_body, resume_full_history, rollback_history_to_selected,
    toggle_selected_suppression, update_selected_pad_profile, update_selected_pocket_profile,
};

use crate::domain::{BackendEvent, JobStageEntry, JobStatusEntry, viewport_diff_response};

use super::state::{AppModel, HttpCommandExecutionResponse};

pub(super) fn run_command(
    model: &mut AppModel,
    request: CommandExecutionRequest,
) -> HttpCommandExecutionResponse {
    let viewport_before = model.bridge_snapshot.viewport.clone();
    let target_object_id = request.target_object_id.clone();

    let behavior = command_behavior(&request.command_id);
    let is_mutating = behavior.opens_undo_transaction();
    if is_mutating {
        let snap_clone = model.bridge_snapshot.clone();
        model.undo_stack.push(&snap_clone);
    }

    let response = execute_command(model, &request);

    if !response.accepted && is_mutating {
        let snap_clone = model.bridge_snapshot.clone();
        model.undo_stack.undo(&snap_clone);
    }

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

    let job_title = job_title_from_command_id(&request.command_id);
    let job_stages = plan_job_stages(
        request.command_id.as_str(),
        response.accepted,
        viewport_diff.is_some(),
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
        stages: job_stages
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
    let source = request.arguments.get("source").map(String::as_str);
    for event in plan_command_events(
        request.command_id.as_str(),
        &response.status_message,
        response.accepted,
        &job_stages,
        source,
    )
    .into_iter()
    .rev()
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
        let viewport_event = viewport_invalidated_event();
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

fn execute_command(model: &mut AppModel, request: &CommandExecutionRequest) -> CommandExecutionResponse {
    if let Some(response) = handle_document_command(model, request) {
        return response;
    }

    if let Some(response) = handle_history_or_model_command(model, request) {
        return response;
    }

    if let Some(response) = handle_partdesign_command(model, request) {
        return response;
    }

    if let Some(response) = handle_undo_redo_command(model, request) {
        return response;
    }

    CommandExecutionResponse {
        command_id: request.command_id.clone(),
        accepted: false,
        status_message: format!("Unknown command: {}", request.command_id),
        document_dirty: model.document.dirty,
    }
}

fn handle_document_command(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> Option<CommandExecutionResponse> {
    match request.command_id.as_str() {
        COMMAND_DOCUMENT_SAVE => {
            model.document.dirty = false;
            model.bridge_snapshot.dirty = false;
            Some(CommandExecutionResponse {
                command_id: request.command_id.clone(),
                accepted: true,
                status_message: "Document marked as saved".into(),
                document_dirty: model.document.dirty,
            })
        }
        COMMAND_DOCUMENT_RECOMPUTE => {
            model.document.dirty = true;
            model.bridge_snapshot.dirty = true;
            Some(CommandExecutionResponse {
                command_id: request.command_id.clone(),
                accepted: true,
                status_message: "Recompute queued through bridge-backed mock backend".into(),
                document_dirty: model.document.dirty,
            })
        }
        COMMAND_SELECTION_FOCUS => Some(CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: true,
            status_message: "Selection focus requested".into(),
            document_dirty: model.document.dirty,
        }),
        _ => None,
    }
}

fn handle_history_or_model_command(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> Option<CommandExecutionResponse> {
    match request.command_id.as_str() {
        COMMAND_HISTORY_ROLLBACK_HERE => Some(handle_history_rollback(model, request)),
        COMMAND_HISTORY_RESUME_FULL => Some(handle_history_resume(model, request)),
        COMMAND_MODEL_TOGGLE_SUPPRESSION => Some(handle_toggle_suppression(model, request)),
        _ => None,
    }
}

fn handle_partdesign_command(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> Option<CommandExecutionResponse> {
    match request.command_id.as_str() {
        COMMAND_PARTDESIGN_NEW_SKETCH => Some(handle_new_sketch(model, request)),
        COMMAND_PARTDESIGN_EDIT_POCKET => Some(handle_edit_pocket(model, request)),
        COMMAND_PARTDESIGN_EDIT_PAD => Some(handle_edit_pad(model, request)),
        COMMAND_PARTDESIGN_POCKET => Some(handle_new_pocket(model, request)),
        COMMAND_PARTDESIGN_PAD => Some(handle_new_pad(model, request)),
        _ => None,
    }
}

fn handle_undo_redo_command(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> Option<CommandExecutionResponse> {
    match request.command_id.as_str() {
        COMMAND_DOCUMENT_UNDO => Some(handle_undo(model, request)),
        COMMAND_DOCUMENT_REDO => Some(handle_redo(model, request)),
        _ => None,
    }
}

fn handle_history_rollback(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> CommandExecutionResponse {
    if let Some((object_id, sequence_index)) = rollback_history_to_selected(&mut model.bridge_snapshot) {
        model.sync_from_snapshot();
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: true,
            status_message: format!(
                "Rolled back model evaluation to {} at step {}",
                object_id, sequence_index
            ),
            document_dirty: model.document.dirty,
        }
    } else {
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: false,
            status_message: "Rollback requires a selected history feature".into(),
            document_dirty: model.document.dirty,
        }
    }
}

fn handle_history_resume(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> CommandExecutionResponse {
    if resume_full_history(&mut model.bridge_snapshot) {
        model.sync_from_snapshot();
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: true,
            status_message: "Restored full feature history".into(),
            document_dirty: model.document.dirty,
        }
    } else {
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: false,
            status_message: "Feature history is already fully resumed".into(),
            document_dirty: model.document.dirty,
        }
    }
}

fn handle_toggle_suppression(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> CommandExecutionResponse {
    if let Some((object_id, suppressed)) = toggle_selected_suppression(&mut model.bridge_snapshot) {
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
        }
    } else {
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: false,
            status_message: "Suppression requires a non-body selection".into(),
            document_dirty: model.document.dirty,
        }
    }
}

fn handle_new_sketch(model: &mut AppModel, request: &CommandExecutionRequest) -> CommandExecutionResponse {
    let requested_label = request.arguments.get("sketch_label").map(String::as_str);
    let reference_plane = request.arguments.get("reference_plane").map(String::as_str);
    if create_sketch_in_body(
        &mut model.bridge_snapshot,
        requested_label,
        reference_plane,
    )
    .is_some()
    {
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
        }
    } else {
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: false,
            status_message: "Sketch creation requires the body to be selected".into(),
            document_dirty: model.document.dirty,
        }
    }
}

fn handle_edit_pocket(model: &mut AppModel, request: &CommandExecutionRequest) -> CommandExecutionResponse {
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
        }
    } else if model.selected_object_id.starts_with("pocket-") {
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: false,
            status_message: "Pocket editing requires a positive depth_mm argument".into(),
            document_dirty: model.document.dirty,
        }
    } else {
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: false,
            status_message: "Pocket editing requires an active pocket selection".into(),
            document_dirty: model.document.dirty,
        }
    }
}

fn handle_edit_pad(model: &mut AppModel, request: &CommandExecutionRequest) -> CommandExecutionResponse {
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
        }
    } else if model.selected_object_id.starts_with("pad-") {
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: false,
            status_message: "Pad editing requires a positive length_mm argument".into(),
            document_dirty: model.document.dirty,
        }
    } else {
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: false,
            status_message: "Pad editing requires an active pad selection".into(),
            document_dirty: model.document.dirty,
        }
    }
}

fn handle_new_pocket(model: &mut AppModel, request: &CommandExecutionRequest) -> CommandExecutionResponse {
    let parsed_depth = request
        .arguments
        .get("depth_mm")
        .and_then(|value| value.parse::<f32>().ok());
    let parsed_extent_mode = request.arguments.get("extent_mode").map(String::as_str);
    if create_pocket_from_selected_sketch(
        &mut model.bridge_snapshot,
        parsed_depth,
        parsed_extent_mode,
    )
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
        }
    } else {
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: false,
            status_message: "Pocket creation requires an active sketch selection".into(),
            document_dirty: model.document.dirty,
        }
    }
}

fn handle_new_pad(model: &mut AppModel, request: &CommandExecutionRequest) -> CommandExecutionResponse {
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

    if create_pad_from_selected_sketch(
        &mut model.bridge_snapshot,
        pad_length,
        Some("dimension"),
        parsed_midplane,
    )
    .is_some()
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
        }
    } else {
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: false,
            status_message: "Pad creation requires an active sketch selection".into(),
            document_dirty: model.document.dirty,
        }
    }
}

fn handle_undo(model: &mut AppModel, request: &CommandExecutionRequest) -> CommandExecutionResponse {
    let current_snap = model.bridge_snapshot.clone();
    if let Some(previous) = model.undo_stack.undo(&current_snap) {
        model.bridge_snapshot = previous;
        model.sync_from_snapshot();
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: true,
            status_message: "Undo applied".into(),
            document_dirty: model.document.dirty,
        }
    } else {
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: false,
            status_message: "Nothing to undo".into(),
            document_dirty: model.document.dirty,
        }
    }
}

fn handle_redo(model: &mut AppModel, request: &CommandExecutionRequest) -> CommandExecutionResponse {
    let current_snap = model.bridge_snapshot.clone();
    if let Some(next) = model.undo_stack.redo(&current_snap) {
        model.bridge_snapshot = next;
        model.sync_from_snapshot();
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: true,
            status_message: "Redo applied".into(),
            document_dirty: model.document.dirty,
        }
    } else {
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: false,
            status_message: "Nothing to redo".into(),
            document_dirty: model.document.dirty,
        }
    }
}

fn parse_bool_flag(value: &str) -> Option<bool> {
    match value {
        "true" | "1" | "yes" | "on" => Some(true),
        "false" | "0" | "no" | "off" => Some(false),
        _ => None,
    }
}
