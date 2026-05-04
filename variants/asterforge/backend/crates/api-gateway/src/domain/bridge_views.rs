use crate::domain::{
    bridge_object_state, command_definition, feature_history_from_bridge, find_pad_length_mm,
    history_marker_label, normalize_workbench_id, object_matches_selection_mode,
    selectable_object_ids_for_mode, workbench_display_name, workbench_state_from_bridge,
    BackendEvent, CommandCatalogResponse, DiagnosticSignal, DiagnosticsResponse,
    DiagnosticsSelection, DiagnosticsSummary, FeatureDependencyState,
    PreselectionStateResponse, SelectionModeOption, SelectionStateResponse, TaskPanelResponse,
    TaskPanelRow, TaskPanelSection,
};
use asterforge_command_core::CommandArgumentDefinition;
use asterforge_freecad_bridge::{
    body_feature_summary, body_next_step, body_workflow_description, dependency_issue_hint,
    dependency_status_label, dependency_workflow_description, pad_inspection_hint,
    pad_workflow_description, pocket_inspection_hint, pocket_workflow_description,
    sketch_next_step, sketch_workflow_description, BridgeDocumentSnapshot, BridgeStatus,
};
use asterforge_document_core::{sketch_constraint_summary, sketch_profile_readiness};

pub fn command_catalog_from_bridge(
    snapshot: &BridgeDocumentSnapshot,
    document_id: &str,
    selected_object_id: Option<&str>,
    can_undo: bool,
    can_redo: bool,
) -> CommandCatalogResponse {
    let workbench_id = normalize_workbench_id(&snapshot.workbench);
    let selected_is_body = matches!(selected_object_id, Some("body-001"));
    let selected_node = selected_object_id.and_then(|object_id| find_bridge_object(snapshot, object_id));
    let selected_state = selected_node.map(|node| bridge_object_state(snapshot, node));
    let selected_length_mm = selected_object_id.and_then(|object_id| find_pad_length_mm(snapshot, object_id));
    let selected_plane = selected_node
        .and_then(|node| node.reference_plane.clone())
        .unwrap_or_else(|| "XY".into());
    let selected_extent_mode = selected_node
        .and_then(|node| node.extent_mode.clone())
        .unwrap_or_else(|| "dimension".into());
    let selected_midplane = selected_node.map(|node| node.midplane).unwrap_or(false);
    let selected_is_sketch = matches!(selected_node, Some(node) if node.object_id.starts_with("sketch-"));
    let selected_is_pad = matches!(selected_node, Some(node) if node.object_id.starts_with("pad-"));
    let selected_is_pocket = matches!(selected_node, Some(node) if node.object_id.starts_with("pocket-"));
    let selected_is_feature = matches!(selected_node, Some(node) if node.object_id != "body-001");
    let history_marker_active = snapshot.history_marker.is_some();
    let selected_is_operable = selected_state
        .as_ref()
        .map(|state| state.active && !state.suppressed)
        .unwrap_or(false);
    let mut commands = vec![
        command_definition("document.recompute", true, vec![]),
        command_definition("document.save", true, vec![]),
        command_definition("selection.focus", selected_object_id.is_some(), vec![]),
        command_definition("extensions.refresh_inventory", true, vec![]),
        command_definition("extensions.review_addon_catalog", true, vec![]),
        command_definition("extensions.review_external_workbenches", true, vec![]),
        command_definition(
            "extensions.run_inventory_entry",
            true,
            vec![CommandArgumentDefinition {
                argument_id: "entry_id".into(),
                label: "Inventory entry".into(),
                value_type: "string".into(),
                required: true,
                default_value: None,
                placeholder: Some("macro:auto_dimensioning".into()),
                unit: None,
                options: vec![],
            }],
        ),
    ];

    if workbench_id == "partdesign" {
        commands.extend([
            command_definition(
                "partdesign.new_sketch",
                selected_is_body,
                vec![
                    CommandArgumentDefinition {
                        argument_id: "sketch_label".into(),
                        label: "Sketch label".into(),
                        value_type: "string".into(),
                        required: false,
                        default_value: Some("Sketch".into()),
                        placeholder: Some("Sketch".into()),
                        unit: None,
                        options: vec![],
                    },
                    CommandArgumentDefinition {
                        argument_id: "reference_plane".into(),
                        label: "Reference plane".into(),
                        value_type: "enum".into(),
                        required: true,
                        default_value: Some(selected_plane.clone()),
                        placeholder: None,
                        unit: None,
                        options: vec!["XY".into(), "XZ".into(), "YZ".into()],
                    },
                ],
            ),
            command_definition(
                "partdesign.pad",
                selected_is_sketch && selected_is_operable,
                vec![
                    CommandArgumentDefinition {
                        argument_id: "length_mm".into(),
                        label: "Pad length".into(),
                        value_type: "quantity".into(),
                        required: false,
                        default_value: Some(format!("{:.2}", selected_length_mm.unwrap_or(12.0))),
                        placeholder: Some("12.00".into()),
                        unit: Some("mm".into()),
                        options: vec![],
                    },
                    CommandArgumentDefinition {
                        argument_id: "midplane".into(),
                        label: "Symmetric to plane".into(),
                        value_type: "boolean".into(),
                        required: true,
                        default_value: Some(selected_midplane.to_string()),
                        placeholder: None,
                        unit: None,
                        options: vec!["false".into(), "true".into()],
                    },
                ],
            ),
            command_definition(
                "partdesign.pocket",
                selected_is_sketch && selected_is_operable,
                vec![
                    CommandArgumentDefinition {
                        argument_id: "depth_mm".into(),
                        label: "Pocket depth".into(),
                        value_type: "quantity".into(),
                        required: false,
                        default_value: Some("8.00".into()),
                        placeholder: Some("8.00".into()),
                        unit: Some("mm".into()),
                        options: vec![],
                    },
                    CommandArgumentDefinition {
                        argument_id: "extent_mode".into(),
                        label: "Extent mode".into(),
                        value_type: "enum".into(),
                        required: true,
                        default_value: Some("dimension".into()),
                        placeholder: None,
                        unit: None,
                        options: vec!["dimension".into(), "through_all".into()],
                    },
                ],
            ),
            command_definition(
                "partdesign.edit_pad",
                selected_is_pad && selected_is_operable,
                vec![
                    CommandArgumentDefinition {
                        argument_id: "length_mm".into(),
                        label: "Pad length".into(),
                        value_type: "quantity".into(),
                        required: true,
                        default_value: Some(format!("{:.2}", selected_length_mm.unwrap_or(12.0))),
                        placeholder: Some("12.00".into()),
                        unit: Some("mm".into()),
                        options: vec![],
                    },
                    CommandArgumentDefinition {
                        argument_id: "midplane".into(),
                        label: "Symmetric to plane".into(),
                        value_type: "boolean".into(),
                        required: true,
                        default_value: Some(selected_midplane.to_string()),
                        placeholder: None,
                        unit: None,
                        options: vec!["false".into(), "true".into()],
                    },
                ],
            ),
            command_definition(
                "partdesign.edit_pocket",
                selected_is_pocket && selected_is_operable,
                vec![
                    CommandArgumentDefinition {
                        argument_id: "depth_mm".into(),
                        label: "Pocket depth".into(),
                        value_type: "quantity".into(),
                        required: true,
                        default_value: Some(format!("{:.2}", selected_length_mm.unwrap_or(8.0))),
                        placeholder: Some("8.00".into()),
                        unit: Some("mm".into()),
                        options: vec![],
                    },
                    CommandArgumentDefinition {
                        argument_id: "extent_mode".into(),
                        label: "Extent mode".into(),
                        value_type: "enum".into(),
                        required: true,
                        default_value: Some(selected_extent_mode.clone()),
                        placeholder: None,
                        unit: None,
                        options: vec!["dimension".into(), "through_all".into()],
                    },
                ],
            ),
        ]);
    }

    commands.extend([
        command_definition("history.rollback_here", selected_is_feature, vec![]),
        command_definition("history.resume_full", history_marker_active, vec![]),
        command_definition("model.toggle_suppression", selected_is_feature, vec![]),
        command_definition("document.undo", can_undo, vec![]),
        command_definition("document.redo", can_redo, vec![]),
    ]);

    CommandCatalogResponse {
        document_id: document_id.to_string(),
        workbench: workbench_state_from_bridge(snapshot),
        commands,
    }
}

