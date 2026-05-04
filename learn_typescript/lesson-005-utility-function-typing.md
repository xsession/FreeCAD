# Lesson 005: Utility Function Typing In `shellViewUtils.ts`

This lesson uses `variants/asterforge/frontend/app/src/shellViewUtils.ts`.

This file matters because it shows TypeScript applied to business logic and UI decision logic, not just API payloads.

## 1. Why utility files are good TypeScript training

Utility files usually contain:

- input validation
- filtering
- sorting
- summarization
- state derivation

That means they are full of function signatures, union types, collection types, and local logic. Those are exactly the places where TypeScript provides the most day-to-day value.

## 2. Simple union types can carry a lot of meaning

Example:

```ts
export type StepViewportPreset = "front" | "back" | "right" | "left" | "top" | "bottom" | "iso";
```

This does two things at once:

- it documents all supported presets
- it prevents invalid preset strings from spreading through the app

This is one of the most practical TypeScript patterns in UI code.

## 3. Typed constants: `Set` and `Record`

This file uses both:

```ts
const REPORT_NOISE_TOPICS = new Set([
  "preselection_changed",
  "recompute_progress",
  ...
]);

const COMMAND_ACTIVITY_TOPICS: Record<string, string[]> = {
  "step.inspect_pmi": ["step_pmi_annotation", "step_pmi_inspection"],
  "step.measure_selection": ["step_measurement"]
};
```

What to learn:

- `Set` is useful for fast membership checks
- `Record<string, string[]>` models a mapping from command id to related activity topics

This is typical domain logic: map one concept to another and do it with explicit types.

## 4. Function parameters tell the story of the logic

Example:

```ts
export function filteredReportEvents(
  events: ActivityEvent[],
  shellSnapshot: ShellSnapshot | null,
  selectedObjectId: string | null
) {
  ...
}
```

Even before reading the body, you already know the function depends on:

- a list of events
- current shell state, which may be absent
- the selected object id, which may also be absent

That is the core TypeScript advantage for utility code. The function boundary explains the decision inputs.

## 5. Typed filtering logic

Inside `filteredReportEvents`, the function uses booleans derived from typed objects:

```ts
const inspection = shellSnapshot?.inspection;
const inspectedPmi = inspection?.step_pmi;
const measured = inspection?.step_measurement;
```

This teaches a useful TypeScript reading habit:

- nullable input types often lead to optional chaining
- optional chaining is a runtime-safe expression of the type model

If a value can be `null`, the code should act like it.

## 6. Sorting and summarization are easier to trust when typed

Examples:

```ts
export function prioritizeReportEvents(events: ActivityEvent[]) {
  ...
}

export function summarizeReportEvents(events: ActivityEvent[]) {
  ...
}
```

Both accept `ActivityEvent[]` and return arrays of the same conceptual thing.

That matters because these functions are reordering or compressing information, not changing its fundamental domain type.

This is a good design smell check:

- if the input and output concept are the same, keep the type stable
- if the output is a new structure, name that new structure

## 7. Typed math helpers are still utility code

The file contains helpers like:

```ts
function normalizeVector(x: number, y: number, z: number) {
  ...
}

function crossProduct(
  left: { x: number; y: number; z: number },
  right: { x: number; y: number; z: number }
) {
  ...
}
```

Lessons here:

- not every useful type needs a named interface
- inline object parameter types are fine for small local math helpers
- number-heavy code benefits from explicit typing even when inference would work

If these helpers started spreading across files, that would be a signal to introduce a shared vector type.

## 8. Domain parsing helpers

Example:

```ts
function stepEntityIdFromObjectId(objectId: string | null | undefined) {
  ...
}
```

This is a small but strong example of defensive typing.

The function explicitly accepts:

- a string
- `null`
- `undefined`

That means the caller does not have to sanitize first. The helper owns the parsing boundary.

## 9. Recursive domain search

Example:

```ts
function findStepAssembly(assemblies: StepAssemblyNode[], entityId: number): StepAssemblyNode | null {
  ...
}
```

This is a recursive tree search over the typed assembly structure.

Important lesson:

- recursive data types often lead to recursive utility functions
- the return type `StepAssemblyNode | null` makes the search outcome explicit

This is the same pattern you saw earlier in the data model, now applied in logic.

## 10. What this file teaches architecturally

This file is where messy UI rules get turned into small typed functions.

That is good engineering because:

- components stay less cluttered
- the functions are easier to test
- domain rules become reusable
- TypeScript keeps the function contracts honest

## 11. Checkpoint questions

You understand the value of this file if you can explain:

1. why `StepViewportPreset` should be a union instead of a plain string
2. why `filteredReportEvents` accepts nullable inputs
3. why `findStepAssembly` returns `StepAssemblyNode | null`
4. why `Record<string, string[]>` fits `COMMAND_ACTIVITY_TOPICS`
5. why small utility helpers are often the easiest place to practice TypeScript fluency

## 12. Short mental model

`shellViewUtils.ts` is where typed domain rules live.

It takes typed events, typed shell state, and typed STEP data, then turns them into sorted, filtered, summarized, or derived values that the UI can render with less branching and less guesswork.