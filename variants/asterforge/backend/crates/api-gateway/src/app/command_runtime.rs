#[cfg(not(test))]
use std::{env, fs, path::PathBuf, process::Command};

use asterforge_command_core::{
    command_behavior, job_title_from_command_id, plan_job_stages,
    plan_command_events, viewport_invalidated_event, CommandExecutionRequest,
    CommandExecutionResponse,
    COMMAND_DOCUMENT_RECOMPUTE, COMMAND_DOCUMENT_REDO, COMMAND_DOCUMENT_SAVE,
    COMMAND_DOCUMENT_UNDO, COMMAND_HISTORY_RESUME_FULL, COMMAND_HISTORY_ROLLBACK_HERE,
    COMMAND_EXTENSIONS_REFRESH_INVENTORY, COMMAND_EXTENSIONS_REVIEW_EXTERNAL_WORKBENCHES,
    COMMAND_EXTENSIONS_RUN_INVENTORY_ENTRY,
    COMMAND_MODEL_TOGGLE_SUPPRESSION, COMMAND_PARTDESIGN_EDIT_PAD,
    COMMAND_PARTDESIGN_EDIT_POCKET, COMMAND_PARTDESIGN_NEW_SKETCH, COMMAND_PARTDESIGN_PAD,
    COMMAND_PARTDESIGN_POCKET, COMMAND_SELECTION_FOCUS, COMMAND_STEP_HIDE_SELECTION,
    COMMAND_STEP_INSPECT_PMI, COMMAND_STEP_ISOLATE_SELECTION, COMMAND_STEP_MEASURE_SELECTION,
    COMMAND_STEP_SELECT_FIRST_CHILD, COMMAND_STEP_SELECT_PARENT, COMMAND_STEP_SHOW_ALL,
    COMMAND_STEP_VIEW_BACK, COMMAND_STEP_VIEW_BOTTOM, COMMAND_STEP_VIEW_FIT_ALL,
    COMMAND_STEP_VIEW_FRONT, COMMAND_STEP_VIEW_ISO, COMMAND_STEP_VIEW_LEFT,
    COMMAND_STEP_VIEW_RESET, COMMAND_STEP_VIEW_RIGHT, COMMAND_STEP_VIEW_TOP,
};
use asterforge_freecad_bridge::{
    compute_viewport_diff, create_pad_from_selected_sketch, create_pocket_from_selected_sketch,
    create_sketch_in_body, resume_full_history, rollback_history_to_selected,
    toggle_selected_suppression, update_selected_pad_profile, update_selected_pocket_profile,
};

use crate::domain::{BackendEvent, JobStageEntry, JobStatusEntry, viewport_diff_response};

use super::state::{AppModel, HttpCommandExecutionResponse};

const REVIEWED_FIXTURE_MACRO_ENTRY_ID: &str = "macro:auto_dimensioning";
const REVIEWED_FIXTURE_MACRO_LABEL: &str = "AutoDimensioning.FCMacro";
const REVIEWED_FAILURE_FIXTURE_MACRO_ENTRY_ID: &str = "macro:broken_reviewed";
const REVIEWED_FAILURE_FIXTURE_MACRO_LABEL: &str = "BrokenReviewedFixture.FCMacro";

struct ReviewedInventoryLaunchResult {
    status_kind: String,
    status_level: String,
    status_summary: String,
    output_excerpt: String,
}

struct ReviewedInventoryRunFailure {
    status_kind: String,
    status_level: String,
    status_summary: String,
    detail: String,
}

pub(super) fn run_command(
    model: &mut AppModel,
    request: CommandExecutionRequest,
) -> HttpCommandExecutionResponse {
    if !model.apply_command_target(request.target_object_id.as_deref()) {
        return HttpCommandExecutionResponse {
            command_id: request.command_id,
            accepted: false,
            status_message: "Target object is not selectable in the active document context".into(),
            document_dirty: model.document.dirty,
            viewport_diff: None,
        };
    }

    let viewport_before = model.bridge_snapshot.viewport.clone();
    let target_object_id = request.target_object_id.clone();

    let behavior = command_behavior(&request.command_id);
    let is_mutating = behavior.opens_undo_transaction();
    if is_mutating {
        let snap_clone = model.bridge_snapshot.clone();
        model.undo_stack.push(&snap_clone);
    }

    let response = execute_command(model, &request);

    if !response.accepted && is_mutating {
        let snap_clone = model.bridge_snapshot.clone();
        model.undo_stack.undo(&snap_clone);
    }

    let viewport_diff = if response.accepted && is_mutating {
        let diff = compute_viewport_diff(&viewport_before, &model.bridge_snapshot.viewport);
        if diff.is_empty() {
            None
        } else {
            Some(viewport_diff_response(
                &model.document.document_id,
                &model.selected_object_id,
                diff,
            ))
        }
    } else {
        None
    };

    let job_title = job_title_from_command_id(&request.command_id);
    let job_stages = plan_job_stages(
        request.command_id.as_str(),
        response.accepted,
        viewport_diff.is_some(),
    );
    let job_entry = JobStatusEntry {
        job_id: format!("job-{}-{}", model.jobs.len() + 1, request.command_id),
        title: job_title,
        command_id: request.command_id.clone(),
        state: if response.accepted {
            "completed".into()
        } else {
            "failed".into()
        },
        progress_percent: if response.accepted { 100 } else { 0 },
        detail: response.status_message.clone(),
        object_id: target_object_id.clone(),
        stages: job_stages
            .iter()
            .cloned()
            .map(|stage| JobStageEntry {
                stage_id: stage.stage_id,
                label: stage.label,
                state: stage.state,
                progress_percent: stage.progress_percent,
            })
            .collect(),
    };
    model.jobs.insert(0, job_entry);
    model.jobs.truncate(8);

    let document_id = model.document.document_id.clone();
    let source = request.arguments.get("source").map(String::as_str);
    for event in plan_command_events(
        request.command_id.as_str(),
        &response.status_message,
        response.accepted,
        &job_stages,
        source,
    )
    .into_iter()
    .rev()
    {
        model.events.insert(
            0,
            BackendEvent {
                topic: event.topic,
                level: event.level,
                message: event.message,
                document_id: document_id.clone(),
                object_id: target_object_id.clone(),
            },
        );
    }

    if response.accepted {
        let selected_object_id = model.selected_object_id.clone();
        let viewport_event = viewport_invalidated_event();
        model.events.insert(
            1,
            BackendEvent {
                topic: viewport_event.topic,
                level: viewport_event.level,
                message: viewport_event.message,
                document_id,
                object_id: Some(selected_object_id),
            },
        );
    }

    HttpCommandExecutionResponse {
        command_id: response.command_id,
        accepted: response.accepted,
        status_message: response.status_message,
        document_dirty: response.document_dirty,
        viewport_diff,
    }
}

