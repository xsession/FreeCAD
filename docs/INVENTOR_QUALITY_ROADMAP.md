# FreeCAD → Inventor-Quality UX Roadmap

Goal: Achieve speed, stability, clean visual presentation, and smooth user experience
comparable to Autodesk Inventor.

## Current State Analysis

| Area | FreeCAD Today | Inventor Target |
|------|--------------|-----------------|
| Anti-aliasing | Default OFF (None) | MSAA 4x+ always |
| Lighting | 1 headlight, backlight/fill OFF | 3-point lighting active |
| Shading | Gouraud (per-vertex) | Per-pixel Phong / PBR |
| Edges | Expensive full-wireframe or none | Smart silhouette edges |
| Background | Blue-gray gradient (0.5,0.5,0.8) | Professional dark/neutral |
| VBO | Disabled by default | GPU-accelerated always |
| Render caching | Auto (coin caching OFF workaround) | Aggressive scene caching |
| Transparency | SORTED_OBJECT_SORTED_TRIANGLE | Order-independent (OIT) |
| Shadows/AO | None | SSAO + soft shadows |
| LOD | None (full mesh always) | Distance-adaptive LOD |
| Selection | Green highlight (emissive) | Subtle blue glow + outline |
| Navigation | Smooth but basic | Inertial + animated transitions |

---

## Phase A: Visual Quality Quick-Wins (No Architecture Changes)

Changes that improve perceived quality immediately by tuning existing parameters.
**Impact: HIGH | Risk: LOW | Effort: SMALL**

### A1. Enable MSAA 4x by Default
- File: `src/Gui/Multisample.cpp` → `readMSAAFromSettings()`
- Change default from `AntiAliasing::None` to `AntiAliasing::MSAA4x`
- File: `src/Gui/Application.cpp` → QSurfaceFormat setup
- Add `defaultFormat.setSamples(4)` to ensure framebuffer supports it

### A2. Professional Background Colors
- File: `src/Gui/Inventor/SoFCBackgroundGradient.cpp`
- Current defaults: fCol(0.5,0.5,0.8) tCol(0.7,0.7,0.9) — dated blue
- New Inventor-style: dark charcoal gradient
  - Top: (0.22, 0.23, 0.25) — dark slate
  - Mid: (0.28, 0.30, 0.33) — medium slate
  - Bottom: (0.18, 0.19, 0.21) — near-black
- File: `src/Gui/View3DInventorViewer.cpp` L687
- Change `setBackgroundColor(QColor(25, 25, 25))` to match

### A3. Enable 3-Point Lighting by Default
- File: `src/Gui/View3DInventorViewer.cpp` L507-515
- Change `backlight->on.setValue(false)` → `true`
- Change `fillLight->on.setValue(false)` → `true`
- Tune backlight intensity: 0.3 (subtle), direction opposite headlight
- Result: Professional studio lighting eliminating harsh shadows

### A4. Modern Selection Colors
- File: `src/Gui/Selection/SoFCUnifiedSelection.cpp`
- Change selection color from bright green (0.1,0.8,0.1) to professional blue (0.2,0.5,0.9)
- Change preselection (hover) to subtle warm highlight (0.9,0.7,0.2)

### A5. Better Default Shape Colors
- File: `src/Gui/ViewParams.h` → FC_VIEW_PARAMS
- `DefaultShapeColor`: 0xCCCCCC00 → 0xC8CBD000 (slight blue-steel tint)
- `DefaultShapeLineColor`: 421075455 → 0x20202000 (darker, subtle edges)
- `DefaultShapeLineWidth`: 2 → 1 (thinner, cleaner edges)

### A6. Enable VBO by Default
- File: `src/Gui/Application.cpp` L499
- Current: `UseVBO` default false, AND the code DISABLES it: `coin_setenv("COIN_VBO", "0", true)`
- Fix: invert the logic — enable VBO by default, disable only if preference says so
- Modern GPUs (even Intel HD 4000+) handle VBO fine

---

## Phase B: Rendering Quality Improvements (Moderate Changes)

### B1. Depth Buffer & Stencil Buffer on All Platforms
- File: `src/Gui/Application.cpp` QSurfaceFormat setup
- Currently only Wayland gets depth=24/stencil=8
- Add for ALL platforms: `setDepthBufferSize(24)`, `setStencilBufferSize(8)`
- Fixes z-fighting on Windows/macOS

