use std::collections::HashMap;
use std::io::{self, Write};
use std::path::PathBuf;
use std::sync::{Arc, Mutex, OnceLock};

use tracing_subscriber::fmt::MakeWriter;

use super::services::AppServices;
use super::state::{AppState, CommandExecutionRequest};
use super::state_requests::{
    ActivateWorkbenchRequest, PreselectionRequest, SelectionModeRequest, SelectionRequest,
    ShellPanelMutationRequest,
};

#[derive(Clone, Default)]
struct SharedLogBuffer {
    inner: Arc<Mutex<Vec<u8>>>,
}

struct SharedLogWriter {
    inner: Arc<Mutex<Vec<u8>>>,
}

impl Write for SharedLogWriter {
    fn write(&mut self, buf: &[u8]) -> io::Result<usize> {
        self.inner
            .lock()
            .expect("log buffer should lock")
            .extend_from_slice(buf);
        Ok(buf.len())
    }

    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}

impl<'a> MakeWriter<'a> for SharedLogBuffer {
    type Writer = SharedLogWriter;

    fn make_writer(&'a self) -> Self::Writer {
        SharedLogWriter {
            inner: self.inner.clone(),
        }
    }
}

impl SharedLogBuffer {
    fn contents(&self) -> String {
        String::from_utf8(
            self.inner
                .lock()
                .expect("log buffer should lock")
                .clone(),
        )
        .expect("captured logs should be utf8")
    }
}

fn find_correlation_id(logs: &str, needle: &str) -> Option<String> {
    logs.lines().find(|line| line.contains(needle)).and_then(|line| {
        let start = line.find("af-")?;
        let suffix = &line[start..];
        let end = suffix
            .find(|ch: char| !matches!(ch, '-' | 'a'..='f' | '0'..='9'))
            .unwrap_or(suffix.len());
        Some(suffix[..end].to_string())
    })
}

fn tracing_test_guard() -> std::sync::MutexGuard<'static, ()> {
    static TRACING_TEST_MUTEX: OnceLock<Mutex<()>> = OnceLock::new();
    TRACING_TEST_MUTEX
        .get_or_init(|| Mutex::new(()))
        .lock()
        .unwrap_or_else(|error| error.into_inner())
}

fn command_request(command_id: &str, target_object_id: Option<&str>) -> CommandExecutionRequest {
    CommandExecutionRequest {
        command_id: command_id.to_string(),
        document_id: "doc-demo-001".to_string(),
        target_object_id: target_object_id.map(str::to_string),
        arguments: HashMap::new(),
    }
}

fn state_with_services() -> AppState {
    AppState::with_services(Arc::new(AppServices::production()))
}

fn state_with_services_and_persistence(persistence_path: PathBuf) -> AppState {
    AppState::with_services_and_persistence(Arc::new(AppServices::production()), Some(persistence_path))
}

#[tokio::test]
async fn rejects_unknown_selection() {
    let state = AppState::new();

    let result = state
        .set_selection(SelectionRequest {
            document_id: "doc-demo-001".to_string(),
            object_id: "does-not-exist".to_string(),
        })
        .await;

    assert!(result.is_none());
}

#[tokio::test]
async fn step_data_is_not_exposed_for_non_step_document() {
    let state = AppState::new();
    let document_id = {
        let model = state.inner.read().await;
        model.document.document_id.clone()
    };

    let index = state
        .step_document_index(&document_id)
        .await
        .expect("STEP lookup should not fail");
    assert!(index.is_none());
}

#[tokio::test]
async fn step_document_open_exposes_parsed_index_and_scene() {
    let state = AppState::new();
    let fixture_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../fixtures/sample-ap242-assembly.stp");
    let opened = state
        .open_document(fixture_path.to_string_lossy().into_owned())
        .await;

    let index = state
        .step_document_index(&opened.document_id)
        .await
        .expect("STEP index should build")
        .expect("opened STEP document should expose STEP index");
    assert!(index
        .header
        .application_protocols
        .iter()
        .any(|protocol| protocol == "AP242"));
    assert!(!index.assemblies.is_empty());
    assert!(!index.tessellated_representations.is_empty());

    let scene = state
        .step_scene_bundle(&opened.document_id)
        .await
        .expect("STEP scene should build")
        .expect("opened STEP document should expose STEP scene");
    assert_eq!(scene.assemblies.len(), index.assemblies.len());
    assert!(!scene.semantic_pmi.is_empty());
}

#[tokio::test]
async fn step_document_projects_tree_properties_and_viewport() {
    let state = AppState::new();
    let fixture_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../fixtures/sample-ap242-assembly.stp");
    let opened = state
        .open_document(fixture_path.to_string_lossy().into_owned())
        .await;

    let tree = state
        .object_tree_proto(&opened.document_id)
        .await
        .expect("STEP object tree should be available");
    assert!(!tree.roots.is_empty());
    assert!(tree.roots[0].object_id.starts_with("step-entity-"));

    let selection = state
        .selection_state(&opened.document_id)
        .await
        .expect("STEP selection state should be available");
    assert_eq!(selection.current_mode, "object");
    assert_eq!(selection.available_modes[0].object_count, 4);
    assert!(!selection.available_modes[1].enabled);

    let properties = state
        .properties(&opened.document_id, &selection.selected_object_id)
        .await
        .expect("STEP properties should be available");
    assert!(properties
        .groups
        .iter()
        .any(|group| group.group_id == "step_record"));

    let viewport = state
        .viewport(&opened.document_id)
        .await
        .expect("STEP viewport should be available");
    assert!(viewport
        .scene
        .drawables
        .iter()
        .all(|drawable| drawable.object_id.starts_with("step-entity-")));
}

#[tokio::test]
async fn step_command_catalog_exposes_step_specific_actions() {
    let state = AppState::new();
    let fixture_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../fixtures/sample-ap242-assembly.stp");
    let opened = state
        .open_document(fixture_path.to_string_lossy().into_owned())
        .await;

    let catalog = state
        .command_catalog(&opened.document_id)
        .await
        .expect("STEP command catalog should be available");
    assert_eq!(catalog.workbench.workbench_id, "step");
    assert!(catalog.commands.iter().any(|command| command.command_id == "step.view_fit_all"));
    assert!(catalog.commands.iter().any(|command| command.command_id == "step.select_first_child"));
    assert!(catalog.commands.iter().any(|command| command.command_id == "step.inspect_pmi"));
    assert!(catalog.commands.iter().any(|command| command.command_id == "step.measure_selection"));
    assert!(catalog.commands.iter().any(|command| command.command_id == "step.hide_selection"));
    assert!(catalog.commands.iter().any(|command| command.command_id == "step.isolate_selection"));
    assert!(catalog.commands.iter().any(|command| command.command_id == "step.show_all"));
}

#[tokio::test]
async fn step_commands_navigate_tree_and_focus_pmi_report() {
    let state = AppState::new();
    let fixture_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../fixtures/sample-ap242-assembly.stp");
    let opened = state
        .open_document(fixture_path.to_string_lossy().into_owned())
        .await;

    let child = state
        .run_command(CommandExecutionRequest {
            command_id: "step.select_first_child".into(),
            document_id: opened.document_id.clone(),
            target_object_id: Some("step-entity-20".into()),
            arguments: HashMap::new(),
        })
        .await
        .expect("STEP child selection should return a response");
    assert!(child.accepted);

    let selection = state
        .selection_state(&opened.document_id)
        .await
        .expect("STEP selection state should be available");
    assert_eq!(selection.selected_object_id, "step-entity-10");

    let parent = state
        .run_command(CommandExecutionRequest {
            command_id: "step.select_parent".into(),
            document_id: opened.document_id.clone(),
            target_object_id: Some("step-entity-10".into()),
            arguments: HashMap::new(),
        })
        .await
        .expect("STEP parent selection should return a response");
    assert!(parent.accepted);

    let inspect = state
        .run_command(CommandExecutionRequest {
            command_id: "step.inspect_pmi".into(),
            document_id: opened.document_id.clone(),
            target_object_id: Some("step-entity-20".into()),
            arguments: HashMap::new(),
        })
        .await
        .expect("STEP PMI inspect should return a response");
    assert!(inspect.accepted);

    let shell = state
        .shell_snapshot(&opened.document_id)
        .await
        .expect("STEP shell snapshot should be available");
    assert_eq!(
        shell.layout
            .panels
            .iter()
            .find(|panel| panel.panel_id == "report_dock")
            .and_then(|panel| panel.active_tab.clone())
            .as_deref(),
        Some("report")
    );

    let events = state
        .events(&opened.document_id)
        .await
        .expect("STEP event stream should be available");
    assert!(events
        .iter()
        .any(|event| event.topic == "step_pmi_inspection" && event.message.contains("Housing / #20")));
    assert!(events.iter().any(|event| {
        event.topic == "step_pmi_annotation"
            && event.message.contains("protocol_summary")
            && event.message.contains("#20")
    }));
}

#[tokio::test]
async fn step_commands_apply_explicit_target_before_execution() {
    let state = AppState::new();
    let fixture_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../fixtures/sample-ap242-assembly.stp");
    let opened = state
        .open_document(fixture_path.to_string_lossy().into_owned())
        .await;

    state
        .set_selection(SelectionRequest {
            document_id: opened.document_id.clone(),
            object_id: "step-entity-20".into(),
        })
        .await
        .expect("root STEP selection should succeed");

    let response = state
        .run_command(CommandExecutionRequest {
            command_id: "step.select_parent".into(),
            document_id: opened.document_id.clone(),
            target_object_id: Some("step-entity-10".into()),
            arguments: HashMap::new(),
        })
        .await
        .expect("STEP parent selection should return a response");
    assert!(response.accepted);

    let selection = state
        .selection_state(&opened.document_id)
        .await
        .expect("STEP selection state should be available");
    assert_eq!(selection.selected_object_id, "step-entity-20");
}

