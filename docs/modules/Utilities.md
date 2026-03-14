# Help Module

> **Source**: `src/Mod/Help/` · ~0 .cpp · ~2 .py  
> **Type**: Pure Python (minimal)

## 📋 Overview
Provides the Help viewer — opens FreeCAD wiki documentation and contextual help from within the application. Uses Qt WebEngine or system browser.

---

# Show Module

> **Source**: `src/Mod/Show/` · ~0 .cpp · ~15 .py  
> **Type**: Pure Python

## 📋 Overview
Temporary visibility management for debugging and demonstration. Key classes:

| Class | Purpose |
|---|---|
| `TempoVis` | Save/restore visibility states |
| `TVStack` | Stack of visibility states |
| `SceneDetail` | Individual visibility setting |

Used internally by tools that need to temporarily show/hide objects during operations.

---

# Plot Module

> **Source**: `src/Mod/Plot/` · ~0 .cpp · ~1 .py  
> **Type**: Stub / minimal

## 📋 Overview
Minimal matplotlib integration stub. Most plotting functionality has moved to external add-ons or direct matplotlib use from Python console.

---

*Part of the [FreeCAD Documentation Hub](../README.md)*
