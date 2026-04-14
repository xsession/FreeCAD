"""
Launch FreeCAD with an explicit CPU affinity mask and process priority.

Cross-platform replacement for launch_freecad_pcores.ps1.

Usage:
    python launch_freecad_pcores.py --exe "C:/Program Files/FreeCAD 1.0/bin/FreeCAD.exe" --affinity-mask-hex 00FF
    python launch_freecad_pcores.py --exe /usr/bin/freecad --affinity-mask-hex FF --priority normal
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


_PRIORITY_MAP_WIN = {
    "normal": 0x00000020,  # NORMAL_PRIORITY_CLASS
    "abovenormal": 0x00008000,  # ABOVE_NORMAL_PRIORITY_CLASS
    "high": 0x00000080,  # HIGH_PRIORITY_CLASS
}

_PRIORITY_MAP_NICE = {
    "normal": 0,
    "abovenormal": -5,
    "high": -10,
}


def _set_affinity_and_priority_psutil(pid: int, affinity_mask: int, priority: str) -> None:
    proc = psutil.Process(pid)
    cpus = [i for i in range(os.cpu_count() or 1) if affinity_mask & (1 << i)]
    if not cpus:
        raise ValueError(f"Affinity mask 0x{affinity_mask:X} selects no CPUs")
    proc.cpu_affinity(cpus)
    if sys.platform == "win32":
        proc.nice(_PRIORITY_MAP_WIN.get(priority, 0x00000020))
    else:
        proc.nice(_PRIORITY_MAP_NICE.get(priority, 0))
    print(f"Applied affinity {cpus} and priority '{priority}' to PID {pid} (psutil)")


def _set_affinity_and_priority_native(pid: int, affinity_mask: int, priority: str) -> None:
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        PROCESS_SET_INFORMATION = 0x0200
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = kernel32.OpenProcess(
            PROCESS_SET_INFORMATION | PROCESS_QUERY_LIMITED_INFORMATION, False, pid
        )
        if not handle:
            raise OSError(f"OpenProcess failed for PID {pid} (error {ctypes.get_last_error()})")
        try:
            if not kernel32.SetProcessAffinityMask(handle, affinity_mask):
                raise OSError(
                    f"SetProcessAffinityMask failed (error {ctypes.get_last_error()})"
                )
            prio_class = _PRIORITY_MAP_WIN.get(priority, 0x00000020)
            if not kernel32.SetPriorityClass(handle, prio_class):
                raise OSError(
                    f"SetPriorityClass failed (error {ctypes.get_last_error()})"
                )
        finally:
            kernel32.CloseHandle(handle)
        print(f"Applied affinity 0x{affinity_mask:X} and priority '{priority}' to PID {pid} (win32)")
    else:
        # Linux / macOS: use taskset-style sched_setaffinity + nice
        cpus = [i for i in range(os.cpu_count() or 1) if affinity_mask & (1 << i)]
        if not cpus:
            raise ValueError(f"Affinity mask 0x{affinity_mask:X} selects no CPUs")
        os.sched_setaffinity(pid, set(cpus))
        nice_val = _PRIORITY_MAP_NICE.get(priority, 0)
        if nice_val != 0:
            os.setpriority(os.PRIO_PROCESS, pid, nice_val)
        print(f"Applied affinity {cpus} and priority '{priority}' to PID {pid} (native)")


def set_affinity_and_priority(pid: int, affinity_mask: int, priority: str) -> None:
    if HAS_PSUTIL:
        _set_affinity_and_priority_psutil(pid, affinity_mask, priority)
    else:
        _set_affinity_and_priority_native(pid, affinity_mask, priority)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Launch FreeCAD with CPU affinity mask and priority class"
    )
    parser.add_argument("--exe", required=True, help="Path to FreeCAD executable")
    parser.add_argument(
        "--affinity-mask-hex",
        required=True,
        help="Hex CPU affinity mask (e.g. 00FF for first 8 cores)",
    )
    parser.add_argument(
        "--priority",
        choices=("normal", "abovenormal", "high"),
        default="high",
        help="Process priority class (default: high)",
    )
    parser.add_argument(
        "extra_args",
        nargs="*",
        help="Additional arguments passed to FreeCAD",
    )
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    exe = Path(args.exe).resolve()
    if not exe.exists():
        print(f"Executable not found: {exe}", file=sys.stderr)
        return 1

    if not re.fullmatch(r"[0-9a-fA-F]+", args.affinity_mask_hex):
        print(f"Invalid hex affinity mask: {args.affinity_mask_hex}", file=sys.stderr)
        return 1

    affinity_mask = int(args.affinity_mask_hex, 16)
    if affinity_mask == 0:
        print("Affinity mask must be non-zero", file=sys.stderr)
        return 1

    priority = args.priority.lower()
    working_dir = str(exe.parent)

    print(f"Launching {exe}")
    print(f"Affinity mask: 0x{args.affinity_mask_hex.upper()}")
    print(f"Priority class: {priority}")

    proc = subprocess.Popen(
        [str(exe)] + args.extra_args,
        cwd=working_dir,
    )

    time.sleep(0.25)

    if proc.poll() is not None:
        print(
            f"Process exited before affinity could be applied (exit code: {proc.returncode})",
            file=sys.stderr,
        )
        return 1

    try:
        set_affinity_and_priority(proc.pid, affinity_mask, priority)
    except Exception as exc:
        print(f"Failed to apply affinity: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
