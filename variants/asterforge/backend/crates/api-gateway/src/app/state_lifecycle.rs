use std::sync::Arc;

use super::services::AppServices;
use super::state::AppState;
use super::{state_bootstrap, state_workspace};

impl AppState {
    pub fn new() -> Self {
        Self::with_services(Arc::new(AppServices::production()))
    }

    pub(super) fn with_services(services: Arc<AppServices>) -> Self {
        Self::with_services_and_persistence(
            services,
            state_workspace::default_persistence_path(),
        )
    }

    pub(super) fn with_services_and_persistence(
        services: Arc<AppServices>,
        persistence_path: Option<std::path::PathBuf>,
    ) -> Self {
        let session_namespace = state_workspace::next_session_namespace();
        let correlation_id = services.next_correlation_id();
        tracing::info!(
            correlation_id,
            session_namespace,
            persistence_path = ?persistence_path.as_deref(),
            "bootstrapping app state"
        );
        let persisted_workspace = persistence_path
            .as_deref()
            .and_then(|path| state_workspace::load_persisted_workspace_state(&correlation_id, path));
        let model = state_bootstrap::build_bootstrap_model(
            &services,
            session_namespace,
            &correlation_id,
            persisted_workspace.as_ref(),
        );

        Self {
            inner: Arc::new(tokio::sync::RwLock::new(model)),
            services,
            persistence_path,
        }
    }
}