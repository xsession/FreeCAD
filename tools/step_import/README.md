# STEP Import Toolkit

This folder contains a practical STEP import pipeline for large assemblies:

- `step_chunk_pipeline.py`: run inside `FreeCADCmd` or FreeCAD to import a large STEP file, apply conservative defeaturing, and split the result into smaller chunk files.
- `parallel_step_import.py`: normal Python wrapper that launches multiple `FreeCADCmd` workers to import separate STEP chunks in parallel.
- `launch_freecad_pcores.py`: cross-platform Python launcher that starts FreeCAD with an explicit CPU affinity mask and priority class.

## Important Notes

This repository already contains STEP import optimizations in C++:

- OCCT threading is enabled for STEP parsing/transfer where supported.
- Imported shapes are pre-tessellated in parallel.
- Large STEP files already use relaxed import defaults.

So the workflow here should be treated as an additional operational layer, not as a replacement for the core importer.

Also, "force P-cores only" cannot be inferred reliably on every machine automatically. The launcher therefore accepts an explicit affinity mask. You can get the right mask from a topology tool such as Process Lasso, Task Manager plus CPU documentation, `lscpu`, or your own lab setup.

## Typical Workflow

### 1. Split a large source STEP into manageable chunk STEP files

Run with `FreeCADCmd`:

```powershell
FreeCADCmd.exe tools\step_import\step_chunk_pipeline.py `
  --mode chunk `
  --input C:\data\big_assembly.step `
  --output-dir C:\data\big_assembly_chunks `
  --target-faces 15000 `
  --target-objects 64 `
  --defeature `
  --remove-small-bodies `
  --fillet-threshold-mm 2.0 `
  --ap-schema AP203
```

This will:

- import the source STEP with speed-oriented options,
- remove obviously tiny bodies and optionally simplify some small-radius blend faces,
- export a set of smaller chunk STEP files,
- write a manifest JSON for later batch processing.

### 2. Import those chunks in parallel

Run with your system Python:

```powershell
python tools\step_import\parallel_step_import.py `
  --freecadcmd "C:\Program Files\FreeCAD 1.0\bin\FreeCADCmd.exe" `
  --pipeline-script tools\step_import\step_chunk_pipeline.py `
  --input-dir C:\data\big_assembly_chunks `
  --output-dir C:\data\big_assembly_fcstd `
  --workers 4
```

Each worker launches an isolated `FreeCADCmd` process so separate chunk imports can overlap safely.

### 3. Launch FreeCAD with a P-core-only affinity mask

```shell
python tools/step_import/launch_freecad_pcores.py \
  --exe "C:\Program Files\FreeCAD 1.0\bin\FreeCAD.exe" \
  --affinity-mask-hex 00FF \
  --priority high \
  "C:\data\big_assembly_fcstd\chunk_000.FCStd"
```

## Heuristics Used

The defeaturing logic is intentionally conservative:

- remove whole bodies whose labels look like fasteners,
- remove tiny bodies by volume / bounding-box diagonal,
- optionally try `TopoShape.defeaturing()` on small-radius analytic faces.

This is a heuristic pass, not a guaranteed semantic recognizer. Always validate geometry before downstream manufacturing or analysis.
