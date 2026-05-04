use asterforge_document_core::DocumentSummary;

use super::state_requests::{
    ActivateWorkbenchRequest, ShellPanelMutationRequest, ShellSessionMutationRequest,
};
use super::services::AppServices;
use super::state::{STEP_WORKBENCH_DISPLAY_NAME, STEP_WORKBENCH_ID};
use super::state_types::AppModel;
use crate::domain::{
    normalize_workbench_id, workbench_display_name, BackendEvent, ShellSnapshot,
};

pub(super) fn apply_activate_workbench(
    services: &AppServices,
    model: &mut AppModel,
    request: ActivateWorkbenchRequest,
) -> Option<DocumentSummary> {
    if model.document.document_id != request.document_id {
        return None;
    }

    let workbench_id = normalize_workbench_id(&request.workbench_id);
    let next_workbench = if model.is_step_document() {
        if workbench_id != STEP_WORKBENCH_ID {
            return None;
        }
        STEP_WORKBENCH_DISPLAY_NAME.to_string()
    } else {
        if !["partdesign", "part", "sketcher", "mesh"].contains(&workbench_id.as_str()) {
            return None;
        }
        workbench_display_name(&workbench_id)
    };
    let document_id = model.document.document_id.clone();
    let selected_object_id = model.selected_object_id.clone();
    model.bridge_snapshot.workbench = next_workbench.clone();
    model.document.summary.workbench = next_workbench.clone();
    model.preselected_object_id = None;
    model.remember_current_document(services);
    model.events.insert(
        0,
        BackendEvent {
            topic: "workbench_changed".into(),
            level: "info".into(),
            message: format!("Activated {} workbench", next_workbench),
            document_id,
            object_id: Some(selected_object_id),
        },
    );

    Some(model.document.summary().clone())
}

pub(super) fn apply_shell_panel_update(
    services: &AppServices,
    model: &mut AppModel,
    request: ShellPanelMutationRequest,
) -> Option<ShellSnapshot> {
    if model.document.document_id != request.document_id {
        return None;
    }

    match request.panel_id.as_str() {
        "combo_view" => {
            if let Some(active_tab) = request.active_tab.as_deref() {
                if !["model", "tasks"].contains(&active_tab) {
                    return None;
                }
                model.combo_view_tab = active_tab.to_string();
            }
            if let Some(visible) = request.visible {
                model.combo_view_visible = visible;
            }
            if let Some(size_hint) = request.size_hint {
                model.combo_view_size_hint = size_hint.clamp(0.22, 0.42);
            }
        }
        "report_dock" => {
            if let Some(active_tab) = request.active_tab.as_deref() {
                if !["report", "python", "jobs", "diagnostics", "history", "commands"]
                    .contains(&active_tab)
                {
                    return None;
                }
                model.bottom_dock_tab = active_tab.to_string();
            }
            if let Some(visible) = request.visible {
                model.report_dock_visible = visible;
            }
            if let Some(size_hint) = request.size_hint {
                model.report_dock_size_hint = size_hint.clamp(0.18, 0.4);
            }
        }
        _ => return None,
    }

    model.remember_current_document(services);

    let document_id = model.document.document_id.clone();
    let selected_object_id = model.selected_object_id.clone();
    let detail = request
        .active_tab
        .clone()
        .or_else(|| request.visible.map(|visible| if visible { "visible".into() } else { "hidden".into() }))
        .or_else(|| request.size_hint.map(|value| format!("size {:.2}", value)))
        .unwrap_or_else(|| "updated".into());

    model.events.insert(
        0,
        BackendEvent {
            topic: "shell_layout_changed".into(),
            level: "info".into(),
            message: format!("{} -> {}", request.panel_id, detail),
            document_id,
            object_id: Some(selected_object_id),
        },
    );

    Some(model.shell_snapshot())
}

pub(super) fn apply_shell_session_update(
    services: &AppServices,
    model: &mut AppModel,
    request: ShellSessionMutationRequest,
) -> Option<ShellSnapshot> {
    if model.document.document_id != request.document_id {
        return None;
    }

    let active_session_id = model.active_session_id();
    let mut changed = false;

    if request.clear_recent_documents {
        model.recent_documents.clear();
        changed = true;
    }

    if request.clear_inactive_workspace_sessions {
        model.workspace_sessions
            .retain(|entry| entry.session_id == active_session_id);
        changed = true;
    }

    if let Some(session_id) = request.remove_workspace_session_id.as_deref() {
        if session_id == active_session_id {
            return None;
        }
        let previous_len = model.workspace_sessions.len();
        model
            .workspace_sessions
            .retain(|entry| entry.session_id != session_id);
        changed |= model.workspace_sessions.len() != previous_len;
    }

    if !changed {
        return Some(model.shell_snapshot());
    }

    model.remember_current_document(services);

    let document_id = model.document.document_id.clone();
    let selected_object_id = model.selected_object_id.clone();
    let detail = if request.clear_recent_documents && request.clear_inactive_workspace_sessions {
        "cleared recent documents and inactive sessions".to_string()
    } else if request.clear_recent_documents {
        "cleared recent documents".to_string()
    } else if request.clear_inactive_workspace_sessions {
        "cleared inactive workspace sessions".to_string()
    } else if let Some(session_id) = request.remove_workspace_session_id {
        format!("dismissed workspace session {session_id}")
    } else {
        "updated shell session state".to_string()
    };

    model.events.insert(
        0,
        BackendEvent {
            topic: "shell_session_changed".into(),
            level: "info".into(),
            message: detail,
            document_id,
            object_id: Some(selected_object_id),
        },
    );

    Some(model.shell_snapshot())
}