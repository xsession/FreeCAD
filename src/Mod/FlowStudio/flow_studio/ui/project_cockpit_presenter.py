# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Presenter and view-state models for the FlowStudio project cockpit.

This module is intentionally UI-toolkit neutral so the same cockpit state can
be rendered by the current Qt task panel or by a future web-based frontend.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from flow_studio.app import FlowStudioProjectCockpitService


class ProjectCockpitActionPort(Protocol):
    """Application/frontend port for cockpit user intents."""

    def execute_command(self, command_name: str) -> None:
        ...

    def activate_result_target(self, object_name: str) -> bool:
        ...


class NullProjectCockpitActions:
    """Default no-op action port used by pure state-only presenter tests."""

    def execute_command(self, command_name: str) -> None:
        return None

    def activate_result_target(self, object_name: str) -> bool:
        return False


@dataclass(frozen=True)
class CockpitBannerState:
    level: str
    title: str
    detail: str


@dataclass(frozen=True)
class CockpitRecipeState:
    visible: bool
    label: str = ""
    summary: str = ""
    reference_url: str = ""
    milestones: tuple[str, ...] = ()
    key_parameters: tuple[str, ...] = ()


@dataclass(frozen=True)
class CockpitStepState:
    state_label: str
    title: str
    gate: str
    hint: str
    level: str


@dataclass(frozen=True)
class CockpitActionState:
    command_name: str
    label: str
    enabled: bool
    level: str


@dataclass(frozen=True)
class CockpitRuntimeState:
    level: str
    title: str
    phase: str
    progress_percent: int
    progress_indeterminate: bool
    details: tuple[str, ...]
    log_tail: tuple[str, ...]
    stop_enabled: bool
    results_enabled: bool
    results_label: str


@dataclass(frozen=True)
class ProjectCockpitViewState:
    profile_label: str
    analysis_label: str
    progress_percent: int
    completed_steps: int
    total_steps: int
    banner: CockpitBannerState
    summary_text: str
    recipe: CockpitRecipeState
    steps: tuple[CockpitStepState, ...]
    actions: tuple[CockpitActionState, ...]
    runtime: CockpitRuntimeState