#[tokio::test]
async fn step_shell_snapshot_exposes_step_workbench_and_step_menu() {
    let state = AppState::new();
    let fixture_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../fixtures/sample-ap242-assembly.stp");
    let opened = state
        .open_document(fixture_path.to_string_lossy().into_owned())
        .await;

    let shell = state
        .shell_snapshot(&opened.document_id)
        .await
        .expect("STEP shell snapshot should be available");
    assert_eq!(shell.workbench_catalog.active_workbench_id, "step");
    assert!(shell.menu_bar.menus.iter().any(|menu| menu.menu_id == "step"));
    let view_menu = shell
        .menu_bar
        .menus
        .iter()
        .find(|menu| menu.menu_id == "view")
        .expect("STEP shell should expose a View menu");
    for command_id in [
        "step.view_reset",
        "step.view_fit_all",
        "step.view_iso",
        "step.view_front",
        "step.view_back",
        "step.view_right",
        "step.view_left",
        "step.view_top",
        "step.view_bottom",
    ] {
        assert!(view_menu
            .items
            .iter()
            .any(|item| item.command_id.as_deref() == Some(command_id)));
    }
    assert!(shell
        .toolbar_bands
        .bands
        .iter()
        .any(|band| band.band_id == "step"));
    let step_band = shell
        .toolbar_bands
        .bands
        .iter()
        .find(|band| band.band_id == "step")
        .expect("STEP shell should expose the STEP toolbar band");
    let view_toolbar = step_band
        .toolbars
        .iter()
        .find(|toolbar| toolbar.toolbar_id == "step-view")
        .expect("STEP shell should expose the STEP view toolbar");
    for command_id in [
        "step.view_reset",
        "step.view_fit_all",
        "step.view_iso",
        "step.view_front",
        "step.view_back",
        "step.view_right",
        "step.view_left",
        "step.view_top",
        "step.view_bottom",
    ] {
        assert!(view_toolbar
            .items
            .iter()
            .any(|item| item.command_id.as_deref() == Some(command_id)));
    }
}

#[tokio::test]
async fn step_document_rejects_non_object_selection_modes() {
    let state = AppState::new();
    let fixture_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../fixtures/sample-ap242-assembly.stp");
    let opened = state
        .open_document(fixture_path.to_string_lossy().into_owned())
        .await;

    let rejected = state
        .set_selection_mode(SelectionModeRequest {
            document_id: opened.document_id.clone(),
            mode_id: "feature".into(),
        })
        .await;
    assert!(rejected.is_none());

    let selection = state
        .selection_state(&opened.document_id)
        .await
        .expect("STEP selection state should remain available");
    assert_eq!(selection.current_mode, "object");
}

#[tokio::test]
async fn step_document_rejects_non_step_workbench_activation() {
    let state = AppState::new();
    let fixture_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../fixtures/sample-ap242-assembly.stp");
    let opened = state
        .open_document(fixture_path.to_string_lossy().into_owned())
        .await;

    let rejected = state
        .activate_workbench(ActivateWorkbenchRequest {
            document_id: opened.document_id.clone(),
            workbench_id: "partdesign".into(),
        })
        .await;
    assert!(rejected.is_none());

    let accepted = state
        .activate_workbench(ActivateWorkbenchRequest {
            document_id: opened.document_id.clone(),
            workbench_id: "step".into(),
        })
        .await
        .expect("STEP workbench activation should succeed");
    assert_eq!(accepted.workbench, "STEP Inspection");

    let shell = state
        .shell_snapshot(&opened.document_id)
        .await
        .expect("STEP shell snapshot should remain available");
    assert_eq!(shell.workbench_catalog.active_workbench_id, "step");
}

#[tokio::test]
async fn selection_mode_retargets_to_matching_object_kind() {
    let state = AppState::new();

    let mode = state
        .set_selection_mode(SelectionModeRequest {
            document_id: "doc-demo-001".to_string(),
            mode_id: "sketch".to_string(),
        })
        .await
        .expect("sketch selection mode should succeed");

    assert_eq!(mode.current_mode, "sketch");
    assert_eq!(mode.selected_object_id, "sketch-001");
}

#[tokio::test]
async fn incompatible_selection_requests_follow_active_selection_mode() {
    let state = AppState::new();

    state
        .set_selection_mode(SelectionModeRequest {
            document_id: "doc-demo-001".to_string(),
            mode_id: "feature".to_string(),
        })
        .await
        .expect("feature selection mode should succeed");

    let selection = state
        .set_selection(SelectionRequest {
            document_id: "doc-demo-001".to_string(),
            object_id: "body-001".to_string(),
        })
        .await
        .expect("selection should be normalized");

    assert_eq!(selection.selected_object_id, "pad-001");
}

#[tokio::test]
async fn preselection_tracks_only_objects_allowed_by_active_mode() {
    let state = AppState::new();

    state
        .set_selection_mode(SelectionModeRequest {
            document_id: "doc-demo-001".to_string(),
            mode_id: "sketch".to_string(),
        })
        .await
        .expect("sketch mode should succeed");

    let preselection = state
        .set_preselection(PreselectionRequest {
            document_id: "doc-demo-001".to_string(),
            object_id: Some("pad-001".to_string()),
        })
        .await
        .expect("preselection request should respond");
    assert!(preselection.object_id.is_none());

    let sketch_preselection = state
        .set_preselection(PreselectionRequest {
            document_id: "doc-demo-001".to_string(),
            object_id: Some("sketch-001".to_string()),
        })
        .await
        .expect("preselection request should respond");
    assert_eq!(sketch_preselection.object_id.as_deref(), Some("sketch-001"));
}

#[tokio::test]
async fn step_visibility_commands_filter_tree_and_viewport() {
    let state = AppState::new();
    let fixture_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../fixtures/sample-ap242-assembly.stp");
    let opened = state
        .open_document(fixture_path.to_string_lossy().into_owned())
        .await;

    let isolate = state
        .run_command(CommandExecutionRequest {
            command_id: "step.isolate_selection".into(),
            document_id: opened.document_id.clone(),
            target_object_id: Some("step-entity-20".into()),
            arguments: HashMap::new(),
        })
        .await
        .expect("STEP isolate command should return a response");
    assert!(isolate.accepted);

    {
        let model = state.inner.read().await;
        assert_eq!(model.object_tree[0].visibility, crate::domain::VisibilityState::Visible);
        assert_eq!(model.object_tree[1].visibility, crate::domain::VisibilityState::Hidden);
    }

    let isolated_viewport = state
        .viewport(&opened.document_id)
        .await
        .expect("isolated STEP viewport should be available");
    assert_eq!(isolated_viewport.scene.drawables.len(), 1);
    assert_eq!(isolated_viewport.scene.drawables[0].object_id, "step-entity-20");

    let hide = state
        .run_command(CommandExecutionRequest {
            command_id: "step.hide_selection".into(),
            document_id: opened.document_id.clone(),
            target_object_id: Some("step-entity-20".into()),
            arguments: HashMap::new(),
        })
        .await
        .expect("STEP hide command should return a response");
    assert!(hide.accepted);

    let diagnostics = state
        .diagnostics(&opened.document_id)
        .await
        .expect("STEP diagnostics should be available");
    assert!(!diagnostics.selection.visible_in_viewport);

    let hidden_catalog = state
        .command_catalog(&opened.document_id)
        .await
        .expect("STEP command catalog should remain available");
    assert!(hidden_catalog
        .commands
        .iter()
        .find(|command| command.command_id == "step.show_all")
        .expect("show all command should exist")
        .enabled);

    let restore = state
        .run_command(CommandExecutionRequest {
            command_id: "step.show_all".into(),
            document_id: opened.document_id.clone(),
            target_object_id: None,
            arguments: HashMap::new(),
        })
        .await
        .expect("STEP show all command should return a response");
    assert!(restore.accepted);

    let restored_viewport = state
        .viewport(&opened.document_id)
        .await
        .expect("restored STEP viewport should be available");
    assert_eq!(restored_viewport.scene.drawables.len(), 2);

    let task_panel = state
        .task_panel(&opened.document_id)
        .await
        .expect("STEP task panel should remain available");
    assert!(task_panel
        .suggested_commands
        .iter()
        .any(|command| command == "step.hide_selection"));
}

#[tokio::test]
async fn sketch_creation_requires_body_selection() {
    let state = AppState::new();

    let response = state
        .run_command(command_request("partdesign.new_sketch", Some("pad-001")))
        .await
        .expect("command should return a response");

    assert!(!response.accepted);
    assert!(response.status_message.contains("body to be selected"));
}

