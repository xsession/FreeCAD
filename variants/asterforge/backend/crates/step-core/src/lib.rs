use std::collections::BTreeMap;
use std::fs::File;
use std::path::{Path, PathBuf};
use std::sync::Arc;
use std::thread;

use anyhow::{anyhow, bail, Context, Result};
use memmap2::Mmap;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct ByteRange {
    pub start: usize,
    pub end: usize,
}

impl ByteRange {
    pub fn len(self) -> usize {
        self.end.saturating_sub(self.start)
    }

    pub fn is_empty(self) -> bool {
        self.start >= self.end
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum StepApplicationProtocol {
    Ap203,
    Ap214,
    Ap242,
    Unknown(String),
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct StepHeaderSection {
    pub source_path: Option<String>,
    pub implementation_level: Option<String>,
    pub file_name: Option<String>,
    pub file_descriptions: Vec<String>,
    pub schema_identifiers: Vec<String>,
    pub application_protocols: Vec<StepApplicationProtocol>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct StepEntitySpan {
    pub entity_id: u64,
    pub keyword: String,
    pub byte_range: ByteRange,
    pub references: Vec<u64>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct StepChunkSummary {
    pub chunk_id: usize,
    pub byte_range: ByteRange,
    pub entity_ids: Vec<u64>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ParsedStepEntity {
    pub entity_id: u64,
    pub keyword: String,
    pub raw_arguments: Vec<String>,
    pub references: Vec<u64>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ClosedShell {
    pub entity_id: u64,
    pub name: Option<String>,
    pub face_ids: Vec<u64>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ManifoldSolidBrep {
    pub entity_id: u64,
    pub name: Option<String>,
    pub outer_shell_id: u64,
}

impl TryFrom<&ParsedStepEntity> for ClosedShell {
    type Error = anyhow::Error;

    fn try_from(entity: &ParsedStepEntity) -> Result<Self> {
        if entity.keyword != "CLOSED_SHELL" {
            bail!("expected CLOSED_SHELL, got {}", entity.keyword);
        }
        if entity.raw_arguments.len() != 2 {
            bail!("CLOSED_SHELL expects 2 arguments, got {}", entity.raw_arguments.len());
        }

        Ok(Self {
            entity_id: entity.entity_id,
            name: parse_optional_step_string(&entity.raw_arguments[0]),
            face_ids: parse_entity_reference_list(&entity.raw_arguments[1])?,
        })
    }
}

impl TryFrom<&ParsedStepEntity> for ManifoldSolidBrep {
    type Error = anyhow::Error;

    fn try_from(entity: &ParsedStepEntity) -> Result<Self> {
        if entity.keyword != "MANIFOLD_SOLID_BREP" {
            bail!("expected MANIFOLD_SOLID_BREP, got {}", entity.keyword);
        }
        if entity.raw_arguments.len() != 2 {
            bail!(
                "MANIFOLD_SOLID_BREP expects 2 arguments, got {}",
                entity.raw_arguments.len()
            );
        }

        Ok(Self {
            entity_id: entity.entity_id,
            name: parse_optional_step_string(&entity.raw_arguments[0]),
            outer_shell_id: parse_entity_reference(&entity.raw_arguments[1])?,
        })
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct StepDocumentIndexDto {
    pub header: StepHeaderSection,
    pub chunks: Vec<StepChunkSummary>,
    pub entities: Vec<StepEntitySpan>,
}

#[derive(Debug, Clone, Copy)]
struct StepSectionRanges {
    header: ByteRange,
    data: ByteRange,
}

#[derive(Debug, Clone)]
struct ChunkPlan {
    chunk_id: usize,
    byte_range: ByteRange,
    record_ranges: Vec<ByteRange>,
}

#[derive(Debug)]
pub struct StepModelIndex {
    mmap: Arc<Mmap>,
    pub source_path: PathBuf,
    pub header: StepHeaderSection,
    pub chunks: Vec<StepChunkSummary>,
    pub entities: BTreeMap<u64, StepEntitySpan>,
}

impl StepModelIndex {
    pub fn to_dto(&self) -> StepDocumentIndexDto {
        StepDocumentIndexDto {
            header: self.header.clone(),
            chunks: self.chunks.clone(),
            entities: self.entities.values().cloned().collect(),
        }
    }

    pub fn load_entity(&self, entity_id: u64) -> Result<ParsedStepEntity> {
        let span = self
            .entities
            .get(&entity_id)
            .ok_or_else(|| anyhow!("unknown STEP entity #{entity_id}"))?;
        parse_step_entity_record(self.record_text(span.byte_range)?, span.byte_range)
    }

    fn record_text(&self, range: ByteRange) -> Result<&str> {
        std::str::from_utf8(&self.mmap[range.start..range.end])
            .with_context(|| format!("invalid UTF-8 in STEP record {}..{}", range.start, range.end))
    }
}

pub struct StepMappedFile {
    source_path: PathBuf,
    mmap: Arc<Mmap>,
    sections: StepSectionRanges,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum StepViewPreset {
    Iso,
    Front,
    Back,
    Right,
    Left,
    Top,
    Bottom,
}

impl StepViewPreset {
    pub fn preset_id(self) -> &'static str {
        match self {
            StepViewPreset::Iso => "iso",
            StepViewPreset::Front => "front",
            StepViewPreset::Back => "back",
            StepViewPreset::Right => "right",
            StepViewPreset::Left => "left",
            StepViewPreset::Top => "top",
            StepViewPreset::Bottom => "bottom",
        }
    }

    pub fn status_message(self) -> String {
        format!("Applied STEP {} view", self.preset_id())
    }
}

pub fn step_view_preset_from_command_id(command_id: &str) -> Option<StepViewPreset> {
    match command_id {
        "step.view_iso" => Some(StepViewPreset::Iso),
        "step.view_front" => Some(StepViewPreset::Front),
        "step.view_back" => Some(StepViewPreset::Back),
        "step.view_right" => Some(StepViewPreset::Right),
        "step.view_left" => Some(StepViewPreset::Left),
        "step.view_top" => Some(StepViewPreset::Top),
        "step.view_bottom" => Some(StepViewPreset::Bottom),
        _ => None,
    }
}

pub fn step_focus_selection_message(object_id: &str) -> String {
    format!("Focused STEP selection {object_id}")
}

pub fn step_view_reset_message() -> String {
    "Reset STEP view to the default inspection camera".into()
}

pub fn step_view_fit_all_message() -> String {
    "Fit all visible STEP geometry in the viewport".into()
}

pub fn step_selected_parent_message(object_id: &str) -> String {
    format!("Selected parent node {object_id}")
}

pub fn step_selected_child_message(object_id: &str) -> String {
    format!("Selected child node {object_id}")
}

pub fn step_pmi_loaded_status_message(label: &str, annotation_count: usize) -> String {
    format!("Loaded PMI inspection for {label} ({annotation_count} annotations)")
}

pub fn step_pmi_loaded_event_message(label: &str, entity_id: u64) -> String {
    format!("Loaded PMI inspection for {label} / #{entity_id}")
}

pub fn step_pmi_annotation_event_message(
    semantic_type: &str,
    text: &str,
    target_entity_ids: &[u64],
) -> String {
    format!(
        "{}: {} (targets: {})",
        semantic_type,
        text,
        target_entity_ids
            .iter()
            .map(|entity_id| format!("#{}", entity_id))
            .collect::<Vec<_>>()
            .join(", ")
    )
}

pub fn step_hidden_subtree_message(object_id: &str) -> String {
    format!("Hidden STEP subtree rooted at {object_id}")
}

pub fn step_measurement_message(label: &str, span_x: f32, span_y: f32, span_z: f32) -> String {
    format!("Measured {label} at {:.2} x {:.2} x {:.2}", span_x, span_y, span_z)
}

pub fn step_isolated_subtree_message(object_id: &str) -> String {
    format!("Isolated STEP subtree rooted at {object_id}")
}

pub fn step_show_all_message() -> String {
    "Restored all STEP nodes to the inspection viewport".into()
}

impl StepMappedFile {
    pub fn open(path: impl AsRef<Path>) -> Result<Self> {
        let source_path = path.as_ref().to_path_buf();
        let file = File::open(&source_path)
            .with_context(|| format!("failed to open STEP file {}", source_path.display()))?;
        let mmap = unsafe { Mmap::map(&file) }
            .with_context(|| format!("failed to memory-map STEP file {}", source_path.display()))?;
        let mmap = Arc::new(mmap);
        let sections = locate_step_sections(&mmap)?;

        Ok(Self {
            source_path,
            mmap,
            sections,
        })
    }

    pub fn build_index(&self, target_chunk_bytes: usize) -> Result<StepModelIndex> {
        let header = parse_header(&self.mmap, self.sections.header, &self.source_path)?;
        let record_ranges = collect_entity_record_ranges(&self.mmap, self.sections.data)?;
        let plans = plan_chunks(&record_ranges, target_chunk_bytes.max(1));

        let mapped_chunks = thread::scope(|scope| {
            let mut handles = Vec::with_capacity(plans.len());
            for plan in &plans {
                let bytes = Arc::clone(&self.mmap);
                let plan = plan.clone();
                handles.push(scope.spawn(move || parse_chunk(bytes.as_ref(), plan)));
            }

            let mut mapped = Vec::with_capacity(handles.len());
            for handle in handles {
                mapped.push(
                    handle
                        .join()
                        .map_err(|_| anyhow!("STEP parsing worker thread panicked"))?,
                );
            }

            Ok::<_, anyhow::Error>(mapped)
        })?;

        let mut chunks = Vec::with_capacity(plans.len());
        let mut entities = BTreeMap::new();
        for mapped_chunk in mapped_chunks {
            let (chunk_summary, local_entities) = mapped_chunk?;
            for entity in local_entities {
                if entities.insert(entity.entity_id, entity).is_some() {
                    bail!("duplicate STEP entity id found while reducing chunk results");
                }
            }
            chunks.push(chunk_summary);
        }

        Ok(StepModelIndex {
            mmap: Arc::clone(&self.mmap),
            source_path: self.source_path.clone(),
            header,
            chunks,
            entities,
        })
    }
}

fn locate_step_sections(bytes: &[u8]) -> Result<StepSectionRanges> {
    let text = std::str::from_utf8(bytes).context("STEP file is not valid UTF-8 compatible ASCII")?;
    let header_marker = text.find("HEADER;").context("STEP file is missing HEADER section")?;
    let data_marker = text.find("DATA;").context("STEP file is missing DATA section")?;
    let header_end = text[header_marker..data_marker]
        .find("ENDSEC;")
        .map(|offset| header_marker + offset)
        .context("STEP header section is missing ENDSEC")?;
    let data_end = text[data_marker..]
        .find("ENDSEC;")
        .map(|offset| data_marker + offset)
        .context("STEP data section is missing ENDSEC")?;

    Ok(StepSectionRanges {
        header: ByteRange {
            start: header_marker + "HEADER;".len(),
            end: header_end,
        },
        data: ByteRange {
            start: data_marker + "DATA;".len(),
            end: data_end,
        },
    })
}

fn parse_header(bytes: &[u8], range: ByteRange, source_path: &Path) -> Result<StepHeaderSection> {
    let text = std::str::from_utf8(&bytes[range.start..range.end]).context("STEP header is not valid UTF-8")?;
    let file_descriptions = extract_header_list_argument(text, "FILE_DESCRIPTION", 0).unwrap_or_default();
    let implementation_level = extract_header_argument(text, "FILE_DESCRIPTION", 1);
    let file_name = extract_header_argument(text, "FILE_NAME", 0);
    let schema_identifiers = extract_header_list_argument(text, "FILE_SCHEMA", 0).unwrap_or_default();
    let application_protocols = classify_protocols(&schema_identifiers);

    Ok(StepHeaderSection {
        source_path: Some(source_path.display().to_string()),
        implementation_level,
        file_name,
        file_descriptions,
        schema_identifiers,
        application_protocols,
    })
}

fn extract_header_argument(section: &str, function_name: &str, index: usize) -> Option<String> {
    let args = extract_function_arguments(section, function_name)?;
    split_top_level_arguments(&args)
        .get(index)
        .and_then(|value| parse_optional_step_string(value))
}

fn extract_header_list_argument(section: &str, function_name: &str, index: usize) -> Option<Vec<String>> {
    let args = extract_function_arguments(section, function_name)?;
    let values = split_top_level_arguments(&args);
    let list = values.get(index)?;
    let list = strip_wrapping_parens(list.trim())?;

    Some(
        split_top_level_arguments(list)
            .into_iter()
            .filter_map(|value| parse_optional_step_string(&value))
            .collect(),
    )
}

fn extract_function_arguments(section: &str, function_name: &str) -> Option<String> {
    let marker = format!("{function_name}(");
    let start = section.find(&marker)? + marker.len();
    let end = find_matching_paren(section, start - 1)?;
    Some(section[start..end].trim().to_string())
}

fn find_matching_paren(text: &str, open_index: usize) -> Option<usize> {
    let bytes = text.as_bytes();
    let mut depth = 0usize;
    let mut in_string = false;
    let mut index = open_index;

    while index < bytes.len() {
        match bytes[index] {
            b'\'' => {
                if in_string && index + 1 < bytes.len() && bytes[index + 1] == b'\'' {
                    index += 1;
                }
                else {
                    in_string = !in_string;
                }
            }
            b'(' if !in_string => depth += 1,
            b')' if !in_string => {
                depth = depth.saturating_sub(1);
                if depth == 0 {
                    return Some(index);
                }
            }
            _ => {}
        }
        index += 1;
    }

    None
}

fn classify_protocols(schema_identifiers: &[String]) -> Vec<StepApplicationProtocol> {
    let mut protocols = Vec::new();

    for schema in schema_identifiers {
        let normalized = schema.trim().to_ascii_uppercase();
        let protocol = if normalized.contains("AP242")
            || normalized.contains("MANAGED_MODEL_BASED_3D_ENGINEERING")
        {
            StepApplicationProtocol::Ap242
        }
        else if normalized.contains("AP214") || normalized.contains("AUTOMOTIVE_DESIGN") {
            StepApplicationProtocol::Ap214
        }
        else if normalized.contains("AP203") || normalized.contains("CONFIG_CONTROL_DESIGN") {
            StepApplicationProtocol::Ap203
        }
        else {
            StepApplicationProtocol::Unknown(schema.clone())
        };

        if !protocols.contains(&protocol) {
            protocols.push(protocol);
        }
    }

    protocols
}

fn collect_entity_record_ranges(bytes: &[u8], range: ByteRange) -> Result<Vec<ByteRange>> {
    let mut cursor = range.start;
    let mut records = Vec::new();

    while cursor < range.end {
        let Some(record_start) = find_next_entity_start(bytes, cursor, range.end) else {
            break;
        };
        let record_end = find_record_terminator(bytes, record_start, range.end)
            .with_context(|| format!("unterminated STEP entity starting at byte {record_start}"))?;
        records.push(ByteRange {
            start: record_start,
            end: record_end,
        });
        cursor = record_end;
    }

    Ok(records)
}

fn find_next_entity_start(bytes: &[u8], mut cursor: usize, end: usize) -> Option<usize> {
    while cursor < end {
        if bytes[cursor] == b'#' {
            let mut lookahead = cursor + 1;
            while lookahead < end && bytes[lookahead].is_ascii_digit() {
                lookahead += 1;
            }
            if lookahead > cursor + 1 {
                let mut separator = lookahead;
                while separator < end && bytes[separator].is_ascii_whitespace() {
                    separator += 1;
                }
                if separator < end && bytes[separator] == b'=' {
                    return Some(cursor);
                }
            }
        }
        cursor += 1;
    }
    None
}

fn find_record_terminator(bytes: &[u8], mut cursor: usize, end: usize) -> Option<usize> {
    let mut in_string = false;
    while cursor < end {
        match bytes[cursor] {
            b'\'' => {
                if in_string && cursor + 1 < end && bytes[cursor + 1] == b'\'' {
                    cursor += 1;
                }
                else {
                    in_string = !in_string;
                }
            }
            b';' if !in_string => return Some(cursor + 1),
            _ => {}
        }
        cursor += 1;
    }
    None
}

fn plan_chunks(record_ranges: &[ByteRange], target_chunk_bytes: usize) -> Vec<ChunkPlan> {
    if record_ranges.is_empty() {
        return vec![ChunkPlan {
            chunk_id: 0,
            byte_range: ByteRange { start: 0, end: 0 },
            record_ranges: Vec::new(),
        }];
    }

    let mut plans = Vec::new();
    let mut current = Vec::new();
    let mut current_start = record_ranges[0].start;
    let mut current_end = current_start;

    for range in record_ranges {
        if !current.is_empty() && range.end.saturating_sub(current_start) > target_chunk_bytes {
            plans.push(ChunkPlan {
                chunk_id: plans.len(),
                byte_range: ByteRange {
                    start: current_start,
                    end: current_end,
                },
                record_ranges: current,
            });
            current = Vec::new();
            current_start = range.start;
        }

        current_end = range.end;
        current.push(*range);
    }

    if !current.is_empty() {
        plans.push(ChunkPlan {
            chunk_id: plans.len(),
            byte_range: ByteRange {
                start: current_start,
                end: current_end,
            },
            record_ranges: current,
        });
    }

    plans
}

fn parse_chunk(bytes: &[u8], plan: ChunkPlan) -> Result<(StepChunkSummary, Vec<StepEntitySpan>)> {
    let mut entity_ids = Vec::with_capacity(plan.record_ranges.len());
    let mut entities = Vec::with_capacity(plan.record_ranges.len());

    for range in &plan.record_ranges {
        let text = std::str::from_utf8(&bytes[range.start..range.end])
            .with_context(|| format!("invalid UTF-8 in STEP chunk {}", plan.chunk_id))?;
        let parsed = parse_step_entity_record(text, *range)?;
        entity_ids.push(parsed.entity_id);
        entities.push(StepEntitySpan {
            entity_id: parsed.entity_id,
            keyword: parsed.keyword,
            byte_range: *range,
            references: parsed.references,
        });
    }

    Ok((
        StepChunkSummary {
            chunk_id: plan.chunk_id,
            byte_range: plan.byte_range,
            entity_ids,
        },
        entities,
    ))
}

fn parse_step_entity_record(record_text: &str, range: ByteRange) -> Result<ParsedStepEntity> {
    let text = record_text.trim();
    let equals = text.find('=').context("STEP record is missing '='")?;
    let entity_id = text[1..equals]
        .trim()
        .parse::<u64>()
        .with_context(|| format!("invalid STEP entity id in range {}..{}", range.start, range.end))?;

    let rhs = text[equals + 1..].trim_end_matches(';').trim();
    let open_paren = rhs.find('(').context("STEP entity is missing '(' after keyword")?;
    let close_paren = rhs.rfind(')').context("STEP entity is missing closing ')' ")?;
    let keyword = rhs[..open_paren].trim().to_ascii_uppercase();
    let raw_arguments = split_top_level_arguments(&rhs[open_paren + 1..close_paren]);
    let references = extract_entity_references(rhs);

    Ok(ParsedStepEntity {
        entity_id,
        keyword,
        raw_arguments,
        references,
    })
}

fn extract_entity_references(text: &str) -> Vec<u64> {
    let bytes = text.as_bytes();
    let mut references = Vec::new();
    let mut index = 0usize;

    while index < bytes.len() {
        if bytes[index] == b'#' {
            let start = index + 1;
            let mut end = start;
            while end < bytes.len() && bytes[end].is_ascii_digit() {
                end += 1;
            }
            if end > start {
                if let Ok(reference) = text[start..end].parse::<u64>() {
                    references.push(reference);
                }
                index = end;
                continue;
            }
        }
        index += 1;
    }

    references
}

fn split_top_level_arguments(text: &str) -> Vec<String> {
    let bytes = text.as_bytes();
    let mut values = Vec::new();
    let mut current = String::new();
    let mut depth = 0usize;
    let mut in_string = false;
    let mut index = 0usize;

    while index < bytes.len() {
        match bytes[index] {
            b'\'' => {
                current.push('\'');
                if in_string && index + 1 < bytes.len() && bytes[index + 1] == b'\'' {
                    current.push('\'');
                    index += 1;
                }
                else {
                    in_string = !in_string;
                }
            }
            b'(' if !in_string => {
                depth += 1;
                current.push('(');
            }
            b')' if !in_string => {
                depth = depth.saturating_sub(1);
                current.push(')');
            }
            b',' if !in_string && depth == 0 => {
                values.push(current.trim().to_string());
                current.clear();
            }
            byte => current.push(byte as char),
        }
        index += 1;
    }

    if !current.trim().is_empty() {
        values.push(current.trim().to_string());
    }

    values
}

fn parse_optional_step_string(token: &str) -> Option<String> {
    let trimmed = token.trim();
    if trimmed == "$" || trimmed == "*" {
        return None;
    }
    if trimmed.starts_with('\'') && trimmed.ends_with('\'') && trimmed.len() >= 2 {
        return Some(trimmed[1..trimmed.len() - 1].replace("''", "'"));
    }

    Some(trimmed.to_string())
}

fn parse_entity_reference(token: &str) -> Result<u64> {
    let trimmed = token.trim();
    let digits = trimmed
        .strip_prefix('#')
        .ok_or_else(|| anyhow!("expected STEP entity reference, got {trimmed}"))?;
    digits
        .parse::<u64>()
        .with_context(|| format!("invalid STEP entity reference {trimmed}"))
}

fn parse_entity_reference_list(token: &str) -> Result<Vec<u64>> {
    let list = strip_wrapping_parens(token.trim())
        .ok_or_else(|| anyhow!("expected STEP entity reference list, got {token}"))?;
    split_top_level_arguments(list)
        .into_iter()
        .map(|value| parse_entity_reference(&value))
        .collect()
}

fn strip_wrapping_parens(token: &str) -> Option<&str> {
    let trimmed = token.trim();
    if trimmed.starts_with('(') && trimmed.ends_with(')') && trimmed.len() >= 2 {
        Some(&trimmed[1..trimmed.len() - 1])
    }
    else {
        None
    }
}

#[cfg(test)]
mod tests {
    use super::{
        step_focus_selection_message, step_measurement_message,
        step_pmi_annotation_event_message, step_pmi_loaded_event_message,
        step_pmi_loaded_status_message, step_selected_child_message,
        step_selected_parent_message, step_show_all_message,
        step_view_preset_from_command_id, step_view_reset_message,
        ClosedShell, ManifoldSolidBrep, StepApplicationProtocol, StepMappedFile,
        StepViewPreset,
    };
    use std::fs;
    use std::path::PathBuf;
    use std::time::{SystemTime, UNIX_EPOCH};

    fn write_temp_step_file(contents: &str) -> PathBuf {
        let stamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("time should move forward")
            .as_nanos();
        let path = std::env::temp_dir().join(format!("asterforge-step-core-{stamp}.stp"));
        fs::write(&path, contents).expect("temp STEP file should be written");
        path
    }

    #[test]
    fn builds_parallel_index_and_lazy_loads_entities() {
        let sample = r#"ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('demo import'),'2;1');
FILE_NAME('demo.stp','2026-05-01T00:00:00',('Copilot'),('OpenAI'),'','AsterForge','');
FILE_SCHEMA(('AP242_MANAGED_MODEL_BASED_3D_ENGINEERING_MIM_LF'));
ENDSEC;
DATA;
#10=CLOSED_SHELL('Outer Shell',(#11,#12));
#11=ADVANCED_FACE('',(),$,.T.);
#12=ADVANCED_FACE('',(),$,.F.);
#20=MANIFOLD_SOLID_BREP('Block',#10);
ENDSEC;
END-ISO-10303-21;
"#;

        let path = write_temp_step_file(sample);
        let mapped = StepMappedFile::open(&path).expect("mmap open should succeed");
        let index = mapped.build_index(32).expect("index build should succeed");

        assert_eq!(index.header.file_name.as_deref(), Some("demo.stp"));
        assert!(index
            .header
            .application_protocols
            .contains(&StepApplicationProtocol::Ap242));
        assert_eq!(index.entities.len(), 4);
        assert!(index.chunks.len() >= 2);

        let shell = index.load_entity(10).expect("entity 10 should load");
        let shell = ClosedShell::try_from(&shell).expect("entity 10 should decode as CLOSED_SHELL");
        assert_eq!(shell.name.as_deref(), Some("Outer Shell"));
        assert_eq!(shell.face_ids, vec![11, 12]);

        let brep = index.load_entity(20).expect("entity 20 should load");
        let brep = ManifoldSolidBrep::try_from(&brep)
            .expect("entity 20 should decode as MANIFOLD_SOLID_BREP");
        assert_eq!(brep.outer_shell_id, 10);

        let _ = fs::remove_file(path);
    }

    #[test]
    fn produces_serializable_index_dto() {
        let sample = r#"ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('demo export'),'2;1');
FILE_NAME('assembly.stp','2026-05-01T00:00:00',('Copilot'),('OpenAI'),'','AsterForge','');
FILE_SCHEMA(('CONFIG_CONTROL_DESIGN','AUTOMOTIVE_DESIGN','AP242_MANAGED_MODEL_BASED_3D_ENGINEERING_MIM_LF'));
ENDSEC;
DATA;
#42=CLOSED_SHELL('Faces',(#11,#12,#13));
#100=MANIFOLD_SOLID_BREP('Housing',#42);
ENDSEC;
END-ISO-10303-21;
"#;

        let path = write_temp_step_file(sample);
        let mapped = StepMappedFile::open(&path).expect("mmap open should succeed");
        let index = mapped.build_index(64).expect("index build should succeed");
        let dto = index.to_dto();

        assert_eq!(dto.entities.len(), 2);
        assert!(dto
            .header
            .application_protocols
            .contains(&StepApplicationProtocol::Ap203));
        assert!(dto
            .header
            .application_protocols
            .contains(&StepApplicationProtocol::Ap214));
        assert!(dto
            .header
            .application_protocols
            .contains(&StepApplicationProtocol::Ap242));

        let _ = fs::remove_file(path);
    }

    #[test]
    fn exposes_step_shell_preset_and_message_helpers() {
        assert_eq!(
            step_view_preset_from_command_id("step.view_iso"),
            Some(StepViewPreset::Iso)
        );
        assert_eq!(StepViewPreset::Top.preset_id(), "top");
        assert_eq!(StepViewPreset::Back.status_message(), "Applied STEP back view");
        assert_eq!(step_view_reset_message(), "Reset STEP view to the default inspection camera");
        assert_eq!(step_focus_selection_message("node-7"), "Focused STEP selection node-7");
        assert_eq!(step_selected_parent_message("asm-1"), "Selected parent node asm-1");
        assert_eq!(step_selected_child_message("part-9"), "Selected child node part-9");
        assert_eq!(step_show_all_message(), "Restored all STEP nodes to the inspection viewport");
    }

    #[test]
    fn formats_step_measurement_and_pmi_messages() {
        assert_eq!(
            step_measurement_message("Bracket", 10.0, 20.25, 30.5),
            "Measured Bracket at 10.00 x 20.25 x 30.50"
        );
        assert_eq!(
            step_pmi_loaded_status_message("Housing", 3),
            "Loaded PMI inspection for Housing (3 annotations)"
        );
        assert_eq!(
            step_pmi_loaded_event_message("Housing", 42),
            "Loaded PMI inspection for Housing / #42"
        );
        assert_eq!(
            step_pmi_annotation_event_message("datum", "A", &[10, 20]),
            "datum: A (targets: #10, #20)"
        );
    }
}