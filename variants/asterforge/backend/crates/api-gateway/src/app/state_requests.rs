#[derive(Debug, Clone, serde::Deserialize)]
pub struct OpenDocumentHttpRequest {
    pub file_path: String,
}

#[derive(Debug, Clone, serde::Deserialize)]
pub struct SelectionRequest {
    pub document_id: String,
    pub object_id: String,
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct SelectionResponse {
    pub selected_object_id: String,
}

#[derive(Debug, Clone, serde::Deserialize)]
pub struct SelectionModeRequest {
    pub document_id: String,
    pub mode_id: String,
}

#[derive(Debug, Clone, serde::Deserialize)]
pub struct ActivateWorkbenchRequest {
    pub document_id: String,
    pub workbench_id: String,
}

#[derive(Debug, Clone, serde::Deserialize)]
pub struct PreselectionRequest {
    pub document_id: String,
    pub object_id: Option<String>,
}

#[derive(Debug, Clone, serde::Deserialize)]
pub struct ShellPanelMutationRequest {
    pub document_id: String,
    pub panel_id: String,
    pub active_tab: Option<String>,
    pub visible: Option<bool>,
    pub size_hint: Option<f32>,
}

#[derive(Debug, Clone, serde::Deserialize)]
pub struct ShellSessionMutationRequest {
    pub document_id: String,
    pub remove_workspace_session_id: Option<String>,
    pub clear_recent_documents: bool,
    pub clear_inactive_workspace_sessions: bool,
}