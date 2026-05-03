# Lesson 009: Component Prop Typing In `App.tsx`

This lesson uses inline prop typing examples from `variants/asterforge/frontend/app/src/App.tsx`.

This file is useful because it shows a pragmatic style: many components use inline prop object types instead of separately named interfaces.

## 1. Inline prop typing example

One example is `ExtensionCompatibilityPanel`:

```ts
function ExtensionCompatibilityPanel({
  commandCatalog,
  extensionCompatibility,
  onRunCommand,
}: {
  commandCatalog: CommandCatalogResponse | null;
  extensionCompatibility: ExtensionCompatibilityState | undefined;
  onRunCommand: (commandId: string, commandArguments?: Record<string, string>) => void;
}) {
  ...
}
```

This tells you all of the component contract in one place.

That is a reasonable choice when:

- the props are only used by one component
- the prop shape is not reused elsewhere
- locality is more helpful than extracting a separate type name

## 2. Nullable and optional props express real rendering states

Notice these prop types:

- `CommandCatalogResponse | null`
- `ExtensionCompatibilityState | undefined`

That tells you the component is designed to render through incomplete backend state, not just final loaded state.

This is important in real UI code. Components often have to handle loading and absence, not just ideal data.

## 3. Typed callback props

The callback prop is also explicit:

```ts
onRunCommand: (commandId: string, commandArguments?: Record<string, string>) => void;
```

This teaches two things:

- callbacks are part of the component contract, just like data props
- callback parameter types should be visible where the component is declared

That makes components easier to wire correctly.

## 4. Larger prop contracts in UI-heavy components

Another example is `CommandPalette`:

```ts
export function CommandPalette({
  catalog,
  open,
  query,
  onQueryChange,
  onClose,
  onRunCommand,
  targetOptions
}: {
  catalog: CommandCatalogResponse | null;
  open: boolean;
  query: string;
  onQueryChange: (value: string) => void;
  onClose: () => void;
  onRunCommand: (
    commandId: string,
    commandArguments?: Record<string, string>,
    targetObjectId?: string
  ) => void;
  targetOptions: CommandTargetOption[];
}) {
  ...
}
```

This is a full prop contract for a behavior-heavy component.

What to notice:

- booleans model UI mode like `open`
- strings model controlled input state like `query`
- callback signatures model parent-child interaction
- domain arrays like `CommandTargetOption[]` model option lists

## 5. Props and local state work together

Inside `CommandPalette`, local state is typed to match prop-driven workflows:

```ts
const [selectedCommandId, setSelectedCommandId] = useState<string | null>(null);
const [activeTargetObjectId, setActiveTargetObjectId] = useState<string | null>(null);
const [draftArguments, setDraftArguments] = useState<Record<string, Record<string, string>>>({});
```

This is worth noticing because component prop contracts and local state design are usually linked.

The props describe what comes in from the parent. The local state describes what the component derives or edits internally.

## 6. When to keep prop types inline and when to extract them

Inline prop typing is good when:

- the component is local
- the props are not reused
- the contract is still readable inline

Extract a named prop type when:

- the component gets large enough that the inline object becomes noisy
- the props are reused in tests or helper wrappers
- you want a named concept like `CommandPaletteProps`

This file leans toward inline types, which is pragmatic for a large but still local component module.

## 7. Checkpoint questions

You understand this lesson if you can explain:

1. why `CommandCatalogResponse | null` is a useful prop type
2. why callback props should be typed explicitly
3. why `CommandPalette` has both prop state and local state
4. when it would be worth extracting a named props interface

## 8. Short mental model

Component prop typing is just API design at the component level. `App.tsx` shows a pragmatic style where inline prop objects make the local contract obvious without forcing extra type declarations everywhere.