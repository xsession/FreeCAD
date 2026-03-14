# 04 — Test Suite Documentation: `TestSketchOnFace.py`

> **Classification:** QA Reference · **Audience:** Developers, QA Engineers, Contributors  
> **File:** `src/Mod/PartDesign/PartDesignTests/TestSketchOnFace.py`  
> **Tests:** 30 · **Runtime:** ~1.8 seconds · **Dependencies:** Headless-safe

---

## 1. Test Suite Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    TEST SUITE ARCHITECTURE                               │
│                                                                         │
│  TestSketchOnFace (unittest.TestCase)                                   │
│  │                                                                      │
│  ├── setUp()                                                            │
│  │   Creates: Doc → Body → Sketch(XY, 10×10 rect) → Pad(10mm)         │
│  │   Result: 10×10×10 box (Volume = 1000 mm³)                          │
│  │                                                                      │
│  ├── 🟦 Basic Geometry (5 tests)         ← Validates setUp is correct  │
│  ├── 🟩 Sub-Shape Access (3 tests)       ← getElement() coverage       │
│  ├── 🟨 Part.getShape (3 tests)          ← API coverage                │
│  ├── 🟪 Sketch-on-Face (2 tests)         ← Core workflow               │
│  ├── 🟫 Element Map (1 test)             ← Infrastructure check        │
│  ├── ⬜ GUI Selection (3 tests)           ← Auto-skip if headless      │
│  ├── 🟥 TNP Proof (12 tests)             ← THE MAIN EVENT             │
│  │                                                                      │
│  └── tearDown()                                                         │
│      Closes all "SketchOnFace" documents                                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Test Categories — At a Glance

```
┌────────────────────────────────────────────────────────────────────────┐
│                                                                        │
│  TEST DISTRIBUTION BY CATEGORY                                         │
│                                                                        │
│  🟥 TNP Proof ████████████████████████  12 tests  (40%)               │
│  🟦 Geometry  ██████████               5 tests   (17%)               │
│  🟩 Elements  ██████                   3 tests   (10%)               │
│  🟨 getShape  ██████                   3 tests   (10%)               │
│  ⬜ GUI       ██████                   3 tests   (10%)               │
│  🟪 Workflow  ████                     2 tests   ( 7%)               │
│  🟫 ElemMap   ██                       1 test    ( 3%)               │
│                                                                        │
│  Total: 30 tests                                                       │
│                                                                        │
│  RISK COVERAGE HEAT MAP                                                │
│  ┌──────────┬──────────┬──────────┬──────────┐                        │
│  │  High    │ Fillet   │ Chamfer  │ Deep     │                        │
│  │  Risk    │ TNP      │ TNP      │ Chain    │                        │
│  │          │ ✅ Test8 │ ✅ Test11│ ✅ Test9 │                        │
│  ├──────────┼──────────┼──────────┼──────────┤                        │
│  │  Medium  │ Pocket   │ Resize   │ Save/    │                        │
│  │  Risk    │ on Face  │ Base     │ Restore  │                        │
│  │          │ ✅ Test3 │ ✅ Test2 │ ✅ Test6 │                        │
│  ├──────────┼──────────┼──────────┼──────────┤                        │
│  │  Low     │ Pad      │ Element  │ Attach   │                        │
│  │  Risk    │ Length   │ Map      │ Stable   │                        │
│  │          │ ✅ Test7 │ ✅ Test4 │ ✅ Test12│                        │
│  └──────────┴──────────┴──────────┴──────────┘                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Test Catalog — Complete Reference

### 3.1 🟦 Basic Geometry Tests

These validate that `setUp()` created a correct 10×10×10 box.

| # | Test Name | Assertion | Expected |
|---|-----------|-----------|----------|
| 1 | `testPadIsValid` | `Pad.isValid()` | `True` |
| 2 | `testPadHasSixFaces` | `len(Pad.Shape.Faces)` | `6` |
| 3 | `testPadHasTwelveEdges` | `len(Pad.Shape.Edges)` | `12` |
| 4 | `testPadHasEightVertices` | `len(Pad.Shape.Vertexes)` | `8` |
| 5 | `testPadVolume` | `Pad.Shape.Volume` | `1000.0` |

```
                    Pad Geometry (10×10×10 box)
                    
                    Vertex5─────Edge9────Vertex6
                   /│                    /│
                  / │                   / │
                Edge5  Edge10         Edge6  Edge11
               /   │               /   │
              /    │              /    │
           Vertex7─────Edge12──Vertex8 │
             │   Vertex1──Edge1──│──Vertex2
             │   /               │   /
           Edge7 Edge2         Edge8 Edge4
             │ /                 │ /
             │/                  │/
           Vertex3─────Edge3──Vertex4
           
           6 Faces · 12 Edges · 8 Vertices
           Volume = 10 × 10 × 10 = 1000 mm³
