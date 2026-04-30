# F2 Migrate Import, Spreadsheet, Measure, and Material

Status: proposed

## Outcome

Complete support flows needed for normal document work in the new shell.

## Why This Matters

Core modeling is not enough on its own. Users still need import, document support, measurement, and material editing to work before the shell can be considered practical.

## Primary Scope

- `src/Mod/Import`
- `src/Mod/Spreadsheet`
- `src/Mod/Measure`
- `src/Mod/Material`

## In Scope

- import support flows needed for normal onboarding into a document
- spreadsheet and measurement surfaces needed for common workflows
- material editing and inspection flows needed by the new shell

## Out of Scope

- the full specialist surface of every support module on first pass
- external plugin migration

## Deliverables

- TS shell support flows for these modules
- parity notes documenting remaining gaps and deferred features

## Repo Anchors

- `src/Mod/Import`
- `src/Mod/Spreadsheet`
- `src/Mod/Measure`
- `src/Mod/Material`
- `tests/test_flowstudio_step_open_smoke.py`
- `tests/test_flowstudio_step_viewport_profile.py`

## Dependencies

- F1

## Acceptance Checklist

- imported documents and document support surfaces behave acceptably in the TypeScript shell
- import-driven workflows can enter the shell without falling back to Qt-only support panels
- support modules required for normal document work are covered in parity review

## Risks And Notes

- import and material flows often expose shell assumptions that core modeling paths do not