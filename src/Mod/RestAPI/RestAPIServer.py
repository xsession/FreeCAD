# SPDX-License-Identifier: LGPL-2.1-or-later
# ***************************************************************************
# *   Copyright (c) 2026 FreeCAD contributors                              *
# *                                                                         *
# *   Lightweight REST API server for FreeCAD.                              *
# *   Uses stdlib http.server – no external dependencies required.          *
# *                                                                         *
# *   Preferences (User parameter:BaseApp/Preferences/RestAPI):            *
# *     Enabled   bool   false   – master switch                           *
# *     Port      int    18735   – TCP port to listen on                   *
# *     APIKey    string ""      – if non-empty, every request must send   *
# *                                 X-API-Key header matching this value    *
# ***************************************************************************

from __future__ import annotations

import json
import re
import secrets
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import FreeCAD

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_server: HTTPServer | None = None
_thread: threading.Thread | None = None


def _prefs():
    return FreeCAD.ParamGet("User parameter:BaseApp/Preferences/RestAPI")


def _doc_dict(doc) -> dict:
    return {
        "name": doc.Name,
        "label": doc.Label,
        "fileName": doc.FileName or None,
        "objectCount": len(doc.Objects),
    }


def _obj_props(obj) -> dict:
    """Return a JSON-safe dictionary of an object's properties."""
    result: dict[str, Any] = {
        "name": obj.Name,
        "label": obj.Label,
        "typeid": obj.TypeId,
    }
    for prop_name in obj.PropertiesList:
        try:
            val = getattr(obj, prop_name)
            # Only include JSON-serialisable scalars / simple types
            if isinstance(val, (bool, int, float, str)):
                result[prop_name] = val
            elif isinstance(val, (list, tuple)):
                result[prop_name] = [
                    v if isinstance(v, (bool, int, float, str)) else str(v)
                    for v in val
                ]
            else:
                result[prop_name] = str(val)
        except Exception:
            pass
    return result


# ---------------------------------------------------------------------------
# Route dispatch
# ---------------------------------------------------------------------------

# URL patterns  →  (method, handler)
_ROUTES: list[tuple[str, str, str]] = [
    # (method, regex, handler_name)
    ("GET",  r"^/api/v1/documents$",                         "_handle_list_documents"),
    ("GET",  r"^/api/v1/documents/(?P<doc>[^/]+)/objects$",  "_handle_list_objects"),
    ("GET",  r"^/api/v1/documents/(?P<doc>[^/]+)/objects/(?P<obj>[^/]+)$",
             "_handle_get_object"),
    ("PUT",  r"^/api/v1/documents/(?P<doc>[^/]+)/objects/(?P<obj>[^/]+)$",
             "_handle_set_object"),
    ("POST", r"^/api/v1/documents/(?P<doc>[^/]+)/recompute$",
             "_handle_recompute"),
    ("GET",  r"^/api/v1/documents/(?P<doc>[^/]+)/export$",   "_handle_export"),
    ("POST", r"^/api/v1/commands/(?P<name>[^/]+)$",          "_handle_command"),
    ("GET",  r"^/api/v1/health$",                            "_handle_health"),
]


# ---------------------------------------------------------------------------
# Request handler
# ---------------------------------------------------------------------------