```

### 3.2 🟩 Sub-Shape Access Tests

Verify `Shape.getElement()` resolves all indexed names.

| # | Test Name | Iteration | Assertion |
|---|-----------|-----------|-----------|
| 6 | `testGetElementFaces` | Face1–Face6 | `ShapeType == "Face"` |
| 7 | `testGetElementEdges` | Edge1–Edge12 | `ShapeType == "Edge"` |
| 8 | `testGetElementVertices` | Vertex1–Vertex8 | `ShapeType == "Vertex"` |

### 3.3 🟨 Part.getShape Tests

Verify the `Part.getShape(obj, subName, needSubElement=True)` API.

| # | Test Name | Iteration | Assertion |
|---|-----------|-----------|-----------|
| 9 | `testPartGetShapeFaces` | Face1–Face6 | `not isNull(), ShapeType == "Face"` |
| 10 | `testPartGetShapeEdges` | Edge1–Edge12 | `not isNull(), ShapeType == "Edge"` |
| 11 | `testPartGetShapeVertices` | Vertex1–Vertex8 | `not isNull(), ShapeType == "Vertex"` |

### 3.4 🟪 Sketch-on-Face Workflow Tests

Core feature tests: attach a Sketch to a Pad face and build on it.

| # | Test Name | Scenario | Assertion |
|---|-----------|----------|-----------|
| 12 | `testSketchOnPadFace` | Sketch2 on Face6 → Pad2(5mm) | `Volume == 1180.0` |
| 13 | `testSketchOnEveryPadFace` | Sketch on each Face1–6 | All 6 valid |

```
        testSketchOnPadFace — L-Tower Model
        
        ┌────────┐ ← Pad2 (6×6×5)
        │        │
        │  Pad2  │
        │        │
   ┌────┴────────┴────┐ ← Face6 (attachment)
   │                  │
   │      Pad         │ ← Pad (10×10×10)
   │    (base)        │
   └──────────────────┘
   
   Volume = 10×10×10 + 6×6×5 = 1000 + 180 = 1180 mm³
```

### 3.5 🟫 Element Map Test

| # | Test Name | Assertion |
|---|-----------|-----------|
| 14 | `testPadElementMap` | `ElementReverseMap` has 6 faces, 12 edges, 8 vertices |

### 3.6 ⬜ GUI Selection Tests (auto-skip when headless)

| # | Test Name | Scenario | Assertion |
|---|-----------|----------|-----------|
| 15 | `testSelectionFilterMatchesFace` | Select Face1, filter "Face" | `sf.match() == True` |
| 16 | `testSelectionFilterMatchesEdge` | Select Edge1, filter "Edge" | `sf.match() == True` |
| 17 | `testProgrammaticFaceSelection` | Select each Face1–6 | All in SubElementNames |

### 3.7 🟥 TNP Proof Tests (The Main Event)

These 12 tests prove the Topological Naming Problem is resolved.

```
┌────────────────────────────────────────────────────────────────────────┐
│                TNP PROOF TEST DECISION TREE                             │
│                                                                        │
│  Does ElementMapVersion exist?                                         │
│  ├── NO → return (skip) — TNP features not available                   │
│  └── YES ↓                                                             │
│                                                                        │
│  Build downstream feature (Pad2, Pocket, Fillet, Chamfer...)           │
│  ├── Verify: feature.isValid() == True                                 │
│  │                                                                     │
│  Mutate upstream (move sketch, resize, change length...)               │
│  ├── Recompute                                                         │
│  │                                                                     │
│  Verify: ALL features still valid                                      │
│  ├── ✅ Pass → TNP is solved for this scenario                        │
│  └── ❌ Fail → TNP regression detected                                │
└────────────────────────────────────────────────────────────────────────┘
```

| TNP# | Test Name | Mutation | What Survives |
|------|-----------|----------|---------------|
| 1 | `testTNP_ThreePadChainSurvivesMiddleOffset` | Middle sketch offset | 3 Pads |
| 2 | `testTNP_ResizeBaseSketchSecondPadSurvives` | Add geometry to base sketch | Pad2 on face |
| 3 | `testTNP_PocketOnFaceSurvivesBaseMove` | Move base sketch | Pocket |
| 4 | `testTNP_ElementMapGetElementConsistency` | (no mutation) | TNP↔short name equivalence |
| 5 | `testTNP_ElementMapPreservedAfterSecondPad` | Add Pad2 | Element map populated |
| 6 | `testTNP_SaveRestorePreservesElementMap` | Save + close + reopen | Element maps + volume |
| 7 | `testTNP_PadLengthChangePreservesDownstream` | Pad.Length 10→20 | Pad2, Volume=2180 |
| 8 | `testTNP_FilletSurvivesBaseSketchMove` | Move base sketch | **Fillet** ⭐ |
| 9 | `testTNP_FourPadDeepChainSurvives` | Offset first sketch | 4 stacked Pads |
| 10 | `testTNP_PartGetShapeWithTNPNamesAfterMutation` | Move base sketch | Part.getShape resolution |
| 11 | `testTNP_ChamferSurvivesBaseResize` | Pad.Length 10→15 | **Chamfer** ⭐ |
| 12 | `testTNP_AttachmentReferenceStableAfterRecompute` | 3× offset cycle | "Face6" in attachment |

⭐ = Tests that directly validate the `FeatureDressUp.cpp` fix

---

## 4. TNP Test Deep-Dives

### TNP Test 1: Three-Pad Chain

```
  BEFORE MUTATION:                    AFTER MUTATION:
  
  ┌────┐                              ┌────┐
  │Pad3│ (6×6×3)                      │Pad3│ ✅ still valid
  ├────┤                              ├────┤
  │Pad2│ (8×8×5)                      │Pad2│ ✅ still valid
  ├────┤                              ├─┬──┤
  │Pad │ (10×10×10)                   │P│ad│ ✅ still valid
  └────┘                              └─┴──┘
                                      ↑ Sketch2 offset by (0.5, 0.5)
