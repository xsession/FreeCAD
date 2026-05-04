use super::services::AppServices;
use super::state_requests::{
    PreselectionRequest, SelectionModeRequest, SelectionRequest, SelectionResponse,
};
use super::state::STEP_OBJECT_MODE;
use super::state_types::AppModel;
use crate::domain::{BackendEvent, PreselectionStateResponse, SelectionStateResponse};

pub(super) fn apply_selection(
    services: &AppServices,
    correlation_id: &str,
    model: &mut AppModel,
    request: SelectionRequest,
) -> Option<SelectionResponse> {
    if model.document.document_id != request.document_id {
        return None;
    }
    let next_selection = model.normalize_selection_for_mode(
        services,
        correlation_id,
        &request.object_id,
        &model.selection_mode,
    )?;
    if !model.properties_by_object.contains_key(&next_selection) {
        return None;
    }

    if !model.is_step_document() {
        model.bridge_snapshot.selected_object_id = next_selection.clone();
    }
    model.selected_object_id = next_selection.clone();
    model.preselected_object_id = None;
    if model.is_step_document() {
        model.remember_current_document(services);
    } else {
        model.sync_from_snapshot(services, correlation_id);
    }
    let document_id = model.document.document_id.clone();
    let selection_mode = model.selection_mode.clone();
    let selection_message = if next_selection == request.object_id {
        format!("Selected {}", next_selection)
    } else {
        format!(
            "Selection mode {} retargeted {} to {}",
            selection_mode, request.object_id, next_selection
        )
    };
    model.events.insert(
        0,
        BackendEvent {
            topic: "selection_changed".into(),
            level: "info".into(),
            message: selection_message,
            document_id: document_id.clone(),
            object_id: Some(next_selection.clone()),
        },
    );
    model.events.insert(
        1,
        BackendEvent {
            topic: "viewport_updated".into(),
            level: "info".into(),
            message: "Viewport synchronized to backend-owned selection".into(),
            document_id,
            object_id: Some(next_selection.clone()),
        },
    );

    Some(SelectionResponse {
        selected_object_id: next_selection,
    })
}

pub(super) fn apply_selection_mode(
    services: &AppServices,
    correlation_id: &str,
    model: &mut AppModel,
    request: SelectionModeRequest,
) -> Option<SelectionStateResponse> {
    if model.document.document_id != request.document_id {
        return None;
    }

    if !["object", "body", "sketch", "feature"].contains(&request.mode_id.as_str()) {
        return None;
    }

    if model.is_step_document() && request.mode_id != STEP_OBJECT_MODE {
        return None;
    }

    let next_selection = model.normalize_selection_for_mode(
        services,
        correlation_id,
        &model.selected_object_id,
        &request.mode_id,
    )?;

    model.selection_mode = request.mode_id;
    if !model.is_step_document() {
        model.bridge_snapshot.selected_object_id = next_selection.clone();
    }
    model.selected_object_id = next_selection.clone();
    model.preselected_object_id = None;
    if model.is_step_document() {
        model.remember_current_document(services);
    } else {
        model.sync_from_snapshot(services, correlation_id);
    }
    let document_id = model.document.document_id.clone();
    let selection_mode = model.selection_mode.clone();
    let mode_message = format!(
        "Selection mode set to {} with {} active",
        selection_mode, next_selection
    );
    model.events.insert(
        0,
        BackendEvent {
            topic: "selection_mode_changed".into(),
            level: "info".into(),
            message: mode_message,
            document_id,
            object_id: Some(next_selection),
        },
    );

    Some(model.selection_state())
}

pub(super) fn apply_preselection(
    services: &AppServices,
    correlation_id: &str,
    model: &mut AppModel,
    request: PreselectionRequest,
) -> Option<PreselectionStateResponse> {
    if model.document.document_id != request.document_id {
        return None;
    }

    let next_preselection = request.object_id.as_deref().and_then(|object_id| {
        let selectable_ids = model.selectable_object_ids_for_active_mode(services, correlation_id);
        selectable_ids
            .into_iter()
            .find(|candidate| candidate == object_id)
    });

    model.preselected_object_id = next_preselection.clone();
    let document_id = model.document.document_id.clone();
    let message = match next_preselection.as_ref() {
        Some(object_id) => format!("Preselection tracking {}", object_id),
        None => "Preselection cleared".into(),
    };
    model.events.insert(
        0,
        BackendEvent {
            topic: "preselection_changed".into(),
            level: "info".into(),
            message,
            document_id,
            object_id: next_preselection,
        },
    );

    Some(model.preselection_state())
}