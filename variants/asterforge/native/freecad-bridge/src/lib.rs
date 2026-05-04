mod contract;
mod session_store;
mod model;
mod prototype;
mod runtime;
mod undo;
mod viewport;
mod workflow;

pub use contract::{
    Bounds2d, BridgeCapabilities, BridgeCommandRequest, BridgeCommandResponse,
    BridgeDocumentSnapshot, BridgeError, BridgeErrorCategory, BridgeObjectNode,
    BridgeOperationResult, BridgeProtocolVersion, BridgeRequestOptions, BridgeRuntimeDescriptor,
    BridgeSessionRequest, BridgeSessionResponse, BridgeStatus, BridgeViewportRequest,
    CameraState, DrawableMesh, FreecadBridgeContract, NativeSessionToken, Point2d, Polyline2d,
    ViewportDiff, ViewportSnapshot,
};
pub use model::{
    create_pad_from_selected_sketch, create_pocket_from_selected_sketch,
    create_sketch_in_body, open_document_snapshot, rebuild_viewport,
    resume_full_history, rollback_history_to_selected, toggle_selected_suppression,
    update_selected_feature_length, update_selected_pad_profile, update_selected_pocket_profile,
};
pub use prototype::{execute_prototype_command_on_snapshot, PrototypeFreecadBridge};
pub use runtime::{bridge_runtime_descriptor, bridge_status};
pub use session_store::{load_prototype_bridge_session, sync_prototype_bridge_session};
pub use undo::{apply_undo_action, UndoAction, UndoActionResult, UndoStack};
pub use viewport::compute_viewport_diff;
pub use workflow::{
    body_feature_summary, body_next_step, body_workflow_description, dependency_issue_hint,
    dependency_status_label, dependency_workflow_description, pad_inspection_hint,
    pad_workflow_description, pocket_inspection_hint, pocket_workflow_description,
    sketch_next_step, sketch_workflow_description,
};
pub(crate) use model::parse_bool_flag;

#[no_mangle]
pub extern "C" fn asterforge_bridge_api_version() -> u32 {
    1
}

#[cfg(test)]
mod tests {
    use std::collections::BTreeMap;

    use super::{
        apply_undo_action,
        body_next_step, body_workflow_description, create_pad_from_selected_sketch,
        create_pocket_from_selected_sketch, create_sketch_in_body, dependency_issue_hint,
        dependency_status_label, dependency_workflow_description,
        execute_prototype_command_on_snapshot, open_document_snapshot,
        pad_workflow_description, pocket_workflow_description, resume_full_history,
        rollback_history_to_selected, sketch_next_step, sketch_workflow_description,
        toggle_selected_suppression, update_selected_feature_length, update_selected_pad_profile,
        update_selected_pocket_profile, BridgeCommandRequest, BridgeRequestOptions,
        BridgeSessionRequest, BridgeViewportRequest, FreecadBridgeContract,
        PrototypeFreecadBridge, UndoAction, UndoStack,
    };

    #[test]
    fn creates_sketch_when_body_selected() {
        let mut snapshot = open_document_snapshot(None);
        snapshot.selected_object_id = "body-001".into();

        let new_sketch = create_sketch_in_body(&mut snapshot, Some("SketchA"), Some("XZ"));

        assert_eq!(new_sketch.as_deref(), Some("sketch-002"));
        assert_eq!(snapshot.selected_object_id, "sketch-002");
        assert!(snapshot.dirty);
        assert!(snapshot
            .roots
            .first()
            .expect("body root should exist")
            .children
            .iter()
            .any(|child| {
                child.object_id == "sketch-002"
                    && child.label == "SketchA"
                    && child.reference_plane.as_deref() == Some("XZ")
                    && child.constraint_count == Some(5)
                    && child.profile_closed == Some(true)
                    && child.fully_constrained == Some(false)
            }));
    }

    #[test]
    fn creates_pad_and_updates_length_from_selected_sketch() {
        let mut snapshot = open_document_snapshot(None);
        snapshot.selected_object_id = "sketch-001".into();

        let new_pad = create_pad_from_selected_sketch(&mut snapshot, Some(20.0), Some("dimension"), true);
        assert_eq!(new_pad.as_deref(), Some("pad-002"));
        assert_eq!(snapshot.selected_object_id, "pad-002");

        let updated = update_selected_feature_length(&mut snapshot, 32.5);
        assert_eq!(updated.as_deref(), Some("pad-002"));

        let updated_profile = update_selected_pad_profile(&mut snapshot, None, Some(false));
        assert_eq!(updated_profile.as_deref(), Some("pad-002"));

        let body = snapshot.roots.first().expect("body root should exist");
        let pad = body
            .children
            .iter()
            .find(|child| child.object_id == "pad-002")
            .expect("new pad should exist");
        assert_eq!(pad.length_mm, Some(32.5));
        assert!(!pad.midplane);
    }

