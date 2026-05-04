use std::collections::HashMap;

use asterforge_document_core::{find_bridge_child, find_pad_length_mm, sketch_constraint_summary};
use asterforge_freecad_bridge::BridgeDocumentSnapshot;

use crate::domain::{bridge_object_state, ObjectNode, PropertyGroup, VisibilityState};

use super::state_model::flatten_object_nodes;
use super::state_step_nav::{
    flatten_step_assemblies, step_entity_id_from_object_id, step_entity_object_id,
};
use super::state_types::StepCacheEntry;

pub(super) fn build_property_map(
    snapshot: &BridgeDocumentSnapshot,
    object_tree: &[ObjectNode],
) -> HashMap<String, Vec<PropertyGroup>> {
    let mut map = HashMap::new();
    collect_properties(snapshot, object_tree, &mut map);
    map
}

fn collect_properties(
    snapshot: &BridgeDocumentSnapshot,
    nodes: &[ObjectNode],
    map: &mut HashMap<String, Vec<PropertyGroup>>,
) {
    for node in nodes {
        let mut groups = crate::domain::sample_property_groups();
        if let Some(first_group) = groups.first_mut() {
            if let Some(label_property) = first_group
                .properties
                .iter_mut()
                .find(|property| property.property_id == "label")
            {
                label_property.value_preview = node.label.clone();
            }
        }

        if let Some(second_group) = groups.get_mut(1) {
            if let Some(length_property) = second_group.properties.first_mut() {
                length_property.value_preview = match node.object_type.as_str() {
                    "PartDesign::Pad" => format!(
                        "{:.2} mm",
                        find_pad_length_mm(snapshot, &node.object_id).unwrap_or(12.0)
                    ),
                    "PartDesign::Pocket" => format!(
                        "{:.2} mm",
                        find_pad_length_mm(snapshot, &node.object_id).unwrap_or(8.0)
                    ),
                    "Sketcher::SketchObject" => find_bridge_child(snapshot, &node.object_id)
                        .map(sketch_constraint_summary)
                        .unwrap_or_else(|| "Unknown sketch state".into()),
                    _ => "Inherited".into(),
                };
                if node.object_type == "Sketcher::SketchObject" {
                    length_property.property_id = "constraint_count".into();
                    length_property.display_name = "Constraint state".into();
                    length_property.property_type = "App::PropertyString".into();
                    length_property.value_kind = "string".into();
                    length_property.read_only = true;
                    length_property.unit = None;
                    length_property.expression_capable = false;
                }
            }
        }

        groups.push(PropertyGroup {
            group_id: "dependency".into(),
            title: "Dependency".into(),
            properties: dependency_properties(snapshot, node),
        });

        if let Some(definition_group) = definition_property_group(snapshot, node) {
            groups.push(definition_group);
        }

        map.insert(node.object_id.clone(), groups);
        collect_properties(snapshot, &node.children, map);
    }
}

fn definition_property_group(
    snapshot: &BridgeDocumentSnapshot,
    node: &ObjectNode,
) -> Option<PropertyGroup> {
    let bridge_node = find_bridge_child(snapshot, &node.object_id)?;
    let mut properties = Vec::new();

    if let Some(reference_plane) = bridge_node.reference_plane.as_ref() {
        properties.push(crate::domain::PropertyMetadata {
            property_id: "reference_plane".into(),
            display_name: "Reference plane".into(),
            property_type: "App::PropertyEnumeration".into(),
            value_kind: "string".into(),
            read_only: true,
            unit: None,
            expression_capable: false,
            value_preview: reference_plane.clone(),
        });
    }

    if let Some(extent_mode) = bridge_node.extent_mode.as_ref() {
        properties.push(crate::domain::PropertyMetadata {
            property_id: "extent_mode".into(),
            display_name: "Extent mode".into(),
            property_type: "App::PropertyEnumeration".into(),
            value_kind: "string".into(),
            read_only: true,
            unit: None,
            expression_capable: false,
            value_preview: extent_mode.clone(),
        });
    }

    if node.object_type == "PartDesign::Pad" {
        properties.push(crate::domain::PropertyMetadata {
            property_id: "midplane".into(),
            display_name: "Symmetric to plane".into(),
            property_type: "App::PropertyBool".into(),
            value_kind: "boolean".into(),
            read_only: true,
            unit: None,
            expression_capable: false,
            value_preview: bridge_node.midplane.to_string(),
        });
    }

    (!properties.is_empty()).then(|| PropertyGroup {
        group_id: "definition".into(),
        title: "Definition".into(),
        properties,
    })
}

fn dependency_properties(
    snapshot: &BridgeDocumentSnapshot,
    node: &ObjectNode,
) -> Vec<crate::domain::PropertyMetadata> {
    let bridge_node = snapshot
        .roots
        .iter()
        .flat_map(|root| std::iter::once(root).chain(root.children.iter()))
        .find(|candidate| candidate.object_id == node.object_id);
    let state = bridge_node.map(|candidate| bridge_object_state(snapshot, candidate));

    vec![
        crate::domain::PropertyMetadata {
            property_id: "model_state".into(),
            display_name: "Model state".into(),
            property_type: "App::PropertyEnumeration".into(),
            value_kind: "string".into(),
            read_only: true,
            unit: None,
            expression_capable: false,
            value_preview: state
                .as_ref()
                .map(|dependency| {
                    if dependency.suppressed {
                        "Suppressed".into()
                    } else if dependency.active {
                        "Active".into()
                    } else {
                        "Inactive".into()
                    }
                })
                .unwrap_or_else(|| "Unknown".into()),
        },
        crate::domain::PropertyMetadata {
            property_id: "inactive_reason".into(),
            display_name: "Dependency note".into(),
            property_type: "App::PropertyString".into(),
            value_kind: "string".into(),
            read_only: true,
            unit: None,
            expression_capable: false,
            value_preview: state
                .and_then(|dependency| dependency.inactive_reason)
                .unwrap_or_else(|| "Resolved".into()),
        },
    ]
}

