# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""End-to-end test runner — runs all E2E test suites inside FreeCAD.

This script is executed headlessly via FreeCADCmd.exe.  It imports and
runs every E2E test suite, writing results to both stdout and a log file.

Usage (from the FreeCAD repo root):
    run_e2e_tests.bat
"""

import sys
import os
import time
import traceback

# Redirect output to log file AND console
# __file__ may not be defined when running via exec(open(...).read())
try:
    _this_dir = os.path.dirname(__file__)
except NameError:
    _this_dir = os.path.dirname(os.path.abspath(sys.argv[0])) if sys.argv else os.getcwd()
LOG_PATH = os.path.join(_this_dir, "..", "..", "e2e_test_results.txt")
# Normalise so the path is clean
LOG_PATH = os.path.normpath(LOG_PATH)
# Fallback: if parent dirs don't exist, write next to flow_studio
if not os.path.isdir(os.path.dirname(LOG_PATH)):
    LOG_PATH = os.path.join(os.getcwd(), "e2e_test_results.txt")

class TeeWriter:
    """Write to both a file and the original stream."""
    def __init__(self, file_obj, stream):
        self.file_obj = file_obj
        self.stream = stream
    def write(self, text):
        self.file_obj.write(text)
        self.stream.write(text)
    def flush(self):
        self.file_obj.flush()
        self.stream.flush()

_original_stdout = sys.stdout
_original_stderr = sys.stderr
_log_file = open(LOG_PATH, "w", encoding="utf-8")
sys.stdout = TeeWriter(_log_file, _original_stdout)
sys.stderr = TeeWriter(_log_file, _original_stderr)


def main():
    t0 = time.time()

    print("=" * 70)
    print("FlowStudio End-to-End Test Runner")
    print(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Log : {os.path.abspath(LOG_PATH)}")
    print("=" * 70)

    import FreeCAD
    print(f"FreeCAD version: {FreeCAD.Version()}")
    print(f"GUI up: {FreeCAD.GuiUp}")
    print()

    all_passed = True
    total_pass = 0
    total_fail = 0
    total_skip = 0
    suites_run = 0

    # ---- Suite 1: STEP Import / Lid Generation / Leak Detection ----
    print("\n" + "#" * 70)
    print("# Suite 1: STEP Import / Lid Generation / Leak Detection")
    print("#" * 70)
    try:
        from flow_studio.tests.test_e2e_step_import import E2EStepImportTests
        suite1 = E2EStepImportTests()
        ok = suite1.run_all()
        if not ok:
            all_passed = False
        for r in suite1.results:
            if r[0] == "PASS": total_pass += 1
            elif r[0] == "FAIL": total_fail += 1
            elif r[0] == "SKIP": total_skip += 1
        suites_run += 1
    except Exception as e:
        print(f"\nSUITE 1 FATAL ERROR: {e}")
        traceback.print_exc()
        all_passed = False

    # ---- Suite 2: Full CFD Workflow ----
    print("\n" + "#" * 70)
    print("# Suite 2: Full CFD Simulation Workflow")
    print("#" * 70)
    try:
        from flow_studio.tests.test_e2e_cfd_workflow import E2ECFDWorkflowTests
        suite2 = E2ECFDWorkflowTests()
        ok = suite2.run_all()
        if not ok:
            all_passed = False
        for r in suite2.results:
            if r[0] == "PASS": total_pass += 1
            elif r[0] == "FAIL": total_fail += 1
            elif r[0] == "SKIP": total_skip += 1
        suites_run += 1
    except Exception as e:
        print(f"\nSUITE 2 FATAL ERROR: {e}")
        traceback.print_exc()
        all_passed = False

    # ---- Suite 3: Real Solver Simulation / Parallelism / Auto-Download ----
    print("\n" + "#" * 70)
    print("# Suite 3: Real Solver Simulation / Parallelism / Auto-Download")
    print("#" * 70)
    try:
        from flow_studio.tests.test_e2e_real_solver import E2ERealSolverTests
        suite3 = E2ERealSolverTests()
        p3, f3, s3 = suite3.run_all()
        total_pass += p3
        total_fail += f3
        total_skip += s3
        if f3 > 0:
            all_passed = False
        suites_run += 1
    except Exception as e:
        print(f"\nSUITE 3 FATAL ERROR: {e}")
        traceback.print_exc()
        all_passed = False

    # ---- Grand Summary ----
    elapsed = time.time() - t0
    total = total_pass + total_fail + total_skip

    print("\n" + "=" * 70)
    print("GRAND SUMMARY")
    print("=" * 70)
    print(f"Suites run : {suites_run}")
    print(f"Total tests: {total}")
    print(f"  Passed   : {total_pass}")
    print(f"  Failed   : {total_fail}")
    print(f"  Skipped  : {total_skip}")
    print(f"Elapsed    : {elapsed:.1f}s")
    print(f"Result     : {'ALL PASSED' if all_passed else 'SOME FAILURES'}")
    print("=" * 70)

    return all_passed


if __name__ == "__main__" or "__name__" not in dir():
    # When run via exec(open(...).read()), __name__ is typically "__main__"
    # but we also handle the case where it's not defined
    try:
        success = main()
    except Exception as e:
        print(f"RUNNER FATAL: {e}")
        traceback.print_exc()
        success = False
    finally:
        _log_file.flush()
        _log_file.close()
        sys.stdout = _original_stdout
        sys.stderr = _original_stderr

    if not success:
        sys.exit(1)
