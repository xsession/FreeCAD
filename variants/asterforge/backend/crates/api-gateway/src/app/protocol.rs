use asterforge_document_core::DocumentSummary;
use asterforge_freecad_bridge::{BridgeCapabilities, BridgeStatus};
use asterforge_protocol_types::asterforge::protocol::v1::{
    BootPayload as ProtoBootPayload, BootReport as ProtoBootReport,
    BridgeCapabilities as ProtoBridgeCapabilities, BridgeStatus as ProtoBridgeStatus,
    CommandArgumentDefinition as ProtoCommandArgumentDefinition,
    CommandCatalogResponse as ProtoCommandCatalogResponse, CommandDefinition as ProtoCommandDefinition,
    CommandReply, DiagnosticSignal as ProtoDiagnosticSignal,
    DiagnosticsResponse as ProtoDiagnosticsResponse, DiagnosticsSelection as ProtoDiagnosticsSelection,
    DiagnosticsSummary as ProtoDiagnosticsSummary, DocumentRef as ProtoDocumentRef,
    EventEnvelope as ProtoEventEnvelope, FeatureHistoryEntry as ProtoFeatureHistoryEntry,
    FeatureHistoryResponse as ProtoFeatureHistoryResponse, JobStageEntry as ProtoJobStageEntry,
    JobStatusEntry as ProtoJobStatusEntry, JobStatusResponse as ProtoJobStatusResponse,
    ObjectNode as ProtoObjectNode, ObjectTreeResponse as ProtoObjectTreeResponse,
    PreselectionState as ProtoPreselectionState, PropertyGroup as ProtoPropertyGroup,
    PropertyMetadata as ProtoPropertyMetadata, PropertyResponse as ProtoPropertyResponse,
    SelectionModeOption as ProtoSelectionModeOption, SelectionReply,
    SelectionState as ProtoSelectionState, TaskPanelResponse as ProtoTaskPanelResponse,
    TaskPanelRow as ProtoTaskPanelRow, TaskPanelSection as ProtoTaskPanelSection,
    ViewportBounds as ProtoViewportBounds, ViewportDiffResponse as ProtoViewportDiffResponse,
    ViewportDrawable as ProtoViewportDrawable, ViewportResponse as ProtoViewportResponse,
    ViewportScene as ProtoViewportScene, WorkbenchState as ProtoWorkbenchState,
};

use crate::domain::{
    sample_bridge_status, BackendEvent, BootReport, CommandCatalogResponse, DiagnosticsResponse,
    FeatureHistoryResponse, JobStageEntry, JobStatusEntry, JobStatusResponse, ObjectNode,
    PreselectionStateResponse, PropertyGroup, PropertyResponse, SelectionModeOption,
    SelectionStateResponse, TaskPanelResponse, ViewportDiffResponse, ViewportResponse,
};

use super::state::{BootPayload, HttpCommandExecutionResponse, SelectionResponse};

pub fn command_reply_from_http(response: HttpCommandExecutionResponse) -> CommandReply {
    CommandReply {
        command_id: response.command_id,
        accepted: response.accepted,
        status_message: response.status_message,
        document_dirty: response.document_dirty,
        viewport_diff: response.viewport_diff.map(proto_viewport_diff_from_http),
    }
}

pub fn http_command_response_from_proto(response: CommandReply) -> HttpCommandExecutionResponse {
    HttpCommandExecutionResponse {
        command_id: response.command_id,
        accepted: response.accepted,
        status_message: response.status_message,
        document_dirty: response.document_dirty,
        viewport_diff: response.viewport_diff.map(http_viewport_diff_from_proto),
    }
}

