use crate::{
    bridge_runtime_descriptor, create_pad_from_selected_sketch, create_pocket_from_selected_sketch,
    create_sketch_in_body, load_prototype_bridge_session, open_document_snapshot, parse_bool_flag,
    resume_full_history, rollback_history_to_selected, sync_prototype_bridge_session,
    toggle_selected_suppression, update_selected_pad_profile, update_selected_pocket_profile,
    BridgeCommandRequest, BridgeCommandResponse, BridgeDocumentSnapshot, BridgeError,
    BridgeOperationResult, BridgeSessionRequest, BridgeSessionResponse, BridgeViewportRequest,
    FreecadBridgeContract, NativeSessionToken, ViewportSnapshot,
};

#[derive(Debug, Default, Clone, Copy)]
pub struct PrototypeFreecadBridge;

impl FreecadBridgeContract for PrototypeFreecadBridge {
    fn describe_runtime(&self) -> BridgeOperationResult<crate::BridgeRuntimeDescriptor> {
        tracing::debug!("describing prototype bridge runtime");
        Ok(bridge_runtime_descriptor())
    }

    fn open_document_session(
        &self,
        request: BridgeSessionRequest,
    ) -> BridgeOperationResult<BridgeSessionResponse> {
        tracing::info!(correlation_id = ?request.options.correlation_id, session_id = %request.session_id, source_path = ?request.source_path, "opening prototype bridge document session");
        let snapshot = open_document_snapshot(request.source_path.as_deref());
        let token = NativeSessionToken {
            session_id: request.session_id,
            native_document_token: format!("mock:{}", snapshot.document_id),
        };
        sync_prototype_bridge_session(&token.session_id, &snapshot);

        Ok(BridgeSessionResponse {
            document_id: snapshot.document_id.clone(),
            display_name: snapshot.display_name.clone(),
            file_path: snapshot.file_path.clone(),
            dirty: snapshot.dirty,
            workbench: snapshot.workbench.clone(),
            token,
        })
    }

    fn execute_command(
        &self,
        request: BridgeCommandRequest,
    ) -> BridgeOperationResult<BridgeCommandResponse> {
        tracing::info!(correlation_id = ?request.options.correlation_id, session_id = %request.session_id, command_id = %request.command_id, target_object_id = ?request.target_object_id, "executing prototype bridge command");
        let mut snapshot = load_prototype_bridge_session(&request.session_id).ok_or_else(|| {
            tracing::warn!(
                correlation_id = ?request.options.correlation_id,
                session_id = %request.session_id,
                command_id = %request.command_id,
                "prototype bridge session missing during command execution"
            );
            session_not_found_error(
                &request.session_id,
                request.options.correlation_id.clone(),
                "Open or synchronize the prototype bridge session before executing commands.",
            )
        })?;

        let response = execute_prototype_command_on_snapshot(&mut snapshot, &request)?;
        sync_prototype_bridge_session(&request.session_id, &snapshot);
        tracing::debug!(correlation_id = ?request.options.correlation_id, command_id = %response.command_id, accepted = response.accepted, "prototype bridge command completed");
        Ok(response)
    }

    fn fetch_viewport(
        &self,
        request: BridgeViewportRequest,
    ) -> BridgeOperationResult<ViewportSnapshot> {
        tracing::debug!(correlation_id = ?request.options.correlation_id, session_id = %request.session_id, object_count = request.object_ids.len(), "fetching prototype bridge viewport");
        let snapshot = load_prototype_bridge_session(&request.session_id).ok_or_else(|| {
            session_not_found_error(
                &request.session_id,
                request.options.correlation_id.clone(),
                "Open or synchronize the prototype bridge session before fetching viewport data.",
            )
        })?;

        if request.object_ids.is_empty() {
            return Ok(snapshot.viewport);
        }

        let drawables = snapshot
            .viewport
            .drawables
            .into_iter()
            .filter(|drawable| request.object_ids.iter().any(|id| id == &drawable.object_id))
            .collect();

        Ok(ViewportSnapshot {
            camera: snapshot.viewport.camera,
            drawables,
        })
    }
}

