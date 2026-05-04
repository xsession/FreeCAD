use asterforge_command_core::{
    BridgeCommandAdapter, BridgeCommandAdapterRequest, BridgeCommandAdapterResponse,
    BridgeCommandErrorCategory, BridgeCommandFailure,
    HistoryCommandAction, HistoryCommandAdapter, HistoryCommandAdapterResponse,
};
use asterforge_freecad_bridge::{
    apply_undo_action,
    bridge_runtime_descriptor, compute_viewport_diff, load_prototype_bridge_session, open_document_snapshot,
    sync_prototype_bridge_session,
    BridgeCommandRequest, BridgeCommandResponse, BridgeDocumentSnapshot,
    BridgeOperationResult, BridgeRuntimeDescriptor, BridgeSessionRequest, BridgeStatus,
    FreecadBridgeContract, PrototypeFreecadBridge, UndoAction, UndoStack, ViewportDiff,
    ViewportSnapshot,
};

use super::state_workspace;

fn runtime_descriptor_via_contract<B>(
    bridge: &B,
    correlation_id: &str,
) -> BridgeRuntimeDescriptor
where
    B: FreecadBridgeContract,
{
    tracing::debug!(correlation_id, "requesting bridge runtime descriptor");
    match bridge.describe_runtime() {
        Ok(descriptor) => descriptor,
        Err(error) => {
            let effective_correlation_id = error.correlation_id.as_deref().unwrap_or(correlation_id);
            tracing::warn!(
                correlation_id = effective_correlation_id,
                code = %error.code,
                "bridge runtime descriptor request failed; falling back to default descriptor"
            );
            bridge_runtime_descriptor()
        }
    }
}

fn open_document_snapshot_via_contract<B, F>(
    bridge: &B,
    correlation_id: &str,
    session_id: &str,
    source_path: Option<&str>,
    load_snapshot: F,
) -> BridgeDocumentSnapshot
where
    B: FreecadBridgeContract,
    F: FnOnce(&str) -> Option<BridgeDocumentSnapshot>,
{
    tracing::info!(correlation_id, session_id, source_path, "opening bridge-backed document session snapshot");
    let request = BridgeSessionRequest {
        session_id: session_id.to_string(),
        source_path: source_path.map(str::to_string),
        requested_workbench: None,
        options: asterforge_freecad_bridge::BridgeRequestOptions {
            timeout_ms: None,
            correlation_id: Some(correlation_id.to_string()),
            retry_safe: false,
        },
    };

    match bridge.open_document_session(request) {
        Ok(_) => load_snapshot(session_id).unwrap_or_else(|| {
            tracing::warn!(
                correlation_id,
                session_id,
                source_path,
                "bridge session opened without a retrievable snapshot; falling back to direct snapshot helper"
            );
            open_document_snapshot(source_path)
        }),
        Err(error) => {
            let effective_correlation_id = error.correlation_id.as_deref().unwrap_or(correlation_id);
            tracing::warn!(
                correlation_id = effective_correlation_id,
                session_id,
                source_path,
                code = %error.code,
                "bridge session open failed; falling back to direct snapshot helper"
            );
            open_document_snapshot(source_path)
        }
    }
}

#[derive(Debug, Clone, Copy)]
pub(super) struct BridgeServices {
    bridge: PrototypeFreecadBridge,
}

impl BridgeServices {
    pub(super) fn production() -> Self {
        Self {
            bridge: PrototypeFreecadBridge,
        }
    }

    pub(super) fn describe_runtime(
        &self,
        correlation_id: &str,
    ) -> BridgeRuntimeDescriptor {
        runtime_descriptor_via_contract(&self.bridge, correlation_id)
    }

    pub(super) fn describe_runtime_with_status(
        &self,
        correlation_id: &str,
        bridge_status: &BridgeStatus,
    ) -> BridgeRuntimeDescriptor {
        let mut descriptor = self.describe_runtime(correlation_id);
        descriptor.worker_mode = bridge_status.worker_mode.clone();
        descriptor.freecad_runtime_detected = bridge_status.freecad_runtime_detected;
        descriptor.capabilities = bridge_status.capabilities.clone();
        descriptor
    }

