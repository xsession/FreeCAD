import { FormEvent, useEffect, useState } from "react";
import {
  fetchBootstrap,
  fetchCommandCatalog,
  fetchDiagnostics,
  fetchEvents,
  fetchFeatureHistory,
  fetchJobs,
  fetchObjectTree,
  fetchPreselectionState,
  fetchProperties,
  fetchSelectionState,
  fetchTaskPanel,
  fetchViewport,
  openDocument,
  runCommand,
  setPreselection,
  setSelection,
  setSelectionMode,
  type ActivityEvent,
  type BootPayload,
  type CommandArgumentDefinition,
  type CommandCatalogResponse,
  type CommandDefinition,
  type CommandExecutionResponse,
  type DiagnosticsResponse,
  type DocumentRef,
  type FeatureHistoryResponse,
  type JobStatusResponse,
  type ObjectNode,
  type PreselectionStateResponse,
  type PropertyResponse,
  type SelectionStateResponse,
  type TaskPanelResponse,
  type ViewportDiffResponse,
  type ViewportDrawable,
  type ViewportResponse
} from "./protocol";

type ShellNotice = {
  id: string;
  level: "info" | "warning" | "error";
  title: string;
  detail: string;
};

type WorkspaceSession = {
  session_id: string;
  document_id: string;
  display_name: string;
  file_path: string;
  workbench: string;
  dirty: boolean;
  selected_object_id: string | null;
};

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
                <strong>{command.label}</strong>
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
          type="button"
        >
          <span>{command.action_label ?? command.label}</span>
          {command.shortcut ? <strong>{command.shortcut}</strong> : null}
        </button>
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
            </button>
          );
        })}
      </div>
    </section>
  );
}

