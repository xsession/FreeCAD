# Lesson 008: Protocol Refinements In `protocol.ts`

This lesson returns to `variants/asterforge/frontend/app/src/protocol.ts`, but with a narrower focus: why the app refines generated types instead of using them unchanged.

## 1. The key idea

`protocol.ts` is not duplicating the generated contracts. It is adapting them.

The main tool it uses is `Omit<...> & { ... }`.

That pattern means:

1. take an existing type
2. remove one or more fields
3. add back better versions of those fields

## 2. `ActivityEvent`

Generated source:

- `level: string`
- `object_id: string | undefined`

Refined frontend alias:

```ts
export type ActivityEvent = Omit<EventEnvelope, "level" | "object_id"> & {
  level: "info" | "warning" | "error";
  object_id?: string | null;
};
```

Why this is better for the app:

- `level` becomes a known UI-safe union
- `object_id` can be omitted or null, which better matches usage patterns in the frontend

## 3. `BootPayload`

Generated source:

- `events: EventEnvelope[]`

Refined frontend alias:

```ts
export type BootPayload = Omit<GeneratedBootPayload, "events"> & {
  events: ActivityEvent[];
};
```

That means once the event shape is refined, the larger boot payload can reuse the refined version.

This is compositional TypeScript design.

## 4. `CommandExecutionRequest`

Generated source:

- `target_object_id: string | undefined`

Refined frontend alias:

```ts
export type CommandExecutionRequest = Omit<CommandInvocation, "target_object_id"> & {
  target_object_id?: string | null;
};
```

Why this matters:

- callers may omit the field entirely
- callers may explicitly send `null`
- the rest of the request stays exactly aligned with the generated contract

## 5. `ViewportDiffResponse`

Generated source includes required camera arrays.

Refined frontend alias:

```ts
export type ViewportDiffResponse = Omit<GeneratedViewportDiffResponse, "camera_eye" | "camera_target"> & {
  camera_eye?: number[];
  camera_target?: number[];
};
```

This is a useful frontend refinement because partial viewport updates may not always need camera data in the same way the raw contract shape suggests.

The refined type makes that usage more honest.

## 6. `CommandExecutionResponse`

```ts
export type CommandExecutionResponse = Omit<CommandReply, "viewport_diff"> & {
  viewport_diff?: ViewportDiffResponse;
};
```

This builds on the previous refinement.

Important lesson:

- once one nested type is improved, parent types can adopt it
- refinements can layer cleanly when the code stays compositional

## 7. Why this style is better than copying whole interfaces

If the team rewrote every generated interface manually, two problems would appear:

1. duplication
2. drift

Using `Omit` keeps the app close to the generated source while still letting the UI tighten the fields it cares about most.

## 8. Checkpoint questions

You understand this lesson if you can explain:

1. why `ActivityEvent` is stricter than `EventEnvelope`
2. why `BootPayload` reuses `ActivityEvent[]` instead of keeping `EventEnvelope[]`
3. why `ViewportDiffResponse` becomes more optional in the frontend alias
4. why `Omit` is safer than rewriting a full copy of the original interface

## 9. Short mental model

Generated types tell the truth about the protocol. Refined types tell the truth about how the frontend wants to consume that protocol. `protocol.ts` is the layer that reconciles those two truths.