// actix-web + actix-files Files service (NamedFile) on 127.0.0.1:PORT
use actix_web::{App, HttpServer};
#[actix_web::main]
async fn main() -> std::io::Result<()> {
    let port: u16 = std::env::args().nth(1).unwrap().parse().unwrap();
    HttpServer::new(|| App::new().service(actix_files::Files::new("/", "data")))
        .workers(1).bind(("127.0.0.1", port))?.run().await
}
