# Lesson 006: Typed Test Patterns In `App.integration.test.tsx`

This lesson uses `variants/asterforge/frontend/app/src/App.integration.test.tsx`.

This file is useful because it shows that TypeScript is not only for app code. The test file also depends on type information to keep mocks, imports, and expectations aligned with the implementation.

## 1. Why this file matters

Frontend migrations often break tests by drifting mock shapes away from real module shapes.

This file resists that problem with three patterns:

1. hoisted mock containers
2. typed import of the real module surface
3. tests built around realistic object shapes

## 2. Hoisted mocks

Example:

```ts
const protocolMocks = vi.hoisted(() => ({
  activateWorkbench: vi.fn(),
  fetchBootstrap: vi.fn(),
  ...
}));
```

This tells Vitest to define the mock container early enough for the module-mocking system.

TypeScript benefit:

- the mocked names mirror the actual exported API surface
- you can reason about the test double shape as a stable object

## 3. Partial real-module mocking with type preservation

The strongest line in the file is:

```ts
const actual = await vi.importActual<typeof import("./protocol")>("./protocol");
```

This means:

- import the real module
- keep its module type information
- override only selected exports

That pattern is valuable because it reduces accidental mismatch between the mock layer and the real module.

## 4. Why `typeof import(...)` matters

`typeof import("./protocol")` is a type query over the module itself.

It tells TypeScript:

- use the actual exported shape of the `./protocol` module
- do not guess or manually retype it

That is similar in spirit to deriving types from existing interfaces instead of duplicating them.

## 5. Mocking one layer while leaving another real

Example pattern:

```ts
vi.mock("./protocol", async () => {
  const actual = await vi.importActual<typeof import("./protocol")>("./protocol");
  return {
    ...actual,
    activateWorkbench: protocolMocks.activateWorkbench,
    ...
  };
});
```

This means the test is not replacing everything blindly. It keeps the real module shape and swaps the behavior it needs to control.

That usually produces more stable tests than fully synthetic modules.

## 6. Realistic typed fixture data

The `beforeEach` block constructs rich objects like `document`, `viewport`, `selectionState`, `shellSnapshot`, and `commandCatalog`.

Even when those objects are not explicitly annotated in-place, the test is still benefiting from the surrounding typed module boundaries, because the component and mocked functions consume known shapes.

Practical lesson:

- typed tests are not only about explicit annotations everywhere
- they are also about building fixtures that fit real contracts

## 7. Why this matters in UI tests

The app under test consumes data from:

- `protocol.ts`
- `stepClient.ts`
- React component props and state

If the mocks drift from those contracts, the test can become misleading. TypeScript reduces that risk by keeping the module interfaces visible.

## 8. Reading strategy for typed test files

Read files like this in this order:

1. hoisted mocks
2. `vi.mock` blocks
3. imported component under test
4. fixture setup in `beforeEach`
5. actual test cases and assertions

That order shows what is fake, what is real, and what contract the component expects.

## 9. Checkpoint questions

You understand this file if you can explain:

1. why `vi.hoisted` is used for the mock containers
2. why `vi.importActual<typeof import("./protocol")>` is stronger than a manually typed object
3. why a partially real module is often better than a fully fake one
4. why realistic fixture objects matter in a typed test

## 10. Short mental model

This test file uses TypeScript to keep test doubles close to the real app contract.

The result is not perfect compile-time proof, but it is much less fragile than untyped or loosely structured mocking.