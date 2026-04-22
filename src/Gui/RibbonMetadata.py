"""Helpers for building explicit ribbon toolbar metadata names."""

import FreeCADGui


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


def register_contextual_ribbon_panel(name, commands):
    FreeCADGui.registerContextualRibbonPanel(name, list(commands))


def unregister_contextual_ribbon_panel(name):
    FreeCADGui.unregisterContextualRibbonPanel(name)