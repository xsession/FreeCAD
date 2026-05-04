import type {
  StepDocumentIndex,
  StepPmiAnnotation,
  StepSceneBundle,
  StepTessellatedFaceSet,
} from "./stepTypes";

const STEP_API_ROOT = "/api/step";

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: {
      Accept: "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    throw new Error(`STEP request failed: ${response.status} ${response.statusText}`);
  }

  return (await response.json()) as T;
}

export async function fetchStepDocumentIndex(documentId: string): Promise<StepDocumentIndex> {
  return fetchJson<StepDocumentIndex>(
    `${STEP_API_ROOT}/documents/${encodeURIComponent(documentId)}/index`,
  );
}

export async function fetchStepSceneBundle(documentId: string): Promise<StepSceneBundle> {
  return fetchJson<StepSceneBundle>(
    `${STEP_API_ROOT}/documents/${encodeURIComponent(documentId)}/scene`,
  );
}

export interface RenderMeshPacket {
  key: string;
  entityId: number;
  positions: Float32Array;
  indices: Uint32Array;
  normals?: Float32Array;
}

export function buildRenderableMeshPackets(
  representations: StepTessellatedFaceSet[],
): RenderMeshPacket[] {
  return representations.map((representation) => ({
    key: representation.representation_id,
    entityId: representation.entity_id,
    positions: Float32Array.from(representation.positions),
    indices: Uint32Array.from(representation.indices),
    normals: representation.normals
      ? Float32Array.from(representation.normals)
      : undefined,
  }));
}

export function buildPmiOverlayLabels(annotations: StepPmiAnnotation[]): string[] {
  return annotations.map(
    (annotation) => `${annotation.semantic_type}: ${annotation.text}`,
  );
}

export function outlineSceneRender(document: StepDocumentIndex): {
  rootAssemblyCount: number;
  meshPacketCount: number;
  pmiOverlayCount: number;
} {
  const packets = buildRenderableMeshPackets(document.tessellated_representations);
  const overlays = buildPmiOverlayLabels(document.semantic_pmi);

  return {
    rootAssemblyCount: document.assemblies.length,
    meshPacketCount: packets.length,
    pmiOverlayCount: overlays.length,
  };
}