# Addon Manager Module

> **Source**: `src/Mod/AddonManager/` · ~0 .cpp · ~99 .py  
> **Dependencies**: FreeCADGui, Qt Network  
> **Type**: Pure Python

## 📋 Overview
Manages installation, update, and removal of FreeCAD add-ons (workbenches, macros, preference packs).

## Key Features
| Feature | Description |
|---|---|
| `Addon` | Addon metadata (name, description, version, URL) |
| `AddonCatalog` | Available addon registry |
| `NetworkManager` | HTTP downloads and git operations |
| `Installer` | Addon installation/removal/update |
| `PackageMetadata` | `package.xml` parser |

### Addon Sources
- **FreeCAD Addons repo** — curated community add-ons
- **Custom URLs** — user-specified git repositories
- **Preference Packs** — UI/keyboard configuration bundles
- **Macro repository** — FreeCAD wiki macros

---
*Part of the [FreeCAD Documentation Hub](../README.md)*
