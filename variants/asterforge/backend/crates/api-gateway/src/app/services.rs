use std::sync::{
    atomic::{AtomicU64, Ordering},
    Arc,
};
use std::collections::HashMap;

use asterforge_command_core::{
    command_behavior, command_dispatch_route, plan_command_runtime, validate_command_request,
    viewport_invalidated_event, CommandBehavior, CommandContext, CommandDispatchRoute,
    CommandExecutionRequest, CommandValidationError, PlannedCommandEvent, PlannedCommandRuntime,
};
use asterforge_document_core::{bridge_document_state, selectable_object_ids_for_mode, DocumentState};
#[derive(Debug, Clone, Copy)]
pub(super) struct CommandCoreServices;
use asterforge_freecad_bridge::{BridgeDocumentSnapshot, BridgeStatus};

use super::bridge_services::{BridgeServices, HistoryServices};
use super::state_properties;
use crate::domain::{object_tree_from_bridge, ObjectNode, PropertyGroup};

#[derive(Debug, Clone)]
pub(super) struct BridgeProjection {
    pub(super) document: DocumentState,
    pub(super) object_tree: Vec<ObjectNode>,
    pub(super) selected_object_id: String,
    pub(super) properties_by_object: HashMap<String, Vec<PropertyGroup>>,
}

impl CommandCoreServices {
    pub(super) fn validate_request(
        &self,
        correlation_id: &str,
        request: &CommandExecutionRequest,
        context: &CommandContext,
    ) -> Result<(), CommandValidationError> {
        tracing::debug!(
            correlation_id,
            command_id = %request.command_id,
            document_id = %request.document_id,
            target_object_id = ?request.target_object_id,
            "validating command request"
        );
        validate_command_request(request, context).map(|_| ())
    }

    pub(super) fn behavior(&self, command_id: &str) -> CommandBehavior {
        command_behavior(command_id)
    }

    pub(super) fn dispatch_route(
        &self,
        command_id: &str,
        step_context_active: bool,
    ) -> CommandDispatchRoute {
        command_dispatch_route(command_id, step_context_active)
    }

    pub(super) fn runtime_plan(
        &self,
        correlation_id: &str,
        command_id: &str,
        status_message: &str,
        accepted: bool,
        viewport_changed: bool,
        source: Option<&str>,
    ) -> PlannedCommandRuntime {
        tracing::debug!(
            correlation_id,
            command_id,
            accepted,
            viewport_changed,
            "planning command runtime"
        );
        plan_command_runtime(
            command_id,
            status_message,
            accepted,
            viewport_changed,
            source,
        )
    }

    pub(super) fn viewport_invalidated_event(&self) -> PlannedCommandEvent {
        viewport_invalidated_event()
    }
}

#[derive(Debug, Clone, Copy)]
pub(super) struct DocumentCoreServices;

impl DocumentCoreServices {
    pub(super) fn project_document_state(
        &self,
        correlation_id: &str,
        snapshot: &BridgeDocumentSnapshot,
        bridge_status: &BridgeStatus,
    ) -> DocumentState {
        tracing::debug!(
            correlation_id,
            document_id = %snapshot.document_id,
            worker_mode = %bridge_status.worker_mode,
            "projecting document state from bridge snapshot"
        );
        bridge_document_state(snapshot, &bridge_status.worker_mode)
    }

    pub(super) fn selectable_object_ids_for_mode(
        &self,
        correlation_id: &str,
        snapshot: &BridgeDocumentSnapshot,
        selection_mode: &str,
    ) -> Vec<String> {
        tracing::debug!(
            correlation_id,
            document_id = %snapshot.document_id,
            selection_mode,
            "projecting selectable object ids"
        );
        selectable_object_ids_for_mode(snapshot, selection_mode)
    }

    pub(super) fn project_bridge_snapshot(
        &self,
        correlation_id: &str,
        snapshot: &BridgeDocumentSnapshot,
        bridge_status: &BridgeStatus,
    ) -> BridgeProjection {
        tracing::debug!(
            correlation_id,
            document_id = %snapshot.document_id,
            "projecting gateway bridge snapshot state"
        );

        let document = self.project_document_state(correlation_id, snapshot, bridge_status);
        let object_tree = object_tree_from_bridge(snapshot);
        let properties_by_object = state_properties::build_property_map(snapshot, &object_tree);

        BridgeProjection {
            document,
            object_tree,
            selected_object_id: snapshot.selected_object_id.clone(),
            properties_by_object,
        }
    }
}

#[derive(Debug, Clone)]
pub(super) struct AppServices {
    pub(super) bridge: BridgeServices,
    pub(super) command: CommandCoreServices,
    pub(super) document: DocumentCoreServices,
    pub(super) history: HistoryServices,
    correlation_seed: Arc<AtomicU64>,
}

impl AppServices {
    pub(super) fn production() -> Self {
        Self {
            bridge: BridgeServices::production(),
            command: CommandCoreServices,
            document: DocumentCoreServices,
            history: HistoryServices,
            correlation_seed: Arc::new(AtomicU64::new(1)),
        }
    }

    pub(super) fn next_correlation_id(&self) -> String {
        let next = self.correlation_seed.fetch_add(1, Ordering::Relaxed);
        format!("af-{:08x}", next)
    }
}

#[cfg(test)]
mod tests {
    use super::AppServices;

    #[test]
    fn correlation_ids_are_unique() {
        let services = AppServices::production();

        let first = services.next_correlation_id();
        let second = services.next_correlation_id();

        assert_ne!(first, second);
        assert!(first.starts_with("af-"));
        assert!(second.starts_with("af-"));
    }
}