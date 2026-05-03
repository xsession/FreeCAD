# Lesson 002: Protocol Contracts In `protocol.ts`

This lesson uses `variants/asterforge/frontend/app/src/protocol.ts`.

If `stepTypes.ts` teaches you how TypeScript models data, `protocol.ts` teaches you how TypeScript models boundaries.

## 1. Why this file matters

This file is the frontend's typed gateway to the backend. It does three important jobs:

1. imports generated contract types
2. re-exports the useful ones for the rest of the app
3. defines typed fetch helpers that return `Promise<T>`

That means much of the app can stay simple because this file centralizes the contract.

## 2. Start at the top: type-only imports

Example pattern:

```ts
import type {
  BootPayload as GeneratedBootPayload,
  CommandCatalogResponse,
  DocumentRef,
  ShellSnapshot,
  ViewportResponse,
  ...
} from "./generated/asterforge";
```

This tells you the source of truth for many API types is generated code.

What to learn:

- `import type` means these names are used only for static typing
- `BootPayload as GeneratedBootPayload` renames a type locally
- the frontend can build friendlier or refined aliases on top of generated contracts

This is common in serious codebases. Generated types are often accurate but not always ergonomic.

## 3. Re-exporting types

Later in the file:

```ts
export type {
  CommandCatalogResponse,
  DocumentRef,
  ShellSnapshot,
  ViewportResponse,
  ...
};
```

This makes `protocol.ts` an API surface for the frontend itself.

Instead of importing directly from `./generated/asterforge` everywhere, the app can import from one stable module.

That has two benefits:

1. fewer import paths spread around the codebase
2. the team can refine or swap internals without changing every consumer

## 4. `Omit` in real code

This file uses `Omit` several times.

Example:

```ts
export type ActivityEvent = Omit<EventEnvelope, "level" | "object_id"> & {
  level: "info" | "warning" | "error";
  object_id?: string | null;
};
```

Read it as:

1. start with `EventEnvelope`
2. remove `level` and `object_id`
3. add back stricter replacements

Why this is good design:

- it avoids copying the whole original type
- it narrows the fields that the app actually wants
- it preserves the rest of the generated contract

This is one of the most valuable TypeScript patterns in a real project.

Another example:

```ts
export type BootPayload = Omit<GeneratedBootPayload, "events"> & {
  events: ActivityEvent[];
};
```

That means the frontend wants the generated boot payload, except with a refined `events` shape.

## 5. Optional versus required fields in request types

Example:

```ts
export type CommandExecutionRequest = Omit<CommandInvocation, "target_object_id"> & {
  target_object_id?: string | null;
};
```

This is teaching an important API design concept.

The field may be:

- missing entirely
- present as a string
- present as `null`

Those are three different states. TypeScript lets the API express that difference.

## 6. Typed async functions

Example:

```ts
export async function fetchBootstrap(): Promise<BootPayload> {
  return fetchJson<BootPayload>("/api/bootstrap");
}
```

Read this as:

- the function is async
- it returns a `Promise`
- when resolved, that promise yields a `BootPayload`

This is how most frontend-backend code becomes understandable. You do not have to guess what comes back.

Another example:

```ts
export async function fetchObjectTree(documentId: string): Promise<ObjectNode[]> {
  return fetchJson<ObjectNode[]>(`/api/documents/${documentId}/tree`);
}
```

Now you know:

- the argument must be a string
- the result is an array of `ObjectNode`

That is a complete function contract in one line.

## 7. Generic helpers

The bottom of the file contains the key helper:

```ts
async function fetchJson<T>(input: string, init?: RequestInit): Promise<T> {
  const response = await fetch(input, init);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}
```

`<T>` is a generic type parameter.

That means:

- `fetchJson` does not know in advance what shape it returns
- the caller supplies that shape
- the helper stays reusable across many endpoints

When the code calls `fetchJson<BootPayload>(...)`, it specializes the generic for that one use.

## 8. Why this pattern scales

This module is effectively a typed adapter layer.

Without it, components would need to know too much about:

- endpoint paths
- request body shapes
- generated contract details
- response refinement logic

With it, components mostly consume named functions and named types.

That separation is especially useful in this migration project because the frontend is growing while backend contracts are still evolving.

## 9. Practical reading strategy for files like this

When you open a protocol file, read it in this order:

1. imported types
2. exported types
3. refined aliases using `Omit`, `Pick`, or intersections
4. request functions and their `Promise<...>` return types
5. the shared generic helper at the bottom

That reading order prevents overload.

## 10. Checkpoint questions

You understand the core of this file if you can answer these:

1. Why does `ActivityEvent` use `Omit` instead of redefining the full object from scratch?
2. What does `Promise<BootPayload>` tell you that plain JavaScript would not?
3. What does the generic `<T>` in `fetchJson<T>` buy the codebase?
4. Why might the team import generated types but re-export from `protocol.ts`?

## 11. Short mental model

`protocol.ts` is the typed handshake between UI and backend.

The generated file defines raw contract shapes. `protocol.ts` refines them into the exact forms the app wants to use, then exposes small typed functions for each endpoint.

## 12. Next step

Now move to `lesson-003-react-state-typing.md`.

That lesson shows how these protocol types become actual UI state inside `App.tsx`.