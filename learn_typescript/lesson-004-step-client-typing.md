# Lesson 004: STEP Client Typing In `stepClient.ts`

This lesson uses `variants/asterforge/frontend/app/src/stepClient.ts`.

If `protocol.ts` is the general app contract layer, `stepClient.ts` is a narrower domain client focused on STEP data.

## 1. Why this file matters

This file is useful because it combines three TypeScript jobs in one place:

1. typed HTTP helpers
2. typed domain objects for rendering
3. typed data transformations from backend payloads into render-friendly structures

That makes it a good bridge between API typing and UI/runtime typing.

## 2. Type-only imports again, but with domain intent

The file starts with:

```ts
import type {
  StepDocumentIndex,
  StepPmiAnnotation,
  StepSceneBundle,
  StepTessellatedFaceSet,
} from "./stepTypes";
```

This tells you the file depends on the domain model defined elsewhere, not on ad hoc inline objects.

That is good architecture. The client layer is consuming stable domain types instead of inventing new ones.

## 3. Generic fetch helper, specialized domain root

The file defines:

```ts
const STEP_API_ROOT = "/api/step";

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  ...
}
```

This is similar to `protocol.ts`, but specialized for one API area.

TypeScript lesson:

- keep shared helper structure small
- keep endpoint-specific code readable
- return `Promise<T>` so every caller knows the result shape

## 4. Endpoint wrappers are extremely readable when typed well

Example:

```ts
export async function fetchStepDocumentIndex(documentId: string): Promise<StepDocumentIndex> {
  return fetchJson<StepDocumentIndex>(
    `${STEP_API_ROOT}/documents/${encodeURIComponent(documentId)}/index`,
  );
}
```

This line tells you almost everything you need:

- input: one `documentId` string
- output: one `StepDocumentIndex`
- route: a document-specific STEP endpoint
- safety detail: the id is encoded with `encodeURIComponent`

That is what good TypeScript does. It turns plumbing into a readable contract.

## 5. Custom interfaces for runtime-ready structures

This file defines a new interface:

```ts
export interface RenderMeshPacket {
  key: string;
  entityId: number;
  positions: Float32Array;
  indices: Uint32Array;
  normals?: Float32Array;
}
```

This is important because it is not just mirroring backend JSON anymore.

It represents a frontend-friendly structure ready for rendering.

Key lesson:

- not every interface has to match network payloads
- some interfaces describe transformed runtime data

That is a major TypeScript skill in frontend work.

## 6. Typed array conversions

Example:

```ts
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
```

This is a strong example of TypeScript documenting a data transformation pipeline.

Input:

- `StepTessellatedFaceSet[]`

Output:

- `RenderMeshPacket[]`

What changed:

- plain number arrays became typed arrays like `Float32Array` and `Uint32Array`
- property names were adapted for rendering use
- optional normals stayed optional

This is not just syntax. It is domain conversion made explicit.

## 7. Small pure functions are ideal TypeScript practice

Example:

```ts
export function buildPmiOverlayLabels(annotations: StepPmiAnnotation[]): string[] {
  return annotations.map(
    (annotation) => `${annotation.semantic_type}: ${annotation.text}`,
  );
}
```

This is a very teachable pattern:

- typed input
- simple pure transformation
- typed output

If you are learning TypeScript, functions like this are the best place to practice because the contract is obvious.

## 8. Composite summary return types

Another example:

```ts
export function outlineSceneRender(document: StepDocumentIndex): {
  rootAssemblyCount: number;
  meshPacketCount: number;
  pmiOverlayCount: number;
} {
  ...
}
```

This uses an inline object return type.

That is reasonable when:

- the shape is small
- the type is only used once
- introducing a named interface would add noise

Practical rule:

- use named interfaces for shared or important concepts
- use inline object types for small local return values

## 9. What this file teaches beyond syntax

This file shows a common frontend architecture pattern:

1. fetch backend data with typed helpers
2. convert backend-friendly shapes into renderer-friendly shapes
3. expose small pure helpers for the rest of the app

That pattern is one of the most reusable skills you can take from this repo.

## 10. Checkpoint questions

You understand this file if you can answer these:

1. Why does `RenderMeshPacket` use `Float32Array` and `Uint32Array` instead of plain arrays?
2. Why is `buildRenderableMeshPackets` a transformation function instead of a fetch function?
3. Why is `outlineSceneRender` allowed to use an inline return type instead of a named interface?
4. Why is it useful that `fetchStepDocumentIndex` returns `Promise<StepDocumentIndex>`?

## 11. Short mental model

`stepClient.ts` is a domain client plus a data-preparation layer.

It fetches typed STEP data, reshapes it into runtime-ready structures, and keeps those transformations explicit enough that the rest of the UI can stay simpler.