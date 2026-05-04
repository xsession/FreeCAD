mod bridge_command_runtime;
mod bridge_services;
mod command_runtime;
mod extension_runtime;
mod protocol;
mod routes;
mod services;
mod state_bootstrap;
mod state_commands;
mod state_lifecycle;
mod state_model;
mod state_mutations;
mod state_open;
mod state_payloads;
mod state_properties;
mod state_proto;
mod state_query;
mod state_reads;
mod state_requests;
mod state_selection;
mod state_shell;
mod state_step_nav;
mod state_step_cache;
mod state_step_tools;
mod state_step_views;
mod state_sync;
mod state_types;
mod state;
#[cfg(test)]
mod state_tests;
mod state_views;
mod state_workspace;
mod step_runtime;

use axum::serve;
use std::sync::Arc;
use state::AppState;
use tokio::net::TcpListener;
use tracing::info;

pub use routes::build_router;

pub struct ApiGateway {
    state: AppState,
    bind_address: String,
}

impl ApiGateway {
    pub async fn bootstrap() -> anyhow::Result<Self> {
        initialize_tracing();

        let bind_address = "127.0.0.1:4180".to_string();
        let services = Arc::new(services::AppServices::production());
        let state = AppState::with_services(services.clone());
        let snapshot = state.snapshot().await;
        let bridge_runtime = state.bridge_runtime_descriptor().await;

        info!(services = ?snapshot.boot_report.services, "api gateway bootstrapped");
        info!(event_streams = ?snapshot.boot_report.event_streams, "event registry ready");
        info!(document = ?snapshot.document, "document ready");
        info!(tree_nodes = snapshot.object_tree.len(), "object tree ready");
        info!(activity_items = snapshot.events.len(), "activity stream ready");
        info!(worker_mode = %bridge_runtime.worker_mode, protocol = ?bridge_runtime.protocol_version, "bridge runtime descriptor ready");

        Ok(Self {
            state,
            bind_address,
        })
    }

    pub async fn run(self) -> anyhow::Result<()> {
        let listener = TcpListener::bind(&self.bind_address).await?;
        info!(bind_address = %self.bind_address, "AsterForge API gateway is ready");

        serve(listener, build_router(self.state))
            .with_graceful_shutdown(shutdown_signal())
            .await?;

        Ok(())
    }
}

async fn shutdown_signal() {
    if let Err(error) = tokio::signal::ctrl_c().await {
        info!(?error, "failed to listen for shutdown signal");
        return;
    }
    info!("shutdown signal received");
}

fn initialize_tracing() {
    let _ = tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| {
                    "info,asterforge_api_gateway=debug,asterforge_command_core=debug,asterforge_document_core=debug,asterforge_freecad_bridge=debug".into()
                }),
        )
        .try_init();
}
