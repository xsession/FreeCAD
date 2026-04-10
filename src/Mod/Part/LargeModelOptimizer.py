# SPDX-License-Identifier: LGPL-2.1-or-later
# Large Model Display Optimizer for FreeCAD
#
# Optimizes rendering performance of large imported STEP/IGES models.
# Reduces tessellation quality on complex objects to maintain interactive frame rates.
#
# Usage (from FreeCAD Python console or as macro):
#   from Part import LargeModelOptimizer
#   LargeModelOptimizer.optimize()           # Auto-optimize all objects
#   LargeModelOptimizer.diagnose()           # Report model complexity
#   LargeModelOptimizer.set_profile("fast")  # Apply preset profile
#
# Or run directly:
#   exec(open("path/to/LargeModelOptimizer.py").read())

import FreeCAD
import FreeCADGui


def _get_part_prefs():
    return FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Part")


def _get_view_prefs():
    return FreeCAD.ParamGet("User parameter:BaseApp/Preferences/View")


def _count_faces(obj):
    """Count the number of topological faces in an object's shape."""
    try:
        if hasattr(obj, "Shape") and not obj.Shape.isNull():
            return len(obj.Shape.Faces)
    except Exception:
        pass
    return 0


def _count_triangles(obj):
    """Estimate triangle count from the tessellation of an object's shape."""
    try:
        if hasattr(obj, "Shape") and not obj.Shape.isNull():
            total = 0
            for face in obj.Shape.Faces:
                mesh = face.tessellate(0.1)  # coarse estimate
                total += len(mesh[1])
            return total
    except Exception:
        pass
    return 0


def _get_shape_objects():
    """Get all document objects that have a Shape and a ViewObject with Deviation."""
    doc = FreeCAD.ActiveDocument
    if not doc:
        return []

    results = []
    for obj in doc.Objects:
        if hasattr(obj, "Shape") and hasattr(obj, "ViewObject"):
            vo = obj.ViewObject
            if hasattr(vo, "Deviation"):
                results.append(obj)
    return results


def diagnose():
    """Print a diagnostic report of model complexity for all shape objects."""
    objects = _get_shape_objects()
    if not objects:
        FreeCAD.Console.PrintMessage("No shape objects found in document.\n")
        return

    FreeCAD.Console.PrintMessage("\n" + "=" * 72 + "\n")
    FreeCAD.Console.PrintMessage("  LARGE MODEL DIAGNOSTIC REPORT\n")
    FreeCAD.Console.PrintMessage("=" * 72 + "\n\n")

    total_faces = 0
    total_tris = 0
    report = []

    for obj in objects:
        faces = _count_faces(obj)
        vo = obj.ViewObject
        deviation = vo.Deviation if hasattr(vo, "Deviation") else -1
        ang_defl = vo.AngularDeflection if hasattr(vo, "AngularDeflection") else -1

        # Quick triangle estimate from existing tessellation
        tri_count = 0
        try:
            if hasattr(obj, "Shape") and not obj.Shape.isNull():
                for face in obj.Shape.Faces:
                    tri = face.tessellate(
                        max(0.01, deviation * 0.01 * _bbox_diag(obj.Shape))
                    )
                    tri_count += len(tri[1])
        except Exception:
            tri_count = -1

        total_faces += faces
        if tri_count > 0:
            total_tris += tri_count
        report.append((obj.Label, faces, tri_count, deviation, ang_defl))

    # Sort by face count descending
    report.sort(key=lambda x: x[1], reverse=True)

    FreeCAD.Console.PrintMessage(
        f"{'Object':<40} {'Faces':>8} {'~Tris':>10} {'Dev%':>6} {'AngDefl':>8}\n"
    )
    FreeCAD.Console.PrintMessage("-" * 72 + "\n")
    for label, faces, tris, dev, ang in report:
        tris_str = f"{tris:>10,}" if tris >= 0 else "     N/A"
        FreeCAD.Console.PrintMessage(
            f"{label[:40]:<40} {faces:>8,} {tris_str} {dev:>6.2f} {ang:>8.1f}\n"
        )

    FreeCAD.Console.PrintMessage("-" * 72 + "\n")
    FreeCAD.Console.PrintMessage(
        f"{'TOTAL':<40} {total_faces:>8,} {total_tris:>10,}\n"
    )
    FreeCAD.Console.PrintMessage("\n")

    # Recommendations
    if total_faces > 10000:
        FreeCAD.Console.PrintWarning(
            f"Model has {total_faces:,} faces - consider using 'fast' or 'balanced' profile.\n"
        )
    if total_tris > 1000000:
        FreeCAD.Console.PrintWarning(
            f"Estimated {total_tris:,} triangles - this will cause rendering lag.\n"
            "Run: LargeModelOptimizer.optimize() or "
            "LargeModelOptimizer.set_profile('fast')\n"
        )

    # Current preference status
    prefs = _get_part_prefs()
    adaptive = prefs.GetBool("AdaptiveDeviation", True)
    threshold = prefs.GetInt("AdaptiveDeviationFaceThreshold", 2000)
    FreeCAD.Console.PrintMessage(
        f"\nPreferences: AdaptiveDeviation={'ON' if adaptive else 'OFF'}, "
        f"FaceThreshold={threshold}\n"
    )

    view_prefs = _get_view_prefs()
    cache = view_prefs.GetInt("RenderCache", 0)
    cache_names = {0: "Auto", 1: "Distributed", 2: "Off"}
    FreeCAD.Console.PrintMessage(
        f"RenderCache={cache_names.get(cache, cache)}\n"
    )
    FreeCAD.Console.PrintMessage("=" * 72 + "\n\n")


