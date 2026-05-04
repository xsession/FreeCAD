use std::ops::{Deref, DerefMut};

use asterforge_freecad_bridge::{BridgeDocumentSnapshot, BridgeObjectNode};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DocumentSummary {
    pub document_id: String,
    pub display_name: String,
    pub workbench: String,
    pub file_path: Option<String>,
    pub dirty: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RecentDocumentEntry {
    pub file_path: String,
    pub display_name: String,
    pub workbench: String,
    pub dirty: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkspaceSessionEntry {
    pub session_id: String,
    pub document_id: String,
    pub display_name: String,
    pub file_path: String,
    pub workbench: String,
    pub dirty: bool,
    pub selected_object_id: Option<String>,
    pub selection_mode: Option<String>,
    pub combo_view_tab: Option<String>,
    pub bottom_dock_tab: Option<String>,
    pub combo_view_visible: Option<bool>,
    pub report_dock_visible: Option<bool>,
    pub combo_view_size_hint: Option<f32>,
    pub report_dock_size_hint: Option<f32>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct DocumentWorkspaceState {
    pub recent_documents: Vec<RecentDocumentEntry>,
    pub workspace_sessions: Vec<WorkspaceSessionEntry>,
}

impl DocumentWorkspaceState {
    pub fn remember_document(
        &mut self,
        recent_entry: RecentDocumentEntry,
        session_entry: WorkspaceSessionEntry,
    ) {
        self.recent_documents
            .retain(|entry| entry.file_path != recent_entry.file_path);
        self.recent_documents.insert(0, recent_entry);
        self.recent_documents.truncate(8);

        self.workspace_sessions
            .retain(|entry| entry.session_id != session_entry.session_id);
        self.workspace_sessions.insert(0, session_entry);
        self.workspace_sessions.truncate(8);
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FeatureHistoryResponse {
    pub document_id: String,
    pub entries: Vec<FeatureHistoryEntry>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FeatureHistoryEntry {
    pub object_id: String,
    pub label: String,
    pub object_type: String,
    pub sequence_index: u32,
    pub source_object_id: Option<String>,
    pub role: String,
    pub suppressed: bool,
    pub active: bool,
    pub inactive_reason: Option<String>,
    pub rolled_back: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DocumentEvaluationState {
    pub total_features: u32,
    pub suppressed_count: u32,
    pub inactive_count: u32,
    pub rolled_back_count: u32,
    pub history_marker_active: bool,
    pub worker_mode: String,
}

impl DocumentEvaluationState {
    pub fn from_feature_history(
        history: &FeatureHistoryResponse,
        history_marker_active: bool,
        worker_mode: impl Into<String>,
    ) -> Self {
        Self {
            total_features: history.entries.len() as u32,
            suppressed_count: history.entries.iter().filter(|entry| entry.suppressed).count() as u32,
            inactive_count: history
                .entries
                .iter()
                .filter(|entry| !entry.active && !entry.suppressed)
                .count() as u32,
            rolled_back_count: history.entries.iter().filter(|entry| entry.rolled_back).count()
                as u32,
            history_marker_active,
            worker_mode: worker_mode.into(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DocumentObjectRecord {
    pub object_id: String,
    pub object_type: String,
    pub label: String,
    pub parent_object_id: Option<String>,
    pub source_object_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DocumentDependencyEdge {
    pub from_object_id: String,
    pub to_object_id: String,
    pub relationship: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct DocumentGraph {
    pub objects: Vec<DocumentObjectRecord>,
    pub dependencies: Vec<DocumentDependencyEdge>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DocumentState {
    pub summary: DocumentSummary,
    pub history: FeatureHistoryResponse,
    pub evaluation: DocumentEvaluationState,
    pub graph: DocumentGraph,
}

impl DocumentState {
    pub fn new(
        summary: DocumentSummary,
        history: FeatureHistoryResponse,
        evaluation: DocumentEvaluationState,
    ) -> Self {
        Self {
            summary,
            history,
            evaluation,
            graph: DocumentGraph::default(),
        }
    }

    pub fn with_graph(mut self, graph: DocumentGraph) -> Self {
        self.graph = graph;
        self
    }

    pub fn sync(
        &mut self,
        summary: DocumentSummary,
        history: FeatureHistoryResponse,
        evaluation: DocumentEvaluationState,
    ) {
        self.summary = summary;
        self.history = history;
        self.evaluation = evaluation;
    }

    pub fn set_graph(&mut self, graph: DocumentGraph) {
        self.graph = graph;
    }

    pub fn matches_document(&self, document_id: &str) -> bool {
        self.summary.document_id == document_id
    }

    pub fn summary(&self) -> &DocumentSummary {
        &self.summary
    }

    pub fn history(&self) -> &FeatureHistoryResponse {
        &self.history
    }

    pub fn evaluation(&self) -> &DocumentEvaluationState {
        &self.evaluation
    }

    pub fn graph(&self) -> &DocumentGraph {
        &self.graph
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FeatureDependencyState {
    pub active: bool,
    pub suppressed: bool,
    pub inactive_reason: Option<String>,
}

pub fn bridge_document_state(
    snapshot: &BridgeDocumentSnapshot,
    worker_mode: &str,
) -> DocumentState {
    tracing::debug!(document_id = %snapshot.document_id, worker_mode, "projecting bridge document state in document-core");
    DocumentState::new(
        document_summary_from_bridge(snapshot),
        feature_history_from_bridge(snapshot),
        document_evaluation_state_from_bridge(snapshot, worker_mode),
    )
    .with_graph(document_graph_from_bridge(snapshot))
}

pub fn document_summary_from_bridge(snapshot: &BridgeDocumentSnapshot) -> DocumentSummary {
    DocumentSummary {
        document_id: snapshot.document_id.clone(),
        display_name: snapshot.display_name.clone(),
        workbench: snapshot.workbench.clone(),
        file_path: snapshot.file_path.clone(),
        dirty: snapshot.dirty,
    }
}

pub fn feature_history_from_bridge(snapshot: &BridgeDocumentSnapshot) -> FeatureHistoryResponse {
    let mut entries = snapshot
        .roots
        .iter()
        .flat_map(|root| root.children.iter())
        .map(|child| {
            let state = bridge_object_state(snapshot, child);
            FeatureHistoryEntry {
                object_id: child.object_id.clone(),
                label: child.label.clone(),
                object_type: child.object_type.clone(),
                sequence_index: child.sequence_index.unwrap_or(0),
                source_object_id: child.source_object_id.clone(),
                role: match child.object_type.as_str() {
                    "Sketcher::SketchObject" => "sketch".into(),
                    "PartDesign::Pad" => "additive".into(),
                    "PartDesign::Pocket" => "subtractive".into(),
                    _ => "support".into(),
                },
                suppressed: child.suppressed,
                active: state.active,
                inactive_reason: state.inactive_reason,
                rolled_back: snapshot
                    .history_marker
                    .map(|marker| child.sequence_index.unwrap_or(0) > marker)
                    .unwrap_or(false),
            }
        })
        .collect::<Vec<_>>();

    entries.sort_by_key(|entry| entry.sequence_index);
    FeatureHistoryResponse {
        document_id: snapshot.document_id.clone(),
        entries,
    }
}

pub fn document_evaluation_state_from_bridge(
    snapshot: &BridgeDocumentSnapshot,
    worker_mode: &str,
) -> DocumentEvaluationState {
    let history = feature_history_from_bridge(snapshot);
    DocumentEvaluationState::from_feature_history(
        &history,
        snapshot.history_marker.is_some(),
        worker_mode,
    )
}

pub fn document_graph_from_bridge(snapshot: &BridgeDocumentSnapshot) -> DocumentGraph {
    let mut graph = DocumentGraph::default();

    for root in &snapshot.roots {
        collect_document_graph_node(&mut graph, root, None);
    }

    graph
}

pub fn bridge_object_state(
    snapshot: &BridgeDocumentSnapshot,
    node: &BridgeObjectNode,
) -> FeatureDependencyState {
    if snapshot
        .history_marker
        .map(|marker| node.sequence_index.unwrap_or(0) > marker)
        .unwrap_or(false)
    {
        return FeatureDependencyState {
            active: false,
            suppressed: false,
            inactive_reason: Some(format!(
                "Inactive because the history marker is set before step {}.",
                node.sequence_index.unwrap_or(0)
            )),
        };
    }

    if node.suppressed {
        return FeatureDependencyState {
            active: false,
            suppressed: true,
            inactive_reason: Some("Feature is manually suppressed.".into()),
        };
    }

    let Some(source_object_id) = node.source_object_id.as_deref() else {
        return FeatureDependencyState {
            active: true,
            suppressed: false,
            inactive_reason: None,
        };
    };

    let Some(source_node) = find_bridge_object(snapshot, source_object_id) else {
        return FeatureDependencyState {
            active: false,
            suppressed: false,
            inactive_reason: Some(format!("Source object {} is missing.", source_object_id)),
        };
    };

    let source_state = bridge_object_state(snapshot, source_node);
    if source_state.suppressed {
        FeatureDependencyState {
            active: false,
            suppressed: false,
            inactive_reason: Some(format!("Blocked by suppressed source {}", source_object_id)),
        }
    } else if !source_state.active {
        FeatureDependencyState {
            active: false,
            suppressed: false,
            inactive_reason: source_state.inactive_reason,
        }
    } else {
        FeatureDependencyState {
            active: true,
            suppressed: false,
            inactive_reason: None,
        }
    }
}

pub fn find_pad_length_mm(snapshot: &BridgeDocumentSnapshot, object_id: &str) -> Option<f32> {
    snapshot
        .roots
        .iter()
        .flat_map(|root| root.children.iter())
        .find(|child| child.object_id == object_id)
        .and_then(|child| child.length_mm)
}

pub fn find_bridge_child<'a>(
    snapshot: &'a BridgeDocumentSnapshot,
    object_id: &str,
) -> Option<&'a BridgeObjectNode> {
    snapshot
        .roots
        .iter()
        .flat_map(|root| root.children.iter())
        .find(|child| child.object_id == object_id)
}

pub fn sketch_constraint_summary(node: &BridgeObjectNode) -> String {
    let count = node.constraint_count.unwrap_or(0);
    if node.fully_constrained.unwrap_or(false) {
        format!("{} constraints resolved", count)
    } else {
        format!("{} constraints, solver pending", count)
    }
}

pub fn sketch_profile_readiness(node: &BridgeObjectNode) -> String {
    match (node.profile_closed, node.fully_constrained) {
        (Some(true), Some(true)) => "Closed profile / fully constrained".into(),
        (Some(true), _) => "Closed profile".into(),
        (Some(false), _) => "Open profile".into(),
        _ => "Profile status unavailable".into(),
    }
}

pub fn selectable_object_ids_for_mode(
    snapshot: &BridgeDocumentSnapshot,
    selection_mode: &str,
) -> Vec<String> {
    tracing::debug!(document_id = %snapshot.document_id, selection_mode, "projecting selectable ids in document-core");
    snapshot
        .roots
        .iter()
        .flat_map(|root| std::iter::once(root).chain(root.children.iter()))
        .filter(|node| object_matches_selection_mode(node.object_type.as_str(), selection_mode))
        .map(|node| node.object_id.clone())
        .collect()
}

pub fn object_matches_selection_mode(object_type: &str, selection_mode: &str) -> bool {
    match selection_mode {
        "object" => true,
        "body" => object_type == "PartDesign::Body",
        "sketch" => object_type == "Sketcher::SketchObject",
        "feature" => matches!(object_type, "PartDesign::Pad" | "PartDesign::Pocket"),
        _ => false,
    }
}

fn collect_document_graph_node(
    graph: &mut DocumentGraph,
    node: &BridgeObjectNode,
    parent_object_id: Option<&str>,
) {
    graph.objects.push(DocumentObjectRecord {
        object_id: node.object_id.clone(),
        object_type: node.object_type.clone(),
        label: node.label.clone(),
        parent_object_id: parent_object_id.map(str::to_string),
        source_object_id: node.source_object_id.clone(),
    });

    if let Some(parent_object_id) = parent_object_id {
        graph.dependencies.push(DocumentDependencyEdge {
            from_object_id: parent_object_id.to_string(),
            to_object_id: node.object_id.clone(),
            relationship: "contains".into(),
        });
    }

    if let Some(source_object_id) = node.source_object_id.as_ref() {
        graph.dependencies.push(DocumentDependencyEdge {
            from_object_id: source_object_id.clone(),
            to_object_id: node.object_id.clone(),
            relationship: "depends_on".into(),
        });
    }

    for child in &node.children {
        collect_document_graph_node(graph, child, Some(&node.object_id));
    }
}

fn find_bridge_object<'a>(
    snapshot: &'a BridgeDocumentSnapshot,
    object_id: &str,
) -> Option<&'a BridgeObjectNode> {
    snapshot
        .roots
        .iter()
        .flat_map(|root| std::iter::once(root).chain(root.children.iter()))
        .find(|node| node.object_id == object_id)
}

impl Deref for DocumentState {
    type Target = DocumentSummary;

    fn deref(&self) -> &Self::Target {
        &self.summary
    }
}

impl DerefMut for DocumentState {
    fn deref_mut(&mut self) -> &mut Self::Target {
        &mut self.summary
    }
}

#[cfg(test)]
mod tests {
    use asterforge_freecad_bridge::open_document_snapshot;

    use super::{
        bridge_document_state, bridge_object_state, document_graph_from_bridge,
        find_bridge_child, find_pad_length_mm, object_matches_selection_mode,
        selectable_object_ids_for_mode, sketch_constraint_summary, sketch_profile_readiness,
        DocumentEvaluationState, DocumentState, DocumentSummary, DocumentWorkspaceState,
        FeatureHistoryEntry, FeatureHistoryResponse, RecentDocumentEntry, WorkspaceSessionEntry,
    };

    #[test]
    fn derives_evaluation_counts_from_feature_history() {
        let history = FeatureHistoryResponse {
            document_id: "doc-demo-001".into(),
            entries: vec![
                FeatureHistoryEntry {
                    object_id: "sketch-001".into(),
                    label: "Sketch".into(),
                    object_type: "Sketcher::SketchObject".into(),
                    sequence_index: 1,
                    source_object_id: None,
                    role: "sketch".into(),
                    suppressed: false,
                    active: true,
                    inactive_reason: None,
                    rolled_back: false,
                },
                FeatureHistoryEntry {
                    object_id: "pad-001".into(),
                    label: "Pad".into(),
                    object_type: "PartDesign::Pad".into(),
                    sequence_index: 2,
                    source_object_id: Some("sketch-001".into()),
                    role: "additive".into(),
                    suppressed: true,
                    active: false,
                    inactive_reason: Some("Feature is manually suppressed.".into()),
                    rolled_back: false,
                },
                FeatureHistoryEntry {
                    object_id: "pocket-001".into(),
                    label: "Pocket".into(),
                    object_type: "PartDesign::Pocket".into(),
                    sequence_index: 3,
                    source_object_id: Some("sketch-001".into()),
                    role: "subtractive".into(),
                    suppressed: false,
                    active: false,
                    inactive_reason: Some("Inactive because the history marker is set before step 3.".into()),
                    rolled_back: true,
                },
            ],
        };

        let evaluation = DocumentEvaluationState::from_feature_history(&history, true, "bridge");

        assert_eq!(evaluation.total_features, 3);
        assert_eq!(evaluation.suppressed_count, 1);
        assert_eq!(evaluation.inactive_count, 1);
        assert_eq!(evaluation.rolled_back_count, 1);
        assert!(evaluation.history_marker_active);
        assert_eq!(evaluation.worker_mode, "bridge");
    }

    #[test]
    fn document_state_matches_document_identity() {
        let summary = DocumentSummary {
            document_id: "doc-demo-001".into(),
            display_name: "demo.FCStd".into(),
            workbench: "PartDesign".into(),
            file_path: Some("demo.FCStd".into()),
            dirty: false,
        };
        let history = FeatureHistoryResponse {
            document_id: "doc-demo-001".into(),
            entries: vec![],
        };
        let evaluation = DocumentEvaluationState::from_feature_history(&history, false, "bridge");

        let state = DocumentState::new(summary, history, evaluation);

        assert!(state.matches_document("doc-demo-001"));
        assert!(!state.matches_document("doc-other"));
    }

    #[test]
    fn workspace_state_remembers_recent_documents_and_sessions() {
        let mut workspace = DocumentWorkspaceState::default();
        workspace.remember_document(
            RecentDocumentEntry {
                file_path: "C:/models/demo.FCStd".into(),
                display_name: "demo.FCStd".into(),
                workbench: "PartDesign".into(),
                dirty: false,
            },
            WorkspaceSessionEntry {
                session_id: "doc-demo-001:C:/models/demo.FCStd".into(),
                document_id: "doc-demo-001".into(),
                display_name: "demo.FCStd".into(),
                file_path: "C:/models/demo.FCStd".into(),
                workbench: "PartDesign".into(),
                dirty: false,
                selected_object_id: Some("pad-001".into()),
                selection_mode: Some("object".into()),
                combo_view_tab: Some("model".into()),
                bottom_dock_tab: Some("report".into()),
                combo_view_visible: Some(true),
                report_dock_visible: Some(true),
                combo_view_size_hint: Some(0.28),
                report_dock_size_hint: Some(0.24),
            },
        );

        assert_eq!(workspace.recent_documents.len(), 1);
        assert_eq!(workspace.workspace_sessions.len(), 1);
        assert_eq!(workspace.recent_documents[0].file_path, "C:/models/demo.FCStd");
    }

    #[test]
    fn projects_bridge_snapshot_into_document_state_and_graph() {
        let snapshot = open_document_snapshot(None);
        let state = bridge_document_state(&snapshot, "mock-worker");

        assert_eq!(state.summary.document_id, "doc-demo-001");
        assert_eq!(state.evaluation.worker_mode, "mock-worker");
        assert!(state.graph.objects.iter().any(|object| object.object_id == "body-001"));
        assert!(state.graph.dependencies.iter().any(|edge| {
            edge.from_object_id == "sketch-001"
                && edge.to_object_id == "pad-001"
                && edge.relationship == "depends_on"
        }));
    }

    #[test]
    fn derives_bridge_object_dependency_state() {
        let mut snapshot = open_document_snapshot(None);
        snapshot.history_marker = Some(1);
        let pad = snapshot
            .roots
            .first()
            .and_then(|body| body.children.iter().find(|child| child.object_id == "pad-001"))
            .expect("pad should exist");

        let state = bridge_object_state(&snapshot, pad);

        assert!(!state.active);
        assert!(!state.suppressed);
        assert!(state
            .inactive_reason
            .expect("inactive reason")
            .contains("history marker"));

        let graph = document_graph_from_bridge(&snapshot);
        assert!(graph.objects.iter().any(|object| object.object_id == "pad-001"));
    }

    #[test]
    fn exposes_selection_mode_object_ids_from_bridge_snapshot() {
        let snapshot = open_document_snapshot(None);

        assert_eq!(selectable_object_ids_for_mode(&snapshot, "body"), vec!["body-001"]);
        assert_eq!(selectable_object_ids_for_mode(&snapshot, "sketch"), vec!["sketch-001"]);
        assert_eq!(selectable_object_ids_for_mode(&snapshot, "feature"), vec!["pad-001"]);
        assert!(object_matches_selection_mode("PartDesign::Pocket", "feature"));
        assert!(!object_matches_selection_mode("Sketcher::SketchObject", "feature"));
    }

    #[test]
    fn exposes_bridge_child_and_sketch_profile_helpers() {
        let snapshot = open_document_snapshot(None);
        let sketch = find_bridge_child(&snapshot, "sketch-001").expect("sketch should exist");

        assert_eq!(find_pad_length_mm(&snapshot, "pad-001"), Some(12.0));
        assert_eq!(sketch_constraint_summary(sketch), "6 constraints resolved");
        assert_eq!(sketch_profile_readiness(sketch), "Closed profile / fully constrained");
    }
}