pub fn boot_payload_proto_from_http(response: BootPayload) -> ProtoBootPayload {
    ProtoBootPayload {
        boot_report: Some(ProtoBootReport {
            services: response.boot_report.services,
            event_streams: response.boot_report.event_streams,
        }),
        bridge_status: Some(proto_bridge_status_from_http(response.bridge_status)),
        document: Some(proto_document_ref_from_http(response.document)),
        object_tree: response.object_tree.into_iter().map(proto_object_node_from_http).collect(),
        selected_object_id: response.selected_object_id,
        selection_state: Some(selection_state_proto_from_http(response.selection_state)),
        preselection_state: Some(preselection_state_proto_from_http(response.preselection_state)),
        jobs: Some(proto_jobs_from_http(response.jobs)),
        properties: Some(proto_properties_from_http(response.properties)),
        viewport: Some(proto_viewport_from_http(response.viewport)),
        feature_history: Some(proto_feature_history_from_http(response.feature_history)),
        command_catalog: Some(proto_command_catalog_from_http(response.command_catalog)),
        task_panel: Some(proto_task_panel_from_http(response.task_panel)),
        diagnostics: Some(proto_diagnostics_from_http(response.diagnostics)),
        events: response.events.into_iter().map(proto_event_from_http).collect(),
    }
}

pub fn http_boot_payload_from_proto(response: ProtoBootPayload) -> BootPayload {
    let boot_report = response.boot_report.unwrap_or(ProtoBootReport {
        services: vec![],
        event_streams: vec![],
    });
    BootPayload {
        boot_report: BootReport {
            services: boot_report.services,
            event_streams: boot_report.event_streams,
        },
        bridge_status: response
            .bridge_status
            .map(http_bridge_status_from_proto)
            .unwrap_or_else(sample_bridge_status),
        document: response
            .document
            .map(http_document_summary_from_proto)
            .unwrap_or(DocumentSummary {
                document_id: String::new(),
                display_name: String::new(),
                workbench: String::new(),
                file_path: None,
                dirty: false,
            }),
        object_tree: response
            .object_tree
            .into_iter()
            .map(http_object_node_from_proto)
            .collect(),
        selected_object_id: response.selected_object_id,
        selection_state: response
            .selection_state
            .map(http_selection_state_from_proto)
            .unwrap_or(SelectionStateResponse {
                document_id: String::new(),
                current_mode: String::new(),
                selected_object_id: String::new(),
                selected_object_label: String::new(),
                selected_object_type: String::new(),
                available_modes: vec![],
            }),
        preselection_state: response
            .preselection_state
            .map(http_preselection_state_from_proto)
            .unwrap_or(PreselectionStateResponse {
                document_id: String::new(),
                current_mode: String::new(),
                object_id: None,
                object_label: None,
                object_type: None,
                selectable: false,
                model_state: String::new(),
                dependency_note: String::new(),
                suggested_commands: vec![],
                detail: String::new(),
            }),
        jobs: response.jobs.map(http_jobs_from_proto).unwrap_or(JobStatusResponse {
            document_id: String::new(),
            jobs: vec![],
        }),
        properties: response
            .properties
            .map(http_properties_from_proto)
            .unwrap_or(PropertyResponse {
                object_id: String::new(),
                groups: vec![],
            }),
        viewport: response
            .viewport
            .map(http_viewport_from_proto)
            .unwrap_or(ViewportResponse {
                document_id: String::new(),
                selected_object_id: String::new(),
                scene: crate::domain::ViewportScene {
                    camera_eye: [0.0, 0.0, 0.0],
                    camera_target: [0.0, 0.0, 0.0],
                    drawables: vec![],
                },
            }),
        feature_history: response
            .feature_history
            .map(http_feature_history_from_proto)
            .unwrap_or(FeatureHistoryResponse {
                document_id: String::new(),
                entries: vec![],
            }),
        command_catalog: response
            .command_catalog
            .map(http_command_catalog_from_proto)
            .unwrap_or(CommandCatalogResponse {
                document_id: String::new(),
                workbench: crate::domain::WorkbenchState {
                    workbench_id: String::new(),
                    display_name: String::new(),
                    mode: String::new(),
                },
                commands: vec![],
            }),
        task_panel: response
            .task_panel
            .map(http_task_panel_from_proto)
            .unwrap_or(TaskPanelResponse {
                document_id: String::new(),
                title: String::new(),
                description: String::new(),
                sections: vec![],
                suggested_commands: vec![],
            }),
        diagnostics: response
            .diagnostics
            .map(http_diagnostics_from_proto)
            .unwrap_or(DiagnosticsResponse {
                document_id: String::new(),
                summary: crate::domain::DiagnosticsSummary {
                    total_features: 0,
                    suppressed_count: 0,
                    inactive_count: 0,
                    rolled_back_count: 0,
                    viewport_drawable_count: 0,
                    warning_count: 0,
                    error_count: 0,
                    history_marker_active: false,
                    worker_mode: String::new(),
                },
                selection: crate::domain::DiagnosticsSelection {
                    object_id: None,
                    object_label: None,
                    object_type: None,
                    model_state: String::new(),
                    dependency_note: String::new(),
                    visible_in_viewport: false,
                },
                recent_signals: vec![],
            }),
        events: response.events.into_iter().map(http_event_from_proto).collect(),
    }
}

