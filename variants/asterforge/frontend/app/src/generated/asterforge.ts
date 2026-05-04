// Generated from protocol/proto/asterforge.proto. Do not edit manually.

export interface BridgeCapabilities {
  fcstd_open: boolean;
  object_tree_fetch: boolean;
  property_fetch: boolean;
  tessellation_fetch: boolean;
  command_execution: boolean;
}

export interface BridgeStatus {
  worker_mode: string;
  freecad_runtime_detected: boolean;
  capabilities: BridgeCapabilities;
}

export interface DocumentRef {
  document_id: string;
  display_name: string;
  file_path: string | undefined;
  workbench: string;
  dirty: boolean;
}

export interface ObjectNode {
  object_id: string;
  label: string;
  object_type: string;
  visibility: string;
  children: ObjectNode[];
}

export interface ObjectTreeResponse {
  document: DocumentRef;
  roots: ObjectNode[];
}

export interface PropertyMetadata {
  property_id: string;
  display_name: string;
  property_type: string;
  value_kind: string;
  read_only: boolean;
  unit: string | undefined;
  expression_capable: boolean;
  value_preview: string;
}

export interface PropertyGroup {
  group_id: string;
  title: string;
  properties: PropertyMetadata[];
}

export interface PropertyResponse {
  object_id: string;
  groups: PropertyGroup[];
}

