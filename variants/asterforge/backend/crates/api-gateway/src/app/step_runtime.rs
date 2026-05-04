use asterforge_command_core::{
    CommandExecutionRequest, CommandExecutionResponse, COMMAND_SELECTION_FOCUS,
    COMMAND_STEP_HIDE_SELECTION, COMMAND_STEP_INSPECT_PMI, COMMAND_STEP_ISOLATE_SELECTION,
    COMMAND_STEP_MEASURE_SELECTION, COMMAND_STEP_SELECT_FIRST_CHILD, COMMAND_STEP_SELECT_PARENT,
    COMMAND_STEP_SHOW_ALL, COMMAND_STEP_VIEW_BACK, COMMAND_STEP_VIEW_BOTTOM,
    COMMAND_STEP_VIEW_FIT_ALL, COMMAND_STEP_VIEW_FRONT, COMMAND_STEP_VIEW_ISO,
    COMMAND_STEP_VIEW_LEFT, COMMAND_STEP_VIEW_RESET, COMMAND_STEP_VIEW_RIGHT,
    COMMAND_STEP_VIEW_TOP,
};
use asterforge_step_core::{
    step_focus_selection_message, step_hidden_subtree_message, step_isolated_subtree_message,
    step_measurement_message, step_pmi_annotation_event_message,
    step_pmi_loaded_event_message, step_pmi_loaded_status_message,
    step_selected_child_message, step_selected_parent_message, step_show_all_message,
    step_view_fit_all_message, step_view_preset_from_command_id, step_view_reset_message,
};

use crate::domain::BackendEvent;

use super::state_step_tools;
use super::state_types::AppModel;

