# 07 — Troubleshooting Guide

> **Classification:** Operations Reference · **Audience:** Developers, QA, Support  
> **Scope:** Diagnosing TNP-related failures in PartDesign DressUp features

---

## 1. Quick Diagnostic Flowchart

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║              TROUBLESHOOTING DECISION TREE                                  ║
║                                                                            ║
║  Symptom: Feature shows error after editing upstream geometry               ║
║                                                                            ║
║  ┌────────────────────────────┐                                            ║
║  │ Is it a Fillet or Chamfer? │                                            ║
║  └─────────┬──────────┬───────┘                                            ║
║         YES│          │NO                                                  ║
║            │          │                                                    ║
║            ▼          ▼                                                    ║
║  ┌──────────────┐  ┌──────────────────────────────┐                        ║
║  │ Check Report │  │ Is it a Pad/Pocket/Sketch    │                        ║
║  │ View for:    │  │ attachment issue?             │                        ║
║  │ "stale,      │  └───────────┬──────────────────┘                        ║
║  │  falling     │              │                                           ║
║  │  back to"    │         See Section 5                                    ║
║  └──────┬───────┘                                                          ║
║         │                                                                  ║
║    ┌────┴────┐                                                             ║
║    │         │                                                             ║
║  Found    Not Found                                                        ║
║    │         │                                                             ║
║    ▼         ▼                                                             ║
║  ┌────────┐ ┌────────────────────────────────────┐                         ║
║  │Fallback│ │ The fix may not be applied.         │                        ║
║  │is      │ │ Check:                              │                        ║
║  │working │ │ 1. Is FeatureDressUp.cpp patched?   │                        ║
║  │ ✅     │ │ 2. Was PartDesign module rebuilt?    │                        ║
║  └────────┘ │ 3. Is the correct .dll/.so loaded?  │                        ║
║             └────────────────────────────────────┘                         ║
║                                                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 2. Common Error Messages

### 2.1 "Invalid edge link: ..."

```
Error: FeatureDressUp.cpp - "Invalid edge link: <name>"

This means getContinuousEdges() could not resolve the edge reference.
```

**Possible Causes:**

| # | Cause | Solution |
|---|-------|----------|
| 1 | Fix not applied | Rebuild PartDesign module |
| 2 | Edge truly deleted (topology changed) | Re-select the edge in the Fillet/Chamfer |
| 3 | Multi-body reference crossing | Ensure Fillet/Chamfer Base references same Body |
| 4 | Corrupt .FCStd file | Try File → Revert, or recompute |

### 2.2 "mapped edge name '...' is stale, falling back to '...'"

```
[WARN] Body.Fillet: mapped edge name 
  ';#f:1;:G;XTR;:H353:7,E.Edge1' is stale, 
  falling back to 'Edge1'
```

**This is informational, not an error!** It means:
- The TNP name couldn't be resolved (expected after mutation)
- The fallback to the short name succeeded
- The feature recomputed correctly

**When to worry:** If this message appears AND the feature is still invalid,
the short name fallback also failed. See Section 4.

### 2.3 "mapped face name '...' is stale, falling back to '...'"

Same as above but for face-based DressUp features (Thickness).

---

## 3. Running Diagnostics

### 3.1 Verify the Fix Is Applied

```powershell
# Check if getContinuousEdges has the fallback
Select-String -Path "src\Mod\PartDesign\App\FeatureDressUp.cpp" -Pattern "falling back to"
```

Expected output: Two matches (one in `getContinuousEdges`, one in `getFaces`).

### 3.2 Run the Test Suite

```powershell
# Full test suite (30 tests)
FreeCADCmd.exe --run-test PartDesignTests.TestSketchOnFace

# Just the Fillet TNP test
FreeCADCmd.exe --run-test PartDesignTests.TestSketchOnFace.testTNP_FilletSurvivesBaseSketchMove

# Just the Chamfer TNP test
FreeCADCmd.exe --run-test PartDesignTests.TestSketchOnFace.testTNP_ChamferSurvivesBaseResize

# Full regression suite
FreeCADCmd.exe --run-test PartDesignTests.TestTopologicalNamingProblem
```

### 3.3 Check Element Map Status

In the FreeCAD Python console:

```python
import FreeCAD as App

doc = App.ActiveDocument
body = doc.getObject("Body")

# Check if element maps are active
print(f"ElementMapVersion: '{body.Shape.ElementMapVersion}'")
# Should print a non-empty string if TNP is active

# Inspect a Pad's element map
pad = doc.getObject("Pad")
print(f"ElementMapSize: {pad.Shape.ElementMapSize}")
print(f"Faces in reverse map: {[k for k in pad.Shape.ElementReverseMap if k.startswith('Face')]}")
print(f"Edges in reverse map: {[k for k in pad.Shape.ElementReverseMap if k.startswith('Edge')]}")
```

### 3.4 Inspect Shadow Subs

```python
# Check what PropertyLinks stores for a Fillet's Base
fillet = doc.getObject("Fillet")

# Get sub-values (what user set)
print(f"SubValues: {fillet.Base[1]}")

# Get shadow subs (TNP internal)
# This requires C++ access — check Report View warnings instead
```

---

## 4. Scenario-Specific Troubleshooting

### 4.1 Fillet Breaks After Moving Sketch