function CommandPalette({
  catalog,
  open,
  query,
  onQueryChange,
  onClose,
  onRunCommand
}: {
  catalog: CommandCatalogResponse | null;
  open: boolean;
  query: string;
  onQueryChange: (value: string) => void;
  onClose: () => void;
  onRunCommand: (commandId: string, commandArguments?: Record<string, string>) => void;
}) {
  const [selectedCommandId, setSelectedCommandId] = useState<string | null>(null);
  const [draftArguments, setDraftArguments] = useState<Record<string, Record<string, string>>>({});

  useEffect(() => {
    if (!open || !catalog) {
      setSelectedCommandId(null);
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

    setDraftArguments((current) => {
      const next = { ...current };
      for (const command of catalog.commands) {
        if (command.arguments.length === 0 || next[command.command_id]) {
          continue;
        }

        next[command.command_id] = Object.fromEntries(
          command.arguments.map((argument) => [
            argument.argument_id,
            argument.default_value ?? ""
          ])
        );
      }
      return next;
    });
  }, [catalog, open, query]);

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

  function inputTypeFor(argument: CommandArgumentDefinition) {
    return argument.value_type === "quantity" || argument.value_type === "float"
      ? "number"
      : "text";
  }

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
                  <strong>{command.action_label ?? command.label}</strong>
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
                  <strong>{selectedCommand.action_label ?? selectedCommand.label}</strong>
                  <p>{selectedCommand.description}</p>
                </div>
                <div className="command-palette-meta">
                  <span>{selectedCommand.group}</span>
                  {selectedCommand.shortcut ? <span>{selectedCommand.shortcut}</span> : null}
                </div>
              </div>
              {selectedCommand.arguments.length > 0 ? (
                <form
                  className="command-palette-form"
                  onSubmit={(event) => {
                    event.preventDefault();
                    onRunCommand(
                      selectedCommand.command_id,
                      draftArguments[selectedCommand.command_id] ?? {}
                    );
                  }}
                >
                  <div className="command-palette-fields">
                    {selectedCommand.arguments.map((argument) => {
                      const inputId = `palette-${selectedCommand.command_id}-${argument.argument_id}`;

                      return (
                        <label className="task-editor-label" htmlFor={inputId} key={inputId}>
                          <span>{argument.label}</span>
                          <div className="task-editor-row">
                            {argument.value_type === "enum" || argument.value_type === "boolean" ? (
                              <select
                                className="task-editor-select"
                                id={inputId}
                                onChange={(event) =>
                                  updateDraftValue(
                                    selectedCommand.command_id,
                                    argument.argument_id,
                                    event.target.value
                                  )
                                }
                                value={currentDraftValue(selectedCommand.command_id, argument)}
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
                                onChange={(event) =>
                                  updateDraftValue(
                                    selectedCommand.command_id,
                                    argument.argument_id,
                                    event.target.value
                                  )
                                }
                                placeholder={argument.placeholder ?? undefined}
                                required={argument.required}
                                step={inputTypeFor(argument) === "number" ? "0.1" : undefined}
                                type={inputTypeFor(argument)}
                                value={currentDraftValue(selectedCommand.command_id, argument)}
                              />
                            )}
                            {argument.unit ? (
                              <span className="task-editor-unit">{argument.unit}</span>
                            ) : null}
                          </div>
                        </label>
                      );
                    })}
                  </div>
                  <button
                    className="action-button action-button-primary"
                    disabled={!selectedCommand.enabled}
                    type="submit"
                  >
                    {selectedCommand.action_label ?? selectedCommand.label}
                  </button>
                </form>
              ) : (
                <button
                  className="action-button action-button-primary"
                  disabled={!selectedCommand.enabled}
                  onClick={() => onRunCommand(selectedCommand.command_id)}
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

    setCommandDrafts((current) => {
      const next: Record<string, Record<string, string>> = {};

      for (const commandId of taskPanel.suggested_commands) {
        const command = commandCatalog.commands.find((item) => item.command_id === commandId);
        if (!command || command.arguments.length === 0) {
          continue;
        }

        next[commandId] = {};
        for (const argument of command.arguments) {
          next[commandId][argument.argument_id] =
            current[commandId]?.[argument.argument_id] ?? argument.default_value ?? "";
        }
      }

      return next;
    });
  }, [taskPanel, commandCatalog]);

  if (!taskPanel) {
    return null;
  }

  const suggestedCommands = taskPanel.suggested_commands
    .map((commandId) => commandCatalog?.commands.find((item) => item.command_id === commandId))
    .filter((command): command is CommandDefinition => Boolean(command));

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

  function inputTypeFor(argument: CommandArgumentDefinition) {
    return argument.value_type === "quantity" || argument.value_type === "float"
      ? "number"
      : "text";
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
              <form
                className="task-editor"
                key={command.command_id}
                onSubmit={(event) => {
                  event.preventDefault();
                  onRunCommand(command.command_id, commandDrafts[command.command_id] ?? {});
                }}
              >
                <div className="task-editor-header">
                  <strong>{command.label}</strong>
                  <span>{command.group}</span>
                </div>
                <p className="task-command-note">{command.description}</p>
                <div className="task-editor-fields">
                  {command.arguments.map((argument) => {
                    const inputId = `${command.command_id}-${argument.argument_id}`;

                    return (
                      <label className="task-editor-label" htmlFor={inputId} key={inputId}>
                        <span>{argument.label}</span>
                        <div className="task-editor-row">
                          {argument.value_type === "enum" || argument.value_type === "boolean" ? (
                            <select
                              className="task-editor-select"
                              id={inputId}
                              onChange={(event) =>
                                updateDraftValue(
                                  command.command_id,
                                  argument.argument_id,
                                  event.target.value
                                )
                              }
                              value={currentDraftValue(command.command_id, argument)}
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
                              onChange={(event) =>
                                updateDraftValue(
                                  command.command_id,
                                  argument.argument_id,
                                  event.target.value
                                )
                              }
                              placeholder={argument.placeholder ?? undefined}
                              required={argument.required}
                              step={inputTypeFor(argument) === "number" ? "0.1" : undefined}
                              type={inputTypeFor(argument)}
                              value={currentDraftValue(command.command_id, argument)}
                            />
                          )}
                          {argument.unit ? <span className="task-editor-unit">{argument.unit}</span> : null}
                        </div>
                      </label>
                    );
                  })}
                </div>
                <button
                  className="action-button action-button-primary"
                  disabled={!command.enabled}
                  type="submit"
                >
                  {command.action_label ?? command.label}
                </button>
              </form>
            ) : (
              <div className="task-editor" key={command.command_id}>
                <div className="task-editor-header">
                  <strong>{command.label}</strong>
                  <span>{command.group}</span>
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

function NotificationCenter({
  notices
}: {
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
          </div>
        ))}
      </div>
    </section>
  );
}

