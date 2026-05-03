# Lesson 003: React State Typing In `App.tsx`

This lesson uses the main state block in `variants/asterforge/frontend/app/src/App.tsx`.

The goal is to see how TypeScript helps a React component manage many kinds of state without turning into guesswork.

## 1. The state block is a map of the app

This block is worth studying because it tells you what the app cares about:

```ts
const [boot, setBoot] = useState<BootPayload | null>(null);
const [document, setDocument] = useState<DocumentRef | null>(null);
const [shellSnapshot, setShellSnapshot] = useState<ShellSnapshot | null>(null);
const [objectTree, setObjectTree] = useState<ObjectNode[]>([]);
...
const [stepStatus, setStepStatus] = useState<"idle" | "loading" | "ready" | "unavailable" | "error">("idle");
...
const [error, setError] = useState<string | null>(null);
```

This is not only React state. It is a model of the screen.

## 2. When to use `T | null`

Examples:

```ts
useState<BootPayload | null>(null)
useState<DocumentRef | null>(null)
useState<ViewportResponse | null>(null)
```

This pattern means:

- the state will eventually hold a real value of type `T`
- but at startup, the value does not exist yet

In this app, that matches reality. Data loads asynchronously, so `null` is a valid initial state.

This is better than pretending the data already exists.

## 3. When to use empty arrays instead of `null`

Example:

```ts
const [objectTree, setObjectTree] = useState<ObjectNode[]>([]);
const [events, setEvents] = useState<ActivityEvent[]>([]);
```

This tells you a design choice:

- an empty collection is still a meaningful collection
- consumers can iterate immediately without a null check

That is often the right choice for lists.

Practical rule:

- use `null` when a value is absent or not loaded yet
- use `[]` when the value is a collection that can legitimately be empty

## 4. Literal union state for UI modes

Example:

```ts
const [stepStatus, setStepStatus] = useState<"idle" | "loading" | "ready" | "unavailable" | "error">("idle");
```

This is one of the best TypeScript patterns for UI work.

Instead of a vague string, the component only allows five known states.

Benefits:

- fewer typos
- clearer control flow
- easier switch statements and conditions
- the type itself documents the state machine

This repo uses TypeScript not only to describe data, but also to describe UI behavior.

## 5. Inference versus explicit typing

Some state is explicit:

```ts
const [selectedObjectId, setSelectedObjectId] = useState<string | null>(null);
```

Some state relies on inference:

```ts
const [paletteOpen, setPaletteOpen] = useState(false);
const [paletteQuery, setPaletteQuery] = useState("");
const [loading, setLoading] = useState(true);
```

Why inference works there:

- `false` clearly implies boolean
- `""` clearly implies string
- `true` clearly implies boolean

Why explicit types are still needed elsewhere:

- `null` alone is not enough to infer the eventual type
- complex object shapes should be named and explicit

Practical rule:

- let TypeScript infer obvious primitives
- be explicit for nullable and structural state

## 6. `Record<string, Record<string, string>>`

The file also contains richer state shapes such as:

```ts
useState<Record<string, Record<string, string>>>({})
```

Read that as:

- top-level keys are strings
- each top-level value is another object
- that inner object also maps string keys to string values

This is useful for draft form state or command argument maps.

It looks dense at first, but it is just a nested dictionary.

## 7. Types from the protocol layer flow straight into state

Notice how many state types come directly from `protocol.ts`:

- `BootPayload`
- `DocumentRef`
- `ShellSnapshot`
- `PropertyResponse`
- `ViewportResponse`
- `CommandCatalogResponse`

This is a healthy architecture.

The component does not redefine those shapes. It imports the contract types and uses them directly.

That reduces duplication and makes refactors safer.

## 8. Loading code shows why the types matter

In the same file, the `load` function does this:

```ts
const payload = await fetchBootstrap();
setBoot(payload);
setDocument(payload.document);
setShellSnapshot(payload.shell_snapshot);
setObjectTree(payload.object_tree);
setSelectedObjectId(payload.selected_object_id);
...
```

This works smoothly because `fetchBootstrap()` already promises a `BootPayload`.

That means the editor can know that `payload.document`, `payload.viewport`, and `payload.events` exist with specific shapes.

This is the real payoff of strong typing: downstream code becomes simpler.

## 9. How to read a large state block without getting lost

Break the state into categories:

1. backend bootstrap data
2. document and shell data
3. selection and inspection data
4. STEP-specific data
5. UI control state such as menu, palette, loading, and errors

You do not need to memorize every line. You need to learn the patterns.

## 10. Practical checkpoints

You understand this state block if you can explain:

1. why `objectTree` starts as `[]` but `document` starts as `null`
2. why `stepStatus` uses a literal union instead of `string`
3. why `paletteOpen` does not need an explicit generic type argument
4. why imported named types are better than inline anonymous object shapes here

## 11. One design lesson beyond syntax

TypeScript is revealing architecture here.

The app has a contract layer, then a state layer, then a rendering layer. If you learn to spot that flow, large frontend files become easier to reason about.

## 12. Small exercise

Try rewriting these in plain English:

1. `useState<CommandExecutionResponse | null>(null)`
2. `useState<ActivityEvent[]>([])`
3. `useState<"idle" | "loading" | "ready" | "unavailable" | "error">("idle")`

If you can translate them, you are already reading TypeScript instead of just looking at it.