### B2. Smooth Edge Rendering (Silhouette Edges)
- Instead of rendering ALL edges (expensive) or NO edges:
- Implement silhouette-only edge detection in a custom SoNode
- Only draw edges where surface normal changes > crease angle
- File: new `src/Gui/Inventor/SoFCSilhouetteEdge.cpp`
- Uses depth buffer + normal discontinuity detection

### B3. Higher Crease Angle for Smoother Shading
- File: `src/Gui/SoFCDB.cpp` L482 → crease angle 0.5 rad
- Increase to ~1.2 rad (70°) for smoother curved surfaces
- Add per-ViewProvider crease angle override

### B4. Screen-Space Ambient Occlusion (SSAO) Post-Process
- New post-processing pass after main render
- File: new `src/Gui/Inventor/SoFCSSAO.cpp`
- Uses depth buffer to compute contact shadows
- Subtle effect (radius ~0.5, intensity ~0.3) for depth perception
- Toggle via preferences, default ON

### B5. Improved Transparency
- Replace SORTED_OBJECT_SORTED_TRIANGLE_BLEND with
  weighted blended order-independent transparency (McGuire/Bavoil 2013)
- Two-pass: accumulation + revealage
- Eliminates sort artifacts on overlapping transparent objects

---

## Phase C: Performance & Responsiveness

### C1. Render Cache Mode = Distributed by Default
- File: `src/Gui/ViewParams.h` → `RenderCache` default 0 → 1
- Distributed caching (mode 1) is faster for complex assemblies
- Auto mode (0) falls back to distributed anyway when coin caching is off

### C2. Adaptive Tessellation LOD
- Implement camera-distance-based LOD for tessellated shapes
- Near objects: full resolution mesh
- Far objects: simplified mesh (2x-4x reduction)
- File: extend `src/Mod/Part/LargeModelOptimizer.py` + C++ SoLOD wrapper

### C3. Frustum Culling
- Skip rendering objects completely outside the view frustum
- Coin3D has basic bounding box culling but it's not aggressive
- File: new `src/Gui/Inventor/SoFCFrustumCull.cpp`

### C4. Inertial Navigation
- Add momentum/deceleration to rotation and pan
- After mouse release, smoothly decelerate rotation
- File: `src/Gui/Navigation/NavigationStyle.cpp`
- Add animation timer for inertial spin-down

### C5. Animated View Transitions
- When switching views (front, top, isometric), animate the camera
- File: `src/Gui/View3DInventorViewer.cpp`
- Use SoTimerSensor to interpolate camera position over ~300ms

---

## Phase D: Advanced Visual Effects

### D1. PBR Material Support
- Replace SoMaterial (Phong) with custom PBR node
- Metalness/roughness workflow
- Environment map for reflections (HDR cubemap)
- Requires GLSL shader pipeline

### D2. Soft Shadow Mapping
- Directional light shadow map (2048x2048)
- PCF (Percentage Closer Filtering) for soft edges
- Only for main directional light

### D3. Edge Outline Post-Process
- Sobel filter on depth + normal buffer
- Clean, consistent 1px edge lines regardless of geometry
- Much cheaper than geometric edge rendering

### D4. HDR Rendering Pipeline
- Render to floating-point framebuffer
- Tone mapping (ACES or Reinhard)
- Enables bloom and proper exposure

---

## Implementation Priority Order

```
WEEK 1-2: Phase A (all items) — Visual quality defaults
WEEK 3-4: Phase B1-B3 + C1 — Depth buffer, edges, caching
WEEK 5-6: Phase C2-C5 — Performance & smooth interaction
WEEK 7-8: Phase B4-B5 — SSAO + transparency
WEEK 9+:  Phase D — Advanced rendering
```

## Acceptance Criteria (Inventor Parity)

1. ✅ Clean, anti-aliased edges with no jaggies at default settings
2. ✅ Professional dark/neutral background with subtle gradient
3. ✅ Three-point studio lighting eliminating harsh single-light shadows
4. ✅ Smooth rotation with inertial momentum
5. ✅ Animated camera transitions between standard views
6. ✅ Subtle ambient occlusion for depth perception
7. ✅ Selection highlighting that's visible but not garish
8. ✅ Responsive UI during all operations (no "Not responding")
9. ✅ 60fps rendering with 100K+ triangle models
10. ✅ Smooth transparency without sorting artifacts
