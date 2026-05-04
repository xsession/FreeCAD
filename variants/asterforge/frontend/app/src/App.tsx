import { FormEvent, useEffect, useState } from "react";
import {
  activateWorkbench,
  fetchBootstrap,
  fetchCommandCatalog,
  fetchDiagnostics,
  fetchEvents,
  fetchFeatureHistory,
  fetchJobs,
  fetchObjectTree,
  fetchPreselectionState,
  fetchShellSnapshot,
  fetchProperties,
  fetchSelectionState,
  fetchTaskPanel,
  fetchViewport,
  openDocument,
  runCommand,
  setPreselection,
  setSelection,
  setSelectionMode,
  updateShellPanelState,
  type ActivityEvent,
  type BootPayload,
  type CommandArgumentDefinition,
  type CommandCatalogResponse,
  type CommandDefinition,
  type CommandExecutionResponse,
  type DiagnosticsResponse,
  type DocumentRef,
  type ExtensionCompatibilityState,
  type FeatureHistoryResponse,
  type JobStatusResponse,
  type ObjectNode,
  type PreselectionStateResponse,
  type PropertyResponse,
  type RecentDocumentEntry,
  type SelectionStateResponse,
  type ShellSnapshot,
  type TaskPanelResponse,
  type ViewportDiffResponse,
  type ViewportDrawable,
  type ViewportResponse,
  type WorkspaceSessionEntry
} from "./protocol";
import { ShellIcon } from "./shellIcons";
import {
  filteredReportEvents,
  prioritizeReportEvents,
  summarizeReportEvents,
  shouldHideCommandNoticeForActivity,
  shouldHideStructuredInspectionCommandNotice,
  type StepViewportPreset,
  viewportOrientationLabel
} from "./shellViewUtils";
import { StepViewportScene } from "./StepViewportScene";
import { fetchStepDocumentIndex, fetchStepSceneBundle } from "./stepClient";
import type { StepDocumentIndex, StepSceneBundle } from "./stepTypes";

export { StepViewportScene } from "./StepViewportScene";

type ShellNotice = {
  id: string;
  level: "info" | "warning" | "error";
  title: string;
  detail: string;
  objectId?: string | null;
  commandAction?: ActivityCommandAction | null;
};

type ActivityCommandAction = {
  commandId: string;
  label: string;
};

function shellNoticePriority(notice: ShellNotice) {
  let priority = 0;

  if (notice.level === "error") {
    priority += 8;
  } else if (notice.level === "warning") {
    priority += 6;
  }
  if (notice.commandAction) {
    priority += 3;
  }
  if (notice.objectId) {
    priority += 2;
  }
  if (notice.title === "document opened") {
    priority -= 1;
  }
  if (notice.title === "document changed") {
    priority -= 3;
  }
  if (notice.title === "job update" || notice.title === "job updates") {
    priority -= 2;
  }

  return priority;
}

export function buildShellNotices(
  commandNotices: ShellNotice[],
  eventNotices: ShellNotice[],
  maxNotices = 4
): ShellNotice[] {
  return [...commandNotices, ...eventNotices]
    .map((notice, index) => ({ notice, index, priority: shellNoticePriority(notice) }))
    .sort((left, right) => right.priority - left.priority || left.index - right.index)
    .slice(0, maxNotices)
    .map(({ notice }) => notice);
}

type WorkspaceSession = {
  session_id: string;
  document_id: string;
  display_name: string;
  file_path: string;
  workbench: string;
  dirty: boolean;
  selected_object_id: string | null;
};

type BottomDockTab = "report" | "python" | "jobs" | "diagnostics" | "history" | "commands" | "extensions";

type ShellInspectionState = NonNullable<ShellSnapshot["inspection"]>;
type StepPmiInspection = NonNullable<ShellInspectionState["step_pmi"]>;
type StepMeasurementInspection = NonNullable<ShellInspectionState["step_measurement"]>;
type CommandTargetOption = {
  objectId: string;
  label: string;
  detail: string;
};

const STEP_VIEWPORT_COMMAND_BY_PRESET: Record<StepViewportPreset, string> = {
  iso: "step.view_iso",
  front: "step.view_front",
  back: "step.view_back",
  right: "step.view_right",
  left: "step.view_left",
  top: "step.view_top",
  bottom: "step.view_bottom"
};

function stepViewportPresetFromCommand(commandId: string): StepViewportPreset | null {
  switch (commandId) {
    case "step.view_iso":
      return "iso";
    case "step.view_front":
      return "front";
    case "step.view_back":
      return "back";
    case "step.view_right":
      return "right";
    case "step.view_left":
      return "left";
    case "step.view_top":
      return "top";
    case "step.view_bottom":
      return "bottom";
    default:
      return null;
  }
}

function isStepViewportResetCommand(commandId: string) {
  return commandId === "step.view_reset" || commandId === "step.view_fit_all";
}

