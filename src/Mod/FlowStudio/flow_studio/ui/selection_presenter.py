# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Presenter helpers for shared FlowStudio selection references."""

from __future__ import annotations


class SelectionPresenter:
    """Frontend-neutral presenter for formatting shared selection references."""

    def build_labels(self, refs):
        labels = []
        for ref_obj, sub_names in refs or []:
            base = getattr(ref_obj, "Label", getattr(ref_obj, "Name", "Object"))
            if isinstance(sub_names, str):
                sub_names = [sub_names]
            if sub_names:
                labels.extend(f"{base}:{sub}" for sub in sub_names)
            else:
                labels.append(base)
        return labels