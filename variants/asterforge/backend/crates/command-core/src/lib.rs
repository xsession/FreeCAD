use std::collections::{BTreeMap, HashMap};

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
pub const COMMAND_STEP_SELECT_PARENT: &str = "step.select_parent";
pub const COMMAND_STEP_SELECT_FIRST_CHILD: &str = "step.select_first_child";
pub const COMMAND_STEP_INSPECT_PMI: &str = "step.inspect_pmi";
pub const COMMAND_STEP_HIDE_SELECTION: &str = "step.hide_selection";
pub const COMMAND_STEP_ISOLATE_SELECTION: &str = "step.isolate_selection";
pub const COMMAND_STEP_SHOW_ALL: &str = "step.show_all";
pub const COMMAND_STEP_MEASURE_SELECTION: &str = "step.measure_selection";
pub const COMMAND_STEP_VIEW_ISO: &str = "step.view_iso";
pub const COMMAND_STEP_VIEW_FIT_ALL: &str = "step.view_fit_all";
pub const COMMAND_STEP_VIEW_RESET: &str = "step.view_reset";
pub const COMMAND_STEP_VIEW_FRONT: &str = "step.view_front";
pub const COMMAND_STEP_VIEW_BACK: &str = "step.view_back";
pub const COMMAND_STEP_VIEW_RIGHT: &str = "step.view_right";
pub const COMMAND_STEP_VIEW_LEFT: &str = "step.view_left";
pub const COMMAND_STEP_VIEW_TOP: &str = "step.view_top";
pub const COMMAND_STEP_VIEW_BOTTOM: &str = "step.view_bottom";
pub const COMMAND_EXTENSIONS_REFRESH_INVENTORY: &str = "extensions.refresh_inventory";
pub const COMMAND_EXTENSIONS_REVIEW_ADDON_CATALOG: &str = "extensions.review_addon_catalog";
pub const COMMAND_EXTENSIONS_REVIEW_EXTERNAL_WORKBENCHES: &str = "extensions.review_external_workbenches";
pub const COMMAND_EXTENSIONS_RUN_INVENTORY_ENTRY: &str = "extensions.run_inventory_entry";

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct CommandSpec {
    pub command_id: &'static str,
    pub label: &'static str,
    pub group: &'static str,
    pub icon: Option<&'static str>,
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
    pub icon: Option<String>,
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

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BridgeCommandErrorCategory {
    ValidationError,
    NativeError,
    Timeout,
    Cancelled,
    WorkerCrashed,
    Unsupported,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BridgeCommandFailure {
    pub category: BridgeCommandErrorCategory,
    pub code: String,
    pub summary: String,
    pub detail: String,
    pub correlation_id: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BridgeCommandAdapterRequest {
    pub session_id: String,
    pub command_id: String,
    pub target_object_id: Option<String>,
    pub arguments: BTreeMap<String, String>,
    pub correlation_id: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BridgeCommandAdapterResponse {
    pub command_id: String,
    pub accepted: bool,
    pub status_message: String,
    pub document_dirty: bool,
}

#[derive(Debug, Clone)]
pub struct BridgeCommandExecutionOutcome<TSnapshot> {
    pub response: CommandExecutionResponse,
    pub updated_snapshot: Option<TSnapshot>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum HistoryCommandAction {
    Undo,
    Redo,
}

#[derive(Debug, Clone)]
pub struct HistoryCommandAdapterResponse<TSnapshot> {
    pub accepted: bool,
    pub status_message: String,
    pub restored_snapshot: Option<TSnapshot>,
}

pub trait HistoryCommandAdapter {
    type Snapshot;
    type Stack;

    fn execute_history_command(
        &self,
        correlation_id: &str,
        action: HistoryCommandAction,
        stack: &mut Self::Stack,
        current_snapshot: &Self::Snapshot,
    ) -> HistoryCommandAdapterResponse<Self::Snapshot>;
}

pub trait BridgeCommandAdapter {
    type Snapshot;

    fn execute_bridge_command(
        &self,
        correlation_id: &str,
        request: BridgeCommandAdapterRequest,
    ) -> Result<BridgeCommandAdapterResponse, BridgeCommandFailure>;

    fn load_bridge_session_snapshot(
        &self,
        correlation_id: &str,
        session_id: &str,
    ) -> Option<Self::Snapshot>;
}

pub fn execute_bridge_command<TSnapshot, TAdapter>(
    adapter: &TAdapter,
    correlation_id: &str,
    session_id: &str,
    fallback_selected_object_id: Option<&str>,
    request: &CommandExecutionRequest,
) -> BridgeCommandExecutionOutcome<TSnapshot>
where
    TAdapter: BridgeCommandAdapter<Snapshot = TSnapshot>,
{
    let target_object_id = request.target_object_id.clone().or_else(|| {
        fallback_selected_object_id
            .filter(|value| !value.is_empty())
            .map(|value| value.to_string())
    });
    let adapter_request = BridgeCommandAdapterRequest {
        session_id: session_id.to_string(),
        command_id: request.command_id.clone(),
        target_object_id,
        arguments: request
            .arguments
            .iter()
            .map(|(key, value)| (key.clone(), value.clone()))
            .collect::<BTreeMap<_, _>>(),
        correlation_id: Some(correlation_id.to_string()),
    };

    tracing::debug!(
        correlation_id,
        command_id = %adapter_request.command_id,
        session_id = %adapter_request.session_id,
        target_object_id = ?adapter_request.target_object_id,
        "executing bridge-backed command through command-core adapter"
    );

    match adapter.execute_bridge_command(correlation_id, adapter_request.clone()) {
        Ok(adapter_response) => {
            let updated_snapshot = adapter_response
                .accepted
                .then(|| adapter.load_bridge_session_snapshot(correlation_id, &adapter_request.session_id))
                .flatten();
            BridgeCommandExecutionOutcome {
                response: CommandExecutionResponse {
                    command_id: adapter_response.command_id,
                    accepted: adapter_response.accepted,
                    status_message: adapter_response.status_message,
                    document_dirty: adapter_response.document_dirty,
                },
                updated_snapshot,
            }
        }
        Err(error) => {
            let effective_correlation_id = error
                .correlation_id
                .as_deref()
                .unwrap_or(correlation_id);
            tracing::warn!(
                correlation_id = effective_correlation_id,
                command_id = %request.command_id,
                category = ?error.category,
                code = %error.code,
                "bridge command failed"
            );
            BridgeCommandExecutionOutcome {
                response: CommandExecutionResponse {
                    command_id: request.command_id.clone(),
                    accepted: false,
                    status_message: match error.category {
                        BridgeCommandErrorCategory::Unsupported => error.summary,
                        _ => error.detail,
                    },
                    document_dirty: false,
                },
                updated_snapshot: None,
            }
        }
    }
}

pub fn execute_history_command<TAdapter>(
    adapter: &TAdapter,
    correlation_id: &str,
    request: &CommandExecutionRequest,
    stack: &mut TAdapter::Stack,
    current_snapshot: &TAdapter::Snapshot,
) -> BridgeCommandExecutionOutcome<TAdapter::Snapshot>
where
    TAdapter: HistoryCommandAdapter,
{
    let action = match request.command_id.as_str() {
        COMMAND_DOCUMENT_UNDO => HistoryCommandAction::Undo,
        COMMAND_DOCUMENT_REDO => HistoryCommandAction::Redo,
        _ => {
            return BridgeCommandExecutionOutcome {
                response: CommandExecutionResponse {
                    command_id: request.command_id.clone(),
                    accepted: false,
                    status_message: "Unsupported history command".into(),
                    document_dirty: false,
                },
                updated_snapshot: None,
            }
        }
    };

    tracing::debug!(
        correlation_id,
        command_id = %request.command_id,
        action = ?action,
        "executing history command through command-core adapter"
    );

    let adapter_response = adapter.execute_history_command(
        correlation_id,
        action,
        stack,
        current_snapshot,
    );

    BridgeCommandExecutionOutcome {
        response: CommandExecutionResponse {
            command_id: request.command_id.clone(),
            accepted: adapter_response.accepted,
            status_message: adapter_response.status_message,
            document_dirty: false,
        },
        updated_snapshot: adapter_response.restored_snapshot,
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExtensionInventorySeedEntry {
    pub entry_id: String,
    pub label: String,
    pub origin: String,
    pub trust_state: String,
    pub compatibility: String,
    pub detail: String,
    pub action_command_id: Option<String>,
    pub action_label: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExtensionLanePlan {
    pub lane_id: String,
    pub status: String,
    pub summary: String,
    pub next_steps: Vec<String>,
    pub command_ids: Vec<String>,
    pub inventory_entries: Vec<ExtensionInventorySeedEntry>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExtensionExecutionPolicyResult {
    pub accepted: bool,
    pub status_message: String,
    pub event_level: String,
    pub event_message: String,
    pub last_run_kind: Option<String>,
    pub last_run_level: Option<String>,
    pub last_run_status: Option<String>,
    pub last_run_detail: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CommandContext {
    pub document_id: String,
    pub selected_object_id: Option<String>,
    pub selectable_object_ids: Vec<String>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CommandValidationErrorKind {
    UnknownCommand,
    DocumentMismatch,
    MissingSelection,
    InvalidTarget,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CommandValidationError {
    pub kind: CommandValidationErrorKind,
    pub command_id: String,
    pub message: String,
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
pub enum CommandDispatchRoute {
    Step,
    BridgeVerticalSlice,
    UndoRedo,
    Extension,
    Unknown,
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
        COMMAND_STEP_SELECT_PARENT
        | COMMAND_STEP_SELECT_FIRST_CHILD
        | COMMAND_STEP_INSPECT_PMI
        | COMMAND_STEP_HIDE_SELECTION
        | COMMAND_STEP_ISOLATE_SELECTION
        | COMMAND_STEP_SHOW_ALL
        | COMMAND_STEP_MEASURE_SELECTION
        | COMMAND_STEP_VIEW_ISO
        | COMMAND_STEP_VIEW_FIT_ALL
        | COMMAND_STEP_VIEW_RESET
        | COMMAND_STEP_VIEW_FRONT
        | COMMAND_STEP_VIEW_BACK
        | COMMAND_STEP_VIEW_RIGHT
        | COMMAND_STEP_VIEW_LEFT
        | COMMAND_STEP_VIEW_TOP
        | COMMAND_STEP_VIEW_BOTTOM
        | COMMAND_EXTENSIONS_REFRESH_INVENTORY
        | COMMAND_EXTENSIONS_REVIEW_ADDON_CATALOG
        | COMMAND_EXTENSIONS_REVIEW_EXTERNAL_WORKBENCHES
        | COMMAND_EXTENSIONS_RUN_INVENTORY_ENTRY => {
            CommandBehavior {
                transaction_mode: CommandTransactionMode::ReadOnly,
                job_kind: CommandJobKind::BackendDispatch,
            }
        }
        _ => CommandBehavior {
            transaction_mode: CommandTransactionMode::ReadOnly,
            job_kind: CommandJobKind::BackendDispatch,
        },
    }
}

pub fn command_dispatch_route(command_id: &str, step_context_active: bool) -> CommandDispatchRoute {
    match command_id {
        COMMAND_SELECTION_FOCUS if step_context_active => CommandDispatchRoute::Step,
        COMMAND_STEP_SELECT_PARENT
        | COMMAND_STEP_SELECT_FIRST_CHILD
        | COMMAND_STEP_INSPECT_PMI
        | COMMAND_STEP_HIDE_SELECTION
        | COMMAND_STEP_ISOLATE_SELECTION
        | COMMAND_STEP_SHOW_ALL
        | COMMAND_STEP_MEASURE_SELECTION
        | COMMAND_STEP_VIEW_ISO
        | COMMAND_STEP_VIEW_FIT_ALL
        | COMMAND_STEP_VIEW_RESET
        | COMMAND_STEP_VIEW_FRONT
        | COMMAND_STEP_VIEW_BACK
        | COMMAND_STEP_VIEW_RIGHT
        | COMMAND_STEP_VIEW_LEFT
        | COMMAND_STEP_VIEW_TOP
        | COMMAND_STEP_VIEW_BOTTOM => CommandDispatchRoute::Step,
        COMMAND_DOCUMENT_RECOMPUTE
        | COMMAND_DOCUMENT_SAVE
        | COMMAND_SELECTION_FOCUS
        | COMMAND_PARTDESIGN_NEW_SKETCH
        | COMMAND_PARTDESIGN_PAD
        | COMMAND_PARTDESIGN_POCKET
        | COMMAND_PARTDESIGN_EDIT_PAD
        | COMMAND_PARTDESIGN_EDIT_POCKET
        | COMMAND_HISTORY_ROLLBACK_HERE
        | COMMAND_HISTORY_RESUME_FULL
        | COMMAND_MODEL_TOGGLE_SUPPRESSION => CommandDispatchRoute::BridgeVerticalSlice,
        COMMAND_DOCUMENT_UNDO | COMMAND_DOCUMENT_REDO => CommandDispatchRoute::UndoRedo,
        COMMAND_EXTENSIONS_REFRESH_INVENTORY
        | COMMAND_EXTENSIONS_REVIEW_ADDON_CATALOG
        | COMMAND_EXTENSIONS_REVIEW_EXTERNAL_WORKBENCHES
        | COMMAND_EXTENSIONS_RUN_INVENTORY_ENTRY => CommandDispatchRoute::Extension,
        _ => CommandDispatchRoute::Unknown,
    }
}

pub fn extension_refresh_lane_plans() -> Vec<ExtensionLanePlan> {
    vec![
        ExtensionLanePlan {
            lane_id: "macros".into(),
            status: "inventory-ready".into(),
            summary: "Macro inventory is now staged in backend-owned compatibility state so trust review and execution boundaries can be layered in without reviving Qt dialogs.".into(),
            next_steps: vec![
                "Review discovered macros and assign trust boundaries.".into(),
                "Replace the reviewed fixture launch with discovered user-macro inventory and persisted approval state.".into(),
            ],
            command_ids: vec![COMMAND_EXTENSIONS_REFRESH_INVENTORY.into()],
            inventory_entries: vec![
                ExtensionInventorySeedEntry {
                    entry_id: "macro:auto_dimensioning".into(),
                    label: "AutoDimensioning.FCMacro".into(),
                    origin: "Reviewed fixture bundle".into(),
                    trust_state: "reviewed".into(),
                    compatibility: "shell-ready".into(),
                    detail: "Launches through the repo FreeCAD console wrapper against a reviewed headless-safe macro fixture so backend execution, logging, and trust boundaries are exercised end to end.".into(),
                    action_command_id: Some(COMMAND_EXTENSIONS_RUN_INVENTORY_ENTRY.into()),
                    action_label: Some("Run Reviewed Macro".into()),
                },
                ExtensionInventorySeedEntry {
                    entry_id: "macro:broken_reviewed".into(),
                    label: "BrokenReviewedFixture.FCMacro".into(),
                    origin: "Reviewed failure fixture".into(),
                    trust_state: "reviewed".into(),
                    compatibility: "shell-ready".into(),
                    detail: "Exercises launcher failure handling so the Extensions dock can surface readable execution errors without relying on Qt-era dialogs.".into(),
                    action_command_id: Some(COMMAND_EXTENSIONS_RUN_INVENTORY_ENTRY.into()),
                    action_label: Some("Run Broken Reviewed Macro".into()),
                },
                ExtensionInventorySeedEntry {
                    entry_id: "macro:legacy_sheetmetal".into(),
                    label: "LegacySheetMetalTools.FCMacro".into(),
                    origin: "Migrated macro bundle".into(),
                    trust_state: "needs-review".into(),
                    compatibility: "qt-bound".into(),
                    detail: "Still assumes Qt dialogs for parameter entry and needs a shell-safe fallback before execution is enabled.".into(),
                    action_command_id: None,
                    action_label: None,
                },
            ],
        },
        ExtensionLanePlan {
            lane_id: "addon-manager".into(),
            status: "inventory-ready".into(),
            summary: "Addon provenance and compatibility inventory is now staged in backend state so install and update flows can be wired without reopening Qt-owned UI assumptions.".into(),
            next_steps: vec![
                "Review backend-owned addon provenance, blockers, and shell-safe migration candidates.".into(),
                "Promote reviewed install, update, and disable flows into explicit backend commands.".into(),
            ],
            command_ids: vec![COMMAND_EXTENSIONS_REVIEW_ADDON_CATALOG.into()],
            inventory_entries: vec![ExtensionInventorySeedEntry {
                entry_id: "addon:ifc_tools".into(),
                label: "IFC Coordination Tools".into(),
                origin: "Addon registry".into(),
                trust_state: "registry-signed".into(),
                compatibility: "reviewing".into(),
                detail: "Metadata and provenance are available, but the task surfaces still assume PySide widgets.".into(),
                action_command_id: None,
                action_label: None,
            }],
        },
    ]
}

pub fn extension_addon_catalog_review_plan() -> ExtensionLanePlan {
    ExtensionLanePlan {
        lane_id: "addon-manager".into(),
        status: "reviewing".into(),
        summary: "AddonManager compatibility review is active so provenance, install blockers, and shell-safe migration candidates can be audited through backend-owned inventory instead of Qt-only dialogs.".into(),
        next_steps: vec![
            "Promote reviewed addon install and update flows into explicit backend commands.".into(),
            "Replace PySide-only preference and task widgets with protocol-driven shell surfaces.".into(),
        ],
        command_ids: vec![COMMAND_EXTENSIONS_REVIEW_ADDON_CATALOG.into()],
        inventory_entries: vec![
            ExtensionInventorySeedEntry {
                entry_id: "addon:ifc_tools".into(),
                label: "IFC Coordination Tools".into(),
                origin: "Addon registry".into(),
                trust_state: "registry-signed".into(),
                compatibility: "reviewing".into(),
                detail: "Manifest, provenance, and dependency metadata are now available in backend state, but task editing still depends on PySide widgets and Qt-bound install surfaces.".into(),
                action_command_id: None,
                action_label: None,
            },
            ExtensionInventorySeedEntry {
                entry_id: "addon:sheetmetal_plus".into(),
                label: "SheetMetal Plus".into(),
                origin: "Community addon feed".into(),
                trust_state: "needs-review".into(),
                compatibility: "qt-bound".into(),
                detail: "Install metadata is discoverable, but command onboarding and parameter dialogs still assume Qt task panels and modal prompts.".into(),
                action_command_id: None,
                action_label: None,
            },
            ExtensionInventorySeedEntry {
                entry_id: "addon:render_studio".into(),
                label: "Render Studio".into(),
                origin: "Reviewed internal catalog".into(),
                trust_state: "reviewed".into(),
                compatibility: "shell-candidate".into(),
                detail: "Manifest registration, icon metadata, and command grouping are portable, but preferences and post-install setup still need backend-owned replacement flows.".into(),
                action_command_id: None,
                action_label: None,
            },
        ],
    }
}

pub fn extension_external_workbench_review_plan() -> ExtensionLanePlan {
    ExtensionLanePlan {
        lane_id: "external-workbenches".into(),
        status: "reviewing".into(),
        summary: "External workbench registration is under active compatibility review so command registration, onboarding, and Qt-bound UI fallbacks can move into explicit shell-safe contracts.".into(),
        next_steps: vec![],
        command_ids: vec![COMMAND_EXTENSIONS_REVIEW_EXTERNAL_WORKBENCHES.into()],
        inventory_entries: vec![ExtensionInventorySeedEntry {
            entry_id: "workbench:robotics_plus".into(),
            label: "RoboticsPlusWorkbench".into(),
            origin: "External workbench manifest".into(),
            trust_state: "manifest-verified".into(),
            compatibility: "reviewing".into(),
            detail: "Command registration is portable, but task panels still require a shell-safe replacement for Qt docking widgets.".into(),
            action_command_id: None,
            action_label: None,
        }],
    }
}

pub fn evaluate_extension_inventory_execution_policy(
    label: &str,
    trust_state: &str,
    compatibility: &str,
) -> Option<ExtensionExecutionPolicyResult> {
    if trust_state == "reviewed" && compatibility == "shell-ready" {
        return None;
    }

    Some(ExtensionExecutionPolicyResult {
        accepted: false,
        status_message: format!("{} is not approved for backend execution yet", label),
        event_level: "warning".into(),
        event_message: format!(
            "Rejected backend execution for {} because the entry is not reviewed and shell-ready yet",
            label
        ),
        last_run_kind: Some("policy-rejected".into()),
        last_run_level: Some("warning".into()),
        last_run_status: Some("Blocked by trust policy".into()),
        last_run_detail: Some(
            "Reviewed backend execution only runs shell-ready entries that have passed explicit trust review.".into(),
        ),
    })
}

pub fn extension_execution_failure_status_message(label: &str) -> String {
    format!("Failed to execute reviewed inventory entry {}", label)
}

pub fn extension_execution_success_status_message(label: &str) -> String {
    format!("Executed reviewed inventory entry {}", label)
}

pub fn extension_execution_success_event_message(
    label: &str,
    origin: &str,
    status_summary: &str,
    output_excerpt: &str,
) -> String {
    format!(
        "Executed reviewed inventory entry {} from {} ({}). Output: {}",
        label, origin, status_summary, output_excerpt
    )
}

pub fn extension_execution_failure_event_message(label: &str, detail: &str) -> String {
    format!("Failed to execute reviewed inventory entry {}: {}", label, detail)
}

pub fn command_spec(command_id: &str) -> Option<CommandSpec> {
    match command_id {
        COMMAND_DOCUMENT_RECOMPUTE => Some(CommandSpec {
            command_id: COMMAND_DOCUMENT_RECOMPUTE,
            label: "Recompute",
            group: "Document",
            icon: Some("recompute"),
            shortcut: Some("Ctrl+R"),
            requires_selection: false,
            description: "Rebuild the dependency graph and refresh the active model.",
            action_label: Some("Recompute"),
        }),
        COMMAND_DOCUMENT_SAVE => Some(CommandSpec {
            command_id: COMMAND_DOCUMENT_SAVE,
            label: "Save",
            group: "Document",
            icon: Some("save"),
            shortcut: Some("Ctrl+S"),
            requires_selection: false,
            description: "Persist the current document state through the backend pipeline.",
            action_label: Some("Save"),
        }),
        COMMAND_SELECTION_FOCUS => Some(CommandSpec {
            command_id: COMMAND_SELECTION_FOCUS,
            label: "Focus Selection",
            group: "View",
            icon: Some("focus"),
            shortcut: Some("F"),
            requires_selection: true,
            description: "Center the viewport workflow around the currently selected object.",
            action_label: Some("Focus"),
        }),
        COMMAND_PARTDESIGN_NEW_SKETCH => Some(CommandSpec {
            command_id: COMMAND_PARTDESIGN_NEW_SKETCH,
            label: "Create Sketch",
            group: "PartDesign",
            icon: Some("sketch"),
            shortcut: None,
            requires_selection: true,
            description: "Create a new sketch inside the selected body.",
            action_label: Some("Create Sketch"),
        }),
        COMMAND_PARTDESIGN_PAD => Some(CommandSpec {
            command_id: COMMAND_PARTDESIGN_PAD,
            label: "Create Pad",
            group: "PartDesign",
            icon: Some("pad"),
            shortcut: None,
            requires_selection: true,
            description: "Extrude the active sketch into a solid PartDesign feature.",
            action_label: Some("Create Pad"),
        }),
        COMMAND_PARTDESIGN_POCKET => Some(CommandSpec {
            command_id: COMMAND_PARTDESIGN_POCKET,
            label: "Create Pocket",
            group: "PartDesign",
            icon: Some("pocket"),
            shortcut: None,
            requires_selection: true,
            description: "Cut material from the active sketch profile into the body.",
            action_label: Some("Create Pocket"),
        }),
        COMMAND_PARTDESIGN_EDIT_PAD => Some(CommandSpec {
            command_id: COMMAND_PARTDESIGN_EDIT_PAD,
            label: "Edit Pad",
            group: "PartDesign",
            icon: Some("pad"),
            shortcut: None,
            requires_selection: true,
            description: "Open the selected pad feature for parameter editing.",
            action_label: Some("Apply Pad"),
        }),
        COMMAND_PARTDESIGN_EDIT_POCKET => Some(CommandSpec {
            command_id: COMMAND_PARTDESIGN_EDIT_POCKET,
            label: "Edit Pocket",
            group: "PartDesign",
            icon: Some("pocket"),
            shortcut: None,
            requires_selection: true,
            description: "Open the selected pocket feature for parameter editing.",
            action_label: Some("Apply Pocket"),
        }),
        COMMAND_HISTORY_ROLLBACK_HERE => Some(CommandSpec {
            command_id: COMMAND_HISTORY_ROLLBACK_HERE,
            label: "Rollback Here",
            group: "History",
            icon: Some("history"),
            shortcut: None,
            requires_selection: true,
            description: "Rebuild the model using history only up to the selected feature.",
            action_label: Some("Roll Here"),
        }),
        COMMAND_HISTORY_RESUME_FULL => Some(CommandSpec {
            command_id: COMMAND_HISTORY_RESUME_FULL,
            label: "Resume Full History",
            group: "History",
            icon: Some("history"),
            shortcut: None,
            requires_selection: false,
            description: "Restore every feature after a rollback marker and rebuild the full result.",
            action_label: Some("Resume Full"),
        }),
        COMMAND_MODEL_TOGGLE_SUPPRESSION => Some(CommandSpec {
            command_id: COMMAND_MODEL_TOGGLE_SUPPRESSION,
            label: "Toggle Suppression",
            group: "Model",
            icon: Some("suppression"),
            shortcut: None,
            requires_selection: true,
            description: "Suppress or unsuppress the selected feature or sketch in the model history.",
            action_label: Some("Toggle"),
        }),
        COMMAND_DOCUMENT_UNDO => Some(CommandSpec {
            command_id: COMMAND_DOCUMENT_UNDO,
            label: "Undo",
            group: "Document",
            icon: Some("undo"),
            shortcut: Some("Ctrl+Z"),
            requires_selection: false,
            description: "Undo the last modeling operation.",
            action_label: Some("Undo"),
        }),
        COMMAND_DOCUMENT_REDO => Some(CommandSpec {
            command_id: COMMAND_DOCUMENT_REDO,
            label: "Redo",
            group: "Document",
            icon: Some("redo"),
            shortcut: Some("Ctrl+Y"),
            requires_selection: false,
            description: "Redo the last undone modeling operation.",
            action_label: Some("Redo"),
        }),
        COMMAND_STEP_SELECT_PARENT => Some(CommandSpec {
            command_id: COMMAND_STEP_SELECT_PARENT,
            label: "Select Parent",
            group: "STEP",
            icon: Some("history"),
            shortcut: None,
            requires_selection: true,
            description: "Move selection to the parent STEP assembly node when one exists.",
            action_label: Some("Select Parent"),
        }),
        COMMAND_STEP_SELECT_FIRST_CHILD => Some(CommandSpec {
            command_id: COMMAND_STEP_SELECT_FIRST_CHILD,
            label: "Select Child",
            group: "STEP",
            icon: Some("focus"),
            shortcut: None,
            requires_selection: true,
            description: "Move selection to the first child node below the current STEP assembly node.",
            action_label: Some("Select Child"),
        }),
        COMMAND_STEP_INSPECT_PMI => Some(CommandSpec {
            command_id: COMMAND_STEP_INSPECT_PMI,
            label: "Inspect PMI",
            group: "STEP",
            icon: Some("focus"),
            shortcut: None,
            requires_selection: true,
            description: "Open the report dock for semantic PMI attached to the selected STEP entity.",
            action_label: Some("Inspect PMI"),
        }),
        COMMAND_STEP_HIDE_SELECTION => Some(CommandSpec {
            command_id: COMMAND_STEP_HIDE_SELECTION,
            label: "Hide Selection",
            group: "STEP",
            icon: Some("hide"),
            shortcut: None,
            requires_selection: true,
            description: "Hide the selected STEP node from the inspection viewport.",
            action_label: Some("Hide"),
        }),
        COMMAND_STEP_ISOLATE_SELECTION => Some(CommandSpec {
            command_id: COMMAND_STEP_ISOLATE_SELECTION,
            label: "Isolate Selection",
            group: "STEP",
            icon: Some("isolate"),
            shortcut: None,
            requires_selection: true,
            description: "Hide every other STEP node so the current selection is isolated.",
            action_label: Some("Isolate"),
        }),
        COMMAND_STEP_SHOW_ALL => Some(CommandSpec {
            command_id: COMMAND_STEP_SHOW_ALL,
            label: "Show All",
            group: "STEP",
            icon: Some("show"),
            shortcut: None,
            requires_selection: false,
            description: "Restore every hidden STEP node to the inspection viewport.",
            action_label: Some("Show All"),
        }),
        COMMAND_STEP_MEASURE_SELECTION => Some(CommandSpec {
            command_id: COMMAND_STEP_MEASURE_SELECTION,
            label: "Measure Selection",
            group: "STEP",
            icon: Some("measure"),
            shortcut: None,
            requires_selection: true,
            description: "Compute the extents of the selected STEP subtree from its tessellated payload.",
            action_label: Some("Measure"),
        }),
        COMMAND_STEP_VIEW_ISO => Some(CommandSpec {
            command_id: COMMAND_STEP_VIEW_ISO,
            label: "Isometric View",
            group: "View",
            icon: Some("focus"),
            shortcut: None,
            requires_selection: false,
            description: "Orient the STEP camera to the standard isometric inspection view.",
            action_label: Some("Iso"),
        }),
        COMMAND_STEP_VIEW_FIT_ALL => Some(CommandSpec {
            command_id: COMMAND_STEP_VIEW_FIT_ALL,
            label: "Fit All",
            group: "View",
            icon: Some("focus"),
            shortcut: None,
            requires_selection: false,
            description: "Frame all visible STEP geometry in the inspection viewport.",
            action_label: Some("Fit"),
        }),
        COMMAND_STEP_VIEW_RESET => Some(CommandSpec {
            command_id: COMMAND_STEP_VIEW_RESET,
            label: "Reset View",
            group: "View",
            icon: Some("focus"),
            shortcut: None,
            requires_selection: false,
            description: "Restore the STEP camera to the default inspection view.",
            action_label: Some("Live"),
        }),
        COMMAND_STEP_VIEW_FRONT => Some(CommandSpec {
            command_id: COMMAND_STEP_VIEW_FRONT,
            label: "Front View",
            group: "View",
            icon: Some("focus"),
            shortcut: None,
            requires_selection: false,
            description: "Orient the STEP camera to the front inspection view.",
            action_label: Some("Front"),
        }),
        COMMAND_STEP_VIEW_BACK => Some(CommandSpec {
            command_id: COMMAND_STEP_VIEW_BACK,
            label: "Back View",
            group: "View",
            icon: Some("focus"),
            shortcut: None,
            requires_selection: false,
            description: "Orient the STEP camera to the back inspection view.",
            action_label: Some("Back"),
        }),
        COMMAND_STEP_VIEW_RIGHT => Some(CommandSpec {
            command_id: COMMAND_STEP_VIEW_RIGHT,
            label: "Right View",
            group: "View",
            icon: Some("focus"),
            shortcut: None,
            requires_selection: false,
            description: "Orient the STEP camera to the right inspection view.",
            action_label: Some("Right"),
        }),
        COMMAND_STEP_VIEW_LEFT => Some(CommandSpec {
            command_id: COMMAND_STEP_VIEW_LEFT,
            label: "Left View",
            group: "View",
            icon: Some("focus"),
            shortcut: None,
            requires_selection: false,
            description: "Orient the STEP camera to the left inspection view.",
            action_label: Some("Left"),
        }),
        COMMAND_STEP_VIEW_TOP => Some(CommandSpec {
            command_id: COMMAND_STEP_VIEW_TOP,
            label: "Top View",
            group: "View",
            icon: Some("focus"),
            shortcut: None,
            requires_selection: false,
            description: "Orient the STEP camera to the top inspection view.",
            action_label: Some("Top"),
        }),
        COMMAND_STEP_VIEW_BOTTOM => Some(CommandSpec {
            command_id: COMMAND_STEP_VIEW_BOTTOM,
            label: "Bottom View",
            group: "View",
            icon: Some("focus"),
            shortcut: None,
            requires_selection: false,
            description: "Orient the STEP camera to the bottom inspection view.",
            action_label: Some("Bottom"),
        }),
        COMMAND_EXTENSIONS_REFRESH_INVENTORY => Some(CommandSpec {
            command_id: COMMAND_EXTENSIONS_REFRESH_INVENTORY,
            label: "Refresh Extension Inventory",
            group: "Extensions",
            icon: Some("recompute"),
            shortcut: None,
            requires_selection: false,
            description: "Refresh backend-owned macro, addon, and external workbench compatibility inventory.",
            action_label: Some("Refresh Inventory"),
        }),
        COMMAND_EXTENSIONS_REVIEW_ADDON_CATALOG => Some(CommandSpec {
            command_id: COMMAND_EXTENSIONS_REVIEW_ADDON_CATALOG,
            label: "Review Addon Catalog",
            group: "Extensions",
            icon: Some("list"),
            shortcut: None,
            requires_selection: false,
            description: "Inspect addon provenance, compatibility blockers, and shell-safe migration candidates in the backend-owned Extensions lane.",
            action_label: Some("Review Addons"),
        }),
        COMMAND_EXTENSIONS_REVIEW_EXTERNAL_WORKBENCHES => Some(CommandSpec {
            command_id: COMMAND_EXTENSIONS_REVIEW_EXTERNAL_WORKBENCHES,
            label: "Review External Workbenches",
            group: "Extensions",
            icon: Some("focus"),
            shortcut: None,
            requires_selection: false,
            description: "Inspect the compatibility lane for external workbench registration and Qt-bound UI fallbacks.",
            action_label: Some("Review Workbenches"),
        }),
        COMMAND_EXTENSIONS_RUN_INVENTORY_ENTRY => Some(CommandSpec {
            command_id: COMMAND_EXTENSIONS_RUN_INVENTORY_ENTRY,
            label: "Run Reviewed Inventory Entry",
            group: "Extensions",
            icon: Some("play"),
            shortcut: None,
            requires_selection: false,
            description: "Execute a reviewed extension inventory entry through backend-owned trust gates.",
            action_label: Some("Run Reviewed Entry"),
        }),
        _ => None,
    }
}

pub fn command_definition(
    command_id: &str,
    enabled: bool,
    arguments: Vec<CommandArgumentDefinition>,
) -> Option<CommandDefinition> {
    let spec = command_spec(command_id)?;

    Some(CommandDefinition {
        command_id: spec.command_id.into(),
        label: spec.label.into(),
        group: spec.group.into(),
        icon: spec.icon.map(str::to_string),
        shortcut: spec.shortcut.map(str::to_string),
        enabled,
        requires_selection: spec.requires_selection,
        description: spec.description.into(),
        action_label: spec.action_label.map(str::to_string),
        arguments,
    })
}

pub fn validate_command_request(
    request: &CommandExecutionRequest,
    context: &CommandContext,
) -> Result<CommandBehavior, CommandValidationError> {
    tracing::debug!(
        command_id = %request.command_id,
        document_id = %request.document_id,
        target_object_id = ?request.target_object_id,
        "validating command request in command-core"
    );
    let Some(spec) = command_spec(&request.command_id) else {
        tracing::warn!(command_id = %request.command_id, "unknown command rejected during validation");
        return Err(CommandValidationError {
            kind: CommandValidationErrorKind::UnknownCommand,
            command_id: request.command_id.clone(),
            message: format!("Unknown command: {}", request.command_id),
        });
    };

    if request.document_id != context.document_id {
        tracing::warn!(command_id = %request.command_id, request_document_id = %request.document_id, active_document_id = %context.document_id, "command rejected due to document mismatch");
        return Err(CommandValidationError {
            kind: CommandValidationErrorKind::DocumentMismatch,
            command_id: request.command_id.clone(),
            message: format!(
                "Command targets document '{}' but active document is '{}'",
                request.document_id, context.document_id
            ),
        });
    }

    let requested_target = request
        .target_object_id
        .as_deref()
        .map(str::trim)
        .filter(|value| !value.is_empty());
    let selected_target = context
        .selected_object_id
        .as_deref()
        .map(str::trim)
        .filter(|value| !value.is_empty());
    let effective_target = requested_target.or(selected_target);

    if spec.requires_selection && effective_target.is_none() {
        tracing::warn!(command_id = %request.command_id, "command rejected due to missing selection");
        return Err(CommandValidationError {
            kind: CommandValidationErrorKind::MissingSelection,
            command_id: request.command_id.clone(),
            message: format!("Command '{}' requires an active selection", request.command_id),
        });
    }

    if let Some(target_object_id) = requested_target {
        if !context.selectable_object_ids.is_empty()
            && !context
                .selectable_object_ids
                .iter()
                .any(|candidate| candidate == target_object_id)
        {
            tracing::warn!(command_id = %request.command_id, target_object_id, "command rejected due to invalid target");
            return Err(CommandValidationError {
                kind: CommandValidationErrorKind::InvalidTarget,
                command_id: request.command_id.clone(),
                message: format!(
                    "Target object '{}' is not selectable in the active command context",
                    target_object_id
                ),
            });
        }
    }

    let behavior = command_behavior(&request.command_id);
    tracing::debug!(command_id = %request.command_id, ?behavior, "command validation accepted");
    Ok(behavior)
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

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PlannedCommandRuntime {
    pub job_title: String,
    pub job_state: String,
    pub job_progress_percent: u32,
    pub job_stages: Vec<PlannedJobStage>,
    pub events: Vec<PlannedCommandEvent>,
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

pub fn plan_command_runtime(
    command_id: &str,
    status_message: &str,
    accepted: bool,
    viewport_changed: bool,
    source: Option<&str>,
) -> PlannedCommandRuntime {
    tracing::debug!(command_id, accepted, viewport_changed, source = ?source, "planning command runtime in command-core");
    let job_stages = plan_job_stages(command_id, accepted, viewport_changed);
    let events = plan_command_events(command_id, status_message, accepted, &job_stages, source);

    PlannedCommandRuntime {
        job_title: job_title_from_command_id(command_id),
        job_state: if accepted {
            "completed".into()
        } else {
            "failed".into()
        },
        job_progress_percent: if accepted { 100 } else { 0 },
        job_stages,
        events,
    }
}

#[cfg(test)]
mod tests {
    use super::{
        execute_bridge_command, execute_history_command, BridgeCommandAdapter,
        BridgeCommandAdapterRequest, BridgeCommandAdapterResponse, BridgeCommandErrorCategory,
        BridgeCommandFailure, HistoryCommandAction, HistoryCommandAdapter,
        HistoryCommandAdapterResponse,
        command_behavior, command_definition, command_dispatch_route, command_spec, job_title_from_command_id,
        evaluate_extension_inventory_execution_policy, extension_execution_failure_event_message,
        extension_execution_failure_status_message, extension_execution_success_event_message,
        extension_execution_success_status_message, extension_external_workbench_review_plan,
        extension_refresh_lane_plans,
        outcome_event_plan, plan_command_events, plan_command_runtime, plan_job_stages,
        stage_event_topic, validate_command_request, viewport_invalidated_event, CommandContext,
        CommandDispatchRoute, CommandJobKind, CommandTransactionMode, CommandValidationErrorKind,
        COMMAND_DOCUMENT_REDO, COMMAND_DOCUMENT_RECOMPUTE, COMMAND_DOCUMENT_SAVE,
        COMMAND_DOCUMENT_UNDO,
        COMMAND_EXTENSIONS_REFRESH_INVENTORY, COMMAND_EXTENSIONS_REVIEW_ADDON_CATALOG,
        COMMAND_HISTORY_ROLLBACK_HERE,
        COMMAND_SELECTION_FOCUS, COMMAND_STEP_VIEW_ISO,
        extension_addon_catalog_review_plan,
    };
    use std::collections::{BTreeMap, HashMap};

    #[derive(Default)]
    struct RecordingBridgeAdapter {
        execute_response: Option<Result<BridgeCommandAdapterResponse, BridgeCommandFailure>>,
        loaded_snapshot: Option<&'static str>,
        recorded_request: Option<BridgeCommandAdapterRequest>,
        load_calls: Vec<(String, String)>,
    }

    impl BridgeCommandAdapter for std::cell::RefCell<RecordingBridgeAdapter> {
        type Snapshot = &'static str;

        fn execute_bridge_command(
            &self,
            _correlation_id: &str,
            request: BridgeCommandAdapterRequest,
        ) -> Result<BridgeCommandAdapterResponse, BridgeCommandFailure> {
            let mut adapter = self.borrow_mut();
            adapter.recorded_request = Some(request);
            adapter
                .execute_response
                .clone()
                .expect("execute response should be configured")
        }

        fn load_bridge_session_snapshot(
            &self,
            correlation_id: &str,
            session_id: &str,
        ) -> Option<Self::Snapshot> {
            let mut adapter = self.borrow_mut();
            adapter
                .load_calls
                .push((correlation_id.to_string(), session_id.to_string()));
            adapter.loaded_snapshot
        }
    }

    #[derive(Default)]
    struct RecordingHistoryAdapter {
        response: Option<HistoryCommandAdapterResponse<&'static str>>,
        recorded_action: Option<HistoryCommandAction>,
        recorded_correlation_id: Option<String>,
        recorded_stack: Option<&'static str>,
        recorded_snapshot: Option<&'static str>,
    }

    impl HistoryCommandAdapter for std::cell::RefCell<RecordingHistoryAdapter> {
        type Snapshot = &'static str;
        type Stack = &'static str;

        fn execute_history_command(
            &self,
            correlation_id: &str,
            action: HistoryCommandAction,
            stack: &mut Self::Stack,
            current_snapshot: &Self::Snapshot,
        ) -> HistoryCommandAdapterResponse<Self::Snapshot> {
            let mut adapter = self.borrow_mut();
            adapter.recorded_action = Some(action);
            adapter.recorded_correlation_id = Some(correlation_id.to_string());
            adapter.recorded_stack = Some(*stack);
            adapter.recorded_snapshot = Some(*current_snapshot);
            adapter
                .response
                .clone()
                .expect("history response should be configured")
        }
    }

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
        assert_eq!(spec.icon, Some("save"));
        assert_eq!(spec.shortcut, Some("Ctrl+S"));
    }

    #[test]
    fn exposes_extension_command_specs() {
        let spec = command_spec(COMMAND_EXTENSIONS_REFRESH_INVENTORY)
            .expect("extension spec should exist");

        assert_eq!(spec.group, "Extensions");
        assert_eq!(spec.action_label, Some("Refresh Inventory"));
    }

    #[test]
    fn builds_command_definition_from_shared_registry() {
        let definition = command_definition(COMMAND_DOCUMENT_SAVE, true, vec![])
            .expect("save definition should exist");

        assert_eq!(definition.command_id, COMMAND_DOCUMENT_SAVE);
        assert!(definition.enabled);
        assert_eq!(definition.label, "Save");
    }

    #[test]
    fn validates_selection_requirement_against_context() {
        let request = super::CommandExecutionRequest {
            command_id: COMMAND_SELECTION_FOCUS.into(),
            document_id: "doc-001".into(),
            target_object_id: None,
            arguments: HashMap::new(),
        };
        let context = CommandContext {
            document_id: "doc-001".into(),
            selected_object_id: None,
            selectable_object_ids: vec!["pad-001".into()],
        };

        let error = validate_command_request(&request, &context).expect_err("selection should be required");

        assert_eq!(error.kind, CommandValidationErrorKind::MissingSelection);
    }

    #[test]
    fn bridge_adapter_shapes_request_and_loads_snapshot_for_accepted_commands() {
        let request = super::CommandExecutionRequest {
            command_id: COMMAND_DOCUMENT_SAVE.into(),
            document_id: "doc-001".into(),
            target_object_id: None,
            arguments: HashMap::from([("source".into(), "toolbar".into())]),
        };
        let adapter = std::cell::RefCell::new(RecordingBridgeAdapter {
            execute_response: Some(Ok(BridgeCommandAdapterResponse {
                command_id: COMMAND_DOCUMENT_SAVE.into(),
                accepted: true,
                status_message: "Document marked as saved".into(),
                document_dirty: false,
            })),
            loaded_snapshot: Some("snapshot-a"),
            recorded_request: None,
            load_calls: vec![],
        });

        let outcome = execute_bridge_command(
            &adapter,
            "af-00000042",
            "session-001",
            Some("pad-001"),
            &request,
        );

        let adapter = adapter.borrow();
        assert_eq!(
            adapter.recorded_request,
            Some(BridgeCommandAdapterRequest {
                session_id: "session-001".into(),
                command_id: COMMAND_DOCUMENT_SAVE.into(),
                target_object_id: Some("pad-001".into()),
                arguments: BTreeMap::from([("source".into(), "toolbar".into())]),
                correlation_id: Some("af-00000042".into()),
            })
        );
        assert_eq!(adapter.load_calls.len(), 1);
        assert_eq!(adapter.load_calls[0], ("af-00000042".into(), "session-001".into()));
        assert!(outcome.response.accepted);
        assert_eq!(outcome.updated_snapshot, Some("snapshot-a"));
    }

    #[test]
    fn bridge_adapter_uses_summary_for_unsupported_failures() {
        let request = super::CommandExecutionRequest {
            command_id: "document.unsupported".into(),
            document_id: "doc-001".into(),
            target_object_id: None,
            arguments: HashMap::new(),
        };
        let adapter = std::cell::RefCell::new(RecordingBridgeAdapter {
            execute_response: Some(Err(BridgeCommandFailure {
                category: BridgeCommandErrorCategory::Unsupported,
                code: "bridge.command_unsupported".into(),
                summary: "Bridge command is not supported".into(),
                detail: "The prototype bridge does not handle this command.".into(),
                correlation_id: Some("af-00000043".into()),
            })),
            loaded_snapshot: Some("snapshot-a"),
            recorded_request: None,
            load_calls: vec![],
        });

        let outcome = execute_bridge_command(&adapter, "af-00000043", "session-001", None, &request);

        assert!(!outcome.response.accepted);
        assert_eq!(outcome.response.status_message, "Bridge command is not supported");
        assert!(outcome.updated_snapshot.is_none());
        assert!(adapter.borrow().load_calls.is_empty());
    }

    #[test]
    fn bridge_adapter_uses_detail_for_validation_failures() {
        let request = super::CommandExecutionRequest {
            command_id: COMMAND_DOCUMENT_SAVE.into(),
            document_id: "doc-001".into(),
            target_object_id: None,
            arguments: HashMap::new(),
        };
        let adapter = std::cell::RefCell::new(RecordingBridgeAdapter {
            execute_response: Some(Err(BridgeCommandFailure {
                category: BridgeCommandErrorCategory::ValidationError,
                code: "bridge.session_not_found".into(),
                summary: "Bridge session was not found".into(),
                detail: "Open or synchronize the prototype bridge session before executing commands.".into(),
                correlation_id: Some("af-00000044".into()),
            })),
            loaded_snapshot: None,
            recorded_request: None,
            load_calls: vec![],
        });

        let outcome = execute_bridge_command(&adapter, "af-00000044", "session-001", None, &request);

        assert!(!outcome.response.accepted);
        assert_eq!(
            outcome.response.status_message,
            "Open or synchronize the prototype bridge session before executing commands."
        );
        assert!(outcome.updated_snapshot.is_none());
    }

    #[test]
    fn history_adapter_routes_undo_and_restores_snapshot() {
        let request = super::CommandExecutionRequest {
            command_id: COMMAND_DOCUMENT_UNDO.into(),
            document_id: "doc-001".into(),
            target_object_id: None,
            arguments: HashMap::new(),
        };
        let adapter = std::cell::RefCell::new(RecordingHistoryAdapter {
            response: Some(HistoryCommandAdapterResponse {
                accepted: true,
                status_message: "Undo applied".into(),
                restored_snapshot: Some("snapshot-prev"),
            }),
            recorded_action: None,
            recorded_correlation_id: None,
            recorded_stack: None,
            recorded_snapshot: None,
        });
        let mut stack = "undo-stack";
        let current_snapshot = "snapshot-current";

        let outcome = execute_history_command(
            &adapter,
            "af-00000045",
            &request,
            &mut stack,
            &current_snapshot,
        );

        let adapter = adapter.borrow();
        assert_eq!(adapter.recorded_action, Some(HistoryCommandAction::Undo));
        assert_eq!(adapter.recorded_correlation_id.as_deref(), Some("af-00000045"));
        assert_eq!(adapter.recorded_stack, Some("undo-stack"));
        assert_eq!(adapter.recorded_snapshot, Some("snapshot-current"));
        assert!(outcome.response.accepted);
        assert_eq!(outcome.response.status_message, "Undo applied");
        assert_eq!(outcome.updated_snapshot, Some("snapshot-prev"));
    }

    #[test]
    fn history_adapter_rejects_non_history_commands() {
        let request = super::CommandExecutionRequest {
            command_id: COMMAND_DOCUMENT_SAVE.into(),
            document_id: "doc-001".into(),
            target_object_id: None,
            arguments: HashMap::new(),
        };
        let adapter = std::cell::RefCell::new(RecordingHistoryAdapter::default());
        let mut stack = "undo-stack";
        let current_snapshot = "snapshot-current";

        let outcome = execute_history_command(
            &adapter,
            "af-00000046",
            &request,
            &mut stack,
            &current_snapshot,
        );

        assert!(!outcome.response.accepted);
        assert_eq!(outcome.response.status_message, "Unsupported history command");
        assert!(outcome.updated_snapshot.is_none());
        assert!(adapter.borrow().recorded_action.is_none());
    }

    #[test]
    fn validates_requested_target_against_selectable_ids() {
        let request = super::CommandExecutionRequest {
            command_id: COMMAND_SELECTION_FOCUS.into(),
            document_id: "doc-001".into(),
            target_object_id: Some("sketch-404".into()),
            arguments: HashMap::new(),
        };
        let context = CommandContext {
            document_id: "doc-001".into(),
            selected_object_id: Some("pad-001".into()),
            selectable_object_ids: vec!["pad-001".into(), "sketch-001".into()],
        };

        let error = validate_command_request(&request, &context).expect_err("target should be rejected");

        assert_eq!(error.kind, CommandValidationErrorKind::InvalidTarget);
    }

    #[test]
    fn rejects_document_mismatch_during_validation() {
        let request = super::CommandExecutionRequest {
            command_id: COMMAND_DOCUMENT_SAVE.into(),
            document_id: "doc-other".into(),
            target_object_id: None,
            arguments: HashMap::new(),
        };
        let context = CommandContext {
            document_id: "doc-001".into(),
            selected_object_id: Some("pad-001".into()),
            selectable_object_ids: vec![],
        };

        let error = validate_command_request(&request, &context).expect_err("document mismatch should fail");

        assert_eq!(error.kind, CommandValidationErrorKind::DocumentMismatch);
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
    fn routes_commands_by_shared_dispatch_metadata() {
        assert_eq!(
            command_dispatch_route(COMMAND_STEP_VIEW_ISO, false),
            CommandDispatchRoute::Step
        );
        assert_eq!(
            command_dispatch_route(COMMAND_SELECTION_FOCUS, true),
            CommandDispatchRoute::Step
        );
        assert_eq!(
            command_dispatch_route(COMMAND_SELECTION_FOCUS, false),
            CommandDispatchRoute::BridgeVerticalSlice
        );
        assert_eq!(
            command_dispatch_route(COMMAND_DOCUMENT_REDO, false),
            CommandDispatchRoute::UndoRedo
        );
        assert_eq!(
            command_dispatch_route(COMMAND_EXTENSIONS_REFRESH_INVENTORY, false),
            CommandDispatchRoute::Extension
        );
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
    fn plans_runtime_bundle_with_job_and_event_metadata() {
        let runtime = plan_command_runtime(
            COMMAND_HISTORY_ROLLBACK_HERE,
            "Rolled back model evaluation",
            true,
            true,
            Some("toolbar"),
        );

        assert_eq!(runtime.job_title, "Rollback Here");
        assert_eq!(runtime.job_state, "completed");
        assert_eq!(runtime.job_progress_percent, 100);
        assert_eq!(runtime.job_stages[1].stage_id, "bridge_mutation");
        assert_eq!(runtime.job_stages[2].stage_id, "viewport_sync");
        assert_eq!(runtime.events.last().expect("outcome event").topic, "task_status");
        assert!(runtime.events.last().expect("outcome event").message.ends_with(" via toolbar"));
    }

    #[test]
    fn exposes_extension_lane_plans_and_execution_policy() {
        let refresh_plans = extension_refresh_lane_plans();
        assert_eq!(refresh_plans.len(), 2);
        assert_eq!(refresh_plans[0].lane_id, "macros");
        assert_eq!(refresh_plans[0].inventory_entries[0].entry_id, "macro:auto_dimensioning");
        assert_eq!(
            refresh_plans[1].command_ids,
            vec![COMMAND_EXTENSIONS_REVIEW_ADDON_CATALOG.to_string()]
        );

        let addon_review_plan = extension_addon_catalog_review_plan();
        assert_eq!(addon_review_plan.lane_id, "addon-manager");
        assert_eq!(addon_review_plan.inventory_entries.len(), 3);
        assert_eq!(addon_review_plan.inventory_entries[1].entry_id, "addon:sheetmetal_plus");

        let review_plan = extension_external_workbench_review_plan();
        assert_eq!(review_plan.lane_id, "external-workbenches");
        assert_eq!(review_plan.inventory_entries[0].entry_id, "workbench:robotics_plus");

        let blocked = evaluate_extension_inventory_execution_policy(
            "LegacySheetMetalTools.FCMacro",
            "needs-review",
            "qt-bound",
        )
        .expect("policy should reject non-shell-ready entry");
        assert!(!blocked.accepted);
        assert!(blocked.status_message.contains("not approved"));
    }

    #[test]
    fn formats_extension_execution_messages() {
        assert_eq!(
            extension_execution_failure_status_message("AutoDimensioning.FCMacro"),
            "Failed to execute reviewed inventory entry AutoDimensioning.FCMacro"
        );
        assert_eq!(
            extension_execution_success_status_message("AutoDimensioning.FCMacro"),
            "Executed reviewed inventory entry AutoDimensioning.FCMacro"
        );
        assert!(extension_execution_success_event_message(
            "AutoDimensioning.FCMacro",
            "Reviewed fixture bundle",
            "launcher success",
            "ASTERFORGE_MACRO_OK"
        )
        .contains("Executed reviewed inventory entry AutoDimensioning.FCMacro"));
        assert!(extension_execution_failure_event_message(
            "AutoDimensioning.FCMacro",
            "test launcher failure"
        )
        .contains("test launcher failure"));
    }

    #[test]
    fn exposes_viewport_invalidated_event_template() {
        let event = viewport_invalidated_event();

        assert_eq!(event.topic, "viewport_updated");
        assert_eq!(event.level, "info");
    }
}