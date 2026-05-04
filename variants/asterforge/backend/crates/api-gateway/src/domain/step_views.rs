use crate::domain::{
    StepAssemblyNode, StepByteRange, StepChunkSummary, StepDocumentIndex, StepEntitySpan,
    StepHeaderSection, StepPmiAnnotation, StepSceneBundle, StepTessellatedFaceSet,
};
use asterforge_step_core::{
    ClosedShell as ParsedClosedShell, ManifoldSolidBrep as ParsedManifoldSolidBrep,
    StepApplicationProtocol as ParsedStepApplicationProtocol,
    StepChunkSummary as ParsedStepChunkSummary, StepDocumentIndexDto as ParsedStepDocumentIndexDto,
    StepEntitySpan as ParsedStepEntitySpan, StepHeaderSection as ParsedStepHeaderSection,
};

pub fn step_document_index_from_parsed(
    index: &ParsedStepDocumentIndexDto,
    breps: &[ParsedManifoldSolidBrep],
    shells: &[ParsedClosedShell],
) -> StepDocumentIndex {
    let assemblies = step_assemblies_from_parsed(breps, shells);
    let semantic_pmi = step_semantic_pmi_from_parsed(index, breps, shells);
    let tessellated_representations = step_tessellations_from_parsed(breps);

    StepDocumentIndex {
        header: step_header_from_parsed(&index.header),
        chunks: index.chunks.iter().map(step_chunk_from_parsed).collect(),
        entities: index.entities.iter().map(step_entity_span_from_parsed).collect(),
        assemblies,
        semantic_pmi,
        tessellated_representations,
    }
}

pub fn step_scene_bundle_from_parsed(
    index: &ParsedStepDocumentIndexDto,
    breps: &[ParsedManifoldSolidBrep],
    shells: &[ParsedClosedShell],
) -> StepSceneBundle {
    StepSceneBundle {
        assemblies: step_assemblies_from_parsed(breps, shells),
        semantic_pmi: step_semantic_pmi_from_parsed(index, breps, shells),
        tessellated_representations: step_tessellations_from_parsed(breps),
    }
}

fn step_header_from_parsed(header: &ParsedStepHeaderSection) -> StepHeaderSection {
    StepHeaderSection {
        source_path: header.source_path.clone(),
        implementation_level: header.implementation_level.clone(),
        file_name: header.file_name.clone(),
        file_descriptions: header.file_descriptions.clone(),
        schema_identifiers: header.schema_identifiers.clone(),
        application_protocols: header
            .application_protocols
            .iter()
            .map(step_protocol_label)
            .collect(),
    }
}

fn step_protocol_label(protocol: &ParsedStepApplicationProtocol) -> String {
    match protocol {
        ParsedStepApplicationProtocol::Ap203 => "AP203".into(),
        ParsedStepApplicationProtocol::Ap214 => "AP214".into(),
        ParsedStepApplicationProtocol::Ap242 => "AP242".into(),
        ParsedStepApplicationProtocol::Unknown(value) => value.clone(),
    }
}

fn step_chunk_from_parsed(chunk: &ParsedStepChunkSummary) -> StepChunkSummary {
    StepChunkSummary {
        chunk_id: chunk.chunk_id,
        byte_range: step_byte_range(chunk.byte_range.start, chunk.byte_range.end),
        entity_ids: chunk.entity_ids.clone(),
    }
}

fn step_entity_span_from_parsed(entity: &ParsedStepEntitySpan) -> StepEntitySpan {
    StepEntitySpan {
        entity_id: entity.entity_id,
        keyword: entity.keyword.clone(),
        byte_range: step_byte_range(entity.byte_range.start, entity.byte_range.end),
        references: entity.references.clone(),
    }
}

fn step_byte_range(start: usize, end: usize) -> StepByteRange {
    StepByteRange { start, end }
}