pub fn selection_reply_from_http(response: SelectionResponse) -> SelectionReply {
    SelectionReply {
        selected_object_id: response.selected_object_id,
    }
}

pub fn http_selection_response_from_proto(response: SelectionReply) -> SelectionResponse {
    SelectionResponse {
        selected_object_id: response.selected_object_id,
    }
}

pub fn selection_state_proto_from_http(response: SelectionStateResponse) -> ProtoSelectionState {
    ProtoSelectionState {
        document_id: response.document_id,
        current_mode: response.current_mode,
        selected_object_id: response.selected_object_id,
        selected_object_label: response.selected_object_label,
        selected_object_type: response.selected_object_type,
        available_modes: response
            .available_modes
            .into_iter()
            .map(|mode| ProtoSelectionModeOption {
                mode_id: mode.mode_id,
                label: mode.label,
                description: mode.description,
                enabled: mode.enabled,
                object_count: mode.object_count,
            })
            .collect(),
    }
}

pub fn http_selection_state_from_proto(response: ProtoSelectionState) -> SelectionStateResponse {
    SelectionStateResponse {
        document_id: response.document_id,
        current_mode: response.current_mode,
        selected_object_id: response.selected_object_id,
        selected_object_label: response.selected_object_label,
        selected_object_type: response.selected_object_type,
        available_modes: response
            .available_modes
            .into_iter()
            .map(|mode| SelectionModeOption {
                mode_id: mode.mode_id,
                label: mode.label,
                description: mode.description,
                enabled: mode.enabled,
                object_count: mode.object_count,
            })
            .collect(),
    }
}

pub fn preselection_state_proto_from_http(
    response: PreselectionStateResponse,
) -> ProtoPreselectionState {
    ProtoPreselectionState {
        document_id: response.document_id,
        current_mode: response.current_mode,
        object_id: response.object_id,
        object_label: response.object_label,
        object_type: response.object_type,
        selectable: response.selectable,
        model_state: response.model_state,
        dependency_note: response.dependency_note,
        suggested_commands: response.suggested_commands,
        detail: response.detail,
    }
}

pub fn http_preselection_state_from_proto(
    response: ProtoPreselectionState,
) -> PreselectionStateResponse {
    PreselectionStateResponse {
        document_id: response.document_id,
        current_mode: response.current_mode,
        object_id: response.object_id,
        object_label: response.object_label,
        object_type: response.object_type,
        selectable: response.selectable,
        model_state: response.model_state,
        dependency_note: response.dependency_note,
        suggested_commands: response.suggested_commands,
        detail: response.detail,
    }
}

pub fn proto_document_ref_from_http(response: DocumentSummary) -> ProtoDocumentRef {
    ProtoDocumentRef {
        document_id: response.document_id,
        display_name: response.display_name,
        file_path: response.file_path,
        workbench: response.workbench,
        dirty: response.dirty,
    }
}

pub fn proto_object_node_from_http(response: ObjectNode) -> ProtoObjectNode {
    ProtoObjectNode {
        object_id: response.object_id,
        label: response.label,
        object_type: response.object_type,
        visibility: match response.visibility {
            crate::domain::VisibilityState::Visible => "visible".into(),
            crate::domain::VisibilityState::Hidden => "hidden".into(),
            crate::domain::VisibilityState::Inherited => "inherited".into(),
        },
        children: response.children.into_iter().map(proto_object_node_from_http).collect(),
    }
}

