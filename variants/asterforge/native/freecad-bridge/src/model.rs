use crate::{
    Bounds2d, BridgeDocumentSnapshot, BridgeObjectNode, CameraState, DrawableMesh, Point2d,
    Polyline2d, ViewportSnapshot,
};

pub(crate) fn parse_bool_flag(value: &str) -> Option<bool> {
    match value.trim().to_ascii_lowercase().as_str() {
        "true" | "1" | "yes" | "on" => Some(true),
        "false" | "0" | "no" | "off" => Some(false),
        _ => None,
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
        workbench: if normalized_path.to_ascii_lowercase().ends_with(".stp")
            || normalized_path.to_ascii_lowercase().ends_with(".step")
        {
            "STEP Inspection".into()
        } else {
            "PartDesign".into()
        },
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
        .count()
        + 1;

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
    let (constraint_count, profile_closed, fully_constrained) = sketch_metadata_for_plane(&reference_plane);
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
    let feature = body.children.iter_mut().find(|child| {
        child.object_id == selected_id
            && (child.object_type == "PartDesign::Pad" || child.object_type == "PartDesign::Pocket")
    })?;

    feature.length_mm = Some(length_mm);
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

pub fn toggle_selected_suppression(snapshot: &mut BridgeDocumentSnapshot) -> Option<(String, bool)> {
    if snapshot.selected_object_id == "body-001" {
        return None;
    }

    let selected_id = snapshot.selected_object_id.clone();
    let suppressed = {
        let body = snapshot.roots.first_mut()?;
        let feature = body.children.iter_mut().find(|child| child.object_id == selected_id)?;
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
                    let x = if child.midplane { 32.0 + offset } else { 34.0 + offset };
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
            Point2d { x: x + width, y: y + height },
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