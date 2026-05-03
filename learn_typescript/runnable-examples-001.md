# Runnable Examples 001

This file gives you executable TypeScript example chunks that match the concepts taught in the lesson set.

The code for these examples lives in:

- `variants/asterforge/frontend/app/src/learnTypescript.examples.test.ts`

## How to run

From the repo root, run:

```powershell
npm --prefix variants/asterforge/frontend/app test -- learnTypescript.examples.test.ts
```

That command uses the existing Vitest setup in the AsterForge frontend app.

## What the examples cover

1. interface object typing
2. union types as a state machine
3. `Record<K, V>` for keyed maps
4. `Omit<...> & { ... }` refinement
5. generic helper functions
6. transport-to-runtime data transformation

## Example 1: interface object typing

Runnable chunk:

```ts
interface ByteRange {
  start: number;
  end: number;
}

function spanSize(range: ByteRange) {
  return range.end - range.start;
}

expect(spanSize({ start: 4, end: 10 })).toBe(6);
```

Why it matters:

- the function accepts a typed object shape
- TypeScript would reject missing or wrongly typed fields before runtime

## Example 2: union types for finite UI state

Runnable chunk:

```ts
type LoadState = "idle" | "loading" | "ready" | "error";

function isBusy(state: LoadState) {
  return state === "loading";
}

expect(isBusy("loading")).toBe(true);
expect(isBusy("ready")).toBe(false);
```

Why it matters:

- this is the same idea used in `App.tsx` for state like `stepStatus`
- invalid state strings are blocked by the type system

## Example 3: `Record<K, V>` as a typed map

Runnable chunk:

```ts
type ViewPreset = "front" | "back" | "iso";

const presetCommands: Record<ViewPreset, string> = {
  front: "step.view_front",
  back: "step.view_back",
  iso: "step.view_iso",
};

expect(presetCommands.iso).toBe("step.view_iso");
```

Why it matters:

- every allowed key must exist
- every value must match the declared value type

## Example 4: refining a generated contract with `Omit`

Runnable chunk:

```ts
interface RawEventEnvelope {
  topic: string;
  level: string;
  object_id: string | undefined;
}

type ActivityEvent = Omit<RawEventEnvelope, "level" | "object_id"> & {
  level: "info" | "warning" | "error";
  object_id?: string | null;
};

const event: ActivityEvent = {
  topic: "step_measurement",
  level: "warning",
  object_id: null,
};

expect(event.level).toBe("warning");
```

Why it matters:

- this mirrors the refinement pattern used in `protocol.ts`
- it keeps most of the source contract while tightening selected fields

## Example 5: generic helper functions

Runnable chunk:

```ts
function identity<T>(value: T): T {
  return value;
}

expect(identity<string>("ap242")).toBe("ap242");
expect(identity<number[]>([1, 2, 3])).toHaveLength(3);
```

Why it matters:

- this is the same general idea as `fetchJson<T>` in `protocol.ts` and `stepClient.ts`
- one function can work with many types while keeping type information intact

## Example 6: transform transport data into runtime data

Runnable chunk:

```ts
interface FaceSetTransport {
  representation_id: string;
  entity_id: number;
  positions: number[];
  indices: number[];
}

interface RenderMeshPacket {
  key: string;
  entityId: number;
  positions: Float32Array;
  indices: Uint32Array;
}

function buildRenderableMeshPacket(faceSet: FaceSetTransport): RenderMeshPacket {
  return {
    key: faceSet.representation_id,
    entityId: faceSet.entity_id,
    positions: Float32Array.from(faceSet.positions),
    indices: Uint32Array.from(faceSet.indices),
  };
}

const packet = buildRenderableMeshPacket({
  representation_id: "rep-1",
  entity_id: 42,
  positions: [0, 1, 2, 3, 4, 5],
  indices: [0, 1, 2],
});

expect(packet.positions).toBeInstanceOf(Float32Array);
expect(packet.indices).toBeInstanceOf(Uint32Array);
```

Why it matters:

- this matches the same architectural move used in `stepClient.ts`
- backend-friendly arrays become runtime-friendly typed arrays

## Best way to use this file

1. read one chunk
2. predict the result before running it
3. run the test file
4. change one value locally and rerun
5. explain in plain English what the type is protecting

## Next step

After running these examples, go back to the real source files and find the corresponding pattern in:

- `src/protocol.ts`
- `src/stepClient.ts`
- `src/App.tsx`
- `src/shellViewUtils.ts`