fn step_assemblies_from_parsed(
    breps: &[ParsedManifoldSolidBrep],
    shells: &[ParsedClosedShell],
) -> Vec<StepAssemblyNode> {
    breps
        .iter()
        .map(|brep| {
            let shell = shells.iter().find(|candidate| candidate.entity_id == brep.outer_shell_id);
            let representation_id = format!("brep-{}-mesh", brep.entity_id);
            let mut pmi_annotation_ids = vec![format!("brep-{}-summary", brep.entity_id)];
            let children = shell
                .map(|shell| {
                    pmi_annotation_ids.push(format!("shell-{}-faces", shell.entity_id));
                    StepAssemblyNode {
                        entity_id: shell.entity_id,
                        label: shell
                            .name
                            .clone()
                            .unwrap_or_else(|| format!("Closed shell #{}", shell.entity_id)),
                        children: vec![],
                        brep_ids: vec![brep.entity_id],
                        tessellated_representation_ids: vec![representation_id.clone()],
                        pmi_annotation_ids: vec![format!("shell-{}-faces", shell.entity_id)],
                    }
                })
                .into_iter()
                .collect();

            StepAssemblyNode {
                entity_id: brep.entity_id,
                label: brep
                    .name
                    .clone()
                    .unwrap_or_else(|| format!("Solid BREP #{}", brep.entity_id)),
                children,
                brep_ids: vec![brep.entity_id],
                tessellated_representation_ids: vec![representation_id],
                pmi_annotation_ids,
            }
        })
        .collect()
}

fn step_semantic_pmi_from_parsed(
    index: &ParsedStepDocumentIndexDto,
    breps: &[ParsedManifoldSolidBrep],
    shells: &[ParsedClosedShell],
) -> Vec<StepPmiAnnotation> {
    let protocol_summary = StepPmiAnnotation {
        annotation_id: "protocol-summary".into(),
        semantic_type: "protocol_summary".into(),
        text: format!(
            "Protocols: {}",
            index
                .header
                .application_protocols
                .iter()
                .map(step_protocol_label)
                .collect::<Vec<_>>()
                .join(", ")
        ),
        target_entity_ids: breps.iter().map(|brep| brep.entity_id).collect(),
        presentation_entity_ids: vec![],
    };

    let mut annotations = vec![protocol_summary];
    annotations.extend(breps.iter().map(|brep| StepPmiAnnotation {
        annotation_id: format!("brep-{}-summary", brep.entity_id),
        semantic_type: "solid_brep".into(),
        text: format!(
            "{} references outer shell #{}",
            brep.name
                .clone()
                .unwrap_or_else(|| format!("BREP #{}", brep.entity_id)),
            brep.outer_shell_id
        ),
        target_entity_ids: vec![brep.entity_id, brep.outer_shell_id],
        presentation_entity_ids: vec![brep.entity_id],
    }));
    annotations.extend(shells.iter().map(|shell| StepPmiAnnotation {
        annotation_id: format!("shell-{}-faces", shell.entity_id),
        semantic_type: "closed_shell_face_count".into(),
        text: format!(
            "{} contains {} advanced faces",
            shell
                .name
                .clone()
                .unwrap_or_else(|| format!("Shell #{}", shell.entity_id)),
            shell.face_ids.len()
        ),
        target_entity_ids: std::iter::once(shell.entity_id)
            .chain(shell.face_ids.iter().copied())
            .collect(),
        presentation_entity_ids: shell.face_ids.clone(),
    }));
    annotations
}

fn step_tessellations_from_parsed(
    breps: &[ParsedManifoldSolidBrep],
) -> Vec<StepTessellatedFaceSet> {
    breps
        .iter()
        .enumerate()
        .map(|(index, brep)| {
            let offset = index as f32 * 1.5;
            StepTessellatedFaceSet {
                representation_id: format!("brep-{}-mesh", brep.entity_id),
                entity_id: brep.entity_id,
                positions: vec![
                    0.0 + offset,
                    0.0,
                    0.0,
                    1.0 + offset,
                    0.0,
                    0.0,
                    1.0 + offset,
                    1.0,
                    0.0,
                    0.0 + offset,
                    1.0,
                    0.0,
                    0.5 + offset,
                    0.5,
                    1.0,
                ],
                normals: None,
                indices: vec![0, 1, 4, 1, 2, 4, 2, 3, 4, 3, 0, 4, 0, 1, 2, 0, 2, 3],
            }
        })
        .collect()
}