pub fn http_object_tree_from_proto(response: ProtoObjectTreeResponse) -> Vec<ObjectNode> {
    response
        .roots
        .into_iter()
        .map(http_object_node_from_proto)
        .collect()
}

pub fn proto_properties_from_http(response: PropertyResponse) -> ProtoPropertyResponse {
    ProtoPropertyResponse {
        object_id: response.object_id,
        groups: response.groups.into_iter().map(proto_property_group_from_http).collect(),
    }
}

pub fn http_properties_from_proto(response: ProtoPropertyResponse) -> PropertyResponse {
    PropertyResponse {
        object_id: response.object_id,
        groups: response.groups.into_iter().map(http_property_group_from_proto).collect(),
    }
}

pub fn proto_jobs_from_http(response: JobStatusResponse) -> ProtoJobStatusResponse {
    ProtoJobStatusResponse {
        document_id: response.document_id,
        jobs: response.jobs.into_iter().map(proto_job_status_entry_from_http).collect(),
    }
}

pub fn http_jobs_from_proto(response: ProtoJobStatusResponse) -> JobStatusResponse {
    JobStatusResponse {
        document_id: response.document_id,
        jobs: response.jobs.into_iter().map(http_job_status_entry_from_proto).collect(),
    }
}

pub fn proto_viewport_from_http(response: ViewportResponse) -> ProtoViewportResponse {
    ProtoViewportResponse {
        document_id: response.document_id,
        selected_object_id: response.selected_object_id,
        scene: Some(ProtoViewportScene {
            camera_eye: response.scene.camera_eye.to_vec(),
            camera_target: response.scene.camera_target.to_vec(),
            drawables: response
                .scene
                .drawables
                .into_iter()
                .map(proto_viewport_drawable_from_http)
                .collect(),
        }),
    }
}

pub fn http_viewport_from_proto(response: ProtoViewportResponse) -> ViewportResponse {
    let scene = response.scene.unwrap_or(ProtoViewportScene {
        camera_eye: vec![],
        camera_target: vec![],
        drawables: vec![],
    });
    ViewportResponse {
        document_id: response.document_id,
        selected_object_id: response.selected_object_id,
        scene: crate::domain::ViewportScene {
            camera_eye: [
                *scene.camera_eye.first().unwrap_or(&0.0),
                *scene.camera_eye.get(1).unwrap_or(&0.0),
                *scene.camera_eye.get(2).unwrap_or(&0.0),
            ],
            camera_target: [
                *scene.camera_target.first().unwrap_or(&0.0),
                *scene.camera_target.get(1).unwrap_or(&0.0),
                *scene.camera_target.get(2).unwrap_or(&0.0),
            ],
            drawables: scene.drawables.into_iter().map(http_viewport_drawable_from_proto).collect(),
        },
    }
}

pub fn proto_feature_history_from_http(response: FeatureHistoryResponse) -> ProtoFeatureHistoryResponse {
    ProtoFeatureHistoryResponse {
        document_id: response.document_id,
        entries: response
            .entries
            .into_iter()
            .map(|entry| ProtoFeatureHistoryEntry {
                object_id: entry.object_id,
                label: entry.label,
                object_type: entry.object_type,
                sequence_index: entry.sequence_index,
                source_object_id: entry.source_object_id,
                role: entry.role,
                suppressed: entry.suppressed,
                active: entry.active,
                inactive_reason: entry.inactive_reason,
                rolled_back: entry.rolled_back,
            })
            .collect(),
    }
}

pub fn http_feature_history_from_proto(response: ProtoFeatureHistoryResponse) -> FeatureHistoryResponse {
    FeatureHistoryResponse {
        document_id: response.document_id,
        entries: response
            .entries
            .into_iter()
            .map(|entry| crate::domain::FeatureHistoryEntry {
                object_id: entry.object_id,
                label: entry.label,
                object_type: entry.object_type,
                sequence_index: entry.sequence_index,
                source_object_id: entry.source_object_id,
                role: entry.role,
                suppressed: entry.suppressed,
                active: entry.active,
                inactive_reason: entry.inactive_reason,
                rolled_back: entry.rolled_back,
            })
            .collect(),
    }
}

