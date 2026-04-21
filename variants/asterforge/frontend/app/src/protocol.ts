export type DocumentRef = {
  document_id: string;
  display_name: string;
  workbench: string;
  file_path: string | null;
  dirty: boolean;
};

export type ObjectNode = {
  object_id: string;
  label: string;
  object_type: string;
  visibility: "visible" | "hidden" | "inherited";
  children: ObjectNode[];
};

export type PropertyMetadata = {
  property_id: string;
  display_name: string;
  property_type: string;
  value_kind: string;
  read_only: boolean;
  unit: string | null;
  expression_capable: boolean;
  value_preview: string;
};

export type PropertyGroup = {
  group_id: string;
  title: string;
  properties: PropertyMetadata[];
};

export type PropertyResponse = {
  object_id: string;
  groups: PropertyGroup[];
};

export type ActivityEvent = {
  topic: string;
  level: "info" | "warning" | "error";
  message: string;
  document_id: string;
  object_id: string | null;
};

export type BootReport = {
  services: string[];
  event_streams: string[];
};

export type BootPayload = {
  boot_report: BootReport;
  bridge_status: {
    worker_mode: string;
    freecad_runtime_detected: boolean;
    capabilities: {
      fcstd_open: boolean;
      object_tree_fetch: boolean;
      property_fetch: boolean;
      tessellation_fetch: boolean;
      command_execution: boolean;
    };
  };
  document: DocumentRef;
  object_tree: ObjectNode[];
  selected_object_id: string;
  selection_state: SelectionStateResponse;
  preselection_state: PreselectionStateResponse;
  jobs: JobStatusResponse;
  properties: PropertyResponse;
  viewport: ViewportResponse;
  feature_history: FeatureHistoryResponse;
  command_catalog: CommandCatalogResponse;
  task_panel: TaskPanelResponse;
  diagnostics: DiagnosticsResponse;
  events: ActivityEvent[];
};

export type ViewportResponse = {
  document_id: string;
  selected_object_id: string;
  scene: {
    camera_eye: [number, number, number];
    camera_target: [number, number, number];
    drawables: ViewportDrawable[];
  };
};

export type ViewportDrawable = {
  object_id: string;
  label: string;
  kind: string;
  accent: string;
  bounds: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  paths: string[];
};

export type WorkbenchState = {
  workbench_id: string;
  display_name: string;
  mode: string;
};

export type CommandCatalogResponse = {
  document_id: string;
  workbench: WorkbenchState;
  commands: CommandDefinition[];
};

export type CommandArgumentDefinition = {
  argument_id: string;
  label: string;
  value_type: string;
  required: boolean;
  default_value: string | null;
  placeholder: string | null;
  unit: string | null;
  options: string[];
};

export type CommandDefinition = {
  command_id: string;
  label: string;
  group: string;
  shortcut: string | null;
  enabled: boolean;
  requires_selection: boolean;
  description: string;
  action_label: string | null;
  arguments: CommandArgumentDefinition[];
};

export type TaskPanelResponse = {
  document_id: string;
  title: string;
  description: string;
  sections: TaskPanelSection[];
  suggested_commands: string[];
};

export type TaskPanelSection = {
  section_id: string;
  title: string;
  rows: TaskPanelRow[];
};

export type TaskPanelRow = {
  label: string;
  value: string;
  emphasis: boolean;
};

export type FeatureHistoryResponse = {
  document_id: string;
  entries: FeatureHistoryEntry[];
};

export type DiagnosticsResponse = {
  document_id: string;
  summary: {
    total_features: number;
    suppressed_count: number;
    inactive_count: number;
    rolled_back_count: number;
    viewport_drawable_count: number;
    warning_count: number;
    error_count: number;
    history_marker_active: boolean;
    worker_mode: string;
  };
  selection: {
    object_id: string | null;
    object_label: string | null;
    object_type: string | null;
    model_state: string;
    dependency_note: string;
    visible_in_viewport: boolean;
  };
  recent_signals: Array<{
    level: "info" | "warning" | "error";
    title: string;
    detail: string;
  }>;
};

export type FeatureHistoryEntry = {
  object_id: string;
  label: string;
  object_type: string;
  sequence_index: number;
  source_object_id: string | null;
  role: string;
  suppressed: boolean;
  active: boolean;
  inactive_reason: string | null;
  rolled_back: boolean;
};

export type CommandExecutionRequest = {
  command_id: string;
  document_id: string;
  target_object_id?: string | null;
  arguments: Record<string, string>;
};

export type CommandExecutionResponse = {
  command_id: string;
  accepted: boolean;
  status_message: string;
  document_dirty: boolean;
  viewport_diff?: ViewportDiffResponse | null;
};