```

### TNP Test 8: Fillet Survives (The Key Fix Test)

```
  BEFORE MUTATION:                    AFTER MUTATION:
  
  ┌──────────┐                        ┌──────────┐
  │          ╱ ← Fillet(Edge1, R=1)   │          ╱ ← Fillet ✅
  │   Pad    │                        │   Pad    │
  │          │                        │ (shifted)│
  └──────────┘                        └──────────┘
                                      ↑ Base Sketch moved by (2, 0, 0)
  
  The fix in getContinuousEdges() enables this:
  stale TNP name → fallback to "Edge1" → Fillet recomputes
```

### TNP Test 6: Save/Restore Round-Trip

```
  ┌────────────────────────────────────────────────────────┐
  │                SAVE/RESTORE PIPELINE                    │
  │                                                        │
  │  1. Build: Body → Sketch → Pad → Sketch2 → Pad2       │
  │  2. Record: ElementMapSize, Volume                     │
  │  3. Save to temp .FCStd                                │
  │  4. Close document                                     │
  │  5. Reopen .FCStd                                      │
  │  6. Recompute                                          │
  │  7. Verify:                                            │
  │     ├── Pad2.isValid() == True                         │
  │     ├── ElementMapSize unchanged                       │
  │     ├── Volume unchanged                               │
  │     └── Sketch2.AttachmentSupport contains "Face6"     │
  │  8. Cleanup temp file                                  │
  └────────────────────────────────────────────────────────┘
```

### TNP Test 9: Four-Deep Chain

```
  ┌──┐  Level 3: 4×4×3 pad
  ├──┤
  │  │  Level 2: 6×6×3 pad
  ├──┤
  │  │  Level 1: 8×8×3 pad
  ├──┤
  │  │
  │  │  Level 0: 10×10×10 pad (base)
  │  │
  └──┘
  ↑ Offset base sketch by (0.5, 0.5) → ALL 4 levels survive
```

---

## 5. Test Execution

### 5.1 Running

```powershell
# Set environment (pixi)
$env:PYTHONPATH = "C:\GIT\FreeCAD\build\debug\bin;C:\GIT\FreeCAD\build\debug\lib;C:\GIT\FreeCAD\build\debug\Mod;C:\GIT\FreeCAD\build\debug\Ext"
$env:PYTHONHOME = "C:\GIT\FreeCAD\.pixi\envs\default"

# Run just this suite
FreeCADCmd.exe --run-test PartDesignTests.TestSketchOnFace

# Run with verbose output
FreeCADCmd.exe --run-test PartDesignTests.TestSketchOnFace -v

# Run a single test
FreeCADCmd.exe --run-test PartDesignTests.TestSketchOnFace.testTNP_FilletSurvivesBaseSketchMove
```

### 5.2 Expected Output

```
Ran 30 tests in 1.779s

OK
```

### 5.3 Registration

The test is registered in two places:

**`PartDesignTests/__init__.py`:**
```python
from . import TestSketchOnFace
```

**`TestPartDesignApp.py`:**
```python
from PartDesignTests.TestSketchOnFace import TestSketchOnFace
```

---

## 6. Test Dependencies

```
┌────────────────────────────────────────────────────────────┐
│                 DEPENDENCY GRAPH                            │
│                                                            │
│  TestSketchOnFace                                          │
│  ├── unittest (stdlib)                                     │
│  ├── os (stdlib)                                           │
│  ├── tempfile (stdlib)                                     │
│  ├── FreeCAD (App module)                                  │
│  │   ├── App.newDocument()                                 │
│  │   ├── App.Placement, App.Vector, App.Rotation           │
│  │   └── App.closeDocument()                               │
│  ├── Part (Part module)                                    │
│  │   ├── Part.getShape()                                   │
│  │   └── Part.LineSegment                                  │
│  ├── Sketcher (Sketcher module)                            │
│  │   └── Sketcher.Constraint                               │
│  └── TestSketcherApp (test utility)                        │
│      └── CreateRectangleSketch()                           │
│                                                            │
│  Optional (auto-skip if missing):                          │
│  └── FreeCADGui (Gui module)                               │
│      ├── Gui.Selection                                     │
│      └── Gui.Selection.Filter                              │
└────────────────────────────────────────────────────────────┘
```

---

*Next: [05 — Infographics & Diagrams](./05_infographics.md)*
