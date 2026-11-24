// Split and quote runners for Rust crates. Usage: rs-words split|quote CASES.json > out.json
use serde_json::{json, Map, Value};
fn main() {
    let a: Vec<String> = std::env::args().collect();
    let cases: Vec<Value> = serde_json::from_str(&std::fs::read_to_string(&a[2]).unwrap()).unwrap();
    let mut out = Map::new();
    let names: Vec<&str> = vec!["shlex (Rust)", "shell-words (Rust)"];
    for n in names {
        let mut m = Map::new();
        for c in &cases {
            let id = c["id"].as_str().unwrap();
            let s = c["s"].as_str().unwrap();
            let r = match (a[1].as_str(), n) {
                ("split", "shlex (Rust)") => match shlex::split(s) { Some(v) => json!({"argv": v}), None => json!({"error": "None (invalid input)"}) },
                ("split", _) => match shell_words::split(s) { Ok(v) => json!({"argv": v}), Err(e) => json!({"error": e.to_string()}) },
                ("quote", "shlex (Rust)") => match shlex::try_quote(s) { Ok(q) => json!({"argv": q}), Err(e) => json!({"error": e.to_string()}) },
                _ => json!({"argv": shell_words::quote(s)}),
            };
            m.insert(id.to_string(), r);
        }
        out.insert(n.to_string(), Value::Object(m));
    }
    println!("{}", serde_json::to_string_pretty(&Value::Object(out)).unwrap());
}
