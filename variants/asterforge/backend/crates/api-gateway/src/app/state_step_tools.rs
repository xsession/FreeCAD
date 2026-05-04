use crate::domain::{ObjectNode, StepAssemblyNode, StepTessellatedFaceSet, VisibilityState};

use super::state::{STEP_DEFAULT_CAMERA_EYE, STEP_DEFAULT_CAMERA_TARGET};
use super::state_model::flatten_object_nodes;
use super::state_step_nav::{find_step_assembly, step_entity_id_from_object_id};
use super::state_types::{
    StepCacheEntry, StepMeasurementSummary, StepPmiInspectionSummary, StepViewportCameraState,
};

pub(super) fn step_hide_object_subtree(object_tree: &mut [ObjectNode], object_id: &str) -> bool {
    set_step_subtree_visibility(object_tree, object_id, VisibilityState::Hidden)
}

pub(super) fn step_show_all_objects(object_tree: &mut [ObjectNode]) {
    set_step_visibility_for_all(object_tree, VisibilityState::Visible);
}

pub(super) fn step_isolate_object_subtree(object_tree: &mut [ObjectNode], object_id: &str) -> bool {
    isolate_step_visibility(object_tree, object_id)
}

pub(super) fn step_selected_object_is_visible(object_tree: &[ObjectNode], object_id: &str) -> bool {
    find_step_object_node(object_tree, object_id)
        .map(|node| !matches!(node.visibility, VisibilityState::Hidden))
        .unwrap_or(false)
}

pub(super) fn step_measurement_for_selection(
    selected_object_id: &str,
    cache: &StepCacheEntry,
) -> Option<StepMeasurementSummary> {
    let entity_id = step_entity_id_from_object_id(selected_object_id)?;
    let assembly = find_step_assembly(entity_id, &cache.scene_bundle.assemblies)?;
    let representation_ids = collect_step_representation_ids(assembly);
    let representations: Vec<&StepTessellatedFaceSet> = cache
        .scene_bundle
        .tessellated_representations
        .iter()
        .filter(|representation| representation_ids.iter().any(|id| id == &representation.representation_id))
        .collect();
    if representations.is_empty() {
        return None;
    }

    let mut min_x = f32::INFINITY;
    let mut min_y = f32::INFINITY;
    let mut min_z = f32::INFINITY;
    let mut max_x = f32::NEG_INFINITY;
    let mut max_y = f32::NEG_INFINITY;
    let mut max_z = f32::NEG_INFINITY;

    for representation in &representations {
        let mut index = 0usize;
        while index + 2 < representation.positions.len() {
            let x = representation.positions[index];
            let y = representation.positions[index + 1];
            let z = representation.positions[index + 2];
            min_x = min_x.min(x);
            min_y = min_y.min(y);
            min_z = min_z.min(z);
            max_x = max_x.max(x);
            max_y = max_y.max(y);
            max_z = max_z.max(z);
            index += 3;
        }
    }

    let annotation_count = cache
        .scene_bundle
        .semantic_pmi
        .iter()
        .filter(|annotation| assembly.pmi_annotation_ids.iter().any(|id| id == &annotation.annotation_id))
        .count();

    Some(StepMeasurementSummary {
        object_id: selected_object_id.into(),
        label: assembly.label.clone(),
        span_x: (max_x - min_x).max(0.0),
        span_y: (max_y - min_y).max(0.0),
        span_z: (max_z - min_z).max(0.0),
        representation_count: representations.len(),
        annotation_count,
    })
}

pub(super) fn step_focus_camera_for_selection(
    selected_object_id: &str,
    cache: &StepCacheEntry,
) -> Option<StepViewportCameraState> {
    let entity_id = step_entity_id_from_object_id(selected_object_id)?;
    let assembly = find_step_assembly(entity_id, &cache.scene_bundle.assemblies)?;
    let representation_ids = collect_step_representation_ids(assembly);
    let representations: Vec<&StepTessellatedFaceSet> = cache
        .scene_bundle
        .tessellated_representations
        .iter()
        .filter(|representation| representation_ids.iter().any(|id| id == &representation.representation_id))
        .collect();
    if representations.is_empty() {
        return None;
    }

    let mut min_x = f32::INFINITY;
    let mut min_y = f32::INFINITY;
    let mut min_z = f32::INFINITY;
    let mut max_x = f32::NEG_INFINITY;
    let mut max_y = f32::NEG_INFINITY;
    let mut max_z = f32::NEG_INFINITY;
    let mut point_count = 0usize;

    for representation in &representations {
        let mut index = 0usize;
        while index + 2 < representation.positions.len() {
            let x = representation.positions[index];
            let y = representation.positions[index + 1];
            let z = representation.positions[index + 2];
            min_x = min_x.min(x);
            min_y = min_y.min(y);
            min_z = min_z.min(z);
            max_x = max_x.max(x);
            max_y = max_y.max(y);
            max_z = max_z.max(z);
            point_count += 1;
            index += 3;
        }
    }

    if point_count == 0 {
        return None;
    }

    let center = [
        (min_x + max_x) / 2.0,
        (min_y + max_y) / 2.0,
        (min_z + max_z) / 2.0,
    ];
    let vector = [
        STEP_DEFAULT_CAMERA_EYE[0] - STEP_DEFAULT_CAMERA_TARGET[0],
        STEP_DEFAULT_CAMERA_EYE[1] - STEP_DEFAULT_CAMERA_TARGET[1],
        STEP_DEFAULT_CAMERA_EYE[2] - STEP_DEFAULT_CAMERA_TARGET[2],
    ];
    let vector_length = (vector[0] * vector[0] + vector[1] * vector[1] + vector[2] * vector[2]).sqrt();
    let direction = if vector_length > f32::EPSILON {
        [
            vector[0] / vector_length,
            vector[1] / vector_length,
            vector[2] / vector_length,
        ]
    } else {
        [0.51214755, 0.42678964, 0.7682213]
    };
    let half_diagonal =
        ((max_x - min_x).powi(2) + (max_y - min_y).powi(2) + (max_z - min_z).powi(2)).sqrt() / 2.0;
    let focus_distance = vector_length.max(half_diagonal * 2.6).max(2.0);

    Some(StepViewportCameraState {
        eye: [
            center[0] + direction[0] * focus_distance,
            center[1] + direction[1] * focus_distance,
            center[2] + direction[2] * focus_distance,
        ],
        target: center,
    })
}

