use std::collections::HashMap;

use serde::{Deserialize, Serialize};

pub const COMMAND_DOCUMENT_RECOMPUTE: &str = "document.recompute";
pub const COMMAND_DOCUMENT_SAVE: &str = "document.save";
pub const COMMAND_SELECTION_FOCUS: &str = "selection.focus";
pub const COMMAND_PARTDESIGN_NEW_SKETCH: &str = "partdesign.new_sketch";
pub const COMMAND_PARTDESIGN_PAD: &str = "partdesign.pad";
pub const COMMAND_PARTDESIGN_POCKET: &str = "partdesign.pocket";
pub const COMMAND_PARTDESIGN_EDIT_PAD: &str = "partdesign.edit_pad";
pub const COMMAND_PARTDESIGN_EDIT_POCKET: &str = "partdesign.edit_pocket";
pub const COMMAND_HISTORY_ROLLBACK_HERE: &str = "history.rollback_here";
pub const COMMAND_HISTORY_RESUME_FULL: &str = "history.resume_full";
pub const COMMAND_MODEL_TOGGLE_SUPPRESSION: &str = "model.toggle_suppression";
pub const COMMAND_DOCUMENT_UNDO: &str = "document.undo";
pub const COMMAND_DOCUMENT_REDO: &str = "document.redo";

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct CommandSpec {
    pub command_id: &'static str,
    pub label: &'static str,
    pub group: &'static str,
    pub shortcut: Option<&'static str>,
    pub requires_selection: bool,
    pub description: &'static str,
    pub action_label: Option<&'static str>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CommandArgumentDefinition {
    pub argument_id: String,
    pub label: String,
    pub value_type: String,
    pub required: bool,
    pub default_value: Option<String>,
    pub placeholder: Option<String>,
    pub unit: Option<String>,
    pub options: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CommandDefinition {
    pub command_id: String,
    pub label: String,
    pub group: String,
    pub shortcut: Option<String>,
    pub enabled: bool,
    pub requires_selection: bool,
    pub description: String,
    pub action_label: Option<String>,
    pub arguments: Vec<CommandArgumentDefinition>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CommandExecutionRequest {
    pub command_id: String,
    pub document_id: String,
    pub target_object_id: Option<String>,
    pub arguments: HashMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CommandExecutionResponse {
    pub command_id: String,
    pub accepted: bool,
    pub status_message: String,
    pub document_dirty: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CommandTransactionMode {
    ReadOnly,
    Mutating,
    UndoRedo,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CommandJobKind {
    BridgeRecompute,
    PersistDocument,
    BridgeMutation,
    BackendDispatch,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct CommandBehavior {
    pub transaction_mode: CommandTransactionMode,
    pub job_kind: CommandJobKind,
}

impl CommandBehavior {
    pub fn opens_undo_transaction(self) -> bool {
        matches!(self.transaction_mode, CommandTransactionMode::Mutating)
    }
}

pub fn command_behavior(command_id: &str) -> CommandBehavior {
    match command_id {
        COMMAND_DOCUMENT_RECOMPUTE => CommandBehavior {
            transaction_mode: CommandTransactionMode::Mutating,
            job_kind: CommandJobKind::BridgeRecompute,
        },
        COMMAND_DOCUMENT_SAVE => CommandBehavior {
            transaction_mode: CommandTransactionMode::ReadOnly,
            job_kind: CommandJobKind::PersistDocument,
        },
        COMMAND_PARTDESIGN_NEW_SKETCH
        | COMMAND_PARTDESIGN_PAD
        | COMMAND_PARTDESIGN_POCKET
        | COMMAND_PARTDESIGN_EDIT_PAD
        | COMMAND_PARTDESIGN_EDIT_POCKET
        | COMMAND_HISTORY_ROLLBACK_HERE
        | COMMAND_HISTORY_RESUME_FULL
        | COMMAND_MODEL_TOGGLE_SUPPRESSION => CommandBehavior {
            transaction_mode: CommandTransactionMode::Mutating,
            job_kind: CommandJobKind::BridgeMutation,
        },
        COMMAND_DOCUMENT_UNDO | COMMAND_DOCUMENT_REDO => CommandBehavior {
            transaction_mode: CommandTransactionMode::UndoRedo,
            job_kind: CommandJobKind::BackendDispatch,
        },
        COMMAND_SELECTION_FOCUS => CommandBehavior {
            transaction_mode: CommandTransactionMode::ReadOnly,
            job_kind: CommandJobKind::BackendDispatch,
        },
        _ => CommandBehavior {
            transaction_mode: CommandTransactionMode::ReadOnly,
            job_kind: CommandJobKind::BackendDispatch,
        },
    }
}

pub fn command_spec(command_id: &str) -> Option<CommandSpec> {
    match command_id {
        COMMAND_DOCUMENT_RECOMPUTE => Some(CommandSpec {
            command_id: COMMAND_DOCUMENT_RECOMPUTE,
            label: "Recompute",
            group: "Document",
            shortcut: Some("Ctrl+R"),
            requires_selection: false,
            description: "Rebuild the dependency graph and refresh the active model.",
            action_label: Some("Recompute"),
        }),
        COMMAND_DOCUMENT_SAVE => Some(CommandSpec {
            command_id: COMMAND_DOCUMENT_SAVE,
            label: "Save",
            group: "Document",
            shortcut: Some("Ctrl+S"),
            requires_selection: false,
            description: "Persist the current document state through the backend pipeline.",
            action_label: Some("Save"),
        }),
        COMMAND_SELECTION_FOCUS => Some(CommandSpec {
            command_id: COMMAND_SELECTION_FOCUS,
            label: "Focus Selection",
            group: "View",
            shortcut: Some("F"),
            requires_selection: true,
            description: "Center the viewport workflow around the currently selected object.",
            action_label: Some("Focus"),
        }),
        COMMAND_PARTDESIGN_NEW_SKETCH => Some(CommandSpec {
            command_id: COMMAND_PARTDESIGN_NEW_SKETCH,
            label: "Create Sketch",
            group: "PartDesign",
            shortcut: None,
            requires_selection: true,
            description: "Create a new sketch inside the selected body.",
            action_label: Some("Create Sketch"),
        }),
        COMMAND_PARTDESIGN_PAD => Some(CommandSpec {
            command_id: COMMAND_PARTDESIGN_PAD,
            label: "Create Pad",
            group: "PartDesign",
            shortcut: None,
            requires_selection: true,
            description: "Extrude the active sketch into a solid PartDesign feature.",
            action_label: Some("Create Pad"),
        }),
        COMMAND_PARTDESIGN_POCKET => Some(CommandSpec {
            command_id: COMMAND_PARTDESIGN_POCKET,
            label: "Create Pocket",
            group: "PartDesign",
            shortcut: None,
            requires_selection: true,
            description: "Cut material from the active sketch profile into the body.",
            action_label: Some("Create Pocket"),
        }),
        COMMAND_PARTDESIGN_EDIT_PAD => Some(CommandSpec {
            command_id: COMMAND_PARTDESIGN_EDIT_PAD,
            label: "Edit Pad",
            group: "PartDesign",
            shortcut: None,
            requires_selection: true,
            description: "Open the selected pad feature for parameter editing.",
            action_label: Some("Apply Pad"),
        }),
        COMMAND_PARTDESIGN_EDIT_POCKET => Some(CommandSpec {
            command_id: COMMAND_PARTDESIGN_EDIT_POCKET,
            label: "Edit Pocket",
            group: "PartDesign",
            shortcut: None,
            requires_selection: true,
            description: "Open the selected pocket feature for parameter editing.",
            action_label: Some("Apply Pocket"),
        }),
        COMMAND_HISTORY_ROLLBACK_HERE => Some(CommandSpec {
            command_id: COMMAND_HISTORY_ROLLBACK_HERE,
            label: "Rollback Here",
            group: "History",
            shortcut: None,
            requires_selection: true,
            description: "Rebuild the model using history only up to the selected feature.",
            action_label: Some("Roll Here"),
        }),
        COMMAND_HISTORY_RESUME_FULL => Some(CommandSpec {
            command_id: COMMAND_HISTORY_RESUME_FULL,
            label: "Resume Full History",
            group: "History",
            shortcut: None,
            requires_selection: false,
            description: "Restore every feature after a rollback marker and rebuild the full result.",
            action_label: Some("Resume Full"),
        }),
        COMMAND_MODEL_TOGGLE_SUPPRESSION => Some(CommandSpec {
            command_id: COMMAND_MODEL_TOGGLE_SUPPRESSION,
            label: "Toggle Suppression",
            group: "Model",
            shortcut: None,
            requires_selection: true,
            description: "Suppress or unsuppress the selected feature or sketch in the model history.",
            action_label: Some("Toggle"),
        }),
        COMMAND_DOCUMENT_UNDO => Some(CommandSpec {
            command_id: COMMAND_DOCUMENT_UNDO,
            label: "Undo",
            group: "Document",
            shortcut: Some("Ctrl+Z"),
            requires_selection: false,
            description: "Undo the last modeling operation.",
            action_label: Some("Undo"),
        }),
        COMMAND_DOCUMENT_REDO => Some(CommandSpec {
            command_id: COMMAND_DOCUMENT_REDO,
            label: "Redo",
            group: "Document",
            shortcut: Some("Ctrl+Y"),
            requires_selection: false,
            description: "Redo the last undone modeling operation.",
            action_label: Some("Redo"),
        }),
        _ => None,
    }
}

pub fn job_title_from_command_id(command_id: &str) -> String {
    command_spec(command_id)
        .map(|spec| spec.label.to_string())
        .unwrap_or_else(|| {
            command_id
                .split('.')
                .next_back()
                .map(|segment| segment.replace('_', " "))
                .unwrap_or_else(|| command_id.to_string())
        })
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PlannedJobStage {
    pub stage_id: String,
    pub label: String,
    pub state: String,
    pub progress_percent: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PlannedCommandEvent {
    pub topic: String,
    pub level: String,
    pub message: String,
}

pub fn plan_job_stages(
    command_id: &str,
    accepted: bool,
    viewport_changed: bool,
) -> Vec<PlannedJobStage> {
    let behavior = command_behavior(command_id);
    let final_state = if accepted { "completed" } else { "failed" };
    let final_progress = if accepted { 100 } else { 0 };
    let mut stages = vec![PlannedJobStage {
        stage_id: "queued".into(),
        label: "Queued by shell".into(),
        state: final_state.into(),
        progress_percent: if accepted { 15 } else { 0 },
    }];

    match behavior.job_kind {
        CommandJobKind::BridgeRecompute => stages.push(PlannedJobStage {
            stage_id: "bridge_recompute".into(),
            label: "Bridge recompute pass".into(),
            state: final_state.into(),
            progress_percent: if accepted { 70 } else { 0 },
        }),
        CommandJobKind::PersistDocument => stages.push(PlannedJobStage {
            stage_id: "persist_document".into(),
            label: "Persist document state".into(),
            state: final_state.into(),
            progress_percent: if accepted { 75 } else { 0 },
        }),
        CommandJobKind::BridgeMutation => stages.push(PlannedJobStage {
            stage_id: "bridge_mutation".into(),
            label: "Apply bridge-backed mutation".into(),
            state: final_state.into(),
            progress_percent: if accepted { 68 } else { 0 },
        }),
        CommandJobKind::BackendDispatch => stages.push(PlannedJobStage {
            stage_id: "backend_dispatch".into(),
            label: "Backend dispatch".into(),
            state: final_state.into(),
            progress_percent: if accepted { 60 } else { 0 },
        }),
    }

    if viewport_changed {
        stages.push(PlannedJobStage {
            stage_id: "viewport_sync".into(),
            label: "Viewport sync".into(),
            state: final_state.into(),
            progress_percent: if accepted { 90 } else { 0 },
        });
    }

    stages.push(PlannedJobStage {
        stage_id: "completed".into(),
        label: if accepted {
            "Job completed".into()
        } else {
            "Job failed".into()
        },
        state: final_state.into(),
        progress_percent: final_progress,
    });
    stages
}

pub fn stage_event_topic(progress_percent: u32) -> &'static str {
    if progress_percent < 100 {
        "recompute_progress"
    } else {
        "task_status"
    }
}

pub fn outcome_event_plan(accepted: bool) -> (&'static str, &'static str) {
    if accepted {
        ("task_status", "info")
    } else {
        ("backend_warning", "warning")
    }
}

pub fn plan_command_events(
    command_id: &str,
    status_message: &str,
    accepted: bool,
    stages: &[PlannedJobStage],
    source: Option<&str>,
) -> Vec<PlannedCommandEvent> {
    let mut events = Vec::new();

    if accepted {
        for stage in stages {
            events.push(PlannedCommandEvent {
                topic: stage_event_topic(stage.progress_percent).into(),
                level: "info".into(),
                message: format!("{}: {}", command_id, stage.label),
            });
        }
    }

    let (topic, level) = outcome_event_plan(accepted);
    let source_suffix = source
        .map(|value| format!(" via {}", value))
        .unwrap_or_default();
    events.push(PlannedCommandEvent {
        topic: topic.into(),
        level: level.into(),
        message: format!("{}{}", status_message, source_suffix),
    });

    events
}

pub fn viewport_invalidated_event() -> PlannedCommandEvent {
    PlannedCommandEvent {
        topic: "viewport_updated".into(),
        level: "info".into(),
        message: "Viewport scene invalidated for selected feature".into(),
    }
}

#[cfg(test)]
mod tests {
    use super::{
        command_behavior, command_spec, job_title_from_command_id, outcome_event_plan,
        plan_command_events, plan_job_stages, stage_event_topic, viewport_invalidated_event,
        CommandJobKind, CommandTransactionMode, COMMAND_DOCUMENT_REDO,
        COMMAND_DOCUMENT_RECOMPUTE, COMMAND_DOCUMENT_SAVE, COMMAND_HISTORY_ROLLBACK_HERE,
        COMMAND_SELECTION_FOCUS,
    };

    #[test]
    fn classifies_mutating_bridge_commands() {
        let behavior = command_behavior(COMMAND_HISTORY_ROLLBACK_HERE);

        assert_eq!(behavior.transaction_mode, CommandTransactionMode::Mutating);
        assert_eq!(behavior.job_kind, CommandJobKind::BridgeMutation);
        assert!(behavior.opens_undo_transaction());
    }

    #[test]
    fn classifies_document_recompute_and_save_separately() {
        let recompute = command_behavior(COMMAND_DOCUMENT_RECOMPUTE);
        let save = command_behavior(COMMAND_DOCUMENT_SAVE);

        assert_eq!(recompute.job_kind, CommandJobKind::BridgeRecompute);
        assert_eq!(save.job_kind, CommandJobKind::PersistDocument);
        assert!(recompute.opens_undo_transaction());
        assert!(!save.opens_undo_transaction());
    }

    #[test]
    fn treats_focus_and_undo_redo_as_non_mutating() {
        let focus = command_behavior(COMMAND_SELECTION_FOCUS);
        let redo = command_behavior(COMMAND_DOCUMENT_REDO);

        assert_eq!(focus.transaction_mode, CommandTransactionMode::ReadOnly);
        assert_eq!(redo.transaction_mode, CommandTransactionMode::UndoRedo);
        assert!(!focus.opens_undo_transaction());
        assert!(!redo.opens_undo_transaction());
    }

    #[test]
    fn exposes_shared_command_spec_metadata() {
        let spec = command_spec(COMMAND_DOCUMENT_SAVE).expect("save spec should exist");

        assert_eq!(spec.label, "Save");
        assert_eq!(spec.group, "Document");
        assert_eq!(spec.shortcut, Some("Ctrl+S"));
    }

    #[test]
    fn derives_job_title_from_registry_before_fallback() {
        assert_eq!(job_title_from_command_id(COMMAND_HISTORY_ROLLBACK_HERE), "Rollback Here");
        assert_eq!(job_title_from_command_id("custom.command_name"), "command name");
    }

    #[test]
    fn plans_bridge_mutation_job_stages() {
        let stages = plan_job_stages(COMMAND_HISTORY_ROLLBACK_HERE, true, true);

        assert_eq!(stages[0].stage_id, "queued");
        assert_eq!(stages[1].stage_id, "bridge_mutation");
        assert_eq!(stages[2].stage_id, "viewport_sync");
        assert_eq!(stages[3].stage_id, "completed");
        assert_eq!(stages[3].progress_percent, 100);
    }

    #[test]
    fn plans_failed_backend_dispatch_job_stages() {
        let stages = plan_job_stages(COMMAND_DOCUMENT_REDO, false, false);

        assert_eq!(stages[0].state, "failed");
        assert_eq!(stages[1].stage_id, "backend_dispatch");
        assert_eq!(stages[2].label, "Job failed");
        assert_eq!(stages[2].progress_percent, 0);
    }

    #[test]
    fn classifies_event_topics_from_progress_and_outcome() {
        assert_eq!(stage_event_topic(15), "recompute_progress");
        assert_eq!(stage_event_topic(100), "task_status");
        assert_eq!(outcome_event_plan(true), ("task_status", "info"));
        assert_eq!(outcome_event_plan(false), ("backend_warning", "warning"));
    }

    #[test]
    fn plans_command_events_with_stage_messages_and_source_suffix() {
        let stages = plan_job_stages(COMMAND_HISTORY_ROLLBACK_HERE, true, false);
        let events = plan_command_events(
            COMMAND_HISTORY_ROLLBACK_HERE,
            "Rolled back model evaluation",
            true,
            &stages,
            Some("toolbar"),
        );

        assert!(events[0].message.starts_with("history.rollback_here: Queued by shell"));
        assert_eq!(events.last().expect("outcome event").topic, "task_status");
        assert!(events.last().expect("outcome event").message.ends_with(" via toolbar"));
    }

    #[test]
    fn exposes_viewport_invalidated_event_template() {
        let event = viewport_invalidated_event();

        assert_eq!(event.topic, "viewport_updated");
        assert_eq!(event.level, "info");
    }
}