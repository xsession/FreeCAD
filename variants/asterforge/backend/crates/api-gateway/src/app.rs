mod routes;
mod state;

use axum::serve;
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
        let state = AppState::new();
        let snapshot = state.snapshot().await;

        info!(services = ?snapshot.boot_report.services, "api gateway bootstrapped");
        info!(event_streams = ?snapshot.boot_report.event_streams, "event registry ready");
        info!(document = ?snapshot.document, "document ready");
        info!(tree_nodes = snapshot.object_tree.len(), "object tree ready");
        info!(activity_items = snapshot.events.len(), "activity stream ready");

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
                .unwrap_or_else(|_| "info,asterforge_api_gateway=debug".into()),
        )
        .try_init();
}
