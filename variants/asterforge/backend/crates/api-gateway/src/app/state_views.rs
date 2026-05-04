use super::state_types::AppModel;
use super::state_model::flatten_object_nodes;
use super::state_step_views::{
    step_command_catalog_response, step_diagnostics_response, step_preselection_state_response,
    step_selection_state_response, step_shell_inspection_state, step_task_panel_response,
    step_viewport_response,
};
use super::state_step_tools::{
    hidden_step_object_count, step_measurement_for_selection, step_selected_object_is_visible,
};
use crate::domain::{
    command_catalog_from_bridge, diagnostics_from_bridge, find_pad_length_mm,
    preselection_state_from_bridge, selection_state_from_bridge, shell_snapshot_from_bridge,
    step_shell_snapshot, task_panel_from_bridge, viewport_from_bridge, CommandCatalogResponse,
    DiagnosticsResponse, PreselectionStateResponse, SelectionStateResponse, ShellSnapshot,
    ShellStatusBarItem, ShellStatusBarState, TaskPanelResponse, ViewportResponse,
};

pub(super) fn viewport(model: &AppModel) -> ViewportResponse {
    model
        .active_step_cache()
        .map(|cache| {
            step_viewport_response(
                &model.document.document_id,
                &model.selected_object_id,
                cache,
                &model.object_tree,
                model
                    .step_viewport_camera_by_document
                    .get(&model.document.document_id),
            )
        })
        .unwrap_or_else(|| viewport_from_bridge(&model.bridge_snapshot, &model.selected_object_id))
}

pub(super) fn command_catalog(model: &AppModel) -> CommandCatalogResponse {
    model
        .active_step_cache()
        .map(|cache| {
            step_command_catalog_response(
                &model.document.document_id,
                &model.selected_object_id,
                cache,
                &model.object_tree,
                model.step_measurement_by_document.get(&model.document.document_id),
            )
        })
        .unwrap_or_else(|| {
            command_catalog_from_bridge(
                &model.bridge_snapshot,
                &model.document.document_id,
                Some(&model.selected_object_id),
                model.undo_stack.can_undo(),
                model.undo_stack.can_redo(),
            )
        })
}

pub(super) fn shell_snapshot(model: &AppModel) -> ShellSnapshot {
    let mut snapshot = model
        .active_step_cache()
        .map(|cache| {
            step_shell_snapshot(
                model.document.summary(),
                &model.extension_compatibility,
                Some(&model.selected_object_id),
                &model.recent_documents,
                &model.workspace_sessions,
                &model.combo_view_tab,
                &model.bottom_dock_tab,
                model.combo_view_visible,
                model.report_dock_visible,
                model.combo_view_size_hint,
                model.report_dock_size_hint,
                &cache.scene_bundle,
                step_selected_object_is_visible(&model.object_tree, &model.selected_object_id),
                flatten_object_nodes(&model.object_tree).len() > 1,
                hidden_step_object_count(&model.object_tree) > 0,
                step_measurement_for_selection(&model.selected_object_id, cache).is_some(),
                step_shell_inspection_state(
                    &model.selected_object_id,
                    model
                        .step_pmi_inspection_by_document
                        .get(&model.document.document_id),
                    model.step_measurement_by_document.get(&model.document.document_id),
                ),
            )
        })
        .unwrap_or_else(|| {
            shell_snapshot_from_bridge(
                &model.bridge_snapshot,
                model.document.summary(),
                &model.extension_compatibility,
                Some(&model.selected_object_id),
                model.undo_stack.can_undo(),
                model.undo_stack.can_redo(),
                &model.recent_documents,
                &model.workspace_sessions,
                &model.combo_view_tab,
                &model.bottom_dock_tab,
                model.combo_view_visible,
                model.report_dock_visible,
                model.combo_view_size_hint,
                model.report_dock_size_hint,
            )
        });

    snapshot.status_bar = Some(build_shell_status_bar(model, &snapshot));
    snapshot
}

pub(super) fn task_panel(model: &AppModel) -> TaskPanelResponse {
    model
        .active_step_cache()
        .map(|cache| {
            step_task_panel_response(
                &model.document.document_id,
                &model.selected_object_id,
                cache,
                &model.object_tree,
                model.step_pmi_inspection_by_document.get(&model.document.document_id),
                model.step_measurement_by_document.get(&model.document.document_id),
            )
        })
        .unwrap_or_else(|| {
            task_panel_from_bridge(
                &model.bridge_snapshot,
                &model.document.document_id,
                Some(&model.selected_object_id),
                find_pad_length_mm(&model.bridge_snapshot, &model.selected_object_id),
                model.undo_stack.can_undo(),
                model.undo_stack.can_redo(),
            )
        })
}

pub(super) fn diagnostics(model: &AppModel) -> DiagnosticsResponse {
    model
        .active_step_cache()
        .map(|cache| {
            step_diagnostics_response(
                &model.document.document_id,
                &model.selected_object_id,
                &model.events,
                &model.bridge_status.worker_mode,
                cache,
                &model.object_tree,
            )
        })
        .unwrap_or_else(|| {
            let mut diagnostics = diagnostics_from_bridge(
                &model.bridge_snapshot,
                Some(&model.selected_object_id),
                &model.events,
                &model.bridge_status,
            );
            diagnostics.summary.total_features = model.document.evaluation().total_features;
            diagnostics.summary.suppressed_count = model.document.evaluation().suppressed_count;
            diagnostics.summary.inactive_count = model.document.evaluation().inactive_count;
            diagnostics.summary.rolled_back_count = model.document.evaluation().rolled_back_count;
            diagnostics.summary.history_marker_active = model.document.evaluation().history_marker_active;
            diagnostics.summary.worker_mode = model.document.evaluation().worker_mode.clone();
            diagnostics
        })
}

