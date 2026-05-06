use std::{fs, path::{Path, PathBuf}, sync::atomic::{AtomicU64, Ordering}};

use asterforge_document_core::DocumentWorkspaceState;

use crate::domain::{normalize_workbench_id, RecentDocumentEntry, WorkspaceSessionEntry};

use super::services::AppServices;
use super::state_types::{AppModel, PersistedWorkspaceState};

pub(super) fn remember_current_document(services: &AppServices, model: &mut AppModel) {
    let file_path = model
        .document
        .file_path
        .clone()
        .unwrap_or_else(|| format!("C:/models/{}.FCStd", model.document.display_name));
    let recent_entry = RecentDocumentEntry {
        file_path: file_path.clone(),
        display_name: model.document.display_name.clone(),
        workbench: model.document.workbench.clone(),
        dirty: model.document.dirty,
    };

    let session_id = format!("{}:{}", model.document.document_id, file_path);
    let session_entry = WorkspaceSessionEntry {
        session_id,
        document_id: model.document.document_id.clone(),
        display_name: model.document.display_name.clone(),
        file_path: file_path.clone(),
        workbench: model.document.workbench.clone(),
        dirty: model.document.dirty,
        selected_object_id: Some(model.selected_object_id.clone()),
        selection_mode: Some(model.selection_mode.clone()),
        combo_view_tab: Some(model.combo_view_tab.clone()),
        bottom_dock_tab: Some(model.bottom_dock_tab.clone()),
        combo_view_visible: Some(model.combo_view_visible),
        report_dock_visible: Some(model.report_dock_visible),
        combo_view_size_hint: Some(model.combo_view_size_hint),
        report_dock_size_hint: Some(model.report_dock_size_hint),
        report_dock_filter_label: model.report_dock_filter_label.clone(),
        report_dock_filter_query: model.report_dock_filter_query.clone(),
        diagnostics_dock_filter_label: model.diagnostics_dock_filter_label.clone(),
        diagnostics_dock_filter_query: model.diagnostics_dock_filter_query.clone(),
    };

    let mut workspace = DocumentWorkspaceState {
        recent_documents: std::mem::take(&mut model.recent_documents),
        workspace_sessions: std::mem::take(&mut model.workspace_sessions),
    };
    workspace.remember_document(recent_entry, session_entry);
    model.recent_documents = workspace.recent_documents;
    model.workspace_sessions = workspace.workspace_sessions;
    services
        .bridge
        .sync_session_snapshot(&active_session_id(model), &model.bridge_snapshot);
}

pub(super) fn active_session_id(model: &AppModel) -> String {
    let file_path = model
        .document
        .file_path
        .clone()
        .unwrap_or_else(|| format!("C:/models/{}.FCStd", model.document.display_name));
    format!(
        "{}:{}:{}",
        model.session_namespace, model.document.document_id, file_path
    )
}

pub(super) fn pending_session_id(session_namespace: &str, source_path: Option<&str>) -> String {
    let source_key = source_path.unwrap_or("untitled");
    format!("{}:pending:{}", session_namespace, source_key)
}

pub(super) fn apply_persisted_workspace_state(
    services: &AppServices,
    model: &mut AppModel,
    state: &PersistedWorkspaceState,
) {
    if let Some(selected_object_id) = state.selected_object_id.as_ref() {
        model.selected_object_id = selected_object_id.clone();
    }

    if let Some(selection_mode) = state.selection_mode.as_ref() {
        model.selection_mode = selection_mode.clone();
    }

    model.recent_documents = state.recent_documents.clone();
    model.workspace_sessions = state.workspace_sessions.clone();
    model.combo_view_tab = state.combo_view_tab.clone();
    model.bottom_dock_tab = state.bottom_dock_tab.clone();
    model.combo_view_visible = state.combo_view_visible;
    model.report_dock_visible = state.report_dock_visible;
    model.combo_view_size_hint = state.combo_view_size_hint;
    model.report_dock_size_hint = state.report_dock_size_hint;
    model.report_dock_filter_label = state.report_dock_filter_label.clone();
    model.report_dock_filter_query = state.report_dock_filter_query.clone();
    model.diagnostics_dock_filter_label = state.diagnostics_dock_filter_label.clone();
    model.diagnostics_dock_filter_query = state.diagnostics_dock_filter_query.clone();
    remember_current_document(services, model);
}

