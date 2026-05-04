use std::{
    collections::HashMap,
    sync::{Mutex, OnceLock},
};

use crate::BridgeDocumentSnapshot;

fn prototype_session_store() -> &'static Mutex<HashMap<String, BridgeDocumentSnapshot>> {
    static STORE: OnceLock<Mutex<HashMap<String, BridgeDocumentSnapshot>>> = OnceLock::new();
    STORE.get_or_init(|| Mutex::new(HashMap::new()))
}

pub fn sync_prototype_bridge_session(session_id: &str, snapshot: &BridgeDocumentSnapshot) {
    let store = prototype_session_store();
    let mut sessions = store.lock().expect("prototype bridge session store should not be poisoned");
    sessions.insert(session_id.to_string(), snapshot.clone());
}

pub fn load_prototype_bridge_session(session_id: &str) -> Option<BridgeDocumentSnapshot> {
    let store = prototype_session_store();
    let sessions = store.lock().expect("prototype bridge session store should not be poisoned");
    sessions.get(session_id).cloned()
}