#[tokio::test]
async fn commands_apply_explicit_target_before_partdesign_execution() {
    let state = AppState::new();

    state
        .set_selection(SelectionRequest {
            document_id: "doc-demo-001".to_string(),
            object_id: "pad-001".to_string(),
        })
        .await
        .expect("pad selection should succeed");

    let response = state
        .run_command(CommandExecutionRequest {
            command_id: "partdesign.new_sketch".to_string(),
            document_id: "doc-demo-001".to_string(),
            target_object_id: Some("body-001".to_string()),
            arguments: HashMap::from([("sketch_label".to_string(), "TargetedSketch".to_string())]),
        })
        .await
        .expect("new sketch command should respond");
    assert!(response.accepted);

    let selection = state
        .selection_state("doc-demo-001")
        .await
        .expect("selection state should remain available");
    assert_eq!(selection.selected_object_type, "Sketcher::SketchObject");

    let history = state
        .feature_history("doc-demo-001")
        .await
        .expect("history should remain available");
    assert!(history.entries.iter().any(|entry| entry.label == "TargetedSketch"));
}

#[tokio::test]
async fn create_sketch_then_pad_updates_history() {
    let state = AppState::new();

    let selected = state
        .set_selection(SelectionRequest {
            document_id: "doc-demo-001".to_string(),
            object_id: "body-001".to_string(),
        })
        .await
        .expect("body selection should succeed");
    assert_eq!(selected.selected_object_id, "body-001");

    let mut sketch_args = HashMap::new();
    sketch_args.insert("sketch_label".to_string(), "SketchQA".to_string());
    let sketch_response = state
        .run_command(CommandExecutionRequest {
            command_id: "partdesign.new_sketch".to_string(),
            document_id: "doc-demo-001".to_string(),
            target_object_id: Some("body-001".to_string()),
            arguments: sketch_args,
        })
        .await
        .expect("new sketch command should respond");
    assert!(sketch_response.accepted);

    let history_after_sketch = state
        .feature_history("doc-demo-001")
        .await
        .expect("history should be available");
    let new_sketch = history_after_sketch
        .entries
        .iter()
        .find(|entry| entry.label == "SketchQA")
        .expect("new sketch should exist in history");
    assert_eq!(new_sketch.object_type, "Sketcher::SketchObject");

    let pad_response = state
        .run_command(CommandExecutionRequest {
            command_id: "partdesign.pad".to_string(),
            document_id: "doc-demo-001".to_string(),
            target_object_id: Some(new_sketch.object_id.clone()),
            arguments: HashMap::from([("length_mm".to_string(), "15.5".to_string())]),
        })
        .await
        .expect("pad command should respond");
    assert!(pad_response.accepted);

    let history_after_pad = state
        .feature_history("doc-demo-001")
        .await
        .expect("history should be available");
    assert!(history_after_pad.entries.iter().any(|entry| {
        entry.object_type == "PartDesign::Pad"
            && entry.source_object_id.as_deref() == Some(new_sketch.object_id.as_str())
    }));
}

#[tokio::test]
async fn undo_reverts_pad_creation() {
    let state = AppState::new();

    state
        .set_selection(SelectionRequest {
            document_id: "doc-demo-001".to_string(),
            object_id: "body-001".to_string(),
        })
        .await
        .expect("body selection should succeed");

    let mut sketch_args = HashMap::new();
    sketch_args.insert("sketch_label".to_string(), "UndoSketch".to_string());
    state
        .run_command(CommandExecutionRequest {
            command_id: "partdesign.new_sketch".to_string(),
            document_id: "doc-demo-001".to_string(),
            target_object_id: None,
            arguments: sketch_args,
        })
        .await
        .expect("sketch creation should succeed");

    let pad_response = state
        .run_command(CommandExecutionRequest {
            command_id: "partdesign.pad".to_string(),
            document_id: "doc-demo-001".to_string(),
            target_object_id: None,
            arguments: HashMap::from([("length_mm".to_string(), "20.0".to_string())]),
        })
        .await
        .expect("pad creation should succeed");
    assert!(pad_response.accepted);

    let undo_response = state
        .run_command(command_request("document.undo", None))
        .await
        .expect("undo should return a response");
    assert!(undo_response.accepted);
    assert_eq!(undo_response.status_message, "Undo applied");

    let history = state
        .feature_history("doc-demo-001")
        .await
        .expect("history should be available");

    assert!(
        !history
            .entries
            .iter()
            .any(|entry| entry.object_type == "PartDesign::Pad" && entry.source_object_id.as_deref() == Some("sketch-002")),
        "pad should be removed after undo"
    );

    let redo_response = state
        .run_command(command_request("document.redo", None))
        .await
        .expect("redo should return a response");
    assert!(redo_response.accepted);

    let history_after_redo = state
        .feature_history("doc-demo-001")
        .await
        .expect("history should be available");
    assert!(
        history_after_redo
            .entries
            .iter()
            .any(|entry| entry.object_type == "PartDesign::Pad" && entry.source_object_id.as_deref() == Some("sketch-002")),
        "pad should reappear after redo"
    );
}

#[tokio::test]
async fn richer_command_arguments_persist_into_properties_and_catalog() {
    let state = AppState::new();

    state
        .set_selection(SelectionRequest {
            document_id: "doc-demo-001".to_string(),
            object_id: "body-001".to_string(),
        })
        .await
        .expect("body selection should succeed");

    let sketch_response = state
        .run_command(CommandExecutionRequest {
            command_id: "partdesign.new_sketch".to_string(),
            document_id: "doc-demo-001".to_string(),
            target_object_id: None,
            arguments: HashMap::from([
                ("sketch_label".to_string(), "PlaneSketch".to_string()),
                ("reference_plane".to_string(), "XZ".to_string()),
            ]),
        })
        .await
        .expect("sketch creation should succeed");
    assert!(sketch_response.accepted);

    let sketch_properties = state
        .properties("doc-demo-001", "sketch-002")
        .await
        .expect("sketch properties should exist");
    let sketch_definition = sketch_properties
        .groups
        .iter()
        .find(|group| group.group_id == "definition")
        .expect("sketch definition group should exist");
    assert!(sketch_definition.properties.iter().any(|property| {
        property.property_id == "reference_plane" && property.value_preview == "XZ"
    }));

    let pad_response = state
        .run_command(CommandExecutionRequest {
            command_id: "partdesign.pad".to_string(),
            document_id: "doc-demo-001".to_string(),
            target_object_id: None,
            arguments: HashMap::from([
                ("length_mm".to_string(), "18.0".to_string()),
                ("midplane".to_string(), "true".to_string()),
            ]),
        })
        .await
        .expect("pad creation should succeed");
    assert!(pad_response.accepted);

    let pad_properties = state
        .properties("doc-demo-001", "pad-002")
        .await
        .expect("pad properties should exist");
    let pad_definition = pad_properties
        .groups
        .iter()
        .find(|group| group.group_id == "definition")
        .expect("pad definition group should exist");
    assert!(pad_definition
        .properties
        .iter()
        .any(|property| property.property_id == "midplane" && property.value_preview == "true"));

    let catalog = state
        .command_catalog("doc-demo-001")
        .await
        .expect("command catalog should exist");
    let edit_pad = catalog
        .commands
        .iter()
        .find(|command| command.command_id == "partdesign.edit_pad")
        .expect("edit pad command should exist");
    assert!(edit_pad
        .arguments
        .iter()
        .any(|argument| argument.argument_id == "midplane" && argument.default_value.as_deref() == Some("true")));
}

#[tokio::test]
async fn sketch_metadata_surfaces_in_task_panel_and_properties() {
    let state = AppState::new();

    state
        .set_selection(SelectionRequest {
            document_id: "doc-demo-001".to_string(),
            object_id: "body-001".to_string(),
        })
        .await
        .expect("body selection should succeed");

    state
        .run_command(CommandExecutionRequest {
            command_id: "partdesign.new_sketch".to_string(),
            document_id: "doc-demo-001".to_string(),
            target_object_id: None,
            arguments: HashMap::from([
                ("sketch_label".to_string(), "StatusSketch".to_string()),
                ("reference_plane".to_string(), "YZ".to_string()),
            ]),
        })
        .await
        .expect("sketch creation should succeed");

    let task_panel = state
        .task_panel("doc-demo-001")
        .await
        .expect("task panel should exist");
    let constraint_section = task_panel
        .sections
        .iter()
        .find(|section| section.section_id == "constraints")
        .expect("constraints section should exist");
    assert!(constraint_section.rows.iter().any(|row| {
        row.label == "Constraint state" && row.value == "4 constraints, solver pending"
    }));
    assert!(constraint_section
        .rows
        .iter()
        .any(|row| row.label == "Profile readiness" && row.value == "Open profile"));

    let properties = state
        .properties("doc-demo-001", "sketch-002")
        .await
        .expect("properties should exist");
    let sketch_group = properties
        .groups
        .iter()
        .find(|group| group.group_id == "constraints")
        .expect("constraints group should exist");
    assert!(sketch_group.properties.iter().any(|property| {
        property.property_id == "constraint_count"
            && property.value_preview == "4 constraints, solver pending"
    }));
}

#[tokio::test]
async fn task_panel_descriptions_follow_bridge_workflow_guidance() {
    let state = AppState::new();

    state
        .set_selection(SelectionRequest {
            document_id: "doc-demo-001".to_string(),
            object_id: "pad-001".to_string(),
        })
        .await
        .expect("pad selection should succeed");

    let pad_panel = state
        .task_panel("doc-demo-001")
        .await
        .expect("pad task panel should exist");
    assert!(pad_panel.description.contains("One-sided pad"));
    assert!(pad_panel
        .sections
        .iter()
        .flat_map(|section| section.rows.iter())
        .any(|row| row.label == "View" && row.value == "Inspect one-sided growth"));

    let suppression_response = state
        .run_command(CommandExecutionRequest {
            command_id: "model.toggle_suppression".to_string(),
            document_id: "doc-demo-001".to_string(),
            target_object_id: Some("pad-001".to_string()),
            arguments: HashMap::new(),
        })
        .await
        .expect("suppression command should respond");
    assert!(suppression_response.accepted);

    let dependency_panel = state
        .task_panel("doc-demo-001")
        .await
        .expect("dependency task panel should exist");
    assert!(dependency_panel.description.contains("manually suppressed"));
    assert!(dependency_panel
        .sections
        .iter()
        .flat_map(|section| section.rows.iter())
        .any(|row| row.label == "State" && row.value == "Suppressed"));
}