    pub(super) fn open_document_snapshot(
        &self,
        correlation_id: &str,
        session_id: &str,
        source_path: Option<&str>,
    ) -> BridgeDocumentSnapshot {
        open_document_snapshot_via_contract(
            &self.bridge,
            correlation_id,
            session_id,
            source_path,
            |session_id| self.load_session_snapshot(correlation_id, session_id),
        )
    }

    pub(super) fn open_pending_document_snapshot(
        &self,
        correlation_id: &str,
        session_namespace: &str,
        source_path: Option<&str>,
    ) -> BridgeDocumentSnapshot {
        let pending_session_id = state_workspace::pending_session_id(session_namespace, source_path);
        self.open_document_snapshot(correlation_id, &pending_session_id, source_path)
    }

    pub(super) fn execute_command(
        &self,
        correlation_id: &str,
        request: BridgeCommandRequest,
    ) -> BridgeOperationResult<BridgeCommandResponse> {
        tracing::info!(
            correlation_id,
            command_id = %request.command_id,
            session_id = %request.session_id,
            target_object_id = ?request.target_object_id,
            "dispatching bridge command"
        );
        self.bridge.execute_command(request)
    }

    pub(super) fn diff_viewport(
        &self,
        before: &ViewportSnapshot,
        after: &ViewportSnapshot,
    ) -> ViewportDiff {
        compute_viewport_diff(before, after)
    }

    pub(super) fn load_session_snapshot(
        &self,
        correlation_id: &str,
        session_id: &str,
    ) -> Option<BridgeDocumentSnapshot> {
        tracing::debug!(correlation_id, session_id, "loading bridge session snapshot");
        load_prototype_bridge_session(session_id)
    }

    pub(super) fn sync_session_snapshot(
        &self,
        session_id: &str,
        snapshot: &BridgeDocumentSnapshot,
    ) {
        sync_prototype_bridge_session(session_id, snapshot);
    }
}

impl BridgeCommandAdapter for BridgeServices {
    type Snapshot = BridgeDocumentSnapshot;

    fn execute_bridge_command(
        &self,
        correlation_id: &str,
        request: BridgeCommandAdapterRequest,
    ) -> Result<BridgeCommandAdapterResponse, BridgeCommandFailure> {
        let bridge_request = BridgeCommandRequest {
            session_id: request.session_id,
            command_id: request.command_id,
            target_object_id: request.target_object_id,
            arguments: request.arguments,
            options: asterforge_freecad_bridge::BridgeRequestOptions {
                timeout_ms: None,
                correlation_id: request.correlation_id,
                retry_safe: false,
            },
        };

        self.execute_command(correlation_id, bridge_request).map(|response| BridgeCommandAdapterResponse {
            command_id: response.command_id,
            accepted: response.accepted,
            status_message: response.status_message,
            document_dirty: response.document_dirty,
        }).map_err(|error| BridgeCommandFailure {
            category: match error.category {
                asterforge_freecad_bridge::BridgeErrorCategory::ValidationError => BridgeCommandErrorCategory::ValidationError,
                asterforge_freecad_bridge::BridgeErrorCategory::NativeError => BridgeCommandErrorCategory::NativeError,
                asterforge_freecad_bridge::BridgeErrorCategory::Timeout => BridgeCommandErrorCategory::Timeout,
                asterforge_freecad_bridge::BridgeErrorCategory::Cancelled => BridgeCommandErrorCategory::Cancelled,
                asterforge_freecad_bridge::BridgeErrorCategory::WorkerCrashed => BridgeCommandErrorCategory::WorkerCrashed,
                asterforge_freecad_bridge::BridgeErrorCategory::Unsupported => BridgeCommandErrorCategory::Unsupported,
            },
            code: error.code,
            summary: error.summary,
            detail: error.detail,
            correlation_id: error.correlation_id,
        })
    }

    fn load_bridge_session_snapshot(
        &self,
        correlation_id: &str,
        session_id: &str,
    ) -> Option<Self::Snapshot> {
        self.load_session_snapshot(correlation_id, session_id)
    }
}

