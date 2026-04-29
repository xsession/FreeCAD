"""Helpers for building explicit ribbon toolbar metadata names."""

try:
    import FreeCADGui
except ImportError:  # pragma: no cover - exercised through injected adapters in tests
    FreeCADGui = None


class FreeCADRibbonRegistryAdapter:
    def __init__(self, gui_module=None):
        self._gui = gui_module if gui_module is not None else FreeCADGui

    def register_contextual_ribbon_panel(self, name, commands):
        self._require_gui().registerContextualRibbonPanel(name, list(commands))

    def unregister_contextual_ribbon_panel(self, name):
        self._require_gui().unregisterContextualRibbonPanel(name)

    def register_ribbon_panel(self, name, commands):
        self._require_gui().registerRibbonPanel(name, list(commands))

    def unregister_ribbon_panel(self, name):
        self._require_gui().unregisterRibbonPanel(name)

    def _require_gui(self):
        if self._gui is None:
            raise RuntimeError("FreeCADGui is required for ribbon registry operations")
        return self._gui


def get_ribbon_registry(gui_module=None):
    return FreeCADRibbonRegistryAdapter(gui_module)


def build_ribbon_toolbar_name(tab_name, panel_name, *flags, order=None, home_priority=None):
    parts = ["Ribbon", tab_name, panel_name]
    parts.extend(flags)
    if home_priority:
        priority = str(home_priority).strip().lower()
        if priority == "primary":
            parts.append("HomePrimary")
        elif priority == "secondary":
            parts.append("HomeSecondary")
        else:
            raise ValueError(f"Unsupported home_priority: {home_priority}")
    if order is not None:
        parts.append(f"Order={order}")
    return "::".join(parts)


def build_contextual_ribbon_toolbar_name(
    tab_name,
    panel_name,
    *type_keywords,
    workbench=None,
    order=None,
    color=None,
):
    parts = ["RibbonContext", tab_name, panel_name]
    if workbench:
        parts.append(f"Workbench={workbench}")
    if type_keywords:
        parts.append(f"Types={','.join(type_keywords)}")
    if color:
        parts.append(f"Color={color}")
    if order is not None:
        parts.append(f"Order={order}")
    return "::".join(parts)


def register_contextual_ribbon_panel(name, commands, registry=None):
    (registry or get_ribbon_registry()).register_contextual_ribbon_panel(name, commands)


def unregister_contextual_ribbon_panel(name, registry=None):
    (registry or get_ribbon_registry()).unregister_contextual_ribbon_panel(name)


def register_ribbon_panel(name, commands, registry=None):
    (registry or get_ribbon_registry()).register_ribbon_panel(name, commands)


def unregister_ribbon_panel(name, registry=None):
    (registry or get_ribbon_registry()).unregister_ribbon_panel(name)