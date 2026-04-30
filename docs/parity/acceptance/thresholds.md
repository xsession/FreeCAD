# Parity Acceptance Thresholds

Status: initial threshold template

## Visual Thresholds

- shell screenshot diff threshold: to be approved
- editing surface screenshot diff threshold: to be approved
- viewport screenshot diff threshold: to be approved separately from shell due to render variance

## Structural Thresholds

- menu command coverage for captured shell states: 100 percent visible-command parity
- toolbar command coverage for captured shell states: 100 percent visible-command parity
- panel ordering parity for reviewed states: exact match unless approved deviation exists

## Interaction Thresholds

- workbench switch parity: no missing shell transitions in reviewed flows
- task-panel flow parity: reviewed flows complete without fallback to Qt shell
- viewport navigation parity: orbit, pan, fit-all, and selection accepted by reviewer

## Review Notes

Use this file to replace placeholders with concrete numeric tolerances once baseline capture begins.