export type ViewportDiffResponse = {
  document_id: string;
  selected_object_id: string;
  added: ViewportDrawable[];
  removed: string[];
  modified: ViewportDrawable[];
  camera_changed: boolean;
  camera_eye: [number, number, number] | null;
  camera_target: [number, number, number] | null;
};

export type SelectionResponse = {
  selected_object_id: string;
};

export type SelectionModeOption = {
  mode_id: string;
  label: string;
  description: string;
  enabled: boolean;
  object_count: number;
};

export type SelectionStateResponse = {
  document_id: string;
  current_mode: string;
  selected_object_id: string;
  selected_object_label: string;
  selected_object_type: string;
  available_modes: SelectionModeOption[];
};

export type PreselectionStateResponse = {
  document_id: string;
  current_mode: string;
  object_id: string | null;
  object_label: string | null;
  object_type: string | null;
  selectable: boolean;
  model_state: string;
  dependency_note: string;
  suggested_commands: string[];
  detail: string;
};

export type JobStatusResponse = {
  document_id: string;
  jobs: Array<{
    job_id: string;
    title: string;
    command_id: string;
    state: string;
    progress_percent: number;
    detail: string;
    object_id: string | null;
    stages: Array<{
      stage_id: string;
      label: string;
      state: string;
      progress_percent: number;
    }>;
  }>;
};

export async function fetchBootstrap(): Promise<BootPayload> {
  return fetchJson<BootPayload>("/api/bootstrap");
}

export async function fetchProperties(
  documentId: string,
  objectId: string
): Promise<PropertyResponse> {
  return fetchJson<PropertyResponse>(`/api/documents/${documentId}/properties/${objectId}`);
}

export async function fetchObjectTree(documentId: string): Promise<ObjectNode[]> {
  return fetchJson<ObjectNode[]>(`/api/documents/${documentId}/tree`);
}

export async function fetchEvents(documentId: string): Promise<ActivityEvent[]> {
  return fetchJson<ActivityEvent[]>(`/api/documents/${documentId}/events`);
}

export async function fetchViewport(documentId: string): Promise<ViewportResponse> {
  return fetchJson<ViewportResponse>(`/api/documents/${documentId}/viewport`);
}

export async function fetchCommandCatalog(documentId: string): Promise<CommandCatalogResponse> {
  return fetchJson<CommandCatalogResponse>(`/api/documents/${documentId}/commands`);
}

export async function fetchTaskPanel(documentId: string): Promise<TaskPanelResponse> {
  return fetchJson<TaskPanelResponse>(`/api/documents/${documentId}/task-panel`);
}

export async function fetchFeatureHistory(documentId: string): Promise<FeatureHistoryResponse> {
  return fetchJson<FeatureHistoryResponse>(`/api/documents/${documentId}/history`);
}

export async function fetchDiagnostics(documentId: string): Promise<DiagnosticsResponse> {
  return fetchJson<DiagnosticsResponse>(`/api/documents/${documentId}/diagnostics`);
}

export async function fetchSelectionState(documentId: string): Promise<SelectionStateResponse> {
  return fetchJson<SelectionStateResponse>(`/api/documents/${documentId}/selection-state`);
}

export async function fetchPreselectionState(
  documentId: string
): Promise<PreselectionStateResponse> {
  return fetchJson<PreselectionStateResponse>(`/api/documents/${documentId}/preselection-state`);
}

export async function fetchJobs(documentId: string): Promise<JobStatusResponse> {
  return fetchJson<JobStatusResponse>(`/api/documents/${documentId}/jobs`);
}

export async function setSelection(
  documentId: string,
  objectId: string
): Promise<SelectionResponse> {
  return fetchJson<SelectionResponse>("/api/selection", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      document_id: documentId,
      object_id: objectId
    })
  });
}

export async function setSelectionMode(
  documentId: string,
  modeId: string
): Promise<SelectionStateResponse> {
  return fetchJson<SelectionStateResponse>("/api/selection/mode", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      document_id: documentId,
      mode_id: modeId
    })
  });
}

export async function setPreselection(
  documentId: string,
  objectId: string | null
): Promise<PreselectionStateResponse> {
  return fetchJson<PreselectionStateResponse>("/api/preselection", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      document_id: documentId,
      object_id: objectId
    })
  });
}

export async function runCommand(
  request: CommandExecutionRequest
): Promise<CommandExecutionResponse> {
  return fetchJson<CommandExecutionResponse>("/api/commands/run", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(request)
  });
}

export async function openDocument(file_path: string): Promise<DocumentRef> {
  return fetchJson<DocumentRef>("/api/documents/open", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ file_path })
  });
}

async function fetchJson<T>(input: string, init?: RequestInit): Promise<T> {
  const response = await fetch(input, init);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}
