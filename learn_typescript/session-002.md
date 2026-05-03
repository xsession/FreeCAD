# Session 002

Date: 2026-05-03

## Purpose

This is the exercise-driven continuation of the TypeScript learning path built from the AsterForge frontend sources.

Use it after reading:

1. `lesson-001-types-from-real-source.md`
2. `lesson-002-protocol-contracts.md`
3. `lesson-003-react-state-typing.md`
4. `lesson-004-step-client-typing.md`
5. `lesson-005-utility-function-typing.md`
6. `lesson-006-typed-test-patterns.md`
7. `lesson-007-generated-contract-flow.md`
8. `lesson-008-protocol-refinements.md`
9. `lesson-009-component-prop-typing.md`

## Source focus for session 002

- `variants/asterforge/frontend/app/src/protocol.ts`
- `variants/asterforge/frontend/app/src/stepClient.ts`
- `variants/asterforge/frontend/app/src/shellViewUtils.ts`
- `variants/asterforge/frontend/app/src/App.tsx`
- `variants/asterforge/frontend/app/src/App.integration.test.tsx`
- `variants/asterforge/frontend/app/src/generated/asterforge.ts`

## Exercise block A: explain the architecture

Write short answers for these:

1. What is the difference between `generated/asterforge.ts` and `protocol.ts`?
2. Why does `stepClient.ts` define `RenderMeshPacket` instead of only reusing backend payload types?
3. Why does `shellViewUtils.ts` use unions, `Record`, and `Set` instead of loose objects and strings?
4. Why do the tests use `vi.importActual<typeof import("./protocol")>`?

## Exercise block B: translate types into English

Translate these precisely into plain English:

1. `ActivityEvent`
2. `CommandExecutionRequest`
3. `RenderMeshPacket`
4. `StepViewportPreset`
5. `CommandPalette` prop contract

## Exercise block C: small rewrite drills

Write these in a scratch file:

1. A type alias named `NoticeLevel` with `"info" | "warning" | "error"`
2. An interface named `PaletteTarget` with `id`, `label`, and `detail` as strings
3. A function signature for `filterTargets(query: string, items: PaletteTarget[]): PaletteTarget[]`
4. A prop interface named `MiniPaletteProps` with `open`, `query`, `onQueryChange`, and `targets`

## Exercise block D: compare raw and refined types

Use `generated/asterforge.ts` and `protocol.ts` side by side.

Explain the differences between:

1. `EventEnvelope` and `ActivityEvent`
2. `CommandInvocation` and `CommandExecutionRequest`
3. generated `ViewportDiffResponse` and refined `ViewportDiffResponse`
4. generated `BootPayload` and refined `BootPayload`

## Success condition

You are ready to move beyond beginner TypeScript in this repo when you can:

1. read a type and explain it in English
2. tell whether a type is raw, refined, runtime-oriented, or component-local
3. identify where a type belongs architecturally
4. write small functions and prop types without guessing

## What to do next in chat

Answer any block from this file, and the next teaching pass should review your answers, correct mistakes, and append that review into a new markdown file.