class ProjectCockpitPresenter:
    """Build cockpit view state independently from any concrete UI toolkit."""

    def __init__(
        self,
        command_labels,
        *,
        service=None,
        actions: ProjectCockpitActionPort | None = None,
    ):
        self._command_labels = tuple(command_labels)
        self._service = service or FlowStudioProjectCockpitService()
        self._actions = actions or NullProjectCockpitActions()

    def build_view_state(self):
        context = self._service.get_workflow_context()
        steps = tuple(self._service.get_workflow_status())
        analysis = context["analysis"]
        profile = context["profile"]

        completed = sum(1 for step in steps if step.complete)
        total = max(1, len(steps))
        progress_percent = int((completed / float(total)) * 100.0)
        banner = self._build_banner_state(profile.label, steps, completed, total)
        summary_text = self._build_summary_text(analysis, completed, total)

        return ProjectCockpitViewState(
            profile_label=profile.label,
            analysis_label=getattr(analysis, "Label", getattr(analysis, "Name", "No Analysis")),
            progress_percent=progress_percent,
            completed_steps=completed,
            total_steps=total,
            banner=banner,
            summary_text=summary_text,
            recipe=self._build_recipe_state(context.get("study_recipe")),
            steps=self._build_step_states(steps),
            actions=self._build_action_states(steps),
            runtime=self._build_runtime_state(analysis),
        )

    def stop_run(self):
        return self._service.terminate_run(self._service.get_active_analysis())

    def handle_command(self, command_name):
        if not command_name:
            return False
        if command_name == "FlowStudio_PostPipeline":
            return self.handle_open_results()
        self._actions.execute_command(command_name)
        return True

    def handle_open_results(self):
        target = self.resolve_results_target()
        if target is None:
            self._actions.execute_command("FlowStudio_PostPipeline")
            return True
        if not self._actions.activate_result_target(target.Name):
            self._actions.execute_command("FlowStudio_PostPipeline")
        return True

    def resolve_results_target(self, analysis=None):
        analysis = analysis or self._service.get_active_analysis()
        return self._preferred_result_object(analysis)

    def _build_banner_state(self, profile_label, steps, completed, total):
        next_step = next((step for step in steps if not step.complete and step.active), None)
        if completed == total:
            return CockpitBannerState(
                level="done",
                title="Project ready for result review",
                detail="All workflow phases are complete. Review results or refine the setup.",
            )
        if next_step is not None:
            return CockpitBannerState(
                level="active",
                title=f"Next forced step: {next_step.number}. {next_step.name}",
                detail=next_step.hint or next_step.description,
            )
        return CockpitBannerState(
            level="warning",
            title="Workflow is blocked",
            detail="Resolve the blocked prerequisites shown below to continue.",
        )

    def _build_summary_text(self, analysis, completed, total):
        return (
            f"Completed {completed}/{total} steps for "
            f"{getattr(analysis, 'Label', getattr(analysis, 'Name', 'No Analysis'))}. "
            "Color coding is enforced: green = done, blue = ready now, grey = blocked."
        )

    def _build_recipe_state(self, recipe):
        if recipe is None:
            return CockpitRecipeState(visible=False)
        return CockpitRecipeState(
            visible=True,
            label=recipe.label,
            summary=recipe.summary,
            reference_url=recipe.reference_url,
            milestones=tuple(recipe.milestones),
            key_parameters=tuple(recipe.key_parameters),
        )

    def _build_step_states(self, steps):
        rows = []
        for step in steps:
            if step.complete:
                state_label = "Done"
                level = "done"
                gate = "Unlocked"
            elif step.active:
                state_label = "Ready"
                level = "active"
                gate = "Do this now"
            else:
                state_label = "Blocked"
                level = "blocked"
                gate = "Waiting for previous step"
            rows.append(
                CockpitStepState(
                    state_label=state_label,
                    title=f"{step.number}. {step.name}",
                    gate=gate,
                    hint=step.hint or "",
                    level=level,
                )
            )
        return tuple(rows)

    def _build_action_states(self, steps):
        step_by_command = {step.command_name: step for step in steps if step.command_name}
        actions = []
        for command_name, label in self._command_labels:
            step = step_by_command.get(command_name)
            enabled = True
            level = "active"
            if step is not None:
                enabled = bool(step.active or step.complete)
                if step.complete:
                    level = "done"
                elif step.active:
                    level = "active"
                else:
                    level = "blocked"
            actions.append(
                CockpitActionState(
                    command_name=command_name,
                    label=label,
                    enabled=enabled,
                    level=level,
                )
            )
        return tuple(actions)

    def _build_runtime_state(self, analysis):
        snapshot = self._service.get_run_snapshot(analysis)
        if snapshot["result_path"]:
            try:
                self._service.sync_post_pipeline(analysis, snapshot=snapshot)
            except Exception:
                pass

        status = snapshot["status"]
        if status == "RUNNING":
            level = "running"
            title = "Simulation is running"
        elif status == "FINISHED":
            level = "done"
            title = "Simulation finished"
        elif status in {"FAILED", "TERMINATING"}:
            level = "failed" if status == "FAILED" else "warning"
            title = "Simulation needs attention"
        else:
            level = "blocked"
            title = "No active simulation"

        elapsed = snapshot["elapsed_seconds"]
        details = [
            f"Backend: {snapshot['backend'] or 'n/a'}",
            f"PID: {snapshot['pid'] or 'n/a'}",
            f"Elapsed: {elapsed:.1f}s",
        ]
        if snapshot["case_dir"]:
            details.append(f"Case: {snapshot['case_dir']}")
        if snapshot["result_path"]:
            result_name = str(snapshot["result_path"]).replace("\\", "/").rstrip("/").split("/")[-1]
            details.append(f"Results: {result_name}")
        if snapshot["last_error"]:
            details.append(f"Last issue: {snapshot['last_error']}")

        preferred_result = self._preferred_result_object(analysis)
        results_label = "Open Primary Plot" if getattr(preferred_result, "FlowType", "") == "FlowStudio::ResultPlot" else "Open Results"

        return CockpitRuntimeState(
            level=level,
            title=title,
            phase=snapshot["phase"],
            progress_percent=int(snapshot["progress_percent"] or 0),
            progress_indeterminate=snapshot["progress_percent"] is None and status == "RUNNING",
            details=tuple(details),
            log_tail=tuple(snapshot["log_tail"] or ()),
            stop_enabled=status == "RUNNING",
            results_enabled=preferred_result is not None or bool(snapshot["result_path"]),
            results_label=results_label,
        )

    def _preferred_result_object(self, analysis):
        if analysis is None:
            return None

        result_plot = None
        post_pipeline = None
        for child in getattr(analysis, "Group", []):
            flow_type = getattr(child, "FlowType", "")
            if flow_type == "FlowStudio::ResultPlot" and result_plot is None:
                result_plot = child
            elif flow_type == "FlowStudio::PostPipeline" and post_pipeline is None:
                post_pipeline = child

        return result_plot or post_pipeline
