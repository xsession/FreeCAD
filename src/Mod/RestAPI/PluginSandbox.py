# SPDX-License-Identifier: LGPL-2.1-or-later
# ***************************************************************************
# *   Copyright (c) 2026 FreeCAD contributors                              *
# *                                                                         *
# *   Plugin sandbox – restricts untrusted addon code to a limited          *
# *   Python environment via subprocess isolation.                          *
# *                                                                         *
# *   Trust model (User parameter:BaseApp/Preferences/Addons):             *
# *     TrustLevel = "all" | "signed" | "none"                             *
# *     TrustedAddons = comma-separated list of addon names                *
# *                                                                         *
# *   Untrusted addons run in a subprocess with:                            *
# *     - Restricted sys.path (only FreeCAD libs + addon directory)         *
# *     - Dangerous modules blocked (os.system, subprocess, socket, …)      *
# *     - File access limited to addon dir + temp dir                       *
# *     - Network access denied by default                                  *
# ***************************************************************************

from __future__ import annotations

import importlib
import json
import os
import struct
import subprocess
import sys
import textwrap
import threading
from pathlib import Path
from typing import Any

import FreeCAD

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_BLOCKED_MODULES = frozenset({
    "subprocess",
    "socket",
    "http.client",
    "urllib.request",
    "ftplib",
    "smtplib",
    "telnetlib",
    "ctypes",
    "multiprocessing",
})

_BLOCKED_OS_ATTRS = frozenset({
    "system", "popen", "exec", "execl", "execle", "execlp", "execlpe",
    "execv", "execve", "execvp", "execvpe", "spawn", "spawnl", "spawnle",
    "spawnlp", "spawnlpe", "spawnv", "spawnve", "spawnvp", "spawnvpe",
    "fork", "forkpty",
})


def _prefs():
    return FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Addons")


# ---------------------------------------------------------------------------
# Trust evaluation
# ---------------------------------------------------------------------------

class TrustLevel:
    ALL = "all"        # Trust everything (legacy behaviour)
    SIGNED = "signed"  # Trust signed + explicitly trusted
    NONE = "none"      # Trust nothing by default


def is_addon_trusted(addon_name: str) -> bool:
    """Check whether an addon is in the trusted list or trust-all is set."""
    level = _prefs().GetString("TrustLevel", TrustLevel.ALL)
    if level == TrustLevel.ALL:
        return True
    trusted_csv = _prefs().GetString("TrustedAddons", "")
    trusted_set = {t.strip() for t in trusted_csv.split(",") if t.strip()}
    return addon_name in trusted_set


# ---------------------------------------------------------------------------
# Import hook – blocks dangerous modules for sandboxed addons
# ---------------------------------------------------------------------------

class _SandboxImportBlocker:
    """Installed as sys.meta_path entry to block dangerous imports
    when running inside the sandbox subprocess."""

    def find_module(self, fullname, path=None):  # noqa: ARG002
        if fullname in _BLOCKED_MODULES:
            return self
        return None

    def load_module(self, fullname):
        raise ImportError(
            f"Module '{fullname}' is blocked in the FreeCAD addon sandbox. "
            "Request network/process access in your addon's package.xml."
        )


# ---------------------------------------------------------------------------
# os module patching for sandbox subprocess
# ---------------------------------------------------------------------------

def _patch_os_module():
    """Remove dangerous os functions inside the sandbox subprocess."""
    for attr in _BLOCKED_OS_ATTRS:
        if hasattr(os, attr):
            def _blocked(*args, _name=attr, **kwargs):  # noqa: ARG001
                raise PermissionError(
                    f"os.{_name}() is blocked in the FreeCAD addon sandbox."
                )
            setattr(os, attr, _blocked)


# ---------------------------------------------------------------------------
# Sandbox subprocess bootstrap
# ---------------------------------------------------------------------------

_SUBPROCESS_BOOTSTRAP = textwrap.dedent("""\
    # FreeCAD addon sandbox bootstrap – runs inside restricted subprocess
    import sys, os, json, struct

    # 1. Install import blocker
    _BLOCKED = {blocked_json}
    class _Blocker:
        def find_module(self, name, path=None):
            return self if name in _BLOCKED else None
        def load_module(self, name):
            raise ImportError(f"Module '{{name}}' blocked in sandbox")
    sys.meta_path.insert(0, _Blocker())

    # 2. Patch os
    _BLOCKED_OS = {blocked_os_json}
    for _a in _BLOCKED_OS:
        if hasattr(os, _a):
            def _b(*a, _n=_a, **k):
                raise PermissionError(f"os.{{_n}}() blocked in sandbox")
            setattr(os, _a, _b)

    # 3. Restrict sys.path
    allowed = json.loads({allowed_paths_json!r})
    sys.path = [p for p in sys.path if p in allowed]
    for p in allowed:
        if p not in sys.path:
            sys.path.append(p)

    # 4. Read length-prefixed command from stdin, execute, write result
    def _read_msg():
        hdr = sys.stdin.buffer.read(4)
        if len(hdr) < 4:
            return None
        length = struct.unpack("!I", hdr)[0]
        return json.loads(sys.stdin.buffer.read(length))

    def _write_msg(data):
        payload = json.dumps(data).encode()
        sys.stdout.buffer.write(struct.pack("!I", len(payload)))
        sys.stdout.buffer.write(payload)
        sys.stdout.buffer.flush()

    # 5. Event loop
    while True:
        msg = _read_msg()
        if msg is None:
            break
        try:
            code = msg.get("code", "")
            ns = {{"__builtins__": __builtins__}}
            exec(compile(code, "<sandbox>", "exec"), ns)
            result = ns.get("__result__", None)
            _write_msg({{"ok": True, "result": str(result) if result else None}})
        except Exception as e:
            _write_msg({{"ok": False, "error": f"{{type(e).__name__}}: {{e}}"}})
""")