#[tokio::test]
async fn step_measure_command_updates_task_panel_and_shell_focus() {
    let state = AppState::new();
    let fixture_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../fixtures/sample-ap242-assembly.stp");
    let opened = state
        .open_document(fixture_path.to_string_lossy().into_owned())
        .await;

    let response = state
        .run_command(CommandExecutionRequest {
            command_id: "step.measure_selection".into(),
            document_id: opened.document_id.clone(),
            target_object_id: Some("step-entity-20".into()),
            arguments: HashMap::new(),
        })
        .await
        .expect("STEP measure command should return a response");
    assert!(response.accepted);
    assert!(response.status_message.contains("Measured Housing"));

    let task_panel = state
        .task_panel(&opened.document_id)
        .await
        .expect("STEP task panel should be available");
    let measurement_section = task_panel
        .sections
        .iter()
        .find(|section| section.section_id == "measurement")
        .expect("measurement section should exist");
    assert!(measurement_section
        .rows
        .iter()
        .any(|row| row.label == "Measured node" && row.value == "Housing"));
    assert!(measurement_section
        .rows
        .iter()
        .any(|row| row.label == "Z span" && row.value == "1.00"));

    let shell = state
        .shell_snapshot(&opened.document_id)
        .await
        .expect("STEP shell snapshot should be available");
    assert_eq!(
        shell.layout
            .panels
            .iter()
            .find(|panel| panel.panel_id == "combo_view")
            .and_then(|panel| panel.active_tab.clone())
            .as_deref(),
        Some("tasks")
    );
    assert_eq!(
        shell.layout
            .panels
            .iter()
            .find(|panel| panel.panel_id == "report_dock")
            .and_then(|panel| panel.active_tab.clone())
            .as_deref(),
        Some("report")
    );
    let measurement_overlay = shell
        .inspection
        .as_ref()
        .and_then(|inspection| inspection.step_measurement.as_ref())
        .expect("shell inspection measurement payload should exist");
    assert_eq!(measurement_overlay.object_id, "step-entity-20");
    assert!((measurement_overlay.span_z - 1.0).abs() < f32::EPSILON);

    let events = state
        .events(&opened.document_id)
        .await
        .expect("STEP event stream should be available");
    assert!(events.iter().any(|event| {
        event.topic == "step_measurement"
            && event.object_id.as_deref() == Some("step-entity-20")
            && event.message.contains("Measured Housing at 1.00 x 1.00 x 1.00")
    }));

    let catalog = state
        .command_catalog(&opened.document_id)
        .await
        .expect("STEP command catalog should remain available");
    assert!(catalog.workbench.mode.contains("live measurement"));
}

#[tokio::test]
async fn step_selection_focus_updates_backend_viewport_camera() {
    let state = AppState::new();
    let fixture_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../fixtures/sample-ap242-assembly.stp");
    let opened = state
        .open_document(fixture_path.to_string_lossy().into_owned())
        .await;

    let before = state
        .viewport(&opened.document_id)
        .await
        .expect("STEP viewport should be available before focus");

    let response = state
        .run_command(CommandExecutionRequest {
            command_id: "selection.focus".into(),
            document_id: opened.document_id.clone(),
            target_object_id: Some("step-entity-20".into()),
            arguments: HashMap::new(),
        })
        .await
        .expect("STEP focus command should return a response");
    assert!(response.accepted);
    assert!(response.status_message.contains("Focused STEP selection"));

    let after = state
        .viewport(&opened.document_id)
        .await
        .expect("STEP viewport should be available after focus");

    assert_eq!(after.selected_object_id, "step-entity-20");
    assert_ne!(after.scene.camera_target, before.scene.camera_target);
    assert_ne!(after.scene.camera_eye, before.scene.camera_eye);
    assert_eq!(after.scene.camera_target, [0.5, 0.5, 0.5]);
}

#[tokio::test]
async fn step_view_preset_commands_update_backend_viewport_camera() {
    let state = AppState::new();
    let fixture_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../fixtures/sample-ap242-assembly.stp");
    let opened = state
        .open_document(fixture_path.to_string_lossy().into_owned())
        .await;

    let focus_response = state
        .run_command(CommandExecutionRequest {
            command_id: "selection.focus".into(),
            document_id: opened.document_id.clone(),
            target_object_id: Some("step-entity-20".into()),
            arguments: HashMap::new(),
        })
        .await
        .expect("STEP focus command should return a response");
    assert!(focus_response.accepted);

    let focused = state
        .viewport(&opened.document_id)
        .await
        .expect("STEP viewport should be available after focus");

    let preset_response = state
        .run_command(CommandExecutionRequest {
            command_id: "step.view_front".into(),
            document_id: opened.document_id.clone(),
            target_object_id: Some("step-entity-20".into()),
            arguments: HashMap::new(),
        })
        .await
        .expect("STEP front view command should return a response");
    assert!(preset_response.accepted);

    let after = state
        .viewport(&opened.document_id)
        .await
        .expect("STEP viewport should be available after preset");

    assert_eq!(after.scene.camera_target, focused.scene.camera_target);
    assert_ne!(after.scene.camera_eye, focused.scene.camera_eye);
    assert!((after.scene.camera_eye[0] - focused.scene.camera_target[0]).abs() < 0.001);
    assert!((after.scene.camera_eye[1] - focused.scene.camera_target[1]).abs() < 0.001);
    assert!(after.scene.camera_eye[2] > focused.scene.camera_target[2]);
}

#[tokio::test]
async fn step_reset_view_command_restores_default_viewport_camera() {
    let state = AppState::new();
    let fixture_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../fixtures/sample-ap242-assembly.stp");
    let opened = state
        .open_document(fixture_path.to_string_lossy().into_owned())
        .await;

    let _ = state
        .run_command(CommandExecutionRequest {
            command_id: "selection.focus".into(),
            document_id: opened.document_id.clone(),
            target_object_id: Some("step-entity-20".into()),
            arguments: HashMap::new(),
        })
        .await
        .expect("STEP focus command should return a response");

    let response = state
        .run_command(CommandExecutionRequest {
            command_id: "step.view_reset".into(),
            document_id: opened.document_id.clone(),
            target_object_id: Some("step-entity-20".into()),
            arguments: HashMap::new(),
        })
        .await
        .expect("STEP reset view command should return a response");
    assert!(response.accepted);
    assert!(response.status_message.contains("Reset STEP view"));

    let after = state
        .viewport(&opened.document_id)
        .await
        .expect("STEP viewport should be available after reset");
    assert_eq!(after.scene.camera_eye, [2.6, 2.2, 3.1]);
    assert_eq!(after.scene.camera_target, [0.8, 0.7, 0.4]);
}

#[tokio::test]
async fn step_fit_all_command_frames_visible_step_geometry() {
    let state = AppState::new();
    let fixture_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../fixtures/sample-ap242-assembly.stp");
    let opened = state
        .open_document(fixture_path.to_string_lossy().into_owned())
        .await;

    let response = state
        .run_command(CommandExecutionRequest {
            command_id: "step.view_fit_all".into(),
            document_id: opened.document_id.clone(),
            target_object_id: Some("step-entity-20".into()),
            arguments: HashMap::new(),
        })
        .await
        .expect("STEP fit-all command should return a response");
    assert!(response.accepted);
    assert!(response.status_message.contains("Fit all visible STEP geometry"));

    let after = state
        .viewport(&opened.document_id)
        .await
        .expect("STEP viewport should be available after fit all");
    assert_eq!(after.scene.camera_target, [1.25, 0.5, 0.5]);
    assert!(after.scene.camera_eye[0] > after.scene.camera_target[0]);
    assert!(after.scene.camera_eye[1] > after.scene.camera_target[1]);
    assert!(after.scene.camera_eye[2] > after.scene.camera_target[2]);
}