fn execute_command(model: &mut AppModel, request: &CommandExecutionRequest) -> CommandExecutionResponse {
    if let Some(response) = handle_step_command(model, request) {
        return response;
    }

    if let Some(response) = handle_document_command(model, request) {
        return response;
    }

    if let Some(response) = handle_history_or_model_command(model, request) {
        return response;
    }

    if let Some(response) = handle_partdesign_command(model, request) {
        return response;
    }

    if let Some(response) = handle_undo_redo_command(model, request) {
        return response;
    }

    if let Some(response) = handle_extension_command(model, request) {
        return response;
    }

    CommandExecutionResponse {
        command_id: request.command_id.clone(),
        accepted: false,
        status_message: format!("Unknown command: {}", request.command_id),
        document_dirty: model.document.dirty,
    }
}

fn handle_extension_command(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> Option<CommandExecutionResponse> {
    match request.command_id.as_str() {
        COMMAND_EXTENSIONS_REFRESH_INVENTORY => {
            let lane_count = model.extension_compatibility.lanes.len();
            model.extension_compatibility.summary = format!(
                "Last refresh completed via backend command runtime. {} compatibility lanes are currently tracked for macros, AddonManager flows, and external workbench registration.",
                lane_count
            );
            if let Some(macros_lane) = model
                .extension_compatibility
                .lanes
                .iter_mut()
                .find(|lane| lane.lane_id == "macros")
            {
                macros_lane.status = "inventory-ready".into();
                macros_lane.summary = "Macro inventory is now staged in backend-owned compatibility state so trust review and execution boundaries can be layered in without reviving Qt dialogs.".into();
                macros_lane.next_steps = vec![
                    "Review discovered macros and assign trust boundaries.".into(),
                    "Replace the reviewed fixture launch with discovered user-macro inventory and persisted approval state.".into(),
                ];
                macros_lane.command_ids = vec!["extensions.refresh_inventory".into()];
                macros_lane.inventory_entries = vec![
                    crate::domain::ExtensionInventoryEntry {
                        entry_id: REVIEWED_FIXTURE_MACRO_ENTRY_ID.into(),
                        label: REVIEWED_FIXTURE_MACRO_LABEL.into(),
                        origin: "Reviewed fixture bundle".into(),
                        trust_state: "reviewed".into(),
                        compatibility: "shell-ready".into(),
                        detail: "Launches through the repo FreeCAD console wrapper against a reviewed headless-safe macro fixture so backend execution, logging, and trust boundaries are exercised end to end.".into(),
                        action_command_id: Some(COMMAND_EXTENSIONS_RUN_INVENTORY_ENTRY.into()),
                        action_label: Some("Run Reviewed Macro".into()),
                        last_run_status: None,
                        last_run_level: None,
                        last_run_detail: None,
                        last_run_kind: None,
                    },
                    crate::domain::ExtensionInventoryEntry {
                        entry_id: REVIEWED_FAILURE_FIXTURE_MACRO_ENTRY_ID.into(),
                        label: REVIEWED_FAILURE_FIXTURE_MACRO_LABEL.into(),
                        origin: "Reviewed failure fixture".into(),
                        trust_state: "reviewed".into(),
                        compatibility: "shell-ready".into(),
                        detail: "Exercises launcher failure handling so the Extensions dock can surface readable execution errors without relying on Qt-era dialogs.".into(),
                        action_command_id: Some(COMMAND_EXTENSIONS_RUN_INVENTORY_ENTRY.into()),
                        action_label: Some("Run Broken Reviewed Macro".into()),
                        last_run_status: None,
                        last_run_level: None,
                        last_run_detail: None,
                        last_run_kind: None,
                    },
                    crate::domain::ExtensionInventoryEntry {
                        entry_id: "macro:legacy_sheetmetal".into(),
                        label: "LegacySheetMetalTools.FCMacro".into(),
                        origin: "Migrated macro bundle".into(),
                        trust_state: "needs-review".into(),
                        compatibility: "qt-bound".into(),
                        detail: "Still assumes Qt dialogs for parameter entry and needs a shell-safe fallback before execution is enabled.".into(),
                        action_command_id: None,
                        action_label: None,
                        last_run_status: None,
                        last_run_level: None,
                        last_run_detail: None,
                        last_run_kind: None,
                    },
                ];
            }
            if let Some(addon_lane) = model
                .extension_compatibility
                .lanes
                .iter_mut()
                .find(|lane| lane.lane_id == "addon-manager")
            {
                addon_lane.status = "inventory-ready".into();
                addon_lane.summary = "Addon provenance and compatibility inventory is now staged in backend state so install and update flows can be wired without reopening Qt-owned UI assumptions.".into();
                addon_lane.inventory_entries = vec![
                    crate::domain::ExtensionInventoryEntry {
                        entry_id: "addon:ifc_tools".into(),
                        label: "IFC Coordination Tools".into(),
                        origin: "Addon registry".into(),
                        trust_state: "registry-signed".into(),
                        compatibility: "reviewing".into(),
                        detail: "Metadata and provenance are available, but the task surfaces still assume PySide widgets.".into(),
                        action_command_id: None,
                        action_label: None,
                        last_run_status: None,
                        last_run_level: None,
                        last_run_detail: None,
                        last_run_kind: None,
                    },
                ];
            }

            Some(CommandExecutionResponse {
                command_id: request.command_id.clone(),
                accepted: true,
                status_message: format!(
                    "Refreshed extension compatibility inventory ({} lanes)",
                    lane_count
                ),
                document_dirty: model.document.dirty,
            })
        }
        COMMAND_EXTENSIONS_REVIEW_EXTERNAL_WORKBENCHES => {
            model.report_dock_visible = true;
            model.bottom_dock_tab = "extensions".into();
            if let Some(workbench_lane) = model
                .extension_compatibility
                .lanes
                .iter_mut()
                .find(|lane| lane.lane_id == "external-workbenches")
            {
                workbench_lane.status = "reviewing".into();
                workbench_lane.summary = "External workbench registration is under active compatibility review so command registration, onboarding, and Qt-bound UI fallbacks can move into explicit shell-safe contracts.".into();
                workbench_lane.command_ids = vec!["extensions.review_external_workbenches".into()];
                workbench_lane.inventory_entries = vec![
                    crate::domain::ExtensionInventoryEntry {
                        entry_id: "workbench:robotics_plus".into(),
                        label: "RoboticsPlusWorkbench".into(),
                        origin: "External workbench manifest".into(),
                        trust_state: "manifest-verified".into(),
                        compatibility: "reviewing".into(),
                        detail: "Command registration is portable, but task panels still require a shell-safe replacement for Qt docking widgets.".into(),
                        action_command_id: None,
                        action_label: None,
                        last_run_status: None,
                        last_run_level: None,
                        last_run_detail: None,
                        last_run_kind: None,
                    },
                ];
            }

            Some(CommandExecutionResponse {
                command_id: request.command_id.clone(),
                accepted: true,
                status_message: "Opened external workbench compatibility review lane".into(),
                document_dirty: model.document.dirty,
            })
        }
        COMMAND_EXTENSIONS_RUN_INVENTORY_ENTRY => {
            let Some(entry_id) = request.arguments.get("entry_id") else {
                return Some(CommandExecutionResponse {
                    command_id: request.command_id.clone(),
                    accepted: false,
                    status_message: "Inventory entry id is required".into(),
                    document_dirty: model.document.dirty,
                });
            };

            let matching_entry = model
                .extension_compatibility
                .lanes
                .iter()
                .flat_map(|lane| lane.inventory_entries.iter())
                .find(|entry| entry.entry_id == *entry_id)
                .cloned();

            let Some(entry) = matching_entry else {
                return Some(CommandExecutionResponse {
                    command_id: request.command_id.clone(),
                    accepted: false,
                    status_message: format!("Extension inventory entry {entry_id} was not found"),
                    document_dirty: model.document.dirty,
                });
            };

            if entry.trust_state != "reviewed" || entry.compatibility != "shell-ready" {
                update_inventory_entry_last_run_result(
                    &mut model.extension_compatibility,
                    entry_id,
                    Some("policy-rejected"),
                    Some("warning"),
                    Some("Blocked by trust policy"),
                    Some("Reviewed backend execution only runs shell-ready entries that have passed explicit trust review."),
                );
                model.events.insert(
                    0,
                    BackendEvent {
                        topic: "extension_inventory_execution".into(),
                        level: "warning".into(),
                        message: format!(
                            "Rejected backend execution for {} because the entry is not reviewed and shell-ready yet",
                            entry.label
                        ),
                        document_id: model.document.document_id.clone(),
                        object_id: None,
                    },
                );
                return Some(CommandExecutionResponse {
                    command_id: request.command_id.clone(),
                    accepted: false,
                    status_message: format!(
                        "{} is not approved for backend execution yet",
                        entry.label
                    ),
                    document_dirty: model.document.dirty,
                });
            }

            let launcher_result = match launch_reviewed_inventory_entry(&entry.entry_id) {
                Ok(status) => status,
                Err(failure) => {
                    update_inventory_entry_last_run_result(
                        &mut model.extension_compatibility,
                        entry_id,
                        Some(&failure.status_kind),
                        Some(&failure.status_level),
                        Some(&failure.status_summary),
                        Some(&failure.detail),
                    );
                    model.events.insert(
                        0,
                        BackendEvent {
                            topic: "extension_inventory_execution".into(),
                            level: failure.status_level.clone(),
                            message: format!(
                                "Failed to execute reviewed inventory entry {}: {}",
                                entry.label, failure.detail
                            ),
                            document_id: model.document.document_id.clone(),
                            object_id: None,
                        },
                    );

                    return Some(CommandExecutionResponse {
                        command_id: request.command_id.clone(),
                        accepted: false,
                        status_message: format!("Failed to execute reviewed inventory entry {}", entry.label),
                        document_dirty: model.document.dirty,
                    });
                }
            };

            model.report_dock_visible = true;
            model.bottom_dock_tab = "extensions".into();
            model.extension_compatibility.summary = format!(
                "Executed reviewed inventory entry {} through the FreeCAD console launcher.",
                entry.label
            );
            update_inventory_entry_last_run_result(
                &mut model.extension_compatibility,
                &entry.entry_id,
                Some(&launcher_result.status_kind),
                Some(&launcher_result.status_level),
                Some(&launcher_result.status_summary),
                Some(&launcher_result.output_excerpt),
            );
            model.events.insert(
                0,
                BackendEvent {
                    topic: "extension_inventory_execution".into(),
                    level: launcher_result.status_level.clone(),
                    message: format!(
                        "Executed reviewed inventory entry {} from {} ({}). Output: {}",
                        entry.label,
                        entry.origin,
                        launcher_result.status_summary,
                        launcher_result.output_excerpt
                    ),
                    document_id: model.document.document_id.clone(),
                    object_id: None,
                },
            );

            Some(CommandExecutionResponse {
                command_id: request.command_id.clone(),
                accepted: true,
                status_message: format!("Executed reviewed inventory entry {}", entry.label),
                document_dirty: model.document.dirty,
            })
        }
        _ => None,
    }
}

#[cfg(test)]
fn launch_reviewed_inventory_entry(
    entry_id: &str,
) -> Result<ReviewedInventoryLaunchResult, ReviewedInventoryRunFailure> {
    if entry_id == REVIEWED_FIXTURE_MACRO_ENTRY_ID {
        Ok(ReviewedInventoryLaunchResult {
            status_kind: "success".into(),
            status_level: "info".into(),
            status_summary: "test launcher success".into(),
            output_excerpt: "ASTERFORGE_MACRO_OK:auto_dimensioning".into(),
        })
    } else if entry_id == REVIEWED_FAILURE_FIXTURE_MACRO_ENTRY_ID {
        Err(ReviewedInventoryRunFailure {
            status_kind: "launcher-failed".into(),
            status_level: "warning".into(),
            status_summary: "Launcher failed".into(),
            detail: "test launcher failure".into(),
        })
    } else {
        Err(ReviewedInventoryRunFailure {
            status_kind: "fixture-missing".into(),
            status_level: "warning".into(),
            status_summary: "Reviewed fixture is missing".into(),
            detail: format!("No reviewed launcher fixture is registered for {entry_id}"),
        })
    }
}

#[cfg(not(test))]
fn launch_reviewed_inventory_entry(
    entry_id: &str,
) -> Result<ReviewedInventoryLaunchResult, ReviewedInventoryRunFailure> {
    let macro_path = reviewed_inventory_entry_macro_path(entry_id).ok_or_else(|| {
        ReviewedInventoryRunFailure {
            status_kind: "fixture-missing".into(),
            status_level: "warning".into(),
            status_summary: "Reviewed fixture is missing".into(),
            detail: format!("No reviewed launcher fixture is registered for {entry_id}"),
        }
    })?;

    if !macro_path.exists() {
        return Err(ReviewedInventoryRunFailure {
            status_kind: "fixture-missing".into(),
            status_level: "warning".into(),
            status_summary: "Reviewed fixture is missing".into(),
            detail: format!("Macro fixture is missing at {}", macro_path.display()),
        });
    }

    let repo_root = freecad_repo_root();
    let launcher_path = repo_root.join("run_freecad.bat");
    if !launcher_path.exists() {
        return Err(format!("Launcher script is missing at {}", launcher_path.display()));
    }

    let wrapper_dir = env::temp_dir().join("FreeCAD").join("asterforge-extension-scripts");
    fs::create_dir_all(&wrapper_dir)
        .map_err(|error| ReviewedInventoryRunFailure {
            status_kind: "launcher-failed".into(),
            status_level: "warning".into(),
            status_summary: "Launcher failed".into(),
            detail: format!("Failed to create launcher wrapper directory: {error}"),
        })?;

    let wrapper_path = wrapper_dir.join(format!(
        "run-reviewed-entry-{}-{}.py",
        sanitize_entry_id(entry_id),
        std::process::id()
    ));
    let wrapper_source = format!(
        "import runpy\nrunpy.run_path(r\"{}\", run_name=\"__main__\")\n",
        macro_path.display()
    );
    fs::write(&wrapper_path, wrapper_source)
        .map_err(|error| ReviewedInventoryRunFailure {
            status_kind: "launcher-failed".into(),
            status_level: "warning".into(),
            status_summary: "Launcher failed".into(),
            detail: format!("Failed to write launcher wrapper: {error}"),
        })?;

    let output = Command::new("cmd")
        .args([
            "/d",
            "/c",
            launcher_path.to_string_lossy().as_ref(),
            "--console",
            "--no-log",
            "--run-script",
            wrapper_path.to_string_lossy().as_ref(),
        ])
        .current_dir(&repo_root)
        .output()
        .map_err(|error| ReviewedInventoryRunFailure {
            status_kind: "launcher-failed".into(),
            status_level: "warning".into(),
            status_summary: "Launcher failed".into(),
            detail: format!("Failed to launch FreeCAD console wrapper: {error}"),
        });

    let _ = fs::remove_file(&wrapper_path);

    let output = output?;
    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
        let stdout = String::from_utf8_lossy(&output.stdout).trim().to_string();
        let detail = if !stderr.is_empty() {
            stderr
        } else if !stdout.is_empty() {
            stdout
        } else {
            format!("launcher exited with status {}", output.status)
        };
        return Err(ReviewedInventoryRunFailure {
            status_kind: "launcher-failed".into(),
            status_level: "warning".into(),
            status_summary: "Launcher failed".into(),
            detail,
        });
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);
    let excerpt = launcher_output_excerpt(&stdout, &stderr);
    if stdout.contains("ASTERFORGE_MACRO_OK:auto_dimensioning") {
        Ok(ReviewedInventoryLaunchResult {
            status_kind: "success".into(),
            status_level: "info".into(),
            status_summary: "launcher confirmed macro execution".into(),
            output_excerpt: excerpt,
        })
    } else {
        Ok(ReviewedInventoryLaunchResult {
            status_kind: "success".into(),
            status_level: "info".into(),
            status_summary: "launcher completed without explicit macro token".into(),
            output_excerpt: excerpt,
        })
    }
}