pub fn proto_command_catalog_from_http(response: CommandCatalogResponse) -> ProtoCommandCatalogResponse {
    ProtoCommandCatalogResponse {
        document_id: response.document_id,
        workbench: Some(ProtoWorkbenchState {
            workbench_id: response.workbench.workbench_id,
            display_name: response.workbench.display_name,
            mode: response.workbench.mode,
        }),
        commands: response
            .commands
            .into_iter()
            .map(|command| ProtoCommandDefinition {
                command_id: command.command_id,
                label: command.label,
                group: command.group,
                shortcut: command.shortcut,
                enabled: command.enabled,
                requires_selection: command.requires_selection,
                description: command.description,
                action_label: command.action_label,
                arguments: command
                    .arguments
                    .into_iter()
                    .map(|argument| ProtoCommandArgumentDefinition {
                        argument_id: argument.argument_id,
                        label: argument.label,
                        value_type: argument.value_type,
                        required: argument.required,
                        default_value: argument.default_value,
                        placeholder: argument.placeholder,
                        unit: argument.unit,
                        options: argument.options,
                    })
                    .collect(),
            })
            .collect(),
    }
}

pub fn http_command_catalog_from_proto(response: ProtoCommandCatalogResponse) -> CommandCatalogResponse {
    let workbench = response.workbench.unwrap_or(ProtoWorkbenchState {
        workbench_id: String::new(),
        display_name: String::new(),
        mode: String::new(),
    });
    CommandCatalogResponse {
        document_id: response.document_id,
        workbench: crate::domain::WorkbenchState {
            workbench_id: workbench.workbench_id,
            display_name: workbench.display_name,
            mode: workbench.mode,
        },
        commands: response
            .commands
            .into_iter()
            .map(|command| crate::domain::CommandDefinition {
                command_id: command.command_id,
                label: command.label,
                group: command.group,
                shortcut: command.shortcut,
                enabled: command.enabled,
                requires_selection: command.requires_selection,
                description: command.description,
                action_label: command.action_label,
                arguments: command
                    .arguments
                    .into_iter()
                    .map(|argument| crate::domain::CommandArgumentDefinition {
                        argument_id: argument.argument_id,
                        label: argument.label,
                        value_type: argument.value_type,
                        required: argument.required,
                        default_value: argument.default_value,
                        placeholder: argument.placeholder,
                        unit: argument.unit,
                        options: argument.options,
                    })
                    .collect(),
            })
            .collect(),
    }
}

pub fn proto_task_panel_from_http(response: TaskPanelResponse) -> ProtoTaskPanelResponse {
    ProtoTaskPanelResponse {
        document_id: response.document_id,
        title: response.title,
        description: response.description,
        sections: response.sections.into_iter().map(proto_task_panel_section_from_http).collect(),
        suggested_commands: response.suggested_commands,
    }
}

pub fn http_task_panel_from_proto(response: ProtoTaskPanelResponse) -> TaskPanelResponse {
    TaskPanelResponse {
        document_id: response.document_id,
        title: response.title,
        description: response.description,
        sections: response.sections.into_iter().map(http_task_panel_section_from_proto).collect(),
        suggested_commands: response.suggested_commands,
    }
}

pub fn proto_diagnostics_from_http(response: DiagnosticsResponse) -> ProtoDiagnosticsResponse {
    ProtoDiagnosticsResponse {
        document_id: response.document_id,
        summary: Some(ProtoDiagnosticsSummary {
            total_features: response.summary.total_features,
            suppressed_count: response.summary.suppressed_count,
            inactive_count: response.summary.inactive_count,
            rolled_back_count: response.summary.rolled_back_count,
            viewport_drawable_count: response.summary.viewport_drawable_count,
            warning_count: response.summary.warning_count,
            error_count: response.summary.error_count,
            history_marker_active: response.summary.history_marker_active,
            worker_mode: response.summary.worker_mode,
        }),
        selection: Some(ProtoDiagnosticsSelection {
            object_id: response.selection.object_id,
            object_label: response.selection.object_label,
            object_type: response.selection.object_type,
            model_state: response.selection.model_state,
            dependency_note: response.selection.dependency_note,
            visible_in_viewport: response.selection.visible_in_viewport,
        }),
        recent_signals: response
            .recent_signals
            .into_iter()
            .map(|signal| ProtoDiagnosticSignal {
                level: signal.level,
                title: signal.title,
                detail: signal.detail,
            })
            .collect(),
    }
}

