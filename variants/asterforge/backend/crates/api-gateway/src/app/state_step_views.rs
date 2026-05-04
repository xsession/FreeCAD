use asterforge_command_core::{command_spec, CommandArgumentDefinition, CommandDefinition};

use super::state::{STEP_DEFAULT_CAMERA_EYE, STEP_DEFAULT_CAMERA_TARGET, STEP_OBJECT_MODE};
use super::state_model::flatten_object_nodes;
use super::state_step_nav::{
    flatten_step_assemblies, step_entity_id_from_object_id, step_entity_object_id,
    step_first_child_object_id, step_parent_object_id,
};
use super::state_step_tools;
use super::state_types::{
    StepCacheEntry, StepMeasurementSummary, StepPmiInspectionSummary, StepViewportCameraState,
};
use crate::domain::{
    BackendEvent, CommandCatalogResponse, DiagnosticsResponse, ObjectNode,
    PreselectionStateResponse, SelectionModeOption, SelectionStateResponse, StepSceneBundle,
    TaskPanelResponse, ViewportResponse,
};

pub(super) fn step_selection_state_response(
    document_id: &str,
    selected_object_id: &str,
    current_mode: &str,
    object_tree: &[ObjectNode],
) -> SelectionStateResponse {
    let nodes = flatten_object_nodes(object_tree);
    let selected_node = nodes
        .iter()
        .find(|node| node.object_id == selected_object_id)
        .copied()
        .or_else(|| nodes.first().copied())
        .expect("STEP tree should contain at least one node");
    let object_count = nodes.len() as u32;

    SelectionStateResponse {
        document_id: document_id.into(),
        current_mode: current_mode.into(),
        selected_object_id: selected_node.object_id.clone(),
        selected_object_label: selected_node.label.clone(),
        selected_object_type: selected_node.object_type.clone(),
        available_modes: vec![
            SelectionModeOption {
                mode_id: "object".into(),
                label: "Object".into(),
                description: "Select parsed STEP entities and assembly nodes.".into(),
                enabled: object_count > 0,
                object_count,
            },
            SelectionModeOption {
                mode_id: "body".into(),
                label: "Bodies".into(),
                description: "Not available for imported STEP topology.".into(),
                enabled: false,
                object_count: 0,
            },
            SelectionModeOption {
                mode_id: "sketch".into(),
                label: "Sketches".into(),
                description: "Not available for imported STEP topology.".into(),
                enabled: false,
                object_count: 0,
            },
            SelectionModeOption {
                mode_id: "feature".into(),
                label: "Features".into(),
                description: "Not available for imported STEP topology.".into(),
                enabled: false,
                object_count: 0,
            },
        ],
    }
}

pub(super) fn step_preselection_state_response(
    document_id: &str,
    preselected_object_id: Option<&str>,
    current_mode: &str,
    cache: &StepCacheEntry,
    object_tree: &[ObjectNode],
) -> PreselectionStateResponse {
    let nodes = flatten_object_nodes(object_tree);
    let preselected = preselected_object_id.and_then(|object_id| {
        nodes.iter().find(|node| node.object_id == object_id).copied()
    });
    let selectable = current_mode == STEP_OBJECT_MODE && preselected.is_some();
    let suggested_commands = preselected
        .and_then(|node| step_entity_id_from_object_id(&node.object_id))
        .map(|entity_id| {
            if cache
                .scene_bundle
                .semantic_pmi
                .iter()
                .any(|annotation| annotation.target_entity_ids.contains(&entity_id))
            {
                vec!["shell.show_report_view".into()]
            } else {
                vec![]
            }
        })
        .unwrap_or_default();

    PreselectionStateResponse {
        document_id: document_id.into(),
        current_mode: current_mode.into(),
        object_id: preselected.map(|node| node.object_id.clone()),
        object_label: preselected.map(|node| node.label.clone()),
        object_type: preselected.map(|node| node.object_type.clone()),
        selectable,
        model_state: if selectable { "parsed".into() } else { "none".into() },
        dependency_note: "Imported STEP topology is read-only in the current shell.".into(),
        suggested_commands,
        detail: preselected
            .map(|node| format!("Parsed STEP node {} is available for inspection.", node.label))
            .unwrap_or_else(|| "No STEP preselection candidate is currently active.".into()),
    }
}