pub(super) fn persisted_workspace_state(model: &AppModel) -> PersistedWorkspaceState {
    PersistedWorkspaceState {
        active_document_path: model.document.file_path.clone(),
        active_workbench_id: Some(normalize_workbench_id(&model.document.workbench)),
        selected_object_id: Some(model.selected_object_id.clone()),
        selection_mode: Some(model.selection_mode.clone()),
        recent_documents: model.recent_documents.clone(),
        workspace_sessions: model.workspace_sessions.clone(),
        combo_view_tab: model.combo_view_tab.clone(),
        bottom_dock_tab: model.bottom_dock_tab.clone(),
        combo_view_visible: model.combo_view_visible,
        report_dock_visible: model.report_dock_visible,
        combo_view_size_hint: model.combo_view_size_hint,
        report_dock_size_hint: model.report_dock_size_hint,
        report_dock_filter_label: model.report_dock_filter_label.clone(),
        report_dock_filter_query: model.report_dock_filter_query.clone(),
        diagnostics_dock_filter_label: model.diagnostics_dock_filter_label.clone(),
        diagnostics_dock_filter_query: model.diagnostics_dock_filter_query.clone(),
    }
}

pub(super) fn default_persistence_path() -> Option<PathBuf> {
    #[cfg(test)]
    {
        return None;
    }

    #[cfg(not(test))]
    {
        if let Some(explicit) = std::env::var_os("ASTERFORGE_SHELL_STATE_FILE") {
            return Some(PathBuf::from(explicit));
        }

        if let Some(appdata) = std::env::var_os("APPDATA") {
            return Some(PathBuf::from(appdata).join("AsterForge").join("shell-state.json"));
        }

        if let Some(state_home) = std::env::var_os("XDG_STATE_HOME") {
            return Some(PathBuf::from(state_home).join("asterforge").join("shell-state.json"));
        }

        std::env::var_os("HOME")
            .map(|home| PathBuf::from(home).join(".asterforge").join("shell-state.json"))
    }
}

pub(super) fn next_session_namespace() -> String {
    static NEXT_SESSION_NAMESPACE: AtomicU64 = AtomicU64::new(1);
    format!(
        "app-session-{}",
        NEXT_SESSION_NAMESPACE.fetch_add(1, Ordering::Relaxed)
    )
}

pub(super) fn load_persisted_workspace_state(
    correlation_id: &str,
    path: &Path,
) -> Option<PersistedWorkspaceState> {
    let contents = match fs::read_to_string(path) {
        Ok(contents) => contents,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return None,
        Err(error) => {
            tracing::warn!(correlation_id, path = %path.display(), ?error, "failed to read persisted shell state");
            return None;
        }
    };

    match serde_json::from_str::<PersistedWorkspaceState>(&contents) {
        Ok(state) => Some(state),
        Err(error) => {
            tracing::warn!(correlation_id, path = %path.display(), ?error, "failed to parse persisted shell state");
            None
        }
    }
}

pub(super) fn save_persisted_workspace_state(
    correlation_id: &str,
    path: &Path,
    state: &PersistedWorkspaceState,
) {
    if let Some(parent) = path.parent() {
        if let Err(error) = fs::create_dir_all(parent) {
            tracing::warn!(correlation_id, path = %path.display(), ?error, "failed to create shell state directory");
            return;
        }
    }

    let contents = match serde_json::to_vec_pretty(state) {
        Ok(contents) => contents,
        Err(error) => {
            tracing::warn!(correlation_id, path = %path.display(), ?error, "failed to serialize persisted shell state");
            return;
        }
    };

    if let Err(error) = fs::write(path, contents) {
        tracing::warn!(correlation_id, path = %path.display(), ?error, "failed to write persisted shell state");
    }
}