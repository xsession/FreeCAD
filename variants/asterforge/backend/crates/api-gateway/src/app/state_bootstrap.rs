use super::services::AppServices;
use super::state_types::{
    AppModel, PersistedWorkspaceState, StepMeasurementSummary, StepPmiInspectionSummary,
    StepViewportCameraState,
};
use super::state_workspace;
use crate::domain::{extension_compatibility_state, sample_boot_report, sample_bridge_status, sample_event_stream};

pub(super) fn build_bootstrap_model(
    services: &AppServices,
    session_namespace: String,
    correlation_id: &str,
    persisted_workspace: Option<&PersistedWorkspaceState>,
) -> AppModel {
    let snapshot = services.bridge.open_pending_document_snapshot(
        correlation_id,
        &session_namespace,
        persisted_workspace.and_then(|state| state.active_document_path.as_deref()),
    );
    let bridge_status = sample_bridge_status();
    let projection = services
        .document
        .project_bridge_snapshot(correlation_id, &snapshot, &bridge_status);

    let mut model = AppModel {
        session_namespace,
        boot_report: sample_boot_report(),
        bridge_status,
        bridge_snapshot: snapshot,
        document: projection.document,
        object_tree: projection.object_tree,
        selection_mode: "object".into(),
        preselected_object_id: None,
        selected_object_id: projection.selected_object_id,
        jobs: vec![],
        properties_by_object: projection.properties_by_object,
        events: sample_event_stream(),
        undo_stack: asterforge_freecad_bridge::UndoStack::new(50),
        recent_documents: vec![],
        workspace_sessions: vec![],
        combo_view_tab: "model".into(),
        bottom_dock_tab: "report".into(),
        combo_view_visible: true,
        report_dock_visible: true,
        combo_view_size_hint: 0.28,
        report_dock_size_hint: 0.24,
        extension_compatibility: extension_compatibility_state(),
        step_cache_by_document: std::collections::HashMap::new(),
        step_pmi_inspection_by_document: std::collections::HashMap::<
            String,
            StepPmiInspectionSummary,
        >::new(),
        step_measurement_by_document: std::collections::HashMap::<
            String,
            StepMeasurementSummary,
        >::new(),
        step_viewport_camera_by_document: std::collections::HashMap::<
            String,
            StepViewportCameraState,
        >::new(),
    };

    if let Some(persisted_workspace) = persisted_workspace {
        state_workspace::apply_persisted_workspace_state(services, &mut model, persisted_workspace);
    } else {
        state_workspace::remember_current_document(services, &mut model);
    }

    model
}

#[cfg(test)]
mod tests {
    use std::sync::Arc;

    use super::build_bootstrap_model;
    use crate::app::services::AppServices;
    use crate::app::state_types::PersistedWorkspaceState;
    use crate::domain::{RecentDocumentEntry, WorkspaceSessionEntry};

    #[test]
    fn bootstrap_model_applies_persisted_workspace_state() {
        let services = Arc::new(AppServices::production());
        let persisted_workspace = PersistedWorkspaceState {
            active_document_path: Some("C:/models/bootstrap-persisted.FCStd".into()),
            active_workbench_id: Some("partdesign".into()),
            selected_object_id: Some("body-001".into()),
            selection_mode: Some("body".into()),
            recent_documents: vec![RecentDocumentEntry {
                file_path: "C:/models/bootstrap-persisted.FCStd".into(),
                display_name: "bootstrap-persisted.FCStd".into(),
                workbench: "PartDesign".into(),
                dirty: false,
            }],
            workspace_sessions: vec![WorkspaceSessionEntry {
                session_id: "persisted-session".into(),
                document_id: "doc-demo-001".into(),
                display_name: "bootstrap-persisted.FCStd".into(),
                file_path: "C:/models/bootstrap-persisted.FCStd".into(),
                workbench: "PartDesign".into(),
                dirty: false,
                selected_object_id: Some("body-001".into()),
                selection_mode: Some("body".into()),
                combo_view_tab: Some("tasks".into()),
                bottom_dock_tab: Some("report".into()),
                combo_view_visible: Some(true),
                report_dock_visible: Some(true),
                combo_view_size_hint: Some(0.31),
                report_dock_size_hint: Some(0.22),
            }],
            combo_view_tab: "tasks".into(),
            bottom_dock_tab: "report".into(),
            combo_view_visible: true,
            report_dock_visible: true,
            combo_view_size_hint: 0.31,
            report_dock_size_hint: 0.22,
        };

        let model = build_bootstrap_model(
            &services,
            "bootstrap-session".into(),
            "af-bootstrap-0001",
            Some(&persisted_workspace),
        );

        assert_eq!(model.selection_mode, "body");
        assert_eq!(model.selected_object_id, "body-001");
        assert_eq!(model.combo_view_tab, "tasks");
        assert_eq!(model.document.file_path.as_deref(), Some("C:/models/bootstrap-persisted.FCStd"));
        assert!(!model.workspace_sessions.is_empty());
    }
}