```
┌─────────────────────────────────────────────────────────────────┐
│ Symptom: Fillet shows error marker after moving base sketch     │
│                                                                 │
│ Step 1: Check Report View                                       │
│   └── Look for "stale, falling back to" message                │
│                                                                 │
│ Step 2: If NO fallback message:                                │
│   └── Fix is not applied. Rebuild PartDesign module.           │
│                                                                 │
│ Step 3: If fallback message BUT still broken:                  │
│   └── The edge index changed. This means the topology          │
│       actually changed (e.g., edges were added/removed).       │
│   └── Re-select the edge in the Fillet dialog.                 │
│                                                                 │
│ Step 4: If fallback message AND working:                       │
│   └── Everything is fine! The warning is informational.        │
│       Consider saving to refresh the shadow subs.              │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Tests Fail in CI

```
┌─────────────────────────────────────────────────────────────────┐
│ Symptom: TestSketchOnFace tests fail in CI but pass locally    │
│                                                                 │
│ Check 1: Element Map availability                              │
│   └── TNP tests auto-skip if ElementMapVersion == ""           │
│   └── Ensure CI build has TNP enabled                          │
│                                                                 │
│ Check 2: GUI tests                                             │
│   └── 3 GUI tests auto-skip when App.GuiUp == False            │
│   └── This is expected in headless CI                          │
│                                                                 │
│ Check 3: Build artifact freshness                              │
│   └── Ensure PartDesign module .dll/.so was rebuilt             │
│   └── Check PYTHONPATH includes correct build directory         │
│                                                                 │
│ Check 4: FreeCADCmd availability                               │
│   └── Ensure FreeCADCmd.exe is in PATH                         │
│   └── Set PYTHONHOME to pixi env if needed                     │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 DLL Lock During Build

```
┌─────────────────────────────────────────────────────────────────┐
│ Symptom: Ninja fails with "cannot open ... .dll for writing"   │
│                                                                 │
│ Cause: FreeCAD or FreeCADCmd is still running with the DLL     │
│        loaded.                                                 │
│                                                                 │
│ Fix:                                                           │
│   taskkill /im FreeCAD.exe /f                                  │
│   taskkill /im FreeCADCmd.exe /f                               │
│   # Then rebuild                                               │
│   ninja -j4 PartDesign                                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Non-DressUp TNP Issues

If the TNP issue is NOT in a DressUp feature, this fix does not apply.
Check these resources:

| Issue | Relevant Code | Test Suite |
|-------|--------------|------------|
| Pad/Pocket attachment | `PropertyLinks.cpp` | `TestTopologicalNamingProblem` |
| Revolution | `FeatureRevolution.cpp` | `TestTopologicalNamingProblem` |
| Loft/Pipe | `FeatureLoft.cpp`, `FeaturePipe.cpp` | `TestTopologicalNamingProblem` |
| Element map corruption | `ElementMap.cpp` | `TestTopologicalNamingProblem` |
| Sketch attachment | `AttachEngine.cpp` | `TestSketchOnFace` (tests 12–13) |

---

## 6. Environment Setup Reference

For running tests manually:

```powershell
# Windows (PowerShell with pixi)
$env:PYTHONPATH = "C:\GIT\FreeCAD\.pixi\envs\default\Lib\site-packages;" +
                  "C:\GIT\FreeCAD\build\debug\bin;" +
                  "C:\GIT\FreeCAD\build\debug\lib;" +
                  "C:\GIT\FreeCAD\build\debug\Mod;" +
                  "C:\GIT\FreeCAD\build\debug\Ext"
$env:PYTHONHOME = "C:\GIT\FreeCAD\.pixi\envs\default"
$env:PATH = "C:\GIT\FreeCAD\.pixi\envs\default\Library\bin;" +
            "C:\GIT\FreeCAD\.pixi\envs\default;" +
            "C:\GIT\FreeCAD\build\debug\bin;" +
            $env:PATH
$env:QT_PLUGIN_PATH = "C:\GIT\FreeCAD\.pixi\envs\default\Library\plugins"

# Run tests
C:\GIT\FreeCAD\build\debug\bin\FreeCADCmd.exe --run-test PartDesignTests.TestSketchOnFace
```

---

## 7. Log Level Configuration

To increase logging verbosity for TNP debugging:

```python
# In FreeCAD Python console:
import FreeCAD
FreeCAD.Console.SetStatus("PartDesign", "Log", True)
FreeCAD.Console.SetStatus("PartDesign", "Wrn", True)

# This enables FC_LOG and FC_WARN output from FeatureDressUp.cpp
# Look for: "mapped edge name '...' is stale, falling back to '...'"
```

---

## 8. Diagnostic Checklist

Use this checklist when investigating a DressUp TNP issue:

```
□ Is ElementMapVersion non-empty? (body.Shape.ElementMapVersion)
□ Is the fix applied? (grep for "falling back to" in FeatureDressUp.cpp)
□ Was the module rebuilt after the fix? (check build timestamp)
□ Is the correct binary loaded? (check PYTHONPATH / PATH)
□ What does Report View say? (look for warnings)
□ Does the feature work after manual recompute? (Ctrl+Shift+R)
□ Does the feature work after save/reopen?
□ Is the edge/face reference valid? (check Base property in properties panel)
□ Did the topology actually change? (edges added/removed vs. just moved)
□ Do the 30 unit tests pass? (FreeCADCmd --run-test PartDesignTests.TestSketchOnFace)
```

---

*Next: [08 — Glossary](./08_glossary.md)*
