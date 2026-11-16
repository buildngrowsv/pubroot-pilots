// Reads cases.json on stdin; writes {"spdx-rs": {case: {ok, tree, probes}|{ok:false, err}}} using the
// public API of the `spdx` crate: Expression::parse (ParseMode::STRICT), Expression::iter (postfix nodes),
// and Expression::evaluate for the allow-list probes (a requirement is allowed if its full rendering, including any WITH addition, is listed).
use serde_json::{json, Value};
use spdx::expression::{ExprNode, Operator};
use std::io::Read;

fn main() {
    let mut s = String::new();
    std::io::stdin().read_to_string(&mut s).unwrap();
    let cases: Vec<Value> = serde_json::from_str(&s).unwrap();
    let mut res = serde_json::Map::new();
    for c in &cases {
        let id = c["id"].as_str().unwrap();
        let expr = c["expr"].as_str().unwrap();
        let r = match spdx::Expression::parse(expr) {
            Ok(e) => {
                let mut stack: Vec<Value> = vec![];
                for n in e.iter() {
                    match n {
                        ExprNode::Req(r) => stack.push(json!(r.req.to_string())),
                        ExprNode::Op(op) => {
                            let b = stack.pop().unwrap();
                            let a = stack.pop().unwrap();
                            let o = if *op == Operator::And { "AND" } else { "OR" };
                            stack.push(json!([o, a, b]));
                        }
                    }
                }
                let probes: Vec<Value> = c["probes"].as_array().unwrap().iter().map(|p| {
                    let allow: Vec<String> = p["allow"].as_array().unwrap().iter().map(|x| x.as_str().unwrap().to_string()).collect();
                    json!(e.evaluate(|req| allow.iter().any(|a| a.eq_ignore_ascii_case(&req.to_string()))))
                }).collect();
                let mut m = json!({"ok": true, "tree": stack.pop().unwrap()});
                if !probes.is_empty() { m["probes"] = json!(probes); }
                m
            }
            Err(e) => json!({"ok": false, "err": format!("{:?}", e.reason)}),
        };
        res.insert(id.to_string(), r);
    }
    println!("{}", serde_json::to_string_pretty(&json!({"spdx-rs": res, "_list_version": spdx::identifiers::VERSION})).unwrap());
}