function ExtensionCompatibilityPanel({
  commandCatalog,
  extensionCompatibility,
  onRunCommand,
}: {
  commandCatalog: CommandCatalogResponse | null;
  extensionCompatibility: ExtensionCompatibilityState | undefined;
  onRunCommand: (commandId: string, commandArguments?: Record<string, string>) => void;
}) {
  if (!extensionCompatibility) {
    return (
      <section className="dock-panel python-console-placeholder">
        <div className="panel-header">
          <h2>Extension Compatibility</h2>
          <span>Waiting for backend state</span>
        </div>
        <div className="python-console-shell">
          <div className="python-console-note">
            Extension compatibility data has not been published by the backend yet.
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="dock-panel python-console-placeholder">
      <div className="panel-header">
        <h2>{extensionCompatibility.title}</h2>
        <span>{extensionCompatibility.lanes.length} migration lanes</span>
      </div>
      <div className="python-console-shell">
        <div className="python-console-note">{extensionCompatibility.summary}</div>
        <div className="property-groups combo-pane-scroll">
          {extensionCompatibility.lanes.map((lane: ExtensionCompatibilityState["lanes"][number]) => (
            <div className="property-group" key={lane.lane_id}>
              {(() => {
                const inventoryEntries = lane.inventory_entries ?? [];
                return (
                  <>
              <h3>{lane.label}</h3>
              <div className="property-row">
                <div>
                  <div className="property-name">Status</div>
                  <div className="property-type">Owner: {lane.owner}</div>
                </div>
                <div className="property-value">
                  <span>{lane.status}</span>
                </div>
              </div>
              {lane.command_ids.length > 0 ? (
                <div className="selection-actions">
                  {lane.command_ids
                    .map((commandId) =>
                      commandCatalog?.commands.find((command) => command.command_id === commandId) ?? null
                    )
                    .filter((command): command is CommandDefinition => command !== null)
                    .map((command) => (
                      <button
                        className="suggested-command-button"
                        disabled={!command.enabled}
                        key={`${lane.lane_id}:${command.command_id}`}
                        onClick={() => onRunCommand(command.command_id)}
                        type="button"
                      >
                        {command.action_label ?? command.label}
                      </button>
                    ))}
                </div>
              ) : null}
              {inventoryEntries.length > 0 ? (
                <div className="property-groups combo-pane-scroll">
                  {inventoryEntries.map((entry) => (
                    <div className="property-group" key={entry.entry_id}>
                      <h3>{entry.label}</h3>
                      <div className="property-row">
                        <div>
                          <div className="property-name">Origin</div>
                          <div className="property-type">Trust: {entry.trust_state}</div>
                        </div>
                        <div className="property-value">
                          <span>{entry.compatibility}</span>
                        </div>
                      </div>
                      <div className="python-console-note">{entry.origin}</div>
                      <div className="python-console-log">
                        <div>{entry.detail}</div>
                      </div>
                      {entry.last_run_status ? (
                        <div className="python-console-note">
                          Last run
                          {entry.last_run_kind || entry.last_run_level
                            ? ` (${[entry.last_run_kind, entry.last_run_level].filter(Boolean).join(", ")})`
                            : ""}
                          : {entry.last_run_status}
                        </div>
                      ) : null}
                      {entry.last_run_detail ? (
                        <div className="python-console-log">
                          <div>{entry.last_run_detail}</div>
                        </div>
                      ) : null}
                      {entry.action_command_id ? (
                        <div className="selection-actions">
                          <button
                            className="suggested-command-button"
                            onClick={() =>
                              onRunCommand(entry.action_command_id!, { entry_id: entry.entry_id })
                            }
                            type="button"
                          >
                            {entry.action_label ?? "Run Entry"}
                          </button>
                        </div>
                      ) : null}
                    </div>
                  ))}
                </div>
              ) : null}
              <div className="python-console-note">{lane.summary}</div>
              <div className="python-console-log">
                {lane.next_steps.map((step: string) => (
                  <div key={step}>{step}</div>
                ))}
              </div>
                  </>
                );
              })()}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function TreeNode({
  node,
  depth = 0,
  preselectedObjectId,
  selectedObjectId,
  selectionMode,
  onHoverChange,
  onSelect
}: {
  node: ObjectNode;
  depth?: number;
  preselectedObjectId: string | null;
  selectedObjectId: string | null;
  selectionMode: string;
  onHoverChange: (objectId: string | null) => void;
  onSelect: (objectId: string) => void;
}) {
  const selected = selectedObjectId === node.object_id;
  const preselected = preselectedObjectId === node.object_id;
  const selectable = objectMatchesSelectionMode(node.object_type, selectionMode);

  return (
    <div className="tree-node" style={{ ["--depth" as string]: depth }}>
      <button
        className={`tree-row ${selected ? "tree-row-selected" : ""} ${preselected ? "tree-row-preselected" : ""} ${selectable ? "" : "tree-row-muted"}`}
        disabled={!selectable}
        onMouseEnter={() => {
          if (selectable) {
            onHoverChange(node.object_id);
          }
        }}
        onMouseLeave={() => onHoverChange(null)}
        onClick={() => onSelect(node.object_id)}
        type="button"
      >
        <span className={`visibility visibility-${node.visibility}`} />
        <div>
          <div className="tree-label">{node.label}</div>
          <div className="tree-type">{node.object_type}</div>
        </div>
        <span className={`selection-availability ${selectable ? "selection-availability-live" : ""}`}>
          {selectable ? "live" : "filtered"}
        </span>
      </button>
      {node.children.length > 0 ? (
        <div className="tree-children">
          {node.children.map((child) => (
            <TreeNode
              key={child.object_id}
              node={child}
              depth={depth + 1}
              onHoverChange={onHoverChange}
              onSelect={onSelect}
              preselectedObjectId={preselectedObjectId}
              selectedObjectId={selectedObjectId}
              selectionMode={selectionMode}
            />
          ))}
        </div>
      ) : null}
    </div>
  );
}

function ViewportScene({
  preselectedObjectId,
  viewport,
  selectedObjectId,
  selectionMode,
  objectTypeById,
  onHoverChange,
  onSelect
}: {
  preselectedObjectId: string | null;
  viewport: ViewportResponse | null;
  selectedObjectId: string | null;
  selectionMode: string;
  objectTypeById: Map<string, string>;
  onHoverChange: (objectId: string | null) => void;
  onSelect: (objectId: string) => void;
}) {
  if (!viewport) {
    return <div className="viewport-empty">Waiting for viewport payload...</div>;
  }

  return (
    <svg className="viewport-svg" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet">
      <defs>
        <linearGradient id="asterforge-grid" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="rgba(255,255,255,0.22)" />
          <stop offset="100%" stopColor="rgba(255,255,255,0.02)" />
        </linearGradient>
      </defs>
      <pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
        <path
          d="M 10 0 L 0 0 0 10"
          fill="none"
          stroke="url(#asterforge-grid)"
          strokeWidth="0.25"
        />
      </pattern>
      <rect x="0" y="0" width="100" height="100" fill="url(#grid)" opacity="0.45" />
      {viewport.scene.drawables.map((drawable) => {
        const preselected = drawable.object_id === preselectedObjectId;
        const selected = drawable.object_id === selectedObjectId;
        const objectType = objectTypeById.get(drawable.object_id) ?? "";
        const selectable = objectMatchesSelectionMode(objectType, selectionMode);

        return (
          <DrawableShape
            drawable={drawable}
            onHoverChange={onHoverChange}
            key={drawable.object_id}
            onSelect={onSelect}
            preselected={preselected}
            selectable={selectable}
            selected={selected}
          />
        );
      })}
    </svg>
  );
}

function DrawableShape({
  drawable,
  selected,
  preselected,
  selectable,
  onHoverChange,
  onSelect
}: {
  drawable: ViewportDrawable;
  selected: boolean;
  preselected: boolean;
  selectable: boolean;
  onHoverChange: (objectId: string | null) => void;
  onSelect: (objectId: string) => void;
}) {
  return (
    <g
      className={`viewport-drawable viewport-drawable-${drawable.kind} ${selectable ? "" : "viewport-drawable-muted"} ${preselected ? "viewport-drawable-preselected" : ""}`}
    >
      <rect
        className={`viewport-hitbox ${selected ? "viewport-hitbox-selected" : ""} ${preselected ? "viewport-hitbox-preselected" : ""} ${selectable ? "viewport-hitbox-live" : ""}`}
        x={drawable.bounds.x}
        y={drawable.bounds.y}
        width={drawable.bounds.width}
        height={drawable.bounds.height}
        onMouseEnter={() => {
          if (selectable) {
            onHoverChange(drawable.object_id);
          }
        }}
        onMouseLeave={() => onHoverChange(null)}
        onClick={() => {
          if (selectable) {
            onSelect(drawable.object_id);
          }
        }}
        rx={3}
      />
      {drawable.paths.map((path, index) => (
        <path
          d={path}
          fill="none"
          key={`${drawable.object_id}-${index}`}
          stroke={drawable.accent}
          strokeOpacity={selectable ? 1 : 0.3}
          strokeWidth={selected ? 1.8 : 1.1}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      ))}
      <text
        x={drawable.bounds.x}
        y={drawable.bounds.y - 2.5}
        className={`viewport-label ${selectable ? "" : "viewport-label-muted"}`}
      >
        {drawable.label}
      </text>
    </g>
  );
}

function formatStepSpan(value: number) {
  return value.toFixed(2);
}

export function ViewportHeadsUp({
  activePreset,
  cameraEye,
  cameraTarget,
  comboViewVisible,
  onChangeSelectionMode,
  onApplyPreset,
  onFitAll,
  onFocusSelection,
  onOpenModel,
  onOpenReport,
  onOpenTasks,
  onResetPreset,
  reportDockVisible,
  selectionState,
  selectedObjectId,
  stepAvailable
}: {
  activePreset: StepViewportPreset | null;
  cameraEye: number[] | undefined;
  cameraTarget: number[] | undefined;
  comboViewVisible: boolean;
  onChangeSelectionMode: (modeId: string) => void;
  onApplyPreset: (preset: StepViewportPreset) => void;
  onFitAll: () => void;
  onFocusSelection: () => void;
  onOpenModel: () => void;
  onOpenReport: () => void;
  onOpenTasks: () => void;
  onResetPreset: () => void;
  reportDockVisible: boolean;
  selectionState: SelectionStateResponse | null;
  selectedObjectId: string | null;
  stepAvailable: boolean;
}) {
  return (
    <>
      <div className="viewport-orientation-chip">
        <span>{stepAvailable ? "STEP HUD" : "Viewport HUD"}</span>
        <strong>{viewportOrientationLabel(cameraEye, cameraTarget)}</strong>
      </div>
      <div className="viewport-hud-toolbar">
        {stepAvailable ? (
          <div className="viewport-hud-preset-group">
            {([
              ["Iso", "iso"],
              ["Front", "front"],
              ["Back", "back"],
              ["Right", "right"],
              ["Left", "left"],
              ["Top", "top"],
              ["Bottom", "bottom"]
            ] as Array<[string, StepViewportPreset]>).map(([label, preset]) => (
              <button
                className={`viewport-hud-button ${activePreset === preset ? "viewport-hud-button-active" : ""}`}
                key={preset}
                onClick={() => onApplyPreset(preset)}
                type="button"
              >
                <span>{label}</span>
              </button>
            ))}
            <button className="viewport-hud-button" onClick={onFitAll} type="button">
              <span>Fit</span>
            </button>
            <button className="viewport-hud-button" onClick={onResetPreset} type="button">
              <span>Live</span>
            </button>
          </div>
        ) : null}
        <button
          className="viewport-hud-button"
          disabled={!selectedObjectId}
          onClick={onFocusSelection}
          type="button"
        >
          <ShellIcon icon="focus" title="Focus selection" />
          <span>Focus</span>
        </button>
        <button
          className={`viewport-hud-button ${comboViewVisible ? "viewport-hud-button-active" : ""}`}
          onClick={onOpenModel}
          type="button"
        >
          <ShellIcon icon="part" title="Open model stack" />
          <span>Model</span>
        </button>
        <button className="viewport-hud-button" onClick={onOpenTasks} type="button">
          <ShellIcon icon="history" title="Open task panel" />
          <span>Tasks</span>
        </button>
        <button
          className={`viewport-hud-button ${reportDockVisible ? "viewport-hud-button-active" : ""}`}
          onClick={onOpenReport}
          type="button"
        >
          <ShellIcon icon="measure" title="Open report dock" />
          <span>Report</span>
        </button>
      </div>
      {selectionState ? (
        <div className="viewport-selection-hud">
          <div className="viewport-selection-hud-header">
            <span className="selection-label">Selection</span>
            <strong>{selectionState.current_mode}</strong>
          </div>
          <div className="viewport-selection-mode-list">
            {selectionState.available_modes.map((mode) => {
              const active = mode.mode_id === selectionState.current_mode;

              return (
                <button
                  className={`viewport-selection-mode-chip ${active ? "viewport-selection-mode-chip-active" : ""}`}
                  disabled={!mode.enabled}
                  key={mode.mode_id}
                  onClick={() => onChangeSelectionMode(mode.mode_id)}
                  title={mode.description}
                  type="button"
                >
                  <strong>{mode.label}</strong>
                  <span>{mode.object_count}</span>
                </button>
              );
            })}
          </div>
        </div>
      ) : null}
    </>
  );
}

function StepPmiInspectionCard({
  inspection
}: {
  inspection: StepPmiInspection;
}) {
  return (
    <article className="inspection-card">
      <div className="panel-header panel-header-dense">
        <h3>PMI Inspection</h3>
        <span>Entity #{inspection.entity_id}</span>
      </div>
      <div className="selection-kv-list">
        <div className="selection-kv">
          <span>Target</span>
          <strong>{inspection.label}</strong>
        </div>
        <div className="selection-kv">
          <span>Object Id</span>
          <strong>{inspection.object_id}</strong>
        </div>
        <div className="selection-kv">
          <span>Linked geometry</span>
          <strong>{inspection.target_object_ids.length}</strong>
        </div>
        <div className="selection-kv">
          <span>Presentation refs</span>
          <strong>{inspection.presentation_object_ids.length}</strong>
        </div>
      </div>
      {inspection.annotation_lines.length > 0 ? (
        <div className="inspection-annotation-list">
          {inspection.annotation_lines.map((line, index) => (
            <div className="inspection-annotation-item" key={`${inspection.object_id}-${index}`}>
              {line}
            </div>
          ))}
        </div>
      ) : null}
    </article>
  );
}

function StepMeasurementInspectionCard({
  inspection
}: {
  inspection: StepMeasurementInspection;
}) {
  return (
    <article className="inspection-card">
      <div className="panel-header panel-header-dense">
        <h3>Measurement Overlay</h3>
        <span>{inspection.label}</span>
      </div>
      <div className="selection-kv-list">
        <div className="selection-kv">
          <span>Span X</span>
          <strong>{formatStepSpan(inspection.span_x)}</strong>
        </div>
        <div className="selection-kv">
          <span>Span Y</span>
          <strong>{formatStepSpan(inspection.span_y)}</strong>
        </div>
        <div className="selection-kv">
          <span>Span Z</span>
          <strong>{formatStepSpan(inspection.span_z)}</strong>
        </div>
        <div className="selection-kv">
          <span>Representations</span>
          <strong>{inspection.representation_count}</strong>
        </div>
        <div className="selection-kv">
          <span>Annotations</span>
          <strong>{inspection.annotation_count}</strong>
        </div>
        <div className="selection-kv">
          <span>Object Id</span>
          <strong>{inspection.object_id}</strong>
        </div>
      </div>
    </article>
  );
}

function inspectionCommand(
  commandCatalog: CommandCatalogResponse | null,
  commandId: string
) {
  return commandCatalog?.commands.find((command) => command.command_id === commandId) ?? null;
}

export function commandNoticeTitle(
  commandCatalog: CommandCatalogResponse | null,
  commandId: string
) {
  const command = inspectionCommand(commandCatalog, commandId);
  return command?.action_label ?? command?.label ?? commandId;
}

export function commandNoticeAction(
  commandCatalog: CommandCatalogResponse | null,
  commandId: string
): ActivityCommandAction | null {
  const command = inspectionCommand(commandCatalog, commandId);
  if (!command) {
    return null;
  }

  return {
    commandId,
    label: command.action_label ?? command.label
  };
}

export function commandNoticeObjectId(
  commandCatalog: CommandCatalogResponse | null,
  commandId: string,
  selectedObjectId: string | null
) {
  const command = inspectionCommand(commandCatalog, commandId);
  if (!command?.requires_selection || !selectedObjectId) {
    return null;
  }

  return selectedObjectId;
}

function reportActivityCommand(activity: ActivityEvent): ActivityCommandAction | null {
  switch (activity.topic) {
    case "step_pmi_annotation":
    case "step_pmi_inspection":
      return {
        commandId: "step.inspect_pmi",
        label: "Refresh PMI"
      };
    case "step_measurement":
      return {
        commandId: "step.measure_selection",
        label: "Refresh Measure"
      };
    default:
      return null;
  }
}

export function buildEventNotices(
  reportEvents: ActivityEvent[],
  includeActivityNotices = true,
  maxNotices = 3
): ShellNotice[] {
  if (!includeActivityNotices) {
    return [];
  }

  const notices: ShellNotice[] = [];
  for (let index = 0; index < reportEvents.length; index += 1) {
    const event = reportEvents[index];

    if (event.topic === "document_changed") {
      const grouped = [event.message];
      let cursor = index + 1;

      while (cursor < reportEvents.length) {
        const nextEvent = reportEvents[cursor];
        if (nextEvent.topic !== "document_changed") {
          break;
        }
        grouped.push(nextEvent.message);
        cursor += 1;
      }

      notices.push({
        id: `document-changed-${index}`,
        level: event.level,
        title: grouped[0].startsWith("Opened ") ? "document opened" : "document changed",
        detail:
          grouped.length > 1
            ? `${grouped[0]} (${grouped.length - 1} additional document update${grouped.length > 2 ? "s" : ""})`
            : grouped[0]
      });
      index = cursor - 1;
      continue;
    }

    if (event.topic === "job_update") {
      const grouped = [event.message];
      let cursor = index + 1;

      while (cursor < reportEvents.length) {
        const nextEvent = reportEvents[cursor];
        if (nextEvent.topic !== "job_update") {
          break;
        }
        grouped.push(nextEvent.message);
        cursor += 1;
      }

      notices.push({
        id: `job-update-${index}`,
        level: event.level,
        title: grouped.length > 1 ? "job updates" : "job update",
        detail:
          grouped.length > 1
            ? `${grouped[0]} (${grouped.length - 1} additional job update${grouped.length > 2 ? "s" : ""})`
            : grouped[0]
      });
      index = cursor - 1;
      continue;
    }

    if (event.topic === "step_pmi_annotation" && event.object_id) {
      const grouped = [event.message];
      let cursor = index + 1;

      while (cursor < reportEvents.length) {
        const nextEvent = reportEvents[cursor];
        if (nextEvent.topic !== "step_pmi_annotation" || nextEvent.object_id !== event.object_id) {
          break;
        }
        grouped.push(nextEvent.message);
        cursor += 1;
      }

      notices.push({
        id: `step-pmi-annotations-${event.object_id}-${index}`,
        level: event.level,
        title: grouped.length > 1 ? "step pmi annotations" : "step pmi annotation",
        detail:
          grouped.length > 1
            ? `${grouped.length} PMI annotations captured for ${event.object_id}: ${grouped[0]}`
            : grouped[0],
        objectId: event.object_id,
        commandAction: {
          commandId: "step.inspect_pmi",
          label: "Refresh PMI"
        }
      });
      index = cursor - 1;
      continue;
    }

    notices.push({
      id: `${event.topic}-${index}`,
      level: event.level,
      title: event.topic.replaceAll("_", " "),
      detail: event.message,
      objectId: event.object_id,
      commandAction: reportActivityCommand(event)
    });
  }

  return notices
    .map((notice, index) => ({ notice, index, priority: shellNoticePriority(notice) }))
    .sort((left, right) => right.priority - left.priority || left.index - right.index)
    .slice(0, maxNotices)
    .map(({ notice }) => notice);
}

function ActivityObjectActions({
  activity,
  commandActionOverride,
  commandCatalog,
  onFocusActivityObject,
  onRunCommand,
  onSelectActivityObject
}: {
  activity: Pick<ActivityEvent, "object_id" | "topic">;
  commandActionOverride?: ActivityCommandAction | null;
  commandCatalog?: CommandCatalogResponse | null;
  onFocusActivityObject?: (objectId: string) => void;
  onRunCommand?: (commandId: string, targetObjectId?: string) => void;
  onSelectActivityObject?: (objectId: string) => void;
}) {
  const commandAction = commandActionOverride ?? reportActivityCommand(activity as ActivityEvent);

  if (!activity.object_id && !commandAction) {
    return null;
  }
  const command = commandAction ? inspectionCommand(commandCatalog ?? null, commandAction.commandId) : null;

  return (
    <div className="activity-actions">
      {commandAction ? (
        <InspectionActionButton
          command={command}
          label={commandAction.label}
          onClick={() => onRunCommand?.(commandAction.commandId, activity.object_id ?? undefined)}
        />
      ) : null}
      {activity.object_id ? (
        <>
          <button
            className="action-button"
            onClick={() => onSelectActivityObject?.(activity.object_id!)}
            type="button"
          >
            <ShellIcon icon="part" title="Select activity object" />
            <span>Select</span>
          </button>
          <button
            className="action-button"
            onClick={() => onFocusActivityObject?.(activity.object_id!)}
            type="button"
          >
            <ShellIcon icon="focus" title="Focus activity object" />
            <span>Focus</span>
          </button>
        </>
      ) : null}
    </div>
  );
}

function InspectionActionButton({
  command,
  disabled,
  label,
  onClick
}: {
  command: CommandDefinition | null;
  disabled?: boolean;
  label?: string;
  onClick: () => void;
}) {
  if (!command) {
    return null;
  }

  return (
    <button
      className="action-button"
      disabled={disabled ?? !command.enabled}
      onClick={onClick}
      type="button"
    >
      <CommandSummaryContent command={command} label={label} showGroup={false} />
    </button>
  );
}

export function ReportInspectionSummary({
  commandCatalog,
  onRunCommand,
  shellSnapshot
}: {
  commandCatalog: CommandCatalogResponse | null;
  onRunCommand: (commandId: string, targetObjectId?: string) => void;
  shellSnapshot: ShellSnapshot | null;
}) {
  const inspection = shellSnapshot?.inspection;
  const focusCommand = inspectionCommand(commandCatalog, "selection.focus");
  const inspectPmiCommand = inspectionCommand(commandCatalog, "step.inspect_pmi");
  const measureSelectionCommand = inspectionCommand(commandCatalog, "step.measure_selection");

  if (!inspection?.step_pmi && !inspection?.step_measurement) {
    return null;
  }

  return (
    <section className="dock-panel">
      <div className="panel-header">
        <h2>Structured Inspection</h2>
        <span>Shell snapshot driven</span>
      </div>
      <div className="inspection-summary-grid">
        {inspection.step_pmi ? (
          <div className="inspection-card-stack">
            <StepPmiInspectionCard inspection={inspection.step_pmi} />
            <div className="inspection-card-actions">
              <InspectionActionButton
                command={inspectPmiCommand}
                label="Refresh PMI"
                onClick={() => onRunCommand("step.inspect_pmi", inspection.step_pmi?.object_id)}
              />
              <InspectionActionButton
                command={focusCommand}
                onClick={() => onRunCommand("selection.focus", inspection.step_pmi?.object_id)}
              />
            </div>
          </div>
        ) : null}
        {inspection.step_measurement ? (
          <div className="inspection-card-stack">
            <StepMeasurementInspectionCard inspection={inspection.step_measurement} />
            <div className="inspection-card-actions">
              <InspectionActionButton
                command={measureSelectionCommand}
                label="Refresh Measure"
                onClick={() =>
                  onRunCommand("step.measure_selection", inspection.step_measurement?.object_id)
                }
              />
              <InspectionActionButton
                command={focusCommand}
                onClick={() => onRunCommand("selection.focus", inspection.step_measurement?.object_id)}
              />
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}

function CommandSummaryContent({
  command,
  label,
  showGroup = true
}: {
  command: Pick<CommandDefinition, "action_label" | "group" | "icon" | "label">;
  label?: string;
  showGroup?: boolean;
}) {
  return (
    <>
      <ShellIcon icon={command.icon} title={command.label} />
      <div className="command-summary-content">
        <strong>{label ?? command.action_label ?? command.label}</strong>
        {showGroup ? <span>{command.group}</span> : null}
      </div>
    </>
  );
}

function commandInputType(argument: CommandArgumentDefinition) {
  return argument.value_type === "quantity" || argument.value_type === "float"
    ? "number"
    : "text";
}

function resolveSuggestedCommands(
  commandCatalog: CommandCatalogResponse | null,
  suggestedCommandIds: string[] | undefined
) {
  if (!commandCatalog || !suggestedCommandIds) {
    return [];
  }

  return suggestedCommandIds
    .map((commandId) => commandCatalog.commands.find((command) => command.command_id === commandId))
    .filter((command): command is CommandDefinition => Boolean(command));
}

function initializeCommandDrafts(
  currentDrafts: Record<string, Record<string, string>>,
  commands: CommandDefinition[]
) {
  const next: Record<string, Record<string, string>> = {};

  for (const command of commands) {
    if (command.arguments.length === 0) {
      continue;
    }

    next[command.command_id] = {};
    for (const argument of command.arguments) {
      next[command.command_id][argument.argument_id] =
        currentDrafts[command.command_id]?.[argument.argument_id] ?? argument.default_value ?? "";
    }
  }

  return next;
}

function initializeSuggestedCommandDrafts(
  currentDrafts: Record<string, Record<string, string>>,
  commandCatalog: CommandCatalogResponse | null,
  suggestedCommandIds: string[] | undefined
) {
  if (!commandCatalog || !suggestedCommandIds) {
    return {};
  }

  return initializeCommandDrafts(
    currentDrafts,
    resolveSuggestedCommands(commandCatalog, suggestedCommandIds)
  );
}

export function SuggestedCommandEditor({
  className,
  command,
  currentDraftValue,
  headerLabel,
  idPrefix,
  onSubmitCommand,
  onUpdateDraftValue,
  submitLabel
}: {
  className: string;
  command: CommandDefinition;
  currentDraftValue: (argument: CommandArgumentDefinition) => string;
  headerLabel?: string;
  idPrefix: string;
  onSubmitCommand: (commandArguments: Record<string, string>) => void;
  onUpdateDraftValue: (argumentId: string, value: string) => void;
  submitLabel: string;
}) {
  return (
    <form
      className={className}
      onSubmit={(event) => {
        event.preventDefault();
        onSubmitCommand(
          Object.fromEntries(
            command.arguments.map((argument) => [
              argument.argument_id,
              currentDraftValue(argument)
            ])
          )
        );
      }}
    >
      <div className="task-editor-header">
        <CommandSummaryContent command={command} label={headerLabel} />
      </div>
      <p className="task-command-note">{command.description}</p>
      <div className="task-editor-fields">
        {command.arguments.map((argument) => {
          const inputId = `${idPrefix}-${command.command_id}-${argument.argument_id}`;

          return (
            <label className="task-editor-label" htmlFor={inputId} key={inputId}>
              <span>{argument.label}</span>
              <div className="task-editor-row">
                {argument.value_type === "enum" || argument.value_type === "boolean" ? (
                  <select
                    className="task-editor-select"
                    id={inputId}
                    onChange={(event) => onUpdateDraftValue(argument.argument_id, event.target.value)}
                    value={currentDraftValue(argument)}
                  >
                    {argument.options.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    className="task-editor-input"
                    id={inputId}
                    onChange={(event) => onUpdateDraftValue(argument.argument_id, event.target.value)}
                    placeholder={argument.placeholder ?? undefined}
                    required={argument.required}
                    step={commandInputType(argument) === "number" ? "0.1" : undefined}
                    type={commandInputType(argument)}
                    value={currentDraftValue(argument)}
                  />
                )}
                {argument.unit ? <span className="task-editor-unit">{argument.unit}</span> : null}
              </div>
            </label>
          );
        })}
      </div>
      <button className="action-button action-button-primary" disabled={!command.enabled} type="submit">
        {submitLabel}
      </button>
    </form>
  );
}

export function ViewportHoverCard({
  commandCatalog,
  onPromotePreselectionCommand,
  preselectionState
}: {
  commandCatalog: CommandCatalogResponse | null;
  onPromotePreselectionCommand: (commandId: string) => void;
  preselectionState: PreselectionStateResponse | null;
}) {
  if (!preselectionState?.object_id) {
    return null;
  }

  const suggestedCommands = preselectionState.suggested_commands.slice(0, 2).map((commandId) => {
    const command = commandCatalog?.commands.find((entry) => entry.command_id === commandId);
    return command
      ? {
          command,
          commandId,
          disabled: command.enabled,
          label: command.action_label ?? command.label,
        }
      : {
          command: {
            action_label: commandId,
            group: "suggested",
            icon: undefined,
            label: commandId
          },
          commandId,
          disabled: false,
          label: commandId,
        };
  });

  return (
    <div className="viewport-hover-card">
      <div className="viewport-hover-card-header">
        <span className="selection-label">Hover Candidate</span>
        <strong>{preselectionState.object_label ?? preselectionState.object_id}</strong>
      </div>
      <div className="viewport-hover-card-meta">
        <span>{preselectionState.model_state}</span>
        <span>{preselectionState.dependency_note}</span>
      </div>
      {suggestedCommands.length > 0 ? (
        <div className="viewport-hover-card-actions">
          {suggestedCommands.map((command) => (
            <button
              className="preselection-action-chip"
              disabled={!command.disabled}
              key={command.commandId}
              onClick={() => onPromotePreselectionCommand(command.commandId)}
              type="button"
            >
              <CommandSummaryContent command={command.command} label={command.label} showGroup={false} />
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}

export function ReportActivityFeed({
  commandCatalog,
  onFocusActivityObject,
  onRunCommand,
  onSelectActivityObject,
  reportEvents
}: {
  commandCatalog?: CommandCatalogResponse | null;
  onFocusActivityObject?: (objectId: string) => void;
  onRunCommand?: (commandId: string, targetObjectId?: string) => void;
  onSelectActivityObject?: (objectId: string) => void;
  reportEvents: ActivityEvent[];
}) {
  const prioritizedEvents = prioritizeReportEvents(summarizeReportEvents(reportEvents));

  return (
    <section className="dock-panel">
      <div className="panel-header">
        <h2>Backend Activity</h2>
        <span>{reportEvents.length} live backend events</span>
      </div>
      {reportEvents.length > 0 ? (
        <div className="activity-list">
          {prioritizedEvents.map((activity, index) => (
            <div className="activity-item" key={`${activity.topic}-${index}`}>
              <span className={`level level-${activity.level}`}>{activity.level}</span>
              <div>
                <div className="activity-topic">
                  {activity.topic}
                  {activity.object_id ? ` / ${activity.object_id}` : ""}
                </div>
                <div className="activity-message">{activity.message}</div>
                <ActivityObjectActions
                  activity={activity}
                  commandCatalog={commandCatalog}
                  onFocusActivityObject={onFocusActivityObject}
                  onRunCommand={onRunCommand}
                  onSelectActivityObject={onSelectActivityObject}
                />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="selection-empty">
          Structured STEP inspection is shown above. No additional backend activity is pending for
          the current report view.
        </p>
      )}
    </section>
  );
}

function CommandCatalog({
  catalog,
  onRunCommand,
  taskPanel
}: {
  catalog: CommandCatalogResponse | null;
  onRunCommand: (commandId: string) => void;
  taskPanel: TaskPanelResponse | null;
}) {
  if (!catalog) {
    return null;
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Command Deck</h2>
        <span>{catalog.workbench.display_name}</span>
      </div>
      <div className="command-catalog">
        {catalog.commands.map((command) => {
          const suggested = taskPanel?.suggested_commands.includes(command.command_id) ?? false;
          return (
            <button
              className={`command-card ${suggested ? "command-card-suggested" : ""}`}
              disabled={!command.enabled}
              key={command.command_id}
              onClick={() => onRunCommand(command.command_id)}
              type="button"
            >
              <div className="command-card-top">
                <div className="command-card-title">
                  <ShellIcon icon={command.icon} title={command.label} />
                  <strong>{command.label}</strong>
                </div>
                {command.shortcut ? <span>{command.shortcut}</span> : null}
              </div>
              <div className="command-card-meta">
                <span>{command.group}</span>
                <span>{command.requires_selection ? "selection" : "global"}</span>
              </div>
              <p>{command.description}</p>
            </button>
          );
        })}
      </div>
    </section>
  );
}

function QuickActionRail({
  catalog,
  onRunCommand
}: {
  catalog: CommandCatalogResponse | null;
  onRunCommand: (commandId: string) => void;
}) {
  if (!catalog) {
    return null;
  }

  const quickCommandIds = [
    "document.undo",
    "document.redo",
    "document.recompute",
    "document.save",
    "selection.focus",
    "history.resume_full"
  ];

  const commands = quickCommandIds
    .map((commandId) => catalog.commands.find((command) => command.command_id === commandId))
    .filter((command): command is CommandDefinition => Boolean(command));

  return (
    <div className="quick-action-rail">
      {commands.map((command) => (
        <button
          className={`action-button ${command.command_id === "document.recompute" ? "action-button-primary" : ""}`}
          disabled={!command.enabled}
          key={command.command_id}
          onClick={() => onRunCommand(command.command_id)}
          style={getToolbarButtonStyle({
            disabled: !command.enabled,
            primary: command.command_id === "document.recompute"
          })}
          type="button"
        >
          <span>{command.action_label ?? command.label}</span>
          {command.shortcut ? <strong>{command.shortcut}</strong> : null}
        </button>
      ))}
    </div>
  );
}

function getToolbarButtonStyle({ disabled, primary }: { disabled: boolean; primary: boolean }) {
  const baseStyle = {
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
    minHeight: 24,
    padding: "2px 8px",
    whiteSpace: "nowrap",
    flexShrink: 0,
    borderRadius: 4,
    fontSize: 11,
    fontWeight: 600,
    lineHeight: 1.1,
    cursor: disabled ? "default" : "pointer"
  } as const;

  if (disabled) {
    return {
      ...baseStyle,
      border: "1px solid rgba(120, 130, 142, 0.82)",
      background: "linear-gradient(180deg, rgba(84, 91, 100, 0.94), rgba(63, 69, 76, 0.97))",
      color: "rgba(206, 214, 223, 0.82)",
      boxShadow: "inset 0 1px 0 rgba(255, 255, 255, 0.08)",
      opacity: 1
    } as const;
  }

  if (primary) {
    return {
      ...baseStyle,
      border: "1px solid rgba(49, 70, 97, 0.96)",
      background: "linear-gradient(180deg, rgba(87, 116, 150, 0.95), rgba(59, 84, 116, 0.98))",
      color: "#f8fbff",
      boxShadow: "inset 0 1px 0 rgba(255, 255, 255, 0.2)"
    } as const;
  }

  return {
    ...baseStyle,
    border: "1px solid var(--shell-frame-border)",
    background: "linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(225, 231, 238, 0.96))",
    color: "var(--shell-text-strong)",
    boxShadow: "inset 0 1px 0 rgba(255, 255, 255, 0.7)"
  } as const;
}

function ShellToolbarBands({
  catalog,
  onRunCommand,
  shellSnapshot
}: {
  catalog: CommandCatalogResponse | null;
  onRunCommand: (commandId: string) => void;
  shellSnapshot: ShellSnapshot | null;
}) {
  if (!catalog || !shellSnapshot) {
    return <QuickActionRail catalog={catalog} onRunCommand={onRunCommand} />;
  }

  const commandById = new Map(catalog.commands.map((command) => [command.command_id, command]));

  return (
    <div className="shell-toolbar-bands" style={{ display: "flex", flexWrap: "wrap", alignItems: "center" }}>
      {shellSnapshot.toolbar_bands.bands.map((band) => (
        <div
          className="shell-toolbar-band"
          key={band.band_id}
          style={{ display: "grid", gridTemplateColumns: "auto auto", alignItems: "center" }}
        >
          <span className="dock-strip-label">{band.label}</span>
          <div className="shell-toolbar-band-actions" style={{ display: "flex", flexWrap: "nowrap" }}>
            {band.toolbars.filter((toolbar) => toolbar.visible).map((toolbar) => (
              <div
                className="shell-toolbar-group"
                key={toolbar.toolbar_id}
                style={{ display: "flex", flexWrap: "nowrap", alignItems: "center" }}
              >
                {toolbar.items.map((item, index) => {
                  if (item.kind === "separator") {
                    return <span className="shell-toolbar-separator" key={`${toolbar.toolbar_id}-${index}`} />;
                  }

                  const command = item.command_id ? commandById.get(item.command_id) : undefined;
                  const label = item.label ?? command?.action_label ?? command?.label ?? item.command_id;
                  const enabled = item.enabled ?? command?.enabled ?? false;
                  const isPrimary = item.command_id === "document.recompute";

                  return (
                    <button
                      className={`action-button ${isPrimary ? "action-button-primary" : ""}`}
                      disabled={!enabled || !item.command_id}
                      key={item.command_id ?? `${toolbar.toolbar_id}-${index}`}
                      onClick={() => {
                        if (item.command_id) {
                          onRunCommand(item.command_id);
                        }
                      }}
                      style={getToolbarButtonStyle({ disabled: !enabled || !item.command_id, primary: isPrimary })}
                      title={toolbar.label}
                      type="button"
                    >
                      <ShellIcon icon={item.icon} title={item.icon ?? undefined} />
                      <span>{label}</span>
                    </button>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function SessionTabs({
  sessions,
  activeDocumentId,
  onActivate
}: {
  sessions: WorkspaceSession[];
  activeDocumentId: string | null;
  onActivate: (session: WorkspaceSession) => void;
}) {
  if (sessions.length === 0) {
    return null;
  }

  return (
    <section className="session-tabs-shell">
      <div className="session-tabs">
        {sessions.map((session) => {
          const active = session.document_id === activeDocumentId;

          return (
            <button
              className={`session-tab ${active ? "session-tab-active" : ""}`}
              key={session.session_id}
              onClick={() => onActivate(session)}
              type="button"
            >
              <div className="session-tab-main">
                <strong>{session.display_name}</strong>
                <span>{session.file_path.split("/").at(-1) ?? session.file_path}</span>
              </div>
              <div className="session-tab-meta">
                <span>{session.workbench}</span>
                <span>{session.dirty ? "Unsaved" : "Saved"}</span>
              </div>
            </button>
          );
        })}
      </div>
    </section>
  );
}

function SelectionModeToolbar({
  selectionState,
  onChangeMode
}: {
  selectionState: SelectionStateResponse | null;
  onChangeMode: (modeId: string) => void;
}) {
  if (!selectionState) {
    return null;
  }

  return (
    <section className="selection-mode-toolbar">
      <div className="selection-mode-header">
        <div>
          <span className="selection-label">Selection Mode</span>
          <strong>{selectionState.selected_object_label}</strong>
        </div>
        <span className="selection-mode-meta">{selectionState.selected_object_type}</span>
      </div>
      <div className="selection-mode-list">
        {selectionState.available_modes.map((mode) => {
          const active = mode.mode_id === selectionState.current_mode;

          return (
            <button
              className={`selection-mode-chip ${active ? "selection-mode-chip-active" : ""}`}
              disabled={!mode.enabled}
              key={mode.mode_id}
              onClick={() => onChangeMode(mode.mode_id)}
              type="button"
            >
              <strong>{mode.label}</strong>
              <span>{mode.object_count} mapped</span>
              <small>{mode.description}</small>
            </button>
          );
        })}
      </div>
    </section>
  );
}

export function CommandPalette({
  catalog,
  open,
  query,
  onQueryChange,
  onClose,
  onRunCommand,
  targetOptions
}: {
  catalog: CommandCatalogResponse | null;
  open: boolean;
  query: string;
  onQueryChange: (value: string) => void;
  onClose: () => void;
  onRunCommand: (
    commandId: string,
    commandArguments?: Record<string, string>,
    targetObjectId?: string
  ) => void;
  targetOptions: CommandTargetOption[];
}) {
  const [selectedCommandId, setSelectedCommandId] = useState<string | null>(null);
  const [activeTargetObjectId, setActiveTargetObjectId] = useState<string | null>(null);
  const [draftArguments, setDraftArguments] = useState<Record<string, Record<string, string>>>({});

  useEffect(() => {
    if (!open || !catalog) {
      setSelectedCommandId(null);
      setActiveTargetObjectId(null);
      setDraftArguments({});
      return;
    }

    const nextCommand = catalog.commands.find((command) => {
      const haystack = [
        command.label,
        command.group,
        command.description,
        command.action_label ?? "",
        command.shortcut ?? ""
      ]
        .join(" ")
        .toLowerCase();
      return haystack.includes(query.trim().toLowerCase());
    }) ?? catalog.commands[0] ?? null;

    setSelectedCommandId((current) =>
      current && catalog.commands.some((command) => command.command_id === current)
        ? current
        : nextCommand?.command_id ?? null
    );

    setDraftArguments((current) => initializeCommandDrafts(current, catalog.commands));
  }, [catalog, open, query]);

  useEffect(() => {
    if (!open) {
      setActiveTargetObjectId(null);
      return;
    }

    setActiveTargetObjectId((current) =>
      current && targetOptions.some((option) => option.objectId === current)
        ? current
        : targetOptions[0]?.objectId ?? null
    );
  }, [open, targetOptions]);

  if (!open || !catalog) {
    return null;
  }

  const normalizedQuery = query.trim().toLowerCase();
  const filteredCommands = catalog.commands.filter((command) => {
    if (!normalizedQuery) {
      return true;
    }

    const haystack = [
      command.label,
      command.group,
      command.description,
      command.action_label ?? "",
      command.shortcut ?? ""
    ]
      .join(" ")
      .toLowerCase();

    return haystack.includes(normalizedQuery);
  });
  const selectedCommand =
    filteredCommands.find((command) => command.command_id === selectedCommandId) ??
    filteredCommands[0] ??
    null;
  const activeTarget = targetOptions.find((option) => option.objectId === activeTargetObjectId) ?? null;
  const requiresTarget = Boolean(selectedCommand?.requires_selection);

  function currentDraftValue(commandId: string, argument: CommandArgumentDefinition) {
    return draftArguments[commandId]?.[argument.argument_id] ?? argument.default_value ?? "";
  }

  function updateDraftValue(commandId: string, argumentId: string, value: string) {
    setDraftArguments((current) => ({
      ...current,
      [commandId]: {
        ...(current[commandId] ?? {}),
        [argumentId]: value
      }
    }));
  }

  return (
    <div
      className="command-palette-backdrop"
      onClick={onClose}
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          onClose();
        }
      }}
      role="presentation"
    >
      <section
        className="command-palette"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="command-palette-header">
          <div>
            <div className="eyebrow">Command Palette</div>
            <h2>{catalog.workbench.display_name}</h2>
          </div>
          <button className="action-button" onClick={onClose} type="button">
            Close
          </button>
        </div>
        <input
          autoFocus
          className="command-palette-input"
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="Search commands, groups, shortcuts, descriptions..."
          value={query}
        />
        <div className="command-palette-body">
          <div className="command-palette-list">
            {filteredCommands.map((command) => (
              <button
                className={`command-palette-item ${
                  command.enabled ? "" : "command-palette-item-disabled"
                } ${
                  selectedCommand?.command_id === command.command_id
                    ? "command-palette-item-selected"
                    : ""
                }`}
                key={command.command_id}
                onClick={() => setSelectedCommandId(command.command_id)}
                type="button"
              >
                <div className="command-palette-main">
                  <div className="command-palette-title">
                    <ShellIcon icon={command.icon} title={command.label} />
                    <strong>{command.action_label ?? command.label}</strong>
                  </div>
                  <span>{command.description}</span>
                </div>
                <div className="command-palette-meta">
                  <span>{command.group}</span>
                  {command.shortcut ? <span>{command.shortcut}</span> : null}
                </div>
              </button>
            ))}
            {filteredCommands.length === 0 ? (
              <div className="command-palette-empty">No commands match this search.</div>
            ) : null}
          </div>
          {selectedCommand ? (
            <div className="command-palette-detail">
              <div className="command-palette-detail-head">
                <div>
                  <div className="command-palette-detail-title">
                    <ShellIcon icon={selectedCommand.icon} title={selectedCommand.label} />
                    <strong>{selectedCommand.action_label ?? selectedCommand.label}</strong>
                  </div>
                  <p>{selectedCommand.description}</p>
                </div>
                <div className="command-palette-meta">
                  <span>{selectedCommand.group}</span>
                  {selectedCommand.shortcut ? <span>{selectedCommand.shortcut}</span> : null}
                </div>
              </div>
              {requiresTarget ? (
                <div className="command-palette-target-panel">
                  <div className="command-palette-target-header">
                    <span className="selection-label">Command Target</span>
                    <strong>{activeTarget?.label ?? "No target selected"}</strong>
                  </div>
                  {targetOptions.length > 0 ? (
                    <div className="command-palette-target-list">
                      {targetOptions.map((option) => {
                        const active = option.objectId === activeTargetObjectId;

                        return (
                          <button
                            className={`command-palette-target-chip ${active ? "command-palette-target-chip-active" : ""}`}
                            key={option.objectId}
                            onClick={() => setActiveTargetObjectId(option.objectId)}
                            type="button"
                          >
                            <strong>{option.label}</strong>
                            <span>{option.detail}</span>
                          </button>
                        );
                      })}
                    </div>
                  ) : (
                    <p className="selection-empty">Selection-required commands need an active selected or hovered object.</p>
                  )}
                </div>
              ) : null}
              {selectedCommand.arguments.length > 0 ? (
                <SuggestedCommandEditor
                  className="command-palette-form"
                  command={selectedCommand}
                  currentDraftValue={(argument) =>
                    currentDraftValue(selectedCommand.command_id, argument)
                  }
                  headerLabel={selectedCommand.action_label ?? selectedCommand.label}
                  idPrefix="palette"
                  onSubmitCommand={(commandArguments) =>
                    onRunCommand(
                      selectedCommand.command_id,
                      commandArguments,
                      requiresTarget ? activeTargetObjectId ?? undefined : undefined
                    )
                  }
                  onUpdateDraftValue={(argumentId, value) =>
                    updateDraftValue(selectedCommand.command_id, argumentId, value)
                  }
                  submitLabel={selectedCommand.action_label ?? selectedCommand.label}
                />
              ) : (
                <button
                  className="action-button action-button-primary"
                  disabled={!selectedCommand.enabled || (requiresTarget && !activeTargetObjectId)}
                  onClick={() =>
                    onRunCommand(
                      selectedCommand.command_id,
                      undefined,
                      requiresTarget ? activeTargetObjectId ?? undefined : undefined
                    )
                  }
                  type="button"
                >
                  {selectedCommand.action_label ?? selectedCommand.label}
                </button>
              )}
            </div>
          ) : null}
        </div>
      </section>
    </div>
  );
}

function FeatureTimeline({
  history,
  selectedObjectId,
  onSelect,
  onToggleSuppression,
  onRollbackHere,
  onResumeFull
}: {
  history: FeatureHistoryResponse | null;
  selectedObjectId: string | null;
  onSelect: (objectId: string) => void;
  onToggleSuppression: (objectId: string) => void;
  onRollbackHere: (objectId: string) => void;
  onResumeFull: () => void;
}) {
  if (!history) {
    return null;
  }

  const rollbackActive = history.entries.some((entry) => entry.rolled_back);

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Feature Timeline</h2>
        <div className="timeline-header-meta">
          <span>{history.entries.length} entries</span>
          {rollbackActive ? (
            <button className="timeline-resume" onClick={onResumeFull} type="button">
              Resume Full
            </button>
          ) : null}
        </div>
      </div>
      <div className="timeline">
        {history.entries.map((entry) => (
          <div
              className={`timeline-entry ${
                selectedObjectId === entry.object_id ? "timeline-entry-selected" : ""
              } ${entry.suppressed ? "timeline-entry-suppressed" : ""} ${
                !entry.active && !entry.suppressed ? "timeline-entry-inactive" : ""
              } ${entry.rolled_back ? "timeline-entry-rolled-back" : ""
              }`}
              key={entry.object_id}
            >
            <div className="timeline-index">{entry.sequence_index}</div>
            <button
              className="timeline-main"
              onClick={() => onSelect(entry.object_id)}
              type="button"
            >
              <div className="timeline-content">
                <strong>{entry.label}</strong>
                <span>{entry.role}</span>
                <span>{entry.source_object_id ? `from ${entry.source_object_id}` : "root sketch"}</span>
                <span className="timeline-state">
                  {entry.suppressed
                    ? "suppressed"
                    : entry.active
                      ? "active"
                      : "inactive"}
                </span>
                {entry.inactive_reason ? (
                  <span className="timeline-reason">{entry.inactive_reason}</span>
                ) : null}
              </div>
            </button>
              <div className="timeline-actions">
                <button
                  className="timeline-rollback"
                  onClick={(event) => {
                    event.stopPropagation();
                    onRollbackHere(entry.object_id);
                  }}
                  type="button"
                >
                  Roll Here
                </button>
                <button
                  className="timeline-toggle"
                  onClick={(event) => {
                    event.stopPropagation();
                    onToggleSuppression(entry.object_id);
                  }}
                  type="button"
                >
                  {entry.suppressed ? "Unsuppress" : "Suppress"}
                </button>
              </div>
            </div>
          ))}
        </div>
    </section>
  );
}

function TaskPanel({
  taskPanel,
  commandCatalog,
  onRunCommand
}: {
  taskPanel: TaskPanelResponse | null;
  commandCatalog: CommandCatalogResponse | null;
  onRunCommand: (commandId: string, commandArguments?: Record<string, string>) => void;
}) {
  const [commandDrafts, setCommandDrafts] = useState<Record<string, Record<string, string>>>({});

  useEffect(() => {
    if (!taskPanel || !commandCatalog) {
      setCommandDrafts({});
      return;
    }

    setCommandDrafts((current) =>
      initializeSuggestedCommandDrafts(current, commandCatalog, taskPanel.suggested_commands)
    );
  }, [taskPanel, commandCatalog]);

  if (!taskPanel) {
    return null;
  }

  const suggestedCommands = resolveSuggestedCommands(commandCatalog, taskPanel.suggested_commands);

  function updateDraftValue(
    commandId: string,
    argumentId: string,
    value: string
  ) {
    setCommandDrafts((current) => ({
      ...current,
      [commandId]: {
        ...(current[commandId] ?? {}),
        [argumentId]: value
      }
    }));
  }

  function currentDraftValue(commandId: string, argument: CommandArgumentDefinition) {
    return commandDrafts[commandId]?.[argument.argument_id] ?? argument.default_value ?? "";
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Task Panel</h2>
        <span>{taskPanel.title}</span>
      </div>
      <p className="task-panel-description">{taskPanel.description}</p>
      <div className="task-sections">
        {taskPanel.sections.map((section) => (
          <div className="task-section" key={section.section_id}>
            <h3>{section.title}</h3>
            <div className="task-rows">
              {section.rows.map((row, index) => (
                <div className="task-row" key={`${section.section_id}-${index}`}>
                  <span>{row.label}</span>
                  <strong className={row.emphasis ? "task-row-emphasis" : ""}>{row.value}</strong>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
      {suggestedCommands.length > 0 ? (
        <div className="task-editor-grid">
          {suggestedCommands.map((command) =>
            command.arguments.length > 0 ? (
              <SuggestedCommandEditor
                className="task-editor"
                command={command}
                currentDraftValue={(argument) => currentDraftValue(command.command_id, argument)}
                headerLabel={command.label}
                idPrefix="task"
                key={command.command_id}
                onSubmitCommand={(commandArguments) => onRunCommand(command.command_id, commandArguments)}
                onUpdateDraftValue={(argumentId, value) =>
                  updateDraftValue(command.command_id, argumentId, value)
                }
                submitLabel={command.action_label ?? command.label}
              />
            ) : (
              <div className="task-editor" key={command.command_id}>
                <div className="task-editor-header">
                  <CommandSummaryContent command={command} label={command.label} />
                </div>
                <p className="task-command-note">{command.description}</p>
                <button
                  className="action-button action-button-primary"
                  disabled={!command.enabled}
                  onClick={() => onRunCommand(command.command_id)}
                  type="button"
                >
                  {command.action_label ?? command.label}
                </button>
              </div>
            )
          )}
        </div>
      ) : null}
    </section>
  );
}

export function NotificationCenter({
  commandCatalog,
  onFocusNoticeObject,
  onRunNoticeCommand,
  onSelectNoticeObject,
  notices
}: {
  commandCatalog?: CommandCatalogResponse | null;
  onFocusNoticeObject?: (objectId: string) => void;
  onRunNoticeCommand?: (commandId: string, targetObjectId?: string) => void;
  onSelectNoticeObject?: (objectId: string) => void;
  notices: ShellNotice[];
}) {
  if (notices.length === 0) {
    return null;
  }

  return (
    <section className="panel shell-notices">
      <div className="panel-header">
        <h2>Shell Notices</h2>
        <span>{notices.length} live signals</span>
      </div>
      <div className="notice-list">
        {notices.map((notice) => (
          <div className={`notice-card notice-card-${notice.level}`} key={notice.id}>
            <div className="notice-card-top">
              <span className={`level level-${notice.level}`}>{notice.level}</span>
              <strong>{notice.title}</strong>
            </div>
            <p>{notice.detail}</p>
            {notice.objectId || notice.commandAction ? (
              <ActivityObjectActions
                activity={{ object_id: notice.objectId, topic: notice.title.replaceAll(" ", "_") }}
                commandActionOverride={notice.commandAction}
                commandCatalog={commandCatalog}
                onFocusActivityObject={onFocusNoticeObject}
                onRunCommand={onRunNoticeCommand}
                onSelectActivityObject={onSelectNoticeObject}
              />
            ) : null}
          </div>
        ))}
      </div>
    </section>
  );
}

export function SelectionInspector({
  selectedObjectId,
  preselectionState,
  objectTree,
  properties,
  featureHistory,
  commandCatalog,
  onRunSelectedCommand,
  onRunPreselectionCommand,
  onPromotePreselectionCommand,
  viewport
}: {
  selectedObjectId: string | null;
  preselectionState: PreselectionStateResponse | null;
  objectTree: ObjectNode[];
  properties: PropertyResponse | null;
  featureHistory: FeatureHistoryResponse | null;
  commandCatalog: CommandCatalogResponse | null;
  onRunSelectedCommand: (commandId: string, commandArguments?: Record<string, string>) => void;
  onRunPreselectionCommand: (commandId: string, commandArguments?: Record<string, string>) => void;
  onPromotePreselectionCommand: (commandId: string) => void;
  viewport: ViewportResponse | null;
}) {
  const [selectedCommandDrafts, setSelectedCommandDrafts] = useState<Record<string, Record<string, string>>>({});
  const [preselectionDrafts, setPreselectionDrafts] = useState<Record<string, Record<string, string>>>({});

  useEffect(() => {
    if (!commandCatalog || !preselectionState?.object_id) {
      setPreselectionDrafts({});
      return;
    }

    setPreselectionDrafts((current) =>
      initializeSuggestedCommandDrafts(current, commandCatalog, preselectionState.suggested_commands)
    );
  }, [commandCatalog, preselectionState]);

  const selectedNode = selectedObjectId
    ? flattenObjectTree(objectTree).find((node) => node.object_id === selectedObjectId) ?? null
    : null;
  const historyEntry = selectedObjectId
    ? featureHistory?.entries.find((entry) => entry.object_id === selectedObjectId) ?? null
    : null;
  const selectedDrawable = selectedObjectId
    ? viewport?.scene.drawables.find((drawable) => drawable.object_id === selectedObjectId) ?? null
    : null;
  const enabledCommands =
    commandCatalog?.commands.filter(
      (command) =>
        command.enabled &&
        (!command.requires_selection || Boolean(selectedObjectId))
    ) ?? [];
  const visibleSelectedCommands = enabledCommands.slice(0, 6);
  const visibleSelectedCommandIds = visibleSelectedCommands.map((command) => command.command_id);
  const visibleSelectedCommandKey = visibleSelectedCommandIds.join("|");
  const preselectionCommands = resolveSuggestedCommands(
    commandCatalog,
    preselectionState?.suggested_commands
  );
  const topPropertyGroup = properties?.groups[0] ?? null;

  useEffect(() => {
    if (!commandCatalog || !selectedObjectId) {
      setSelectedCommandDrafts({});
      return;
    }

    setSelectedCommandDrafts((current) =>
      initializeSuggestedCommandDrafts(
        current,
        commandCatalog,
        visibleSelectedCommandIds
      )
    );
  }, [commandCatalog, selectedObjectId, visibleSelectedCommandKey]);

  function updateSelectedDraftValue(
    commandId: string,
    argumentId: string,
    value: string
  ) {
    setSelectedCommandDrafts((current) => ({
      ...current,
      [commandId]: {
        ...(current[commandId] ?? {}),
        [argumentId]: value
      }
    }));
  }

  function currentSelectedDraftValue(
    commandId: string,
    argument: CommandArgumentDefinition
  ) {
    return selectedCommandDrafts[commandId]?.[argument.argument_id] ?? argument.default_value ?? "";
  }

  function updatePreselectionDraftValue(
    commandId: string,
    argumentId: string,
    value: string
  ) {
    setPreselectionDrafts((current) => ({
      ...current,
      [commandId]: {
        ...(current[commandId] ?? {}),
        [argumentId]: value
      }
    }));
  }

  function currentPreselectionDraftValue(
    commandId: string,
    argument: CommandArgumentDefinition
  ) {
    return preselectionDrafts[commandId]?.[argument.argument_id] ?? argument.default_value ?? "";
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Selection Inspector</h2>
        <span>{selectedObjectId ?? "No selection"}</span>
      </div>
      <div className="selection-inspector">
        <div className="selection-card">
          <span className="selection-label">Object</span>
          <strong>{selectedNode?.label ?? "Nothing selected"}</strong>
          <span className="selection-meta">{selectedNode?.object_type ?? "No backend object focus"}</span>
        </div>
        <div className="selection-card">
          <span className="selection-label">Model State</span>
          <strong>
            {historyEntry
              ? historyEntry.suppressed
                ? "Suppressed"
                : historyEntry.rolled_back
                  ? "Rolled back"
                  : historyEntry.active
                    ? "Active"
                    : "Inactive"
              : "Context object"}
          </strong>
          <span className="selection-meta">
            {historyEntry?.inactive_reason ??
              (selectedDrawable ? "Visible in viewport scene" : "No visible drawable in current scene")}
          </span>
        </div>
        <div className="selection-card">
          <span className="selection-label">Viewport Presence</span>
          <strong>{selectedDrawable ? selectedDrawable.kind : "Not rendered"}</strong>
          <span className="selection-meta">
            {selectedDrawable
              ? `${selectedDrawable.bounds.width.toFixed(1)} x ${selectedDrawable.bounds.height.toFixed(1)}`
              : "Hidden, rolled back, or non-visual object"}
          </span>
        </div>
      </div>
      <div className="selection-detail-grid">
        <div className="selection-detail">
          <h3>Property Focus</h3>
          {topPropertyGroup ? (
            <div className="selection-kv-list">
              {topPropertyGroup.properties.slice(0, 3).map((property) => (
                <div className="selection-kv" key={property.property_id}>
                  <span>{property.display_name}</span>
                  <strong>{property.value_preview}</strong>
                </div>
              ))}
            </div>
          ) : (
            <p className="selection-empty">No property payload loaded for the current selection.</p>
          )}
        </div>
        <div className="selection-detail">
          <h3>Available Commands</h3>
          {enabledCommands.length > 0 ? (
            <div className="selection-command-list">
              {visibleSelectedCommands.map((command) => {
                if (command.arguments.length > 0) {
                  return (
                    <SuggestedCommandEditor
                      className="selection-action-editor"
                      command={command}
                      currentDraftValue={(argument) => currentSelectedDraftValue(command.command_id, argument)}
                      idPrefix="selected"
                      key={`selected-form-${command.command_id}`}
                      onSubmitCommand={(commandArguments) =>
                        onRunSelectedCommand(command.command_id, commandArguments)
                      }
                      onUpdateDraftValue={(argumentId, value) =>
                        updateSelectedDraftValue(command.command_id, argumentId, value)
                      }
                      submitLabel={command.action_label ?? command.label}
                    />
                  );
                }

                return (
                  <button
                    className="selection-command-chip selection-command-chip-button"
                    key={command.command_id}
                    onClick={() => onRunSelectedCommand(command.command_id)}
                    type="button"
                  >
                    <CommandSummaryContent command={command} />
                  </button>
                );
              })}
            </div>
          ) : (
            <p className="selection-empty">No enabled commands are currently available.</p>
          )}
        </div>
        <div className="selection-detail">
          <h3>Hover Guidance</h3>
          {preselectionState?.object_id ? (
            <div className="selection-kv-list">
              <div className="selection-kv">
                <span>Candidate</span>
                <strong>{preselectionState.object_label ?? preselectionState.object_id}</strong>
              </div>
              <div className="selection-kv">
                <span>State</span>
                <strong>{preselectionState.model_state}</strong>
              </div>
              <div className="selection-kv">
                <span>Dependency</span>
                <strong>{preselectionState.dependency_note}</strong>
              </div>
              <div className="selection-command-list">
                {preselectionCommands.slice(0, 4).map((command) => (
                  command.arguments.length > 0 ? (
                    <SuggestedCommandEditor
                      className="selection-action-editor"
                      command={command}
                      currentDraftValue={(argument) => currentPreselectionDraftValue(command.command_id, argument)}
                      idPrefix="hover"
                      key={`hover-form-${command.command_id}`}
                      onSubmitCommand={(commandArguments) =>
                        onRunPreselectionCommand(command.command_id, commandArguments)
                      }
                      onUpdateDraftValue={(argumentId, value) =>
                        updatePreselectionDraftValue(command.command_id, argumentId, value)
                      }
                      submitLabel="Run On Hovered"
                    />
                  ) : (
                    <button
                      className="selection-command-chip selection-command-chip-button"
                      key={`hover-${command.command_id}`}
                      onClick={() => onPromotePreselectionCommand(command.command_id)}
                      type="button"
                    >
                      <CommandSummaryContent command={command} />
                    </button>
                  )
                ))}
              </div>
            </div>
          ) : (
            <p className="selection-empty">Hover a selectable object to preview backend guidance.</p>
          )}
        </div>
      </div>
    </section>
  );
}

function DiagnosticsPanel({
  diagnostics,
  commandStatus
}: {
  diagnostics: DiagnosticsResponse | null;
  commandStatus: CommandExecutionResponse | null;
}) {
  if (!diagnostics) {
    return null;
  }

  const commandHealth = commandStatus
    ? commandStatus.accepted
      ? "Backend accepted the latest command."
      : "Latest command was rejected and needs attention."
    : "No recent command execution recorded in this session.";

  return (
    <section className="panel panel-wide">
      <div className="panel-header">
        <h2>Diagnostics</h2>
        <span>{diagnostics.selection.object_id ?? "No active selection"}</span>
      </div>
      <div className="diagnostic-summary-grid">
        <div className="diagnostic-card">
          <span className="diagnostic-label">History Health</span>
          <strong>{diagnostics.summary.total_features} steps tracked</strong>
          <p>
            {diagnostics.summary.suppressed_count} suppressed, {diagnostics.summary.inactive_count} inactive,{" "}
            {diagnostics.summary.rolled_back_count} rolled back
          </p>
        </div>
        <div className="diagnostic-card">
          <span className="diagnostic-label">Viewport Scene</span>
          <strong>{diagnostics.summary.viewport_drawable_count} drawables live</strong>
          <p>
            {diagnostics.summary.history_marker_active
              ? "Scene is currently filtered by the history rollback marker."
              : `Full scene is active in ${diagnostics.summary.worker_mode}.`}
          </p>
        </div>
        <div className="diagnostic-card">
          <span className="diagnostic-label">Event Stream</span>
          <strong>
            {diagnostics.summary.warning_count +
              diagnostics.summary.error_count +
              diagnostics.recent_signals.filter((signal) => signal.level === "info").length}{" "}
            signals sampled
          </strong>
          <p>
            {diagnostics.recent_signals.filter((signal) => signal.level === "info").length} info,{" "}
            {diagnostics.summary.warning_count} warnings, {diagnostics.summary.error_count} errors
          </p>
        </div>
        <div className="diagnostic-card">
          <span className="diagnostic-label">Last Command</span>
          <strong>{commandStatus?.command_id ?? "No recent command"}</strong>
          <p>{commandHealth}</p>
        </div>
      </div>
      <div className="diagnostic-detail-grid">
        <div className="diagnostic-detail">
          <h3>Selection Health</h3>
          <div className="selection-kv-list">
            <div className="selection-kv">
              <span>Selected object</span>
              <strong>{diagnostics.selection.object_id ?? "None"}</strong>
            </div>
            <div className="selection-kv">
              <span>Timeline state</span>
              <strong>{diagnostics.selection.model_state}</strong>
            </div>
            <div className="selection-kv">
              <span>Dependency note</span>
              <strong>{diagnostics.selection.dependency_note}</strong>
            </div>
            <div className="selection-kv">
              <span>Viewport visibility</span>
              <strong>{diagnostics.selection.visible_in_viewport ? "Visible" : "Not visible"}</strong>
            </div>
          </div>
        </div>
        <div className="diagnostic-detail">
          <h3>Recent Signals</h3>
          <div className="diagnostic-event-list">
            {diagnostics.recent_signals.map((signal, index) => (
              <div className="diagnostic-event" key={`${signal.title}-${index}`}>
                <span className={`level level-${signal.level}`}>{signal.level}</span>
                <div>
                  <strong>{signal.title}</strong>
                  <p>{signal.detail}</p>
                </div>
              </div>
            ))}
            {diagnostics.recent_signals.length === 0 ? (
              <p className="selection-empty">No backend events have been published yet.</p>
            ) : null}
          </div>
        </div>
      </div>
    </section>
  );
}

function JobsPanel({
  jobs
}: {
  jobs: JobStatusResponse | null;
}) {
  if (!jobs) {
    return null;
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Jobs</h2>
        <span>{jobs.jobs.length} recent</span>
      </div>
      <div className="jobs-list">
        {jobs.jobs.length > 0 ? (
          jobs.jobs.map((job) => (
            <div className="job-card" key={job.job_id}>
              <div className="job-card-top">
                <strong>{job.title}</strong>
                <span className={`job-state job-state-${job.state}`}>{job.state}</span>
              </div>
              <div className="job-progress">
                <div className="job-progress-bar" style={{ width: `${job.progress_percent}%` }} />
              </div>
              <p>{job.detail}</p>
              <div className="job-stage-list">
                {job.stages.map((stage) => (
                  <div className="job-stage-chip" key={`${job.job_id}-${stage.stage_id}`}>
                    <span>{stage.label}</span>
                    <strong>{stage.progress_percent}%</strong>
                  </div>
                ))}
              </div>
              <div className="job-meta">
                <span>{job.command_id}</span>
                <span>{job.object_id ?? "global"}</span>
              </div>
            </div>
          ))
        ) : (
          <p className="selection-empty">No backend jobs have been recorded yet.</p>
        )}
      </div>
    </section>
  );
}

const initialPath = "C:/models/actuator-mount.FCStd";

function applyViewportDiff(
  current: ViewportResponse,
  diff: ViewportDiffResponse
): ViewportResponse {
  const removedSet = new Set(diff.removed);
  let drawables = current.scene.drawables.filter(
    (d) => !removedSet.has(d.object_id)
  );

  const modifiedMap = new Map(diff.modified.map((d) => [d.object_id, d]));
  drawables = drawables.map((d) => modifiedMap.get(d.object_id) ?? d);

  drawables = drawables.concat(diff.added);

  return {
    document_id: diff.document_id,
    selected_object_id: diff.selected_object_id,
    scene: {
      camera_eye: diff.camera_eye ?? current.scene.camera_eye,
      camera_target: diff.camera_target ?? current.scene.camera_target,
      drawables,
    },
  };
}

function isStepFilePath(filePath: string | null | undefined) {
  return Boolean(filePath && /\.(stp|step|p21)$/i.test(filePath));
}

function flattenObjectTree(nodes: ObjectNode[]): ObjectNode[] {
  return nodes.flatMap((node) => [node, ...flattenObjectTree(node.children)]);
}

function objectMatchesSelectionMode(objectType: string, selectionMode: string) {
  switch (selectionMode) {
    case "object":
      return true;
    case "body":
      return objectType === "PartDesign::Body";
    case "sketch":
      return objectType === "Sketcher::SketchObject";
    case "feature":
      return objectType === "PartDesign::Pad" || objectType === "PartDesign::Pocket";
    default:
      return false;
  }
}

export default function App() {
  const [boot, setBoot] = useState<BootPayload | null>(null);
  const [document, setDocument] = useState<DocumentRef | null>(null);
  const [shellSnapshot, setShellSnapshot] = useState<ShellSnapshot | null>(null);
  const [objectTree, setObjectTree] = useState<ObjectNode[]>([]);
  const [selectedObjectId, setSelectedObjectId] = useState<string | null>(null);
  const [properties, setProperties] = useState<PropertyResponse | null>(null);
  const [viewport, setViewport] = useState<ViewportResponse | null>(null);
  const [featureHistory, setFeatureHistory] = useState<FeatureHistoryResponse | null>(null);
  const [commandCatalog, setCommandCatalog] = useState<CommandCatalogResponse | null>(null);
  const [taskPanel, setTaskPanel] = useState<TaskPanelResponse | null>(null);
  const [diagnostics, setDiagnostics] = useState<DiagnosticsResponse | null>(null);
  const [preselectionState, setPreselectionState] = useState<PreselectionStateResponse | null>(null);
  const [selectionState, setSelectionState] = useState<SelectionStateResponse | null>(null);
  const [jobs, setJobs] = useState<JobStatusResponse | null>(null);
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [commandStatus, setCommandStatus] = useState<CommandExecutionResponse | null>(null);
  const [stepDocument, setStepDocument] = useState<StepDocumentIndex | null>(null);
  const [stepScene, setStepScene] = useState<StepSceneBundle | null>(null);
  const [stepViewportPreset, setStepViewportPreset] = useState<StepViewportPreset | null>(null);
  const [stepStatus, setStepStatus] = useState<"idle" | "loading" | "ready" | "unavailable" | "error">("idle");
  const [openPath, setOpenPath] = useState(initialPath);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [paletteQuery, setPaletteQuery] = useState("");
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        setLoading(true);
        const payload = await fetchBootstrap();
        if (!active) {
          return;
        }

        setBoot(payload);
        setDocument(payload.document);
        setShellSnapshot(payload.shell_snapshot);
        setObjectTree(payload.object_tree);
        setSelectedObjectId(payload.selected_object_id);
        setProperties(payload.properties);
        setViewport(payload.viewport);
        setFeatureHistory(payload.feature_history);
        setCommandCatalog(payload.command_catalog);
        setTaskPanel(payload.task_panel);
        setDiagnostics(payload.diagnostics);
        setPreselectionState(payload.preselection_state);
        setSelectionState(payload.selection_state);
        setJobs(payload.jobs);
        setEvents(payload.events);
        setError(null);
      } catch (reason) {
        if (!active) {
          return;
        }
        setError(reason instanceof Error ? reason.message : "Failed to load backend");
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setPaletteOpen(true);
        return;
      }

      if (event.key === "Escape") {
        setPaletteOpen(false);
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  useEffect(() => {
    let active = true;

    async function loadStepArtifacts() {
      if (!document?.document_id || !isStepFilePath(document.file_path)) {
        if (!active) {
          return;
        }
        setStepDocument(null);
        setStepScene(null);
        setStepStatus("unavailable");
        return;
      }

      try {
        setStepStatus("loading");
        const [nextStepDocument, nextStepScene] = await Promise.all([
          fetchStepDocumentIndex(document.document_id),
          fetchStepSceneBundle(document.document_id)
        ]);
        if (!active) {
          return;
        }

        setStepDocument(nextStepDocument);
        setStepScene(nextStepScene);
        setStepStatus("ready");
      } catch (reason) {
        if (!active) {
          return;
        }

        setStepDocument(null);
        setStepScene(null);
        if (reason instanceof Error && /404/.test(reason.message)) {
          setStepStatus("unavailable");
          return;
        }

        setStepStatus("error");
      }
    }

    void loadStepArtifacts();
    return () => {
      active = false;
    };
  }, [document?.document_id, document?.file_path]);

  useEffect(() => {
    setStepViewportPreset(null);
  }, [document?.document_id]);

  async function refreshDocumentSlices(
    documentId: string,
    objectId?: string,
    documentOverride?: DocumentRef
  ) {
    const nextSelectionState = await fetchSelectionState(documentId);
    const resolvedObjectId = objectId ?? nextSelectionState.selected_object_id;
    const [
      nextProperties,
      nextObjectTree,
      nextViewport,
      nextHistory,
      nextEvents,
      nextCommandCatalog,
      nextTaskPanel,
      nextDiagnostics,
      nextPreselectionState,
      nextJobs,
      nextShellSnapshot
    ] = await Promise.all([
      fetchProperties(documentId, resolvedObjectId),
      fetchObjectTree(documentId),
      fetchViewport(documentId),
      fetchFeatureHistory(documentId),
      fetchEvents(documentId),
      fetchCommandCatalog(documentId),
      fetchTaskPanel(documentId),
      fetchDiagnostics(documentId),
      fetchPreselectionState(documentId),
      fetchJobs(documentId),
      fetchShellSnapshot(documentId)
    ]);
    const activeDocument = documentOverride ?? document ?? nextShellSnapshot.document;
    setProperties(nextProperties);
    setObjectTree(nextObjectTree);
    setViewport(nextViewport);
    setFeatureHistory(nextHistory);
    setEvents(nextEvents);
    setCommandCatalog(nextCommandCatalog);
    setTaskPanel(nextTaskPanel);
    setDiagnostics(nextDiagnostics);
    setPreselectionState(nextPreselectionState);
    setSelectionState(nextSelectionState);
    setSelectedObjectId(nextSelectionState.selected_object_id);
    setJobs(nextJobs);
    setShellSnapshot(nextShellSnapshot);
    if (activeDocument) {
      setDocument(activeDocument);
      setBoot((current) =>
        current
          ? {
              ...current,
              document: activeDocument,
              object_tree: nextObjectTree,
              selected_object_id: nextSelectionState.selected_object_id,
              properties: nextProperties,
              viewport: nextViewport,
              feature_history: nextHistory,
              command_catalog: nextCommandCatalog,
              task_panel: nextTaskPanel,
              diagnostics: nextDiagnostics,
              selection_state: nextSelectionState,
              preselection_state: nextPreselectionState,
              jobs: nextJobs,
              shell_snapshot: nextShellSnapshot,
              events: nextEvents
            }
          : current
      );
    }
  }

  async function handleSelect(objectId: string) {
    if (!document) {
      return;
    }

    setSelectedObjectId(objectId);
    try {
      const selection = await setSelection(document.document_id, objectId);
      setSelectedObjectId(selection.selected_object_id);
      await refreshDocumentSlices(document.document_id, selection.selected_object_id);
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Failed to fetch selection");
    }
  }

  async function handleSelectAndCommand(
    objectId: string,
    commandId: string,
    extraArguments: Record<string, string> = {}
  ) {
    if (!document) {
      return;
    }

    setSelectedObjectId(objectId);
    try {
      const selection = await setSelection(document.document_id, objectId);
      setSelectedObjectId(selection.selected_object_id);
      await handleCommand(commandId, extraArguments);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Failed to coordinate selection");
    }
  }

  async function handleSelectionModeChange(modeId: string) {
    if (!document) {
      return;
    }

    try {
      const nextSelectionState = await setSelectionMode(document.document_id, modeId);
      setSelectionState(nextSelectionState);
      setSelectedObjectId(nextSelectionState.selected_object_id);
      await refreshDocumentSlices(document.document_id, nextSelectionState.selected_object_id);
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Failed to update selection mode");
    }
  }

  async function handlePreselectionChange(objectId: string | null) {
    if (!document) {
      return;
    }

    if (preselectionState?.object_id === objectId) {
      return;
    }

    try {
      const nextPreselectionState = await setPreselection(document.document_id, objectId);
      setPreselectionState(nextPreselectionState);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Failed to update preselection");
    }
  }

  async function handlePromotePreselectionCommand(commandId: string) {
    if (!preselectionState?.object_id) {
      return;
    }

    await handleSelectAndCommand(preselectionState.object_id, commandId);
  }

  async function handleRunPreselectionCommand(
    commandId: string,
    commandArguments: Record<string, string> = {}
  ) {
    if (!preselectionState?.object_id) {
      return;
    }

    await handleSelectAndCommand(preselectionState.object_id, commandId, commandArguments);
  }

  async function handleCommand(
    commandId: string,
    extraArguments: Record<string, string> = {},
    targetObjectId?: string
  ) {
    if (!document) {
      return;
    }

    const command = commandCatalog?.commands.find(
      (item: CommandDefinition) => item.command_id === commandId
    );
    if (command && !command.enabled) {
      return;
    }

    const defaultArguments = Object.fromEntries(
      (command?.arguments ?? [])
        .filter((argument) => argument.default_value !== null)
        .map((argument) => [argument.argument_id, argument.default_value ?? ""])
    );

    try {
      const effectiveTargetObjectId = targetObjectId ?? selectedObjectId ?? undefined;
      const response = await runCommand({
        command_id: commandId,
        document_id: document.document_id,
        target_object_id: effectiveTargetObjectId,
        arguments: {
          source: "react-shell",
          ...defaultArguments,
          ...extraArguments
        }
      });
      setCommandStatus(response);
      if (response.accepted) {
        const appliedPreset = stepViewportPresetFromCommand(commandId);
        if (appliedPreset) {
          setStepViewportPreset(appliedPreset);
        } else if (commandId === "selection.focus" || isStepViewportResetCommand(commandId)) {
          setStepViewportPreset(null);
        }
      }
      const nextDocument = {
        ...document,
        dirty: response.document_dirty
      };
      setDocument(nextDocument);

      // Apply incremental diff when available, fall back to full fetch
      if (response.viewport_diff && viewport) {
        const patched = applyViewportDiff(viewport, response.viewport_diff);
        setViewport(patched);
        setSelectedObjectId(patched.selected_object_id);
        await refreshDocumentSlices(document.document_id, patched.selected_object_id, nextDocument);
      } else if (selectedObjectId || effectiveTargetObjectId) {
        const nextViewport = await fetchViewport(document.document_id);
        setSelectedObjectId(nextViewport.selected_object_id);
        await refreshDocumentSlices(document.document_id, nextViewport.selected_object_id, nextDocument);
      } else {
        setEvents(await fetchEvents(document.document_id));
      }

      setError(null);
      setPaletteOpen(false);
      setPaletteQuery("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Failed to run command");
    }
  }

  async function handleOpenDocument(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!document && !boot) {
      return;
    }

    await openDocumentPath(openPath);
  }

  async function handleWorkbenchChange(workbenchId: string) {
    if (!document) {
      return;
    }

    const enabledWorkbenchCount = (shellSnapshot?.workbench_catalog.workbenches ?? []).filter(
      (workbench) => workbench.enabled
    ).length;
    if (enabledWorkbenchCount <= 1) {
      return;
    }

    const activeWorkbenchId = shellSnapshot?.workbench_catalog.active_workbench_id ?? document.workbench.toLowerCase();
    if (workbenchId === activeWorkbenchId) {
      return;
    }

    try {
      const nextDocument = await activateWorkbench(document.document_id, workbenchId);
      await refreshDocumentSlices(
        nextDocument.document_id,
        selectedObjectId ?? selectionState?.selected_object_id,
        nextDocument
      );
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Failed to activate workbench");
    }
  }

  async function openDocumentPath(filePath: string) {
    if (!boot && !document) {
      return;
    }

    try {
      const nextDocument = await openDocument(filePath);
      const [
        nextViewport,
        nextCommandCatalog,
        nextTaskPanel,
        nextEvents,
        nextDiagnostics,
        nextPreselectionState,
        nextSelectionState,
        nextJobs,
        nextShellSnapshot
      ] = await Promise.all([
        fetchViewport(nextDocument.document_id),
        fetchCommandCatalog(nextDocument.document_id),
        fetchTaskPanel(nextDocument.document_id),
        fetchEvents(nextDocument.document_id),
        fetchDiagnostics(nextDocument.document_id),
        fetchPreselectionState(nextDocument.document_id),
        fetchSelectionState(nextDocument.document_id),
        fetchJobs(nextDocument.document_id),
        fetchShellSnapshot(nextDocument.document_id)
      ]);
      const nextHistory = await fetchFeatureHistory(nextDocument.document_id);
      const nextObjectTree = await fetchObjectTree(nextDocument.document_id);
      const nextSelectedObjectId = nextViewport.selected_object_id;
      const nextProperties = await fetchProperties(
        nextDocument.document_id,
        nextSelectedObjectId
      );

      setDocument(nextDocument);
      setObjectTree(nextObjectTree);
      setSelectedObjectId(nextSelectedObjectId);
      setViewport(nextViewport);
      setFeatureHistory(nextHistory);
      setProperties(nextProperties);
      setCommandCatalog(nextCommandCatalog);
      setTaskPanel(nextTaskPanel);
      setDiagnostics(nextDiagnostics);
      setPreselectionState(nextPreselectionState);
      setSelectionState(nextSelectionState);
      setJobs(nextJobs);
      setShellSnapshot(nextShellSnapshot);
      setEvents(nextEvents);
      setCommandStatus(null);
      setBoot((current) =>
        current
          ? {
              ...current,
              document: nextDocument,
              object_tree: nextObjectTree,
              selected_object_id: nextSelectedObjectId,
              properties: nextProperties,
              viewport: nextViewport,
              feature_history: nextHistory,
              command_catalog: nextCommandCatalog,
              task_panel: nextTaskPanel,
              diagnostics: nextDiagnostics,
              selection_state: nextSelectionState,
              preselection_state: nextPreselectionState,
              jobs: nextJobs,
              shell_snapshot: nextShellSnapshot,
              events: nextEvents
            }
          : current
        );
      setOpenPath(filePath);
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Failed to open document");
    }
  }

  async function handlePanelTabChange(panelId: string, activeTab: string) {
    if (!document) {
      return;
    }

    try {
      const nextShellSnapshot = await updateShellPanelState(document.document_id, panelId, {
        active_tab: activeTab,
        visible: true
      });
      setShellSnapshot(nextShellSnapshot);
      setBoot((current) =>
        current
          ? {
              ...current,
              shell_snapshot: nextShellSnapshot
            }
          : current
      );
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Failed to update shell layout");
    }
  }

  async function handlePanelVisibilityChange(panelId: "combo_view" | "report_dock", visible: boolean) {
    if (!document) {
      return;
    }

    try {
      const nextShellSnapshot = await updateShellPanelState(document.document_id, panelId, {
        visible
      });
      setShellSnapshot(nextShellSnapshot);
      setBoot((current) =>
        current
          ? {
              ...current,
              shell_snapshot: nextShellSnapshot
            }
          : current
      );
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Failed to update panel visibility");
    }
  }

  async function handlePanelSizeChange(
    panelId: "combo_view" | "report_dock",
    nextSizeHint: number
  ) {
    if (!document) {
      return;
    }

    try {
      const nextShellSnapshot = await updateShellPanelState(document.document_id, panelId, {
        size_hint: nextSizeHint
      });
      setShellSnapshot(nextShellSnapshot);
      setBoot((current) =>
        current
          ? {
              ...current,
              shell_snapshot: nextShellSnapshot
            }
          : current
      );
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Failed to resize panel");
    }
  }

  async function handleMenuAction(commandId: string | null | undefined) {
    setOpenMenuId(null);
    if (!commandId) {
      return;
    }

    switch (commandId) {
      case "shell.toggle_combo_view":
        await handlePanelVisibilityChange("combo_view", !comboViewVisible);
        return;
      case "shell.show_model_stack":
        await handlePanelTabChange("combo_view", "model");
        return;
      case "shell.show_task_stack":
        await handlePanelTabChange("combo_view", "tasks");
        return;
      case "shell.toggle_bottom_dock":
        await handlePanelVisibilityChange("report_dock", !reportDockVisible);
        return;
      case "shell.show_report_view":
        await handlePanelTabChange("report_dock", "report");
        return;
      case "shell.show_python_console":
        await handlePanelTabChange("report_dock", "python");
        return;
      case "shell.show_extensions_manager":
        await handlePanelTabChange("report_dock", "extensions");
        return;
      default:
        await handleCommand(commandId);
    }
  }

  async function handleApplyStepViewportPreset(preset: StepViewportPreset) {
    await handleCommand(STEP_VIEWPORT_COMMAND_BY_PRESET[preset]);
  }

  async function handleResetStepViewportPreset() {
    setStepViewportPreset(null);
    await handleCommand("step.view_reset");
  }

  async function handleFitAllStepViewport() {
    setStepViewportPreset(null);
    await handleCommand("step.view_fit_all");
  }

  const reportEvents = filteredReportEvents(events, shellSnapshot, selectedObjectId);
  const flattenedTree = flattenObjectTree(objectTree);
  const objectTypeById = new Map(flattenedTree.map((node) => [node.object_id, node.object_type]));
  const selectableObjectCount = flattenedTree.filter((node) =>
    objectMatchesSelectionMode(node.object_type, selectionState?.current_mode ?? "object")
  ).length;
  const stepAvailable = stepStatus === "ready" && Boolean(stepDocument) && Boolean(stepScene);
  const stepProtocolSummary = stepDocument?.header.application_protocols.join(", ") ?? "No STEP payload";
  const paletteTargetOptions: CommandTargetOption[] = [
    selectedObjectId && selectionState
      ? {
          objectId: selectedObjectId,
          label: selectionState.selected_object_label,
          detail: `Selected ${selectionState.selected_object_type}`
        }
      : null,
    preselectionState?.selectable && preselectionState.object_id && preselectionState.object_id !== selectedObjectId
      ? {
          objectId: preselectionState.object_id,
          label: preselectionState.object_label ?? preselectionState.object_id,
          detail: `Hovered ${preselectionState.object_type ?? "object"}`
        }
      : null
  ].filter((option): option is CommandTargetOption => Boolean(option));
  if (loading) {
    return <div className="splash">Connecting AsterForge shell to backend...</div>;
  }

  if (error && !boot) {
    return (
      <div className="splash splash-error">
        <strong>AsterForge backend unavailable</strong>
        <span>{error}</span>
      </div>
    );
  }

  if (!boot || !document) {
    return (
      <div className="splash splash-error">
        <strong>No boot payload received</strong>
      </div>
    );
  }

  const visibleMenus = shellSnapshot?.menu_bar.menus.filter((menu) => menu.visible) ?? [];
  const workbenchOptions = shellSnapshot?.workbench_catalog.workbenches ?? [];
  const fallbackWorkbenchOption = {
    workbench_id: document.workbench.toLowerCase(),
    display_name: document.workbench,
    enabled: true,
    icon: undefined,
    description: undefined,
    category: "Current context",
    migration_lane: "Bridge surfaced"
  };
  const selectableWorkbenchOptions =
    workbenchOptions.length > 0 ? workbenchOptions : [fallbackWorkbenchOption];
  const activeWorkbenchId = shellSnapshot?.workbench_catalog.active_workbench_id ?? document.workbench.toLowerCase();
  const activeWorkbench = workbenchOptions.find(
    (workbench) => workbench.workbench_id === activeWorkbenchId
  ) ?? fallbackWorkbenchOption;
  const workbenchLocked = selectableWorkbenchOptions.length <= 1;
  const visiblePanels = shellSnapshot?.layout.panels.filter((panel) => panel.visible).length ?? 0;
  const recentDocuments: RecentDocumentEntry[] = shellSnapshot?.recent_documents ?? [];
  const workspaceSessions: WorkspaceSession[] =
    (shellSnapshot?.workspace_sessions ?? []).map((session: WorkspaceSessionEntry) => ({
      ...session,
      selected_object_id: session.selected_object_id ?? null
    }));
  const comboViewTab =
    shellSnapshot?.layout.panels.find((panel) => panel.panel_id === "combo_view")?.active_tab ??
    "model";
  const bottomDockTab =
    shellSnapshot?.layout.panels.find((panel) => panel.panel_id === "report_dock")?.active_tab ??
    "report";
  const includeActivityNotices = bottomDockTab !== "report";
  const extensionCompatibility = (
    shellSnapshot as (ShellSnapshot & { extension_compatibility?: ExtensionCompatibilityState }) | null
  )?.extension_compatibility;
  const commandNotice: ShellNotice[] =
    commandStatus &&
    !shouldHideStructuredInspectionCommandNotice(commandStatus, shellSnapshot, selectedObjectId) &&
    !shouldHideCommandNoticeForActivity(commandStatus, reportEvents)
      ? [
          {
            id: `command-${commandStatus.command_id}-${commandStatus.accepted ? "ok" : "warn"}`,
            level: commandStatus.accepted ? "info" : "warning",
            title: commandNoticeTitle(commandCatalog, commandStatus.command_id),
            detail: commandStatus.status_message,
            objectId: commandNoticeObjectId(
              commandCatalog,
              commandStatus.command_id,
              selectedObjectId
            ),
            commandAction: commandNoticeAction(commandCatalog, commandStatus.command_id)
          }
        ]
      : [];
  const eventNotices = buildEventNotices(reportEvents, includeActivityNotices, 4);
  const shellNotices = buildShellNotices(commandNotice, eventNotices);
  const comboViewPanel = shellSnapshot?.layout.panels.find((panel) => panel.panel_id === "combo_view");
  const reportDockPanel = shellSnapshot?.layout.panels.find((panel) => panel.panel_id === "report_dock");
  const comboViewVisible = comboViewPanel?.visible ?? true;
  const reportDockVisible = reportDockPanel?.visible ?? true;
  const comboViewSizeHint = comboViewPanel?.size_hint ?? 0.28;
  const reportDockSizeHint = reportDockPanel?.size_hint ?? 0.24;
  const comboColumnPercent = Math.round(comboViewSizeHint * 100);
  const workspaceStyle = comboViewVisible
    ? {
        gridTemplateColumns: `minmax(260px, ${comboColumnPercent}%) minmax(0, ${100 - comboColumnPercent}%)`
      }
    : {
        gridTemplateColumns: "minmax(0, 1fr)"
      };
  const mainColumnStyle = reportDockVisible
    ? {
        gridTemplateRows: `minmax(0, ${Math.max(0.45, 1 - reportDockSizeHint)}fr) minmax(200px, ${reportDockSizeHint}fr)`
      }
    : {
        gridTemplateRows: "minmax(0, 1fr)"
      };
  const reopenTabs: Array<{ panelId: "combo_view" | "report_dock"; label: string }> = [
    ...(comboViewVisible ? [] : [{ panelId: "combo_view" as const, label: "Show Combo View" }]),
    ...(reportDockVisible ? [] : [{ panelId: "report_dock" as const, label: "Show Bottom Dock" }])
  ];

  return (
    <div className="app-shell freecad-shell">
      <div className="freecad-menubar">
        {visibleMenus.map((menu) => (
          <div
            className={`freecad-menu ${openMenuId === menu.menu_id ? "freecad-menu-open" : ""}`}
            key={menu.menu_id}
            onMouseLeave={() => setOpenMenuId((current) => (current === menu.menu_id ? null : current))}
          >
            <button
              aria-expanded={openMenuId === menu.menu_id}
              className="freecad-menu-button"
              onClick={() =>
                setOpenMenuId((current) => (current === menu.menu_id ? null : menu.menu_id))
              }
              type="button"
            >
              {menu.label}
            </button>
            {openMenuId === menu.menu_id ? (
              <div className="freecad-menu-dropdown">
                {menu.items.map((item, index) =>
                  item.kind === "separator" ? (
                    <div className="freecad-menu-separator" key={`${menu.menu_id}-separator-${index}`} />
                  ) : (
                    <button
                      className={`freecad-menu-item ${item.checked ? "freecad-menu-item-checked" : ""}`}
                      disabled={item.enabled === false}
                      key={`${menu.menu_id}-${item.label ?? item.command_id ?? index}`}
                      onClick={() => void handleMenuAction(item.command_id)}
                      type="button"
                    >
                      <span className="freecad-menu-item-check">{item.checked ? "x" : ""}</span>
                      <span className="freecad-menu-item-label">{item.label ?? item.command_id ?? "Unavailable"}</span>
                    </button>
                  )
                )}
              </div>
            ) : null}
          </div>
        ))}
      </div>

      <div className="freecad-toolbar-stack">
        <div className="freecad-toolbar-row">
          <div className="freecad-brand">
            <div className="freecad-frame-title">FreeCAD</div>
            <strong>{document.display_name}</strong>
          </div>
          <label className="workbench-picker">
            <span>Workbench</span>
            <div className="workbench-active-chip">
              <ShellIcon icon={activeWorkbench.icon} title={activeWorkbench.display_name} />
              <div>
                <strong>{activeWorkbench.display_name}</strong>
                <small className="workbench-active-chip-meta">
                  {activeWorkbench.category} | {activeWorkbench.migration_lane}
                </small>
              </div>
            </div>
            {workbenchLocked ? (
              <div className="workbench-lock-note">
                {activeWorkbench.description ?? "Workbench is fixed by the active document context."}
              </div>
            ) : (
              <select
                value={activeWorkbenchId}
                onChange={(event) => void handleWorkbenchChange(event.target.value)}
              >
                {selectableWorkbenchOptions.map((workbench) => (
                  <option disabled={!workbench.enabled} key={workbench.workbench_id} value={workbench.workbench_id}>
                    {workbench.display_name} ({workbench.category}, {workbench.migration_lane})
                  </option>
                ))}
              </select>
            )}
          </label>
          <form className="open-form freecad-open-form" onSubmit={handleOpenDocument}>
            <input
              className="open-input"
              onChange={(event) => setOpenPath(event.target.value)}
              placeholder="C:/models/example.FCStd"
              value={openPath}
            />
            <button className="action-button action-button-primary" type="submit">
              Open
            </button>
          </form>
          <button className="action-button" onClick={() => setPaletteOpen(true)} type="button">
            Command Palette
            <strong>Ctrl+K</strong>
          </button>
        </div>

        <div className="freecad-toolbar-row freecad-toolbar-row-compact">
          <ShellToolbarBands
            catalog={commandCatalog}
            onRunCommand={(commandId) => void handleCommand(commandId)}
            shellSnapshot={shellSnapshot}
          />
          <div className="status-cluster">
            <span className="badge badge-hot">{document.workbench}</span>
            <span className="badge">{document.dirty ? "Unsaved changes" : "Saved"}</span>
            <span className="badge">{boot.boot_report.services.length} backend services</span>
            <span className="badge">{boot.bridge_status.worker_mode}</span>
            <span className="badge">{visiblePanels} visible panels</span>
          </div>
          {reopenTabs.length > 0 ? (
            <div className="shell-layout-actions">
              {reopenTabs.map((entry) => (
                <button
                  className="action-button"
                  key={entry.panelId}
                  onClick={() => void handlePanelVisibilityChange(entry.panelId, true)}
                  type="button"
                >
                  {entry.label}
                </button>
              ))}
            </div>
          ) : null}
        </div>

        {recentDocuments.length > 0 ? (
          <div className="freecad-toolbar-row freecad-toolbar-row-compact">
            <span className="dock-strip-label">Recent</span>
            <div className="recent-docs-list">
              {recentDocuments.map((entry) => (
                <button
                  className={`recent-doc-chip ${openPath === entry.file_path ? "recent-doc-chip-active" : ""}`}
                  key={entry.file_path}
                  onClick={() => setOpenPath(entry.file_path)}
                  type="button"
                >
                  {entry.display_name}
                </button>
              ))}
            </div>
          </div>
        ) : null}
      </div>

      <SessionTabs
        activeDocumentId={document.document_id}
        onActivate={(session) => {
          if (session.document_id === document.document_id) {
            setOpenPath(session.file_path);
            return;
          }
          void openDocumentPath(session.file_path);
        }}
        sessions={workspaceSessions}
      />

      <CommandPalette
        catalog={commandCatalog}
        onClose={() => setPaletteOpen(false)}
        onQueryChange={setPaletteQuery}
        onRunCommand={(commandId, commandArguments, targetObjectId) =>
          void handleCommand(commandId, commandArguments ?? {}, targetObjectId)
        }
        open={paletteOpen}
        query={paletteQuery}
        targetOptions={paletteTargetOptions}
      />

      {error ? <div className="inline-alert">{error}</div> : null}

      <main className="freecad-workspace" style={workspaceStyle}>
        {comboViewVisible ? (
        <aside className="panel freecad-combo-view">
          <div className="dock-tab-strip">
            <button
              className={`dock-tab-button ${comboViewTab === "model" ? "dock-tab-button-active" : ""}`}
              onClick={() => void handlePanelTabChange("combo_view", "model")}
              type="button"
            >
              Model
            </button>
            <button
              className={`dock-tab-button ${comboViewTab === "tasks" ? "dock-tab-button-active" : ""}`}
              onClick={() => void handlePanelTabChange("combo_view", "tasks")}
              type="button"
            >
              Tasks
            </button>
            <button
              className="dock-tab-button dock-tab-button-utility"
              onClick={() => void handlePanelSizeChange("combo_view", comboViewSizeHint - 0.03)}
              type="button"
            >
              Narrower
            </button>
            <button
              className="dock-tab-button dock-tab-button-utility"
              onClick={() => void handlePanelSizeChange("combo_view", comboViewSizeHint + 0.03)}
              type="button"
            >
              Wider
            </button>
            <button
              className="dock-tab-button dock-tab-button-utility"
              onClick={() => void handlePanelVisibilityChange("combo_view", false)}
              type="button"
            >
              Hide
            </button>
          </div>

          {comboViewTab === "model" ? (
            <div className="combo-view-body combo-model-stack">
              <section className="dock-panel combo-pane">
                <div className="panel-header panel-header-dense">
                  <h2>Model</h2>
                  <span>
                    {selectionState
                      ? `${selectionState.current_mode} / ${selectableObjectCount} selectable`
                      : document.file_path ?? "Unsaved document"}
                  </span>
                </div>
                <div className="tree-panel combo-pane-scroll">
                  {objectTree.map((node) => (
                    <TreeNode
                      key={node.object_id}
                      node={node}
                      onHoverChange={(objectId) => void handlePreselectionChange(objectId)}
                      onSelect={handleSelect}
                      preselectedObjectId={preselectionState?.object_id ?? null}
                      selectedObjectId={selectedObjectId}
                      selectionMode={selectionState?.current_mode ?? "object"}
                    />
                  ))}
                </div>
              </section>

              <section className="dock-panel combo-pane combo-pane-properties">
                <div className="panel-header panel-header-dense">
                  <h2>Data</h2>
                  <span>{properties?.object_id ?? "No active selection"}</span>
                </div>
                <div className="property-groups combo-pane-scroll">
                  {(properties?.groups ?? []).map((group) => (
                    <div className="property-group" key={group.group_id}>
                      <h3>{group.title}</h3>
                      {group.properties.map((property) => (
                        <div className="property-row" key={property.property_id}>
                          <div>
                            <div className="property-name">{property.display_name}</div>
                            <div className="property-type">{property.property_type}</div>
                          </div>
                          <div className="property-value">
                            <span>{property.value_preview}</span>
                            {property.expression_capable ? <em>fx</em> : null}
                          </div>
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              </section>
            </div>
          ) : (
            <div className="combo-view-body combo-view-task-stack">
              <TaskPanel
                commandCatalog={commandCatalog}
                onRunCommand={(commandId, commandArguments) =>
                  void handleCommand(commandId, commandArguments ?? {})
                }
                taskPanel={taskPanel}
              />
              <SelectionInspector
                commandCatalog={commandCatalog}
                featureHistory={featureHistory}
                objectTree={objectTree}
                onRunSelectedCommand={(commandId, commandArguments) =>
                  void handleCommand(commandId, commandArguments ?? {})
                }
                onPromotePreselectionCommand={(commandId) =>
                  void handlePromotePreselectionCommand(commandId)
                }
                onRunPreselectionCommand={(commandId, commandArguments) =>
                  void handleRunPreselectionCommand(commandId, commandArguments ?? {})
                }
                preselectionState={preselectionState}
                properties={properties}
                selectedObjectId={selectedObjectId}
                viewport={viewport}
              />
            </div>
          )}
        </aside>
        ) : null}

        <section className="freecad-main-column" style={mainColumnStyle}>
          <section className="panel viewport-panel freecad-viewport-panel">
            <div className="panel-header">
              <h2>3D View</h2>
              <span>{document.file_path ?? "Unsaved document"}</span>
            </div>
            <div className="viewport-canvas">
              {stepAvailable && stepDocument && stepScene ? (
                <StepViewportScene
                  cameraEye={viewport?.scene.camera_eye}
                  cameraTarget={viewport?.scene.camera_target}
                  onHoverChange={(objectId) => void handlePreselectionChange(objectId)}
                  onSelect={handleSelect}
                  preselectedObjectId={preselectionState?.object_id ?? null}
                  selectedObjectId={selectedObjectId}
                  shellSnapshot={shellSnapshot}
                  stepDocument={stepDocument}
                  stepScene={stepScene}
                  visibleDrawables={viewport?.scene.drawables}
                />
              ) : (
                <ViewportScene
                  objectTypeById={objectTypeById}
                  onHoverChange={(objectId) => void handlePreselectionChange(objectId)}
                  onSelect={handleSelect}
                  preselectedObjectId={preselectionState?.object_id ?? null}
                  selectedObjectId={selectedObjectId}
                  selectionMode={selectionState?.current_mode ?? "object"}
                  viewport={viewport}
                />
              )}
              <ViewportHeadsUp
                activePreset={stepViewportPreset}
                cameraEye={viewport?.scene.camera_eye}
                cameraTarget={viewport?.scene.camera_target}
                comboViewVisible={comboViewVisible}
                onChangeSelectionMode={(modeId) => void handleSelectionModeChange(modeId)}
                onApplyPreset={(preset) => void handleApplyStepViewportPreset(preset)}
                onFitAll={() => void handleFitAllStepViewport()}
                onFocusSelection={() => void handleCommand("selection.focus")}
                onOpenModel={() => void handlePanelTabChange("combo_view", "model")}
                onOpenReport={() => void handlePanelTabChange("report_dock", "report")}
                onOpenTasks={() => void handlePanelTabChange("combo_view", "tasks")}
                onResetPreset={() => void handleResetStepViewportPreset()}
                reportDockVisible={reportDockVisible}
                selectionState={selectionState}
                selectedObjectId={selectedObjectId}
                stepAvailable={stepAvailable}
              />
              <div className="viewport-overlay">
                <span>
                  {stepAvailable
                    ? "STEP scene streaming from parser-backed gateway state"
                    : "Selection synchronized through backend state"}
                </span>
                <strong>
                  {stepAvailable && stepDocument
                    ? `${stepDocument.assemblies.length} root STEP assemblies`
                    : selectedObjectId
                      ? `Focused object: ${selectedObjectId}`
                      : "No object selected"}
                </strong>
                <em>
                  {stepAvailable
                    ? `Protocols: ${stepProtocolSummary}`
                    : preselectionState?.object_label
                      ? `Hover candidate: ${preselectionState.object_label}`
                      : "Hover candidate: none"}
                </em>
                {stepAvailable && stepScene ? (
                  <em>
                    {stepScene.semantic_pmi.length} PMI notes, {stepScene.tessellated_representations.length} tessellated sets
                  </em>
                ) : null}
                {stepStatus === "loading" ? <em>Loading STEP scene bundle...</em> : null}
                <ViewportHoverCard
                  commandCatalog={commandCatalog}
                  onPromotePreselectionCommand={(commandId) => void handlePromotePreselectionCommand(commandId)}
                  preselectionState={preselectionState}
                />
              </div>
            </div>
            <SelectionModeToolbar
              onChangeMode={(modeId) => void handleSelectionModeChange(modeId)}
              selectionState={selectionState}
            />
            {commandStatus ? (
              <div
                className={`command-status ${commandStatus.accepted ? "command-status-ok" : "command-status-warn"}`}
              >
                {commandStatus.status_message}
              </div>
            ) : null}
          </section>

          {reportDockVisible ? (
          <section className="panel freecad-bottom-dock">
            <div className="dock-tab-strip dock-tab-strip-bottom">
              <button
                className={`dock-tab-button ${bottomDockTab === "report" ? "dock-tab-button-active" : ""}`}
                onClick={() => void handlePanelTabChange("report_dock", "report")}
                type="button"
              >
                Report view
              </button>
              <button
                className={`dock-tab-button ${bottomDockTab === "python" ? "dock-tab-button-active" : ""}`}
                onClick={() => void handlePanelTabChange("report_dock", "python")}
                type="button"
              >
                Python console
              </button>
              <button
                className={`dock-tab-button ${bottomDockTab === "jobs" ? "dock-tab-button-active" : ""}`}
                onClick={() => void handlePanelTabChange("report_dock", "jobs")}
                type="button"
              >
                Jobs
              </button>
              <button
                className={`dock-tab-button ${bottomDockTab === "diagnostics" ? "dock-tab-button-active" : ""}`}
                onClick={() => void handlePanelTabChange("report_dock", "diagnostics")}
                type="button"
              >
                Diagnostics
              </button>
              <button
                className={`dock-tab-button ${bottomDockTab === "history" ? "dock-tab-button-active" : ""}`}
                onClick={() => void handlePanelTabChange("report_dock", "history")}
                type="button"
              >
                History
              </button>
              <button
                className={`dock-tab-button ${bottomDockTab === "commands" ? "dock-tab-button-active" : ""}`}
                onClick={() => void handlePanelTabChange("report_dock", "commands")}
                type="button"
              >
                Commands
              </button>
              <button
                className={`dock-tab-button ${bottomDockTab === "extensions" ? "dock-tab-button-active" : ""}`}
                onClick={() => void handlePanelTabChange("report_dock", "extensions")}
                type="button"
              >
                Extensions
              </button>
              <button
                className="dock-tab-button dock-tab-button-utility"
                onClick={() => void handlePanelSizeChange("report_dock", reportDockSizeHint - 0.03)}
                type="button"
              >
                Shorter
              </button>
              <button
                className="dock-tab-button dock-tab-button-utility"
                onClick={() => void handlePanelSizeChange("report_dock", reportDockSizeHint + 0.03)}
                type="button"
              >
                Taller
              </button>
              <button
                className="dock-tab-button dock-tab-button-utility"
                onClick={() => void handlePanelVisibilityChange("report_dock", false)}
                type="button"
              >
                Hide
              </button>
            </div>

            <div className="bottom-dock-content">
              {bottomDockTab === "report" ? (
                <div className="bottom-dock-report">
                  <NotificationCenter
                    commandCatalog={commandCatalog}
                    notices={shellNotices}
                    onFocusNoticeObject={(objectId) =>
                      void handleSelectAndCommand(objectId, "selection.focus")
                    }
                    onRunNoticeCommand={(commandId, targetObjectId) =>
                      void handleCommand(commandId, {}, targetObjectId)
                    }
                    onSelectNoticeObject={(objectId) => void handleSelect(objectId)}
                  />
                  <ReportInspectionSummary
                    commandCatalog={commandCatalog}
                    onRunCommand={(commandId, targetObjectId) =>
                      void handleCommand(commandId, {}, targetObjectId)
                    }
                    shellSnapshot={shellSnapshot}
                  />
                  <ReportActivityFeed
                    commandCatalog={commandCatalog}
                    onFocusActivityObject={(objectId) =>
                      void handleSelectAndCommand(objectId, "selection.focus")
                    }
                    onRunCommand={(commandId, targetObjectId) =>
                      void handleCommand(commandId, {}, targetObjectId)
                    }
                    onSelectActivityObject={(objectId) => void handleSelect(objectId)}
                    reportEvents={reportEvents}
                  />
                </div>
              ) : null}

              {bottomDockTab === "python" ? (
                <section className="dock-panel python-console-placeholder">
                  <div className="panel-header">
                    <h2>Python Console</h2>
                    <span>Compatibility host planned</span>
                  </div>
                  <div className="python-console-shell">
                    <div className="python-console-log">
                      <div>{">>> import FreeCAD as App"}</div>
                      <div>{">>> App.ActiveDocument"}</div>
                      <div>{"<Backend automation bridge pending>"}</div>
                    </div>
                    <div className="python-console-note">
                      This dock slot is intentionally reserved now so the React shell matches the
                      classic FreeCAD workspace anatomy while we wire a real backend console
                      service next.
                    </div>
                  </div>
                </section>
              ) : null}

              {bottomDockTab === "jobs" ? <JobsPanel jobs={jobs} /> : null}
              {bottomDockTab === "diagnostics" ? (
                <DiagnosticsPanel commandStatus={commandStatus} diagnostics={diagnostics} />
              ) : null}
              {bottomDockTab === "history" ? (
                <FeatureTimeline
                  history={featureHistory}
                  onSelect={(objectId) => void handleSelect(objectId)}
                  onRollbackHere={(objectId) => {
                    if (selectedObjectId !== objectId) {
                      void handleSelectAndCommand(objectId, "history.rollback_here");
                      return;
                    }
                    void handleCommand("history.rollback_here");
                  }}
                  onResumeFull={() => void handleCommand("history.resume_full")}
                  onToggleSuppression={(objectId) => {
                    if (selectedObjectId !== objectId) {
                      void handleSelectAndCommand(objectId, "model.toggle_suppression");
                      return;
                    }
                    void handleCommand("model.toggle_suppression");
                  }}
                  selectedObjectId={selectedObjectId}
                />
              ) : null}
              {bottomDockTab === "commands" ? (
                <CommandCatalog
                  catalog={commandCatalog}
                  onRunCommand={(id) => void handleCommand(id)}
                  taskPanel={taskPanel}
                />
              ) : null}
              {bottomDockTab === "extensions" ? (
                <ExtensionCompatibilityPanel
                  commandCatalog={commandCatalog}
                  extensionCompatibility={extensionCompatibility}
                  onRunCommand={(commandId, commandArguments) =>
                    void handleCommand(commandId, commandArguments ?? {})
                  }
                />
              ) : null}
            </div>
          </section>
          ) : null}
        </section>
      </main>

      <footer className="freecad-statusbar">
        <span>Workbench: {document.workbench}</span>
        <span>Document: {document.display_name}</span>
        <span>{document.dirty ? "State: modified" : "State: saved"}</span>
        <span>Selection: {selectedObjectId ?? "none"}</span>
        <span>Worker: {boot.bridge_status.worker_mode}</span>
        <span>Jobs: {jobs?.jobs.length ?? 0}</span>
        <span>Layout: {shellSnapshot?.layout.layout_id ?? "shell-pending"}</span>
      </footer>
    </div>
  );
}