#[tokio::test]
async fn step_inspect_pmi_populates_task_panel_drill_down() {
    let state = AppState::new();
    let fixture_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../fixtures/sample-ap242-assembly.stp");
    let opened = state
        .open_document(fixture_path.to_string_lossy().into_owned())
        .await;

    let response = state
        .run_command(CommandExecutionRequest {
            command_id: "step.inspect_pmi".into(),
            document_id: opened.document_id.clone(),
            target_object_id: Some("step-entity-20".into()),
            arguments: HashMap::new(),
        })
        .await
        .expect("STEP PMI inspect should return a response");
    assert!(response.accepted);
    assert!(response.status_message.contains("Loaded PMI inspection"));

    let task_panel = state
        .task_panel(&opened.document_id)
        .await
        .expect("STEP task panel should be available");
    let pmi_section = task_panel
        .sections
        .iter()
        .find(|section| section.section_id == "pmi")
        .expect("PMI section should exist");
    assert!(pmi_section
        .rows
        .iter()
        .any(|row| row.label == "Inspected node" && row.value == "Housing"));
    assert!(pmi_section
        .rows
        .iter()
        .any(|row| row.label == "Annotations" && row.value == "2"));

    let annotation_sections: Vec<_> = task_panel
        .sections
        .iter()
        .filter(|section| section.section_id.starts_with("pmi-annotation-"))
        .collect();
    assert_eq!(annotation_sections.len(), 2);
    assert!(annotation_sections.iter().any(|section| {
        section
            .rows
            .iter()
            .any(|row| row.label == "Type" && row.value == "protocol_summary")
    }));
    assert!(annotation_sections.iter().any(|section| {
        section.rows.iter().any(|row| {
            row.label == "Text"
                && (row.value.contains("Protocols: AP242")
                    || row.value.contains("references outer shell"))
        })
    }));

    let shell = state
        .shell_snapshot(&opened.document_id)
        .await
        .expect("STEP shell snapshot should be available");
    assert_eq!(
        shell.layout
            .panels
            .iter()
            .find(|panel| panel.panel_id == "combo_view")
            .and_then(|panel| panel.active_tab.clone())
            .as_deref(),
        Some("tasks")
    );

    let shell = state
        .shell_snapshot(&opened.document_id)
        .await
        .expect("STEP shell snapshot should be available");
    let inspected_overlay = shell
        .inspection
        .as_ref()
        .and_then(|inspection| inspection.step_pmi.as_ref())
        .expect("shell inspection PMI payload should exist");
    assert_eq!(inspected_overlay.object_id, "step-entity-20");
    assert!(inspected_overlay
        .target_object_ids
        .iter()
        .any(|object_id| object_id == "step-entity-20"));
}

#[tokio::test]
async fn command_response_includes_viewport_diff() {
    let state = AppState::new();

    state
        .set_selection(SelectionRequest {
            document_id: "doc-demo-001".to_string(),
            object_id: "body-001".to_string(),
        })
        .await
        .expect("body selection should succeed");

    let response = state
        .run_command(CommandExecutionRequest {
            command_id: "partdesign.new_sketch".to_string(),
            document_id: "doc-demo-001".to_string(),
            target_object_id: None,
            arguments: HashMap::from([("sketch_label".to_string(), "DiffSketch".to_string())]),
        })
        .await
        .expect("sketch creation should succeed");
    assert!(response.accepted);

    let diff = response
        .viewport_diff
        .expect("accepted mutating command should include viewport diff");
    assert!(
        !diff.added.is_empty() || !diff.modified.is_empty(),
        "diff should contain changes after sketch creation"
    );
}

#[tokio::test]
async fn command_catalog_exposes_backend_argument_metadata() {
    let state = AppState::new();

    state
        .set_selection(SelectionRequest {
            document_id: "doc-demo-001".to_string(),
            object_id: "body-001".to_string(),
        })
        .await
        .expect("body selection should succeed");

    let catalog = state
        .command_catalog("doc-demo-001")
        .await
        .expect("command catalog should be available");
    let create_sketch = catalog
        .commands
        .iter()
        .find(|command| command.command_id == "partdesign.new_sketch")
        .expect("create sketch command should exist");

    assert!(create_sketch.enabled);
    assert_eq!(create_sketch.arguments.len(), 2);
    assert_eq!(create_sketch.arguments[0].argument_id, "sketch_label");
    assert_eq!(create_sketch.arguments[0].default_value.as_deref(), Some("Sketch"));
    assert_eq!(create_sketch.arguments[1].argument_id, "reference_plane");
    assert_eq!(create_sketch.arguments[1].default_value.as_deref(), Some("XY"));
}

#[tokio::test]
async fn command_catalog_tracks_undo_and_redo_availability() {
    let state = AppState::new();

    let initial_catalog = state
        .command_catalog("doc-demo-001")
        .await
        .expect("initial catalog should be available");
    let initial_undo = initial_catalog
        .commands
        .iter()
        .find(|command| command.command_id == "document.undo")
        .expect("undo command should exist");
    let initial_redo = initial_catalog
        .commands
        .iter()
        .find(|command| command.command_id == "document.redo")
        .expect("redo command should exist");
    assert!(!initial_undo.enabled);
    assert!(!initial_redo.enabled);

    state
        .set_selection(SelectionRequest {
            document_id: "doc-demo-001".to_string(),
            object_id: "body-001".to_string(),
        })
        .await
        .expect("body selection should succeed");
    state
        .run_command(CommandExecutionRequest {
            command_id: "partdesign.new_sketch".to_string(),
            document_id: "doc-demo-001".to_string(),
            target_object_id: None,
            arguments: HashMap::from([("sketch_label".to_string(), "Undoable".to_string())]),
        })
        .await
        .expect("sketch creation should succeed");

    let after_change_catalog = state
        .command_catalog("doc-demo-001")
        .await
        .expect("catalog after change should be available");
    assert!(after_change_catalog
        .commands
        .iter()
        .find(|command| command.command_id == "document.undo")
        .expect("undo command should exist")
        .enabled);
    assert!(!after_change_catalog
        .commands
        .iter()
        .find(|command| command.command_id == "document.redo")
        .expect("redo command should exist")
        .enabled);
}

#[tokio::test]
async fn shell_snapshot_exposes_layout_and_dynamic_command_state() {
    let state = AppState::new();

    let initial_snapshot = state
        .shell_snapshot("doc-demo-001")
        .await
        .expect("shell snapshot should be available");
    assert_eq!(initial_snapshot.workbench_catalog.active_workbench_id, "partdesign");
    assert_eq!(initial_snapshot.document.document_id, "doc-demo-001");
    assert_eq!(
        initial_snapshot
            .layout
            .panels
            .iter()
            .find(|panel| panel.panel_id == "report_dock")
            .and_then(|panel| panel.active_tab.as_deref()),
        Some("report")
    );

    let initial_undo = initial_snapshot
        .toolbar_bands
        .bands
        .iter()
        .flat_map(|band| band.toolbars.iter())
        .flat_map(|toolbar| toolbar.items.iter())
        .find(|item| item.command_id.as_deref() == Some("document.undo"))
        .expect("undo toolbar item should exist");
    assert_eq!(initial_undo.enabled, Some(false));

    state
        .set_selection(SelectionRequest {
            document_id: "doc-demo-001".to_string(),
            object_id: "body-001".to_string(),
        })
        .await
        .expect("body selection should succeed");
    state
        .run_command(CommandExecutionRequest {
            command_id: "partdesign.new_sketch".to_string(),
            document_id: "doc-demo-001".to_string(),
            target_object_id: None,
            arguments: HashMap::from([("sketch_label".to_string(), "ShellSketch".to_string())]),
        })
        .await
        .expect("sketch creation should succeed");

    let updated_snapshot = state
        .shell_snapshot("doc-demo-001")
        .await
        .expect("shell snapshot should remain available");
    let updated_undo = updated_snapshot
        .toolbar_bands
        .bands
        .iter()
        .flat_map(|band| band.toolbars.iter())
        .flat_map(|toolbar| toolbar.items.iter())
        .find(|item| item.command_id.as_deref() == Some("document.undo"))
        .expect("undo toolbar item should exist");
    assert_eq!(updated_undo.enabled, Some(true));
}

#[tokio::test]
async fn activate_workbench_updates_document_and_backend_owned_shell_state() {
    let state = AppState::new();

    let updated_document = state
        .activate_workbench(ActivateWorkbenchRequest {
            document_id: "doc-demo-001".to_string(),
            workbench_id: "sketcher".to_string(),
        })
        .await
        .expect("workbench activation should succeed");

    assert_eq!(updated_document.workbench, "Sketcher");

    let shell_snapshot = state
        .shell_snapshot("doc-demo-001")
        .await
        .expect("shell snapshot should remain available");
    assert_eq!(shell_snapshot.workbench_catalog.active_workbench_id, "sketcher");

    let command_catalog = state
        .command_catalog("doc-demo-001")
        .await
        .expect("command catalog should be available");
    assert_eq!(command_catalog.workbench.display_name, "Sketcher");
    assert!(!command_catalog
        .commands
        .iter()
        .any(|command| command.command_id == "partdesign.new_sketch"));

    let task_panel = state
        .task_panel("doc-demo-001")
        .await
        .expect("task panel should be available");
    assert_eq!(task_panel.title, "Sketcher Workspace");
}

#[tokio::test]
async fn shell_snapshot_tracks_recent_documents_sessions_and_panel_tabs() {
    let state = AppState::new();

    state.open_document("C:/models/fixture-one.FCStd".to_string()).await;
    state
        .update_shell_panel(ShellPanelMutationRequest {
            document_id: "doc-demo-001".to_string(),
            panel_id: "combo_view".to_string(),
            active_tab: Some("tasks".to_string()),
            visible: None,
            size_hint: None,
        })
        .await
        .expect("combo panel update should succeed");

    let shell_snapshot = state
        .shell_snapshot("doc-demo-001")
        .await
        .expect("shell snapshot should be available");
    assert_eq!(shell_snapshot.recent_documents[0].file_path, "C:/models/fixture-one.FCStd");
    assert_eq!(shell_snapshot.workspace_sessions[0].file_path, "C:/models/fixture-one.FCStd");
    assert_eq!(shell_snapshot.workspace_sessions[0].selection_mode.as_deref(), Some("object"));
    assert_eq!(shell_snapshot.workspace_sessions[0].combo_view_tab.as_deref(), Some("tasks"));
    assert_eq!(shell_snapshot.workspace_sessions[0].bottom_dock_tab.as_deref(), Some("report"));
    assert_eq!(shell_snapshot.workspace_sessions[0].combo_view_visible, Some(true));
    assert_eq!(shell_snapshot.workspace_sessions[0].report_dock_visible, Some(true));
    assert_eq!(shell_snapshot.workspace_sessions[0].combo_view_size_hint, Some(0.28));
    assert_eq!(shell_snapshot.workspace_sessions[0].report_dock_size_hint, Some(0.24));
    assert_eq!(
        shell_snapshot.workspace_sessions[0].report_dock_filter_label.as_deref(),
        None
    );
    assert_eq!(
        shell_snapshot.workspace_sessions[0].diagnostics_dock_filter_query.as_deref(),
        None
    );
    assert_eq!(
        shell_snapshot
            .layout
            .panels
            .iter()
            .find(|panel| panel.panel_id == "combo_view")
            .and_then(|panel| panel.active_tab.as_deref()),
        Some("tasks")
    );
}