pub(super) fn step_viewport_response(
    document_id: &str,
    selected_object_id: &str,
    cache: &StepCacheEntry,
    object_tree: &[ObjectNode],
    camera: Option<&StepViewportCameraState>,
) -> ViewportResponse {
    ViewportResponse {
        document_id: document_id.into(),
        selected_object_id: selected_object_id.into(),
        scene: crate::domain::ViewportScene {
            camera_eye: camera.map(|camera| camera.eye).unwrap_or(STEP_DEFAULT_CAMERA_EYE),
            camera_target: camera.map(|camera| camera.target).unwrap_or(STEP_DEFAULT_CAMERA_TARGET),
            drawables: cache
                .scene_bundle
                .tessellated_representations
                .iter()
                .filter(|representation| {
                    state_step_tools::step_selected_object_is_visible(
                        object_tree,
                        &step_entity_object_id(representation.entity_id),
                    )
                })
                .map(|representation| step_drawable_from_representation(representation, &cache.scene_bundle))
                .collect(),
        },
    }
}

pub(super) fn step_task_panel_response(
    document_id: &str,
    selected_object_id: &str,
    cache: &StepCacheEntry,
    object_tree: &[ObjectNode],
    inspection: Option<&StepPmiInspectionSummary>,
    measurement: Option<&StepMeasurementSummary>,
) -> TaskPanelResponse {
    let has_parent = step_parent_object_id(selected_object_id, &cache.scene_bundle.assemblies).is_some();
    let has_child = step_first_child_object_id(selected_object_id, &cache.scene_bundle.assemblies).is_some();
    let selected_visible = state_step_tools::step_selected_object_is_visible(object_tree, selected_object_id);
    let hidden_count = state_step_tools::hidden_step_object_count(object_tree);
    let has_pmi = step_entity_id_from_object_id(selected_object_id)
        .map(|entity_id| {
            cache
                .scene_bundle
                .semantic_pmi
                .iter()
                .any(|annotation| annotation.target_entity_ids.contains(&entity_id))
        })
        .unwrap_or(false);
    let selection_matches_inspection = inspection
        .map(|result| result.object_id == selected_object_id)
        .unwrap_or(false);
    let selection_matches_measurement = measurement
        .map(|result| result.object_id == selected_object_id)
        .unwrap_or(false);

    let mut sections = vec![
        crate::domain::TaskPanelSection {
            section_id: "selection".into(),
            title: "Selection".into(),
            rows: vec![
                crate::domain::TaskPanelRow {
                    label: "Active node".into(),
                    value: selected_object_id.into(),
                    emphasis: true,
                },
                crate::domain::TaskPanelRow {
                    label: "Visibility".into(),
                    value: if selected_visible { "Visible".into() } else { "Hidden".into() },
                    emphasis: selected_visible,
                },
            ],
        },
        crate::domain::TaskPanelSection {
            section_id: "pmi".into(),
            title: "PMI".into(),
            rows: if let Some(result) = inspection.filter(|_| selection_matches_inspection) {
                vec![
                    crate::domain::TaskPanelRow {
                        label: "Inspected node".into(),
                        value: result.label.clone(),
                        emphasis: true,
                    },
                    crate::domain::TaskPanelRow {
                        label: "STEP entity".into(),
                        value: format!("#{}", result.entity_id),
                        emphasis: false,
                    },
                    crate::domain::TaskPanelRow {
                        label: "Annotations".into(),
                        value: result.annotations.len().to_string(),
                        emphasis: true,
                    },
                ]
            } else if has_pmi {
                vec![crate::domain::TaskPanelRow {
                    label: "semantic_pmi".into(),
                    value: "PMI is available for this selection. Run Inspect PMI to load the drill-down.".into(),
                    emphasis: false,
                }]
            } else {
                vec![crate::domain::TaskPanelRow {
                    label: "semantic_pmi".into(),
                    value: "No PMI attached to the current selection.".into(),
                    emphasis: false,
                }]
            },
        },
    ];

    if let Some(result) = inspection.filter(|_| selection_matches_inspection) {
        for (index, annotation) in result.annotations.iter().enumerate() {
            sections.push(crate::domain::TaskPanelSection {
                section_id: format!("pmi-annotation-{}", index + 1),
                title: format!("PMI Annotation {}", index + 1),
                rows: vec![
                    crate::domain::TaskPanelRow {
                        label: "Type".into(),
                        value: annotation.semantic_type.clone(),
                        emphasis: true,
                    },
                    crate::domain::TaskPanelRow {
                        label: "Text".into(),
                        value: annotation.text.clone(),
                        emphasis: true,
                    },
                    crate::domain::TaskPanelRow {
                        label: "Targets".into(),
                        value: annotation
                            .target_entity_ids
                            .iter()
                            .map(|entity_id| format!("#{}", entity_id))
                            .collect::<Vec<_>>()
                            .join(", "),
                        emphasis: false,
                    },
                    crate::domain::TaskPanelRow {
                        label: "Presentation".into(),
                        value: if annotation.presentation_entity_ids.is_empty() {
                            "None".into()
                        } else {
                            annotation
                                .presentation_entity_ids
                                .iter()
                                .map(|entity_id| format!("#{}", entity_id))
                                .collect::<Vec<_>>()
                                .join(", ")
                        },
                        emphasis: false,
                    },
                ],
            });
        }
    }

    if let Some(result) = measurement.filter(|_| selection_matches_measurement) {
        sections.push(crate::domain::TaskPanelSection {
            section_id: "measurement".into(),
            title: "Measurement".into(),
            rows: vec![
                crate::domain::TaskPanelRow {
                    label: "Measured node".into(),
                    value: result.label.clone(),
                    emphasis: true,
                },
                crate::domain::TaskPanelRow {
                    label: "X span".into(),
                    value: format!("{:.2}", result.span_x),
                    emphasis: true,
                },
                crate::domain::TaskPanelRow {
                    label: "Y span".into(),
                    value: format!("{:.2}", result.span_y),
                    emphasis: true,
                },
                crate::domain::TaskPanelRow {
                    label: "Z span".into(),
                    value: format!("{:.2}", result.span_z),
                    emphasis: true,
                },
                crate::domain::TaskPanelRow {
                    label: "Mesh packets".into(),
                    value: result.representation_count.to_string(),
                    emphasis: false,
                },
                crate::domain::TaskPanelRow {
                    label: "PMI annotations".into(),
                    value: result.annotation_count.to_string(),
                    emphasis: false,
                },
            ],
        });
    }

    TaskPanelResponse {
        document_id: document_id.into(),
        title: "STEP Inspection".into(),
        description: "Imported STEP topology is available for inspection and standards review.".into(),
        sections,
        suggested_commands: [
            has_parent.then(|| "step.select_parent".into()),
            has_child.then(|| "step.select_first_child".into()),
            has_pmi.then(|| "step.inspect_pmi".into()),
            state_step_tools::step_measurement_for_selection(selected_object_id, cache)
                .is_some()
                .then(|| "step.measure_selection".into()),
            selected_visible.then(|| "step.hide_selection".into()),
            (flatten_object_nodes(object_tree).len() > 1).then(|| "step.isolate_selection".into()),
            (hidden_count > 0).then(|| "step.show_all".into()),
            Some("selection.focus".into()),
        ]
        .into_iter()
        .flatten()
        .collect(),
    }
}

