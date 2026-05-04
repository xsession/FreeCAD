# Exercises 001: Repo-Based TypeScript Practice

Use these files while answering:

- `variants/asterforge/frontend/app/src/stepTypes.ts`
- `variants/asterforge/frontend/app/src/protocol.ts`
- `variants/asterforge/frontend/app/src/App.tsx`
- `variants/asterforge/frontend/app/src/App.integration.test.tsx`

## Part A: Read and translate

1. In `stepTypes.ts`, explain `StepAssemblyNode` in plain English.
2. In `stepTypes.ts`, explain why `children: StepAssemblyNode[]` is recursive.
3. In `App.tsx`, explain the difference between `objectId?: string | null` and `selectedObjectId: string | null`.
4. In `protocol.ts`, explain `Promise<ObjectNode[]>` in plain English.
5. In `protocol.ts`, explain `fetchJson<T>` in one sentence.

## Part B: Spot the design choice

1. Find one example where the code uses a union of string literals to model a UI state.
2. Find one example where the code uses `Record<K, V>` to model a dictionary.
3. Find one example where the code uses `Omit` to refine a generated type.
4. Find one example where the code uses `import type`.
5. Find one example where the code uses inferred primitive state instead of an explicit type.

## Part C: Short writing drills

Write one or two sentences for each:

1. Why is `protocol.ts` a boundary module?
2. Why is `stepTypes.ts` a good beginner file?
3. Why are typed React state values useful in a migration project?
4. Why are typed tests useful when mocking modules?

## Part D: Small code exercises

Do these mentally first, then in a scratch file if you want.

1. Define a type alias named `LoadState` with these values: `"idle" | "loading" | "success" | "error"`.
2. Define an interface named `SelectionSummary` with fields `objectId`, `label`, and `kind`, all strings.
3. Define a function signature for `fetchSelectionSummary(documentId: string): Promise<SelectionSummary[]>`.
4. Define a `Record<string, string>` that maps command ids to button labels.

## Part E: Answer key expectations

You are aiming for these ideas, not exact wording:

1. interfaces describe object shapes
2. union types restrict allowed values
3. `null` often means not loaded yet or intentionally empty
4. `[]` often means a valid empty collection
5. `Omit` refines an existing type instead of duplicating it
6. generics let reusable helpers work with many response shapes

## Part F: What to ask next

If you want the next lesson, the best follow-ups are:

1. `stepClient.ts` for typed API helpers around STEP data
2. `shellViewUtils.ts` for utility function signatures and data transformations
3. `App.integration.test.tsx` for deeper typed mocking patterns