#[tokio::test]
async fn shell_panel_mutation_updates_visibility_and_size_hints() {
    let state = AppState::new();

    let shell_snapshot = state
        .update_shell_panel(ShellPanelMutationRequest {
            document_id: "doc-demo-001".to_string(),
            panel_id: "report_dock".to_string(),
            active_tab: None,
            visible: Some(false),
            size_hint: Some(0.31),
        })
        .await
        .expect("report dock mutation should succeed");

    let report_dock = shell_snapshot
        .layout
        .panels
        .iter()
        .find(|panel| panel.panel_id == "report_dock")
        .expect("report dock panel should exist");
    assert!(!report_dock.visible);
    assert_eq!(report_dock.size_hint, Some(0.31));
}

#[tokio::test]
async fn shell_snapshot_exposes_extension_compatibility_state() {
    let state = AppState::new();

    let shell_snapshot = state
        .shell_snapshot("doc-demo-001")
        .await
        .expect("shell snapshot should be available");

    assert_eq!(shell_snapshot.extension_compatibility.title, "Extension Compatibility");
    assert!(shell_snapshot
        .extension_compatibility
        .summary
        .contains("AddonManager"));
    assert!(shell_snapshot
        .extension_compatibility
        .lanes
        .iter()
        .any(|lane| lane.lane_id == "macros" && lane.status == "staging"));
    assert!(shell_snapshot
        .extension_compatibility
        .lanes
        .iter()
        .any(|lane| {
            lane.lane_id == "addon-manager"
                && lane.command_ids.contains(&"extensions.review_addon_catalog".to_string())
        }));
    assert_eq!(
        shell_snapshot
            .menu_bar
            .menus
            .iter()
            .find(|menu| menu.menu_id == "macro")
            .and_then(|menu| menu.items.first())
            .and_then(|item| item.command_id.as_deref()),
        Some("shell.show_extensions_manager")
    );
}

#[tokio::test]
async fn command_catalog_exposes_extension_commands() {
    let state = AppState::new();

    let command_catalog = state
        .command_catalog("doc-demo-001")
        .await
        .expect("command catalog should be available");

    assert!(command_catalog.commands.iter().any(|command| {
        command.command_id == "extensions.refresh_inventory" && command.group == "Extensions"
    }));
    assert!(command_catalog.commands.iter().any(|command| {
        command.command_id == "extensions.review_addon_catalog" && command.enabled
    }));
    assert!(command_catalog.commands.iter().any(|command| {
        command.command_id == "extensions.review_external_workbenches" && command.enabled
    }));
    assert!(command_catalog.commands.iter().any(|command| {
        command.command_id == "extensions.run_inventory_entry" && command.enabled
    }));
}

#[tokio::test]
async fn extension_refresh_command_runs_through_backend_dispatch() {
    let state = AppState::new();

    let response = state
        .run_command(command_request("extensions.refresh_inventory", None))
        .await
        .expect("extension refresh command should return a response");

    assert!(response.accepted);
    assert!(response.status_message.contains("Refreshed extension compatibility inventory"));

    let shell_snapshot = state
        .shell_snapshot("doc-demo-001")
        .await
        .expect("shell snapshot should be available");
    assert!(shell_snapshot
        .extension_compatibility
        .summary
        .contains("Last refresh completed via backend command runtime"));
    assert!(shell_snapshot
        .extension_compatibility
        .lanes
        .iter()
        .any(|lane| lane.lane_id == "macros" && lane.status == "inventory-ready"));
    assert!(shell_snapshot
        .extension_compatibility
        .lanes
        .iter()
        .find(|lane| lane.lane_id == "macros")
        .map(|lane| lane.inventory_entries.iter().any(|entry| entry.trust_state == "reviewed"))
        .unwrap_or(false));
    assert!(shell_snapshot
        .extension_compatibility
        .lanes
        .iter()
        .find(|lane| lane.lane_id == "macros")
        .map(|lane| {
            lane.inventory_entries.iter().any(|entry| {
                entry.entry_id == "macro:auto_dimensioning"
                    && entry.action_command_id.as_deref() == Some("extensions.run_inventory_entry")
            })
        })
        .unwrap_or(false));
    assert!(shell_snapshot
        .extension_compatibility
        .lanes
        .iter()
        .find(|lane| lane.lane_id == "addon-manager")
        .map(|lane| {
            lane.command_ids == vec!["extensions.review_addon_catalog"]
                && lane
                    .inventory_entries
                    .iter()
                    .any(|entry| entry.entry_id == "addon:ifc_tools")
        })
        .unwrap_or(false));
}

#[tokio::test]
async fn addon_catalog_review_command_updates_extension_lane_state() {
    let state = AppState::new();

    let response = state
        .run_command(command_request("extensions.review_addon_catalog", None))
        .await
        .expect("addon catalog review command should return a response");

    assert!(response.accepted);
    assert!(response
        .status_message
        .contains("Opened AddonManager compatibility review lane"));

    let shell_snapshot = state
        .shell_snapshot("doc-demo-001")
        .await
        .expect("shell snapshot should be available");
    assert_eq!(
        shell_snapshot
            .layout
            .panels
            .iter()
            .find(|panel| panel.panel_id == "report_dock")
            .and_then(|panel| panel.active_tab.as_deref()),
        Some("extensions")
    );
    assert!(shell_snapshot
        .extension_compatibility
        .summary
        .contains("AddonManager compatibility review is active"));
    assert!(shell_snapshot
        .extension_compatibility
        .lanes
        .iter()
        .find(|lane| lane.lane_id == "addon-manager")
        .map(|lane| {
            lane.status == "reviewing"
                && lane.inventory_entries.len() == 3
                && lane
                    .inventory_entries
                    .iter()
                    .any(|entry| entry.entry_id == "addon:sheetmetal_plus")
                && lane
                    .inventory_entries
                    .iter()
                    .any(|entry| entry.compatibility == "shell-candidate")
        })
        .unwrap_or(false));
}

#[tokio::test]
async fn external_workbench_review_command_updates_extension_lane_state() {
    let state = AppState::new();

    let response = state
        .run_command(command_request("extensions.review_external_workbenches", None))
        .await
        .expect("external workbench review command should return a response");

    assert!(response.accepted);
    assert!(response
        .status_message
        .contains("Opened external workbench compatibility review lane"));

    let shell_snapshot = state
        .shell_snapshot("doc-demo-001")
        .await
        .expect("shell snapshot should be available");
    assert_eq!(
        shell_snapshot
            .layout
            .panels
            .iter()
            .find(|panel| panel.panel_id == "report_dock")
            .and_then(|panel| panel.active_tab.as_deref()),
        Some("extensions")
    );
    assert!(shell_snapshot
        .extension_compatibility
        .lanes
        .iter()
        .any(|lane| lane.lane_id == "external-workbenches" && lane.status == "reviewing"));
}

#[tokio::test]
async fn extension_reviewed_inventory_entry_runs_through_backend_dispatch() {
    let state = AppState::new();

    state
        .run_command(command_request("extensions.refresh_inventory", None))
        .await
        .expect("extension refresh command should return a response");

    let response = state
        .run_command(CommandExecutionRequest {
            command_id: "extensions.run_inventory_entry".into(),
            document_id: "doc-demo-001".into(),
            target_object_id: None,
            arguments: HashMap::from([("entry_id".into(), "macro:auto_dimensioning".into())]),
        })
        .await
        .expect("reviewed inventory entry command should return a response");

    assert!(response.accepted);
    assert!(response.status_message.contains("AutoDimensioning.FCMacro"));

    let events = state
        .events("doc-demo-001")
        .await
        .expect("extension event stream should be available");
    assert!(events.iter().any(|event| {
        event.topic == "extension_inventory_execution"
            && event.message.contains("AutoDimensioning.FCMacro")
            && event.message.contains("Reviewed fixture bundle")
            && event.message.contains("test launcher success")
            && event.message.contains("ASTERFORGE_MACRO_OK:auto_dimensioning")
    }));

    let shell_snapshot = state
        .shell_snapshot("doc-demo-001")
        .await
        .expect("shell snapshot should be available");
    assert!(shell_snapshot
        .extension_compatibility
        .lanes
        .iter()
        .flat_map(|lane| lane.inventory_entries.iter())
        .any(|entry| {
            entry.entry_id == "macro:auto_dimensioning"
                && entry.last_run_kind.as_deref() == Some("success")
                && entry.last_run_status.as_deref() == Some("test launcher success")
                && entry.last_run_level.as_deref() == Some("info")
                && entry.last_run_detail.as_deref() == Some("ASTERFORGE_MACRO_OK:auto_dimensioning")
        }));
}

