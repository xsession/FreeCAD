# Parity Acceptance Thresholds

Status: active threshold set for the current screenshot baseline review lane

## Visual Thresholds

- shell screenshot diff threshold: fail review above 0.50 percent differing pixels per full-window shell artifact
- editing surface screenshot diff threshold: fail review above 1.00 percent differing pixels for tree, property, and task-panel crops
- viewport screenshot diff threshold: fail review above 2.50 percent differing pixels for viewport or overlay-focused artifacts
- icon and spacing drift threshold: no more than 2 px positional drift for reviewed toolbar, dock, and property-grid controls unless explicitly approved in the review log
- text drift threshold: no clipped labels, and no more than 1 pt effective font-size drift or 2 px baseline drift in reviewed shell chrome

## Structural Thresholds

- menu command coverage for captured shell states: 100 percent visible-command parity for the reviewed state
- toolbar command coverage for captured shell states: 100 percent visible-command parity for the reviewed state
- panel presence parity for reviewed states: every panel recorded in the baseline metadata must be present in the matching TypeScript review state unless an approved deviation is logged
- panel ordering parity for reviewed states: exact match unless an approved deviation exists in the review log
- metadata completeness for reviewed baselines: required artifact paths and baseline descriptors must be populated for every manifest baseline under review

## Interaction Thresholds

- workbench switch parity: no missing shell transitions, no blank-shell intermediate frame, and no fallback to unmanaged Qt chrome in the reviewed flow
- task-panel flow parity: reviewed flows complete without fallback to Qt shell and retain the expected Tasks or Report docking state through completion
- viewport navigation parity: orbit, pan, fit-all, and selection must complete without broken redraw, lost selection context, or missing overlay state
- command targeting parity: selection-scoped commands must act on the intended object or subelement with no silent retargeting during reviewed flows

## Review Gates

- Gate 1 static shell review passes when shell baselines stay within the shell threshold and meet the structural thresholds
- Gate 2 editing-surface review passes when tree, property, and task-panel baselines stay within the editing-surface threshold and meet the task-flow threshold
- Gate 3 viewport review passes when viewport baselines stay within the viewport threshold and the navigation threshold is satisfied on the reviewed document set

## Review Notes

- these thresholds are intentionally stricter for shell chrome than for viewport artifacts because viewport rendering and selection overlays have higher runtime variance on the current Windows path
- any approved deviation must be recorded in the dated review log under `docs/parity/acceptance/`
- `viewport-selection-light` remains reviewable under the viewport threshold only when the persisted selection-emphasis path described in the review log is used