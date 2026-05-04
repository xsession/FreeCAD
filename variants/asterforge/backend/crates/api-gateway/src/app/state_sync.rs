use super::services::AppServices;
use super::state::STEP_OBJECT_MODE;
use super::state_step_nav::step_selectable_object_ids_for_mode;
use super::state_types::AppModel;

pub(super) fn selectable_object_ids_for_active_mode(
    services: &AppServices,
    correlation_id: &str,
    model: &AppModel,
) -> Vec<String> {
    if model.active_step_cache().is_some() {
        step_selectable_object_ids_for_mode(&model.object_tree, &model.selection_mode)
    } else {
        services
            .document
            .selectable_object_ids_for_mode(correlation_id, &model.bridge_snapshot, &model.selection_mode)
    }
}

pub(super) fn sync_from_snapshot(services: &AppServices, correlation_id: &str, model: &mut AppModel) {
    let projection = services
        .document
        .project_bridge_snapshot(correlation_id, &model.bridge_snapshot, &model.bridge_status);
    model.document = projection.document;
    model.object_tree = projection.object_tree;
    model.selected_object_id = projection.selected_object_id;
    model.properties_by_object = projection.properties_by_object;
    model.remember_current_document(services);
}

pub(super) fn apply_command_target(
    services: &AppServices,
    correlation_id: &str,
    model: &mut AppModel,
    target_object_id: Option<&str>,
) -> bool {
    let Some(target_object_id) = target_object_id.filter(|value| !value.is_empty()) else {
        return true;
    };

    let Some(next_selection) = normalize_selection_for_mode(
        services,
        correlation_id,
        model,
        target_object_id,
        &model.selection_mode,
    ) else {
        return false;
    };
    if next_selection != target_object_id {
        return false;
    }

    model.preselected_object_id = None;
    if model.active_step_cache().is_some() {
        model.selected_object_id = next_selection;
        model.remember_current_document(services);
    } else {
        model.bridge_snapshot.selected_object_id = next_selection;
        sync_from_snapshot(services, correlation_id, model);
    }

    true
}

pub(super) fn normalize_selection_for_mode(
    services: &AppServices,
    correlation_id: &str,
    model: &AppModel,
    requested_object_id: &str,
    selection_mode: &str,
) -> Option<String> {
    if model.active_step_cache().is_some() {
        return (selection_mode == STEP_OBJECT_MODE
            && model.properties_by_object.contains_key(requested_object_id))
            .then(|| requested_object_id.to_string())
            .or_else(|| model.properties_by_object.keys().next().cloned());
    }

    if selection_mode == "object" {
        return model
            .properties_by_object
            .contains_key(requested_object_id)
            .then(|| requested_object_id.to_string());
    }

    let selectable_ids = services
        .document
        .selectable_object_ids_for_mode(correlation_id, &model.bridge_snapshot, selection_mode);
    if selectable_ids.is_empty() {
        return None;
    }

    if selectable_ids.iter().any(|object_id| object_id == requested_object_id) {
        Some(requested_object_id.to_string())
    } else {
        selectable_ids.into_iter().next()
    }
}