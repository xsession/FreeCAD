#[cfg(not(test))]
use std::{env, fs, path::PathBuf, process::Command};

use asterforge_command_core::{
    CommandExecutionRequest, CommandExecutionResponse,
    evaluate_extension_inventory_execution_policy, extension_addon_catalog_review_plan,
    extension_execution_failure_event_message, extension_execution_failure_status_message,
    extension_execution_success_event_message, extension_execution_success_status_message,
    extension_external_workbench_review_plan, extension_refresh_lane_plans,
    ExtensionInventorySeedEntry, COMMAND_EXTENSIONS_REFRESH_INVENTORY,
    COMMAND_EXTENSIONS_REVIEW_ADDON_CATALOG, COMMAND_EXTENSIONS_REVIEW_EXTERNAL_WORKBENCHES,
    COMMAND_EXTENSIONS_RUN_INVENTORY_ENTRY,
};

use crate::domain::{BackendEvent, ExtensionCompatibilityState, ExtensionInventoryEntry};

use super::state_types::AppModel;

const REVIEWED_FIXTURE_MACRO_ENTRY_ID: &str = "macro:auto_dimensioning";
#[cfg(not(test))]
const REVIEWED_FIXTURE_MACRO_LABEL: &str = "AutoDimensioning.FCMacro";
const REVIEWED_FAILURE_FIXTURE_MACRO_ENTRY_ID: &str = "macro:broken_reviewed";

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

pub(super) fn handle_extension_command(
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
            for plan in extension_refresh_lane_plans() {
                if let Some(lane) = model
                    .extension_compatibility
                    .lanes
                    .iter_mut()
                    .find(|lane| lane.lane_id == plan.lane_id)
                {
                    lane.status = plan.status;
                    lane.summary = plan.summary;
                    lane.next_steps = plan.next_steps;
                    lane.command_ids = plan.command_ids;
                    lane.inventory_entries = plan
                        .inventory_entries
                        .into_iter()
                        .map(inventory_entry_from_seed)
                        .collect();
                }
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
            let plan = extension_external_workbench_review_plan();
            if let Some(workbench_lane) = model
                .extension_compatibility
                .lanes
                .iter_mut()
                .find(|lane| lane.lane_id == plan.lane_id)
            {
                workbench_lane.status = plan.status;
                workbench_lane.summary = plan.summary;
                workbench_lane.command_ids = plan.command_ids;
                workbench_lane.inventory_entries = plan
                    .inventory_entries
                    .into_iter()
                    .map(inventory_entry_from_seed)
                    .collect();
            }

            Some(CommandExecutionResponse {
                command_id: request.command_id.clone(),
                accepted: true,
                status_message: "Opened external workbench compatibility review lane".into(),
                document_dirty: model.document.dirty,
            })
        }
        COMMAND_EXTENSIONS_REVIEW_ADDON_CATALOG => {
            model.report_dock_visible = true;
            model.bottom_dock_tab = "extensions".into();
            model.extension_compatibility.summary =
                "AddonManager compatibility review is active in backend-owned shell state so provenance, install blockers, and shell-safe migration candidates can be audited without Qt dialogs.".into();
            let plan = extension_addon_catalog_review_plan();
            if let Some(addon_lane) = model
                .extension_compatibility
                .lanes
                .iter_mut()
                .find(|lane| lane.lane_id == plan.lane_id)
            {
                addon_lane.status = plan.status;
                addon_lane.summary = plan.summary;
                addon_lane.next_steps = plan.next_steps;
                addon_lane.command_ids = plan.command_ids;
                addon_lane.inventory_entries = plan
                    .inventory_entries
                    .into_iter()
                    .map(inventory_entry_from_seed)
                    .collect();
            }

            Some(CommandExecutionResponse {
                command_id: request.command_id.clone(),
                accepted: true,
                status_message: "Opened AddonManager compatibility review lane".into(),
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

            if let Some(policy) = evaluate_extension_inventory_execution_policy(
                &entry.label,
                &entry.trust_state,
                &entry.compatibility,
            ) {
                update_inventory_entry_last_run_result(
                    &mut model.extension_compatibility,
                    entry_id,
                    policy.last_run_kind.as_deref(),
                    policy.last_run_level.as_deref(),
                    policy.last_run_status.as_deref(),
                    policy.last_run_detail.as_deref(),
                );
                model.events.insert(
                    0,
                    BackendEvent {
                        topic: "extension_inventory_execution".into(),
                        level: policy.event_level,
                        message: policy.event_message,
                        document_id: model.document.document_id.clone(),
                        object_id: None,
                    },
                );
                return Some(CommandExecutionResponse {
                    command_id: request.command_id.clone(),
                    accepted: policy.accepted,
                    status_message: policy.status_message,
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
                            message: extension_execution_failure_event_message(
                                &entry.label,
                                &failure.detail,
                            ),
                            document_id: model.document.document_id.clone(),
                            object_id: None,
                        },
                    );

                    return Some(CommandExecutionResponse {
                        command_id: request.command_id.clone(),
                        accepted: false,
                        status_message: extension_execution_failure_status_message(&entry.label),
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
                    message: extension_execution_success_event_message(
                        &entry.label,
                        &entry.origin,
                        &launcher_result.status_summary,
                        &launcher_result.output_excerpt,
                    ),
                    document_id: model.document.document_id.clone(),
                    object_id: None,
                },
            );

            Some(CommandExecutionResponse {
                command_id: request.command_id.clone(),
                accepted: true,
                status_message: extension_execution_success_status_message(&entry.label),
                document_dirty: model.document.dirty,
            })
        }
        _ => None,
    }
}

fn inventory_entry_from_seed(entry: ExtensionInventorySeedEntry) -> ExtensionInventoryEntry {
    ExtensionInventoryEntry {
        entry_id: entry.entry_id,
        label: entry.label,
        origin: entry.origin,
        trust_state: entry.trust_state,
        compatibility: entry.compatibility,
        detail: entry.detail,
        action_command_id: entry.action_command_id,
        action_label: entry.action_label,
        last_run_status: None,
        last_run_level: None,
        last_run_detail: None,
        last_run_kind: None,
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
        return Err(ReviewedInventoryRunFailure {
            status_kind: "launcher-failed".into(),
            status_level: "warning".into(),
            status_summary: "Launcher failed".into(),
            detail: format!("Launcher script is missing at {}", launcher_path.display()),
        });
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
    state: &mut ExtensionCompatibilityState,
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