# Variant Parity Data

This directory contains machine-readable planning data for the React + Rust FreeCAD variant.

These files are intended to back:

- parity dashboards
- roadmap reporting
- CI coverage checks
- plugin compatibility tracking
- golden workflow planning

## Files

- `parity_matrix.yaml`: top-level parity rows for platform, workbenches, plugins, and workflows
- `workbenches.yaml`: normalized workbench inventory
- `plugins.yaml`: strategic plugin category inventory
- `golden_workflows.yaml`: workflow acceptance inventory

## Conventions

- `status` values should align with the legend in `FREECAD_FULL_PARITY_MATRIX.md`
- `migration_mode` should use `A`, `B`, `C`, or `D`
- `priority` should use `P0`, `P1`, `P2`, or `P3`
- `compatibility_tier` should use `Tier 1`, `Tier 2`, `Tier 3`, or `Tier 4`

## Notes

- This is source-of-truth planning data, not generated output.
- Keep IDs stable once referenced externally.
- Prefer adding fields over changing meanings.
