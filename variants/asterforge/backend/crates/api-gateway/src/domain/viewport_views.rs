use crate::domain::{
    ObjectNode, ViewportBounds, ViewportDiffResponse, ViewportDrawable, ViewportResponse,
    ViewportScene, VisibilityState,
};
use asterforge_freecad_bridge::{
    open_document_snapshot, BridgeDocumentSnapshot, DrawableMesh, ViewportDiff, ViewportSnapshot,
};

#[allow(dead_code)]
pub fn sample_object_tree() -> Vec<ObjectNode> {
    let snapshot = open_document_snapshot(None);
    snapshot.roots.iter().map(object_node_from_bridge).collect()
}

#[allow(dead_code)]
pub fn sample_viewport(selected_object_id: &str) -> ViewportResponse {
    let snapshot = open_document_snapshot(None);
    viewport_from_bridge(&snapshot, selected_object_id)
}

pub fn object_tree_from_bridge(snapshot: &BridgeDocumentSnapshot) -> Vec<ObjectNode> {
    snapshot.roots.iter().map(object_node_from_bridge).collect()
}

pub fn viewport_from_bridge(
    snapshot: &BridgeDocumentSnapshot,
    selected_object_id: &str,
) -> ViewportResponse {
    ViewportResponse {
        document_id: snapshot.document_id.clone(),
        selected_object_id: selected_object_id.to_string(),
        scene: viewport_scene_from_bridge(&snapshot.viewport),
    }
}

pub fn viewport_diff_response(
    document_id: &str,
    selected_object_id: &str,
    diff: ViewportDiff,
) -> ViewportDiffResponse {
    ViewportDiffResponse {
        document_id: document_id.to_string(),
        selected_object_id: selected_object_id.to_string(),
        added: diff.added.iter().map(viewport_drawable_from_bridge).collect(),
        removed: diff.removed,
        modified: diff.modified.iter().map(viewport_drawable_from_bridge).collect(),
        camera_changed: diff.camera_changed,
        camera_eye: diff.camera.as_ref().map(|camera| camera.eye),
        camera_target: diff.camera.as_ref().map(|camera| camera.target),
    }
}

fn viewport_scene_from_bridge(snapshot: &ViewportSnapshot) -> ViewportScene {
    ViewportScene {
        camera_eye: snapshot.camera.eye,
        camera_target: snapshot.camera.target,
        drawables: snapshot
            .drawables
            .iter()
            .map(viewport_drawable_from_bridge)
            .collect(),
    }
}

fn viewport_drawable_from_bridge(drawable: &DrawableMesh) -> ViewportDrawable {
    ViewportDrawable {
        object_id: drawable.object_id.clone(),
        label: drawable.label.clone(),
        kind: drawable.kind.clone(),
        accent: drawable.accent.clone(),
        bounds: ViewportBounds {
            x: drawable.bounds.x,
            y: drawable.bounds.y,
            width: drawable.bounds.width,
            height: drawable.bounds.height,
        },
        paths: drawable
            .edges
            .iter()
            .map(|polyline| {
                polyline
                    .points
                    .iter()
                    .enumerate()
                    .map(|(index, point)| {
                        if index == 0 {
                            format!("M {} {}", point.x, point.y)
                        } else {
                            format!("L {} {}", point.x, point.y)
                        }
                    })
                    .collect::<Vec<_>>()
                    .join(" ")
            })
            .collect(),
    }
}

fn object_node_from_bridge(node: &asterforge_freecad_bridge::BridgeObjectNode) -> ObjectNode {
    ObjectNode {
        object_id: node.object_id.clone(),
        label: node.label.clone(),
        object_type: node.object_type.clone(),
        visibility: match node.visibility.as_str() {
            "hidden" => VisibilityState::Hidden,
            "inherited" => VisibilityState::Inherited,
            _ => VisibilityState::Visible,
        },
        children: node.children.iter().map(object_node_from_bridge).collect(),
    }
}