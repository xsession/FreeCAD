# Lesson 001: Learn TypeScript From Real Source

This lesson uses three real files from the repo:

- `variants/asterforge/frontend/app/src/stepTypes.ts`
- `variants/asterforge/frontend/app/src/App.tsx`
- `variants/asterforge/frontend/app/src/App.integration.test.tsx`

## 1. What TypeScript is doing here

TypeScript is JavaScript plus a type system. In this repo, it is mainly doing four jobs:

1. describing backend payload shapes
2. making React component state safer
3. documenting valid values directly in code
4. helping tests stay aligned with production modules

If JavaScript says, "this value exists at runtime," TypeScript adds, "and here is the shape it is expected to have."

## 2. Start with the simplest file: `stepTypes.ts`

This file is a strong beginner entry point because it mostly defines data shapes.

Example pattern from the file:

```ts
export interface ByteRange {
  start: number;
  end: number;
}
```

What this means:

- `interface` declares the shape of an object
- `start` must be a number
- `end` must be a number
- anything typed as `ByteRange` must contain both fields

In plain JavaScript, you could pass `{ start: 0 }` by mistake. In TypeScript, that mistake is caught early.

Another useful example:

```ts
export type StepApplicationProtocol = "AP203" | "AP214" | "AP242" | string;
```

This is a `type` alias using a union.

What to notice:

- a value can be the string literal `"AP203"`
- or `"AP214"`
- or `"AP242"`
- or any other string

This tells you two things about the codebase design:

- the common protocols are known and named
- the system still allows future or unknown protocol strings

That is a practical TypeScript pattern: be specific where useful, but not artificially closed.

## 3. `interface` versus `type`

This repo uses both. A practical rule for this codebase:

- use `interface` for object shapes, especially API payloads
- use `type` for unions, extracted aliases, and type composition

Examples from the repo:

```ts
export interface StepSceneBundle {
  assemblies: StepAssemblyNode[];
  semantic_pmi: StepPmiAnnotation[];
  tessellated_representations: StepTessellatedFaceSet[];
}

type BottomDockTab = "report" | "python" | "jobs" | "diagnostics" | "history" | "commands" | "extensions";
```

The first describes an object shape. The second describes a limited set of allowed string values.

## 4. Arrays and nesting

This repo models backend data with nested object graphs.

Example:

```ts
export interface StepAssemblyNode {
  entity_id: number;
  label: string;
  children: StepAssemblyNode[];
  brep_ids: number[];
  tessellated_representation_ids: string[];
  pmi_annotation_ids: string[];
}
```

Important TypeScript ideas here:

- `number[]` means array of numbers
- `string[]` means array of strings
- `children: StepAssemblyNode[]` is recursive typing

Recursive typing matters in this project because CAD and assembly data are tree-shaped.

## 5. Move to `App.tsx`: TypeScript inside React

`.ts` files are plain TypeScript.

`.tsx` files are TypeScript plus JSX markup. Use `.tsx` when the file renders React elements.

Example from `App.tsx`:

```ts
type ShellNotice = {
  id: string;
  level: "info" | "warning" | "error";
  title: string;
  detail: string;
  objectId?: string | null;
  commandAction?: ActivityCommandAction | null;
};
```

What to learn from this one block:

- object types can be declared with `type`, not only `interface`
- `level` is a union of allowed string literals
- `objectId?` means the property is optional
- `string | null` means the property may exist but explicitly hold no value

That difference matters:

- `objectId?: ...` means the field might be absent
- `objectId: string | null` means the field must exist, but it may be null

## 6. Typed function parameters and return values

Example:

```ts
function shellNoticePriority(notice: ShellNotice) {
  let priority = 0;
  ...
  return priority;
}
```

Even without writing `: number`, TypeScript infers that the function returns a number because `priority` is numeric.

Example with an explicit return type:

```ts
export function buildShellNotices(
  commandNotices: ShellNotice[],
  eventNotices: ShellNotice[],
  maxNotices = 4
): ShellNotice[] {
  ...
}
```

What this teaches:

- each parameter is typed
- `ShellNotice[]` means array of notices
- `maxNotices = 4` is a default parameter
- the function promises to return `ShellNotice[]`

This is one of the biggest TypeScript wins: function contracts are visible at the call site.

## 7. `Record<K, V>` in real code

This repo uses:

```ts
const STEP_VIEWPORT_COMMAND_BY_PRESET: Record<StepViewportPreset, string> = {
  iso: "step.view_iso",
  front: "step.view_front",
  back: "step.view_back",
  right: "step.view_right",
  left: "step.view_left",
  top: "step.view_top",
  bottom: "step.view_bottom"
};
```

Read `Record<StepViewportPreset, string>` as:

- keys must be valid `StepViewportPreset` values
- values must be strings

This is safer than a loose JavaScript object because TypeScript can tell you when a required preset key is missing.

## 8. Type-only imports

`App.tsx` uses both value imports and type-only imports.

Example:

```ts
import { fetchStepDocumentIndex, fetchStepSceneBundle } from "./stepClient";
import type { StepDocumentIndex, StepSceneBundle, StepTessellatedFaceSet } from "./stepTypes";
```

Why `import type` matters:

- it signals these names are used only for type checking
- it avoids treating them as runtime values
- it makes intent clearer in large codebases

In a migration-heavy project like this one, that clarity helps separate API shape modeling from executable logic.

## 9. Type extraction from existing types

This line in `App.tsx` is an advanced but important pattern:

```ts
type ShellInspectionState = NonNullable<ShellSnapshot["inspection"]>;
```

Break it down:

- `ShellSnapshot["inspection"]` means: get the type of the `inspection` property from `ShellSnapshot`
- `NonNullable<...>` removes `null` and `undefined`

This prevents the app from manually redefining a type that already exists elsewhere.

That is senior-level TypeScript hygiene: derive types from the source of truth instead of duplicating them.

## 10. Tests are TypeScript too

In `App.integration.test.tsx`, this line is worth studying:

```ts
const actual = await vi.importActual<typeof import("./protocol")>("./protocol");
```

This means:

- import the real module
- keep its type information
- use that type information while mocking parts of it

This is valuable because test doubles stay closer to the real module contract.

Another useful pattern:

```ts
const protocolMocks = vi.hoisted(() => ({
  activateWorkbench: vi.fn(),
  fetchBootstrap: vi.fn(),
  ...
}));
```

Even when the mocks are loose here, the surrounding module structure is still typed, which reduces drift between tests and implementation.

## 11. What to practice in this repo right now

Open `stepTypes.ts` and try these exercises:

1. Find every `number[]` and say out loud what real CAD data it represents.
2. Find one recursive type and explain why recursion is necessary.
3. Change one interface mentally into plain English. Example: "A `StepSceneBundle` is an object with assemblies, PMI annotations, and tessellated representations."

Open `App.tsx` and try these exercises:

1. Find every union like `"info" | "warning" | "error"`.
2. Find one optional field and explain how it differs from `null`.
3. Find one inferred return type and one explicit return type.
4. Find one derived type like `NonNullable<ShellSnapshot["inspection"]>` and identify its source type.

Open `App.integration.test.tsx` and try these exercises:

1. Identify what is mocked and what remains real.
2. Find one place where module structure matters more than raw runtime behavior.
3. Explain why typed tests are useful during a frontend migration.

## 12. Mental model to keep

For this project, the fastest way to learn TypeScript is:

1. start from data shapes
2. move to functions that consume those shapes
3. then study components and tests

That order works because the backend payload contracts define most of the frontend design.

## 13. One simple checkpoint

If you understand this sentence, you are on the right track:

"`stepTypes.ts` defines the shape of STEP data, `App.tsx` consumes that typed data in React UI logic, and `App.integration.test.tsx` verifies that behavior with typed module mocks."

## 14. Next lesson

The strongest next step is `src/protocol.ts`.

That file will teach you:

- exported request and response types
- frontend-backend contracts
- how TypeScript organizes larger API surfaces
- how to read a typed integration boundary without getting lost