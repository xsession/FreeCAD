import { FormEvent, PointerEvent as ReactPointerEvent, Suspense, lazy, useEffect, useRef, useState } from "react";
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
  updateShellSessionState,
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
  type ShellStatusBarItem as ProtocolShellStatusBarItem,
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
import { fetchStepDocumentIndex, fetchStepSceneBundle } from "./stepClient";
import type { StepDocumentIndex, StepSceneBundle } from "./stepTypes";

export { StepViewportScene } from "./StepViewportScene";

const LazyStepViewportScene = lazy(async () => {
  const module = await import("./StepViewportScene");
  return { default: module.StepViewportScene };
});

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

type DockFilterState = {
  label: string;
  query: string;
};

type ResizableShellPanelId = "combo_view" | "report_dock";
type ResizeAxis = "horizontal" | "vertical";

const PANEL_RESIZE_HANDLE_SIZE = 10;

function clampValue(value: number, minimum: number, maximum: number) {
  return Math.min(Math.max(value, minimum), maximum);
}

function clampShellPanelSizeHint(panelId: ResizableShellPanelId, sizeHint: number) {
  return panelId === "combo_view"
    ? clampValue(sizeHint, 0.22, 0.42)
    : clampValue(sizeHint, 0.18, 0.4);
}

function resolveShellPanelSizeHintFromPointer(
  panelId: ResizableShellPanelId,
  axis: ResizeAxis,
  pointerPosition: number,
  rect: DOMRect
) {
  const span = axis === "horizontal" ? rect.width : rect.height;
  if (span <= 0) {
    return null;
  }

  const rawSizeHint =
    axis === "horizontal" ? (pointerPosition - rect.left) / span : (rect.bottom - pointerPosition) / span;
  return clampShellPanelSizeHint(panelId, rawSizeHint);
}

function dockFilterStateFromParts(label?: string | null, query?: string | null): DockFilterState | null {
  if (!label || !query) {
    return null;
  }

  return { label, query };
}

function activeWorkspaceSessionForDocument(
  shellSnapshot: ShellSnapshot | null,
  document: DocumentRef | null
): WorkspaceSessionEntry | null {
  if (!shellSnapshot || !document) {
    return null;
  }

  return (
    shellSnapshot.workspace_sessions.find((session) => session.document_id === document.document_id) ??
    shellSnapshot.workspace_sessions.find(
      (session) => Boolean(document.file_path) && session.file_path === document.file_path
    ) ??
    null
  );
}

function sessionDockFilterSummary(session: WorkspaceSession) {
  if (session.report_dock_filter_label) {
    return `Report Scope: ${session.report_dock_filter_label}`;
  }

  if (session.diagnostics_dock_filter_label) {
    return `Diagnostics Scope: ${session.diagnostics_dock_filter_label}`;
  }

  return null;
}

function sessionScopeTarget(session: WorkspaceSession):
  | { tab: "report" | "diagnostics"; filterState: DockFilterState }
  | null {
  const reportFilter = dockFilterStateFromParts(
    session.report_dock_filter_label,
    session.report_dock_filter_query
  );
  if (reportFilter) {
    return { tab: "report", filterState: reportFilter };
  }

  const diagnosticsFilter = dockFilterStateFromParts(
    session.diagnostics_dock_filter_label,
    session.diagnostics_dock_filter_query
  );
  if (diagnosticsFilter) {
    return { tab: "diagnostics", filterState: diagnosticsFilter };
  }

  return null;
}

type ViewportAnchor = {
  x: number;
  y: number;
};

type StatusbarTone = "neutral" | "info" | "warning" | "error";

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

function titleCaseShellToken(value: string | null | undefined, fallback: string) {
  if (!value) {
    return fallback;
  }

  return value
    .split(/[_-]+/)
    .filter(Boolean)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
}

function isEditableEventTarget(target: EventTarget | null) {
  if (!(target instanceof HTMLElement)) {
    return false;
  }

  const tagName = target.tagName.toLowerCase();
  return target.isContentEditable || tagName === "input" || tagName === "textarea" || tagName === "select";
}

function selectionModeShortcutLabel(index: number) {
  return index >= 0 && index < 9 ? `${index + 1}` : null;
}

function normalizeStatusbarTone(tone: string | null | undefined): StatusbarTone {
  switch (tone) {
    case "info":
    case "warning":
    case "error":
      return tone;
    default:
      return "neutral";
  }
}

function statusbarToneClass(tone: StatusbarTone) {
  switch (tone) {
    case "info":
      return "freecad-statusbar-item-info";
    case "warning":
      return "freecad-statusbar-item-warning";
    case "error":
      return "freecad-statusbar-item-error";
    default:
      return "";
  }
}

function StatusbarItem({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: string;
  tone?: string | null;
}) {
  const normalizedTone = normalizeStatusbarTone(tone);

  return (
    <span className={`freecad-statusbar-item ${statusbarToneClass(normalizedTone)}`.trim()}>
      <span className="freecad-statusbar-label">{label}</span>
      <span className="freecad-statusbar-value">{value}</span>
    </span>
  );
}

