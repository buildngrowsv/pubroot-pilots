// Rust subjects. Usage: rs-refs CASES.json -> {lib: {id: {"ref": [registry, repository, tag, digest]} | {"error"}}}
// - oci-spec 0.10.0 distribution::Reference via FromStr (also re-exported as oci_client::Reference by oci-client 0.18)
use serde_json::{json, Map, Value};
use std::str::FromStr;

fn oci(s: &str) -> Value {
    match oci_spec::distribution::Reference::from_str(s) {
        Ok(r) => json!({ "ref": [r.registry(), r.repository(), r.tag(), r.digest()] }),
        Err(e) => json!({ "error": e.to_string() }),
    }
}

fn main() {
    let path = std::env::args().nth(1).expect("cases");
    let cases: Vec<Value> = serde_json::from_str(&std::fs::read_to_string(path).unwrap()).unwrap();
    let mut a = Map::new();
    for c in cases {
        let id = c["id"].as_str().unwrap().to_string();
        let s = c["s"].as_str().unwrap();
        a.insert(id, oci(s));
    }
    println!("{}", serde_json::to_string_pretty(&json!({ "oci-spec": a })).unwrap());
}
