"""
Performance test for STEP import optimizations.
Run this from FreeCAD's Python console:
    exec(open(r"C:\GIT\FreeCAD\tests\test_step_import_perf.py").read())
"""
import time
import FreeCAD
import Import

step_file = r"C:\GIT\FreeCAD\tests\models\cn-06-13-00_asm.stp"

print("=" * 60)
print(f"STEP Import Performance Test")
print(f"File: {step_file}")
print("=" * 60)

# Create a new document
doc = FreeCAD.newDocument("StepTest")

# Time the import
t0 = time.perf_counter()
Import.insert(step_file, doc.Name)
t1 = time.perf_counter()

import_time = t1 - t0

# Gather stats
objs = doc.Objects
num_objects = len(objs)

total_faces = 0
for obj in objs:
    if hasattr(obj, "Shape") and obj.Shape:
        try:
            total_faces += obj.Shape.countElement("Face")
        except Exception:
            pass

print("=" * 60)
print(f"RESULTS:")
print(f"  Import time:    {import_time:.2f} s")
print(f"  Objects:        {num_objects}")
print(f"  Total faces:    {total_faces}")
print("=" * 60)
print("Check the Report View (View > Panels > Report view) for:")
print("  - [STEP Import] File size: XX MB — enabling optimizations")
print("  - Import: Batch tessellating N shapes in parallel...")
print("  - Import: Batch tessellation complete: X.XXs")
print("  - Part: Adaptive tessellation for N faces")
print()
print("Try rotating the model - edges/points are hidden during")
print("navigation for smoother interaction.")