pub(super) fn handle_step_command(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> Option<CommandExecutionResponse> {
    if !model.step_cache_by_document.contains_key(&model.document.document_id) {
        return None;
    }

    match request.command_id.as_str() {
        COMMAND_SELECTION_FOCUS => Some(handle_step_focus_selection(model, request)),
        COMMAND_STEP_VIEW_ISO => Some(handle_step_view_preset(model, request)),
        COMMAND_STEP_VIEW_FIT_ALL => Some(handle_step_view_fit_all(model, request)),
        COMMAND_STEP_VIEW_RESET => Some(handle_step_view_reset(model, request)),
        COMMAND_STEP_VIEW_FRONT => Some(handle_step_view_preset(model, request)),
        COMMAND_STEP_VIEW_BACK => Some(handle_step_view_preset(model, request)),
        COMMAND_STEP_VIEW_RIGHT => Some(handle_step_view_preset(model, request)),
        COMMAND_STEP_VIEW_LEFT => Some(handle_step_view_preset(model, request)),
        COMMAND_STEP_VIEW_TOP => Some(handle_step_view_preset(model, request)),
        COMMAND_STEP_VIEW_BOTTOM => Some(handle_step_view_preset(model, request)),
        COMMAND_STEP_SELECT_PARENT => Some(handle_step_select_parent(model, request)),
        COMMAND_STEP_SELECT_FIRST_CHILD => Some(handle_step_select_first_child(model, request)),
        COMMAND_STEP_INSPECT_PMI => Some(handle_step_inspect_pmi(model, request)),
        COMMAND_STEP_MEASURE_SELECTION => Some(handle_step_measure_selection(model, request)),
        COMMAND_STEP_HIDE_SELECTION => Some(handle_step_hide_selection(model, request)),
        COMMAND_STEP_ISOLATE_SELECTION => Some(handle_step_isolate_selection(model, request)),
        COMMAND_STEP_SHOW_ALL => Some(handle_step_show_all(model, request)),
        _ => None,
    }
}

pub(super) fn rejected_step_command(
    model: &AppModel,
    request: &CommandExecutionRequest,
    message: &str,
) -> CommandExecutionResponse {
    CommandExecutionResponse {
        command_id: request.command_id.clone(),
        accepted: false,
        status_message: message.into(),
        document_dirty: model.document.dirty,
    }
}

fn handle_step_focus_selection(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> CommandExecutionResponse {
    let Some(cache) = model.step_cache_by_document.get(&model.document.document_id) else {
        return rejected_step_command(model, request, "STEP cache is unavailable");
    };
    let Some(camera) = state_step_tools::step_focus_camera_for_selection(&model.selected_object_id, cache) else {
        return rejected_step_command(model, request, "Selected STEP node has no focusable tessellated payload");
    };

    model
        .step_viewport_camera_by_document
        .insert(model.document.document_id.clone(), camera);
    CommandExecutionResponse {
        command_id: request.command_id.clone(),
        accepted: true,
        status_message: step_focus_selection_message(&model.selected_object_id),
        document_dirty: model.document.dirty,
    }
}

fn handle_step_view_preset(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> CommandExecutionResponse {
    let Some(preset) = step_view_preset_from_command_id(&request.command_id) else {
        return rejected_step_command(model, request, "Unknown STEP viewport preset");
    };
    let Some(camera) = state_step_tools::step_viewport_camera_for_preset(
        model.step_viewport_camera_by_document.get(&model.document.document_id),
        preset.preset_id(),
    ) else {
        return rejected_step_command(model, request, "Unknown STEP viewport preset");
    };

    model
        .step_viewport_camera_by_document
        .insert(model.document.document_id.clone(), camera);
    CommandExecutionResponse {
        command_id: request.command_id.clone(),
        accepted: true,
        status_message: preset.status_message(),
        document_dirty: model.document.dirty,
    }
}

fn handle_step_view_reset(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> CommandExecutionResponse {
    model.step_viewport_camera_by_document.insert(
        model.document.document_id.clone(),
        state_step_tools::step_reset_viewport_camera(),
    );
    CommandExecutionResponse {
        command_id: request.command_id.clone(),
        accepted: true,
        status_message: step_view_reset_message(),
        document_dirty: model.document.dirty,
    }
}

fn handle_step_view_fit_all(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> CommandExecutionResponse {
    let Some(cache) = model.step_cache_by_document.get(&model.document.document_id) else {
        return rejected_step_command(model, request, "STEP cache is unavailable");
    };
    let Some(camera) = state_step_tools::step_fit_all_viewport_camera(
        cache,
        &model.object_tree,
        model.step_viewport_camera_by_document.get(&model.document.document_id),
    ) else {
        return rejected_step_command(model, request, "Visible STEP geometry has no fit-all bounds");
    };

    model
        .step_viewport_camera_by_document
        .insert(model.document.document_id.clone(), camera);
    CommandExecutionResponse {
        command_id: request.command_id.clone(),
        accepted: true,
        status_message: step_view_fit_all_message(),
        document_dirty: model.document.dirty,
    }
}

fn handle_step_select_parent(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> CommandExecutionResponse {
    let Some(cache) = model.step_cache_by_document.get(&model.document.document_id) else {
        return rejected_step_command(model, request, "STEP cache is unavailable");
    };
    let Some(parent_id) = super::state_step_nav::step_parent_object_id(
        &model.selected_object_id,
        &cache.scene_bundle.assemblies,
    ) else {
        return rejected_step_command(model, request, "Selected STEP node has no parent assembly");
    };

    model.selected_object_id = parent_id.clone();
    CommandExecutionResponse {
        command_id: request.command_id.clone(),
        accepted: true,
        status_message: step_selected_parent_message(&parent_id),
        document_dirty: model.document.dirty,
    }
}

fn handle_step_select_first_child(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> CommandExecutionResponse {
    let Some(cache) = model.step_cache_by_document.get(&model.document.document_id) else {
        return rejected_step_command(model, request, "STEP cache is unavailable");
    };
    let Some(child_id) = super::state_step_nav::step_first_child_object_id(
        &model.selected_object_id,
        &cache.scene_bundle.assemblies,
    ) else {
        return rejected_step_command(model, request, "Selected STEP node has no child assembly");
    };

    model.selected_object_id = child_id.clone();
    CommandExecutionResponse {
        command_id: request.command_id.clone(),
        accepted: true,
        status_message: step_selected_child_message(&child_id),
        document_dirty: model.document.dirty,
    }
}

fn handle_step_inspect_pmi(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> CommandExecutionResponse {
    let Some(cache) = model.step_cache_by_document.get(&model.document.document_id) else {
        return rejected_step_command(model, request, "STEP cache is unavailable");
    };
    let Some(result) = state_step_tools::step_pmi_inspection_for_selection(
        &model.selected_object_id,
        cache,
        &model.object_tree,
    ) else {
        return rejected_step_command(model, request, "Selected STEP entity has no semantic PMI");
    };

    model
        .step_pmi_inspection_by_document
        .insert(model.document.document_id.clone(), result.clone());
    model.combo_view_visible = true;
    model.combo_view_tab = "tasks".into();
    model.report_dock_visible = true;
    model.bottom_dock_tab = "report".into();
    let document_id = model.document.document_id.clone();
    let object_id = Some(model.selected_object_id.clone());
    for annotation in result.annotations.iter().rev() {
        model.events.insert(
            0,
            BackendEvent {
                topic: "step_pmi_annotation".into(),
                level: "info".into(),
                message: step_pmi_annotation_event_message(
                    &annotation.semantic_type,
                    &annotation.text,
                    &annotation.target_entity_ids,
                ),
                document_id: document_id.clone(),
                object_id: object_id.clone(),
            },
        );
    }
    model.events.insert(
        0,
        BackendEvent {
            topic: "step_pmi_inspection".into(),
            level: "info".into(),
            message: step_pmi_loaded_event_message(&result.label, result.entity_id),
            document_id,
            object_id,
        },
    );
    CommandExecutionResponse {
        command_id: request.command_id.clone(),
        accepted: true,
        status_message: step_pmi_loaded_status_message(&result.label, result.annotations.len()),
        document_dirty: model.document.dirty,
    }
}

fn handle_step_hide_selection(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> CommandExecutionResponse {
    if !state_step_tools::step_hide_object_subtree(&mut model.object_tree, &model.selected_object_id) {
        return rejected_step_command(model, request, "Selected STEP node could not be hidden");
    }

    CommandExecutionResponse {
        command_id: request.command_id.clone(),
        accepted: true,
        status_message: step_hidden_subtree_message(&model.selected_object_id),
        document_dirty: model.document.dirty,
    }
}

fn handle_step_measure_selection(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> CommandExecutionResponse {
    let Some(cache) = model.step_cache_by_document.get(&model.document.document_id) else {
        return rejected_step_command(model, request, "STEP cache is unavailable");
    };
    let Some(result) = state_step_tools::step_measurement_for_selection(&model.selected_object_id, cache) else {
        return rejected_step_command(model, request, "Selected STEP node has no measurable tessellated payload");
    };

    model
        .step_measurement_by_document
        .insert(model.document.document_id.clone(), result.clone());
    model.combo_view_visible = true;
    model.combo_view_tab = "tasks".into();
    model.report_dock_visible = true;
    model.bottom_dock_tab = "report".into();
    model.events.insert(
        0,
        BackendEvent {
            topic: "step_measurement".into(),
            level: "info".into(),
            message: step_measurement_message(
                &result.label,
                result.span_x,
                result.span_y,
                result.span_z,
            ),
            document_id: model.document.document_id.clone(),
            object_id: Some(model.selected_object_id.clone()),
        },
    );

    CommandExecutionResponse {
        command_id: request.command_id.clone(),
        accepted: true,
        status_message: step_measurement_message(
            &result.label,
            result.span_x,
            result.span_y,
            result.span_z,
        ),
        document_dirty: model.document.dirty,
    }
}

fn handle_step_isolate_selection(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> CommandExecutionResponse {
    if !state_step_tools::step_isolate_object_subtree(&mut model.object_tree, &model.selected_object_id) {
        return rejected_step_command(model, request, "Selected STEP node could not be isolated");
    }

    CommandExecutionResponse {
        command_id: request.command_id.clone(),
        accepted: true,
        status_message: step_isolated_subtree_message(&model.selected_object_id),
        document_dirty: model.document.dirty,
    }
}

fn handle_step_show_all(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> CommandExecutionResponse {
    state_step_tools::step_show_all_objects(&mut model.object_tree);

    CommandExecutionResponse {
        command_id: request.command_id.clone(),
        accepted: true,
        status_message: step_show_all_message(),
        document_dirty: model.document.dirty,
    }
}