pub fn task_panel_from_bridge(
    snapshot: &BridgeDocumentSnapshot,
    document_id: &str,
    selected_object_id: Option<&str>,
    selected_length_mm: Option<f32>,
    can_undo: bool,
    can_redo: bool,
) -> TaskPanelResponse {
    let workbench_id = normalize_workbench_id(&snapshot.workbench);
    let selected_node = selected_object_id.and_then(|object_id| find_bridge_object(snapshot, object_id));
    let selected_state = selected_node.map(|node| bridge_object_state(snapshot, node));
    if workbench_id != "partdesign" {
        let mut suggested_commands = vec!["document.recompute".into(), "document.save".into()];
        if selected_object_id.is_some() {
            suggested_commands.insert(0, "selection.focus".into());
        }
        if snapshot.history_marker.is_some() {
            suggested_commands.push("history.resume_full".into());
        }
        if selected_object_id
            .and_then(|object_id| find_bridge_object(snapshot, object_id))
            .map(|node| node.object_id != "body-001")
            .unwrap_or(false)
        {
            suggested_commands.push("model.toggle_suppression".into());
        }
        if can_undo {
            suggested_commands.push("document.undo".into());
        }
        if can_redo {
            suggested_commands.push("document.redo".into());
        }

        let (title, description, sections) = match workbench_id.as_str() {
            "sketcher" => {
                let sketch_node = selected_node.filter(|node| node.object_type == "Sketcher::SketchObject");
                (
                    "Sketcher Workspace".into(),
                    sketch_node
                        .map(sketch_workflow_description)
                        .unwrap_or_else(|| {
                            "Sketcher owns the current shell context. Select a sketch to inspect constraints, profile readiness, and plane setup while deeper sketch editing services are being migrated.".into()
                        }),
                    vec![
                        TaskPanelSection {
                            section_id: "sketch_session".into(),
                            title: "Sketch Session".into(),
                            rows: vec![
                                TaskPanelRow {
                                    label: "Active object".into(),
                                    value: selected_node
                                        .map(|node| node.label.clone())
                                        .unwrap_or_else(|| "No sketch selected".into()),
                                    emphasis: true,
                                },
                                TaskPanelRow {
                                    label: "Reference plane".into(),
                                    value: sketch_node
                                        .and_then(|node| node.reference_plane.clone())
                                        .unwrap_or_else(|| "Select a sketch to inspect plane alignment".into()),
                                    emphasis: false,
                                },
                                TaskPanelRow {
                                    label: "Constraint state".into(),
                                    value: sketch_node
                                        .map(sketch_constraint_summary)
                                        .unwrap_or_else(|| "Constraint analysis pending selection".into()),
                                    emphasis: false,
                                },
                                TaskPanelRow {
                                    label: "Profile readiness".into(),
                                    value: sketch_node
                                        .map(sketch_profile_readiness)
                                        .unwrap_or_else(|| "Open a sketch to evaluate profile closure".into()),
                                    emphasis: true,
                                },
                            ],
                        },
                        TaskPanelSection {
                            section_id: "workspace".into(),
                            title: "Workspace".into(),
                            rows: vec![
                                TaskPanelRow {
                                    label: "Shell mode".into(),
                                    value: "Sketch inspection and selection parity".into(),
                                    emphasis: false,
                                },
                                TaskPanelRow {
                                    label: "History".into(),
                                    value: history_marker_label(snapshot),
                                    emphasis: false,
                                },
                                TaskPanelRow {
                                    label: "Next migration focus".into(),
                                    value: "Constraint editing and solver feedback".into(),
                                    emphasis: false,
                                },
                            ],
                        },
                    ],
                )
            }
            "part" => (
                "Part Workspace".into(),
                selected_node
                    .map(|node| {
                        format!(
                            "Part shell context is active. {} is selected while direct modeling commands are still being extracted from the Qt shell.",
                            node.label
                        )
                    })
                    .unwrap_or_else(|| {
                        "Part shell context is active. Use this workspace to inspect document structure, selection state, and viewport presence while direct modeling actions migrate out of Qt.".into()
                    }),
                vec![
                    TaskPanelSection {
                        section_id: "part_workspace".into(),
                        title: "Part Workspace".into(),
                        rows: vec![
                            TaskPanelRow {
                                label: "Active object".into(),
                                value: selected_node
                                    .map(|node| node.label.clone())
                                    .unwrap_or_else(|| "Body".into()),
                                emphasis: true,
                            },
                            TaskPanelRow {
                                label: "Object type".into(),
                                value: selected_node
                                    .map(|node| node.object_type.clone())
                                    .unwrap_or_else(|| "Part::Feature".into()),
                                emphasis: false,
                            },
                            TaskPanelRow {
                                label: "Viewport focus".into(),
                                value: if selected_object_id.is_some() {
                                    "Selection can be centered from the shell".into()
                                } else {
                                    "Pick an object to drive focus".into()
                                },
                                emphasis: false,
                            },
                        ],
                    },
                    TaskPanelSection {
                        section_id: "migration_status".into(),
                        title: "Migration Status".into(),
                        rows: vec![
                            TaskPanelRow {
                                label: "Shell state".into(),
                                value: "Backend-owned sessions, layout, and workbench chrome".into(),
                                emphasis: false,
                            },
                            TaskPanelRow {
                                label: "History".into(),
                                value: history_marker_label(snapshot),
                                emphasis: false,
                            },
                            TaskPanelRow {
                                label: "Next migration focus".into(),
                                value: "Direct solid operations and Boolean command extraction".into(),
                                emphasis: false,
                            },
                        ],
                    },
                ],
            ),
            _ => (
                format!("{} Workspace", workbench_display_name(&workbench_id)),
                format!(
                    "{} owns the active shell context. Modeling commands remain backend-authoritative while dedicated {} tools are still being migrated.",
                    workbench_display_name(&workbench_id),
                    workbench_display_name(&workbench_id)
                ),
                vec![
                    TaskPanelSection {
                        section_id: "workspace".into(),
                        title: "Workspace".into(),
                        rows: vec![
                            TaskPanelRow {
                                label: "Active workbench".into(),
                                value: workbench_display_name(&workbench_id),
                                emphasis: true,
                            },
                            TaskPanelRow {
                                label: "Selection mode".into(),
                                value: "object".into(),
                                emphasis: false,
                            },
                            TaskPanelRow {
                                label: "History".into(),
                                value: history_marker_label(snapshot),
                                emphasis: false,
                            },
                        ],
                    },
                    TaskPanelSection {
                        section_id: "selection".into(),
                        title: "Selection".into(),
                        rows: vec![
                            TaskPanelRow {
                                label: "Active object".into(),
                                value: selected_node
                                    .map(|node| node.label.clone())
                                    .unwrap_or_else(|| "Body".into()),
                                emphasis: true,
                            },
                            TaskPanelRow {
                                label: "Object type".into(),
                                value: selected_node
                                    .map(|node| node.object_type.clone())
                                    .unwrap_or_else(|| "PartDesign::Body".into()),
                                emphasis: false,
                            },
                            TaskPanelRow {
                                label: "Availability".into(),
                                value: selected_state
                                    .as_ref()
                                    .map(|state| {
                                        if state.suppressed {
                                            "Suppressed".into()
                                        } else if state.active {
                                            "Active".into()
                                        } else {
                                            state
                                                .inactive_reason
                                                .clone()
                                                .unwrap_or_else(|| "Inactive".into())
                                        }
                                    })
                                    .unwrap_or_else(|| "Active".into()),
                                emphasis: false,
                            },
                        ],
                    },
                ],
            ),
        };

        return TaskPanelResponse {
            document_id: document_id.to_string(),
            title,
            description,
            sections,
            suggested_commands,
        };
    }

    let (title, description, sections, mut suggested_commands): (
        String,
        String,
        Vec<TaskPanelSection>,
        Vec<String>,
    ) = match selected_object_id {
        Some(selected)
            if selected.starts_with("sketch-")
                && selected_state
                    .as_ref()
                    .map(|state| state.active && !state.suppressed)
                    .unwrap_or(false) =>
        (
            "Sketch Workflow".into(),
            selected_node
                .map(sketch_workflow_description)
                .unwrap_or_else(|| "Sketch state unavailable.".into()),
            vec![
                TaskPanelSection {
                    section_id: "selection".into(),
                    title: "Selection".into(),
                    rows: vec![
                        TaskPanelRow {
                            label: "Active object".into(),
                            value: selected.to_uppercase(),
                            emphasis: true,
                        },
                        TaskPanelRow {
                            label: "Expected next step".into(),
                            value: selected_node
                                .map(sketch_next_step)
                                .unwrap_or_else(|| "Inspect sketch readiness".into()),
                            emphasis: false,
                        },
                        TaskPanelRow {
                            label: "Reference plane".into(),
                            value: selected_node
                                .and_then(|node| node.reference_plane.clone())
                                .unwrap_or_else(|| "XY".into()),
                            emphasis: false,
                        },
                    ],
                },
                TaskPanelSection {
                    section_id: "constraints".into(),
                    title: "Constraints".into(),
                    rows: vec![
                        TaskPanelRow {
                            label: "Constraint state".into(),
                            value: selected_node
                                .map(sketch_constraint_summary)
                                .unwrap_or_else(|| "Unknown sketch state".into()),
                            emphasis: false,
                        },
                        TaskPanelRow {
                            label: "Profile readiness".into(),
                            value: selected_node
                                .map(sketch_profile_readiness)
                                .unwrap_or_else(|| "Profile status unavailable".into()),
                            emphasis: true,
                        },
                        TaskPanelRow {
                            label: "History".into(),
                            value: history_marker_label(snapshot),
                            emphasis: false,
                        },
                    ],
                },
            ],
            vec![
                "partdesign.pad".into(),
                "partdesign.pocket".into(),
                "history.rollback_here".into(),
                "model.toggle_suppression".into(),
                "document.recompute".into(),
            ],
        ),
        Some(selected)
            if selected.starts_with("pad-")
                && selected_state
                    .as_ref()
                    .map(|state| state.active && !state.suppressed)
                    .unwrap_or(false) =>
        (
            "Pad Feature".into(),
            selected_node
                .map(pad_workflow_description)
                .unwrap_or_else(|| "Pad state unavailable.".into()),
            vec![
                TaskPanelSection {
                    section_id: "feature".into(),
                    title: "Feature State".into(),
                    rows: vec![
                        TaskPanelRow {
                            label: "Active feature".into(),
                            value: selected.to_uppercase(),
                            emphasis: true,
                        },
                        TaskPanelRow {
                            label: "Length".into(),
                            value: format!("{:.2} mm", selected_length_mm.unwrap_or(12.0)),
                            emphasis: false,
                        },
                        TaskPanelRow {
                            label: "Symmetric".into(),
                            value: if selected_node.map(|node| node.midplane).unwrap_or(false) {
                                "Enabled".into()
                            } else {
                                "Disabled".into()
                            },
                            emphasis: false,
                        },
                    ],
                },
                TaskPanelSection {
                    section_id: "actions".into(),
                    title: "Suggested Checks".into(),
                    rows: vec![
                        TaskPanelRow {
                            label: "Regeneration".into(),
                            value: "Recompute after edits".into(),
                            emphasis: false,
                        },
                        TaskPanelRow {
                            label: "View".into(),
                            value: selected_node
                                .map(pad_inspection_hint)
                                .unwrap_or_else(|| "Inspect current feature".into()),
                            emphasis: false,
                        },
                        TaskPanelRow {
                            label: "History".into(),
                            value: history_marker_label(snapshot),
                            emphasis: false,
                        },
                    ],
                },
            ],
            vec![
                "partdesign.edit_pad".into(),
                "history.rollback_here".into(),
                "model.toggle_suppression".into(),
                "document.recompute".into(),
                "selection.focus".into(),
                "document.save".into(),
            ],
        ),
        Some(selected)
            if selected.starts_with("pocket-")
                && selected_state
                    .as_ref()
                    .map(|state| state.active && !state.suppressed)
                    .unwrap_or(false) =>
        (
            "Pocket Feature".into(),
            selected_node
                .map(pocket_workflow_description)
                .unwrap_or_else(|| "Pocket state unavailable.".into()),
            vec![
                TaskPanelSection {
                    section_id: "feature".into(),
                    title: "Feature State".into(),
                    rows: vec![
                        TaskPanelRow {
                            label: "Active feature".into(),
                            value: selected.to_uppercase(),
                            emphasis: true,
                        },
                        TaskPanelRow {
                            label: "Depth".into(),
                            value: format!("{:.2} mm", selected_length_mm.unwrap_or(8.0)),
                            emphasis: false,
                        },
                        TaskPanelRow {
                            label: "Extent".into(),
                            value: selected_node
                                .and_then(|node| node.extent_mode.clone())
                                .unwrap_or_else(|| "dimension".into()),
                            emphasis: false,
                        },
                    ],
                },
                TaskPanelSection {
                    section_id: "actions".into(),
                    title: "Suggested Checks".into(),
                    rows: vec![
                        TaskPanelRow {
                            label: "Regeneration".into(),
                            value: "Recompute after cut-depth edits".into(),
                            emphasis: false,
                        },
                        TaskPanelRow {
                            label: "View".into(),
                            value: selected_node
                                .map(pocket_inspection_hint)
                                .unwrap_or_else(|| "Inspect the subtractive region".into()),
                            emphasis: false,
                        },
                        TaskPanelRow {
                            label: "History".into(),
                            value: history_marker_label(snapshot),
                            emphasis: false,
                        },
                    ],
                },
            ],
            vec![
                "partdesign.edit_pocket".into(),
                "history.rollback_here".into(),
                "model.toggle_suppression".into(),
                "document.recompute".into(),
                "selection.focus".into(),
                "document.save".into(),
            ],
        ),
        Some(selected) => {
            let state = selected_state.clone().unwrap_or(FeatureDependencyState {
                active: false,
                suppressed: false,
                inactive_reason: Some("Selected object is not available in the dependency graph.".into()),
            });
            let selected_label = selected_node
                .map(|node| node.label.clone())
                .unwrap_or_else(|| selected.to_uppercase());
            let selected_bridge_node = selected_node.cloned().unwrap_or(asterforge_freecad_bridge::BridgeObjectNode {
                object_id: selected.to_string(),
                label: selected_label.clone(),
                object_type: "App::FeaturePython".into(),
                visibility: "visible".into(),
                length_mm: None,
                constraint_count: None,
                profile_closed: None,
                fully_constrained: None,
                reference_plane: None,
                extent_mode: None,
                midplane: false,
                source_object_id: None,
                sequence_index: None,
                suppressed: state.suppressed,
                children: vec![],
            });

            (
                "Dependency State".into(),
                dependency_workflow_description(&selected_bridge_node, state.inactive_reason.as_deref()),
                vec![TaskPanelSection {
                    section_id: "dependency".into(),
                    title: "Dependency Status".into(),
                    rows: vec![
                        TaskPanelRow {
                            label: "Selected object".into(),
                            value: selected_label,
                            emphasis: true,
                        },
                        TaskPanelRow {
                            label: "State".into(),
                            value: dependency_status_label(&selected_bridge_node),
                            emphasis: true,
                        },
                        TaskPanelRow {
                            label: "Reason".into(),
                            value: dependency_issue_hint(
                                &selected_bridge_node,
                                state.inactive_reason.as_deref(),
                            ),
                            emphasis: false,
                        },
                        TaskPanelRow {
                            label: "History".into(),
                            value: history_marker_label(snapshot),
                            emphasis: false,
                        },
                    ],
                }],
                vec![
                    "history.rollback_here".into(),
                    "history.resume_full".into(),
                    "model.toggle_suppression".into(),
                    "document.recompute".into(),
                ],
            )
        }
        _ => (
            "Body Overview".into(),
            body_workflow_description(snapshot),
            vec![TaskPanelSection {
                section_id: "body".into(),
                title: "Body Status".into(),
                rows: vec![
                    TaskPanelRow {
                        label: "Contained features".into(),
                        value: body_feature_summary(snapshot),
                        emphasis: false,
                    },
                    TaskPanelRow {
                        label: "Recommended next action".into(),
                        value: body_next_step(snapshot),
                        emphasis: true,
                    },
                    TaskPanelRow {
                        label: "History".into(),
                        value: history_marker_label(snapshot),
                        emphasis: false,
                    },
                ],
            }],
            vec![
                "partdesign.new_sketch".into(),
                "history.resume_full".into(),
                "document.recompute".into(),
                "document.save".into(),
            ],
        ),
    };

    if can_undo {
        suggested_commands.push("document.undo".into());
    }
    if can_redo {
        suggested_commands.push("document.redo".into());
    }

    TaskPanelResponse {
        document_id: document_id.to_string(),
        title,
        description,
        sections,
        suggested_commands,
    }
}

