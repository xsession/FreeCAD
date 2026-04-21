use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BridgeCapabilities {
    pub fcstd_open: bool,
    pub object_tree_fetch: bool,
    pub property_fetch: bool,
    pub tessellation_fetch: bool,
    pub command_execution: bool,
}

impl Default for BridgeCapabilities {
    fn default() -> Self {
        Self {
            fcstd_open: true,
            object_tree_fetch: true,
            property_fetch: true,
            tessellation_fetch: true,
            command_execution: true,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BridgeStatus {
    pub worker_mode: String,
    pub freecad_runtime_detected: bool,
    pub capabilities: BridgeCapabilities,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BridgeDocumentSnapshot {
    pub document_id: String,
    pub display_name: String,
    pub workbench: String,
    pub file_path: Option<String>,
    pub dirty: bool,
    pub history_marker: Option<u32>,
    pub roots: Vec<BridgeObjectNode>,
    pub selected_object_id: String,
    pub viewport: ViewportSnapshot,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BridgeObjectNode {
    pub object_id: String,
    pub label: String,
    pub object_type: String,
    pub visibility: String,
    pub length_mm: Option<f32>,
    pub constraint_count: Option<u32>,
    pub profile_closed: Option<bool>,
    pub fully_constrained: Option<bool>,
    pub reference_plane: Option<String>,
    pub extent_mode: Option<String>,
    pub midplane: bool,
    pub source_object_id: Option<String>,
    pub sequence_index: Option<u32>,
    pub suppressed: bool,
    pub children: Vec<BridgeObjectNode>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ViewportSnapshot {
    pub camera: CameraState,
    pub drawables: Vec<DrawableMesh>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CameraState {
    pub eye: [f32; 3],
    pub target: [f32; 3],
    pub up: [f32; 3],
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DrawableMesh {
    pub object_id: String,
    pub label: String,
    pub kind: String,
    pub accent: String,
    pub bounds: Bounds2d,
    pub edges: Vec<Polyline2d>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Bounds2d {
    pub x: f32,
    pub y: f32,
    pub width: f32,
    pub height: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Polyline2d {
    pub points: Vec<Point2d>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Point2d {
    pub x: f32,
    pub y: f32,
}

// ---------------------------------------------------------------------------
// Viewport diffs
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ViewportDiff {
    pub added: Vec<DrawableMesh>,
    pub removed: Vec<String>,
    pub modified: Vec<DrawableMesh>,
    pub camera_changed: bool,
    pub camera: Option<CameraState>,
}

impl ViewportDiff {
    pub fn is_empty(&self) -> bool {
        self.added.is_empty() && self.removed.is_empty() && self.modified.is_empty() && !self.camera_changed
    }
}

/// Compare two viewport snapshots and produce an incremental diff.
pub fn compute_viewport_diff(before: &ViewportSnapshot, after: &ViewportSnapshot) -> ViewportDiff {
    use std::collections::HashMap;

    let before_map: HashMap<&str, &DrawableMesh> = before
        .drawables
        .iter()
        .map(|d| (d.object_id.as_str(), d))
        .collect();

    let after_map: HashMap<&str, &DrawableMesh> = after
        .drawables
        .iter()
        .map(|d| (d.object_id.as_str(), d))
        .collect();

    let mut added = Vec::new();
    let mut removed = Vec::new();
    let mut modified = Vec::new();

    // Detect added & modified
    for (id, after_drawable) in &after_map {
        match before_map.get(id) {
            None => added.push((*after_drawable).clone()),
            Some(before_drawable) => {
                if !drawables_equal(before_drawable, after_drawable) {
                    modified.push((*after_drawable).clone());
                }
            }
        }
    }

    // Detect removed
    for id in before_map.keys() {
        if !after_map.contains_key(id) {
            removed.push(id.to_string());
        }
    }

    let camera_changed = before.camera.eye != after.camera.eye
        || before.camera.target != after.camera.target
        || before.camera.up != after.camera.up;

    ViewportDiff {
        added,
        removed,
        modified,
        camera_changed,
        camera: if camera_changed {
            Some(after.camera.clone())
        } else {
            None
        },
    }
}

fn drawables_equal(a: &DrawableMesh, b: &DrawableMesh) -> bool {
    a.object_id == b.object_id
        && a.label == b.label
        && a.kind == b.kind
        && a.accent == b.accent
        && a.bounds.x == b.bounds.x
        && a.bounds.y == b.bounds.y
        && a.bounds.width == b.bounds.width
        && a.bounds.height == b.bounds.height
        && a.edges.len() == b.edges.len()
        && a.edges.iter().zip(b.edges.iter()).all(|(ea, eb)| {
            ea.points.len() == eb.points.len()
                && ea
                    .points
                    .iter()
                    .zip(eb.points.iter())
                    .all(|(pa, pb)| pa.x == pb.x && pa.y == pb.y)
        })
}

// ---------------------------------------------------------------------------
// Undo / redo
// ---------------------------------------------------------------------------

/// Manages an undo/redo stack around a `BridgeDocumentSnapshot`.
#[derive(Debug, Clone)]
pub struct UndoStack {
    undo: Vec<BridgeDocumentSnapshot>,
    redo: Vec<BridgeDocumentSnapshot>,
    max_depth: usize,
}

impl UndoStack {
    pub fn new(max_depth: usize) -> Self {
        Self {
            undo: Vec::new(),
            redo: Vec::new(),
            max_depth,
        }
    }

    /// Snapshot the current state before a mutation.
    pub fn push(&mut self, snapshot: &BridgeDocumentSnapshot) {
        if self.undo.len() >= self.max_depth {
            self.undo.remove(0);
        }
        self.undo.push(snapshot.clone());
        self.redo.clear();
    }

    /// Undo: restore the previous state, pushing `current` onto the redo stack.
    pub fn undo(&mut self, current: &BridgeDocumentSnapshot) -> Option<BridgeDocumentSnapshot> {
        let previous = self.undo.pop()?;
        self.redo.push(current.clone());
        Some(previous)
    }

    /// Redo: restore the next state, pushing `current` onto the undo stack.
    pub fn redo(&mut self, current: &BridgeDocumentSnapshot) -> Option<BridgeDocumentSnapshot> {
        let next = self.redo.pop()?;
        self.undo.push(current.clone());
        Some(next)
    }

    pub fn can_undo(&self) -> bool {
        !self.undo.is_empty()
    }

    pub fn can_redo(&self) -> bool {
        !self.redo.is_empty()
    }

    pub fn undo_depth(&self) -> usize {
        self.undo.len()
    }

    pub fn redo_depth(&self) -> usize {
        self.redo.len()
    }
}

// ---------------------------------------------------------------------------
// Bridge status
// ---------------------------------------------------------------------------

pub fn bridge_status() -> BridgeStatus {
    BridgeStatus {
        worker_mode: "mock-freecad-worker".into(),
        freecad_runtime_detected: false,
        capabilities: BridgeCapabilities::default(),
    }
}

pub fn open_document_snapshot(file_path: Option<&str>) -> BridgeDocumentSnapshot {
    let normalized_path = file_path.unwrap_or("C:/models/actuator-mount.FCStd").replace('\\', "/");
    let display_name = normalized_path
        .rsplit('/')
        .next()
        .unwrap_or("Actuator Mount.FCStd")
        .trim_end_matches(".FCStd")
        .to_string();

    let mut snapshot = BridgeDocumentSnapshot {
        document_id: "doc-demo-001".into(),
        display_name: if display_name.is_empty() {
            "Actuator Mount".into()
        } else {
            display_name
        },
        workbench: "PartDesign".into(),
        file_path: Some(normalized_path),
        dirty: false,
        history_marker: None,
        roots: vec![BridgeObjectNode {
            object_id: "body-001".into(),
            label: "Body".into(),
            object_type: "PartDesign::Body".into(),
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
            suppressed: false,
            children: vec![
                BridgeObjectNode {
                    object_id: "sketch-001".into(),
                    label: "Sketch".into(),
                    object_type: "Sketcher::SketchObject".into(),
                    visibility: "visible".into(),
                    length_mm: None,
                    constraint_count: Some(6),
                    profile_closed: Some(true),
                    fully_constrained: Some(true),
                    reference_plane: Some("XY".into()),
                    extent_mode: None,
                    midplane: false,
                    source_object_id: None,
                    sequence_index: Some(1),
                    suppressed: false,
                    children: vec![],
                },
                BridgeObjectNode {
                    object_id: "pad-001".into(),
                    label: "Pad".into(),
                    object_type: "PartDesign::Pad".into(),
                    visibility: "visible".into(),
                    length_mm: Some(12.0),
                    constraint_count: None,
                    profile_closed: None,
                    fully_constrained: None,
                    reference_plane: None,
                    extent_mode: Some("dimension".into()),
                    midplane: false,
                    source_object_id: Some("sketch-001".into()),
                    sequence_index: Some(2),
                    suppressed: false,
                    children: vec![],
                },
            ],
        }],
        selected_object_id: "pad-001".into(),
        viewport: ViewportSnapshot {
            camera: CameraState {
                eye: [10.0, 8.0, 12.0],
                target: [0.0, 0.0, 0.0],
                up: [0.0, 0.0, 1.0],
            },
            drawables: Vec::new(),
        },
    };
    rebuild_viewport(&mut snapshot);
    snapshot
}

pub fn create_pad_from_selected_sketch(
    snapshot: &mut BridgeDocumentSnapshot,
    length_mm: Option<f32>,
    extent_mode: Option<&str>,
    midplane: bool,
) -> Option<String> {
    if !snapshot.selected_object_id.starts_with("sketch-") {
        return None;
    }

    let body = snapshot.roots.first_mut()?;
    let next_index = body
        .children
        .iter()
        .filter(|child| child.object_type == "PartDesign::Pad")
        .count() + 1;

    let object_id = format!("pad-{:03}", next_index);
    let label = if next_index == 1 {
        "Pad001".to_string()
    } else {
        format!("Pad{:03}", next_index)
    };

    body.children.push(BridgeObjectNode {
        object_id: object_id.clone(),
        label,
        object_type: "PartDesign::Pad".into(),
        visibility: "visible".into(),
        length_mm: Some(length_mm.unwrap_or(12.0)),
        constraint_count: None,
        profile_closed: None,
        fully_constrained: None,
        reference_plane: None,
        extent_mode: Some(normalize_extent_mode(extent_mode, "dimension")),
        midplane,
        source_object_id: Some(snapshot.selected_object_id.clone()),
        sequence_index: Some(next_sequence_index(body)),
        suppressed: false,
        children: vec![],
    });

    snapshot.history_marker = None;
    snapshot.selected_object_id = object_id.clone();
    snapshot.dirty = true;
    rebuild_viewport(snapshot);
    Some(object_id)
}

pub fn create_pocket_from_selected_sketch(
    snapshot: &mut BridgeDocumentSnapshot,
    depth_mm: Option<f32>,
    extent_mode: Option<&str>,
) -> Option<String> {
    if !snapshot.selected_object_id.starts_with("sketch-") {
        return None;
    }

    let body = snapshot.roots.first_mut()?;
    let next_index = body
        .children
        .iter()
        .filter(|child| child.object_type == "PartDesign::Pocket")
        .count()
        + 1;

    let object_id = format!("pocket-{:03}", next_index);
    let label = if next_index == 1 {
        "Pocket001".to_string()
    } else {
        format!("Pocket{:03}", next_index)
    };

    body.children.push(BridgeObjectNode {
        object_id: object_id.clone(),
        label,
        object_type: "PartDesign::Pocket".into(),
        visibility: "visible".into(),
        length_mm: Some(depth_mm.unwrap_or(8.0)),
        constraint_count: None,
        profile_closed: None,
        fully_constrained: None,
        reference_plane: None,
        extent_mode: Some(normalize_extent_mode(extent_mode, "dimension")),
        midplane: false,
        source_object_id: Some(snapshot.selected_object_id.clone()),
        sequence_index: Some(next_sequence_index(body)),
        suppressed: false,
        children: vec![],
    });

    snapshot.history_marker = None;
    snapshot.selected_object_id = object_id.clone();
    snapshot.dirty = true;
    rebuild_viewport(snapshot);
    Some(object_id)
}

pub fn create_sketch_in_body(
    snapshot: &mut BridgeDocumentSnapshot,
    label: Option<&str>,
    reference_plane: Option<&str>,
) -> Option<String> {
    if snapshot.selected_object_id != "body-001" {
        return None;
    }

    let body = snapshot.roots.first_mut()?;
    let next_index = body
        .children
        .iter()
        .filter(|child| child.object_type == "Sketcher::SketchObject")
        .count()
        + 1;

    let object_id = format!("sketch-{:03}", next_index);
    let requested_label = label.unwrap_or("").trim();
    let reference_plane = normalize_reference_plane(reference_plane, "XY");
    let (constraint_count, profile_closed, fully_constrained) =
        sketch_metadata_for_plane(&reference_plane);
    let label = if requested_label.is_empty() {
        if next_index == 1 {
            "Sketch".to_string()
        } else {
            format!("Sketch{:03}", next_index)
        }
    } else {
        requested_label.to_string()
    };

    body.children.push(BridgeObjectNode {
        object_id: object_id.clone(),
        label,
        object_type: "Sketcher::SketchObject".into(),
        visibility: "visible".into(),
        length_mm: None,
        constraint_count: Some(constraint_count),
        profile_closed: Some(profile_closed),
        fully_constrained: Some(fully_constrained),
        reference_plane: Some(reference_plane),
        extent_mode: None,
        midplane: false,
        source_object_id: None,
        sequence_index: Some(next_sequence_index(body)),
        suppressed: false,
        children: vec![],
    });

    snapshot.history_marker = None;
    snapshot.selected_object_id = object_id.clone();
    snapshot.dirty = true;
    rebuild_viewport(snapshot);
    Some(object_id)
}

pub fn update_selected_feature_length(
    snapshot: &mut BridgeDocumentSnapshot,
    length_mm: f32,
) -> Option<String> {
    if !snapshot.selected_object_id.starts_with("pad-")
        && !snapshot.selected_object_id.starts_with("pocket-")
    {
        return None;
    }

    let selected_id = snapshot.selected_object_id.clone();
    let body = snapshot.roots.first_mut()?;
    let pad = body
        .children
        .iter_mut()
        .find(|child| {
            child.object_id == selected_id
                && (child.object_type == "PartDesign::Pad"
                    || child.object_type == "PartDesign::Pocket")
        })?;

    pad.length_mm = Some(length_mm);
    snapshot.history_marker = None;
    snapshot.dirty = true;
    rebuild_viewport(snapshot);
    Some(selected_id)
}

pub fn update_selected_pad_profile(
    snapshot: &mut BridgeDocumentSnapshot,
    length_mm: Option<f32>,
    midplane: Option<bool>,
) -> Option<String> {
    if !snapshot.selected_object_id.starts_with("pad-") {
        return None;
    }

    let selected_id = snapshot.selected_object_id.clone();
    let body = snapshot.roots.first_mut()?;
    let pad = body
        .children
        .iter_mut()
        .find(|child| child.object_id == selected_id && child.object_type == "PartDesign::Pad")?;

    if let Some(length_mm) = length_mm {
        pad.length_mm = Some(length_mm);
    }
    if let Some(midplane) = midplane {
        pad.midplane = midplane;
    }
    snapshot.history_marker = None;
    snapshot.dirty = true;
    rebuild_viewport(snapshot);
    Some(selected_id)
}

pub fn update_selected_pocket_profile(
    snapshot: &mut BridgeDocumentSnapshot,
    depth_mm: Option<f32>,
    extent_mode: Option<&str>,
) -> Option<String> {
    if !snapshot.selected_object_id.starts_with("pocket-") {
        return None;
    }

    let selected_id = snapshot.selected_object_id.clone();
    let body = snapshot.roots.first_mut()?;
    let pocket = body
        .children
        .iter_mut()
        .find(|child| child.object_id == selected_id && child.object_type == "PartDesign::Pocket")?;

    if let Some(depth_mm) = depth_mm {
        pocket.length_mm = Some(depth_mm);
    }
    if let Some(extent_mode) = extent_mode {
        pocket.extent_mode = Some(normalize_extent_mode(Some(extent_mode), "dimension"));
    }
    snapshot.history_marker = None;
    snapshot.dirty = true;
    rebuild_viewport(snapshot);
    Some(selected_id)
}

pub fn sketch_workflow_description(node: &BridgeObjectNode) -> String {
    match (node.profile_closed, node.fully_constrained) {
        (Some(true), Some(true)) => {
            "Sketch is production-ready. Create a PartDesign feature from the resolved profile.".into()
        }
        (Some(true), _) => {
            "Sketch profile is closed, but constraints still need cleanup before feature creation.".into()
        }
        (Some(false), _) => {
            "Sketch is still open. Close the profile before creating a PartDesign feature.".into()
        }
        _ => "Sketch state is available through the bridge, but readiness is still unresolved.".into(),
    }
}

pub fn sketch_next_step(node: &BridgeObjectNode) -> String {
    match (node.profile_closed, node.fully_constrained) {
        (Some(true), Some(true)) => "Create a pad or pocket".into(),
        (Some(true), _) => "Finish constraints before feature creation".into(),
        (Some(false), _) => "Close the profile before feature creation".into(),
        _ => "Inspect sketch readiness".into(),
    }
}

pub fn pad_workflow_description(node: &BridgeObjectNode) -> String {
    if node.midplane {
        "Symmetric pad selected. Validate centered growth, then recompute or continue downstream modeling.".into()
    } else {
        "One-sided pad selected. Inspect length and downstream dependencies before continuing.".into()
    }
}

pub fn pad_inspection_hint(node: &BridgeObjectNode) -> String {
    if node.midplane {
        "Inspect centered extent".into()
    } else {
        "Inspect one-sided growth".into()
    }
}

pub fn pocket_workflow_description(node: &BridgeObjectNode) -> String {
    if node.extent_mode.as_deref() == Some("through_all") {
        "Through-all pocket selected. Verify the cut propagates cleanly across the full body depth.".into()
    } else {
        "Dimensioned pocket selected. Review cut depth and recompute after edits.".into()
    }
}

pub fn pocket_inspection_hint(node: &BridgeObjectNode) -> String {
    if node.extent_mode.as_deref() == Some("through_all") {
        "Inspect full-depth removal".into()
    } else {
        "Inspect the subtractive region".into()
    }
}

pub fn body_workflow_description(snapshot: &BridgeDocumentSnapshot) -> String {
    let Some(body) = snapshot.roots.first() else {
        return "Body state unavailable.".into();
    };

    let sketch_count = body
        .children
        .iter()
        .filter(|child| child.object_type == "Sketcher::SketchObject")
        .count();
    let feature_count = body
        .children
        .iter()
        .filter(|child| child.object_type != "Sketcher::SketchObject")
        .count();

    if sketch_count == 0 {
        "Body selected. Start by creating a sketch to seed the feature history.".into()
    } else if feature_count == 0 {
        format!(
            "Body selected with {} sketch{} queued. Convert a sketch into the next feature.",
            sketch_count,
            if sketch_count == 1 { "" } else { "es" }
        )
    } else {
        format!(
            "Body selected with {} sketch{} and {} feature{} in history.",
            sketch_count,
            if sketch_count == 1 { "" } else { "es" },
            feature_count,
            if feature_count == 1 { "" } else { "s" }
        )
    }
}

pub fn body_next_step(snapshot: &BridgeDocumentSnapshot) -> String {
    let Some(body) = snapshot.roots.first() else {
        return "Inspect body state".into();
    };

    let has_active_sketch = body.children.iter().any(|child| {
        child.object_type == "Sketcher::SketchObject" && !child.suppressed
    });

    if has_active_sketch {
        "Select an active sketch or create the next feature".into()
    } else {
        "Create a sketch on the body".into()
    }
}

pub fn body_feature_summary(snapshot: &BridgeDocumentSnapshot) -> String {
    let Some(body) = snapshot.roots.first() else {
        return "No body loaded".into();
    };

    let active_count = body
        .children
        .iter()
        .filter(|child| !child.suppressed)
        .count();
    format!("{} backend-managed items", active_count)
}

pub fn dependency_workflow_description(
    node: &BridgeObjectNode,
    inactive_reason: Option<&str>,
) -> String {
    if node.suppressed {
        "Selected object is manually suppressed and removed from the active model result.".into()
    } else if let Some(inactive_reason) = inactive_reason {
        format!(
            "Selected object is inactive in the current model evaluation: {}",
            inactive_reason
        )
    } else {
        "Selected object is inactive in the current model evaluation.".into()
    }
}

pub fn dependency_status_label(node: &BridgeObjectNode) -> String {
    if node.suppressed {
        "Suppressed".into()
    } else {
        "Inactive".into()
    }
}

pub fn dependency_issue_hint(
    node: &BridgeObjectNode,
    inactive_reason: Option<&str>,
) -> String {
    if node.suppressed {
        "Feature is manually suppressed and removed from the active model result.".into()
    } else {
        inactive_reason
            .unwrap_or("Feature is waiting on an upstream dependency.")
            .into()
    }
}

pub fn toggle_selected_suppression(snapshot: &mut BridgeDocumentSnapshot) -> Option<(String, bool)> {
    if snapshot.selected_object_id == "body-001" {
        return None;
    }

    let selected_id = snapshot.selected_object_id.clone();
    let suppressed = {
        let body = snapshot.roots.first_mut()?;
        let feature = body
            .children
            .iter_mut()
            .find(|child| child.object_id == selected_id)?;

        feature.suppressed = !feature.suppressed;
        feature.suppressed
    };
    snapshot.history_marker = None;
    snapshot.dirty = true;
    rebuild_viewport(snapshot);
    Some((selected_id, suppressed))
}

pub fn rollback_history_to_selected(snapshot: &mut BridgeDocumentSnapshot) -> Option<(String, u32)> {
    if snapshot.selected_object_id == "body-001" {
        return None;
    }

    let (feature_id, sequence_index) = {
        let body = snapshot.roots.first()?;
        let feature = body
            .children
            .iter()
            .find(|child| child.object_id == snapshot.selected_object_id)?;
        (feature.object_id.clone(), feature.sequence_index?)
    };

    snapshot.history_marker = Some(sequence_index);
    snapshot.dirty = true;
    rebuild_viewport(snapshot);
    Some((feature_id, sequence_index))
}

pub fn resume_full_history(snapshot: &mut BridgeDocumentSnapshot) -> bool {
    if snapshot.history_marker.is_none() {
        return false;
    }

    snapshot.history_marker = None;
    snapshot.dirty = true;
    rebuild_viewport(snapshot);
    true
}

pub fn rebuild_viewport(snapshot: &mut BridgeDocumentSnapshot) {
    let mut drawables = vec![DrawableMesh {
        object_id: "body-001".into(),
        label: "Body".into(),
        kind: "body".into(),
        accent: "#8fe3c1".into(),
        bounds: Bounds2d {
            x: 16.0,
            y: 14.0,
            width: 58.0,
            height: 66.0,
        },
        edges: vec![
            rectangle(16.0, 14.0, 58.0, 66.0),
            rectangle(24.0, 22.0, 42.0, 24.0),
        ],
    }];

    if let Some(body) = snapshot.roots.first() {
        let mut pad_index = 0usize;
        for child in &body.children {
            if !is_feature_active(body, child, snapshot.history_marker) {
                continue;
            }
            match child.object_type.as_str() {
                "Sketcher::SketchObject" => drawables.push(DrawableMesh {
                    object_id: child.object_id.clone(),
                    label: child.label.clone(),
                    kind: "sketch".into(),
                    accent: match child.reference_plane.as_deref().unwrap_or("XY") {
                        "XZ" => "#8ec5ff".into(),
                        "YZ" => "#c3f584".into(),
                        _ => "#ffd166".into(),
                    },
                    bounds: Bounds2d {
                        x: match child.reference_plane.as_deref().unwrap_or("XY") {
                            "XZ" => 24.0,
                            "YZ" => 32.0,
                            _ => 28.0,
                        },
                        y: match child.reference_plane.as_deref().unwrap_or("XY") {
                            "XZ" => 28.0,
                            "YZ" => 36.0,
                            _ => 32.0,
                        },
                        width: 24.0,
                        height: 18.0,
                    },
                    edges: vec![Polyline2d {
                        points: vec![
                            Point2d {
                                x: match child.reference_plane.as_deref().unwrap_or("XY") {
                                    "XZ" => 24.0,
                                    "YZ" => 32.0,
                                    _ => 28.0,
                                },
                                y: match child.reference_plane.as_deref().unwrap_or("XY") {
                                    "XZ" => 46.0,
                                    "YZ" => 52.0,
                                    _ => 48.0,
                                },
                            },
                            Point2d {
                                x: match child.reference_plane.as_deref().unwrap_or("XY") {
                                    "XZ" => 32.0,
                                    "YZ" => 40.0,
                                    _ => 36.0,
                                },
                                y: match child.reference_plane.as_deref().unwrap_or("XY") {
                                    "XZ" => 28.0,
                                    "YZ" => 36.0,
                                    _ => 32.0,
                                },
                            },
                            Point2d {
                                x: match child.reference_plane.as_deref().unwrap_or("XY") {
                                    "XZ" => 40.0,
                                    "YZ" => 48.0,
                                    _ => 44.0,
                                },
                                y: match child.reference_plane.as_deref().unwrap_or("XY") {
                                    "XZ" => 41.0,
                                    "YZ" => 49.0,
                                    _ => 45.0,
                                },
                            },
                            Point2d {
                                x: match child.reference_plane.as_deref().unwrap_or("XY") {
                                    "XZ" => 48.0,
                                    "YZ" => 56.0,
                                    _ => 52.0,
                                },
                                y: match child.reference_plane.as_deref().unwrap_or("XY") {
                                    "XZ" => 28.0,
                                    "YZ" => 36.0,
                                    _ => 32.0,
                                },
                            },
                        ],
                    }],
                }),
                "PartDesign::Pad" => {
                    let offset = pad_index as f32 * 7.5;
                    let length = child.length_mm.unwrap_or(12.0);
                    let height = 22.0 + (length / 12.0) * 12.0;
                    let width = if child.midplane { 30.0 } else { 26.0 };
                    let x = if child.midplane {
                        32.0 + offset
                    } else {
                        34.0 + offset
                    };
                    drawables.push(DrawableMesh {
                        object_id: child.object_id.clone(),
                        label: child.label.clone(),
                        kind: "feature".into(),
                        accent: if pad_index == 0 { "#ff8f3d".into() } else { "#ffb26b".into() },
                        bounds: Bounds2d {
                            x,
                            y: 38.0 - height + 10.0 - offset * 0.25,
                            width,
                            height,
                        },
                        edges: vec![
                            rectangle(x, 38.0 - height + 10.0 - offset * 0.25, width, height),
                            rectangle(x + 4.0, 42.0 - height + 10.0 - offset * 0.25, width - 8.0, 10.0),
                        ],
                    });
                    pad_index += 1;
                }
                "PartDesign::Pocket" => {
                    let offset = pad_index as f32 * 6.0;
                    let depth = child.length_mm.unwrap_or(8.0);
                    let height = if child.extent_mode.as_deref() == Some("through_all") {
                        34.0
                    } else {
                        18.0 + (depth / 8.0) * 8.0
                    };
                    drawables.push(DrawableMesh {
                        object_id: child.object_id.clone(),
                        label: child.label.clone(),
                        kind: "pocket".into(),
                        accent: if child.extent_mode.as_deref() == Some("through_all") {
                            "#4da0ff".into()
                        } else {
                            "#70b8ff".into()
                        },
                        bounds: Bounds2d {
                            x: 30.0 + offset,
                            y: 46.0 - height * 0.5,
                            width: 18.0,
                            height,
                        },
                        edges: vec![
                            rectangle(30.0 + offset, 46.0 - height * 0.5, 18.0, height),
                            rectangle(34.0 + offset, 50.0 - height * 0.5, 10.0, height * 0.45),
                        ],
                    });
                    pad_index += 1;
                }
                _ => {}
            }
        }
    }

    snapshot.viewport = ViewportSnapshot {
        camera: CameraState {
            eye: [10.0, 8.0, 12.0],
            target: [0.0, 0.0, 0.0],
            up: [0.0, 0.0, 1.0],
        },
        drawables,
    };
}

fn is_feature_active(
    body: &BridgeObjectNode,
    node: &BridgeObjectNode,
    history_marker: Option<u32>,
) -> bool {
    if node.suppressed {
        return false;
    }

    if history_marker
        .map(|marker| node.sequence_index.unwrap_or(0) > marker)
        .unwrap_or(false)
    {
        return false;
    }

    let Some(source_object_id) = node.source_object_id.as_deref() else {
        return true;
    };

    body.children
        .iter()
        .find(|child| child.object_id == source_object_id)
        .map(|child| is_feature_active(body, child, history_marker))
        .unwrap_or(false)
}

fn rectangle(x: f32, y: f32, width: f32, height: f32) -> Polyline2d {
    Polyline2d {
        points: vec![
            Point2d { x, y },
            Point2d { x: x + width, y },
            Point2d {
                x: x + width,
                y: y + height,
            },
            Point2d { x, y: y + height },
            Point2d { x, y },
        ],
    }
}

fn next_sequence_index(body: &BridgeObjectNode) -> u32 {
    body.children
        .iter()
        .filter_map(|child| child.sequence_index)
        .max()
        .unwrap_or(0)
        + 1
}

fn normalize_reference_plane(reference_plane: Option<&str>, fallback: &str) -> String {
    match reference_plane.unwrap_or(fallback) {
        "XZ" => "XZ".into(),
        "YZ" => "YZ".into(),
        _ => "XY".into(),
    }
}

fn sketch_metadata_for_plane(reference_plane: &str) -> (u32, bool, bool) {
    match reference_plane {
        "XZ" => (5, true, false),
        "YZ" => (4, false, false),
        _ => (6, true, true),
    }
}

fn normalize_extent_mode(extent_mode: Option<&str>, fallback: &str) -> String {
    match extent_mode.unwrap_or(fallback) {
        "through_all" => "through_all".into(),
        _ => "dimension".into(),
    }
}

#[no_mangle]
pub extern "C" fn asterforge_bridge_api_version() -> u32 {
    1
}

#[cfg(test)]
mod tests {
    use super::{
        body_next_step, body_workflow_description, create_pad_from_selected_sketch,
        create_pocket_from_selected_sketch, create_sketch_in_body, dependency_issue_hint,
        dependency_status_label, dependency_workflow_description, open_document_snapshot,
        pad_workflow_description, pocket_workflow_description, resume_full_history,
        rollback_history_to_selected, sketch_next_step, sketch_workflow_description,
        toggle_selected_suppression, update_selected_feature_length, update_selected_pad_profile,
        update_selected_pocket_profile,
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
}
