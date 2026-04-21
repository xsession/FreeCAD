"""Engineering database editor UI entry points for FlowStudio."""

try:
	from flow_studio.engineering_database_editor import (  # noqa: F401
		EngineeringDatabaseDialog,
		show_engineering_database_editor,
	)
except ModuleNotFoundError as exc:
	if exc.name not in {"FreeCAD", "PySide"}:
		raise

	EngineeringDatabaseDialog = None  # type: ignore[assignment]

	def show_engineering_database_editor():
		raise RuntimeError(
			"FlowStudio engineering database editor requires the FreeCAD GUI runtime."
		)


__all__ = ["EngineeringDatabaseDialog", "show_engineering_database_editor"]