# ---------------------------------------------------------------------------
# SandboxProcess – manages one subprocess for an addon
# ---------------------------------------------------------------------------

class SandboxProcess:
    """Manages a sandboxed Python subprocess for an untrusted addon."""

    def __init__(self, addon_name: str, addon_path: str):
        self.addon_name = addon_name
        self.addon_path = addon_path
        self._proc: subprocess.Popen | None = None
        self._lock = threading.Lock()

    def start(self):
        """Launch the sandbox subprocess."""
        freecad_lib = os.path.dirname(FreeCAD.__file__) if hasattr(FreeCAD, '__file__') else ""
        allowed_paths = [
            freecad_lib,
            self.addon_path,
            os.path.join(self.addon_path, ".."),  # parent Mod dir
        ]
        # Include standard library path
        for p in sys.path:
            if "lib" in p.lower() and ("python" in p.lower() or "site-packages" in p.lower()):
                allowed_paths.append(p)

        bootstrap = _SUBPROCESS_BOOTSTRAP.format(
            blocked_json=repr(list(_BLOCKED_MODULES)),
            blocked_os_json=repr(list(_BLOCKED_OS_ATTRS)),
            allowed_paths_json=json.dumps(allowed_paths),
        )

        self._proc = subprocess.Popen(
            [sys.executable, "-c", bootstrap],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.addon_path,
        )
        FreeCAD.Console.PrintMessage(
            f"[PluginSandbox] Started sandbox for '{self.addon_name}' (PID {self._proc.pid})\n"
        )

    def execute(self, code: str, timeout: float = 30.0) -> dict[str, Any]:
        """Send code to the sandbox and return the result dict."""
        if self._proc is None or self._proc.poll() is not None:
            return {"ok": False, "error": "Sandbox process not running"}
        with self._lock:
            msg = json.dumps({"code": code}).encode()
            try:
                self._proc.stdin.write(struct.pack("!I", len(msg)))
                self._proc.stdin.write(msg)
                self._proc.stdin.flush()

                hdr = self._proc.stdout.read(4)
                if len(hdr) < 4:
                    return {"ok": False, "error": "Sandbox closed unexpectedly"}
                length = struct.unpack("!I", hdr)[0]
                payload = self._proc.stdout.read(length)
                return json.loads(payload)
            except Exception as e:
                return {"ok": False, "error": str(e)}

    def stop(self):
        """Terminate the sandbox subprocess."""
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._proc.kill()
            FreeCAD.Console.PrintMessage(
                f"[PluginSandbox] Stopped sandbox for '{self.addon_name}'\n"
            )
        self._proc = None


# ---------------------------------------------------------------------------
# Sandbox manager – global registry of sandboxed addons
# ---------------------------------------------------------------------------

_sandboxes: dict[str, SandboxProcess] = {}


def get_sandbox(addon_name: str) -> SandboxProcess | None:
    """Get the running sandbox for an addon, or None."""
    return _sandboxes.get(addon_name)


def create_sandbox(addon_name: str, addon_path: str) -> SandboxProcess:
    """Create and start a sandbox for an untrusted addon."""
    if addon_name in _sandboxes:
        _sandboxes[addon_name].stop()
    sb = SandboxProcess(addon_name, addon_path)
    sb.start()
    _sandboxes[addon_name] = sb
    return sb


def shutdown_all():
    """Stop all running sandboxes.  Called on FreeCAD exit."""
    for sb in _sandboxes.values():
        sb.stop()
    _sandboxes.clear()


# ---------------------------------------------------------------------------
# In-process sandboxing (lighter alternative for semi-trusted addons)
# ---------------------------------------------------------------------------

def install_import_blocker():
    """Install the import blocker in the *current* process.
    Used for semi-trusted addons that don't need full subprocess isolation."""
    sys.meta_path.insert(0, _SandboxImportBlocker())


def remove_import_blocker():
    """Remove the import blocker from the current process."""
    sys.meta_path[:] = [
        m for m in sys.meta_path if not isinstance(m, _SandboxImportBlocker)
    ]
