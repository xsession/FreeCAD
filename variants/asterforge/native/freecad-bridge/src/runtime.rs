use crate::{BridgeCapabilities, BridgeRuntimeDescriptor, BridgeStatus};

pub fn bridge_status() -> BridgeStatus {
    BridgeStatus {
        worker_mode: "mock-freecad-worker".into(),
        freecad_runtime_detected: false,
        capabilities: BridgeCapabilities::default(),
    }
}

pub fn bridge_runtime_descriptor() -> BridgeRuntimeDescriptor {
    BridgeRuntimeDescriptor::default()
}