pub fn execute_prototype_command_on_snapshot(
    snapshot: &mut BridgeDocumentSnapshot,
    request: &BridgeCommandRequest,
) -> BridgeOperationResult<BridgeCommandResponse> {
    if let Some(target_object_id) = request
        .target_object_id
        .as_deref()
        .map(str::trim)
        .filter(|value| !value.is_empty())
    {
        snapshot.selected_object_id = target_object_id.to_string();
    }

    match request.command_id.as_str() {
        "document.save" => Ok(BridgeCommandResponse {
            command_id: request.command_id.clone(),
            accepted: {
                snapshot.dirty = false;
                true
            },
            status_message: "Document marked as saved".into(),
            document_dirty: snapshot.dirty,
            changed_object_ids: vec![],
            history_marker: snapshot.history_marker,
        }),
        "document.recompute" => Ok(BridgeCommandResponse {
            command_id: request.command_id.clone(),
            accepted: {
                snapshot.dirty = true;
                true
            },
            status_message: "Recompute queued through bridge-backed mock backend".into(),
            document_dirty: snapshot.dirty,
            changed_object_ids: vec![],
            history_marker: snapshot.history_marker,
        }),
        "selection.focus" => Ok(BridgeCommandResponse {
            command_id: request.command_id.clone(),
            accepted: true,
            status_message: "Selection focus requested".into(),
            document_dirty: snapshot.dirty,
            changed_object_ids: vec![],
            history_marker: snapshot.history_marker,
        }),
        "history.rollback_here" => {
            if let Some((object_id, sequence_index)) = rollback_history_to_selected(snapshot) {
                Ok(BridgeCommandResponse {
                    command_id: request.command_id.clone(),
                    accepted: true,
                    status_message: format!(
                        "Rolled back model evaluation to {} at step {}",
                        object_id, sequence_index
                    ),
                    document_dirty: snapshot.dirty,
                    changed_object_ids: vec![object_id],
                    history_marker: snapshot.history_marker,
                })
            } else {
                Ok(rejected_response(
                    snapshot,
                    request,
                    "Rollback requires a selected history feature",
                ))
            }
        }
        "history.resume_full" => {
            if resume_full_history(snapshot) {
                Ok(BridgeCommandResponse {
                    command_id: request.command_id.clone(),
                    accepted: true,
                    status_message: "Restored full feature history".into(),
                    document_dirty: snapshot.dirty,
                    changed_object_ids: vec![],
                    history_marker: snapshot.history_marker,
                })
            } else {
                Ok(rejected_response(
                    snapshot,
                    request,
                    "Feature history is already fully resumed",
                ))
            }
        }
        "model.toggle_suppression" => {
            if let Some((object_id, suppressed)) = toggle_selected_suppression(snapshot) {
                Ok(BridgeCommandResponse {
                    command_id: request.command_id.clone(),
                    accepted: true,
                    status_message: if suppressed {
                        format!("Suppressed {}", object_id)
                    } else {
                        format!("Unsuppressed {}", object_id)
                    },
                    document_dirty: snapshot.dirty,
                    changed_object_ids: vec![object_id],
                    history_marker: snapshot.history_marker,
                })
            } else {
                Ok(rejected_response(
                    snapshot,
                    request,
                    "Suppression requires a non-body selection",
                ))
            }
        }
        "partdesign.new_sketch" => {
            let requested_label = request.arguments.get("sketch_label").map(String::as_str);
            let reference_plane = request.arguments.get("reference_plane").map(String::as_str);
            if create_sketch_in_body(snapshot, requested_label, reference_plane).is_some() {
                Ok(BridgeCommandResponse {
                    command_id: request.command_id.clone(),
                    accepted: true,
                    status_message: format!(
                        "Created a new sketch in the active body on {}: {}",
                        reference_plane.unwrap_or("XY"),
                        snapshot.selected_object_id,
                    ),
                    document_dirty: snapshot.dirty,
                    changed_object_ids: vec![snapshot.selected_object_id.clone()],
                    history_marker: snapshot.history_marker,
                })
            } else {
                Ok(rejected_response(
                    snapshot,
                    request,
                    "Sketch creation requires the body to be selected",
                ))
            }
        }
        "partdesign.edit_pocket" => {
            let parsed_depth = request
                .arguments
                .get("depth_mm")
                .and_then(|value| value.parse::<f32>().ok());
            let parsed_extent_mode = request.arguments.get("extent_mode").map(String::as_str);
            let normalized_depth = parsed_depth.filter(|value| *value > 0.0);
            let selected_object_id = snapshot.selected_object_id.clone();
            let updated = update_selected_pocket_profile(snapshot, normalized_depth, parsed_extent_mode);

            let response = if selected_object_id.starts_with("pocket-") && updated.is_some() {
                BridgeCommandResponse {
                    command_id: request.command_id.clone(),
                    accepted: true,
                    status_message: format!(
                        "Updated {} to {:.2} mm depth ({})",
                        selected_object_id,
                        parsed_depth.unwrap_or(0.0),
                        parsed_extent_mode.unwrap_or("dimension")
                    ),
                    document_dirty: snapshot.dirty,
                    changed_object_ids: vec![selected_object_id],
                    history_marker: snapshot.history_marker,
                }
            } else if snapshot.selected_object_id.starts_with("pocket-") {
                rejected_response(
                    snapshot,
                    request,
                    "Pocket editing requires a positive depth_mm argument",
                )
            } else {
                rejected_response(
                    snapshot,
                    request,
                    "Pocket editing requires an active pocket selection",
                )
            };
            Ok(response)
        }
        "partdesign.edit_pad" => {
            let parsed_length = request
                .arguments
                .get("length_mm")
                .and_then(|value| value.parse::<f32>().ok());
            let parsed_midplane = request
                .arguments
                .get("midplane")
                .and_then(|value| parse_bool_flag(value));
            let normalized_length = parsed_length.filter(|value| *value > 0.0);
            let selected_object_id = snapshot.selected_object_id.clone();
            let updated = update_selected_pad_profile(snapshot, normalized_length, parsed_midplane);

            let response = if updated.is_some() {
                BridgeCommandResponse {
                    command_id: request.command_id.clone(),
                    accepted: true,
                    status_message: format!(
                        "Updated {} to {:.2} mm ({})",
                        selected_object_id,
                        parsed_length.unwrap_or(0.0),
                        if parsed_midplane.unwrap_or(false) {
                            "symmetric"
                        } else {
                            "one-sided"
                        }
                    ),
                    document_dirty: snapshot.dirty,
                    changed_object_ids: vec![selected_object_id],
                    history_marker: snapshot.history_marker,
                }
            } else if snapshot.selected_object_id.starts_with("pad-") {
                rejected_response(
                    snapshot,
                    request,
                    "Pad editing requires a positive length_mm argument",
                )
            } else {
                rejected_response(
                    snapshot,
                    request,
                    "Pad editing requires an active pad selection",
                )
            };
            Ok(response)
        }
        "partdesign.pocket" => {
            let parsed_depth = request
                .arguments
                .get("depth_mm")
                .and_then(|value| value.parse::<f32>().ok());
            let parsed_extent_mode = request.arguments.get("extent_mode").map(String::as_str);
            if create_pocket_from_selected_sketch(snapshot, parsed_depth, parsed_extent_mode).is_some() {
                Ok(BridgeCommandResponse {
                    command_id: request.command_id.clone(),
                    accepted: true,
                    status_message: format!(
                        "Created a new pocket feature from the selected sketch ({})",
                        parsed_extent_mode.unwrap_or("dimension")
                    ),
                    document_dirty: snapshot.dirty,
                    changed_object_ids: vec![snapshot.selected_object_id.clone()],
                    history_marker: snapshot.history_marker,
                })
            } else {
                Ok(rejected_response(
                    snapshot,
                    request,
                    "Pocket creation requires an active sketch selection",
                ))
            }
        }
        "partdesign.pad" => {
            let parsed_length = request
                .arguments
                .get("length_mm")
                .and_then(|value| value.parse::<f32>().ok());
            let parsed_midplane = request
                .arguments
                .get("midplane")
                .and_then(|value| parse_bool_flag(value))
                .unwrap_or(false);
            let pad_length = parsed_length.filter(|value| *value > 0.0);
            if create_pad_from_selected_sketch(snapshot, pad_length, Some("dimension"), parsed_midplane).is_some() {
                Ok(BridgeCommandResponse {
                    command_id: request.command_id.clone(),
                    accepted: true,
                    status_message: format!(
                        "Created a new pad feature from the selected sketch at {:.2} mm ({})",
                        pad_length.unwrap_or(12.0),
                        if parsed_midplane { "symmetric" } else { "one-sided" }
                    ),
                    document_dirty: snapshot.dirty,
                    changed_object_ids: vec![snapshot.selected_object_id.clone()],
                    history_marker: snapshot.history_marker,
                })
            } else {
                Ok(rejected_response(
                    snapshot,
                    request,
                    "Pad creation requires an active sketch selection",
                ))
            }
        }
        _ => Err(BridgeError {
            category: crate::BridgeErrorCategory::Unsupported,
            code: "bridge.command_unsupported".into(),
            summary: format!("Bridge command '{}' is not supported", request.command_id),
            detail: "The requested command is not yet routed through the prototype bridge executor.".into(),
            correlation_id: request.options.correlation_id.clone(),
        }),
    }
}

fn rejected_response(
    snapshot: &BridgeDocumentSnapshot,
    request: &BridgeCommandRequest,
    status_message: &str,
) -> BridgeCommandResponse {
    BridgeCommandResponse {
        command_id: request.command_id.clone(),
        accepted: false,
        status_message: status_message.into(),
        document_dirty: snapshot.dirty,
        changed_object_ids: vec![],
        history_marker: snapshot.history_marker,
    }
}

fn session_not_found_error(
    session_id: &str,
    correlation_id: Option<String>,
    detail: &str,
) -> BridgeError {
    BridgeError {
        category: crate::BridgeErrorCategory::ValidationError,
        code: "bridge.session_not_found".into(),
        summary: format!("Bridge session '{}' was not found", session_id),
        detail: detail.into(),
        correlation_id,
    }
}