type WorkspaceSession = {
  session_id: string;
  document_id: string;
  display_name: string;
  file_path: string;
  workbench: string;
  dirty: boolean;
  selected_object_id: string | null;
  selection_mode: string | null;
  combo_view_tab: string | null;
  bottom_dock_tab: BottomDockTab | null;
  combo_view_visible: boolean | null;
  report_dock_visible: boolean | null;
  combo_view_size_hint: number | null;
  report_dock_size_hint: number | null;
  report_dock_filter_label: string | null;
  report_dock_filter_query: string | null;
  diagnostics_dock_filter_label: string | null;
  diagnostics_dock_filter_query: string | null;
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

function filterObjectTree(nodes: ObjectNode[], query: string): ObjectNode[] {
  if (!query.trim()) {
    return nodes;
  }

  const normalizedQuery = query.trim().toLowerCase();

  return nodes.flatMap((node) => {
    const filteredChildren = filterObjectTree(node.children, query);
    const matchesNode = matchesPromptFilter(
      `${node.label} ${node.object_type} ${node.object_id}`,
      normalizedQuery
    );

    if (!matchesNode && filteredChildren.length === 0) {
      return [];
    }

    return [{
      ...node,
      children: filteredChildren
    }];
  });
}

export function ModelBrowserPane({
  objectTree,
  onHoverChange,
  onSelect,
  preselectedObjectId,
  selectedObjectId,
  selectionMode,
}: {
  objectTree: ObjectNode[];
  onHoverChange: (objectId: string | null) => void;
  onSelect: (objectId: string) => void;
  preselectedObjectId: string | null;
  selectedObjectId: string | null;
  selectionMode: string;
}) {
  const [filterQuery, setFilterQuery] = useState("");

  const filteredTree = filterObjectTree(objectTree, filterQuery);
  const flattenedFilteredTree = flattenObjectTree(filteredTree);
  const visibleSelectableCount = flattenedFilteredTree.filter((node) =>
    objectMatchesSelectionMode(node.object_type, selectionMode)
  ).length;

  return (
    <section className="dock-panel combo-pane">
      <div className="panel-header panel-header-dense">
        <h2>Model</h2>
        <span>{selectionMode} / {visibleSelectableCount} selectable</span>
      </div>
      <div className="prompt-pane-toolbar">
        <label className="prompt-pane-search">
          <span>Filter</span>
          <input
            className="prompt-pane-search-input"
            onChange={(event) => setFilterQuery(event.target.value)}
            placeholder="Search labels, ids, and object types..."
            value={filterQuery}
          />
        </label>
        <div className="prompt-pane-summary">
          <span>{filteredTree.length} roots</span>
          <strong>{flattenedFilteredTree.length} visible nodes</strong>
        </div>
      </div>
      <div className="tree-panel combo-pane-scroll">
        {filteredTree.map((node) => (
          <TreeNode
            key={node.object_id}
            node={node}
            onHoverChange={onHoverChange}
            onSelect={onSelect}
            preselectedObjectId={preselectedObjectId}
            selectedObjectId={selectedObjectId}
            selectionMode={selectionMode}
          />
        ))}
        {filteredTree.length === 0 ? (
          <div className="tree-panel-empty">No model nodes match this filter.</div>
        ) : null}
      </div>
    </section>
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
  onOpenPalette,
  onOpenModel,
  onOpenReport,
  onOpenTasks,
  onResetPreset,
  reportDockVisible,
  selectionState,
  selectedObjectId,
  stepAvailable,
  workbenchLabel
}: {
  activePreset: StepViewportPreset | null;
  cameraEye: number[] | undefined;
  cameraTarget: number[] | undefined;
  comboViewVisible: boolean;
  onChangeSelectionMode: (modeId: string) => void;
  onApplyPreset: (preset: StepViewportPreset) => void;
  onFitAll: () => void;
  onFocusSelection: () => void;
  onOpenPalette: () => void;
  onOpenModel: () => void;
  onOpenReport: () => void;
  onOpenTasks: () => void;
  onResetPreset: () => void;
  reportDockVisible: boolean;
  selectionState: SelectionStateResponse | null;
  selectedObjectId: string | null;
  stepAvailable: boolean;
  workbenchLabel: string;
}) {
  return (
    <>
      <div className="viewport-orientation-chip">
        <span>{stepAvailable ? "STEP HUD" : "Viewport HUD"}</span>
        <strong>{viewportOrientationLabel(cameraEye, cameraTarget)}</strong>
      </div>
      <div className="viewport-quickbar">
        <button className="viewport-quickbar-button viewport-quickbar-button-primary" onClick={onOpenPalette} type="button">
          <ShellIcon icon="list" title="Open command palette" />
          <span>Search</span>
          <strong>F</strong>
        </button>
        <div className="viewport-quickbar-chip">
          <span>Workbench</span>
          <strong>{workbenchLabel}</strong>
        </div>
        <div className="viewport-quickbar-chip viewport-quickbar-chip-muted">
          <span>Panels</span>
          <strong>{comboViewVisible || reportDockVisible ? "Live" : "Minimal"}</strong>
        </div>
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
            {selectionState.available_modes.map((mode, index) => {
              const active = mode.mode_id === selectionState.current_mode;
              const shortcutLabel = selectionModeShortcutLabel(index);

              return (
                <button
                  className={`viewport-selection-mode-chip ${active ? "viewport-selection-mode-chip-active" : ""}`}
                  disabled={!mode.enabled}
                  key={mode.mode_id}
                  onClick={() => onChangeSelectionMode(mode.mode_id)}
                  title={shortcutLabel ? `${mode.description} Shortcut: ${shortcutLabel}` : mode.description}
                  type="button"
                >
                  {shortcutLabel ? <span className="selection-mode-shortcut">{shortcutLabel}</span> : null}
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

function matchesPromptFilter(value: string, query: string) {
  if (!query.trim()) {
    return true;
  }

  return value.toLowerCase().includes(query.trim().toLowerCase());
}

function resolveViewportCommandContext(
  commandCatalog: CommandCatalogResponse | null,
  preselectionState: PreselectionStateResponse | null,
  selectedObjectId: string | null,
  taskPanel: TaskPanelResponse | null
) {
  if (!commandCatalog) {
    return {
      targetLabel: "",
      targetObjectId: undefined,
      targetStateLabel: "Workbench",
      visibleCommandStateKey: "",
      visibleCommands: [] as CommandDefinition[]
    };
  }

  const prioritizedCommandIds = [
    ...(preselectionState?.suggested_commands ?? []),
    ...(taskPanel?.suggested_commands ?? []),
    ...(selectedObjectId ? ["selection.focus"] : [])
  ];
  const commandById = new Map(commandCatalog.commands.map((command) => [command.command_id, command]));
  const visibleCommands = Array.from(new Set(prioritizedCommandIds))
    .map((commandId) => commandById.get(commandId))
    .filter((command): command is CommandDefinition => Boolean(command))
    .filter((command) => command.enabled)
    .slice(0, 6);

  return {
    targetLabel:
      preselectionState?.object_label ??
      preselectionState?.object_id ??
      selectedObjectId ??
      commandCatalog.workbench.display_name,
    targetObjectId: preselectionState?.object_id ?? selectedObjectId ?? undefined,
    targetStateLabel: preselectionState?.object_id
      ? "Hover"
      : selectedObjectId
        ? "Selection"
        : "Workbench",
    visibleCommandStateKey: visibleCommands
      .map((command) => `${command.command_id}:${command.arguments.length}`)
      .join("|"),
    visibleCommands
  };
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

export function ViewportCommandBar({
  commandCatalog,
  onOpenPalette,
  onRunCommand,
  preselectionState,
  selectedObjectId,
  taskPanel,
}: {
  commandCatalog: CommandCatalogResponse | null;
  onOpenPalette: () => void;
  onRunCommand: (
    commandId: string,
    commandArguments?: Record<string, string>,
    targetObjectId?: string
  ) => void;
  preselectionState: PreselectionStateResponse | null;
  selectedObjectId: string | null;
  taskPanel: TaskPanelResponse | null;
}) {
  const [commandDrafts, setCommandDrafts] = useState<Record<string, Record<string, string>>>({});
  const [expandedCommandId, setExpandedCommandId] = useState<string | null>(null);

  if (!commandCatalog) {
    return null;
  }

  const {
    targetLabel,
    targetObjectId,
    targetStateLabel,
    visibleCommandStateKey,
    visibleCommands
  } = resolveViewportCommandContext(commandCatalog, preselectionState, selectedObjectId, taskPanel);

  useEffect(() => {
    setCommandDrafts((current) => initializeCommandDrafts(current, visibleCommands));

    if (
      expandedCommandId &&
      !visibleCommands.some(
        (command) => command.command_id === expandedCommandId && command.arguments.length > 0
      )
    ) {
      setExpandedCommandId(null);
    }
  }, [expandedCommandId, visibleCommandStateKey]);

  if (visibleCommands.length === 0) {
    return null;
  }

  const expandedCommand =
    expandedCommandId
      ? visibleCommands.find((command) => command.command_id === expandedCommandId) ?? null
      : null;

  function updateDraftValue(commandId: string, argumentId: string, value: string) {
    setCommandDrafts((current) => ({
      ...current,
      [commandId]: {
        ...(current[commandId] ?? {}),
        [argumentId]: value,
      },
    }));
  }

  function currentDraftValue(commandId: string, argument: CommandArgumentDefinition) {
    return commandDrafts[commandId]?.[argument.argument_id] ?? argument.default_value ?? "";
  }

  function handleViewportCommand(command: CommandDefinition) {
    if (command.arguments.length > 0) {
      setExpandedCommandId((current) =>
        current === command.command_id ? null : command.command_id
      );
      return;
    }

    onRunCommand(
      command.command_id,
      undefined,
      command.requires_selection ? targetObjectId : undefined
    );
  }

  return (
    <div aria-label="Viewport tool shelf" className="viewport-command-bar" role="region">
      <div className="viewport-command-bar-header">
        <div className="viewport-command-bar-heading">
          <div className="viewport-command-bar-label">Tool Shelf</div>
          <div className="viewport-command-bar-context">
            <span>{targetStateLabel}</span>
            <strong>{targetLabel}</strong>
          </div>
        </div>
        <div className="viewport-command-bar-summary">
          <span>{visibleCommands.length} live tools</span>
          <strong>
            {expandedCommand
              ? expandedCommand.action_label ?? expandedCommand.label
              : commandCatalog.workbench.display_name}
          </strong>
        </div>
      </div>
      <div className="viewport-command-bar-actions">
        {visibleCommands.map((command) => (
          <button
            className={`viewport-command-bar-button ${
              expandedCommandId === command.command_id ? "viewport-command-bar-button-active" : ""
            }`}
            key={command.command_id}
            onClick={() => handleViewportCommand(command)}
            type="button"
          >
            <ShellIcon icon={command.icon} title={command.label} />
            <div className="viewport-command-bar-button-copy">
              <span>{command.action_label ?? command.label}</span>
              <small>{command.group}</small>
            </div>
            {command.arguments.length > 0 ? <strong>Edit</strong> : null}
            {!command.arguments.length && command.shortcut ? <strong>{command.shortcut}</strong> : null}
          </button>
        ))}
        <button
          className="viewport-command-bar-button viewport-command-bar-button-tail viewport-command-bar-button-utility"
          onClick={onOpenPalette}
          type="button"
        >
          <ShellIcon icon="list" title="More commands" />
          <div className="viewport-command-bar-button-copy">
            <span>More</span>
            <small>palette</small>
          </div>
          <strong>F</strong>
        </button>
      </div>
      {expandedCommand && expandedCommand.arguments.length > 0 ? (
        <SuggestedCommandEditor
          className="task-editor viewport-command-editor"
          command={expandedCommand}
          currentDraftValue={(argument) => currentDraftValue(expandedCommand.command_id, argument)}
          headerLabel={expandedCommand.action_label ?? expandedCommand.label}
          idPrefix="viewport-command-bar"
          onSubmitCommand={(commandArguments) => {
            onRunCommand(
              expandedCommand.command_id,
              commandArguments,
              expandedCommand.requires_selection ? targetObjectId : undefined
            );
            setExpandedCommandId(null);
          }}
          onUpdateDraftValue={(argumentId, value) =>
            updateDraftValue(expandedCommand.command_id, argumentId, value)
          }
          submitLabel={expandedCommand.action_label ?? expandedCommand.label}
        />
      ) : null}
    </div>
  );
}

export function ViewportCommandLens({
  anchor,
  commandCatalog,
  onClose,
  onOpenPalette,
  onRunCommand,
  open,
  preselectionState,
  selectedObjectId,
  taskPanel,
}: {
  anchor: ViewportAnchor | null;
  commandCatalog: CommandCatalogResponse | null;
  onClose: () => void;
  onOpenPalette: () => void;
  onRunCommand: (
    commandId: string,
    commandArguments?: Record<string, string>,
    targetObjectId?: string
  ) => void;
  open: boolean;
  preselectionState: PreselectionStateResponse | null;
  selectedObjectId: string | null;
  taskPanel: TaskPanelResponse | null;
}) {
  const [commandDrafts, setCommandDrafts] = useState<Record<string, Record<string, string>>>({});
  const [expandedCommandId, setExpandedCommandId] = useState<string | null>(null);

  const {
    targetLabel,
    targetObjectId,
    targetStateLabel,
    visibleCommandStateKey,
    visibleCommands
  } = resolveViewportCommandContext(commandCatalog, preselectionState, selectedObjectId, taskPanel);

  useEffect(() => {
    if (!open) {
      setExpandedCommandId(null);
      return;
    }

    setCommandDrafts((current) => initializeCommandDrafts(current, visibleCommands));

    if (
      expandedCommandId &&
      !visibleCommands.some(
        (command) => command.command_id === expandedCommandId && command.arguments.length > 0
      )
    ) {
      setExpandedCommandId(null);
    }
  }, [expandedCommandId, open, visibleCommandStateKey]);

  if (!open || !commandCatalog || visibleCommands.length === 0) {
    return null;
  }

  const expandedCommand =
    expandedCommandId
      ? visibleCommands.find((command) => command.command_id === expandedCommandId) ?? null
      : null;
  const lensStyle = anchor
    ? {
        left: `${Math.max(96, anchor.x)}px`,
        top: `${Math.max(84, anchor.y)}px`
      }
    : undefined;

  function updateDraftValue(commandId: string, argumentId: string, value: string) {
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

  function handleLensCommand(command: CommandDefinition) {
    if (command.arguments.length > 0) {
      setExpandedCommandId((current) => (current === command.command_id ? null : command.command_id));
      return;
    }

    onRunCommand(command.command_id, undefined, command.requires_selection ? targetObjectId : undefined);
    onClose();
  }

  return (
    <div
      aria-label="Viewport command lens"
      className={`viewport-command-lens ${anchor ? "" : "viewport-command-lens-centered"}`.trim()}
      role="region"
      style={lensStyle}
    >
      <div className="viewport-command-lens-header">
        <div>
          <span className="viewport-command-lens-label">Command Lens</span>
          <strong>{targetLabel}</strong>
        </div>
        <div className="viewport-command-lens-meta">
          <span>{targetStateLabel}</span>
          <span>Space / Right Click</span>
        </div>
      </div>
      <div className="viewport-command-lens-grid">
        {visibleCommands.map((command) => (
          <button
            className={`viewport-command-lens-button ${
              expandedCommandId === command.command_id ? "viewport-command-lens-button-active" : ""
            }`}
            key={command.command_id}
            onClick={() => handleLensCommand(command)}
            type="button"
          >
            <ShellIcon icon={command.icon} title={command.label} />
            <div className="viewport-command-lens-copy">
              <strong>{command.action_label ?? command.label}</strong>
              <span>{command.group}</span>
            </div>
            {command.arguments.length > 0 ? <small>Edit</small> : null}
          </button>
        ))}
      </div>
      <div className="viewport-command-lens-actions">
        <button className="action-button" onClick={onClose} type="button">
          Close
        </button>
        <button
          className="action-button action-button-primary"
          onClick={() => {
            onClose();
            onOpenPalette();
          }}
          type="button"
        >
          Command Palette
        </button>
      </div>
      {expandedCommand && expandedCommand.arguments.length > 0 ? (
        <SuggestedCommandEditor
          className="task-editor viewport-command-lens-editor"
          command={expandedCommand}
          currentDraftValue={(argument) => currentDraftValue(expandedCommand.command_id, argument)}
          headerLabel={expandedCommand.action_label ?? expandedCommand.label}
          idPrefix="viewport-command-lens"
          onSubmitCommand={(commandArguments) => {
            onRunCommand(
              expandedCommand.command_id,
              commandArguments,
              expandedCommand.requires_selection ? targetObjectId : undefined
            );
            setExpandedCommandId(null);
            onClose();
          }}
          onUpdateDraftValue={(argumentId, value) =>
            updateDraftValue(expandedCommand.command_id, argumentId, value)
          }
          submitLabel={expandedCommand.action_label ?? expandedCommand.label}
        />
      ) : null}
    </div>
  );
}

export function ReportActivityFeed({
  commandCatalog,
  filterState,
  onClearFilter,
  onFocusActivityObject,
  onRunCommand,
  onSelectActivityObject,
  reportEvents
}: {
  commandCatalog?: CommandCatalogResponse | null;
  filterState?: DockFilterState | null;
  onClearFilter?: () => void;
  onFocusActivityObject?: (objectId: string) => void;
  onRunCommand?: (commandId: string, targetObjectId?: string) => void;
  onSelectActivityObject?: (objectId: string) => void;
  reportEvents: ActivityEvent[];
}) {
  const scopedEvents = filterState?.query
    ? reportEvents.filter((activity) =>
        matchesPromptFilter(
          `${activity.topic} ${activity.message} ${activity.object_id ?? ""}`,
          filterState.query
        )
      )
    : reportEvents;
  const prioritizedEvents = prioritizeReportEvents(summarizeReportEvents(scopedEvents));

  return (
    <section className="dock-panel">
      <div className="panel-header">
        <h2>Backend Activity</h2>
        <span>{scopedEvents.length} live backend events</span>
      </div>
      {filterState ? (
        <div className="prompt-pane-toolbar dock-filter-toolbar">
          <div className="prompt-pane-summary">
            <span>Scoped View</span>
            <strong>{filterState.label}</strong>
          </div>
          <button className="dock-tab-button dock-tab-button-utility" onClick={onClearFilter} type="button">
            Clear Filter
          </button>
        </div>
      ) : null}
      {scopedEvents.length > 0 ? (
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
          {filterState
            ? "No backend activity matched the current dock filter."
            : "Structured STEP inspection is shown above. No additional backend activity is pending for the current report view."}
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
  activeFilePath,
  onActivate,
  onActivateScope,
  onClearInactive,
  onDismiss
}: {
  sessions: WorkspaceSession[];
  activeDocumentId: string | null;
  activeFilePath: string | null | undefined;
  onActivate: (session: WorkspaceSession) => void;
  onActivateScope: (session: WorkspaceSession) => void;
  onClearInactive: () => void;
  onDismiss: (session: WorkspaceSession) => void;
}) {
  if (sessions.length === 0) {
    return null;
  }

  return (
    <section className="session-tabs-shell">
      <div className="session-tabs-header">
        <span className="dock-strip-label">Workspace Sessions</span>
        {sessions.length > 1 ? (
          <button className="action-button action-button-subtle" onClick={onClearInactive} type="button">
            Clear Other Sessions
          </button>
        ) : null}
      </div>
      <div className="session-tabs">
        {sessions.map((session) => {
          const active =
            session.document_id === activeDocumentId ||
            (activeFilePath !== null && activeFilePath !== undefined && session.file_path === activeFilePath);
          const sessionModeLabel = titleCaseShellToken(session.selection_mode, "Object");
          const sessionStateLabel = session.dirty ? "Unsaved" : "Saved";
          const sessionFilterSummary = sessionDockFilterSummary(session);
          const scopeTarget = sessionScopeTarget(session);
          const sessionScopeButtonLabel = scopeTarget?.filterState.label ?? sessionFilterSummary;

          return (
            <div className={`session-tab-card ${active ? "session-tab-card-active" : ""}`} key={session.session_id}>
              <button
                className={`session-tab ${active ? "session-tab-active" : ""}`}
                onClick={() => onActivate(session)}
                title={`${session.file_path} • ${session.workbench} • ${sessionModeLabel} • ${sessionStateLabel}${session.selected_object_id ? ` • ${session.selected_object_id}` : ""}${sessionFilterSummary ? ` • ${sessionFilterSummary}` : ""}`}
                type="button"
              >
                <div className="session-tab-main">
                  <strong>{session.display_name}</strong>
                  <span>{session.file_path}</span>
                </div>
                <div className="session-tab-meta">
                  <span>{session.workbench}</span>
                  <span>{sessionModeLabel}</span>
                  <span>{sessionStateLabel}</span>
                </div>
              </button>
              {sessionFilterSummary && scopeTarget ? (
                <button
                  aria-label={sessionFilterSummary}
                  className="session-tab-scope session-tab-scope-button"
                  onClick={() => onActivateScope(session)}
                  title={`Open ${sessionFilterSummary}`}
                  type="button"
                >
                  {sessionScopeButtonLabel}
                </button>
              ) : null}
              {!active ? (
                <button
                  className="session-tab-close"
                  onClick={() => onDismiss(session)}
                  title="Dismiss session"
                  type="button"
                >
                  x
                </button>
              ) : null}
            </div>
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
        {selectionState.available_modes.map((mode, index) => {
          const active = mode.mode_id === selectionState.current_mode;
          const shortcutLabel = selectionModeShortcutLabel(index);

          return (
            <button
              className={`selection-mode-chip ${active ? "selection-mode-chip-active" : ""}`}
              disabled={!mode.enabled}
              key={mode.mode_id}
              onClick={() => onChangeMode(mode.mode_id)}
              title={shortcutLabel ? `${mode.description} Shortcut: ${shortcutLabel}` : mode.description}
              type="button"
            >
              <div className="selection-mode-chip-title">
                {shortcutLabel ? <span className="selection-mode-shortcut">{shortcutLabel}</span> : null}
                <strong>{mode.label}</strong>
              </div>
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
            <div className="command-palette-shortcut-note">Quick open: F or Ctrl+K</div>
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

export function TaskPanel({
  taskPanel,
  commandCatalog,
  onRunCommand
}: {
  taskPanel: TaskPanelResponse | null;
  commandCatalog: CommandCatalogResponse | null;
  onRunCommand: (commandId: string, commandArguments?: Record<string, string>) => void;
}) {
  const [commandDrafts, setCommandDrafts] = useState<Record<string, Record<string, string>>>({});
  const [filterQuery, setFilterQuery] = useState("");

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
  const filteredSections = taskPanel.sections
    .map((section) => {
      if (!filterQuery.trim()) {
        return section;
      }

      const rows = section.rows.filter((row) =>
        matchesPromptFilter(`${section.title} ${row.label} ${row.value}`, filterQuery)
      );

      return rows.length > 0 || matchesPromptFilter(section.title, filterQuery)
        ? { ...section, rows }
        : null;
    })
    .filter((section): section is TaskPanelResponse["sections"][number] => Boolean(section));
  const filteredSuggestedCommands = suggestedCommands.filter((command) =>
    matchesPromptFilter(
      `${command.label} ${command.action_label ?? ""} ${command.description} ${command.group}`,
      filterQuery
    )
  );
  const visibleRowCount = filteredSections.reduce((count, section) => count + section.rows.length, 0);

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
      <div className="prompt-pane-toolbar">
        <label className="prompt-pane-search">
          <span>Filter</span>
          <input
            className="prompt-pane-search-input"
            onChange={(event) => setFilterQuery(event.target.value)}
            placeholder="Search tasks, rows, and commands..."
            value={filterQuery}
          />
        </label>
      </div>
      <div className="task-panel-meta-strip">
        <div className="task-panel-meta-chip">
          <span>Sections</span>
          <strong>{filteredSections.length}</strong>
        </div>
        <div className="task-panel-meta-chip">
          <span>Rows</span>
          <strong>{visibleRowCount}</strong>
        </div>
        <div className="task-panel-meta-chip">
          <span>Actions</span>
          <strong>{filteredSuggestedCommands.length}</strong>
        </div>
      </div>
      <div className="task-sections">
        {filteredSections.map((section) => (
          <div className="task-section" key={section.section_id}>
            <div className="task-section-header">
              <h3>{section.title}</h3>
              <span>{section.rows.length} rows</span>
            </div>
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
        {filteredSections.length === 0 ? (
          <div className="task-section task-section-empty">No task rows match this filter.</div>
        ) : null}
      </div>
      {filteredSuggestedCommands.length > 0 ? (
        <div className="task-editor-grid">
          {filteredSuggestedCommands.map((command) =>
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

export function PropertyInspectorPane({
  objectId,
  properties,
}: {
  objectId: string | null | undefined;
  properties: PropertyResponse | null;
}) {
  const [filterQuery, setFilterQuery] = useState("");

  const filteredGroups = (properties?.groups ?? [])
    .map((group) => {
      if (!filterQuery.trim()) {
        return group;
      }

      const visibleProperties = group.properties.filter((property) =>
        matchesPromptFilter(
          `${group.title} ${property.display_name} ${property.property_type} ${property.value_preview}`,
          filterQuery
        )
      );

      return visibleProperties.length > 0 || matchesPromptFilter(group.title, filterQuery)
        ? { ...group, properties: visibleProperties }
        : null;
    })
    .filter((group): group is PropertyResponse["groups"][number] => Boolean(group));
  const visiblePropertyCount = filteredGroups.reduce(
    (count, group) => count + group.properties.length,
    0
  );

  return (
    <section className="dock-panel combo-pane combo-pane-properties">
      <div className="panel-header panel-header-dense">
        <h2>Data</h2>
        <span>{objectId ?? "No active selection"}</span>
      </div>
      <div className="prompt-pane-toolbar">
        <label className="prompt-pane-search">
          <span>Filter</span>
          <input
            className="prompt-pane-search-input"
            onChange={(event) => setFilterQuery(event.target.value)}
            placeholder="Search properties, values, and groups..."
            value={filterQuery}
          />
        </label>
        <div className="prompt-pane-summary">
          <span>{filteredGroups.length} groups</span>
          <strong>{visiblePropertyCount} visible properties</strong>
        </div>
      </div>
      <div className="property-groups combo-pane-scroll">
        {filteredGroups.map((group) => (
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
        {filteredGroups.length === 0 ? (
          <div className="property-group property-group-empty">No properties match this filter.</div>
        ) : null}
      </div>
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

export function DiagnosticsPanel({
  diagnostics,
  commandStatus,
  filterState,
  onClearFilter
}: {
  diagnostics: DiagnosticsResponse | null;
  commandStatus: CommandExecutionResponse | null;
  filterState?: DockFilterState | null;
  onClearFilter?: () => void;
}) {
  if (!diagnostics) {
    return null;
  }

  const visibleSignals = filterState?.query
    ? diagnostics.recent_signals.filter((signal) =>
        matchesPromptFilter(`${signal.title} ${signal.detail}`, filterState.query)
      )
    : diagnostics.recent_signals;

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
      {filterState ? (
        <div className="prompt-pane-toolbar dock-filter-toolbar">
          <div className="prompt-pane-summary">
            <span>Scoped View</span>
            <strong>{filterState.label}</strong>
          </div>
          <button className="dock-tab-button dock-tab-button-utility" onClick={onClearFilter} type="button">
            Clear Filter
          </button>
        </div>
      ) : null}
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
            {visibleSignals.map((signal, index) => (
              <div className="diagnostic-event" key={`${signal.title}-${index}`}>
                <span className={`level level-${signal.level}`}>{signal.level}</span>
                <div>
                  <strong>{signal.title}</strong>
                  <p>{signal.detail}</p>
                </div>
              </div>
            ))}
            {visibleSignals.length === 0 ? (
              <p className="selection-empty">
                {filterState
                  ? "No diagnostics signals matched the current dock filter."
                  : "No backend events have been published yet."}
              </p>
            ) : null}
          </div>
        </div>
      </div>
    </section>
  );
}

function JobActions({
  className,
  commandCatalog,
  job,
  onFocusJobObject,
  onRunJobCommand,
  onSelectJobObject
}: {
  className?: string;
  commandCatalog: CommandCatalogResponse | null;
  job: JobStatusResponse["jobs"][number];
  onFocusJobObject?: (objectId: string) => void;
  onRunJobCommand?: (commandId: string, targetObjectId?: string) => void;
  onSelectJobObject?: (objectId: string) => void;
}) {
  const command = inspectionCommand(commandCatalog, job.command_id);
  const commandTargetObjectId = command?.requires_selection ? job.object_id : undefined;
  const canRunCommand = Boolean(command && (!command.requires_selection || commandTargetObjectId));

  if (!canRunCommand && !job.object_id) {
    return null;
  }

  return (
    <div className={className ?? "activity-actions"}>
      {canRunCommand ? (
        <InspectionActionButton
          command={command}
          label={command?.action_label ?? command?.label}
          onClick={() => onRunJobCommand?.(job.command_id, commandTargetObjectId)}
        />
      ) : null}
      {job.object_id ? (
        <>
          <button className="action-button" onClick={() => onSelectJobObject?.(job.object_id!)} type="button">
            <ShellIcon icon="part" title="Select job object" />
            <span>Select</span>
          </button>
          <button className="action-button" onClick={() => onFocusJobObject?.(job.object_id!)} type="button">
            <ShellIcon icon="focus" title="Focus job object" />
            <span>Focus</span>
          </button>
        </>
      ) : null}
    </div>
  );
}

function relatedJobEvents(job: JobStatusResponse["jobs"][number], reportEvents: ActivityEvent[]) {
  const matchingEvents = reportEvents.filter((event) => {
    if (job.object_id && event.object_id === job.object_id) {
      return true;
    }

    return !job.object_id && event.topic === "job_update";
  });

  return prioritizeReportEvents(summarizeReportEvents(matchingEvents)).slice(0, 3);
}

function jobDockFilterState(job: JobStatusResponse["jobs"][number]): DockFilterState {
  if (job.object_id) {
    return {
      label: `${job.title} / ${job.object_id}`,
      query: job.object_id
    };
  }

  return {
    label: `${job.title} / ${job.command_id}`,
    query: job.title || job.command_id
  };
}

export function JobsPanel({
  commandCatalog,
  jobs,
  onFocusJobObject,
  onOpenJobDiagnostics,
  onOpenJobReport,
  onRunJobCommand,
  reportEvents,
  onSelectJobObject
}: {
  commandCatalog: CommandCatalogResponse | null;
  jobs: JobStatusResponse | null;
  onFocusJobObject?: (objectId: string) => void;
  onOpenJobDiagnostics?: (filterState: DockFilterState) => void;
  onOpenJobReport?: (filterState: DockFilterState) => void;
  onRunJobCommand?: (commandId: string, targetObjectId?: string) => void;
  reportEvents?: ActivityEvent[];
  onSelectJobObject?: (objectId: string) => void;
}) {
  const [expandedJobId, setExpandedJobId] = useState<string | null>(null);

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
            (() => {
              const isExpanded = expandedJobId === job.job_id;
              const jobEvents = relatedJobEvents(job, reportEvents ?? []);
              const dockFilter = jobDockFilterState(job);

              return (
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
                  <div className="job-card-toolbar">
                    <JobActions
                      className="activity-actions job-card-actions"
                      commandCatalog={commandCatalog}
                      job={job}
                      onFocusJobObject={onFocusJobObject}
                      onRunJobCommand={onRunJobCommand}
                      onSelectJobObject={onSelectJobObject}
                    />
                    <button
                      aria-expanded={isExpanded}
                      className="dock-tab-button dock-tab-button-utility job-detail-toggle"
                      onClick={() => setExpandedJobId((current) => (current === job.job_id ? null : job.job_id))}
                      type="button"
                    >
                      {isExpanded ? "Hide Details" : "Details"}
                    </button>
                  </div>
                  {isExpanded ? (
                    <div className="job-detail-panel">
                      <section className="job-detail-section">
                        <div className="panel-header panel-header-dense">
                          <h3>Stage Diagnostics</h3>
                          <span>{job.stages.length} tracked</span>
                        </div>
                        {job.stages.length > 0 ? (
                          <div className="job-stage-detail-list">
                            {job.stages.map((stage) => (
                              <div className="job-stage-detail-row" key={`${job.job_id}-detail-${stage.stage_id}`}>
                                <strong>{stage.label}</strong>
                                <span>{stage.state}</span>
                                <span>{stage.progress_percent}%</span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="selection-empty">This job did not publish stage diagnostics.</p>
                        )}
                      </section>
                      <section className="job-detail-section">
                        <div className="panel-header panel-header-dense">
                          <h3>Recent Backend Activity</h3>
                          <span>{jobEvents.length} excerpts</span>
                        </div>
                        <div className="job-detail-links">
                          <button
                            className="dock-tab-button dock-tab-button-utility"
                            onClick={() => onOpenJobReport?.(dockFilter)}
                            type="button"
                          >
                            Open Report
                          </button>
                          <button
                            className="dock-tab-button dock-tab-button-utility"
                            onClick={() => onOpenJobDiagnostics?.(dockFilter)}
                            type="button"
                          >
                            Open Diagnostics
                          </button>
                        </div>
                        {jobEvents.length > 0 ? (
                          <div className="job-log-list">
                            {jobEvents.map((activity, index) => (
                              <div className="job-log-entry" key={`${job.job_id}-activity-${activity.topic}-${index}`}>
                                <span className={`level level-${activity.level}`}>{activity.level}</span>
                                <div>
                                  <div className="job-log-topic">
                                    {activity.topic}
                                    {activity.object_id ? ` / ${activity.object_id}` : ""}
                                  </div>
                                  <div className="job-log-message">{activity.message}</div>
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="selection-empty">No related backend activity has been captured for this job yet.</p>
                        )}
                      </section>
                    </div>
                  ) : null}
                  <div className="job-meta">
                    <span>{job.command_id}</span>
                    <span>{job.object_id ?? "global"}</span>
                  </div>
                </div>
              );
            })()
          ))
        ) : (
          <p className="selection-empty">No backend jobs have been recorded yet.</p>
        )}
      </div>
    </section>
  );
}

export function BottomDockPinnedRail({
  commandCatalog,
  jobs,
  notices,
  onFocusJobObject,
  onFocusNoticeObject,
  onOpenJobs,
  onOpenReport,
  onRunJobCommand,
  onRunNoticeCommand,
  onSelectJobObject,
  onSelectNoticeObject,
}: {
  commandCatalog: CommandCatalogResponse | null;
  jobs: JobStatusResponse | null;
  notices: ShellNotice[];
  onFocusJobObject?: (objectId: string) => void;
  onFocusNoticeObject?: (objectId: string) => void;
  onOpenJobs: () => void;
  onOpenReport: () => void;
  onRunJobCommand?: (commandId: string, targetObjectId?: string) => void;
  onRunNoticeCommand?: (commandId: string, targetObjectId?: string) => void;
  onSelectJobObject?: (objectId: string) => void;
  onSelectNoticeObject?: (objectId: string) => void;
}) {
  const recentJobs = jobs?.jobs.slice(0, 2) ?? [];
  const visibleNotices = notices.slice(0, 2);

  if (visibleNotices.length === 0 && recentJobs.length === 0) {
    return null;
  }

  return (
    <aside className="bottom-dock-pinned-rail">
      <section className="bottom-dock-pinned-card">
        <div className="panel-header panel-header-dense">
          <h2>Pinned Notices</h2>
          <button className="dock-tab-button dock-tab-button-utility" onClick={onOpenReport} type="button">
            Open Report
          </button>
        </div>
        {visibleNotices.length > 0 ? (
          <div className="bottom-dock-pinned-list">
            {visibleNotices.map((notice) => (
              <div className="bottom-dock-pinned-item" key={notice.id}>
                <span className={`level level-${notice.level}`}>{notice.level}</span>
                <div>
                  <strong>{notice.title}</strong>
                  <p>{notice.detail}</p>
                  <ActivityObjectActions
                    activity={{ object_id: notice.objectId ?? null, topic: notice.title.replaceAll(" ", "_") }}
                    commandActionOverride={notice.commandAction}
                    commandCatalog={commandCatalog}
                    onFocusActivityObject={onFocusNoticeObject}
                    onRunCommand={onRunNoticeCommand}
                    onSelectActivityObject={onSelectNoticeObject}
                  />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="selection-empty">No live notices are pinned right now.</p>
        )}
      </section>
      <section className="bottom-dock-pinned-card">
        <div className="panel-header panel-header-dense">
          <h2>Pinned Jobs</h2>
          <button className="dock-tab-button dock-tab-button-utility" onClick={onOpenJobs} type="button">
            Open Jobs
          </button>
        </div>
        {recentJobs.length > 0 ? (
          <div className="bottom-dock-pinned-list">
            {recentJobs.map((job) => (
              <div className="bottom-dock-pinned-item" key={job.job_id}>
                <span className={`job-state job-state-${job.state}`}>{job.state}</span>
                <div>
                  <strong>{job.title}</strong>
                  <p>{job.detail}</p>
                  <JobActions
                    className="activity-actions bottom-dock-pinned-actions"
                    commandCatalog={commandCatalog}
                    job={job}
                    onFocusJobObject={onFocusJobObject}
                    onRunJobCommand={onRunJobCommand}
                    onSelectJobObject={onSelectJobObject}
                  />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="selection-empty">No jobs are currently pinned.</p>
        )}
      </section>
    </aside>
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
  const workspaceRef = useRef<HTMLElement | null>(null);
  const mainColumnRef = useRef<HTMLElement | null>(null);
  const [boot, setBoot] = useState<BootPayload | null>(null);
  const [document, setDocument] = useState<DocumentRef | null>(null);
  const [reportDockFilter, setReportDockFilter] = useState<DockFilterState | null>(null);
  const [diagnosticsDockFilter, setDiagnosticsDockFilter] = useState<DockFilterState | null>(null);
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
  const [viewportCommandLensOpen, setViewportCommandLensOpen] = useState(false);
  const [viewportPointerAnchor, setViewportPointerAnchor] = useState<ViewportAnchor | null>(null);
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeResizePanelId, setActiveResizePanelId] = useState<ResizableShellPanelId | null>(null);
  const [comboViewDraftSizeHint, setComboViewDraftSizeHint] = useState<number | null>(null);
  const [reportDockDraftSizeHint, setReportDockDraftSizeHint] = useState<number | null>(null);

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
      if (isEditableEventTarget(event.target)) {
        if (event.key === "Escape") {
          setPaletteOpen(false);
          setViewportCommandLensOpen(false);
        }
        return;
      }

      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setViewportCommandLensOpen(false);
        setPaletteOpen(true);
        return;
      }

      if (!event.ctrlKey && !event.metaKey && !event.altKey && event.key.toLowerCase() === "f") {
        event.preventDefault();
        setViewportCommandLensOpen(false);
        setPaletteOpen(true);
        return;
      }

      if (!paletteOpen && !event.ctrlKey && !event.metaKey && !event.altKey && event.code === "Space") {
        event.preventDefault();
        setViewportCommandLensOpen((current) => !current);
        return;
      }

      if (!paletteOpen && !event.ctrlKey && !event.metaKey && !event.altKey) {
        const shortcutMatch = event.code.match(/^(Digit|Numpad)([1-9])$/);
        if (shortcutMatch && selectionState) {
          const shortcutIndex = Number(shortcutMatch[2]) - 1;
          const targetMode = selectionState.available_modes[shortcutIndex];
          if (targetMode?.enabled && targetMode.mode_id !== selectionState.current_mode) {
            event.preventDefault();
            void handleSelectionModeChange(targetMode.mode_id);
            return;
          }
        }
      }

      if (event.key === "Escape") {
        setPaletteOpen(false);
        setViewportCommandLensOpen(false);
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [paletteOpen, selectionState]);

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

  useEffect(() => {
    const activeSession = activeWorkspaceSessionForDocument(shellSnapshot, document);
    setReportDockFilter(
      dockFilterStateFromParts(
        activeSession?.report_dock_filter_label,
        activeSession?.report_dock_filter_query
      )
    );
    setDiagnosticsDockFilter(
      dockFilterStateFromParts(
        activeSession?.diagnostics_dock_filter_label,
        activeSession?.diagnostics_dock_filter_query
      )
    );
  }, [document, shellSnapshot]);

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
      setViewportCommandLensOpen(false);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Failed to run command");
    }
  }

  function setViewportAnchorFromClientPosition(element: HTMLDivElement, clientX: number, clientY: number) {
    const rect = element.getBoundingClientRect();
    setViewportPointerAnchor({
      x: clientX - rect.left,
      y: clientY - rect.top
    });
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

  async function openDocumentPath(filePath: string): Promise<DocumentRef | null> {
    if (!boot && !document) {
      return null;
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
      return nextDocument;
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Failed to open document");
      return null;
    }
  }

  async function handleRecentDocumentOpen(filePath: string) {
    const activeFilePath = document?.file_path ?? null;
    if (activeFilePath === filePath) {
      setOpenPath(filePath);
      return;
    }

    await openDocumentPath(filePath);
  }

  async function handleSessionActivate(
    session: WorkspaceSession,
    preferredBottomDockTab?: "report" | "diagnostics"
  ) {
    const activeFilePath = document?.file_path ?? null;
    let activeDocument = document;
    const sameActiveDocument = activeFilePath === session.file_path;

    if (!sameActiveDocument) {
      const nextDocument = await openDocumentPath(session.file_path);
      if (!nextDocument) {
        return;
      }
      activeDocument = nextDocument;
    } else {
      setOpenPath(session.file_path);
    }

    if (!activeDocument) {
      return;
    }

    try {
      let nextDocument = activeDocument;
      const targetWorkbenchId = session.workbench.toLowerCase();
      if (targetWorkbenchId !== activeDocument.workbench.toLowerCase()) {
        nextDocument = await activateWorkbench(activeDocument.document_id, targetWorkbenchId);
      }

      const targetSelectionMode = session.selection_mode;
      if (
        targetSelectionMode &&
        (!sameActiveDocument || targetSelectionMode !== (selectionState?.current_mode ?? "object"))
      ) {
        await setSelectionMode(nextDocument.document_id, targetSelectionMode);
      }

      if (session.combo_view_tab || session.combo_view_visible !== null) {
        await updateShellPanelState(nextDocument.document_id, "combo_view", {
          active_tab: session.combo_view_tab ?? undefined,
          visible: session.combo_view_visible ?? undefined,
          size_hint: session.combo_view_size_hint ?? undefined
        });
      }

      if (session.bottom_dock_tab || session.report_dock_visible !== null || preferredBottomDockTab) {
        await updateShellPanelState(nextDocument.document_id, "report_dock", {
          active_tab: preferredBottomDockTab ?? session.bottom_dock_tab ?? undefined,
          visible: session.report_dock_visible ?? undefined,
          size_hint: session.report_dock_size_hint ?? undefined
        });
      }

      setReportDockFilter(
        dockFilterStateFromParts(session.report_dock_filter_label, session.report_dock_filter_query)
      );
      setDiagnosticsDockFilter(
        dockFilterStateFromParts(
          session.diagnostics_dock_filter_label,
          session.diagnostics_dock_filter_query
        )
      );

      const restoredSelectionId = sameActiveDocument
        ? session.selected_object_id ?? selectionState?.selected_object_id ?? null
        : session.selected_object_id ?? null;
      if (restoredSelectionId) {
        const restoredSelection = await setSelection(nextDocument.document_id, restoredSelectionId);
        await refreshDocumentSlices(nextDocument.document_id, restoredSelection.selected_object_id, nextDocument);
      } else {
        await refreshDocumentSlices(nextDocument.document_id, undefined, nextDocument);
      }

      setOpenPath(session.file_path);
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Failed to restore workspace session");
    }
  }

  async function handleClearRecentDocuments() {
    if (!document) {
      return;
    }

    try {
      const nextShellSnapshot = await updateShellSessionState(document.document_id, {
        clear_recent_documents: true
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
      setError(reason instanceof Error ? reason.message : "Failed to clear recent documents");
    }
  }

  async function handleDismissSession(session: WorkspaceSession) {
    if (!document) {
      return;
    }

    try {
      const nextShellSnapshot = await updateShellSessionState(document.document_id, {
        remove_workspace_session_id: session.session_id
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
      setError(reason instanceof Error ? reason.message : "Failed to dismiss workspace session");
    }
  }

  async function handleClearInactiveSessions() {
    if (!document) {
      return;
    }

    try {
      const nextShellSnapshot = await updateShellSessionState(document.document_id, {
        clear_inactive_workspace_sessions: true
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
      setError(reason instanceof Error ? reason.message : "Failed to clear inactive sessions");
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

  async function handlePersistDockFilters(mutation: {
    report_dock_filter_label?: string;
    report_dock_filter_query?: string;
    diagnostics_dock_filter_label?: string;
    diagnostics_dock_filter_query?: string;
    clear_report_dock_filter?: boolean;
    clear_diagnostics_dock_filter?: boolean;
  }) {
    if (!document) {
      return;
    }

    try {
      const nextShellSnapshot = await updateShellSessionState(document.document_id, mutation);
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
      setError(reason instanceof Error ? reason.message : "Failed to persist dock filter state");
    }
  }

  async function handleOpenFilteredBottomDockTab(tab: "report" | "diagnostics", filterState: DockFilterState) {
    if (tab === "report") {
      setReportDockFilter(filterState);
      await handlePersistDockFilters({
        report_dock_filter_label: filterState.label,
        report_dock_filter_query: filterState.query
      });
    } else {
      setDiagnosticsDockFilter(filterState);
      await handlePersistDockFilters({
        diagnostics_dock_filter_label: filterState.label,
        diagnostics_dock_filter_query: filterState.query
      });
    }

    await handlePanelTabChange("report_dock", tab);
  }

  async function handleSessionScopeActivate(session: WorkspaceSession) {
    const scopeTarget = sessionScopeTarget(session);

    if (!scopeTarget) {
      await handleSessionActivate(session);
      return;
    }

    const activeFilePath = document?.file_path ?? null;
    const sameActiveDocument = activeFilePath === session.file_path;

    if (sameActiveDocument) {
      await handleOpenFilteredBottomDockTab(scopeTarget.tab, scopeTarget.filterState);
      return;
    }

    await handleSessionActivate(session, scopeTarget.tab);
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

  function handlePanelResizeDragStart(
    panelId: ResizableShellPanelId,
    axis: ResizeAxis,
    container: HTMLElement | null,
    event: ReactPointerEvent<HTMLDivElement>
  ) {
    if (!container) {
      return;
    }

    const rect = container.getBoundingClientRect();
    const initialSizeHint = resolveShellPanelSizeHintFromPointer(
      panelId,
      axis,
      axis === "horizontal" ? event.clientX : event.clientY,
      rect
    );

    if (initialSizeHint === null) {
      return;
    }

    event.preventDefault();
    setActiveResizePanelId(panelId);

    const applyDraftSizeHint =
      panelId === "combo_view" ? setComboViewDraftSizeHint : setReportDockDraftSizeHint;
    applyDraftSizeHint(initialSizeHint);

    const handlePointerMove = (moveEvent: PointerEvent) => {
      const nextSizeHint = resolveShellPanelSizeHintFromPointer(
        panelId,
        axis,
        axis === "horizontal" ? moveEvent.clientX : moveEvent.clientY,
        rect
      );
      if (nextSizeHint !== null) {
        applyDraftSizeHint(nextSizeHint);
      }
    };

    const clearDragState = () => {
      setActiveResizePanelId((current) => (current === panelId ? null : current));
      applyDraftSizeHint(null);
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", handlePointerUp);
      window.removeEventListener("pointercancel", handlePointerCancel);
    };

    const handlePointerUp = (upEvent: PointerEvent) => {
      const nextSizeHint =
        resolveShellPanelSizeHintFromPointer(
          panelId,
          axis,
          axis === "horizontal" ? upEvent.clientX : upEvent.clientY,
          rect
        ) ?? initialSizeHint;
      clearDragState();
      void handlePanelSizeChange(panelId, nextSizeHint);
    };

    const handlePointerCancel = () => {
      clearDragState();
    };

    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerup", handlePointerUp);
    window.addEventListener("pointercancel", handlePointerCancel);
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
      selected_object_id: session.selected_object_id ?? null,
      selection_mode: session.selection_mode ?? null,
      combo_view_tab: session.combo_view_tab ?? null,
      bottom_dock_tab: (session.bottom_dock_tab as BottomDockTab | undefined) ?? null,
      combo_view_visible: session.combo_view_visible ?? null,
      report_dock_visible: session.report_dock_visible ?? null,
      combo_view_size_hint: session.combo_view_size_hint ?? null,
      report_dock_size_hint: session.report_dock_size_hint ?? null,
      report_dock_filter_label: session.report_dock_filter_label ?? null,
      report_dock_filter_query: session.report_dock_filter_query ?? null,
      diagnostics_dock_filter_label: session.diagnostics_dock_filter_label ?? null,
      diagnostics_dock_filter_query: session.diagnostics_dock_filter_query ?? null
    }));
  const activeWorkspaceSession = activeWorkspaceSessionForDocument(shellSnapshot, document);
  const activeWorkspaceScopeSession =
    activeWorkspaceSession ?? workspaceSessions.find((session) => Boolean(sessionScopeTarget(session))) ?? null;
  const activeWorkspaceScopeTarget = activeWorkspaceScopeSession
    ? sessionScopeTarget(activeWorkspaceScopeSession)
    : null;
  const activeWorkspaceScopeSummary = activeWorkspaceScopeSession
    ? sessionDockFilterSummary(activeWorkspaceScopeSession)
    : null;
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
  const comboViewSizeHint = comboViewDraftSizeHint ?? comboViewPanel?.size_hint ?? 0.28;
  const reportDockSizeHint = reportDockDraftSizeHint ?? reportDockPanel?.size_hint ?? 0.24;
  const comboColumnPercent = Math.round(comboViewSizeHint * 100);
  const selectionModeLabel =
    selectionState?.available_modes.find((mode) => mode.mode_id === selectionState.current_mode)?.label ??
    titleCaseShellToken(selectionState?.current_mode, "Object");
  const selectionSummary =
    selectionState?.selected_object_label ?? selectedObjectId ?? diagnostics?.selection.object_label ?? "None";
  const warningCount = diagnostics?.summary.warning_count ?? 0;
  const errorCount = diagnostics?.summary.error_count ?? 0;
  const diagnosticsSummary =
    diagnostics === null
      ? "Pending"
      : errorCount > 0
        ? `${errorCount} errors, ${warningCount} warnings`
        : warningCount > 0
          ? `${warningCount} warnings`
          : "Clear";
  const diagnosticsTone: StatusbarTone = errorCount > 0 ? "error" : warningCount > 0 ? "warning" : "info";
  const noticeTone: StatusbarTone = shellNotices.some((notice) => notice.level === "error")
    ? "error"
    : shellNotices.some((notice) => notice.level === "warning")
      ? "warning"
      : "info";
  const jobsCount = jobs?.jobs.length ?? 0;
  const workerModeLabel = titleCaseShellToken(boot.bridge_status.worker_mode, "Unknown");
  const dockSummary = reportDockVisible ? titleCaseShellToken(bottomDockTab, "Report") : "Hidden";
  const bottomDockSections: Array<{ count: string; label: string; summary: string; tab: BottomDockTab }> = [
    {
      tab: "report",
      label: "Report",
      count: `${shellNotices.length}`,
      summary: shellNotices.length > 0 ? "Notices and inspection activity" : "Inspection summary"
    },
    {
      tab: "python",
      label: "Python",
      count: "Host",
      summary: "Compatibility console slot"
    },
    {
      tab: "jobs",
      label: "Jobs",
      count: `${jobsCount}`,
      summary: jobsCount > 0 ? "Queued or running work" : "No active jobs"
    },
    {
      tab: "diagnostics",
      label: "Diagnostics",
      count: diagnosticsSummary,
      summary: "Selection and worker health"
    },
    {
      tab: "history",
      label: "History",
      count: `${featureHistory?.entries.length ?? 0}`,
      summary: "Rollback and suppression lane"
    },
    {
      tab: "commands",
      label: "Commands",
      count: `${commandCatalog?.commands.length ?? 0}`,
      summary: commandCatalog?.workbench.display_name ?? activeWorkbench.display_name
    },
    {
      tab: "extensions",
      label: "Extensions",
      count: `${extensionCompatibility?.lanes.length ?? 0}`,
      summary:
        extensionCompatibility?.lanes.length
          ? `${extensionCompatibility.lanes.length} compatibility lanes`
          : "Compatibility surface"
    }
  ];
  const activeBottomDockSection =
    bottomDockSections.find((section) => section.tab === bottomDockTab) ?? bottomDockSections[0];
  const showPinnedBottomDockRail = bottomDockTab !== "report" && (shellNotices.length > 0 || jobsCount > 0);
  const totalPanels = shellSnapshot?.layout.panels.length ?? 0;
  const fallbackStatusbarItems: ProtocolShellStatusBarItem[] = [
    {
      item_id: "workbench",
      label: "Workbench",
      value: activeWorkbench.display_name,
      tone: "neutral",
    },
    {
      item_id: "document",
      label: "Document",
      value: document.display_name,
      tone: "neutral",
    },
    {
      item_id: "state",
      label: "State",
      value: document.dirty ? "Modified" : "Saved",
      tone: document.dirty ? "warning" : "info",
    },
    {
      item_id: "mode",
      label: "Mode",
      value: selectionModeLabel,
      tone: "neutral",
    },
    {
      item_id: "selection",
      label: "Selection",
      value: selectionSummary,
      tone: "neutral",
    },
    {
      item_id: "diagnostics",
      label: "Diagnostics",
      value: diagnosticsSummary,
      tone: diagnosticsTone,
    },
    {
      item_id: "dock",
      label: "Dock",
      value: dockSummary,
      tone: reportDockVisible ? "info" : "warning",
    },
    {
      item_id: "worker",
      label: "Worker",
      value: workerModeLabel,
      tone: "neutral",
    },
    {
      item_id: "jobs",
      label: "Jobs",
      value: `${jobsCount}`,
      tone: jobsCount > 0 ? "warning" : "info",
    },
    {
      item_id: "panels",
      label: "Panels",
      value: `${visiblePanels}/${totalPanels} visible`,
      tone: "neutral",
    },
  ];
  const statusbarItems = (shellSnapshot?.status_bar?.items ?? fallbackStatusbarItems).filter(
    (item) => item.item_id !== "notices"
  );
  const comboColumnWidth = `clamp(232px, ${Math.max(20, comboColumnPercent)}vw, 344px)`;
  const inspectorColumnWidth = "clamp(300px, 24vw, 380px)";
  const bottomDockHeight = `clamp(184px, ${Math.max(18, Math.round(reportDockSizeHint * 100))}vh, 296px)`;
  const studioWorkspaceStyle = comboViewVisible
    ? {
        columnGap: 0,
        gridTemplateColumns: `${comboColumnWidth} ${PANEL_RESIZE_HANDLE_SIZE}px minmax(0, 1fr) ${inspectorColumnWidth}`
      }
    : {
        gridTemplateColumns: `minmax(0, 1fr) ${inspectorColumnWidth}`
      };
  const studioCenterColumnStyle = reportDockVisible
    ? {
        gridTemplateRows: `minmax(0, 1fr) ${PANEL_RESIZE_HANDLE_SIZE}px ${bottomDockHeight}`,
        rowGap: 0
      }
    : {
        gridTemplateRows: "minmax(0, 1fr)"
      };
  const workspaceStyle = comboViewVisible
    ? {
        columnGap: 0,
        gridTemplateColumns: `${comboColumnWidth} ${PANEL_RESIZE_HANDLE_SIZE}px minmax(0, 1fr)`
      }
    : {
        gridTemplateColumns: "minmax(0, 1fr)"
      };
  const mainColumnStyle = reportDockVisible
    ? {
        gridTemplateRows: `minmax(0, 1fr) ${PANEL_RESIZE_HANDLE_SIZE}px ${bottomDockHeight}`,
        rowGap: 0
      }
    : {
        gridTemplateRows: "minmax(0, 1fr)"
      };
  const reopenTabs: Array<{ panelId: "combo_view" | "report_dock"; label: string }> = [
    ...(comboViewVisible ? [] : [{ panelId: "combo_view" as const, label: "Show Combo View" }]),
    ...(reportDockVisible ? [] : [{ panelId: "report_dock" as const, label: "Show Bottom Dock" }])
  ];
  const studioInspectorPrimary =
    comboViewTab === "tasks" ? (
      <TaskPanel
        commandCatalog={commandCatalog}
        onRunCommand={(commandId, commandArguments) =>
          void handleCommand(commandId, commandArguments ?? {})
        }
        taskPanel={taskPanel}
      />
    ) : (
      <PropertyInspectorPane objectId={properties?.object_id} properties={properties} />
    );
  const studioInspectorSecondary =
    comboViewTab === "tasks" ? (
      <PropertyInspectorPane objectId={properties?.object_id} properties={properties} />
    ) : (
      <TaskPanel
        commandCatalog={commandCatalog}
        onRunCommand={(commandId, commandArguments) =>
          void handleCommand(commandId, commandArguments ?? {})
        }
        taskPanel={taskPanel}
      />
    );

  return (
    <div className="app-shell freecad-shell">
      <div className="freecad-toolbar-stack studio-shell-header">
        <div className="freecad-toolbar-row studio-shell-row">
          <div className="freecad-inline-menubar studio-inline-menubar">
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

          <div className="freecad-brand studio-title-cluster">
            <div className="freecad-frame-title">AsterForge Studio</div>
            <strong>{document.display_name}</strong>
          </div>

          <div className="studio-shell-actions">
            <label className="workbench-picker studio-workbench-picker">
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

            <form className="open-form freecad-open-form studio-open-form" onSubmit={handleOpenDocument}>
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
              <strong>F / Ctrl+K</strong>
            </button>
          </div>

          <div className="status-cluster studio-status-cluster">
            <span className="badge badge-hot">{document.workbench}</span>
            <span className="badge">{document.dirty ? "Unsaved changes" : "Saved"}</span>
            <span className="badge">{boot.boot_report.services.length} backend services</span>
            <span className="badge">{boot.bridge_status.worker_mode}</span>
            <span className="badge">{visiblePanels} visible panels</span>
          </div>
        </div>

        <div className="freecad-toolbar-row freecad-toolbar-row-compact studio-command-rail">
          <ShellToolbarBands
            catalog={commandCatalog}
            onRunCommand={(commandId) => void handleCommand(commandId)}
            shellSnapshot={shellSnapshot}
          />
          {activeWorkspaceScopeSession && activeWorkspaceScopeTarget && activeWorkspaceScopeSummary ? (
            <button
              aria-label={activeWorkspaceScopeSummary}
              className="action-button studio-scope-chip"
              onClick={() => {
                void handleSessionScopeActivate(activeWorkspaceScopeSession);
              }}
              title={`Open ${activeWorkspaceScopeSummary}`}
              type="button"
            >
              {activeWorkspaceScopeTarget.filterState.label}
            </button>
          ) : null}
          {reopenTabs.length > 0 ? (
            <div className="shell-layout-actions studio-restore-actions">
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
      </div>

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

      <main className="studio-workspace" ref={workspaceRef} style={studioWorkspaceStyle}>
        {comboViewVisible ? (
        <aside className="panel studio-sidebar-left">
          <div className="studio-pane-heading">
            <div>
              <span className="dock-strip-label">Studio</span>
              <strong>Scene Browser</strong>
            </div>
            <div className="studio-pane-actions">
              <button
                className={`dock-tab-button ${comboViewTab === "model" ? "dock-tab-button-active" : ""}`}
                onClick={() => void handlePanelTabChange("combo_view", "model")}
                type="button"
              >
                Scene
              </button>
              <button
                className={`dock-tab-button ${comboViewTab === "tasks" ? "dock-tab-button-active" : ""}`}
                onClick={() => void handlePanelTabChange("combo_view", "tasks")}
                type="button"
              >
                Workflow
              </button>
              <button
                className="dock-tab-button dock-tab-button-utility"
                onClick={() => void handlePanelVisibilityChange("combo_view", false)}
                type="button"
              >
                Hide
              </button>
            </div>
          </div>

          <div className="studio-sidebar-scroll">
            <SessionTabs
              activeDocumentId={document.document_id}
              activeFilePath={document.file_path}
              onClearInactive={() => {
                void handleClearInactiveSessions();
              }}
              onDismiss={(session) => {
                void handleDismissSession(session);
              }}
              onActivate={(session) => {
                void handleSessionActivate(session);
              }}
              onActivateScope={(session) => {
                void handleSessionScopeActivate(session);
              }}
              sessions={workspaceSessions}
            />

            {recentDocuments.length > 0 ? (
              <section className="studio-sidebar-section">
                <div className="studio-sidebar-section-head">
                  <span className="dock-strip-label">Recent</span>
                  <button
                    className="action-button action-button-subtle"
                    onClick={() => void handleClearRecentDocuments()}
                    type="button"
                  >
                    Clear History
                  </button>
                </div>
                <div className="recent-docs-list studio-recent-docs-list">
                  {recentDocuments.map((entry) => (
                    <button
                      className={`recent-doc-chip ${(document.file_path ?? openPath) === entry.file_path ? "recent-doc-chip-active" : ""}`}
                      key={entry.file_path}
                      onClick={() => void handleRecentDocumentOpen(entry.file_path)}
                      title={`${entry.display_name} • ${entry.workbench} • ${entry.dirty ? "Unsaved" : "Saved"}`}
                      type="button"
                    >
                      {entry.display_name}
                    </button>
                  ))}
                </div>
              </section>
            ) : null}

            <div className="combo-view-body combo-model-stack studio-scene-stack">
              <ModelBrowserPane
                objectTree={objectTree}
                onHoverChange={(objectId) => void handlePreselectionChange(objectId)}
                onSelect={handleSelect}
                preselectedObjectId={preselectionState?.object_id ?? null}
                selectedObjectId={selectedObjectId}
                selectionMode={selectionState?.current_mode ?? "object"}
              />
            </div>
          </div>
        </aside>
        ) : null}

        {comboViewVisible ? (
          <div
            aria-label="Resize combo view"
            aria-orientation="vertical"
            className={`freecad-pane-resize-handle freecad-pane-resize-handle-vertical ${
              activeResizePanelId === "combo_view" ? "freecad-pane-resize-handle-active" : ""
            }`.trim()}
            onPointerDown={(event) =>
              handlePanelResizeDragStart("combo_view", "horizontal", workspaceRef.current, event)
            }
            role="separator"
          />
        ) : null}

        <section className="studio-center-column" ref={mainColumnRef} style={studioCenterColumnStyle}>
          <section className="panel viewport-panel freecad-viewport-panel studio-viewport-shell">
            <div className="studio-viewport-chrome">
              <div className="studio-viewport-title">
                <span className="dock-strip-label">Viewport</span>
                <strong>{document.file_path ?? "Unsaved document"}</strong>
              </div>
              <div className="studio-viewport-actions">
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
                  onClick={() => void handlePanelVisibilityChange("report_dock", !reportDockVisible)}
                  type="button"
                >
                  {reportDockVisible ? "Hide Utilities" : "Show Utilities"}
                </button>
              </div>
            </div>
            <div
              className="viewport-canvas"
              onContextMenu={(event) => {
                event.preventDefault();
                setViewportAnchorFromClientPosition(event.currentTarget, event.clientX, event.clientY);
                setViewportCommandLensOpen(true);
              }}
              onPointerDown={(event) => {
                setViewportAnchorFromClientPosition(event.currentTarget, event.clientX, event.clientY);
              }}
              onPointerMove={(event) => {
                setViewportAnchorFromClientPosition(event.currentTarget, event.clientX, event.clientY);
              }}
            >
              {stepAvailable && stepDocument && stepScene ? (
                <Suspense fallback={<div className="viewport-empty">Loading STEP viewport...</div>}>
                  <LazyStepViewportScene
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
                </Suspense>
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
                onOpenPalette={() => {
                  setViewportCommandLensOpen(false);
                  setPaletteOpen(true);
                }}
                onOpenModel={() => void handlePanelTabChange("combo_view", "model")}
                onOpenReport={() => void handlePanelTabChange("report_dock", "report")}
                onOpenTasks={() => void handlePanelTabChange("combo_view", "tasks")}
                onResetPreset={() => void handleResetStepViewportPreset()}
                reportDockVisible={reportDockVisible}
                selectionState={selectionState}
                selectedObjectId={selectedObjectId}
                stepAvailable={stepAvailable}
                workbenchLabel={activeWorkbench.display_name}
              />
              <ViewportCommandBar
                commandCatalog={commandCatalog}
                onOpenPalette={() => {
                  setViewportCommandLensOpen(false);
                  setPaletteOpen(true);
                }}
                onRunCommand={(commandId, commandArguments, targetObjectId) =>
                  void handleCommand(commandId, commandArguments ?? {}, targetObjectId)
                }
                preselectionState={preselectionState}
                selectedObjectId={selectedObjectId}
                taskPanel={taskPanel}
              />
              <ViewportCommandLens
                anchor={viewportPointerAnchor}
                commandCatalog={commandCatalog}
                onClose={() => setViewportCommandLensOpen(false)}
                onOpenPalette={() => setPaletteOpen(true)}
                onRunCommand={(commandId, commandArguments, targetObjectId) =>
                  void handleCommand(commandId, commandArguments ?? {}, targetObjectId)
                }
                open={viewportCommandLensOpen}
                preselectionState={preselectionState}
                selectedObjectId={selectedObjectId}
                taskPanel={taskPanel}
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
            <div
              aria-label="Resize bottom dock"
              aria-orientation="horizontal"
              className={`freecad-pane-resize-handle freecad-pane-resize-handle-horizontal ${
                activeResizePanelId === "report_dock" ? "freecad-pane-resize-handle-active" : ""
              }`.trim()}
              onPointerDown={(event) =>
                handlePanelResizeDragStart("report_dock", "vertical", mainColumnRef.current, event)
              }
              role="separator"
            />
          ) : null}

          {reportDockVisible ? (
          <section className="panel freecad-bottom-dock studio-bottom-dock-shell">
            <div className="bottom-dock-tray">
              <div className="bottom-dock-tray-header">
                <div className="bottom-dock-tray-title">
                  <span>Utilities</span>
                  <strong>{activeBottomDockSection.label}</strong>
                </div>
                <div className="bottom-dock-tray-summary">
                  <span>{activeBottomDockSection.summary}</span>
                  <strong>{activeBottomDockSection.count}</strong>
                </div>
              </div>
              <div className="bottom-dock-tray-strip">
                {bottomDockSections.map((section) => (
                  <button
                    className={`bottom-dock-chip ${bottomDockTab === section.tab ? "bottom-dock-chip-active" : ""}`}
                    key={section.tab}
                    onClick={() => void handlePanelTabChange("report_dock", section.tab)}
                    type="button"
                  >
                    <span>{section.label}</span>
                    <strong>{section.count}</strong>
                  </button>
                ))}
              </div>
              <div className="bottom-dock-tray-actions">
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
            </div>

            <div className={`bottom-dock-layout ${showPinnedBottomDockRail ? "bottom-dock-layout-with-rail" : ""}`.trim()}>
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
                      filterState={reportDockFilter}
                      onClearFilter={() => {
                        setReportDockFilter(null);
                        void handlePersistDockFilters({ clear_report_dock_filter: true });
                      }}
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

                {bottomDockTab === "jobs" ? (
                  <JobsPanel
                    commandCatalog={commandCatalog}
                    jobs={jobs}
                    onFocusJobObject={(objectId) => void handleSelectAndCommand(objectId, "selection.focus")}
                    onOpenJobDiagnostics={(filterState) =>
                      void handleOpenFilteredBottomDockTab("diagnostics", filterState)
                    }
                    onOpenJobReport={(filterState) =>
                      void handleOpenFilteredBottomDockTab("report", filterState)
                    }
                    onRunJobCommand={(commandId, targetObjectId) =>
                      void handleCommand(commandId, {}, targetObjectId)
                    }
                    reportEvents={events}
                    onSelectJobObject={(objectId) => void handleSelect(objectId)}
                  />
                ) : null}
                {bottomDockTab === "diagnostics" ? (
                  <DiagnosticsPanel
                    commandStatus={commandStatus}
                    diagnostics={diagnostics}
                    filterState={diagnosticsDockFilter}
                    onClearFilter={() => {
                      setDiagnosticsDockFilter(null);
                      void handlePersistDockFilters({ clear_diagnostics_dock_filter: true });
                    }}
                  />
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

              {showPinnedBottomDockRail ? (
                <BottomDockPinnedRail
                  commandCatalog={commandCatalog}
                  jobs={jobs}
                  notices={shellNotices}
                  onFocusJobObject={(objectId) => void handleSelectAndCommand(objectId, "selection.focus")}
                  onFocusNoticeObject={(objectId) => void handleSelectAndCommand(objectId, "selection.focus")}
                  onOpenJobs={() => void handlePanelTabChange("report_dock", "jobs")}
                  onOpenReport={() => void handlePanelTabChange("report_dock", "report")}
                  onRunJobCommand={(commandId, targetObjectId) =>
                    void handleCommand(commandId, {}, targetObjectId)
                  }
                  onRunNoticeCommand={(commandId, targetObjectId) =>
                    void handleCommand(commandId, {}, targetObjectId)
                  }
                  onSelectJobObject={(objectId) => void handleSelect(objectId)}
                  onSelectNoticeObject={(objectId) => void handleSelect(objectId)}
                />
              ) : null}
            </div>
          </section>
          ) : null}
        </section>

        <aside className="panel studio-sidebar-right">
          <div className="studio-pane-heading studio-pane-heading-right">
            <div>
              <span className="dock-strip-label">Inspector</span>
              <strong>{comboViewTab === "tasks" ? "Workflow" : "Selection"}</strong>
            </div>
            <div className="studio-pane-actions">
              <button
                className={`dock-tab-button ${comboViewTab === "model" ? "dock-tab-button-active" : ""}`}
                onClick={() => void handlePanelTabChange("combo_view", "model")}
                type="button"
              >
                Inspect
              </button>
              <button
                className={`dock-tab-button ${comboViewTab === "tasks" ? "dock-tab-button-active" : ""}`}
                onClick={() => void handlePanelTabChange("combo_view", "tasks")}
                type="button"
              >
                Workflow
              </button>
            </div>
          </div>

          <div className="studio-sidebar-scroll studio-sidebar-scroll-right">
            {studioInspectorPrimary}
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
            {studioInspectorSecondary}
          </div>
        </aside>
      </main>

      <footer className="freecad-statusbar">
        {statusbarItems.map((item) => (
          <StatusbarItem key={item.item_id} label={item.label} value={item.value} tone={item.tone} />
        ))}
        <StatusbarItem label="Notices" value={`${shellNotices.length} live`} tone={noticeTone} />
      </footer>
    </div>
  );
}
