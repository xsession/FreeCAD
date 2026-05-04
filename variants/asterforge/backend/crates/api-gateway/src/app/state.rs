use std::{path::PathBuf, sync::Arc};

pub use asterforge_command_core::CommandExecutionRequest;
use asterforge_document_core::DocumentSummary;
use asterforge_freecad_bridge::{
    BridgeRuntimeDescriptor,
};
use tokio::sync::RwLock;

use super::state_payloads::{AppSnapshot, BootPayload};
use super::state_requests::{
    ActivateWorkbenchRequest, PreselectionRequest, SelectionModeRequest, SelectionRequest,
    SelectionResponse, ShellPanelMutationRequest, ShellSessionMutationRequest,
};
use super::services::AppServices;
use super::state_types::AppModel;
use super::{state_commands, state_mutations, state_reads};

use crate::domain::{
    BackendEvent, CommandCatalogResponse,
    DiagnosticsResponse, FeatureHistoryResponse,
    JobStatusResponse, PreselectionStateResponse,
    PropertyResponse, SelectionStateResponse, ShellSnapshot,
    StepDocumentIndex, StepSceneBundle,
    TaskPanelResponse, ViewportResponse,
};

pub use super::state_commands::HttpCommandExecutionResponse;

pub(super) const STEP_OBJECT_MODE: &str = "object";
pub(super) const STEP_WORKBENCH_ID: &str = "step";
pub(super) const STEP_WORKBENCH_DISPLAY_NAME: &str = "STEP Inspection";
pub(super) const STEP_DEFAULT_CAMERA_EYE: [f32; 3] = [2.6, 2.2, 3.1];
pub(super) const STEP_DEFAULT_CAMERA_TARGET: [f32; 3] = [0.8, 0.7, 0.4];

#[derive(Clone)]
pub struct AppState {
    pub(super) inner: Arc<RwLock<AppModel>>,
    pub(super) services: Arc<AppServices>,
    pub(super) persistence_path: Option<PathBuf>,
}

impl AppState {
    pub async fn snapshot(&self) -> AppSnapshot {
        state_reads::snapshot(&self.inner).await
    }

    pub async fn bridge_runtime_descriptor(&self) -> BridgeRuntimeDescriptor {
        state_reads::bridge_runtime_descriptor(&self.inner, &self.services).await
    }

    #[allow(dead_code)]
    pub async fn boot_payload(&self) -> BootPayload {
        state_reads::boot_payload(&self.inner).await
    }

    pub async fn open_document(&self, file_path: String) -> DocumentSummary {
        state_mutations::open_document(
            &self.inner,
            &self.services,
            self.persistence_path.as_deref(),
            file_path,
        )
        .await
    }

    pub async fn set_selection(&self, request: SelectionRequest) -> Option<SelectionResponse> {
        state_mutations::set_selection(
            &self.inner,
            &self.services,
            self.persistence_path.as_deref(),
            request,
        )
        .await
    }

    pub async fn set_selection_mode(
        &self,
        request: SelectionModeRequest,
    ) -> Option<SelectionStateResponse> {
        state_mutations::set_selection_mode(
            &self.inner,
            &self.services,
            self.persistence_path.as_deref(),
            request,
        )
        .await
    }

    pub async fn activate_workbench(
        &self,
        request: ActivateWorkbenchRequest,
    ) -> Option<DocumentSummary> {
        state_mutations::activate_workbench(
            &self.inner,
            &self.services,
            self.persistence_path.as_deref(),
            request,
        )
        .await
    }

    pub async fn properties(&self, document_id: &str, object_id: &str) -> Option<PropertyResponse> {
        state_reads::properties(&self.inner, document_id, object_id).await
    }

    pub async fn events(&self, document_id: &str) -> Option<Vec<BackendEvent>> {
        state_reads::events(&self.inner, document_id).await
    }

    pub async fn viewport(&self, document_id: &str) -> Option<ViewportResponse> {
        state_reads::viewport(&self.inner, document_id).await
    }

    pub async fn command_catalog(&self, document_id: &str) -> Option<CommandCatalogResponse> {
        state_reads::command_catalog(&self.inner, document_id).await
    }

    pub async fn shell_snapshot(&self, document_id: &str) -> Option<ShellSnapshot> {
        state_reads::shell_snapshot(&self.inner, document_id).await
    }

    pub async fn update_shell_panel(
        &self,
        request: ShellPanelMutationRequest,
    ) -> Option<ShellSnapshot> {
        state_mutations::update_shell_panel(
            &self.inner,
            &self.services,
            self.persistence_path.as_deref(),
            request,
        )
        .await
    }

    pub async fn update_shell_sessions(
        &self,
        request: ShellSessionMutationRequest,
    ) -> Option<ShellSnapshot> {
        state_mutations::update_shell_sessions(
            &self.inner,
            &self.services,
            self.persistence_path.as_deref(),
            request,
        )
        .await
    }

    pub async fn feature_history(&self, document_id: &str) -> Option<FeatureHistoryResponse> {
        state_reads::feature_history(&self.inner, document_id).await
    }

    pub async fn task_panel(&self, document_id: &str) -> Option<TaskPanelResponse> {
        state_reads::task_panel(&self.inner, document_id).await
    }

    pub async fn diagnostics(&self, document_id: &str) -> Option<DiagnosticsResponse> {
        state_reads::diagnostics(&self.inner, document_id).await
    }

    pub async fn selection_state(&self, document_id: &str) -> Option<SelectionStateResponse> {
        state_reads::selection_state(&self.inner, document_id).await
    }

    #[allow(dead_code)]
    pub async fn preselection_state(
        &self,
        document_id: &str,
    ) -> Option<PreselectionStateResponse> {
        state_reads::preselection_state(&self.inner, document_id).await
    }

    pub async fn set_preselection(
        &self,
        request: PreselectionRequest,
    ) -> Option<PreselectionStateResponse> {
        state_mutations::set_preselection(&self.inner, &self.services, request).await
    }

    pub async fn jobs(&self, document_id: &str) -> Option<JobStatusResponse> {
        state_reads::jobs(&self.inner, document_id).await
    }

    pub async fn run_command(
        &self,
        request: CommandExecutionRequest,
    ) -> Option<HttpCommandExecutionResponse> {
        state_commands::run_command(
            &self.inner,
            &self.services,
            self.persistence_path.as_deref(),
            request,
        )
        .await
    }

    pub async fn step_document_index(
        &self,
        document_id: &str,
    ) -> anyhow::Result<Option<StepDocumentIndex>> {
        state_reads::step_document_index(&self.inner, document_id).await
    }

    pub async fn step_scene_bundle(
        &self,
        document_id: &str,
    ) -> anyhow::Result<Option<StepSceneBundle>> {
        state_reads::step_scene_bundle(&self.inner, document_id).await
    }
}
