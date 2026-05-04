use std::collections::HashMap;

use crate::{DrawableMesh, ViewportDiff, ViewportSnapshot};

pub fn compute_viewport_diff(before: &ViewportSnapshot, after: &ViewportSnapshot) -> ViewportDiff {
    let before_map = before
        .drawables
        .iter()
        .map(|drawable| (drawable.object_id.as_str(), drawable))
        .collect::<HashMap<_, _>>();
    let after_map = after
        .drawables
        .iter()
        .map(|drawable| (drawable.object_id.as_str(), drawable))
        .collect::<HashMap<_, _>>();

    let mut diff = ViewportDiff::default();

    for drawable in &after.drawables {
        match before_map.get(drawable.object_id.as_str()) {
            None => diff.added.push(drawable.clone()),
            Some(previous) if !drawables_equal(previous, drawable) => {
                diff.modified.push(drawable.clone())
            }
            _ => {}
        }
    }

    for drawable in &before.drawables {
        if !after_map.contains_key(drawable.object_id.as_str()) {
            diff.removed.push(drawable.object_id.clone());
        }
    }

    diff.camera_changed = before.camera != after.camera;
    if diff.camera_changed {
        diff.camera = Some(after.camera.clone());
    }

    diff
}

fn drawables_equal(a: &DrawableMesh, b: &DrawableMesh) -> bool {
    a.label == b.label
        && a.kind == b.kind
        && a.accent == b.accent
        && a.bounds == b.bounds
        && a.edges == b.edges
}