#[tokio::test]
async fn extension_reviewed_inventory_entry_failure_persists_status() {
    let state = AppState::new();

    state
        .run_command(command_request("extensions.refresh_inventory", None))
        .await
        .expect("extension refresh command should return a response");

    let response = state
        .run_command(CommandExecutionRequest {
            command_id: "extensions.run_inventory_entry".into(),
            document_id: "doc-demo-001".into(),
            target_object_id: None,
            arguments: HashMap::from([("entry_id".into(), "macro:broken_reviewed".into())]),
        })
        .await
        .expect("reviewed failing inventory entry command should return a response");

    assert!(!response.accepted);
    assert!(response.status_message.contains("BrokenReviewedFixture.FCMacro"));

    let events = state
        .events("doc-demo-001")
        .await
        .expect("extension event stream should be available");
    assert!(events.iter().any(|event| {
        event.topic == "extension_inventory_execution"
            && event.level == "warning"
            && event.message.contains("BrokenReviewedFixture.FCMacro")
            && event.message.contains("test launcher failure")
    }));

    let shell_snapshot = state
        .shell_snapshot("doc-demo-001")
        .await
        .expect("shell snapshot should be available");
    assert!(shell_snapshot
        .extension_compatibility
        .lanes
        .iter()
        .flat_map(|lane| lane.inventory_entries.iter())
        .any(|entry| {
            entry.entry_id == "macro:broken_reviewed"
                && entry.last_run_kind.as_deref() == Some("launcher-failed")
                && entry.last_run_status.as_deref() == Some("Launcher failed")
                && entry.last_run_level.as_deref() == Some("warning")
                && entry.last_run_detail.as_deref() == Some("test launcher failure")
        }));
}

#[tokio::test]
async fn extension_unreviewed_inventory_entry_persists_policy_rejection() {
    let state = AppState::new();

    state
        .run_command(command_request("extensions.refresh_inventory", None))
        .await
        .expect("extension refresh command should return a response");

    let response = state
        .run_command(CommandExecutionRequest {
            command_id: "extensions.run_inventory_entry".into(),
            document_id: "doc-demo-001".into(),
            target_object_id: None,
            arguments: HashMap::from([("entry_id".into(), "macro:legacy_sheetmetal".into())]),
        })
        .await
        .expect("unreviewed inventory entry command should return a response");

    assert!(!response.accepted);
    assert!(response.status_message.contains("LegacySheetMetalTools.FCMacro"));

    let events = state
        .events("doc-demo-001")
        .await
        .expect("extension event stream should be available");
    assert!(events.iter().any(|event| {
        event.topic == "extension_inventory_execution"
            && event.level == "warning"
            && event.message.contains("LegacySheetMetalTools.FCMacro")
            && event.message.contains("not reviewed and shell-ready yet")
    }));

    let shell_snapshot = state
        .shell_snapshot("doc-demo-001")
        .await
        .expect("shell snapshot should be available");
    assert!(shell_snapshot
        .extension_compatibility
        .lanes
        .iter()
        .flat_map(|lane| lane.inventory_entries.iter())
        .any(|entry| {
            entry.entry_id == "macro:legacy_sheetmetal"
                && entry.last_run_kind.as_deref() == Some("policy-rejected")
                && entry.last_run_status.as_deref() == Some("Blocked by trust policy")
                && entry.last_run_level.as_deref() == Some("warning")
                && entry.last_run_detail.as_deref()
                    == Some(
                        "Reviewed backend execution only runs shell-ready entries that have passed explicit trust review.",
                    )
        }));
}

#[tokio::test]
async fn fcstd_vertical_slice_runs_through_service_container() {
    let state = state_with_services();

    let opened = state
        .open_document("C:/models/service-fixture.FCStd".to_string())
        .await;
    assert_eq!(opened.document_id, "doc-demo-001");
    assert_eq!(opened.workbench, "PartDesign");
    assert_eq!(opened.file_path.as_deref(), Some("C:/models/service-fixture.FCStd"));

    let tree = state
        .object_tree_proto(&opened.document_id)
        .await
        .expect("object tree should be available after FCStd open");
    assert_eq!(tree.roots[0].object_id, "body-001");

    let initial_properties = state
        .properties(&opened.document_id, "pad-001")
        .await
        .expect("initial pad properties should exist");
    assert!(!initial_properties.groups.is_empty());

    state
        .set_selection(SelectionRequest {
            document_id: opened.document_id.clone(),
            object_id: "body-001".into(),
        })
        .await
        .expect("body selection should succeed after FCStd open");

    let sketch_response = state
        .run_command(CommandExecutionRequest {
            command_id: "partdesign.new_sketch".into(),
            document_id: opened.document_id.clone(),
            target_object_id: None,
            arguments: HashMap::from([
                ("sketch_label".into(), "ServiceSketch".into()),
                ("reference_plane".into(), "XZ".into()),
            ]),
        })
        .await
        .expect("sketch creation should respond");
    assert!(sketch_response.accepted);

    let history_after_sketch = state
        .feature_history(&opened.document_id)
        .await
        .expect("history should exist after sketch creation");
    let created_sketch = history_after_sketch
        .entries
        .iter()
        .find(|entry| entry.label == "ServiceSketch")
        .expect("service sketch should exist in history");

    let pad_response = state
        .run_command(CommandExecutionRequest {
            command_id: "partdesign.pad".into(),
            document_id: opened.document_id.clone(),
            target_object_id: Some(created_sketch.object_id.clone()),
            arguments: HashMap::from([
                ("length_mm".into(), "21.0".into()),
                ("midplane".into(), "true".into()),
            ]),
        })
        .await
        .expect("pad creation should respond");
    assert!(pad_response.accepted);

    let pad_properties = state
        .properties(&opened.document_id, "pad-002")
        .await
        .expect("new pad properties should exist");
    assert!(pad_properties
        .groups
        .iter()
        .find(|group| group.group_id == "constraints")
        .into_iter()
        .flat_map(|group| group.properties.iter())
        .any(|property| property.property_id == "length" && property.value_preview == "21.00 mm"));
    assert!(pad_properties
        .groups
        .iter()
        .flat_map(|group| group.properties.iter())
        .any(|property| property.property_id == "midplane" && property.value_preview == "true"));

    let undo_response = state
        .run_command(command_request("document.undo", None))
        .await
        .expect("undo should respond after pad creation");
    assert!(undo_response.accepted);

    let history_after_undo = state
        .feature_history(&opened.document_id)
        .await
        .expect("history should exist after undo");
    assert!(!history_after_undo
        .entries
        .iter()
        .any(|entry| entry.object_id == "pad-002"));

    let redo_response = state
        .run_command(command_request("document.redo", None))
        .await
        .expect("redo should respond after undo");
    assert!(redo_response.accepted);

    let history_after_redo = state
        .feature_history(&opened.document_id)
        .await
        .expect("history should exist after redo");
    assert!(history_after_redo
        .entries
        .iter()
        .any(|entry| entry.object_id == "pad-002"));

    let save_response = state
        .run_command(command_request("document.save", None))
        .await
        .expect("save should respond after redo");
    assert!(save_response.accepted);
    assert!(!save_response.document_dirty);

    let jobs = state
        .jobs(&opened.document_id)
        .await
        .expect("job status should remain available");
    assert_eq!(jobs.jobs[0].command_id, "document.save");

    let events = state
        .events(&opened.document_id)
        .await
        .expect("event stream should remain available");
    assert!(events
        .iter()
        .any(|event| event.message.contains("Opened C:/models/service-fixture.FCStd")));
    assert!(events
        .iter()
        .any(|event| event.message.contains("Document marked as saved")));
}