pub(super) fn step_object_tree_from_cache(cache: &StepCacheEntry) -> Vec<ObjectNode> {
    cache
        .scene_bundle
        .assemblies
        .iter()
        .map(step_object_node_from_assembly)
        .collect()
}

fn step_object_node_from_assembly(assembly: &crate::domain::StepAssemblyNode) -> ObjectNode {
    ObjectNode {
        object_id: step_entity_object_id(assembly.entity_id),
        label: assembly.label.clone(),
        object_type: if assembly.children.is_empty() {
            "STEP::MANIFOLD_SOLID_BREP".into()
        } else {
            "STEP::ASSEMBLY_NODE".into()
        },
        visibility: VisibilityState::Visible,
        children: assembly.children.iter().map(step_object_node_from_assembly).collect(),
    }
}

pub(super) fn step_property_map_from_cache(
    cache: &StepCacheEntry,
    object_tree: &[ObjectNode],
) -> HashMap<String, Vec<PropertyGroup>> {
    let entity_by_id: HashMap<u64, &crate::domain::StepEntitySpan> = cache
        .document_index
        .entities
        .iter()
        .map(|entity| (entity.entity_id, entity))
        .collect();
    let assembly_by_id: HashMap<u64, &crate::domain::StepAssemblyNode> =
        flatten_step_assemblies(&cache.scene_bundle.assemblies)
            .into_iter()
            .map(|assembly| (assembly.entity_id, assembly))
            .collect();

    flatten_object_nodes(object_tree)
        .into_iter()
        .filter_map(|node| {
            let entity_id = step_entity_id_from_object_id(&node.object_id)?;
            Some((
                node.object_id.clone(),
                step_property_groups_for_node(
                    node,
                    entity_id,
                    entity_by_id.get(&entity_id).copied(),
                    assembly_by_id.get(&entity_id).copied(),
                ),
            ))
        })
        .collect()
}

fn step_property_groups_for_node(
    node: &ObjectNode,
    entity_id: u64,
    entity: Option<&crate::domain::StepEntitySpan>,
    assembly: Option<&crate::domain::StepAssemblyNode>,
) -> Vec<PropertyGroup> {
    let mut groups = vec![PropertyGroup {
        group_id: "base".into(),
        title: "Base".into(),
        properties: vec![
            crate::domain::PropertyMetadata {
                property_id: "label".into(),
                display_name: "Label".into(),
                property_type: "App::PropertyString".into(),
                value_kind: "string".into(),
                read_only: true,
                unit: None,
                expression_capable: false,
                value_preview: node.label.clone(),
            },
            crate::domain::PropertyMetadata {
                property_id: "entity_id".into(),
                display_name: "Entity Id".into(),
                property_type: "Step::EntityId".into(),
                value_kind: "integer".into(),
                read_only: true,
                unit: None,
                expression_capable: false,
                value_preview: format!("#{entity_id}"),
            },
        ],
    }];

    if let Some(entity) = entity {
        groups.push(PropertyGroup {
            group_id: "step_record".into(),
            title: "STEP Record".into(),
            properties: vec![
                crate::domain::PropertyMetadata {
                    property_id: "keyword".into(),
                    display_name: "Keyword".into(),
                    property_type: "Step::Keyword".into(),
                    value_kind: "string".into(),
                    read_only: true,
                    unit: None,
                    expression_capable: false,
                    value_preview: entity.keyword.clone(),
                },
                crate::domain::PropertyMetadata {
                    property_id: "references".into(),
                    display_name: "Reference count".into(),
                    property_type: "Step::ReferenceList".into(),
                    value_kind: "integer".into(),
                    read_only: true,
                    unit: None,
                    expression_capable: false,
                    value_preview: entity.references.len().to_string(),
                },
                crate::domain::PropertyMetadata {
                    property_id: "byte_range".into(),
                    display_name: "Byte range".into(),
                    property_type: "Step::ByteRange".into(),
                    value_kind: "string".into(),
                    read_only: true,
                    unit: None,
                    expression_capable: false,
                    value_preview: format!("{}..{}", entity.byte_range.start, entity.byte_range.end),
                },
            ],
        });
    }

    if let Some(assembly) = assembly {
        groups.push(PropertyGroup {
            group_id: "topology".into(),
            title: "Topology".into(),
            properties: vec![
                crate::domain::PropertyMetadata {
                    property_id: "child_count".into(),
                    display_name: "Child count".into(),
                    property_type: "App::PropertyInteger".into(),
                    value_kind: "integer".into(),
                    read_only: true,
                    unit: None,
                    expression_capable: false,
                    value_preview: assembly.children.len().to_string(),
                },
                crate::domain::PropertyMetadata {
                    property_id: "brep_count".into(),
                    display_name: "BREP count".into(),
                    property_type: "App::PropertyInteger".into(),
                    value_kind: "integer".into(),
                    read_only: true,
                    unit: None,
                    expression_capable: false,
                    value_preview: assembly.brep_ids.len().to_string(),
                },
                crate::domain::PropertyMetadata {
                    property_id: "pmi_count".into(),
                    display_name: "PMI annotations".into(),
                    property_type: "App::PropertyInteger".into(),
                    value_kind: "integer".into(),
                    read_only: true,
                    unit: None,
                    expression_capable: false,
                    value_preview: assembly.pmi_annotation_ids.len().to_string(),
                },
            ],
        });
    }

    groups
}