pub(super) fn selection_state(model: &AppModel) -> SelectionStateResponse {
    model
        .active_step_cache()
        .map(|_| {
            step_selection_state_response(
                &model.document.document_id,
                &model.selected_object_id,
                &model.selection_mode,
                &model.object_tree,
            )
        })
        .unwrap_or_else(|| {
            selection_state_from_bridge(
                &model.bridge_snapshot,
                &model.selected_object_id,
                &model.selection_mode,
            )
        })
}

pub(super) fn preselection_state(model: &AppModel) -> PreselectionStateResponse {
    model
        .active_step_cache()
        .map(|cache| {
            step_preselection_state_response(
                &model.document.document_id,
                model.preselected_object_id.as_deref(),
                &model.selection_mode,
                cache,
                &model.object_tree,
            )
        })
        .unwrap_or_else(|| {
            preselection_state_from_bridge(
                &model.bridge_snapshot,
                model.preselected_object_id.as_deref(),
                &model.selection_mode,
                model.undo_stack.can_undo(),
                model.undo_stack.can_redo(),
            )
        })
}

fn build_shell_status_bar(model: &AppModel, shell_snapshot: &ShellSnapshot) -> ShellStatusBarState {
    let selection_state = model.selection_state();
    let diagnostics = model.diagnostics();
    let jobs = model.jobs();
    let visible_panels = shell_snapshot
        .layout
        .panels
        .iter()
        .filter(|panel| panel.visible)
        .count();
    let total_panels = shell_snapshot.layout.panels.len();
    let active_workbench = shell_snapshot
        .workbench_catalog
        .workbenches
        .iter()
        .find(|workbench| {
            workbench.workbench_id == shell_snapshot.workbench_catalog.active_workbench_id
        })
        .map(|workbench| workbench.display_name.clone())
        .unwrap_or_else(|| model.document.workbench.clone());
    let selection_mode = selection_state
        .available_modes
        .iter()
        .find(|mode| mode.mode_id == selection_state.current_mode)
        .map(|mode| mode.label.clone())
        .unwrap_or_else(|| title_case_shell_token(&selection_state.current_mode, "Object"));
    let selection_summary = if !selection_state.selected_object_label.is_empty() {
        selection_state.selected_object_label
    } else if !selection_state.selected_object_id.is_empty() {
        selection_state.selected_object_id
    } else {
        "None".into()
    };
    let dock_summary = shell_snapshot
        .layout
        .panels
        .iter()
        .find(|panel| panel.panel_id == "report_dock")
        .map(|panel| {
            if panel.visible {
                title_case_shell_token(panel.active_tab.as_deref().unwrap_or("report"), "Report")
            } else {
                "Hidden".into()
            }
        })
        .unwrap_or_else(|| "Report".into());
    let worker_mode = title_case_shell_token(&model.bridge_status.worker_mode, "Unknown");
    let warning_count = diagnostics.summary.warning_count;
    let error_count = diagnostics.summary.error_count;
    let diagnostics_summary = if error_count > 0 {
        format!("{} errors, {} warnings", error_count, warning_count)
    } else if warning_count > 0 {
        format!("{} warnings", warning_count)
    } else {
        "Clear".into()
    };
    let diagnostics_tone = if error_count > 0 {
        "error"
    } else if warning_count > 0 {
        "warning"
    } else {
        "info"
    };

    ShellStatusBarState {
        items: vec![
            status_bar_item("workbench", "Workbench", &active_workbench, "neutral"),
            status_bar_item("document", "Document", &model.document.display_name, "neutral"),
            status_bar_item(
                "state",
                "State",
                if model.document.dirty { "Modified" } else { "Saved" },
                if model.document.dirty { "warning" } else { "info" },
            ),
            status_bar_item("mode", "Mode", &selection_mode, "neutral"),
            status_bar_item("selection", "Selection", &selection_summary, "neutral"),
            status_bar_item("diagnostics", "Diagnostics", &diagnostics_summary, diagnostics_tone),
            status_bar_item(
                "dock",
                "Dock",
                &dock_summary,
                if dock_summary == "Hidden" { "warning" } else { "info" },
            ),
            status_bar_item("worker", "Worker", &worker_mode, "neutral"),
            status_bar_item(
                "jobs",
                "Jobs",
                &jobs.jobs.len().to_string(),
                if jobs.jobs.is_empty() { "info" } else { "warning" },
            ),
            status_bar_item(
                "panels",
                "Panels",
                &format!("{}/{} visible", visible_panels, total_panels),
                "neutral",
            ),
        ],
    }
}

fn status_bar_item(item_id: &str, label: &str, value: &str, tone: &str) -> ShellStatusBarItem {
    ShellStatusBarItem {
        item_id: item_id.into(),
        label: label.into(),
        value: value.into(),
        tone: tone.into(),
    }
}

fn title_case_shell_token(value: &str, fallback: &str) -> String {
    if value.is_empty() {
        return fallback.into();
    }

    value
        .split(['_', '-'])
        .filter(|segment| !segment.is_empty())
        .map(|segment| {
            let mut chars = segment.chars();
            match chars.next() {
                Some(first) => format!("{}{}", first.to_ascii_uppercase(), chars.as_str()),
                None => String::new(),
            }
        })
        .collect::<Vec<_>>()
        .join(" ")
}