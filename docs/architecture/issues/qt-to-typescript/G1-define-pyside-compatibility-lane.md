# G1 Define PySide Compatibility Lane

Status: proposed

## Outcome

Prevent PySide-heavy modules from blocking the initial shell cutover.

## Why This Matters

Bundled Python UI surfaces, especially in AddonManager and BIM, are too large to disappear instantly. A compatibility strategy is required so the migration does not stall on all PySide surfaces at once.

## Primary Scope

- `src/Mod/AddonManager/**`
- `src/Mod/BIM/**`
- Python UI helpers using `FreeCADGui.PySideUic`

## In Scope

- transition policy for PySide-heavy bundled modules
- criteria for compatibility lane versus full migration priority
- deprecation and replacement staging

## Out of Scope

- immediate rewrite of all PySide UIs
- final plugin API design in complete detail

## Deliverables

- compatibility lane definition
- module classification and policy note
- migration guidance for bundled Python UI owners

## Repo Anchors

- `src/Mod/AddonManager/**`
- `src/Mod/BIM/**`
- `src/Ext/freecad/UiTools.py`
- `docs/PYSIDE_USAGE_TABLE.md`

## Dependencies

- plugin and compatibility policy definition

## Acceptance Checklist

- there is a written, supported transition strategy for PySide-heavy bundled modules
- the highest-risk modules have explicit treatment rules instead of generic migration language
- the shell roadmap is no longer blocked on rewriting all PySide modules first

## Risks And Notes

- a vague compatibility lane will become permanent technical debt; define entry and exit rules clearly