export type StepApplicationProtocol = "AP203" | "AP214" | "AP242" | string;

export interface ByteRange {
  start: number;
  end: number;
}

export interface StepHeaderSection {
  source_path: string | null;
  implementation_level: string | null;
  file_name: string | null;
  file_descriptions: string[];
  schema_identifiers: string[];
  application_protocols: StepApplicationProtocol[];
}

export interface StepEntitySpan {
  entity_id: number;
  keyword: string;
  byte_range: ByteRange;
  references: number[];
}

export interface StepChunkSummary {
  chunk_id: number;
  byte_range: ByteRange;
  entity_ids: number[];
}

export interface ClosedShell {
  entity_id: number;
  name: string | null;
  face_ids: number[];
}

export interface ManifoldSolidBrep {
  entity_id: number;
  name: string | null;
  outer_shell_id: number;
}

export interface StepPmiAnnotation {
  annotation_id: string;
  semantic_type: string;
  text: string;
  target_entity_ids: number[];
  presentation_entity_ids: number[];
}

export interface StepTessellatedFaceSet {
  representation_id: string;
  entity_id: number;
  positions: number[];
  normals?: number[];
  indices: number[];
}

export interface StepAssemblyNode {
  entity_id: number;
  label: string;
  children: StepAssemblyNode[];
  brep_ids: number[];
  tessellated_representation_ids: string[];
  pmi_annotation_ids: string[];
}

export interface StepDocumentIndex {
  header: StepHeaderSection;
  chunks: StepChunkSummary[];
  entities: StepEntitySpan[];
  assemblies: StepAssemblyNode[];
  semantic_pmi: StepPmiAnnotation[];
  tessellated_representations: StepTessellatedFaceSet[];
}

export interface StepSceneBundle {
  assemblies: StepAssemblyNode[];
  semantic_pmi: StepPmiAnnotation[];
  tessellated_representations: StepTessellatedFaceSet[];
}