#[cfg(not(test))]
fn reviewed_inventory_entry_macro_path(entry_id: &str) -> Option<PathBuf> {
    match entry_id {
        REVIEWED_FIXTURE_MACRO_ENTRY_ID => Some(
            freecad_repo_root()
                .join("variants")
                .join("asterforge")
                .join("backend")
                .join("fixtures")
                .join("macros")
                .join(REVIEWED_FIXTURE_MACRO_LABEL),
        ),
            REVIEWED_FAILURE_FIXTURE_MACRO_ENTRY_ID => None,
        _ => None,
    }
}

#[cfg(not(test))]
fn freecad_repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../../../..")
}

#[cfg(not(test))]
fn sanitize_entry_id(value: &str) -> String {
    value
        .chars()
        .map(|ch| if ch.is_ascii_alphanumeric() { ch } else { '-' })
        .collect()
}

fn update_inventory_entry_last_run_result(
    state: &mut crate::domain::ExtensionCompatibilityState,
    entry_id: &str,
    last_run_kind: Option<&str>,
    last_run_level: Option<&str>,
    last_run_status: Option<&str>,
    last_run_detail: Option<&str>,
) {
    if let Some(entry) = state
        .lanes
        .iter_mut()
        .flat_map(|lane| lane.inventory_entries.iter_mut())
        .find(|entry| entry.entry_id == entry_id)
    {
        entry.last_run_kind = last_run_kind.map(str::to_string);
        entry.last_run_status = last_run_status.map(str::to_string);
        entry.last_run_level = last_run_level.map(str::to_string);
        entry.last_run_detail = last_run_detail.map(str::to_string);
    }
}

