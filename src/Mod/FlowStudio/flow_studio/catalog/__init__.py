"""Grouped engineering catalog and editor entry points for FlowStudio."""

from flow_studio.catalog.database import *  # noqa: F401,F403
from flow_studio.catalog.optics import *  # noqa: F401,F403

try:  # pragma: no cover - GUI editor is optional in headless tests
	from flow_studio.catalog.editor import *  # noqa: F401,F403
except ModuleNotFoundError as exc:  # pragma: no cover - import-safe package boundary
	if exc.name not in {"FreeCAD", "PySide"}:
		raise
