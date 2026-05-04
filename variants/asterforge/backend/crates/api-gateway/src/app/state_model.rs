use super::services::AppServices;
use super::state_types::{AppModel, PersistedWorkspaceState, StepCacheEntry};
use super::{state_step_cache, state_sync, state_views, state_workspace};
use crate::domain::{
    CommandCatalogResponse, DiagnosticsResponse, FeatureHistoryResponse, JobStatusResponse,
    ObjectNode, PreselectionStateResponse, SelectionStateResponse, ShellSnapshot,
    TaskPanelResponse, ViewportResponse,
};

impl AppModel {
    pub(super) fn active_step_cache(&self) -> Option<&StepCacheEntry> {
        self.step_cache_by_document.get(&self.document.document_id)
    }

    pub(super) fn is_step_document(&self) -> bool {
        state_step_cache::is_step_document(self)
    }

    pub(super) fn selectable_object_ids_for_active_mode(
        &self,
        services: &AppServices,
        correlation_id: &str,
    ) -> Vec<String> {
        state_sync::selectable_object_ids_for_active_mode(services, correlation_id, self)
    }

    pub(super) fn apply_step_projection_for_active_document(&mut self, document_id: &str) {
        state_step_cache::apply_step_projection_for_active_document(self, document_id)
    }

    pub(super) fn viewport(&self) -> ViewportResponse {
        state_views::viewport(self)
    }

    pub(super) fn command_catalog(&self) -> CommandCatalogResponse {
        state_views::command_catalog(self)
    }

    pub(super) fn shell_snapshot(&self) -> ShellSnapshot {
        state_views::shell_snapshot(self)
    }

    pub(super) fn feature_history(&self) -> FeatureHistoryResponse {
        self.document.history().clone()
    }

    pub(super) fn task_panel(&self) -> TaskPanelResponse {
        state_views::task_panel(self)
    }

    pub(super) fn diagnostics(&self) -> DiagnosticsResponse {
        state_views::diagnostics(self)
    }

    pub(super) fn selection_state(&self) -> SelectionStateResponse {
        state_views::selection_state(self)
    }

    pub(super) fn preselection_state(&self) -> PreselectionStateResponse {
        state_views::preselection_state(self)
    }

    pub(super) fn jobs(&self) -> JobStatusResponse {
        JobStatusResponse {
            document_id: self.document.document_id.clone(),
            jobs: self.jobs.clone(),
        }
    }

    pub(super) fn sync_from_snapshot(&mut self, services: &AppServices, correlation_id: &str) {
        state_sync::sync_from_snapshot(services, correlation_id, self)
    }

    pub(super) fn apply_command_target(
        &mut self,
        services: &AppServices,
        correlation_id: &str,
        target_object_id: Option<&str>,
    ) -> bool {
        state_sync::apply_command_target(services, correlation_id, self, target_object_id)
    }

    pub(super) fn remember_current_document(&mut self, services: &AppServices) {
        state_workspace::remember_current_document(services, self)
    }

    pub(super) fn active_session_id(&self) -> String {
        state_workspace::active_session_id(self)
    }

    pub(super) fn persisted_workspace_state(&self) -> PersistedWorkspaceState {
        state_workspace::persisted_workspace_state(self)
    }

    pub(super) fn normalize_selection_for_mode(
        &self,
        services: &AppServices,
        correlation_id: &str,
        requested_object_id: &str,
        selection_mode: &str,
    ) -> Option<String> {
        state_sync::normalize_selection_for_mode(
            services,
            correlation_id,
            self,
            requested_object_id,
            selection_mode,
        )
    }
}

pub(super) fn flatten_object_nodes(nodes: &[ObjectNode]) -> Vec<&ObjectNode> {
    let mut flattened = Vec::new();
    for node in nodes {
        flattened.push(node);
        flattened.extend(flatten_object_nodes(&node.children));
    }
    flattened
}