#[cfg(not(test))]
fn launcher_output_excerpt(stdout: &str, stderr: &str) -> String {
    let candidate = stdout
        .lines()
        .chain(stderr.lines())
        .map(str::trim)
        .find(|line| !line.is_empty())
        .unwrap_or("launcher produced no console output");

    const MAX_LEN: usize = 160;
    if candidate.len() <= MAX_LEN {
        candidate.to_string()
    } else {
        format!("{}...", &candidate[..MAX_LEN])
    }
}

fn handle_step_command(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> Option<CommandExecutionResponse> {
    if !model.step_cache_by_document.contains_key(&model.document.document_id) {
        return None;
    }

    match request.command_id.as_str() {
        COMMAND_SELECTION_FOCUS => Some(handle_step_focus_selection(model, request)),
        COMMAND_STEP_VIEW_ISO => Some(handle_step_view_preset(model, request, "iso")),
        COMMAND_STEP_VIEW_FIT_ALL => Some(handle_step_view_fit_all(model, request)),
        COMMAND_STEP_VIEW_RESET => Some(handle_step_view_reset(model, request)),
        COMMAND_STEP_VIEW_FRONT => Some(handle_step_view_preset(model, request, "front")),
        COMMAND_STEP_VIEW_BACK => Some(handle_step_view_preset(model, request, "back")),
        COMMAND_STEP_VIEW_RIGHT => Some(handle_step_view_preset(model, request, "right")),
        COMMAND_STEP_VIEW_LEFT => Some(handle_step_view_preset(model, request, "left")),
        COMMAND_STEP_VIEW_TOP => Some(handle_step_view_preset(model, request, "top")),
        COMMAND_STEP_VIEW_BOTTOM => Some(handle_step_view_preset(model, request, "bottom")),
        COMMAND_STEP_SELECT_PARENT => Some(handle_step_select_parent(model, request)),
        COMMAND_STEP_SELECT_FIRST_CHILD => Some(handle_step_select_first_child(model, request)),
        COMMAND_STEP_INSPECT_PMI => Some(handle_step_inspect_pmi(model, request)),
        COMMAND_STEP_MEASURE_SELECTION => Some(handle_step_measure_selection(model, request)),
        COMMAND_STEP_HIDE_SELECTION => Some(handle_step_hide_selection(model, request)),
        COMMAND_STEP_ISOLATE_SELECTION => Some(handle_step_isolate_selection(model, request)),
        COMMAND_STEP_SHOW_ALL => Some(handle_step_show_all(model, request)),
        _ => None,
    }
}

fn handle_step_focus_selection(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> CommandExecutionResponse {
    let Some(cache) = model.step_cache_by_document.get(&model.document.document_id) else {
        return rejected_step_command(model, request, "STEP cache is unavailable");
    };
    let Some(camera) = super::state::step_focus_camera_for_selection(&model.selected_object_id, cache) else {
        return rejected_step_command(model, request, "Selected STEP node has no focusable tessellated payload");
    };

    model
        .step_viewport_camera_by_document
        .insert(model.document.document_id.clone(), camera);
    CommandExecutionResponse {
        command_id: request.command_id.clone(),
        accepted: true,
        status_message: format!("Focused STEP selection {}", model.selected_object_id),
        document_dirty: model.document.dirty,
    }
}

fn handle_step_view_preset(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
    preset: &str,
) -> CommandExecutionResponse {
    let Some(camera) = super::state::step_viewport_camera_for_preset(
        model.step_viewport_camera_by_document.get(&model.document.document_id),
        preset,
    ) else {
        return rejected_step_command(model, request, "Unknown STEP viewport preset");
    };

    model
        .step_viewport_camera_by_document
        .insert(model.document.document_id.clone(), camera);
    CommandExecutionResponse {
        command_id: request.command_id.clone(),
        accepted: true,
        status_message: format!("Applied STEP {} view", preset),
        document_dirty: model.document.dirty,
    }
}

fn handle_step_view_reset(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> CommandExecutionResponse {
    model.step_viewport_camera_by_document.insert(
        model.document.document_id.clone(),
        super::state::step_reset_viewport_camera(),
    );
    CommandExecutionResponse {
        command_id: request.command_id.clone(),
        accepted: true,
        status_message: "Reset STEP view to the default inspection camera".into(),
        document_dirty: model.document.dirty,
    }
}

fn handle_step_view_fit_all(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> CommandExecutionResponse {
    let Some(cache) = model.step_cache_by_document.get(&model.document.document_id) else {
        return rejected_step_command(model, request, "STEP cache is unavailable");
    };
    let Some(camera) = super::state::step_fit_all_viewport_camera(
        cache,
        &model.object_tree,
        model.step_viewport_camera_by_document.get(&model.document.document_id),
    ) else {
        return rejected_step_command(model, request, "Visible STEP geometry has no fit-all bounds");
    };

    model
        .step_viewport_camera_by_document
        .insert(model.document.document_id.clone(), camera);
    CommandExecutionResponse {
        command_id: request.command_id.clone(),
        accepted: true,
        status_message: "Fit all visible STEP geometry in the viewport".into(),
        document_dirty: model.document.dirty,
    }
}

fn handle_document_command(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> Option<CommandExecutionResponse> {
    match request.command_id.as_str() {
        COMMAND_DOCUMENT_SAVE => {
            model.document.dirty = false;
            model.bridge_snapshot.dirty = false;
            Some(CommandExecutionResponse {
                command_id: request.command_id.clone(),
                accepted: true,
                status_message: "Document marked as saved".into(),
                document_dirty: model.document.dirty,
            })
        }
        COMMAND_DOCUMENT_RECOMPUTE => {
            model.document.dirty = true;
            model.bridge_snapshot.dirty = true;
            Some(CommandExecutionResponse {
                command_id: request.command_id.clone(),
                accepted: true,
                status_message: "Recompute queued through bridge-backed mock backend".into(),
                document_dirty: model.document.dirty,
            })
        }
        COMMAND_SELECTION_FOCUS => Some(CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: true,
            status_message: "Selection focus requested".into(),
            document_dirty: model.document.dirty,
        }),
        _ => None,
    }
}

fn handle_step_select_parent(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> CommandExecutionResponse {
    let Some(cache) = model.step_cache_by_document.get(&model.document.document_id) else {
        return rejected_step_command(model, request, "STEP cache is unavailable");
    };
    let Some(parent_id) = super::state::step_parent_object_id(
        &model.selected_object_id,
        &cache.scene_bundle.assemblies,
    ) else {
        return rejected_step_command(model, request, "Selected STEP node has no parent assembly");
    };

    model.selected_object_id = parent_id.clone();
    CommandExecutionResponse {
        command_id: request.command_id.clone(),
        accepted: true,
        status_message: format!("Selected parent node {}", parent_id),
        document_dirty: model.document.dirty,
    }
}

fn handle_step_select_first_child(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> CommandExecutionResponse {
    let Some(cache) = model.step_cache_by_document.get(&model.document.document_id) else {
        return rejected_step_command(model, request, "STEP cache is unavailable");
    };
    let Some(child_id) = super::state::step_first_child_object_id(
        &model.selected_object_id,
        &cache.scene_bundle.assemblies,
    ) else {
        return rejected_step_command(model, request, "Selected STEP node has no child assembly");
    };

    model.selected_object_id = child_id.clone();
    CommandExecutionResponse {
        command_id: request.command_id.clone(),
        accepted: true,
        status_message: format!("Selected child node {}", child_id),
        document_dirty: model.document.dirty,
    }
}

fn handle_step_inspect_pmi(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> CommandExecutionResponse {
    let Some(cache) = model.step_cache_by_document.get(&model.document.document_id) else {
        return rejected_step_command(model, request, "STEP cache is unavailable");
    };
    let Some(result) = super::state::step_pmi_inspection_for_selection(
        &model.selected_object_id,
        cache,
        &model.object_tree,
    ) else {
        return rejected_step_command(model, request, "Selected STEP entity has no semantic PMI");
    };

    model
        .step_pmi_inspection_by_document
        .insert(model.document.document_id.clone(), result.clone());
    model.combo_view_visible = true;
    model.combo_view_tab = "tasks".into();
    model.report_dock_visible = true;
    model.bottom_dock_tab = "report".into();
    let document_id = model.document.document_id.clone();
    let object_id = Some(model.selected_object_id.clone());
    for annotation in result.annotations.iter().rev() {
        model.events.insert(
            0,
            BackendEvent {
                topic: "step_pmi_annotation".into(),
                level: "info".into(),
                message: format!(
                    "{}: {} (targets: {})",
                    annotation.semantic_type,
                    annotation.text,
                    annotation
                        .target_entity_ids
                        .iter()
                        .map(|entity_id| format!("#{}", entity_id))
                        .collect::<Vec<_>>()
                        .join(", ")
                ),
                document_id: document_id.clone(),
                object_id: object_id.clone(),
            },
        );
    }
    model.events.insert(
        0,
        BackendEvent {
            topic: "step_pmi_inspection".into(),
            level: "info".into(),
            message: format!(
                "Loaded PMI inspection for {} / #{}",
                result.label, result.entity_id
            ),
            document_id,
            object_id,
        },
    );
    CommandExecutionResponse {
        command_id: request.command_id.clone(),
        accepted: true,
        status_message: format!(
            "Loaded PMI inspection for {} ({} annotations)",
            result.label,
            result.annotations.len()
        ),
        document_dirty: model.document.dirty,
    }
}

fn handle_step_hide_selection(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> CommandExecutionResponse {
    if !super::state::step_hide_object_subtree(&mut model.object_tree, &model.selected_object_id) {
        return rejected_step_command(model, request, "Selected STEP node could not be hidden");
    }

    CommandExecutionResponse {
        command_id: request.command_id.clone(),
        accepted: true,
        status_message: format!("Hidden STEP subtree rooted at {}", model.selected_object_id),
        document_dirty: model.document.dirty,
    }
}

fn handle_step_measure_selection(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> CommandExecutionResponse {
    let Some(cache) = model.step_cache_by_document.get(&model.document.document_id) else {
        return rejected_step_command(model, request, "STEP cache is unavailable");
    };
    let Some(result) = super::state::step_measurement_for_selection(&model.selected_object_id, cache) else {
        return rejected_step_command(model, request, "Selected STEP node has no measurable tessellated payload");
    };

    model
        .step_measurement_by_document
        .insert(model.document.document_id.clone(), result.clone());
    model.combo_view_visible = true;
    model.combo_view_tab = "tasks".into();
    model.report_dock_visible = true;
    model.bottom_dock_tab = "report".into();
    model.events.insert(
        0,
        BackendEvent {
            topic: "step_measurement".into(),
            level: "info".into(),
            message: format!(
                "Measured {} at {:.2} x {:.2} x {:.2}",
                result.label, result.span_x, result.span_y, result.span_z
            ),
            document_id: model.document.document_id.clone(),
            object_id: Some(model.selected_object_id.clone()),
        },
    );

    CommandExecutionResponse {
        command_id: request.command_id.clone(),
        accepted: true,
        status_message: format!(
            "Measured {} at {:.2} x {:.2} x {:.2}",
            result.label, result.span_x, result.span_y, result.span_z
        ),
        document_dirty: model.document.dirty,
    }
}

fn handle_step_isolate_selection(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> CommandExecutionResponse {
    if !super::state::step_isolate_object_subtree(&mut model.object_tree, &model.selected_object_id) {
        return rejected_step_command(model, request, "Selected STEP node could not be isolated");
    }

    CommandExecutionResponse {
        command_id: request.command_id.clone(),
        accepted: true,
        status_message: format!("Isolated STEP subtree rooted at {}", model.selected_object_id),
        document_dirty: model.document.dirty,
    }
}

fn handle_step_show_all(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> CommandExecutionResponse {
    super::state::step_show_all_objects(&mut model.object_tree);

    CommandExecutionResponse {
        command_id: request.command_id.clone(),
        accepted: true,
        status_message: "Restored all STEP nodes to the inspection viewport".into(),
        document_dirty: model.document.dirty,
    }
}

fn rejected_step_command(
    model: &AppModel,
    request: &CommandExecutionRequest,
    message: &str,
) -> CommandExecutionResponse {
    CommandExecutionResponse {
        command_id: request.command_id.clone(),
        accepted: false,
        status_message: message.into(),
        document_dirty: model.document.dirty,
    }
}

fn handle_history_or_model_command(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> Option<CommandExecutionResponse> {
    match request.command_id.as_str() {
        COMMAND_HISTORY_ROLLBACK_HERE => Some(handle_history_rollback(model, request)),
        COMMAND_HISTORY_RESUME_FULL => Some(handle_history_resume(model, request)),
        COMMAND_MODEL_TOGGLE_SUPPRESSION => Some(handle_toggle_suppression(model, request)),
        _ => None,
    }
}

fn handle_partdesign_command(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> Option<CommandExecutionResponse> {
    match request.command_id.as_str() {
        COMMAND_PARTDESIGN_NEW_SKETCH => Some(handle_new_sketch(model, request)),
        COMMAND_PARTDESIGN_EDIT_POCKET => Some(handle_edit_pocket(model, request)),
        COMMAND_PARTDESIGN_EDIT_PAD => Some(handle_edit_pad(model, request)),
        COMMAND_PARTDESIGN_POCKET => Some(handle_new_pocket(model, request)),
        COMMAND_PARTDESIGN_PAD => Some(handle_new_pad(model, request)),
        _ => None,
    }
}

fn handle_undo_redo_command(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> Option<CommandExecutionResponse> {
    match request.command_id.as_str() {
        COMMAND_DOCUMENT_UNDO => Some(handle_undo(model, request)),
        COMMAND_DOCUMENT_REDO => Some(handle_redo(model, request)),
        _ => None,
    }
}

fn handle_history_rollback(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> CommandExecutionResponse {
    if let Some((object_id, sequence_index)) = rollback_history_to_selected(&mut model.bridge_snapshot) {
        model.sync_from_snapshot();
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: true,
            status_message: format!(
                "Rolled back model evaluation to {} at step {}",
                object_id, sequence_index
            ),
            document_dirty: model.document.dirty,
        }
    } else {
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: false,
            status_message: "Rollback requires a selected history feature".into(),
            document_dirty: model.document.dirty,
        }
    }
}

fn handle_history_resume(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> CommandExecutionResponse {
    if resume_full_history(&mut model.bridge_snapshot) {
        model.sync_from_snapshot();
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: true,
            status_message: "Restored full feature history".into(),
            document_dirty: model.document.dirty,
        }
    } else {
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: false,
            status_message: "Feature history is already fully resumed".into(),
            document_dirty: model.document.dirty,
        }
    }
}

fn handle_toggle_suppression(
    model: &mut AppModel,
    request: &CommandExecutionRequest,
) -> CommandExecutionResponse {
    if let Some((object_id, suppressed)) = toggle_selected_suppression(&mut model.bridge_snapshot) {
        model.sync_from_snapshot();
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: true,
            status_message: if suppressed {
                format!("Suppressed {}", object_id)
            } else {
                format!("Unsuppressed {}", object_id)
            },
            document_dirty: model.document.dirty,
        }
    } else {
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: false,
            status_message: "Suppression requires a non-body selection".into(),
            document_dirty: model.document.dirty,
        }
    }
}

fn handle_new_sketch(model: &mut AppModel, request: &CommandExecutionRequest) -> CommandExecutionResponse {
    let requested_label = request.arguments.get("sketch_label").map(String::as_str);
    let reference_plane = request.arguments.get("reference_plane").map(String::as_str);
    if create_sketch_in_body(
        &mut model.bridge_snapshot,
        requested_label,
        reference_plane,
    )
    .is_some()
    {
        model.sync_from_snapshot();
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: true,
            status_message: format!(
                "Created a new sketch in the active body on {}: {}",
                reference_plane.unwrap_or("XY"),
                model.selected_object_id,
            ),
            document_dirty: model.document.dirty,
        }
    } else {
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: false,
            status_message: "Sketch creation requires the body to be selected".into(),
            document_dirty: model.document.dirty,
        }
    }
}

fn handle_edit_pocket(model: &mut AppModel, request: &CommandExecutionRequest) -> CommandExecutionResponse {
    let parsed_depth = request
        .arguments
        .get("depth_mm")
        .and_then(|value| value.parse::<f32>().ok());
    let parsed_extent_mode = request.arguments.get("extent_mode").map(String::as_str);
    let normalized_depth = parsed_depth.filter(|value| *value > 0.0);
    let updated = update_selected_pocket_profile(
        &mut model.bridge_snapshot,
        normalized_depth,
        parsed_extent_mode,
    );

    if model.selected_object_id.starts_with("pocket-") && updated.is_some() {
        model.sync_from_snapshot();
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: true,
            status_message: format!(
                "Updated {} to {:.2} mm depth ({})",
                model.selected_object_id,
                parsed_depth.unwrap_or(0.0),
                parsed_extent_mode.unwrap_or("dimension")
            ),
            document_dirty: model.document.dirty,
        }
    } else if model.selected_object_id.starts_with("pocket-") {
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: false,
            status_message: "Pocket editing requires a positive depth_mm argument".into(),
            document_dirty: model.document.dirty,
        }
    } else {
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: false,
            status_message: "Pocket editing requires an active pocket selection".into(),
            document_dirty: model.document.dirty,
        }
    }
}

fn handle_edit_pad(model: &mut AppModel, request: &CommandExecutionRequest) -> CommandExecutionResponse {
    let parsed_length = request
        .arguments
        .get("length_mm")
        .and_then(|value| value.parse::<f32>().ok());
    let parsed_midplane = request
        .arguments
        .get("midplane")
        .and_then(|value| parse_bool_flag(value));
    let normalized_length = parsed_length.filter(|value| *value > 0.0);
    let updated = update_selected_pad_profile(
        &mut model.bridge_snapshot,
        normalized_length,
        parsed_midplane,
    );

    if updated.is_some() {
        model.sync_from_snapshot();
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: true,
            status_message: format!(
                "Updated {} to {:.2} mm ({})",
                model.selected_object_id,
                parsed_length.unwrap_or(0.0),
                if parsed_midplane.unwrap_or(false) {
                    "symmetric"
                } else {
                    "one-sided"
                }
            ),
            document_dirty: model.document.dirty,
        }
    } else if model.selected_object_id.starts_with("pad-") {
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: false,
            status_message: "Pad editing requires a positive length_mm argument".into(),
            document_dirty: model.document.dirty,
        }
    } else {
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: false,
            status_message: "Pad editing requires an active pad selection".into(),
            document_dirty: model.document.dirty,
        }
    }
}

fn handle_new_pocket(model: &mut AppModel, request: &CommandExecutionRequest) -> CommandExecutionResponse {
    let parsed_depth = request
        .arguments
        .get("depth_mm")
        .and_then(|value| value.parse::<f32>().ok());
    let parsed_extent_mode = request.arguments.get("extent_mode").map(String::as_str);
    if create_pocket_from_selected_sketch(
        &mut model.bridge_snapshot,
        parsed_depth,
        parsed_extent_mode,
    )
    .is_some()
    {
        model.sync_from_snapshot();
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: true,
            status_message: format!(
                "Created a new pocket feature from the selected sketch ({})",
                parsed_extent_mode.unwrap_or("dimension")
            ),
            document_dirty: model.document.dirty,
        }
    } else {
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: false,
            status_message: "Pocket creation requires an active sketch selection".into(),
            document_dirty: model.document.dirty,
        }
    }
}

