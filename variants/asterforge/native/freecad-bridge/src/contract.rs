use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BridgeCapabilities {
    pub fcstd_open: bool,
    pub object_tree_fetch: bool,
    pub property_fetch: bool,
    pub tessellation_fetch: bool,
    pub command_execution: bool,
}

impl Default for BridgeCapabilities {
    fn default() -> Self {
        Self {
            fcstd_open: true,
            object_tree_fetch: true,
            property_fetch: true,
            tessellation_fetch: true,
            command_execution: true,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BridgeStatus {
    pub worker_mode: String,
    pub freecad_runtime_detected: bool,
    pub capabilities: BridgeCapabilities,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct BridgeProtocolVersion {
    pub major: u16,
    pub minor: u16,
    pub patch: u16,
}

impl Default for BridgeProtocolVersion {
    fn default() -> Self {
        Self {
            major: 1,
            minor: 0,
            patch: 0,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct BridgeRequestOptions {
    pub timeout_ms: Option<u64>,
    pub correlation_id: Option<String>,
    pub retry_safe: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum BridgeErrorCategory {
    ValidationError,
    NativeError,
    Timeout,
    Cancelled,
    WorkerCrashed,
    Unsupported,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BridgeError {
    pub category: BridgeErrorCategory,
    pub code: String,
    pub summary: String,
    pub detail: String,
    pub correlation_id: Option<String>,
}

pub type BridgeOperationResult<T> = Result<T, BridgeError>;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BridgeRuntimeDescriptor {
    pub protocol_version: BridgeProtocolVersion,
    pub worker_mode: String,
    pub freecad_runtime_detected: bool,
    pub freecad_runtime_version: Option<String>,
    pub occt_version: Option<String>,
    pub capabilities: BridgeCapabilities,
    pub limitations: Vec<String>,
}

impl Default for BridgeRuntimeDescriptor {
    fn default() -> Self {
        Self {
            protocol_version: BridgeProtocolVersion::default(),
            worker_mode: "mock-freecad-worker".into(),
            freecad_runtime_detected: false,
            freecad_runtime_version: None,
            occt_version: None,
            capabilities: BridgeCapabilities {
                fcstd_open: true,
                object_tree_fetch: true,
                property_fetch: true,
                tessellation_fetch: true,
                command_execution: false,
            },
            limitations: vec![
                "native command execution is not yet implemented through the bridge contract"
                    .into(),
                "runtime metadata is currently mock-backed and intended for contract integration work"
                    .into(),
            ],
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NativeSessionToken {
    pub session_id: String,
    pub native_document_token: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BridgeSessionRequest {
    pub session_id: String,
    pub source_path: Option<String>,
    pub requested_workbench: Option<String>,
    pub options: BridgeRequestOptions,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BridgeSessionResponse {
    pub document_id: String,
    pub display_name: String,
    pub file_path: Option<String>,
    pub dirty: bool,
    pub workbench: String,
    pub token: NativeSessionToken,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BridgeCommandRequest {
    pub session_id: String,
    pub command_id: String,
    pub target_object_id: Option<String>,
    pub arguments: BTreeMap<String, String>,
    pub options: BridgeRequestOptions,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BridgeCommandResponse {
    pub command_id: String,
    pub accepted: bool,
    pub status_message: String,
    pub document_dirty: bool,
    pub changed_object_ids: Vec<String>,
    pub history_marker: Option<u32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BridgeViewportRequest {
    pub session_id: String,
    pub object_ids: Vec<String>,
    pub options: BridgeRequestOptions,
}

pub trait FreecadBridgeContract {
    fn describe_runtime(&self) -> BridgeOperationResult<BridgeRuntimeDescriptor>;
    fn open_document_session(
        &self,
        request: BridgeSessionRequest,
    ) -> BridgeOperationResult<BridgeSessionResponse>;
    fn execute_command(
        &self,
        request: BridgeCommandRequest,
    ) -> BridgeOperationResult<BridgeCommandResponse>;
    fn fetch_viewport(
        &self,
        request: BridgeViewportRequest,
    ) -> BridgeOperationResult<ViewportSnapshot>;
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BridgeDocumentSnapshot {
    pub document_id: String,
    pub display_name: String,
    pub workbench: String,
    pub file_path: Option<String>,
    pub dirty: bool,
    pub history_marker: Option<u32>,
    pub roots: Vec<BridgeObjectNode>,
    pub selected_object_id: String,
    pub viewport: ViewportSnapshot,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BridgeObjectNode {
    pub object_id: String,
    pub label: String,
    pub object_type: String,
    pub visibility: String,
    pub length_mm: Option<f32>,
    pub constraint_count: Option<u32>,
    pub profile_closed: Option<bool>,
    pub fully_constrained: Option<bool>,
    pub reference_plane: Option<String>,
    pub extent_mode: Option<String>,
    pub midplane: bool,
    pub source_object_id: Option<String>,
    pub sequence_index: Option<u32>,
    pub suppressed: bool,
    pub children: Vec<BridgeObjectNode>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ViewportSnapshot {
    pub camera: CameraState,
    pub drawables: Vec<DrawableMesh>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct CameraState {
    pub eye: [f32; 3],
    pub target: [f32; 3],
    pub up: [f32; 3],
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct DrawableMesh {
    pub object_id: String,
    pub label: String,
    pub kind: String,
    pub accent: String,
    pub bounds: Bounds2d,
    pub edges: Vec<Polyline2d>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Bounds2d {
    pub x: f32,
    pub y: f32,
    pub width: f32,
    pub height: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Polyline2d {
    pub points: Vec<Point2d>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Point2d {
    pub x: f32,
    pub y: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq)]
pub struct ViewportDiff {
    pub added: Vec<DrawableMesh>,
    pub removed: Vec<String>,
    pub modified: Vec<DrawableMesh>,
    pub camera_changed: bool,
    pub camera: Option<CameraState>,
}

impl ViewportDiff {
    pub fn is_empty(&self) -> bool {
        self.added.is_empty()
            && self.removed.is_empty()
            && self.modified.is_empty()
            && !self.camera_changed
    }
}