pub(super) fn step_viewport_camera_for_preset(
    camera: Option<&StepViewportCameraState>,
    preset: &str,
) -> Option<StepViewportCameraState> {
    let baseline = camera.cloned().unwrap_or_else(step_default_viewport_camera_state);
    let direction = step_camera_direction_for_preset(preset)?;
    let distance = step_camera_distance(&baseline.eye, &baseline.target).max(2.0);

    Some(StepViewportCameraState {
        eye: [
            baseline.target[0] + direction[0] * distance,
            baseline.target[1] + direction[1] * distance,
            baseline.target[2] + direction[2] * distance,
        ],
        target: baseline.target,
    })
}

pub(super) fn step_reset_viewport_camera() -> StepViewportCameraState {
    step_default_viewport_camera_state()
}

pub(super) fn step_fit_all_viewport_camera(
    cache: &StepCacheEntry,
    object_tree: &[ObjectNode],
    camera: Option<&StepViewportCameraState>,
) -> Option<StepViewportCameraState> {
    let visible_entity_ids: Vec<u64> = flatten_object_nodes(object_tree)
        .into_iter()
        .filter(|node| !matches!(node.visibility, VisibilityState::Hidden))
        .filter_map(|node| step_entity_id_from_object_id(&node.object_id))
        .collect();

    let representations: Vec<&StepTessellatedFaceSet> = cache
        .scene_bundle
        .tessellated_representations
        .iter()
        .filter(|representation| visible_entity_ids.contains(&representation.entity_id))
        .collect();
    let (center, half_diagonal) = step_camera_frame_from_representations(&representations)?;

    let baseline = camera.cloned().unwrap_or_else(step_default_viewport_camera_state);
    let vector = [
        baseline.eye[0] - baseline.target[0],
        baseline.eye[1] - baseline.target[1],
        baseline.eye[2] - baseline.target[2],
    ];
    let vector_length = (vector[0] * vector[0] + vector[1] * vector[1] + vector[2] * vector[2]).sqrt();
    let direction = if vector_length > f32::EPSILON {
        [
            vector[0] / vector_length,
            vector[1] / vector_length,
            vector[2] / vector_length,
        ]
    } else {
        [0.51214755, 0.42678964, 0.7682213]
    };
    let focus_distance = vector_length.max(half_diagonal * 2.6).max(2.0);

    Some(StepViewportCameraState {
        eye: [
            center[0] + direction[0] * focus_distance,
            center[1] + direction[1] * focus_distance,
            center[2] + direction[2] * focus_distance,
        ],
        target: center,
    })
}

pub(super) fn step_pmi_inspection_for_selection(
    selected_object_id: &str,
    cache: &StepCacheEntry,
    object_tree: &[ObjectNode],
) -> Option<StepPmiInspectionSummary> {
    let entity_id = step_entity_id_from_object_id(selected_object_id)?;
    let annotations: Vec<crate::domain::StepPmiAnnotation> = cache
        .scene_bundle
        .semantic_pmi
        .iter()
        .filter(|annotation| annotation.target_entity_ids.contains(&entity_id))
        .cloned()
        .collect();
    if annotations.is_empty() {
        return None;
    }

    let label = find_step_object_node(object_tree, selected_object_id)
        .map(|node| node.label.clone())
        .unwrap_or_else(|| selected_object_id.into());

    Some(StepPmiInspectionSummary {
        object_id: selected_object_id.into(),
        label,
        entity_id,
        annotations,
    })
}

pub(super) fn hidden_step_object_count(object_tree: &[ObjectNode]) -> usize {
    flatten_object_nodes(object_tree)
        .into_iter()
        .filter(|node| matches!(node.visibility, VisibilityState::Hidden))
        .count()
}