fn handle_new_pad(model: &mut AppModel, request: &CommandExecutionRequest) -> CommandExecutionResponse {
    let parsed_length = request
        .arguments
        .get("length_mm")
        .and_then(|value| value.parse::<f32>().ok());
    let parsed_midplane = request
        .arguments
        .get("midplane")
        .and_then(|value| parse_bool_flag(value))
        .unwrap_or(false);
    let pad_length = parsed_length.filter(|value| *value > 0.0);

    if create_pad_from_selected_sketch(
        &mut model.bridge_snapshot,
        pad_length,
        Some("dimension"),
        parsed_midplane,
    )
    .is_some()
    {
        model.sync_from_snapshot();
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: true,
            status_message: format!(
                "Created a new pad feature from the selected sketch at {:.2} mm ({})",
                pad_length.unwrap_or(12.0),
                if parsed_midplane { "symmetric" } else { "one-sided" }
            ),
            document_dirty: model.document.dirty,
        }
    } else {
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: false,
            status_message: "Pad creation requires an active sketch selection".into(),
            document_dirty: model.document.dirty,
        }
    }
}

fn handle_undo(model: &mut AppModel, request: &CommandExecutionRequest) -> CommandExecutionResponse {
    let current_snap = model.bridge_snapshot.clone();
    if let Some(previous) = model.undo_stack.undo(&current_snap) {
        model.bridge_snapshot = previous;
        model.sync_from_snapshot();
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: true,
            status_message: "Undo applied".into(),
            document_dirty: model.document.dirty,
        }
    } else {
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: false,
            status_message: "Nothing to undo".into(),
            document_dirty: model.document.dirty,
        }
    }
}

fn handle_redo(model: &mut AppModel, request: &CommandExecutionRequest) -> CommandExecutionResponse {
    let current_snap = model.bridge_snapshot.clone();
    if let Some(next) = model.undo_stack.redo(&current_snap) {
        model.bridge_snapshot = next;
        model.sync_from_snapshot();
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: true,
            status_message: "Redo applied".into(),
            document_dirty: model.document.dirty,
        }
    } else {
        CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: false,
            status_message: "Nothing to redo".into(),
            document_dirty: model.document.dirty,
        }
    }
}

fn parse_bool_flag(value: &str) -> Option<bool> {
    match value {
        "true" | "1" | "yes" | "on" => Some(true),
        "false" | "0" | "no" | "off" => Some(false),
        _ => None,
    }
}