    #[test]
    fn creates_and_updates_pocket_from_selected_sketch() {
        let mut snapshot = open_document_snapshot(None);
        snapshot.selected_object_id = "sketch-001".into();

        let pocket = create_pocket_from_selected_sketch(&mut snapshot, Some(6.0), Some("through_all"));
        assert_eq!(pocket.as_deref(), Some("pocket-001"));
        assert_eq!(snapshot.selected_object_id, "pocket-001");

        let updated = update_selected_feature_length(&mut snapshot, 9.5);
        assert_eq!(updated.as_deref(), Some("pocket-001"));

        let updated_profile = update_selected_pocket_profile(&mut snapshot, None, Some("dimension"));
        assert_eq!(updated_profile.as_deref(), Some("pocket-001"));

        let body = snapshot.roots.first().expect("body root should exist");
        let pocket = body
            .children
            .iter()
            .find(|child| child.object_id == "pocket-001")
            .expect("new pocket should exist");
        assert_eq!(pocket.length_mm, Some(9.5));
        assert_eq!(pocket.extent_mode.as_deref(), Some("dimension"));
    }

    #[test]
    fn suppress_and_rollback_history_roundtrip() {
        let mut snapshot = open_document_snapshot(None);
        snapshot.selected_object_id = "pad-001".into();

        let toggled = toggle_selected_suppression(&mut snapshot);
        assert_eq!(toggled, Some(("pad-001".into(), true)));

        let rolled = rollback_history_to_selected(&mut snapshot);
        assert_eq!(rolled, Some(("pad-001".into(), 2)));
        assert_eq!(snapshot.history_marker, Some(2));

        let resumed = resume_full_history(&mut snapshot);
        assert!(resumed);
        assert_eq!(snapshot.history_marker, None);
    }

    #[test]
    fn viewport_diff_detects_added_and_removed() {
        use super::{compute_viewport_diff, rebuild_viewport};

        let mut snapshot = open_document_snapshot(None);
        let before = snapshot.viewport.clone();

        // Add a new sketch → produces a new drawable
        snapshot.selected_object_id = "body-001".into();
        create_sketch_in_body(&mut snapshot, Some("DiffSketch"), Some("YZ"));
        rebuild_viewport(&mut snapshot);

        let diff = compute_viewport_diff(&before, &snapshot.viewport);
        assert!(!diff.is_empty());
        assert!(
            diff.added
                .iter()
                .any(|d| d.label == "DiffSketch"),
            "new sketch should appear as added"
        );
    }

    #[test]
    fn viewport_diff_detects_modification() {
        use super::{compute_viewport_diff, rebuild_viewport};

        let mut snapshot = open_document_snapshot(None);
        let before = snapshot.viewport.clone();

        // Modify the pad length → changes its drawable bounds
        snapshot.selected_object_id = "pad-001".into();
        update_selected_feature_length(&mut snapshot, 50.0);
        rebuild_viewport(&mut snapshot);

        let diff = compute_viewport_diff(&before, &snapshot.viewport);
        assert!(
            diff.modified
                .iter()
                .any(|d| d.object_id == "pad-001"),
            "pad-001 should appear as modified"
        );
    }

    #[test]
    fn undo_stack_roundtrip() {
        use super::UndoStack;

        let mut stack = UndoStack::new(10);
        let snapshot_a = open_document_snapshot(None);

        // push state A, mutate to B
        stack.push(&snapshot_a);
        let mut snapshot_b = snapshot_a.clone();
        snapshot_b.dirty = true;
        snapshot_b.display_name = "B".into();

        assert!(stack.can_undo());
        assert!(!stack.can_redo());

        // undo → back to A
        let restored = stack.undo(&snapshot_b).expect("should undo");
        assert_eq!(restored.display_name, snapshot_a.display_name);
        assert!(stack.can_redo());

        // redo → back to B
        let redone = stack.redo(&restored).expect("should redo");
        assert_eq!(redone.display_name, "B");
        assert!(!stack.can_redo());
    }

    #[test]
    fn workflow_helpers_reflect_bridge_state() {
        let mut snapshot = open_document_snapshot(None);
        let (sketch, pad) = {
            let body = snapshot.roots.first().expect("body should exist");
            let sketch = body
                .children
                .iter()
                .find(|child| child.object_id == "sketch-001")
                .expect("default sketch should exist")
                .clone();
            let pad = body
                .children
                .iter()
                .find(|child| child.object_id == "pad-001")
                .expect("default pad should exist")
                .clone();
            (sketch, pad)
        };

        assert_eq!(sketch_next_step(&sketch), "Create a pad or pocket");
        assert!(sketch_workflow_description(&sketch).contains("production-ready"));
        assert!(pad_workflow_description(&pad).contains("One-sided"));
        assert!(body_workflow_description(&snapshot).contains("1 sketch"));
        assert!(body_next_step(&snapshot).contains("Select an active sketch"));

        snapshot.selected_object_id = "sketch-001".into();
        let pocket = create_pocket_from_selected_sketch(&mut snapshot, Some(6.0), Some("through_all"));
        assert_eq!(pocket.as_deref(), Some("pocket-001"));
        let pocket = snapshot
            .roots
            .first()
            .and_then(|body| body.children.iter().find(|child| child.object_id == "pocket-001"))
            .expect("pocket should exist");
        assert!(pocket_workflow_description(pocket).contains("Through-all pocket"));
        assert_eq!(dependency_status_label(pocket), "Inactive");
        assert!(dependency_workflow_description(pocket, Some("Blocked by source")).contains("Blocked by source"));

        let mut suppressed_pad = pad;
        suppressed_pad.suppressed = true;
        assert_eq!(dependency_status_label(&suppressed_pad), "Suppressed");
        assert!(dependency_issue_hint(&suppressed_pad, None).contains("manually suppressed"));
    }

