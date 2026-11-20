// axum + tower-http ServeDir on 127.0.0.1:PORT
use tower_http::services::ServeDir;
#[tokio::main]
async fn main() {
    let port = std::env::args().nth(1).unwrap();
    let app = axum::Router::new().fallback_service(ServeDir::new("data"));
    let l = tokio::net::TcpListener::bind(format!("127.0.0.1:{port}")).await.unwrap();
    axum::serve(l, app).await.unwrap();
}
