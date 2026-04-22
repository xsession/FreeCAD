use std::ops::{Deref, DerefMut};

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
    use super::{
        DocumentEvaluationState, DocumentState, DocumentSummary, FeatureHistoryEntry,
        FeatureHistoryResponse,
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
}