# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Application service for the FlowStudio project cockpit use case."""

from __future__ import annotations

from flow_studio.core.workflow import get_active_analysis, get_workflow_context, get_workflow_status
from flow_studio.runtime.monitor import get_run_snapshot, sync_post_pipeline, terminate_run


class FlowStudioProjectCockpitService:
    """Backend-facing service used by cockpit presenters and other frontends."""

    def get_active_analysis(self):
        return get_active_analysis()

    def get_workflow_context(self):
        return get_workflow_context()

    def get_workflow_status(self):
        return tuple(get_workflow_status())

    def get_run_snapshot(self, analysis=None):
        return get_run_snapshot(analysis)

    def sync_post_pipeline(self, analysis, *, snapshot=None):
        return sync_post_pipeline(analysis, snapshot=snapshot)

    def terminate_run(self, analysis=None):
        return terminate_run(analysis)