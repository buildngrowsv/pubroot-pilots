// Rust subject: gix-config File::from_bytes_no_includes (gitoxide). Usage: rs-gitconfig CASES.json
// Output: {"gix-config": {id: {"entries": [[key, value|null]...]} | {"error": "..."}}}. Keys as in py/run.py.
use serde_json::{json, Map, Value};

fn parse(text: &str) -> Value {
    let meta = gix_config::file::Metadata::api();
    match gix_config::File::from_bytes_no_includes(text.as_bytes(), meta, Default::default()) {
        Err(e) => json!({ "error": e.to_string() }),
        Ok(f) => {
            let mut ents = Vec::new();
            for s in f.sections() {
                let h = s.header();
                let mut k = h.name().to_string().to_lowercase();
                if let Some(sub) = h.subsection_name() { k.push('.'); k.push_str(&sub.to_string()); }
                // value_names() yields every occurrence in order; values() returns all values of one name, and an
                // implicit value (no '=') is reported by value_implicit() as Some(None)
                let mut seen: Vec<String> = Vec::new();
                for name in s.value_names() {
                    let n = name.to_lowercase();
                    if seen.contains(&n) { continue; }
                    seen.push(n.clone());
                    let vals = s.values(&name);
                    let last_implicit = matches!(s.value_implicit(&name), Some(None));
                    let cnt = vals.len();
                    for (i, v) in vals.into_iter().enumerate() {
                        if last_implicit && i + 1 == cnt { ents.push(json!([format!("{}.{}", k, n), Value::Null])); }
                        else { ents.push(json!([format!("{}.{}", k, n), v.to_string()])); }
                    }
                    if cnt == 0 && last_implicit { ents.push(json!([format!("{}.{}", k, n), Value::Null])); }
                }
            }
            json!({ "entries": ents })
        }
    }
}

fn main() {
    let path = std::env::args().nth(1).expect("cases");
    let cases: Vec<Value> = serde_json::from_str(&std::fs::read_to_string(path).unwrap()).unwrap();
    let mut out = Map::new();
    for c in cases { out.insert(c["id"].as_str().unwrap().to_string(), parse(c["text"].as_str().unwrap())); }
    println!("{}", serde_json::to_string_pretty(&json!({ "gix-config": out })).unwrap());
}
