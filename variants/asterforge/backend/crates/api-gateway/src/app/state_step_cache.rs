use std::path::{Path, PathBuf};

use anyhow::Context;
use asterforge_step_core::{
    ClosedShell as StepClosedShell, ManifoldSolidBrep as StepManifoldSolidBrep, StepMappedFile,
};

use crate::domain::{step_document_index_from_parsed, step_scene_bundle_from_parsed};

use super::{
    state::STEP_OBJECT_MODE,
    state_model::flatten_object_nodes,
    state_properties,
    state_types::{AppModel, StepCacheEntry},
};

pub(super) fn resolve_step_cache(
    model: &mut AppModel,
    document_id: &str,
) -> anyhow::Result<Option<StepCacheEntry>> {
    if model.document.document_id != document_id {
        return Ok(None);
    }

    let Some(source_path) = step_source_path(&model.document.file_path) else {
        model.step_cache_by_document.remove(document_id);
        return Ok(None);
    };

    if let Some(cached) = model.step_cache_by_document.get(document_id) {
        if cached.source_path == source_path {
            return Ok(Some(cached.clone()));
        }
    }

    let cache_entry = load_step_bundle_from_path(&source_path)?;
    model
        .step_cache_by_document
        .insert(document_id.to_string(), cache_entry.clone());
    Ok(Some(cache_entry))
}

pub(super) fn is_step_document(model: &AppModel) -> bool {
    step_source_path(&model.document.file_path).is_some()
}

pub(super) fn apply_step_projection_for_active_document(model: &mut AppModel, document_id: &str) {
    let Ok(Some(cache)) = resolve_step_cache(model, document_id) else {
        return;
    };

    model.selection_mode = STEP_OBJECT_MODE.into();
    model.object_tree = state_properties::step_object_tree_from_cache(&cache);
    model.properties_by_object = state_properties::step_property_map_from_cache(&cache, &model.object_tree);

    if !model.properties_by_object.contains_key(&model.selected_object_id) {
        if let Some(first_node) = flatten_object_nodes(&model.object_tree).first() {
            model.selected_object_id = first_node.object_id.clone();
        }
    }
}

fn load_step_bundle_from_path(source_path: &Path) -> anyhow::Result<StepCacheEntry> {
    let mapped = StepMappedFile::open(source_path)
        .with_context(|| format!("failed to open STEP source {}", source_path.display()))?;
    let model_index = mapped
        .build_index(96)
        .with_context(|| format!("failed to index STEP source {}", source_path.display()))?;
    let dto = model_index.to_dto();
    let mut shells = Vec::new();
    let mut breps = Vec::new();

    for entity_id in model_index.entities.keys().copied() {
        let entity = model_index
            .load_entity(entity_id)
            .with_context(|| format!("failed to load STEP entity #{entity_id}"))?;
        if let Ok(shell) = StepClosedShell::try_from(&entity) {
            shells.push(shell);
            continue;
        }
        if let Ok(brep) = StepManifoldSolidBrep::try_from(&entity) {
            breps.push(brep);
        }
    }

    Ok(StepCacheEntry {
        source_path: source_path.to_path_buf(),
        document_index: step_document_index_from_parsed(&dto, &breps, &shells),
        scene_bundle: step_scene_bundle_from_parsed(&dto, &breps, &shells),
    })
}

fn step_source_path(file_path: &Option<String>) -> Option<PathBuf> {
    let candidate = PathBuf::from(file_path.as_ref()?);
    let extension = candidate
        .extension()
        .and_then(|value| value.to_str())
        .map(|value| value.to_ascii_lowercase())?;

    ["stp", "step", "p21"].contains(&extension.as_str()).then_some(candidate)
}