pub fn http_diagnostics_from_proto(response: ProtoDiagnosticsResponse) -> DiagnosticsResponse {
    let summary = response.summary.unwrap_or(ProtoDiagnosticsSummary {
        total_features: 0,
        suppressed_count: 0,
        inactive_count: 0,
        rolled_back_count: 0,
        viewport_drawable_count: 0,
        warning_count: 0,
        error_count: 0,
        history_marker_active: false,
        worker_mode: String::new(),
    });
    let selection = response.selection.unwrap_or(ProtoDiagnosticsSelection {
        object_id: None,
        object_label: None,
        object_type: None,
        model_state: String::new(),
        dependency_note: String::new(),
        visible_in_viewport: false,
    });
    DiagnosticsResponse {
        document_id: response.document_id,
        summary: crate::domain::DiagnosticsSummary {
            total_features: summary.total_features,
            suppressed_count: summary.suppressed_count,
            inactive_count: summary.inactive_count,
            rolled_back_count: summary.rolled_back_count,
            viewport_drawable_count: summary.viewport_drawable_count,
            warning_count: summary.warning_count,
            error_count: summary.error_count,
            history_marker_active: summary.history_marker_active,
            worker_mode: summary.worker_mode,
        },
        selection: crate::domain::DiagnosticsSelection {
            object_id: selection.object_id,
            object_label: selection.object_label,
            object_type: selection.object_type,
            model_state: selection.model_state,
            dependency_note: selection.dependency_note,
            visible_in_viewport: selection.visible_in_viewport,
        },
        recent_signals: response
            .recent_signals
            .into_iter()
            .map(|signal| crate::domain::DiagnosticSignal {
                level: signal.level,
                title: signal.title,
                detail: signal.detail,
            })
            .collect(),
    }
}

pub fn proto_event_from_http(response: BackendEvent) -> ProtoEventEnvelope {
    ProtoEventEnvelope {
        topic: response.topic,
        level: response.level,
        message: response.message,
        document_id: response.document_id,
        object_id: response.object_id,
    }
}

pub fn http_events_from_proto(response: Vec<ProtoEventEnvelope>) -> Vec<BackendEvent> {
    response.into_iter().map(http_event_from_proto).collect()
}

fn proto_bridge_status_from_http(response: BridgeStatus) -> ProtoBridgeStatus {
    ProtoBridgeStatus {
        worker_mode: response.worker_mode,
        freecad_runtime_detected: response.freecad_runtime_detected,
        capabilities: Some(ProtoBridgeCapabilities {
            fcstd_open: response.capabilities.fcstd_open,
            object_tree_fetch: response.capabilities.object_tree_fetch,
            property_fetch: response.capabilities.property_fetch,
            tessellation_fetch: response.capabilities.tessellation_fetch,
            command_execution: response.capabilities.command_execution,
        }),
    }
}

fn http_bridge_status_from_proto(response: ProtoBridgeStatus) -> BridgeStatus {
    let capabilities = response.capabilities.unwrap_or(ProtoBridgeCapabilities {
        fcstd_open: false,
        object_tree_fetch: false,
        property_fetch: false,
        tessellation_fetch: false,
        command_execution: false,
    });

    BridgeStatus {
        worker_mode: response.worker_mode,
        freecad_runtime_detected: response.freecad_runtime_detected,
        capabilities: BridgeCapabilities {
            fcstd_open: capabilities.fcstd_open,
            object_tree_fetch: capabilities.object_tree_fetch,
            property_fetch: capabilities.property_fetch,
            tessellation_fetch: capabilities.tessellation_fetch,
            command_execution: capabilities.command_execution,
        },
    }
}

