use asterforge_protocol_types::asterforge::protocol::v1::{
    BootPayload as ProtoBootPayload, CommandCatalogResponse as ProtoCommandCatalogResponse,
    CommandInvocation, CommandReply, DiagnosticsResponse as ProtoDiagnosticsResponse,
    DocumentRef as ProtoDocumentRef, EventEnvelope as ProtoEventEnvelope,
    FeatureHistoryResponse as ProtoFeatureHistoryResponse,
    JobStatusResponse as ProtoJobStatusResponse, ObjectTreeResponse as ProtoObjectTreeResponse,
    PreselectionRequest as ProtoPreselectionRequest,
    PreselectionState as ProtoPreselectionState, PropertyResponse as ProtoPropertyResponse,
    SelectionModeRequest as ProtoSelectionModeRequest, SelectionRef, SelectionReply,
    SelectionState as ProtoSelectionState,
    ShellPanelMutationRequest as ProtoShellPanelMutationRequest,
    ShellSessionMutationRequest as ProtoShellSessionMutationRequest,
    ShellSnapshot as ProtoShellSnapshot, TaskPanelResponse as ProtoTaskPanelResponse,
    ViewportResponse as ProtoViewportResponse,
    WorkbenchActivationRequest as ProtoWorkbenchActivationRequest,
};

use super::protocol::{
    preselection_state_proto_from_http, proto_document_ref_from_http,
    proto_shell_snapshot_from_http, selection_reply_from_http,
    selection_state_proto_from_http,
};
use super::state::AppState;
use super::state_requests::{
    ActivateWorkbenchRequest, PreselectionRequest, SelectionModeRequest,
    SelectionRequest, ShellPanelMutationRequest, ShellSessionMutationRequest,
};

impl AppState {
    pub async fn boot_payload_proto(&self) -> ProtoBootPayload {
        super::state_reads::boot_payload_proto(&self.inner).await
    }

    pub async fn set_selection_proto(&self, request: SelectionRef) -> Option<SelectionReply> {
        self.set_selection(SelectionRequest {
            document_id: request.document_id,
            object_id: request.object_id,
        })
        .await
        .map(selection_reply_from_http)
    }

    pub async fn set_selection_mode_proto(
        &self,
        request: ProtoSelectionModeRequest,
    ) -> Option<ProtoSelectionState> {
        self.set_selection_mode(SelectionModeRequest {
            document_id: request.document_id,
            mode_id: request.mode_id,
        })
        .await
        .map(selection_state_proto_from_http)
    }

    #[allow(dead_code)]
    pub async fn activate_workbench_proto(
        &self,
        request: ProtoWorkbenchActivationRequest,
    ) -> Option<ProtoDocumentRef> {
        self.activate_workbench(ActivateWorkbenchRequest {
            document_id: request.document_id,
            workbench_id: request.workbench_id,
        })
        .await
        .map(proto_document_ref_from_http)
    }

    pub async fn object_tree_proto(&self, document_id: &str) -> Option<ProtoObjectTreeResponse> {
        super::state_reads::object_tree_proto(&self.inner, document_id).await
    }

    pub async fn properties_proto(
        &self,
        document_id: &str,
        object_id: &str,
    ) -> Option<ProtoPropertyResponse> {
        super::state_reads::properties_proto(&self.inner, document_id, object_id).await
    }

    pub async fn events_proto(&self, document_id: &str) -> Option<Vec<ProtoEventEnvelope>> {
        super::state_reads::events_proto(&self.inner, document_id).await
    }

    pub async fn viewport_proto(&self, document_id: &str) -> Option<ProtoViewportResponse> {
        super::state_reads::viewport_proto(&self.inner, document_id).await
    }

    pub async fn shell_snapshot_proto(&self, document_id: &str) -> Option<ProtoShellSnapshot> {
        super::state_reads::shell_snapshot_proto(&self.inner, document_id).await
    }

    #[allow(dead_code)]
    pub async fn update_shell_panel_proto(
        &self,
        request: ProtoShellPanelMutationRequest,
    ) -> Option<ProtoShellSnapshot> {
        self.update_shell_panel(ShellPanelMutationRequest {
            document_id: request.document_id,
            panel_id: request.panel_id,
            active_tab: request.active_tab,
            visible: request.visible,
            size_hint: request.size_hint,
        })
        .await
        .map(proto_shell_snapshot_from_http)
    }

    #[allow(dead_code)]
    pub async fn update_shell_sessions_proto(
        &self,
        request: ProtoShellSessionMutationRequest,
    ) -> Option<ProtoShellSnapshot> {
        self.update_shell_sessions(ShellSessionMutationRequest {
            document_id: request.document_id,
            remove_workspace_session_id: request.remove_workspace_session_id,
            clear_recent_documents: request.clear_recent_documents,
            clear_inactive_workspace_sessions: request.clear_inactive_workspace_sessions,
        })
        .await
        .map(proto_shell_snapshot_from_http)
    }

    pub async fn command_catalog_proto(
        &self,
        document_id: &str,
    ) -> Option<ProtoCommandCatalogResponse> {
        super::state_reads::command_catalog_proto(&self.inner, document_id).await
    }

    pub async fn feature_history_proto(
        &self,
        document_id: &str,
    ) -> Option<ProtoFeatureHistoryResponse> {
        super::state_reads::feature_history_proto(&self.inner, document_id).await
    }

    pub async fn task_panel_proto(&self, document_id: &str) -> Option<ProtoTaskPanelResponse> {
        super::state_reads::task_panel_proto(&self.inner, document_id).await
    }

    pub async fn diagnostics_proto(
        &self,
        document_id: &str,
    ) -> Option<ProtoDiagnosticsResponse> {
        super::state_reads::diagnostics_proto(&self.inner, document_id).await
    }

    pub async fn selection_state_proto(&self, document_id: &str) -> Option<ProtoSelectionState> {
        super::state_reads::selection_state_proto(&self.inner, document_id).await
    }

    pub async fn preselection_state_proto(
        &self,
        document_id: &str,
    ) -> Option<ProtoPreselectionState> {
        super::state_reads::preselection_state_proto(&self.inner, document_id).await
    }

    pub async fn set_preselection_proto(
        &self,
        request: ProtoPreselectionRequest,
    ) -> Option<ProtoPreselectionState> {
        self.set_preselection(PreselectionRequest {
            document_id: request.document_id,
            object_id: request.object_id,
        })
        .await
        .map(preselection_state_proto_from_http)
    }

    pub async fn jobs_proto(&self, document_id: &str) -> Option<ProtoJobStatusResponse> {
        super::state_reads::jobs_proto(&self.inner, document_id).await
    }

    pub async fn run_command_proto(&self, request: CommandInvocation) -> Option<CommandReply> {
        super::state_commands::run_command_proto(
            &self.inner,
            &self.services,
            self.persistence_path.as_deref(),
            request,
        )
        .await
    }
}