fn step_default_viewport_camera_state() -> StepViewportCameraState {
    StepViewportCameraState {
        eye: STEP_DEFAULT_CAMERA_EYE,
        target: STEP_DEFAULT_CAMERA_TARGET,
    }
}

fn step_camera_distance(eye: &[f32; 3], target: &[f32; 3]) -> f32 {
    let dx = eye[0] - target[0];
    let dy = eye[1] - target[1];
    let dz = eye[2] - target[2];
    (dx * dx + dy * dy + dz * dz).sqrt()
}

fn step_camera_frame_from_representations(
    representations: &[&StepTessellatedFaceSet],
) -> Option<([f32; 3], f32)> {
    if representations.is_empty() {
        return None;
    }

    let mut min_x = f32::INFINITY;
    let mut min_y = f32::INFINITY;
    let mut min_z = f32::INFINITY;
    let mut max_x = f32::NEG_INFINITY;
    let mut max_y = f32::NEG_INFINITY;
    let mut max_z = f32::NEG_INFINITY;
    let mut point_count = 0usize;

    for representation in representations {
        let mut index = 0usize;
        while index + 2 < representation.positions.len() {
            let x = representation.positions[index];
            let y = representation.positions[index + 1];
            let z = representation.positions[index + 2];
            min_x = min_x.min(x);
            min_y = min_y.min(y);
            min_z = min_z.min(z);
            max_x = max_x.max(x);
            max_y = max_y.max(y);
            max_z = max_z.max(z);
            point_count += 1;
            index += 3;
        }
    }

    if point_count == 0 {
        return None;
    }

    let center = [
        (min_x + max_x) / 2.0,
        (min_y + max_y) / 2.0,
        (min_z + max_z) / 2.0,
    ];
    let half_diagonal =
        ((max_x - min_x).powi(2) + (max_y - min_y).powi(2) + (max_z - min_z).powi(2)).sqrt() / 2.0;
    Some((center, half_diagonal))
}

fn step_camera_direction_for_preset(preset: &str) -> Option<[f32; 3]> {
    match preset {
        "iso" => Some(normalize_step_camera_direction([1.0, 1.0, 1.0])),
        "front" => Some([0.0, 0.0, 1.0]),
        "back" => Some([0.0, 0.0, -1.0]),
        "right" => Some([1.0, 0.0, 0.0]),
        "left" => Some([-1.0, 0.0, 0.0]),
        "top" => Some([0.0, 1.0, 0.0]),
        "bottom" => Some([0.0, -1.0, 0.0]),
        _ => None,
    }
}

fn normalize_step_camera_direction(direction: [f32; 3]) -> [f32; 3] {
    let length = (direction[0] * direction[0]
        + direction[1] * direction[1]
        + direction[2] * direction[2])
        .sqrt();
    if length <= f32::EPSILON {
        [0.0, 0.0, 1.0]
    } else {
        [
            direction[0] / length,
            direction[1] / length,
            direction[2] / length,
        ]
    }
}

fn collect_step_representation_ids(assembly: &StepAssemblyNode) -> Vec<String> {
    let mut ids = assembly.tessellated_representation_ids.clone();
    for child in &assembly.children {
        ids.extend(collect_step_representation_ids(child));
    }
    ids.sort();
    ids.dedup();
    ids
}

fn find_step_object_node<'a>(nodes: &'a [ObjectNode], object_id: &str) -> Option<&'a ObjectNode> {
    for node in nodes {
        if node.object_id == object_id {
            return Some(node);
        }
        if let Some(found) = find_step_object_node(&node.children, object_id) {
            return Some(found);
        }
    }
    None
}

fn set_step_visibility_for_all(nodes: &mut [ObjectNode], visibility: VisibilityState) {
    for node in nodes {
        node.visibility = visibility.clone();
        set_step_visibility_for_all(&mut node.children, visibility.clone());
    }
}

fn set_step_subtree_visibility(
    nodes: &mut [ObjectNode],
    object_id: &str,
    visibility: VisibilityState,
) -> bool {
    for node in nodes {
        if node.object_id == object_id {
            node.visibility = visibility.clone();
            set_step_visibility_for_all(&mut node.children, visibility.clone());
            return true;
        }
        if set_step_subtree_visibility(&mut node.children, object_id, visibility.clone()) {
            return true;
        }
    }
    false
}

fn isolate_step_visibility(nodes: &mut [ObjectNode], object_id: &str) -> bool {
    let mut found = false;
    for node in nodes {
        let child_contains_target = isolate_step_visibility(&mut node.children, object_id);
        if node.object_id == object_id {
            node.visibility = VisibilityState::Visible;
            set_step_visibility_for_all(&mut node.children, VisibilityState::Visible);
            found = true;
        } else if child_contains_target {
            node.visibility = VisibilityState::Inherited;
            found = true;
        } else {
            node.visibility = VisibilityState::Hidden;
            set_step_visibility_for_all(&mut node.children, VisibilityState::Hidden);
        }
    }
    found
}

