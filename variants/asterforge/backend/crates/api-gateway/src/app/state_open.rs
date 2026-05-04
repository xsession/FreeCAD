use asterforge_document_core::DocumentSummary;
use asterforge_freecad_bridge::BridgeDocumentSnapshot;

use super::services::AppServices;
use super::state_types::AppModel;
use crate::domain::{BackendEvent, JobStageEntry, JobStatusEntry, extension_compatibility_state};

pub(super) fn apply_open_document(
    services: &AppServices,
    correlation_id: &str,
    model: &mut AppModel,
    file_path: &str,
    snapshot: BridgeDocumentSnapshot,
) -> DocumentSummary {
    model.bridge_snapshot = snapshot;
    model.preselected_object_id = None;
    model.step_cache_by_document.clear();
    model.step_pmi_inspection_by_document.clear();
    model.step_measurement_by_document.clear();
    model.step_viewport_camera_by_document.clear();
    model.extension_compatibility = extension_compatibility_state();
    model.sync_from_snapshot(services, correlation_id);
    let document_id = model.document.document_id.clone();
    model.apply_step_projection_for_active_document(&document_id);
    model.remember_current_document(services);

    let open_stages = open_document_stages(model.is_step_document());
    let next_job_id = format!("job-{}-document.open", model.jobs.len() + 1);
    model.jobs.insert(
        0,
        JobStatusEntry {
            job_id: next_job_id,
            title: "Open document".into(),
            command_id: "document.open".into(),
            state: "completed".into(),
            progress_percent: 100,
            detail: format!("Opened {}", file_path),
            object_id: None,
            stages: open_stages.clone(),
        },
    );
    model.jobs.truncate(8);

    for stage in open_stages {
        model.events.insert(
            0,
            BackendEvent {
                topic: if stage.progress_percent < 100 {
                    "worker_lifecycle".into()
                } else {
                    "document_changed".into()
                },
                level: "info".into(),
                message: format!("document.open: {}", stage.label),
                document_id: document_id.clone(),
                object_id: None,
            },
        );
    }
    model.events.insert(
        0,
        BackendEvent {
            topic: "document_changed".into(),
            level: "info".into(),
            message: format!("Opened {}", file_path),
            document_id,
            object_id: None,
        },
    );

    model.document.summary().clone()
}

fn open_document_stages(is_step_document: bool) -> Vec<JobStageEntry> {
    let load_label = if is_step_document {
        "Read STEP Part 21 payload"
    } else {
        "Read FCStd payload"
    };

    vec![
        JobStageEntry {
            stage_id: "queued".into(),
            label: "Queued by shell".into(),
            state: "completed".into(),
            progress_percent: 15,
        },
        JobStageEntry {
            stage_id: "read_document".into(),
            label: load_label.into(),
            state: "completed".into(),
            progress_percent: 55,
        },
        JobStageEntry {
            stage_id: "hydrate_backend".into(),
            label: "Hydrate backend state".into(),
            state: "completed".into(),
            progress_percent: 82,
        },
        JobStageEntry {
            stage_id: "completed".into(),
            label: "Document ready".into(),
            state: "completed".into(),
            progress_percent: 100,
        },
    ]
}

#[cfg(test)]
mod tests {
    use super::open_document_stages;

    #[test]
    fn open_document_stages_use_fcstd_label_for_native_documents() {
        let stages = open_document_stages(false);

        assert_eq!(stages[1].stage_id, "read_document");
        assert_eq!(stages[1].label, "Read FCStd payload");
    }

    #[test]
    fn open_document_stages_use_step_label_for_step_documents() {
        let stages = open_document_stages(true);

        assert_eq!(stages[1].stage_id, "read_document");
        assert_eq!(stages[1].label, "Read STEP Part 21 payload");
    }
}