pub fn diagnostics_from_bridge(
    snapshot: &BridgeDocumentSnapshot,
    selected_object_id: Option<&str>,
    events: &[BackendEvent],
    bridge_status: &BridgeStatus,
) -> DiagnosticsResponse {
    let history = feature_history_from_bridge(snapshot);
    let selected_node = selected_object_id.and_then(|object_id| find_bridge_object(snapshot, object_id));
    let selected_entry = selected_object_id.and_then(|object_id| {
        history
            .entries
            .iter()
            .find(|entry| entry.object_id == object_id)
    });

    DiagnosticsResponse {
        document_id: snapshot.document_id.clone(),
        summary: DiagnosticsSummary {
            total_features: history.entries.len() as u32,
            suppressed_count: history.entries.iter().filter(|entry| entry.suppressed).count() as u32,
            inactive_count: history
                .entries
                .iter()
                .filter(|entry| !entry.active && !entry.suppressed)
                .count() as u32,
            rolled_back_count: history.entries.iter().filter(|entry| entry.rolled_back).count() as u32,
            viewport_drawable_count: snapshot.viewport.drawables.len() as u32,
            warning_count: events.iter().filter(|event| event.level == "warning").count() as u32,
            error_count: events.iter().filter(|event| event.level == "error").count() as u32,
            history_marker_active: snapshot.history_marker.is_some(),
            worker_mode: bridge_status.worker_mode.clone(),
        },
        selection: DiagnosticsSelection {
            object_id: selected_object_id.map(ToOwned::to_owned),
            object_label: selected_node.map(|node| node.label.clone()),
            object_type: selected_node.map(|node| node.object_type.clone()),
            model_state: selected_entry
                .map(|entry| {
                    if entry.suppressed {
                        "suppressed".into()
                    } else if entry.rolled_back {
                        "rolled_back".into()
                    } else if entry.active {
                        "active".into()
                    } else {
                        "inactive".into()
                    }
                })
                .unwrap_or_else(|| "context".into()),
            dependency_note: selected_entry
                .and_then(|entry| entry.inactive_reason.clone())
                .unwrap_or_else(|| "Resolved".into()),
            visible_in_viewport: selected_object_id
                .map(|object_id| {
                    snapshot
                        .viewport
                        .drawables
                        .iter()
                        .any(|drawable| drawable.object_id == object_id)
                })
                .unwrap_or(false),
        },
        recent_signals: events
            .iter()
            .take(4)
            .map(|event| DiagnosticSignal {
                level: event.level.clone(),
                title: event.topic.replace('_', " "),
                detail: event.message.clone(),
            })
            .collect(),
    }
}

