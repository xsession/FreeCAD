"""
Performance test for STEP import - runs in FreeCADCmd (no GUI).
Measures pure import + tessellation time.
"""
import sys
import time
import FreeCAD

step_file = r"C:\GIT\FreeCAD\tests\models\cn-06-13-00_asm.stp"

print("=" * 60)
print("STEP Import Performance Test (Console Mode)")
print(f"File: {step_file}")
print("=" * 60)

import os
size_mb = os.path.getsize(step_file) / (1024 * 1024)
print(f"File size: {size_mb:.1f} MB")
print()

# Create a new document
doc = FreeCAD.newDocument("StepTest")

# Time the import (includes OCC parse + transfer + batch tessellation)
print("Starting import...")
t0 = time.perf_counter()
import Import
Import.insert(step_file, doc.Name)
t1 = time.perf_counter()
import_time = t1 - t0

# Gather stats
objs = doc.Objects
num_objects = len(objs)

total_faces = 0
total_parts = 0
for obj in objs:
    if hasattr(obj, "Shape") and obj.Shape:
        try:
            fc = obj.Shape.countElement("Face")
            total_faces += fc
            total_parts += 1
        except Exception:
            pass

print()
print("=" * 60)
print("RESULTS:")
print(f"  Total import time:  {import_time:.2f} s")
print(f"  Objects created:    {num_objects}")
print(f"  Part features:      {total_parts}")
print(f"  Total BRep faces:   {total_faces}")
print(f"  Throughput:         {size_mb / import_time:.2f} MB/s")
print("=" * 60)

# Exit
sys.exit(0)
