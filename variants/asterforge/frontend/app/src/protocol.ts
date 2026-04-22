import type {
  BootPayload as GeneratedBootPayload,
  BootReport,
  CommandArgumentDefinition,
  CommandCatalogResponse,
  CommandDefinition,
  CommandInvocation,
  CommandReply,
  DiagnosticsResponse,
  DocumentRef,
  EventEnvelope,
  FeatureHistoryEntry,
  FeatureHistoryResponse,
  JobStatusResponse,
  ObjectNode,
  PreselectionState,
  PropertyGroup,
  PropertyMetadata,
  PropertyResponse,
  SelectionModeOption,
  SelectionReply,
  SelectionState,
  TaskPanelResponse,
  TaskPanelRow,
  TaskPanelSection,
  ViewportDiffResponse as GeneratedViewportDiffResponse,
  ViewportDrawable,
  ViewportResponse,
  WorkbenchState
} from "./generated/asterforge";

export type {
  BootReport,
  CommandArgumentDefinition,
  CommandCatalogResponse,
  CommandDefinition,
  DiagnosticsResponse,
  DocumentRef,
  FeatureHistoryEntry,
  FeatureHistoryResponse,
  JobStatusResponse,
  ObjectNode,
  PropertyGroup,
  PropertyMetadata,
  PropertyResponse,
  SelectionModeOption,
  TaskPanelResponse,
  TaskPanelRow,
  TaskPanelSection,
  ViewportDrawable,
  ViewportResponse,
  WorkbenchState
};

export type ActivityEvent = Omit<EventEnvelope, "level" | "object_id"> & {
  level: "info" | "warning" | "error";
  object_id?: string | null;
};
export type BootPayload = Omit<GeneratedBootPayload, "events"> & {
  events: ActivityEvent[];
};
export type CommandExecutionRequest = Omit<CommandInvocation, "target_object_id"> & {
  target_object_id?: string | null;
};
export type ViewportDiffResponse = Omit<GeneratedViewportDiffResponse, "camera_eye" | "camera_target"> & {
  camera_eye?: number[];
  camera_target?: number[];
};
export type CommandExecutionResponse = Omit<CommandReply, "viewport_diff"> & {
  viewport_diff?: ViewportDiffResponse;
};
export type PreselectionStateResponse = PreselectionState;
export type SelectionResponse = SelectionReply;
export type SelectionStateResponse = SelectionState;

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
