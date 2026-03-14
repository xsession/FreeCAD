# PartDesign TNP Resolution — Enterprise Documentation

> **Version** 1.0.0 · **FreeCAD** 1.2.0-dev · **Date** 2026-03-14

---

## 📚 Documentation Index

| # | Document | Description |
|---|----------|-------------|
| 1 | [**Overview**](./01_overview.md) | Executive summary, project goals, and scope |
| 2 | [**Architecture Deep-Dive**](./02_architecture.md) | Element map system, PropertyLinks, shadow subs |
| 3 | [**C++ Fix Technical Reference**](./03_cpp_fix_reference.md) | Detailed analysis of the `FeatureDressUp.cpp` patch |
| 4 | [**Test Suite Documentation**](./04_test_suite.md) | All 30 tests — purpose, category, and expected behavior |
| 5 | [**Infographics & Diagrams**](./05_infographics.md) | ASCII architecture diagrams, data-flow charts, decision trees |
| 6 | [**Changelog & History**](./06_changelog_history.md) | Git archaeology, timeline, and version history |
| 7 | [**Troubleshooting Guide**](./07_troubleshooting.md) | Common failures, debugging steps, and diagnostic tools |
| 8 | [**Glossary**](./08_glossary.md) | Terminology reference for TNP, element maps, and FreeCAD internals |

---

## 🎯 Quick Start

```
# Run the full test suite (30 tests)
FreeCADCmd.exe --run-test PartDesignTests.TestSketchOnFace

# Run existing TNP regression suite (68 tests)
FreeCADCmd.exe --run-test PartDesignTests.TestTopologicalNamingProblem
```

## 📊 Status Dashboard

```
┌─────────────────────────────────────────────────────────┐
│              TEST SUITE STATUS DASHBOARD                │
├─────────────────────────┬───────┬───────┬───────────────┤
│ Suite                   │ Pass  │ Fail  │ Status        │
├─────────────────────────┼───────┼───────┼───────────────┤
│ TestSketchOnFace        │ 30/30 │  0    │ ✅ ALL PASS   │
│ TestTopologicalNaming   │ 68/68 │  0    │ ✅ ALL PASS   │
├─────────────────────────┼───────┼───────┼───────────────┤
│ TOTAL                   │ 98/98 │  0    │ ✅ ZERO REGR. │
└─────────────────────────┴───────┴───────┴───────────────┘
```

## 🏗️ Files Modified

| File | Type | Change |
|------|------|--------|
| `App/FeatureDressUp.cpp` | C++ | TNP fallback in `getContinuousEdges()` + `getFaces()` |
| `PartDesignTests/TestSketchOnFace.py` | Python | New — 30 comprehensive tests |
| `PartDesignTests/__init__.py` | Python | Registration import |
| `TestPartDesignApp.py` | Python | Registration import |

---

*Generated for FreeCAD PartDesign module — LGPL-2.1-or-later*
