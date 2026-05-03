# Exercises 001: Answer Key

This answer key is based on these files:

- `variants/asterforge/frontend/app/src/stepTypes.ts`
- `variants/asterforge/frontend/app/src/protocol.ts`
- `variants/asterforge/frontend/app/src/App.tsx`
- `variants/asterforge/frontend/app/src/App.integration.test.tsx`

The goal is not exact wording. The goal is accurate understanding.

## Part A: Read and translate

1. `StepAssemblyNode` in plain English:
   It is a typed object representing one assembly node in a STEP document, including its numeric entity id, display label, child assembly nodes, B-Rep ids, tessellated representation ids, and PMI annotation ids.

2. Why `children: StepAssemblyNode[]` is recursive:
   The type refers to itself because an assembly can contain nested subassemblies of the same shape.

3. Difference between `objectId?: string | null` and `selectedObjectId: string | null`:
   The first property may be missing entirely, while the second must exist but may hold either a string or `null`.

4. `Promise<ObjectNode[]>` in plain English:
   The function returns an asynchronous result that eventually resolves to an array of object-tree nodes.

5. `fetchJson<T>` in one sentence:
   It is a generic helper that fetches JSON and returns the parsed response as whatever type the caller supplies.

## Part B: Spot the design choice

1. Union of string literals for UI state:
   In `App.tsx`, `useState<"idle" | "loading" | "ready" | "unavailable" | "error">("idle")` models STEP loading state.

2. `Record<K, V>` example:
   In `App.tsx`, `useState<Record<string, Record<string, string>>>({})` models nested draft maps.

3. `Omit` example:
   In `protocol.ts`, `type ActivityEvent = Omit<EventEnvelope, "level" | "object_id"> & { ... }` refines the generated event type.

4. `import type` example:
   In `protocol.ts`, the module imports generated contract types with `import type { ... } from "./generated/asterforge"`.

5. Inferred primitive state example:
   In `App.tsx`, `useState(false)` infers a boolean state for `paletteOpen`.

## Part C: Short writing drills

1. Why `protocol.ts` is a boundary module:
   It sits between UI components and backend endpoints, centralizing request functions and the exported response types that the rest of the frontend depends on.

2. Why `stepTypes.ts` is a good beginner file:
   It is mostly pure data modeling, so you can learn interfaces, arrays, unions, and recursive structures without also having to parse React rendering logic.

3. Why typed React state values are useful in a migration project:
   They make evolving backend contracts and UI states explicit, which reduces regressions while the frontend architecture is still changing.

4. Why typed tests are useful when mocking modules:
   They help keep the mock surface aligned with the real module contract, which reduces test drift.

## Part D: Small code exercises

1. `LoadState`:

```ts
type LoadState = "idle" | "loading" | "success" | "error";
```

2. `SelectionSummary`:

```ts
interface SelectionSummary {
  objectId: string;
  label: string;
  kind: string;
}
```

3. Function signature:

```ts
function fetchSelectionSummary(documentId: string): Promise<SelectionSummary[]> {
  throw new Error("not implemented");
}
```

4. `Record<string, string>` example:

```ts
const commandLabels: Record<string, string> = {
  "selection.focus": "Focus",
  "step.view_reset": "Reset View",
};
```

## Part E: Big takeaways

1. Types in this repo are not abstract theory. They map directly to backend contracts, UI state, and utility logic.
2. The fastest way to learn from this codebase is still: data shapes first, then protocol contracts, then component state, then utility functions and tests.
3. If you can translate a type into plain English, you are already making real progress.