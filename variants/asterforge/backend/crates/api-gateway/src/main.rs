mod app;
mod domain;

use app::ApiGateway;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    ApiGateway::bootstrap().await?.run().await
}