export interface ViewportBounds {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface ViewportDrawable {
  object_id: string;
  label: string;
  kind: string;
  accent: string;
  bounds: ViewportBounds;
  paths: string[];
}

export interface ViewportScene {
  camera_eye: number[];
  camera_target: number[];
  drawables: ViewportDrawable[];
}

export interface ViewportResponse {
  document_id: string;
  selected_object_id: string;
  scene: ViewportScene;
}

export interface WorkbenchState {
  workbench_id: string;
  display_name: string;
  mode: string;
}

export interface WorkbenchCatalogEntry {
  workbench_id: string;
  display_name: string;
  icon: string | undefined;
  enabled: boolean;
  description: string | undefined;
  category: string;
  migration_lane: string;
}

export interface WorkbenchCatalog {
  active_workbench_id: string;
  workbenches: WorkbenchCatalogEntry[];
}

export interface MenuItem {
  kind: string;
  label: string | undefined;
  command_id: string | undefined;
  enabled: boolean | undefined;
  checked: boolean | undefined;
  submenu: Menu | undefined;
}

export interface Menu {
  menu_id: string;
  label: string;
  visible: boolean;
  items: MenuItem[];
}

export interface MenuBarState {
  workbench_id: string;
  menus: Menu[];
}

export interface ToolbarItem {
  kind: string;
  command_id: string | undefined;
  label: string | undefined;
  icon: string | undefined;
  enabled: boolean | undefined;
  checked: boolean | undefined;
}

export interface Toolbar {
  toolbar_id: string;
  label: string;
  visible: boolean;
  items: ToolbarItem[];
}

export interface ToolbarBand {
  band_id: string;
  label: string;
  toolbars: Toolbar[];
}

export interface ToolbarBandState {
  workbench_id: string;
  bands: ToolbarBand[];
}

export interface ShellPanelState {
  panel_id: string;
  region: string;
  visible: boolean;
  order: number;
  active_tab: string | undefined;
  size_hint: number | undefined;
}

export interface ShellLayoutState {
  layout_id: string;
  panels: ShellPanelState[];
}

export interface RecentDocumentEntry {
  file_path: string;
  display_name: string;
  workbench: string;
  dirty: boolean;
}

export interface WorkspaceSessionEntry {
  session_id: string;
  document_id: string;
  display_name: string;
  file_path: string;
  workbench: string;
  dirty: boolean;
  selected_object_id: string | undefined;
}

export interface ShellSnapshot {
  document: DocumentRef;
  workbench_catalog: WorkbenchCatalog;
  menu_bar: MenuBarState;
  toolbar_bands: ToolbarBandState;
  layout: ShellLayoutState;
  recent_documents: RecentDocumentEntry[];
  workspace_sessions: WorkspaceSessionEntry[];
  inspection: ShellInspectionState | undefined;
  extension_compatibility: ExtensionCompatibilityState | undefined;
}

export interface ShellInspectionState {
  step_pmi: StepPmiInspectionOverlay | undefined;
  step_measurement: StepMeasurementOverlay | undefined;
}

export interface ExtensionCompatibilityState {
  title: string;
  summary: string;
  lanes: ExtensionCompatibilityLane[];
}

export interface ExtensionCompatibilityLane {
  lane_id: string;
  label: string;
  status: string;
  owner: string;
  summary: string;
  next_steps: string[];
  command_ids: string[];
  inventory_entries: ExtensionInventoryEntry[];
}

export interface ExtensionInventoryEntry {
  entry_id: string;
  label: string;
  origin: string;
  trust_state: string;
  compatibility: string;
  detail: string;
  action_command_id: string | undefined;
  action_label: string | undefined;
  last_run_status: string | undefined;
  last_run_level: string | undefined;
  last_run_detail: string | undefined;
  last_run_kind: string | undefined;
}

export interface CommandArgumentDefinition {
  argument_id: string;
  label: string;
  value_type: string;
  required: boolean;
  default_value: string | undefined;
  placeholder: string | undefined;
  unit: string | undefined;
  options: string[];
}

export interface CommandDefinition {
  command_id: string;
  label: string;
  group: string;
  icon: string | undefined;
  shortcut: string | undefined;
  enabled: boolean;
  requires_selection: boolean;
  description: string;
  action_label: string | undefined;
  arguments: CommandArgumentDefinition[];
}

export interface CommandCatalogResponse {
  document_id: string;
  workbench: WorkbenchState;
  commands: CommandDefinition[];
}

export interface TaskPanelRow {
  label: string;
  value: string;
  emphasis: boolean;
}

export interface TaskPanelSection {
  section_id: string;
  title: string;
  rows: TaskPanelRow[];
}

export interface TaskPanelResponse {
  document_id: string;
  title: string;
  description: string;
  sections: TaskPanelSection[];
  suggested_commands: string[];
}

export interface StepPmiInspectionOverlay {
  object_id: string;
  label: string;
  entity_id: number;
  target_object_ids: string[];
  presentation_object_ids: string[];
  annotation_lines: string[];
}

export interface StepMeasurementOverlay {
  object_id: string;
  label: string;
  span_x: number;
  span_y: number;
  span_z: number;
  representation_count: number;
  annotation_count: number;
}

export interface FeatureHistoryEntry {
  object_id: string;
  label: string;
  object_type: string;
  sequence_index: number;
  source_object_id: string | undefined;
  role: string;
  suppressed: boolean;
  active: boolean;
  inactive_reason: string | undefined;
  rolled_back: boolean;
}

export interface FeatureHistoryResponse {
  document_id: string;
  entries: FeatureHistoryEntry[];
}

export interface DiagnosticsSummary {
  total_features: number;
  suppressed_count: number;
  inactive_count: number;
  rolled_back_count: number;
  viewport_drawable_count: number;
  warning_count: number;
  error_count: number;
  history_marker_active: boolean;
  worker_mode: string;
}

export interface DiagnosticsSelection {
  object_id: string | undefined;
  object_label: string | undefined;
  object_type: string | undefined;
  model_state: string;
  dependency_note: string;
  visible_in_viewport: boolean;
}

export interface DiagnosticSignal {
  level: string;
  title: string;
  detail: string;
}

export interface DiagnosticsResponse {
  document_id: string;
  summary: DiagnosticsSummary;
  selection: DiagnosticsSelection;
  recent_signals: DiagnosticSignal[];
}

export interface BootReport {
  services: string[];
  event_streams: string[];
}

export interface SelectionRef {
  document_id: string;
  object_id: string;
  subelement: string;
  selection_mode: string;
}

export interface SelectionReply {
  selected_object_id: string;
}

export interface SelectionModeOption {
  mode_id: string;
  label: string;
  description: string;
  enabled: boolean;
  object_count: number;
}

export interface SelectionState {
  document_id: string;
  current_mode: string;
  selected_object_id: string;
  selected_object_label: string;
  selected_object_type: string;
  available_modes: SelectionModeOption[];
}

export interface SelectionModeRequest {
  document_id: string;
  mode_id: string;
}

export interface WorkbenchActivationRequest {
  document_id: string;
  workbench_id: string;
}

export interface ShellPanelMutationRequest {
  document_id: string;
  panel_id: string;
  active_tab: string | undefined;
  visible: boolean | undefined;
  size_hint: number | undefined;
}

export interface PreselectionState {
  document_id: string;
  current_mode: string;
  object_id: string | undefined;
  object_label: string | undefined;
  object_type: string | undefined;
  selectable: boolean;
  model_state: string;
  dependency_note: string;
  suggested_commands: string[];
  detail: string;
}

export interface JobStatusEntry {
  job_id: string;
  title: string;
  command_id: string;
  state: string;
  progress_percent: number;
  detail: string;
  object_id: string | undefined;
  stages: JobStageEntry[];
}

export interface JobStageEntry {
  stage_id: string;
  label: string;
  state: string;
  progress_percent: number;
}

export interface JobStatusResponse {
  document_id: string;
  jobs: JobStatusEntry[];
}

export interface PreselectionRequest {
  document_id: string;
  object_id: string | undefined;
}

export interface CommandInvocation {
  command_id: string;
  document_id: string;
  target_object_id: string | undefined;
  arguments: Record<string, string>;
}

export interface EventEnvelope {
  topic: string;
  level: string;
  message: string;
  document_id: string;
  object_id: string | undefined;
}

export interface OpenDocumentRequest {
  file_path: string;
}

export interface ObjectTreeRequest {
  document_id: string;
}

export interface PropertyRequest {
  document_id: string;
  object_id: string;
}

export interface CommandReply {
  command_id: string;
  accepted: boolean;
  status_message: string;
  document_dirty: boolean;
  viewport_diff: ViewportDiffResponse;
}

export interface ViewportDiffResponse {
  document_id: string;
  selected_object_id: string;
  added: ViewportDrawable[];
  removed: string[];
  modified: ViewportDrawable[];
  camera_changed: boolean;
  camera_eye: number[];
  camera_target: number[];
}

export interface SubscribeRequest {
  document_id: string;
}

export interface BootPayload {
  boot_report: BootReport;
  bridge_status: BridgeStatus;
  document: DocumentRef;
  object_tree: ObjectNode[];
  selected_object_id: string;
  selection_state: SelectionState;
  preselection_state: PreselectionState;
  jobs: JobStatusResponse;
  properties: PropertyResponse;
  viewport: ViewportResponse;
  feature_history: FeatureHistoryResponse;
  command_catalog: CommandCatalogResponse;
  task_panel: TaskPanelResponse;
  diagnostics: DiagnosticsResponse;
  events: EventEnvelope[];
  shell_snapshot: ShellSnapshot;
}

export interface Empty {
}