#[derive(Debug, Clone, Copy)]
pub(super) struct HistoryServices;

impl HistoryCommandAdapter for HistoryServices {
    type Snapshot = BridgeDocumentSnapshot;
    type Stack = UndoStack;

    fn execute_history_command(
        &self,
        correlation_id: &str,
        action: HistoryCommandAction,
        stack: &mut Self::Stack,
        current_snapshot: &Self::Snapshot,
    ) -> HistoryCommandAdapterResponse<Self::Snapshot> {
        tracing::info!(
            correlation_id,
            action = ?action,
            "dispatching history command through explicit adapter"
        );
        let result = apply_undo_action(
            stack,
            current_snapshot,
            match action {
                HistoryCommandAction::Undo => UndoAction::Undo,
                HistoryCommandAction::Redo => UndoAction::Redo,
            },
        );

        HistoryCommandAdapterResponse {
            accepted: result.accepted,
            status_message: result.status_message,
            restored_snapshot: result.snapshot,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::{open_document_snapshot_via_contract, runtime_descriptor_via_contract};
    use asterforge_freecad_bridge::{
        bridge_runtime_descriptor, load_prototype_bridge_session, open_document_snapshot,
        sync_prototype_bridge_session, BridgeError, BridgeErrorCategory,
        BridgeOperationResult, BridgeSessionRequest, BridgeSessionResponse,
        BridgeViewportRequest, FreecadBridgeContract, NativeSessionToken,
        PrototypeFreecadBridge, ViewportSnapshot,
    };

    #[derive(Clone)]
    struct SuccessfulSessionBridge;

    impl FreecadBridgeContract for SuccessfulSessionBridge {
        fn describe_runtime(&self) -> BridgeOperationResult<asterforge_freecad_bridge::BridgeRuntimeDescriptor> {
            PrototypeFreecadBridge.describe_runtime()
        }

        fn open_document_session(
            &self,
            request: BridgeSessionRequest,
        ) -> BridgeOperationResult<BridgeSessionResponse> {
            let snapshot = open_document_snapshot(request.source_path.as_deref());
            sync_prototype_bridge_session(&request.session_id, &snapshot);
            Ok(BridgeSessionResponse {
                document_id: snapshot.document_id.clone(),
                display_name: snapshot.display_name.clone(),
                file_path: snapshot.file_path.clone(),
                dirty: snapshot.dirty,
                workbench: snapshot.workbench.clone(),
                token: NativeSessionToken {
                    session_id: request.session_id,
                    native_document_token: "mock:session-open-success".into(),
                },
            })
        }

        fn execute_command(
            &self,
            request: asterforge_freecad_bridge::BridgeCommandRequest,
        ) -> BridgeOperationResult<asterforge_freecad_bridge::BridgeCommandResponse> {
            PrototypeFreecadBridge.execute_command(request)
        }

        fn fetch_viewport(
            &self,
            request: BridgeViewportRequest,
        ) -> BridgeOperationResult<ViewportSnapshot> {
            PrototypeFreecadBridge.fetch_viewport(request)
        }
    }

    #[derive(Clone)]
    struct FailingSessionBridge;

    impl FreecadBridgeContract for FailingSessionBridge {
        fn describe_runtime(&self) -> BridgeOperationResult<asterforge_freecad_bridge::BridgeRuntimeDescriptor> {
            PrototypeFreecadBridge.describe_runtime()
        }

        fn open_document_session(
            &self,
            request: BridgeSessionRequest,
        ) -> BridgeOperationResult<BridgeSessionResponse> {
            Err(BridgeError {
                category: BridgeErrorCategory::ValidationError,
                code: "bridge.session_open_failed".into(),
                summary: "Failed to open bridge session".into(),
                detail: format!("Failed to open session {}", request.session_id),
                correlation_id: request.options.correlation_id,
            })
        }

        fn execute_command(
            &self,
            request: asterforge_freecad_bridge::BridgeCommandRequest,
        ) -> BridgeOperationResult<asterforge_freecad_bridge::BridgeCommandResponse> {
            PrototypeFreecadBridge.execute_command(request)
        }

        fn fetch_viewport(
            &self,
            request: BridgeViewportRequest,
        ) -> BridgeOperationResult<ViewportSnapshot> {
            PrototypeFreecadBridge.fetch_viewport(request)
        }
    }

    #[derive(Clone)]
    struct FailingRuntimeBridge;

    impl FreecadBridgeContract for FailingRuntimeBridge {
        fn describe_runtime(&self) -> BridgeOperationResult<asterforge_freecad_bridge::BridgeRuntimeDescriptor> {
            Err(BridgeError {
                category: BridgeErrorCategory::NativeError,
                code: "bridge.runtime_unavailable".into(),
                summary: "Runtime descriptor unavailable".into(),
                detail: "Descriptor lookup failed".into(),
                correlation_id: Some("af-runtime-fail".into()),
            })
        }

        fn open_document_session(
            &self,
            request: BridgeSessionRequest,
        ) -> BridgeOperationResult<BridgeSessionResponse> {
            PrototypeFreecadBridge.open_document_session(request)
        }

        fn execute_command(
            &self,
            request: asterforge_freecad_bridge::BridgeCommandRequest,
        ) -> BridgeOperationResult<asterforge_freecad_bridge::BridgeCommandResponse> {
            PrototypeFreecadBridge.execute_command(request)
        }

        fn fetch_viewport(
            &self,
            request: BridgeViewportRequest,
        ) -> BridgeOperationResult<ViewportSnapshot> {
            PrototypeFreecadBridge.fetch_viewport(request)
        }
    }

    #[test]
    fn document_open_uses_contract_session_snapshot_when_available() {
        let snapshot = open_document_snapshot_via_contract(
            &SuccessfulSessionBridge,
            "af-00000001",
            "session-open-success",
            Some("C:/models/contract-success.FCStd"),
            load_prototype_bridge_session,
        );

        assert_eq!(snapshot.file_path.as_deref(), Some("C:/models/contract-success.FCStd"));
        assert_eq!(snapshot.document_id, "doc-demo-001");
    }

    #[test]
    fn document_open_falls_back_to_direct_snapshot_when_session_open_fails() {
        let snapshot = open_document_snapshot_via_contract(
            &FailingSessionBridge,
            "af-00000002",
            "session-open-failure",
            Some("C:/models/fallback.FCStd"),
            |_| None,
        );

        assert_eq!(snapshot.file_path.as_deref(), Some("C:/models/fallback.FCStd"));
        assert_eq!(snapshot.document_id, "doc-demo-001");
    }

    #[test]
    fn document_open_falls_back_to_direct_snapshot_when_session_snapshot_is_missing() {
        let snapshot = open_document_snapshot_via_contract(
            &SuccessfulSessionBridge,
            "af-00000003",
            "session-open-missing-snapshot",
            Some("C:/models/fallback-missing.FCStd"),
            |_| None,
        );

        assert_eq!(snapshot.file_path.as_deref(), Some("C:/models/fallback-missing.FCStd"));
        assert_eq!(snapshot.document_id, "doc-demo-001");
    }

    #[test]
    fn runtime_descriptor_uses_contract_result_when_available() {
        let descriptor = runtime_descriptor_via_contract(&PrototypeFreecadBridge, "af-runtime-success");

        assert_eq!(descriptor.worker_mode, "mock-freecad-worker");
        assert!(!descriptor.capabilities.command_execution);
    }

    #[test]
    fn runtime_descriptor_falls_back_to_default_when_contract_fails() {
        let descriptor = runtime_descriptor_via_contract(&FailingRuntimeBridge, "af-runtime-fallback");

        let fallback = bridge_runtime_descriptor();
        assert_eq!(descriptor.worker_mode, fallback.worker_mode);
        assert_eq!(descriptor.capabilities.command_execution, fallback.capabilities.command_execution);
        assert_eq!(descriptor.protocol_version.major, fallback.protocol_version.major);
    }
}