pub(super) fn step_shell_inspection_state(
    selected_object_id: &str,
    inspection: Option<&StepPmiInspectionSummary>,
    measurement: Option<&StepMeasurementSummary>,
) -> Option<crate::domain::ShellInspectionState> {
    let step_pmi = inspection
        .filter(|result| result.object_id == selected_object_id)
        .map(step_pmi_overlay_from_inspection);
    let step_measurement = measurement
        .filter(|result| result.object_id == selected_object_id)
        .map(step_measurement_overlay_from_summary);

    if step_pmi.is_none() && step_measurement.is_none() {
        None
    } else {
        Some(crate::domain::ShellInspectionState {
            step_pmi,
            step_measurement,
        })
    }
}

pub(super) fn step_command_catalog_response(
    document_id: &str,
    selected_object_id: &str,
    cache: &StepCacheEntry,
    object_tree: &[ObjectNode],
    measurement: Option<&StepMeasurementSummary>,
) -> CommandCatalogResponse {
    let has_parent = step_parent_object_id(selected_object_id, &cache.scene_bundle.assemblies).is_some();
    let has_child = step_first_child_object_id(selected_object_id, &cache.scene_bundle.assemblies).is_some();
    let selected_visible = state_step_tools::step_selected_object_is_visible(object_tree, selected_object_id);
    let has_pmi = step_entity_id_from_object_id(selected_object_id)
        .map(|entity_id| {
            cache
                .scene_bundle
                .semantic_pmi
                .iter()
                .any(|annotation| annotation.target_entity_ids.contains(&entity_id))
        })
        .unwrap_or(false);
    let object_count = flatten_object_nodes(object_tree).len();
    let hidden_count = state_step_tools::hidden_step_object_count(object_tree);
    let can_measure = state_step_tools::step_measurement_for_selection(selected_object_id, cache).is_some();
    let has_measurement = measurement
        .map(|result| result.object_id == selected_object_id)
        .unwrap_or(false);

    CommandCatalogResponse {
        document_id: document_id.into(),
        workbench: crate::domain::WorkbenchState {
            workbench_id: "step".into(),
            display_name: "STEP Inspection".into(),
            mode: if has_measurement {
                format!("{} imported nodes, live measurement", object_count)
            } else {
                format!("{} imported nodes", object_count)
            },
        },
        commands: vec![
            step_command_definition("selection.focus", true),
            step_command_definition("extensions.refresh_inventory", true),
            step_command_definition("extensions.review_addon_catalog", true),
            step_command_definition("extensions.review_external_workbenches", true),
            step_command_definition_with_arguments(
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
            step_command_definition("step.view_iso", true),
            step_command_definition("step.view_fit_all", true),
            step_command_definition("step.view_reset", true),
            step_command_definition("step.view_front", true),
            step_command_definition("step.view_back", true),
            step_command_definition("step.view_right", true),
            step_command_definition("step.view_left", true),
            step_command_definition("step.view_top", true),
            step_command_definition("step.view_bottom", true),
            step_command_definition("step.select_parent", has_parent),
            step_command_definition("step.select_first_child", has_child),
            step_command_definition("step.inspect_pmi", has_pmi),
            step_command_definition("step.measure_selection", can_measure),
            step_command_definition("step.hide_selection", selected_visible),
            step_command_definition("step.isolate_selection", object_count > 1),
            step_command_definition("step.show_all", hidden_count > 0),
        ],
    }
}

pub(super) fn step_diagnostics_response(
    document_id: &str,
    selected_object_id: &str,
    events: &[BackendEvent],
    worker_mode: &str,
    cache: &StepCacheEntry,
    object_tree: &[ObjectNode],
) -> DiagnosticsResponse {
    let nodes = flatten_object_nodes(object_tree);
    let selected = nodes.iter().find(|node| node.object_id == selected_object_id).copied();

    DiagnosticsResponse {
        document_id: document_id.into(),
        summary: crate::domain::DiagnosticsSummary {
            total_features: cache.document_index.entities.len() as u32,
            suppressed_count: 0,
            inactive_count: 0,
            rolled_back_count: 0,
            viewport_drawable_count: cache.scene_bundle.tessellated_representations.len() as u32,
            warning_count: 0,
            error_count: 0,
            history_marker_active: false,
            worker_mode: worker_mode.into(),
        },
        selection: crate::domain::DiagnosticsSelection {
            object_id: selected.map(|node| node.object_id.clone()),
            object_label: selected.map(|node| node.label.clone()),
            object_type: selected.map(|node| node.object_type.clone()),
            model_state: "parsed".into(),
            dependency_note: "STEP import is read-only in the current shell runtime.".into(),
            visible_in_viewport: state_step_tools::step_selected_object_is_visible(object_tree, selected_object_id),
        },
        recent_signals: events
            .iter()
            .take(4)
            .map(|event| crate::domain::DiagnosticSignal {
                level: event.level.clone(),
                title: event.topic.replace('_', " "),
                detail: event.message.clone(),
            })
            .collect(),
    }
}

fn step_drawable_from_representation(
    representation: &crate::domain::StepTessellatedFaceSet,
    scene: &StepSceneBundle,
) -> crate::domain::ViewportDrawable {
    let points = project_step_points(&representation.positions);
    let paths = step_paths_from_points(&points, &representation.indices);
    let (min_x, max_x, min_y, max_y) = step_bounds_from_points(&points);
    let label = flatten_step_assemblies(&scene.assemblies)
        .into_iter()
        .find(|assembly| assembly.entity_id == representation.entity_id)
        .map(|assembly| assembly.label.clone())
        .unwrap_or_else(|| format!("STEP #{}", representation.entity_id));

    crate::domain::ViewportDrawable {
        object_id: step_entity_object_id(representation.entity_id),
        label,
        kind: "step-brep".into(),
        accent: "#7bd6ff".into(),
        bounds: crate::domain::ViewportBounds {
            x: min_x,
            y: min_y,
            width: (max_x - min_x).max(1.0),
            height: (max_y - min_y).max(1.0),
        },
        paths,
    }
}

fn step_pmi_overlay_from_inspection(
    inspection: &StepPmiInspectionSummary,
) -> crate::domain::StepPmiInspectionOverlay {
    crate::domain::StepPmiInspectionOverlay {
        object_id: inspection.object_id.clone(),
        label: inspection.label.clone(),
        entity_id: inspection.entity_id,
        target_object_ids: inspection
            .annotations
            .iter()
            .flat_map(|annotation| annotation.target_entity_ids.iter().copied())
            .map(step_entity_object_id)
            .collect::<Vec<_>>(),
        presentation_object_ids: inspection
            .annotations
            .iter()
            .flat_map(|annotation| annotation.presentation_entity_ids.iter().copied())
            .map(step_entity_object_id)
            .collect::<Vec<_>>(),
        annotation_lines: inspection
            .annotations
            .iter()
            .map(|annotation| format!("{}: {}", annotation.semantic_type, annotation.text))
            .collect(),
    }
}

fn step_measurement_overlay_from_summary(
    measurement: &StepMeasurementSummary,
) -> crate::domain::StepMeasurementOverlay {
    crate::domain::StepMeasurementOverlay {
        object_id: measurement.object_id.clone(),
        label: measurement.label.clone(),
        span_x: measurement.span_x,
        span_y: measurement.span_y,
        span_z: measurement.span_z,
        representation_count: measurement.representation_count,
        annotation_count: measurement.annotation_count,
    }
}

fn step_command_definition(command_id: &str, enabled: bool) -> CommandDefinition {
    step_command_definition_with_arguments(command_id, enabled, vec![])
}

fn step_command_definition_with_arguments(
    command_id: &str,
    enabled: bool,
    arguments: Vec<CommandArgumentDefinition>,
) -> CommandDefinition {
    let spec = command_spec(command_id).expect("STEP command spec should exist");
    CommandDefinition {
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
    }
}

fn project_step_points(positions: &[f32]) -> Vec<(f32, f32)> {
    let mut points = Vec::new();
    let mut index = 0usize;
    while index + 2 < positions.len() {
        let x = positions[index];
        let y = positions[index + 1];
        let z = positions[index + 2];
        points.push((18.0 + x * 22.0 + z * 6.0, 80.0 - y * 20.0 - z * 7.0));
        index += 3;
    }
    points
}

fn step_paths_from_points(points: &[(f32, f32)], indices: &[u32]) -> Vec<String> {
    let mut paths = Vec::new();
    let mut index = 0usize;
    while index + 2 < indices.len() {
        let Some(a) = points.get(indices[index] as usize) else {
            index += 3;
            continue;
        };
        let Some(b) = points.get(indices[index + 1] as usize) else {
            index += 3;
            continue;
        };
        let Some(c) = points.get(indices[index + 2] as usize) else {
            index += 3;
            continue;
        };
        paths.push(format!(
            "M {:.2} {:.2} L {:.2} {:.2} L {:.2} {:.2} Z",
            a.0, a.1, b.0, b.1, c.0, c.1
        ));
        index += 3;
    }
    paths
}

fn step_bounds_from_points(points: &[(f32, f32)]) -> (f32, f32, f32, f32) {
    let mut min_x = 20.0;
    let mut min_y = 20.0;
    let mut max_x = 80.0;
    let mut max_y = 80.0;
    if let Some(first) = points.first() {
        min_x = first.0;
        min_y = first.1;
        max_x = first.0;
        max_y = first.1;
        for point in points.iter().skip(1) {
            min_x = min_x.min(point.0);
            min_y = min_y.min(point.1);
            max_x = max_x.max(point.0);
            max_y = max_y.max(point.1);
        }
    }
    (min_x, max_x, min_y, max_y)
}