def _bbox_diag(shape):
    """Get approximate bounding box diagonal length."""
    try:
        bb = shape.BoundBox
        return (
            (bb.XMax - bb.XMin) + (bb.YMax - bb.YMin) + (bb.ZMax - bb.ZMin)
        ) / 300.0
    except Exception:
        return 1.0


def optimize(deviation=None, angular_deflection=None, face_threshold=2000):
    """Auto-optimize all shape objects based on their complexity.

    Objects with more faces get higher deviation (coarser tessellation).
    Objects with fewer faces keep original quality.

    Args:
        deviation: Override deviation for all objects (None = auto-calculate).
        angular_deflection: Override angular deflection (None = auto).
        face_threshold: Objects with more faces than this get optimized.
    """
    objects = _get_shape_objects()
    if not objects:
        FreeCAD.Console.PrintMessage("No shape objects to optimize.\n")
        return

    optimized = 0
    for obj in objects:
        faces = _count_faces(obj)
        vo = obj.ViewObject

        if deviation is not None:
            vo.Deviation = deviation
            optimized += 1
        elif faces > face_threshold:
            # Auto-scale: sqrt(faces/threshold) scaling
            import math
            scale = math.sqrt(faces / face_threshold)
            new_dev = min(vo.Deviation * scale, 50.0)
            new_dev = max(new_dev, vo.Deviation)  # never decrease
            vo.Deviation = new_dev
            optimized += 1

        if angular_deflection is not None:
            vo.AngularDeflection = angular_deflection
        elif faces > face_threshold * 5:
            # Very complex: relax angular deflection
            vo.AngularDeflection = max(vo.AngularDeflection, 33.0)

    FreeCAD.Console.PrintMessage(
        f"Optimized {optimized}/{len(objects)} objects.\n"
    )

    # Enable adaptive deviation for future tessellations
    prefs = _get_part_prefs()
    prefs.SetBool("AdaptiveDeviation", True)
    prefs.SetInt("AdaptiveDeviationFaceThreshold", face_threshold)


def set_profile(profile="balanced"):
    """Apply a rendering performance profile.

    Profiles:
        'fast':      Maximum performance, lower visual quality.
                     Best for 100MB+ STEP models.
        'balanced':  Good balance of quality and performance.
                     Good for 20-100MB STEP models.
        'quality':   Maximum visual quality (FreeCAD defaults).
                     For small models only.

    Args:
        profile: One of 'fast', 'balanced', 'quality'.
    """
    profiles = {
        "fast": {
            "deviation": 5.0,
            "angular_deflection": 33.0,
            "adaptive": True,
            "face_threshold": 500,
            "max_scale": 15.0,
            "render_cache": 1,  # Distributed
            "mesh_deviation_default": 1.0,
        },
        "balanced": {
            "deviation": 1.5,
            "angular_deflection": 28.5,
            "adaptive": True,
            "face_threshold": 2000,
            "max_scale": 10.0,
            "render_cache": 1,  # Distributed
            "mesh_deviation_default": 0.5,
        },
        "quality": {
            "deviation": 0.5,
            "angular_deflection": 28.5,
            "adaptive": False,
            "face_threshold": 2000,
            "max_scale": 10.0,
            "render_cache": 0,  # Auto
            "mesh_deviation_default": 0.2,
        },
    }

    if profile not in profiles:
        FreeCAD.Console.PrintError(
            f"Unknown profile '{profile}'. Use: fast, balanced, quality\n"
        )
        return

    p = profiles[profile]

    # Set per-object properties
    objects = _get_shape_objects()
    for obj in objects:
        vo = obj.ViewObject
        vo.Deviation = p["deviation"]
        vo.AngularDeflection = p["angular_deflection"]

    # Set global preferences
    part_prefs = _get_part_prefs()
    part_prefs.SetBool("AdaptiveDeviation", p["adaptive"])
    part_prefs.SetInt("AdaptiveDeviationFaceThreshold", p["face_threshold"])
    part_prefs.SetFloat("AdaptiveDeviationMaxScale", p["max_scale"])
    part_prefs.SetFloat("MeshDeviation", p["mesh_deviation_default"])

    # Render cache
    view_prefs = _get_view_prefs()
    view_prefs.SetInt("RenderCache", p["render_cache"])

    FreeCAD.Console.PrintMessage(
        f"Applied '{profile}' profile to {len(objects)} objects.\n"
        f"  Deviation: {p['deviation']}%, AngularDeflection: {p['angular_deflection']}deg\n"
        f"  AdaptiveDeviation: {'ON' if p['adaptive'] else 'OFF'}, "
        f"FaceThreshold: {p['face_threshold']}\n"
        f"  RenderCache: {'Distributed' if p['render_cache'] == 1 else 'Auto'}\n"
    )

    if profile in ("fast", "balanced"):
        FreeCAD.Console.PrintMessage(
            "\nTip: Switch display mode to 'Shaded' (no edges) for extra performance.\n"
            "     Edges are expensive to render on complex models.\n"
        )