function SelectionInspector({
  selectedObjectId,
  preselectionState,
  objectTree,
  properties,
  featureHistory,
  commandCatalog,
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
  onRunPreselectionCommand: (commandId: string, commandArguments?: Record<string, string>) => void;
  onPromotePreselectionCommand: (commandId: string) => void;
  viewport: ViewportResponse | null;
}) {
  const [preselectionDrafts, setPreselectionDrafts] = useState<Record<string, Record<string, string>>>({});

  useEffect(() => {
    if (!commandCatalog || !preselectionState?.object_id) {
      setPreselectionDrafts({});
      return;
    }

    setPreselectionDrafts((current) => {
      const next: Record<string, Record<string, string>> = {};

      for (const commandId of preselectionState.suggested_commands) {
        const command = commandCatalog.commands.find((item) => item.command_id === commandId);
        if (!command || command.arguments.length === 0) {
          continue;
        }

        next[commandId] = {};
        for (const argument of command.arguments) {
          next[commandId][argument.argument_id] =
            current[commandId]?.[argument.argument_id] ?? argument.default_value ?? "";
        }
      }

      return next;
    });
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
  const preselectionCommands =
    commandCatalog?.commands.filter((command) =>
      preselectionState?.suggested_commands.includes(command.command_id)
    ) ?? [];
  const topPropertyGroup = properties?.groups[0] ?? null;

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

  function inputTypeFor(argument: CommandArgumentDefinition) {
    return argument.value_type === "quantity" || argument.value_type === "float"
      ? "number"
      : "text";
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
              {enabledCommands.slice(0, 6).map((command) => (
                <div className="selection-command-chip" key={command.command_id}>
                  <strong>{command.action_label ?? command.label}</strong>
                  <span>{command.group}</span>
                </div>
              ))}
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
                    <form
                      className="selection-action-editor"
                      key={`hover-form-${command.command_id}`}
                      onSubmit={(event) => {
                        event.preventDefault();
                        onRunPreselectionCommand(
                          command.command_id,
                          preselectionDrafts[command.command_id] ?? {}
                        );
                      }}
                    >
                      <div className="task-editor-header">
                        <strong>{command.action_label ?? command.label}</strong>
                        <span>{command.group}</span>
                      </div>
                      <p className="task-command-note">{command.description}</p>
                      <div className="task-editor-fields">
                        {command.arguments.map((argument) => {
                          const inputId = `hover-${command.command_id}-${argument.argument_id}`;

                          return (
                            <label className="task-editor-label" htmlFor={inputId} key={inputId}>
                              <span>{argument.label}</span>
                              <div className="task-editor-row">
                                {argument.value_type === "enum" || argument.value_type === "boolean" ? (
                                  <select
                                    className="task-editor-select"
                                    id={inputId}
                                    onChange={(event) =>
                                      updatePreselectionDraftValue(
                                        command.command_id,
                                        argument.argument_id,
                                        event.target.value
                                      )
                                    }
                                    value={currentPreselectionDraftValue(command.command_id, argument)}
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
                                    onChange={(event) =>
                                      updatePreselectionDraftValue(
                                        command.command_id,
                                        argument.argument_id,
                                        event.target.value
                                      )
                                    }
                                    placeholder={argument.placeholder ?? undefined}
                                    required={argument.required}
                                    step={inputTypeFor(argument) === "number" ? "0.1" : undefined}
                                    type={inputTypeFor(argument)}
                                    value={currentPreselectionDraftValue(command.command_id, argument)}
                                  />
                                )}
                                {argument.unit ? <span className="task-editor-unit">{argument.unit}</span> : null}
                              </div>
                            </label>
                          );
                        })}
                      </div>
                      <button className="action-button action-button-primary" type="submit">
                        Run On Hovered
                      </button>
                    </form>
                  ) : (
                    <button
                      className="selection-command-chip selection-command-chip-button"
                      key={`hover-${command.command_id}`}
                      onClick={() => onPromotePreselectionCommand(command.command_id)}
                      type="button"
                    >
                      <strong>{command.action_label ?? command.label}</strong>
                      <span>{command.group}</span>
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
  const [openPath, setOpenPath] = useState(initialPath);
  const [recentDocuments, setRecentDocuments] = useState<string[]>([initialPath]);
  const [workspaceSessions, setWorkspaceSessions] = useState<WorkspaceSession[]>([]);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [paletteQuery, setPaletteQuery] = useState("");
  const [comboViewTab, setComboViewTab] = useState<"model" | "tasks">("model");
  const [bottomDockTab, setBottomDockTab] = useState<
    "report" | "python" | "jobs" | "diagnostics" | "history" | "commands"
  >("report");
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
        if (payload.document.file_path) {
          upsertWorkspaceSession({
            document_id: payload.document.document_id,
            display_name: payload.document.display_name,
            dirty: payload.document.dirty,
            file_path: payload.document.file_path,
            selected_object_id: payload.selected_object_id,
            workbench: payload.document.workbench
          });
        }
        if (payload.document.file_path) {
          setRecentDocuments((current) => [
            payload.document.file_path ?? initialPath,
            ...current.filter((path) => path !== payload.document.file_path)
          ].slice(0, 5));
        }
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

  function upsertWorkspaceSession(session: Omit<WorkspaceSession, "session_id">) {
    setWorkspaceSessions((current) => {
      const existing = current.find((item) => item.file_path === session.file_path);
      if (existing) {
        return current.map((item) =>
          item.file_path === session.file_path
            ? {
                ...item,
                ...session,
                session_id: item.session_id
              }
            : item
        );
      }

      return [
        {
          ...session,
          session_id: `${session.document_id}:${session.file_path}`
        },
        ...current
      ].slice(0, 8);
    });
  }

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

  async function refreshDocumentSlices(documentId: string, objectId: string) {
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
      nextSelectionState,
      nextJobs
    ] = await Promise.all([
      fetchProperties(documentId, objectId),
      fetchObjectTree(documentId),
      fetchViewport(documentId),
      fetchFeatureHistory(documentId),
      fetchEvents(documentId),
      fetchCommandCatalog(documentId),
      fetchTaskPanel(documentId),
      fetchDiagnostics(documentId),
      fetchPreselectionState(documentId),
      fetchSelectionState(documentId),
      fetchJobs(documentId)
    ]);
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
    setJobs(nextJobs);
    upsertWorkspaceSession({
      document_id: documentId,
      display_name: document?.display_name ?? documentId,
      dirty: document?.dirty ?? false,
      file_path: document?.file_path ?? openPath,
      selected_object_id: objectId,
      workbench: document?.workbench ?? "unknown"
    });
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
    extraArguments: Record<string, string> = {}
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
      const response = await runCommand({
        command_id: commandId,
        document_id: document.document_id,
        target_object_id: selectedObjectId,
        arguments: {
          source: "react-shell",
          ...defaultArguments,
          ...extraArguments
        }
      });
      setCommandStatus(response);
      const nextDocument = {
        ...document,
        dirty: response.document_dirty
      };
      setDocument(nextDocument);
      upsertWorkspaceSession({
        document_id: nextDocument.document_id,
        display_name: nextDocument.display_name,
        dirty: nextDocument.dirty,
        file_path: nextDocument.file_path ?? openPath,
        selected_object_id: selectedObjectId,
        workbench: nextDocument.workbench
      });

      // Apply incremental diff when available, fall back to full fetch
      if (response.viewport_diff && viewport) {
        const patched = applyViewportDiff(viewport, response.viewport_diff);
        setViewport(patched);
        setSelectedObjectId(patched.selected_object_id);
        await refreshDocumentSlices(document.document_id, patched.selected_object_id);
      } else if (selectedObjectId) {
        const nextViewport = await fetchViewport(document.document_id);
        setSelectedObjectId(nextViewport.selected_object_id);
        await refreshDocumentSlices(document.document_id, nextViewport.selected_object_id);
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
        nextJobs
      ] = await Promise.all([
        fetchViewport(nextDocument.document_id),
        fetchCommandCatalog(nextDocument.document_id),
        fetchTaskPanel(nextDocument.document_id),
        fetchEvents(nextDocument.document_id),
        fetchDiagnostics(nextDocument.document_id),
        fetchPreselectionState(nextDocument.document_id),
        fetchSelectionState(nextDocument.document_id),
        fetchJobs(nextDocument.document_id)
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
      setEvents(nextEvents);
      setCommandStatus(null);
      upsertWorkspaceSession({
        document_id: nextDocument.document_id,
        display_name: nextDocument.display_name,
        dirty: nextDocument.dirty,
        file_path: nextDocument.file_path ?? filePath,
        selected_object_id: nextSelectedObjectId,
        workbench: nextDocument.workbench
      });
      setRecentDocuments((current) => [
        filePath,
        ...current.filter((path) => path !== filePath)
      ].slice(0, 5));
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

  const commandNotice: ShellNotice[] = commandStatus
    ? [
        {
          id: `command-${commandStatus.command_id}-${commandStatus.accepted ? "ok" : "warn"}`,
          level: commandStatus.accepted ? "info" : "warning",
          title: commandStatus.command_id,
          detail: commandStatus.status_message
        }
      ]
    : [];
  const eventNotices: ShellNotice[] = events.slice(0, 3).map((event, index) => ({
    id: `${event.topic}-${index}`,
    level: event.level,
    title: event.topic.replaceAll("_", " "),
    detail: event.message
  }));
  const shellNotices = [...commandNotice, ...eventNotices].slice(0, 4);
  const flattenedTree = flattenObjectTree(objectTree);
  const objectTypeById = new Map(flattenedTree.map((node) => [node.object_id, node.object_type]));
  const selectableObjectCount = flattenedTree.filter((node) =>
    objectMatchesSelectionMode(node.object_type, selectionState?.current_mode ?? "object")
  ).length;

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

  return (
    <div className="app-shell freecad-shell">
      <div className="freecad-menubar">
        {["File", "Edit", "View", "Tools", "Macro", "Window", "Help"].map((menu) => (
          <button className="freecad-menu-button" key={menu} type="button">
            {menu}
          </button>
        ))}
      </div>

      <div className="freecad-toolbar-stack">
        <div className="freecad-toolbar-row">
          <div className="freecad-brand">
            <div className="eyebrow">AsterForge / FreeCAD Layout Transplant</div>
            <strong>{document.display_name}</strong>
          </div>
          <label className="workbench-picker">
            <span>Workbench</span>
            <select value={document.workbench} onChange={() => undefined}>
              <option value={document.workbench}>{document.workbench}</option>
            </select>
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
          <QuickActionRail
            catalog={commandCatalog}
            onRunCommand={(commandId) => void handleCommand(commandId)}
          />
          <div className="status-cluster">
            <span className="badge badge-hot">{document.workbench}</span>
            <span className="badge">{document.dirty ? "Unsaved changes" : "Saved"}</span>
            <span className="badge">{boot.boot_report.services.length} backend services</span>
            <span className="badge">{boot.bridge_status.worker_mode}</span>
          </div>
        </div>

        {recentDocuments.length > 0 ? (
          <div className="freecad-toolbar-row freecad-toolbar-row-compact">
            <span className="dock-strip-label">Recent</span>
            <div className="recent-docs-list">
              {recentDocuments.map((path) => (
                <button
                  className={`recent-doc-chip ${openPath === path ? "recent-doc-chip-active" : ""}`}
                  key={path}
                  onClick={() => setOpenPath(path)}
                  type="button"
                >
                  {path.split("/").at(-1) ?? path}
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
        onRunCommand={(commandId, commandArguments) =>
          void handleCommand(commandId, commandArguments ?? {})
        }
        open={paletteOpen}
        query={paletteQuery}
      />

      {error ? <div className="inline-alert">{error}</div> : null}

      <main className="freecad-workspace">
        <aside className="panel freecad-combo-view">
          <div className="dock-tab-strip">
            <button
              className={`dock-tab-button ${comboViewTab === "model" ? "dock-tab-button-active" : ""}`}
              onClick={() => setComboViewTab("model")}
              type="button"
            >
              Model
            </button>
            <button
              className={`dock-tab-button ${comboViewTab === "tasks" ? "dock-tab-button-active" : ""}`}
              onClick={() => setComboViewTab("tasks")}
              type="button"
            >
              Tasks
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

        <section className="freecad-main-column">
          <section className="panel viewport-panel freecad-viewport-panel">
            <div className="panel-header">
              <h2>3D View</h2>
              <span>{document.file_path ?? "Unsaved document"}</span>
            </div>
            <div className="viewport-canvas">
              <ViewportScene
                objectTypeById={objectTypeById}
                onHoverChange={(objectId) => void handlePreselectionChange(objectId)}
                onSelect={handleSelect}
                preselectedObjectId={preselectionState?.object_id ?? null}
                selectedObjectId={selectedObjectId}
                selectionMode={selectionState?.current_mode ?? "object"}
                viewport={viewport}
              />
              <div className="viewport-overlay">
                <span>Selection synchronized through backend state</span>
                <strong>
                  {selectedObjectId ? `Focused object: ${selectedObjectId}` : "No object selected"}
                </strong>
                <em>
                  {preselectionState?.object_label
                    ? `Hover candidate: ${preselectionState.object_label}`
                    : "Hover candidate: none"}
                </em>
                {preselectionState?.object_id ? (
                  <div className="preselection-hint-strip">
                    <span>{preselectionState.model_state}</span>
                    <span>{preselectionState.dependency_note}</span>
                    {preselectionState.suggested_commands.slice(0, 2).map((commandId) => (
                      <button
                        className="preselection-action-chip"
                        key={commandId}
                        onClick={() => void handlePromotePreselectionCommand(commandId)}
                        type="button"
                      >
                        {commandId}
                      </button>
                    ))}
                  </div>
                ) : null}
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

          <section className="panel freecad-bottom-dock">
            <div className="dock-tab-strip dock-tab-strip-bottom">
              <button
                className={`dock-tab-button ${bottomDockTab === "report" ? "dock-tab-button-active" : ""}`}
                onClick={() => setBottomDockTab("report")}
                type="button"
              >
                Report view
              </button>
              <button
                className={`dock-tab-button ${bottomDockTab === "python" ? "dock-tab-button-active" : ""}`}
                onClick={() => setBottomDockTab("python")}
                type="button"
              >
                Python console
              </button>
              <button
                className={`dock-tab-button ${bottomDockTab === "jobs" ? "dock-tab-button-active" : ""}`}
                onClick={() => setBottomDockTab("jobs")}
                type="button"
              >
                Jobs
              </button>
              <button
                className={`dock-tab-button ${bottomDockTab === "diagnostics" ? "dock-tab-button-active" : ""}`}
                onClick={() => setBottomDockTab("diagnostics")}
                type="button"
              >
                Diagnostics
              </button>
              <button
                className={`dock-tab-button ${bottomDockTab === "history" ? "dock-tab-button-active" : ""}`}
                onClick={() => setBottomDockTab("history")}
                type="button"
              >
                History
              </button>
              <button
                className={`dock-tab-button ${bottomDockTab === "commands" ? "dock-tab-button-active" : ""}`}
                onClick={() => setBottomDockTab("commands")}
                type="button"
              >
                Commands
              </button>
            </div>

            <div className="bottom-dock-content">
              {bottomDockTab === "report" ? (
                <div className="bottom-dock-report">
                  <NotificationCenter notices={shellNotices} />
                  <section className="dock-panel">
                    <div className="panel-header">
                      <h2>Backend Activity</h2>
                      <span>Live in-memory API events</span>
                    </div>
                    <div className="activity-list">
                      {events.map((activity, index) => (
                        <div className="activity-item" key={`${activity.topic}-${index}`}>
                          <span className={`level level-${activity.level}`}>{activity.level}</span>
                          <div>
                            <div className="activity-topic">
                              {activity.topic}
                              {activity.object_id ? ` / ${activity.object_id}` : ""}
                            </div>
                            <div className="activity-message">{activity.message}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </section>
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
            </div>
          </section>
        </section>
      </main>

      <footer className="freecad-statusbar">
        <span>Workbench: {document.workbench}</span>
        <span>Document: {document.display_name}</span>
        <span>{document.dirty ? "State: modified" : "State: saved"}</span>
        <span>Selection: {selectedObjectId ?? "none"}</span>
        <span>Worker: {boot.bridge_status.worker_mode}</span>
        <span>Jobs: {jobs?.jobs.length ?? 0}</span>
      </footer>
    </div>
  );
}
