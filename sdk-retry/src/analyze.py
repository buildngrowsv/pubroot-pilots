#!/usr/bin/env python3
"""Join server-side attempts with client-side outcomes; one row per (sdk, scenario) across reps."""
import json, collections
att = [json.loads(l) for l in open("results/attempts.jsonl")]
cli = [json.loads(l) for l in open("results/client.jsonl")]
by = collections.defaultdict(list)
for a in att: by[(a["run_id"], a["scenario"])].append(a)
rows = []
for c in cli:
    A = by.get((c["run_id"], c["scenario"]), [])
    keys = [tuple(sorted(a["idem_headers"].items())) for a in A]
    idem_present = any(a["idem_headers"] for a in A)
    idem_stable = idem_present and len(set(keys)) == 1 and all(a["idem_headers"] for a in A)
    err = c.get("error") or ""
    rows.append(dict(sdk=c["sdk"], version=c.get("version"), scenario=c["scenario"], rep=c["run_id"].split("-")[0],
        attempts=len(A), duplicates=max(len(A) - 1, 0), same_body=len({a["body_sha256"] for a in A}) <= 1,
        idem_header_names=sorted({k for a in A for k in a["idem_headers"]}), idem_present=idem_present, idem_stable_across_attempts=idem_stable,
        retry_count_header=[a["retry_count_header"] for a in A], elapsed_s=c.get("elapsed_s"),
        client_timed_out=("imeout" in err), error=err[:120]))
json.dump(rows, open("results/joined.json", "w"), indent=1)
agg = collections.OrderedDict()
for r in rows:
    k = (r["sdk"], r["scenario"]); agg.setdefault(k, []).append(r)
md = "| SDK (version) | scenario | attempts per logical call (3 reps) | idempotency header sent | same key on every attempt | client saw a timeout |\n|---|---|---|---|---|---|\n"
for (sdk, sc), rs in agg.items():
    md += f"| {sdk} {rs[0]['version']} | {sc} | {', '.join(str(r['attempts']) for r in rs)} | {'yes: ' + ','.join(rs[0]['idem_header_names']) if any(r['idem_present'] for r in rs) else 'no'} | {'yes' if all(r['idem_stable_across_attempts'] for r in rs) else ('n/a' if not any(r['idem_present'] for r in rs) else 'no')} | {'yes' if all(r['client_timed_out'] for r in rs) else ('no' if not any(r['client_timed_out'] for r in rs) else 'mixed')} |\n"
tot = sum(r["duplicates"] for r in rows); n = len(rows)
md += f"\nTotal logical calls: {n}; total duplicate POSTs reaching the stub: {tot}; calls with >1 attempt: {sum(r['attempts'] > 1 for r in rows)}; duplicate POSTs carrying a stable idempotency key: {sum(r['duplicates'] for r in rows if r['idem_stable_across_attempts'])}.\n"
open("results/summary.md", "w").write(md); print(md)
