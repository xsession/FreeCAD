# FreeCAD Chat Summary - 2026-04-23

## Scope
This session focused on three linked issues in the Windows FreeCAD build:
- imported STEP files appearing in the tree but not in the 3D view
- missing GUI icon resources reported by the launcher
- a blank or non-rendering main GUI after launching the built application

## Outcomes

### 1. STEP import render fix
- Root cause: imported objects were created while import status suppressed view updates, and the GUI import path did not force a visible post-import refresh.
- Fix: after import completion, newly created visible objects now explicitly refresh their view providers before `Std_ViewFitAll`.

File:
- `src/Mod/Import/Gui/AppImportGuiPy.cpp`

### 2. Missing icon warnings fixed
- Root cause: ribbon/search and selection-filter actions referenced icon names that were not present in bundled resources.
- Fix: added the missing SVG assets and registered them in the Qt resource file.

Files:
- `src/Gui/Icons/edit-find.svg`
- `src/Gui/Icons/solid-selection.svg`
- `src/Gui/Icons/resource.qrc`

### 3. Blank GUI on startup resolved
- Root cause: persisted user GUI state in `user.cfg`, specifically saved window geometry and serialized main-window layout state, caused the built FreeCAD GUI to open blank even though startup, plugins, and OpenGL initialization were healthy.
- Confirmation path:
  - launching with a fresh temporary `user.cfg` rendered normally
  - restoring a known-good main-window state into the real profile also restored normal rendering
- Fix applied: backed up the real user config and replaced the problematic main-window restore values with known-good values while preserving the rest of the profile.

User config files involved:
- `C:/Users/livanyi/AppData/Roaming/FreeCAD/v1-2/user.cfg`
- `C:/Users/livanyi/AppData/Roaming/FreeCAD/v1-2/user.cfg.pre-blank-gui-backup`

## Validation
- The Windows build completed successfully after the icon changes.
- Diagnostic startup logs showed normal Qt plugin loading and OpenGL initialization.
- FreeCAD rendered correctly with a clean temporary config.
- FreeCAD rendered correctly again with the repaired real config.

## Current Status
- STEP imports should now refresh visible geometry correctly after import.
- Missing `edit-find` and `solid-selection` icon warnings are addressed.
- The blank-GUI startup problem is resolved for the active user profile.
- A separate warning remains for a corrupted recent project file:
  - `E:/WORK/flow_studio_sims/simplified_whole_detector_curve.FCStd`

## Continuation Plan

### Priority 1: Confirm the import fix in normal use
- Launch the repaired build normally.
- Re-import the previously failing STEP model.
- Confirm the object appears both in the model tree and the 3D view without requiring manual visibility toggles or recompute workarounds.

### Priority 2: Watch for layout-state regression
- Restart FreeCAD a few times with the repaired profile.
- Confirm the blank-GUI problem does not return after the application saves layout state again.
- If it returns, narrow the exact bad preference by comparing only these groups:
  - `BaseApp/Preferences/MainWindow`
  - `BaseApp/MainWindow`

### Priority 3: Investigate the exit/crash artifacts from the clean-config diagnostic run
- Review:
  - `C:/Users/livanyi/AppData/Roaming/FreeCAD/v1-2/crash.log`
  - `C:/Users/livanyi/AppData/Roaming/FreeCAD/v1-2/crash.dmp`
- Determine whether the crash was only an artifact of the diagnostic/temporary-config run or a real shutdown bug worth fixing.

### Priority 4: Handle the corrupted FCStd file separately
- Verify whether `E:/WORK/flow_studio_sims/simplified_whole_detector_curve.FCStd` can be opened or repaired.
- If needed, recover from backup or remove it from recent files to avoid startup noise.

## Files Changed In This Session
- `src/Mod/Import/Gui/AppImportGuiPy.cpp`
- `src/Gui/Icons/resource.qrc`
- `src/Gui/Icons/edit-find.svg`
- `src/Gui/Icons/solid-selection.svg`

## Practical Next Step
Run the built GUI with the repaired profile, re-import the original STEP file, and verify that both the 3D rendering and normal startup behavior remain stable across a clean restart.