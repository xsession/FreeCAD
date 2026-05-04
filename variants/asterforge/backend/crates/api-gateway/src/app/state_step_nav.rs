use crate::domain::{ObjectNode, StepAssemblyNode};

use super::state::STEP_OBJECT_MODE;

pub(super) fn step_entity_object_id(entity_id: u64) -> String {
    format!("step-entity-{entity_id}")
}

pub(super) fn step_entity_id_from_object_id(object_id: &str) -> Option<u64> {
    object_id.strip_prefix("step-entity-")?.parse::<u64>().ok()
}

pub(super) fn step_parent_object_id(
    object_id: &str,
    assemblies: &[StepAssemblyNode],
) -> Option<String> {
    let entity_id = step_entity_id_from_object_id(object_id)?;
    find_step_parent_entity_id(entity_id, assemblies).map(step_entity_object_id)
}

pub(super) fn step_first_child_object_id(
    object_id: &str,
    assemblies: &[StepAssemblyNode],
) -> Option<String> {
    let entity_id = step_entity_id_from_object_id(object_id)?;
    find_step_assembly(entity_id, assemblies)
        .and_then(|assembly| assembly.children.first())
        .map(|child| step_entity_object_id(child.entity_id))
}

pub(super) fn step_selectable_object_ids_for_mode(
    object_tree: &[ObjectNode],
    selection_mode: &str,
) -> Vec<String> {
    if selection_mode != STEP_OBJECT_MODE {
        return vec![];
    }

    flatten_object_nodes(object_tree)
        .into_iter()
        .map(|node| node.object_id.clone())
        .collect()
}

pub(super) fn flatten_step_assemblies(
    assemblies: &[StepAssemblyNode],
) -> Vec<&StepAssemblyNode> {
    let mut flattened = Vec::new();
    for assembly in assemblies {
        flattened.push(assembly);
        flattened.extend(flatten_step_assemblies(&assembly.children));
    }
    flattened
}

pub(super) fn find_step_assembly(
    entity_id: u64,
    assemblies: &[StepAssemblyNode],
) -> Option<&StepAssemblyNode> {
    for assembly in assemblies {
        if assembly.entity_id == entity_id {
            return Some(assembly);
        }
        if let Some(found) = find_step_assembly(entity_id, &assembly.children) {
            return Some(found);
        }
    }
    None
}

fn find_step_parent_entity_id(entity_id: u64, assemblies: &[StepAssemblyNode]) -> Option<u64> {
    for assembly in assemblies {
        if assembly.children.iter().any(|child| child.entity_id == entity_id) {
            return Some(assembly.entity_id);
        }
        if let Some(found) = find_step_parent_entity_id(entity_id, &assembly.children) {
            return Some(found);
        }
    }
    None
}

fn flatten_object_nodes(nodes: &[ObjectNode]) -> Vec<&ObjectNode> {
    let mut flattened = Vec::new();
    for node in nodes {
        flattened.push(node);
        flattened.extend(flatten_object_nodes(&node.children));
    }
    flattened
}