#[tokio::test]
async fn step_vertical_slice_runs_through_service_container() {
    let state = state_with_services();
    let fixture_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../fixtures/sample-ap242-assembly.stp");

    let opened = state
        .open_document(fixture_path.to_string_lossy().into_owned())
        .await;
    assert_eq!(opened.workbench, "STEP Inspection");

    let index = state
        .step_document_index(&opened.document_id)
        .await
        .expect("STEP index should build")
        .expect("STEP document should expose parsed index");
    assert!(!index.assemblies.is_empty());

    let scene = state
        .step_scene_bundle(&opened.document_id)
        .await
        .expect("STEP scene should build")
        .expect("STEP document should expose scene bundle");
    assert!(!scene.semantic_pmi.is_empty());

    let tree = state
        .object_tree_proto(&opened.document_id)
        .await
        .expect("STEP object tree should be available");
    assert!(tree.roots.iter().all(|node| node.object_id.starts_with("step-entity-")));

    let properties = state
        .properties(&opened.document_id, "step-entity-20")
        .await
        .expect("STEP properties should be available");
    assert!(properties.groups.iter().any(|group| group.group_id == "step_record"));

    let focus_response = state
        .run_command(CommandExecutionRequest {
            command_id: "selection.focus".into(),
            document_id: opened.document_id.clone(),
            target_object_id: Some("step-entity-20".into()),
            arguments: HashMap::new(),
        })
        .await
        .expect("STEP focus should respond");
    assert!(focus_response.accepted);

    let measure_response = state
        .run_command(CommandExecutionRequest {
            command_id: "step.measure_selection".into(),
            document_id: opened.document_id.clone(),
            target_object_id: Some("step-entity-20".into()),
            arguments: HashMap::new(),
        })
        .await
        .expect("STEP measure should respond");
    assert!(measure_response.accepted);

    let inspect_response = state
        .run_command(CommandExecutionRequest {
            command_id: "step.inspect_pmi".into(),
            document_id: opened.document_id.clone(),
            target_object_id: Some("step-entity-20".into()),
            arguments: HashMap::new(),
        })
        .await
        .expect("STEP PMI inspect should respond");
    assert!(inspect_response.accepted);

    let viewport = state
        .viewport(&opened.document_id)
        .await
        .expect("STEP viewport should remain available");
    assert_eq!(viewport.selected_object_id, "step-entity-20");
    assert_eq!(viewport.scene.camera_target, [0.5, 0.5, 0.5]);

    let task_panel = state
        .task_panel(&opened.document_id)
        .await
        .expect("STEP task panel should remain available");
    assert!(task_panel.sections.iter().any(|section| section.section_id == "measurement"));
    assert!(task_panel.sections.iter().any(|section| section.section_id == "pmi"));

    let shell = state
        .shell_snapshot(&opened.document_id)
        .await
        .expect("STEP shell snapshot should remain available");
    assert!(shell
        .inspection
        .as_ref()
        .and_then(|inspection| inspection.step_measurement.as_ref())
        .is_some());
    assert!(shell
        .inspection
        .as_ref()
        .and_then(|inspection| inspection.step_pmi.as_ref())
        .is_some());

    let events = state
        .events(&opened.document_id)
        .await
        .expect("STEP event stream should remain available");
    assert!(events.iter().any(|event| {
        event.topic == "step_measurement" && event.object_id.as_deref() == Some("step-entity-20")
    }));
    assert!(events.iter().any(|event| {
        event.topic == "step_pmi_inspection"
            && event.object_id.as_deref() == Some("step-entity-20")
    }));
}

#[tokio::test(flavor = "current_thread")]
async fn bridge_failure_logs_preserve_correlation_id_across_gateway_and_bridge() {
    let _guard = tracing_test_guard();
    let state = state_with_services();
    {
        let mut model = state.inner.write().await;
        model.session_namespace = "broken-session".into();
    }

    let log_buffer = SharedLogBuffer::default();
    let subscriber = tracing_subscriber::fmt()
        .with_writer(log_buffer.clone())
        .with_ansi(false)
        .without_time()
        .with_max_level(tracing::Level::DEBUG)
        .compact()
        .finish();
    let dispatch = tracing::Dispatch::new(subscriber);

    let response = {
        let _guard = tracing::dispatcher::set_default(&dispatch);
        state
            .run_command(command_request("document.save", None))
            .await
            .expect("save response should exist")
    };

    assert!(!response.accepted);

    let logs = log_buffer.contents();
    let gateway_id = find_correlation_id(&logs, "bridge vertical slice returned rejected response")
        .unwrap_or_else(|| panic!("gateway correlation id should be present; logs: {logs}"));
    let bridge_id = find_correlation_id(&logs, "prototype bridge session missing during command execution")
        .unwrap_or_else(|| panic!("bridge correlation id should be present; logs: {logs}"));
    let error_id = find_correlation_id(&logs, "bridge command failed")
        .unwrap_or_else(|| panic!("bridge failure correlation id should be present; logs: {logs}"));

    assert_eq!(gateway_id, bridge_id);
    assert_eq!(gateway_id, error_id);
}

#[tokio::test(flavor = "current_thread")]
async fn persistence_warning_logs_preserve_correlation_id() {
    let _guard = tracing_test_guard();
    let temp_root = std::env::temp_dir().join(format!(
        "asterforge-persist-test-{}",
        std::process::id()
    ));
    std::fs::create_dir_all(&temp_root).expect("temp root should be created");
    let blocked_parent = temp_root.join("blocked-parent");
    std::fs::write(&blocked_parent, b"not-a-directory")
        .expect("blocked parent file should be created");
    let persistence_path = blocked_parent.join("shell-state.json");

    let state = state_with_services_and_persistence(persistence_path.clone());

    let log_buffer = SharedLogBuffer::default();
    let subscriber = tracing_subscriber::fmt()
        .with_writer(log_buffer.clone())
        .with_ansi(false)
        .without_time()
        .with_max_level(tracing::Level::DEBUG)
        .compact()
        .finish();
    let dispatch = tracing::Dispatch::new(subscriber);

    let _snapshot = {
        let _guard = tracing::dispatcher::set_default(&dispatch);
        state
            .update_shell_panel(ShellPanelMutationRequest {
                document_id: "doc-demo-001".into(),
                panel_id: "combo_view".into(),
                active_tab: Some("tasks".into()),
                visible: None,
                size_hint: None,
            })
            .await
            .expect("shell panel update should succeed even if persistence fails")
    };

    let logs = log_buffer.contents();
    let persist_id = find_correlation_id(&logs, "persisting workspace model")
        .expect("persist correlation id should be present");
    let warning_id = find_correlation_id(&logs, "failed to create shell state directory")
        .expect("persistence warning correlation id should be present");

    assert_eq!(persist_id, warning_id);

    let _ = std::fs::remove_file(&blocked_parent);
    let _ = std::fs::remove_dir_all(&temp_root);
}

#[tokio::test(flavor = "current_thread")]
async fn open_document_logs_bridge_session_open_with_shared_correlation_id() {
    let _guard = tracing_test_guard();
    let state = state_with_services();

    let log_buffer = SharedLogBuffer::default();
    let subscriber = tracing_subscriber::fmt()
        .with_writer(log_buffer.clone())
        .with_ansi(false)
        .without_time()
        .with_max_level(tracing::Level::DEBUG)
        .compact()
        .finish();
    let dispatch = tracing::Dispatch::new(subscriber);

    let _opened = {
        let _guard = tracing::dispatcher::set_default(&dispatch);
        state.open_document("C:/models/contract-open.FCStd".into()).await
    };

    let logs = log_buffer.contents();
    let gateway_id = find_correlation_id(&logs, "opening bridge-backed document session snapshot")
        .unwrap_or_else(|| panic!("gateway open correlation id should be present; logs: {logs}"));
    let bridge_id = find_correlation_id(&logs, "opening prototype bridge document session")
        .unwrap_or_else(|| panic!("bridge open correlation id should be present; logs: {logs}"));

    assert_eq!(gateway_id, bridge_id);
}

#[tokio::test(flavor = "current_thread")]
async fn bootstrap_restore_parse_warning_preserves_correlation_id() {
    let _guard = tracing_test_guard();
    let temp_root = std::env::temp_dir().join(format!(
        "asterforge-bootstrap-restore-test-{}",
        std::process::id()
    ));
    std::fs::create_dir_all(&temp_root).expect("temp root should be created");
    let persistence_path = temp_root.join("shell-state.json");
    std::fs::write(&persistence_path, b"{not-valid-json")
        .expect("invalid persisted state file should be created");

    let log_buffer = SharedLogBuffer::default();
    let subscriber = tracing_subscriber::fmt()
        .with_writer(log_buffer.clone())
        .with_ansi(false)
        .without_time()
        .with_max_level(tracing::Level::DEBUG)
        .compact()
        .finish();
    let dispatch = tracing::Dispatch::new(subscriber);

    let state = {
        let _guard = tracing::dispatcher::set_default(&dispatch);
        state_with_services_and_persistence(persistence_path.clone())
    };

    let document = state.snapshot().await.document;
    assert_eq!(document.document_id, "doc-demo-001");

    let logs = log_buffer.contents();
    let restore_id = find_correlation_id(&logs, "failed to parse persisted shell state")
        .unwrap_or_else(|| panic!("restore warning correlation id should be present; logs: {logs}"));
    let bootstrap_id = find_correlation_id(&logs, "bootstrapping app state")
        .unwrap_or_else(|| panic!("bootstrap correlation id should be present; logs: {logs}"));

    assert_eq!(restore_id, bootstrap_id);

    let _ = std::fs::remove_file(&persistence_path);
    let _ = std::fs::remove_dir_all(&temp_root);
}

#[tokio::test(flavor = "current_thread")]
async fn bootstrap_restore_read_warning_preserves_correlation_id() {
    let _guard = tracing_test_guard();
    let temp_root = std::env::temp_dir().join(format!(
        "asterforge-bootstrap-read-test-{}",
        std::process::id()
    ));
    std::fs::create_dir_all(&temp_root).expect("temp root should be created");

    let log_buffer = SharedLogBuffer::default();
    let subscriber = tracing_subscriber::fmt()
        .with_writer(log_buffer.clone())
        .with_ansi(false)
        .without_time()
        .with_max_level(tracing::Level::DEBUG)
        .compact()
        .finish();
    let dispatch = tracing::Dispatch::new(subscriber);

    let state = {
        let _guard = tracing::dispatcher::set_default(&dispatch);
        state_with_services_and_persistence(temp_root.clone())
    };

    let document = state.snapshot().await.document;
    assert_eq!(document.document_id, "doc-demo-001");

    let logs = log_buffer.contents();
    let restore_id = find_correlation_id(&logs, "failed to read persisted shell state")
        .unwrap_or_else(|| panic!("restore warning correlation id should be present; logs: {logs}"));
    let bootstrap_id = find_correlation_id(&logs, "bootstrapping app state")
        .unwrap_or_else(|| panic!("bootstrap correlation id should be present; logs: {logs}"));

    assert_eq!(restore_id, bootstrap_id);

    let _ = std::fs::remove_dir_all(&temp_root);
}