    #[test]
    fn prototype_command_executor_marks_document_saved() {
        let mut snapshot = open_document_snapshot(None);
        snapshot.dirty = true;

        let response = execute_prototype_command_on_snapshot(
            &mut snapshot,
            &BridgeCommandRequest {
                session_id: "session-demo-001".into(),
                command_id: "document.save".into(),
                target_object_id: None,
                arguments: BTreeMap::new(),
                options: BridgeRequestOptions::default(),
            },
        )
        .expect("document save should succeed");

        assert!(response.accepted);
        assert!(!snapshot.dirty);
        assert_eq!(response.status_message, "Document marked as saved");
    }

    #[test]
    fn prototype_command_executor_creates_sketch_from_body_selection() {
        let mut snapshot = open_document_snapshot(None);
        snapshot.selected_object_id = "body-001".into();

        let response = execute_prototype_command_on_snapshot(
            &mut snapshot,
            &BridgeCommandRequest {
                session_id: "session-demo-001".into(),
                command_id: "partdesign.new_sketch".into(),
                target_object_id: Some("body-001".into()),
                arguments: BTreeMap::from([
                    ("sketch_label".into(), "BridgeSketch".into()),
                    ("reference_plane".into(), "XZ".into()),
                ]),
                options: BridgeRequestOptions::default(),
            },
        )
        .expect("new sketch should succeed");

        assert!(response.accepted);
        assert_eq!(snapshot.selected_object_id, "sketch-002");
        assert!(snapshot
            .roots
            .first()
            .expect("body should exist")
            .children
            .iter()
            .any(|child| child.label == "BridgeSketch"));
    }

    #[test]
    fn prototype_bridge_trait_executes_command_against_session_store() {
        let bridge = PrototypeFreecadBridge;
        let session = bridge
            .open_document_session(BridgeSessionRequest {
                session_id: "session-trait-001".into(),
                source_path: None,
                requested_workbench: None,
                options: BridgeRequestOptions::default(),
            })
            .expect("session should open");

        let response = bridge
            .execute_command(BridgeCommandRequest {
                session_id: session.token.session_id.clone(),
                command_id: "document.save".into(),
                target_object_id: None,
                arguments: BTreeMap::new(),
                options: BridgeRequestOptions::default(),
            })
            .expect("command should execute");

        assert!(response.accepted);

        let viewport = bridge
            .fetch_viewport(BridgeViewportRequest {
                session_id: session.token.session_id,
                object_ids: vec![],
                options: BridgeRequestOptions::default(),
            })
            .expect("viewport should load");

        assert_eq!(viewport.camera.eye, [10.0, 8.0, 12.0]);
        assert_eq!(viewport.camera.target, [0.0, 0.0, 0.0]);
    }

    #[test]
    fn prototype_bridge_trait_requires_existing_session() {
        let bridge = PrototypeFreecadBridge;
        let error = bridge
            .execute_command(BridgeCommandRequest {
                session_id: "session-missing".into(),
                command_id: "document.save".into(),
                target_object_id: None,
                arguments: BTreeMap::new(),
                options: BridgeRequestOptions::default(),
            })
            .expect_err("missing session should fail");

        assert_eq!(error.code, "bridge.session_not_found");
    }

    #[test]
    fn apply_undo_action_restores_previous_snapshot() {
        let mut stack = UndoStack::new(10);
        let original = open_document_snapshot(None);
        let mut mutated = original.clone();
        mutated.selected_object_id = "sketch-001".into();

        stack.push(&original);
        let result = apply_undo_action(&mut stack, &mutated, UndoAction::Undo);

        assert!(result.accepted);
        assert_eq!(result.status_message, "Undo applied");
        assert_eq!(result.snapshot.expect("undo snapshot").selected_object_id, original.selected_object_id);
        assert!(stack.can_redo());
    }

    #[test]
    fn apply_undo_action_reports_empty_stack() {
        let mut stack = UndoStack::new(10);
        let snapshot = open_document_snapshot(None);

        let result = apply_undo_action(&mut stack, &snapshot, UndoAction::Redo);

        assert!(!result.accepted);
        assert_eq!(result.status_message, "Nothing to redo");
        assert!(result.snapshot.is_none());
    }
}