pub fn selection_state_from_bridge(
    snapshot: &BridgeDocumentSnapshot,
    selected_object_id: &str,
    current_mode: &str,
) -> SelectionStateResponse {
    let selected_node = find_bridge_object(snapshot, selected_object_id)
        .or_else(|| snapshot.roots.first())
        .expect("bridge snapshot should always include at least one root object");

    let selectable_modes = [
        (
            "object",
            "Object",
            "Select any backend-published object in the document tree.",
        ),
        (
            "body",
            "Bodies",
            "Focus body containers when driving high-level PartDesign workflow steps.",
        ),
        (
            "sketch",
            "Sketches",
            "Jump between sketch definitions and profile-authoring states.",
        ),
        (
            "feature",
            "Features",
            "Select downstream PartDesign features such as pads and pockets.",
        ),
    ];

    SelectionStateResponse {
        document_id: snapshot.document_id.clone(),
        current_mode: current_mode.to_string(),
        selected_object_id: selected_node.object_id.clone(),
        selected_object_label: selected_node.label.clone(),
        selected_object_type: selected_node.object_type.clone(),
        available_modes: selectable_modes
            .into_iter()
            .map(|(mode_id, label, description)| {
                let object_count = selectable_object_ids_for_mode(snapshot, mode_id).len() as u32;
                SelectionModeOption {
                    mode_id: mode_id.to_string(),
                    label: label.to_string(),
                    description: description.to_string(),
                    enabled: object_count > 0,
                    object_count,
                }
            })
            .collect(),
    }
}

