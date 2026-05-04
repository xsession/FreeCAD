use crate::{BridgeDocumentSnapshot, BridgeObjectNode};

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