class _Handler(BaseHTTPRequestHandler):
    """Thin HTTP handler that validates API key then routes to handlers."""

    # Suppress default stderr logging
    def log_message(self, fmt, *args):  # noqa: ARG002
        pass

    # ── Auth ──────────────────────────────────────────────────────────

    def _check_auth(self) -> bool:
        api_key = _prefs().GetString("APIKey", "")
        if not api_key:
            return True  # No key configured → allow (localhost only)
        request_key = self.headers.get("X-API-Key", "")
        if not secrets.compare_digest(request_key, api_key):
            self._json_error(HTTPStatus.UNAUTHORIZED, "Invalid or missing X-API-Key")
            return False
        return True

    # ── Routing ───────────────────────────────────────────────────────

    def _dispatch(self, method: str):
        if not self._check_auth():
            return
        path = self.path.split("?")[0]  # Strip query string
        for route_method, pattern, handler_name in _ROUTES:
            if route_method != method:
                continue
            m = re.match(pattern, path)
            if m:
                handler = getattr(self, handler_name)
                handler(m)
                return
        self._json_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")

    def do_GET(self):
        self._dispatch("GET")

    def do_PUT(self):
        self._dispatch("PUT")

    def do_POST(self):
        self._dispatch("POST")

    # ── Response helpers ──────────────────────────────────────────────

    def _json_response(self, data: Any, status: HTTPStatus = HTTPStatus.OK):
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json_error(self, status: HTTPStatus, message: str):
        self._json_response({"error": message}, status)

    # ── Handlers ──────────────────────────────────────────────────────

    def _handle_health(self, _match):
        self._json_response({"status": "ok", "version": FreeCAD.Version()})

    def _handle_list_documents(self, _match):
        docs = FreeCAD.listDocuments()
        self._json_response([_doc_dict(d) for d in docs.values()])

    def _handle_list_objects(self, match):
        doc = self._get_doc(match.group("doc"))
        if doc is None:
            return
        self._json_response([
            {"name": o.Name, "label": o.Label, "typeid": o.TypeId}
            for o in doc.Objects
        ])

    def _handle_get_object(self, match):
        obj = self._get_object(match.group("doc"), match.group("obj"))
        if obj is None:
            return
        self._json_response(_obj_props(obj))

    def _handle_set_object(self, match):
        obj = self._get_object(match.group("doc"), match.group("obj"))
        if obj is None:
            return
        body = self._read_json_body()
        if body is None:
            return
        try:
            for prop_name, value in body.items():
                if prop_name in ("name", "label", "typeid"):
                    continue
                if hasattr(obj, prop_name):
                    setattr(obj, prop_name, value)
            self._json_response({"ok": True})
        except Exception as e:
            self._json_error(HTTPStatus.BAD_REQUEST, str(e))

    def _handle_recompute(self, match):
        doc = self._get_doc(match.group("doc"))
        if doc is None:
            return
        doc.recompute()
        self._json_response({"ok": True})

    def _handle_export(self, match):
        doc = self._get_doc(match.group("doc"))
        if doc is None:
            return
        qs = self.path.split("?", 1)[1] if "?" in self.path else ""
        params = dict(p.split("=", 1) for p in qs.split("&") if "=" in p)
        fmt = params.get("format", "step").lower()

        import tempfile, os
        suffix = {"step": ".step", "iges": ".igs", "stl": ".stl", "brep": ".brep"}
        ext = suffix.get(fmt, ".step")
        tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
        tmp_path = tmp.name
        tmp.close()
        try:
            import Part as PartMod  # noqa: N811
            shapes = [o.Shape for o in doc.Objects if hasattr(o, "Shape")]
            if not shapes:
                self._json_error(HTTPStatus.BAD_REQUEST, "No shapes in document")
                return
            compound = PartMod.makeCompound(shapes)
            compound.exportStep(tmp_path) if fmt == "step" else compound.exportBrep(tmp_path)

            with open(tmp_path, "rb") as f:
                data = f.read()
            self.send_response(HTTPStatus.OK.value)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Disposition", f'attachment; filename="export{ext}"')
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self._json_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(e))
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def _handle_command(self, match):
        cmd_name = match.group("name")
        try:
            import FreeCADGui
            FreeCADGui.runCommand(cmd_name)
            self._json_response({"ok": True})
        except Exception as e:
            self._json_error(HTTPStatus.BAD_REQUEST, str(e))

    # ── Helpers ──────────────────────────────────────────────────────

    def _get_doc(self, name):
        docs = FreeCAD.listDocuments()
        doc = docs.get(name)
        if doc is None:
            self._json_error(HTTPStatus.NOT_FOUND, f"Document '{name}' not found")
        return doc

    def _get_object(self, doc_name, obj_name):
        doc = self._get_doc(doc_name)
        if doc is None:
            return None
        obj = doc.getObject(obj_name)
        if obj is None:
            self._json_error(HTTPStatus.NOT_FOUND,
                             f"Object '{obj_name}' not found in '{doc_name}'")
        return obj

    def _read_json_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            self._json_error(HTTPStatus.BAD_REQUEST, "Empty body")
            return None
        try:
            return json.loads(self.rfile.read(length))
        except json.JSONDecodeError as e:
            self._json_error(HTTPStatus.BAD_REQUEST, f"Invalid JSON: {e}")
            return None


# ---------------------------------------------------------------------------
# Server lifecycle
# ---------------------------------------------------------------------------

def start():
    """Start the REST API server on localhost in a daemon thread."""
    global _server, _thread
    if _server is not None:
        return  # Already running

    port = _prefs().GetInt("Port", 18735)

    # Bind to localhost only (security: never expose to network by default)
    _server = HTTPServer(("127.0.0.1", port), _Handler)
    _thread = threading.Thread(target=_server.serve_forever, daemon=True,
                               name="FreeCAD-REST-API")
    _thread.start()
    FreeCAD.Console.PrintMessage(f"[RestAPI] Listening on http://127.0.0.1:{port}\n")


def stop():
    """Shutdown the server gracefully."""
    global _server, _thread
    if _server is None:
        return
    _server.shutdown()
    _server = None
    _thread = None
    FreeCAD.Console.PrintMessage("[RestAPI] Server stopped\n")