fn http_document_summary_from_proto(response: ProtoDocumentRef) -> DocumentSummary {
    DocumentSummary {
        document_id: response.document_id,
        display_name: response.display_name,
        workbench: response.workbench,
        file_path: response.file_path,
        dirty: response.dirty,
    }
}

fn http_object_node_from_proto(response: ProtoObjectNode) -> ObjectNode {
    ObjectNode {
        object_id: response.object_id,
        label: response.label,
        object_type: response.object_type,
        visibility: match response.visibility.as_str() {
            "visible" => crate::domain::VisibilityState::Visible,
            "hidden" => crate::domain::VisibilityState::Hidden,
            _ => crate::domain::VisibilityState::Inherited,
        },
        children: response.children.into_iter().map(http_object_node_from_proto).collect(),
    }
}

fn proto_property_group_from_http(response: PropertyGroup) -> ProtoPropertyGroup {
    ProtoPropertyGroup {
        group_id: response.group_id,
        title: response.title,
        properties: response
            .properties
            .into_iter()
            .map(proto_property_metadata_from_http)
            .collect(),
    }
}

fn http_property_group_from_proto(response: ProtoPropertyGroup) -> PropertyGroup {
    PropertyGroup {
        group_id: response.group_id,
        title: response.title,
        properties: response
            .properties
            .into_iter()
            .map(http_property_metadata_from_proto)
            .collect(),
    }
}

fn proto_property_metadata_from_http(response: crate::domain::PropertyMetadata) -> ProtoPropertyMetadata {
    ProtoPropertyMetadata {
        property_id: response.property_id,
        display_name: response.display_name,
        property_type: response.property_type,
        value_kind: response.value_kind,
        read_only: response.read_only,
        unit: response.unit,
        expression_capable: response.expression_capable,
        value_preview: response.value_preview,
    }
}

fn http_property_metadata_from_proto(response: ProtoPropertyMetadata) -> crate::domain::PropertyMetadata {
    crate::domain::PropertyMetadata {
        property_id: response.property_id,
        display_name: response.display_name,
        property_type: response.property_type,
        value_kind: response.value_kind,
        read_only: response.read_only,
        unit: response.unit,
        expression_capable: response.expression_capable,
        value_preview: response.value_preview,
    }
}

fn proto_job_status_entry_from_http(response: JobStatusEntry) -> ProtoJobStatusEntry {
    ProtoJobStatusEntry {
        job_id: response.job_id,
        title: response.title,
        command_id: response.command_id,
        state: response.state,
        progress_percent: response.progress_percent,
        detail: response.detail,
        object_id: response.object_id,
        stages: response.stages.into_iter().map(proto_job_stage_entry_from_http).collect(),
    }
}

fn http_job_status_entry_from_proto(response: ProtoJobStatusEntry) -> JobStatusEntry {
    JobStatusEntry {
        job_id: response.job_id,
        title: response.title,
        command_id: response.command_id,
        state: response.state,
        progress_percent: response.progress_percent,
        detail: response.detail,
        object_id: response.object_id,
        stages: response.stages.into_iter().map(http_job_stage_entry_from_proto).collect(),
    }
}

fn proto_job_stage_entry_from_http(response: JobStageEntry) -> ProtoJobStageEntry {
    ProtoJobStageEntry {
        stage_id: response.stage_id,
        label: response.label,
        state: response.state,
        progress_percent: response.progress_percent,
    }
}

fn http_job_stage_entry_from_proto(response: ProtoJobStageEntry) -> JobStageEntry {
    JobStageEntry {
        stage_id: response.stage_id,
        label: response.label,
        state: response.state,
        progress_percent: response.progress_percent,
    }
}

fn proto_task_panel_section_from_http(response: crate::domain::TaskPanelSection) -> ProtoTaskPanelSection {
    ProtoTaskPanelSection {
        section_id: response.section_id,
        title: response.title,
        rows: response.rows.into_iter().map(proto_task_panel_row_from_http).collect(),
    }
}

