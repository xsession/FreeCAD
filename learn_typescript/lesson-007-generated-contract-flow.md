# Lesson 007: Generated Contract Flow In `generated/asterforge.ts`

This lesson uses `variants/asterforge/frontend/app/src/generated/asterforge.ts`.

This file is the raw type source for much of the frontend. It is generated from protocol definitions, so it should be treated as authoritative but low-level.

## 1. Why generated files matter

Generated types tell you what the backend protocol actually says, not what a frontend developer wishes it said.

That is why this file is useful for learning:

- it reveals the raw contract
- it explains where many frontend types come from
- it shows why the app sometimes refines those types in `protocol.ts`

## 2. Raw interface examples

This file defines interfaces such as:

```ts
export interface CommandInvocation {
  command_id: string;
  document_id: string;
  target_object_id: string | undefined;
  arguments: Record<string, string>;
}
```

```ts
export interface EventEnvelope {
  topic: string;
  level: string;
  message: string;
  document_id: string;
  object_id: string | undefined;
}
```

```ts
export interface BootPayload {
  ...
  events: EventEnvelope[];
  shell_snapshot: ShellSnapshot;
}
```

These are raw transport-level definitions.

## 3. Why raw generated contracts are not always the final app type

Notice some fields are wide or awkward for UI use:

- `level: string`
- `object_id: string | undefined`
- `target_object_id: string | undefined`

Those are accurate as protocol shapes, but the app may want slightly stricter or more ergonomic forms.

That is why `protocol.ts` exists.

## 4. Generated types are still valuable even when refined later

You should not read the existence of refinements as a problem. It is normal.

Good architecture often looks like this:

1. generated raw contract layer
2. frontend refinement layer
3. component and utility consumption layer

This repo follows that pattern clearly.

## 5. How to read a generated file without drowning in it

Do not try to memorize every interface.

Instead:

1. identify the major top-level types the app uses often
2. find which fields are broad or optional
3. compare those with the refined aliases in `protocol.ts`

For this repo, the most useful generated interfaces to compare are:

- `EventEnvelope`
- `CommandInvocation`
- `CommandReply`
- `ViewportDiffResponse`
- `BootPayload`

## 6. Concrete flow example

Raw generated shape:

```ts
export interface EventEnvelope {
  topic: string;
  level: string;
  message: string;
  document_id: string;
  object_id: string | undefined;
}
```

Refined frontend shape in `protocol.ts`:

```ts
export type ActivityEvent = Omit<EventEnvelope, "level" | "object_id"> & {
  level: "info" | "warning" | "error";
  object_id?: string | null;
};
```

That one comparison explains a lot of the frontend architecture.

## 7. Why generated files should usually not be edited

The file itself says it is generated and should not be edited manually.

That means if the contract is wrong, the real fix belongs upstream in the protocol definition or generation pipeline, not in this TypeScript output.

That distinction matters in professional codebases.

## 8. Checkpoint questions

You understand this file if you can explain:

1. why generated types are useful even when the frontend refines them
2. why `level: string` may be accurate but not ideal for UI code
3. why `protocol.ts` sits on top of generated contracts instead of replacing them
4. why editing generated files directly is usually the wrong move

## 9. Short mental model

`generated/asterforge.ts` is the raw contract source. It defines what the wire format looks like. The rest of the frontend becomes easier to understand once you see how `protocol.ts` and the components build on top of it.