def set_display_mode(mode="Shaded"):
    """Set display mode for all visible shape objects.

    'Shaded' mode is significantly faster than 'Flat Lines' because
    it skips edge rendering (which can double the rendering cost).

    Args:
        mode: 'Shaded', 'Flat Lines', 'Wireframe', or 'Points'
    """
    objects = _get_shape_objects()
    changed = 0
    for obj in objects:
        vo = obj.ViewObject
        if vo.Visibility and vo.DisplayMode != mode:
            vo.DisplayMode = mode
            changed += 1

    FreeCAD.Console.PrintMessage(
        f"Set {changed} objects to '{mode}' display mode.\n"
    )


def enable_adaptive_deviation(enable=True, face_threshold=2000, max_scale=10.0):
    """Enable or disable adaptive tessellation for future renders.

    When enabled, shapes with more than face_threshold faces will be
    automatically tessellated at reduced quality to maintain performance.

    Args:
        enable: True to enable, False to disable.
        face_threshold: Number of faces above which adaptation kicks in.
        max_scale: Maximum deviation multiplier (caps quality reduction).
    """
    prefs = _get_part_prefs()
    prefs.SetBool("AdaptiveDeviation", enable)
    prefs.SetInt("AdaptiveDeviationFaceThreshold", face_threshold)
    prefs.SetFloat("AdaptiveDeviationMaxScale", max_scale)
    FreeCAD.Console.PrintMessage(
        f"AdaptiveDeviation={'ON' if enable else 'OFF'}, "
        f"threshold={face_threshold}, maxScale={max_scale}\n"
    )


def optimize_render_settings():
    """Apply optimal rendering preferences for large models.

    - RenderCache: Distributed (forces GL display list caching)
    - Reduces unnecessary redraws
    """
    view_prefs = _get_view_prefs()

    # Enable distributed render cache (forces GL caching per object)
    view_prefs.SetInt("RenderCache", 1)

    FreeCAD.Console.PrintMessage(
        "Render settings optimized:\n"
        "  RenderCache = Distributed (1)\n"
        "\nRestart FreeCAD or reopen the 3D view for cache changes to take effect.\n"
    )


# Auto-run when executed as macro
if __name__ == "__main__" or FreeCAD.ActiveDocument:
    try:
        if FreeCAD.ActiveDocument and len(FreeCAD.ActiveDocument.Objects) > 0:
            diagnose()
            FreeCAD.Console.PrintMessage(
                "\nAvailable commands:\n"
                "  LargeModelOptimizer.diagnose()            - Show model complexity report\n"
                "  LargeModelOptimizer.optimize()            - Auto-optimize all objects\n"
                "  LargeModelOptimizer.set_profile('fast')   - Apply fast rendering profile\n"
                "  LargeModelOptimizer.set_profile('balanced') - Balanced quality/performance\n"
                "  LargeModelOptimizer.set_display_mode('Shaded') - Skip edge rendering\n"
                "  LargeModelOptimizer.enable_adaptive_deviation() - Enable C++ adaptive mode\n"
                "  LargeModelOptimizer.optimize_render_settings()  - Optimize GL settings\n"
            )
    except Exception:
        pass