fn http_task_panel_section_from_proto(response: ProtoTaskPanelSection) -> crate::domain::TaskPanelSection {
    crate::domain::TaskPanelSection {
        section_id: response.section_id,
        title: response.title,
        rows: response.rows.into_iter().map(http_task_panel_row_from_proto).collect(),
    }
}

fn proto_task_panel_row_from_http(response: crate::domain::TaskPanelRow) -> ProtoTaskPanelRow {
    ProtoTaskPanelRow {
        label: response.label,
        value: response.value,
        emphasis: response.emphasis,
    }
}

fn http_task_panel_row_from_proto(response: ProtoTaskPanelRow) -> crate::domain::TaskPanelRow {
    crate::domain::TaskPanelRow {
        label: response.label,
        value: response.value,
        emphasis: response.emphasis,
    }
}

fn http_event_from_proto(response: ProtoEventEnvelope) -> BackendEvent {
    BackendEvent {
        topic: response.topic,
        level: response.level,
        message: response.message,
        document_id: response.document_id,
        object_id: response.object_id,
    }
}

fn proto_viewport_diff_from_http(response: ViewportDiffResponse) -> ProtoViewportDiffResponse {
    ProtoViewportDiffResponse {
        document_id: response.document_id,
        selected_object_id: response.selected_object_id,
        added: response.added.into_iter().map(proto_viewport_drawable_from_http).collect(),
        removed: response.removed,
        modified: response
            .modified
            .into_iter()
            .map(proto_viewport_drawable_from_http)
            .collect(),
        camera_changed: response.camera_changed,
        camera_eye: response.camera_eye.unwrap_or_default().to_vec(),
        camera_target: response.camera_target.unwrap_or_default().to_vec(),
    }
}

fn proto_viewport_drawable_from_http(drawable: crate::domain::ViewportDrawable) -> ProtoViewportDrawable {
    ProtoViewportDrawable {
        object_id: drawable.object_id,
        label: drawable.label,
        kind: drawable.kind,
        accent: drawable.accent,
        bounds: Some(ProtoViewportBounds {
            x: drawable.bounds.x,
            y: drawable.bounds.y,
            width: drawable.bounds.width,
            height: drawable.bounds.height,
        }),
        paths: drawable.paths,
    }
}

fn http_viewport_diff_from_proto(response: ProtoViewportDiffResponse) -> ViewportDiffResponse {
    ViewportDiffResponse {
        document_id: response.document_id,
        selected_object_id: response.selected_object_id,
        added: response.added.into_iter().map(http_viewport_drawable_from_proto).collect(),
        removed: response.removed,
        modified: response
            .modified
            .into_iter()
            .map(http_viewport_drawable_from_proto)
            .collect(),
        camera_changed: response.camera_changed,
        camera_eye: (!response.camera_eye.is_empty()).then_some([
            *response.camera_eye.first().unwrap_or(&0.0),
            *response.camera_eye.get(1).unwrap_or(&0.0),
            *response.camera_eye.get(2).unwrap_or(&0.0),
        ]),
        camera_target: (!response.camera_target.is_empty()).then_some([
            *response.camera_target.first().unwrap_or(&0.0),
            *response.camera_target.get(1).unwrap_or(&0.0),
            *response.camera_target.get(2).unwrap_or(&0.0),
        ]),
    }
}

fn http_viewport_drawable_from_proto(drawable: ProtoViewportDrawable) -> crate::domain::ViewportDrawable {
    let bounds = drawable.bounds.unwrap_or(ProtoViewportBounds {
        x: 0.0,
        y: 0.0,
        width: 0.0,
        height: 0.0,
    });

    crate::domain::ViewportDrawable {
        object_id: drawable.object_id,
        label: drawable.label,
        kind: drawable.kind,
        accent: drawable.accent,
        bounds: crate::domain::ViewportBounds {
            x: bounds.x,
            y: bounds.y,
            width: bounds.width,
            height: bounds.height,
        },
        paths: drawable.paths,
    }
}