pub fn preselection_state_from_bridge(
    snapshot: &BridgeDocumentSnapshot,
    preselected_object_id: Option<&str>,
    current_mode: &str,
    can_undo: bool,
    can_redo: bool,
) -> PreselectionStateResponse {
    let preselected_node = preselected_object_id.and_then(|object_id| find_bridge_object(snapshot, object_id));
    let selectable = preselected_node
        .map(|node| object_matches_selection_mode(node.object_type.as_str(), current_mode))
        .unwrap_or(false);
    let preselected_state = preselected_node.map(|node| bridge_object_state(snapshot, node));
    let suggested_commands = preselected_object_id
        .filter(|_| selectable)
        .map(|object_id| {
            task_panel_from_bridge(
                snapshot,
                &snapshot.document_id,
                Some(object_id),
                find_pad_length_mm(snapshot, object_id),
                can_undo,
                can_redo,
            )
            .suggested_commands
        })
        .unwrap_or_default();

    PreselectionStateResponse {
        document_id: snapshot.document_id.clone(),
        current_mode: current_mode.to_string(),
        object_id: preselected_node.map(|node| node.object_id.clone()),
        object_label: preselected_node.map(|node| node.label.clone()),
        object_type: preselected_node.map(|node| node.object_type.clone()),
        selectable,
        model_state: match preselected_state.as_ref() {
            Some(state) if state.suppressed => "suppressed".into(),
            Some(state) if state.active => "active".into(),
            Some(_) => "inactive".into(),
            None => "none".into(),
        },
        dependency_note: preselected_state
            .and_then(|state| state.inactive_reason)
            .unwrap_or_else(|| "Resolved".into()),
        suggested_commands,
        detail: match preselected_node {
            Some(node) if selectable => {
                format!("Preselection candidate {} is valid for {} mode.", node.label, current_mode)
            }
            Some(node) => format!(
                "Candidate {} is filtered out by the active {} mode.",
                node.label, current_mode
            ),
            None => "No preselection candidate is currently active.".into(),
        },
    }
}

fn find_bridge_object<'a>(
    snapshot: &'a BridgeDocumentSnapshot,
    object_id: &str,
) -> Option<&'a asterforge_freecad_bridge::BridgeObjectNode> {
    snapshot
        .roots
        .iter()
        .flat_map(|root| std::iter::once(root).chain(root.children.iter()))
        .find(|node| node.object_id == object_id)
}