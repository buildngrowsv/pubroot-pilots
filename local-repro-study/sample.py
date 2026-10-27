"""Deterministic sampling for the local-repro pilot (research stub).
Frame: data/frame.json (slim, committed) or data/frame_raw.json (full GitHub search result from fetch_frame.sh).
Auto rule: body has a fenced code block containing 'export default', and mentions
wrangler dev / miniflare / vitest-pool-workers; title is not a feature/deploy/types item."""
import json, os, random, re
full = os.path.exists("data/frame_raw.json")
d = json.load(open("data/frame_raw.json" if full else "data/frame.json"))
excl = re.compile(r"\b(deploy|types?|feat|support|add|enable|expose|ability|workaround|coverage|--json|create)\b", re.I)
elig = []
for i in d["items"]:
    if full:
        b = i["body"] or ""
        has_code = any("export default" in x for x in re.findall(r"```.*?```", b, re.S))
        local = bool(re.search(r"wrangler dev|miniflare|vitest-pool-workers", b, re.I))
    else:
        has_code, local = i["body_has_export_default_code_block"], i["body_mentions_local_tooling"]
    if has_code and local and not excl.search(i["title"]):
        elig.append(i["number"])
rng = random.Random(20261026)
order = elig[:]; rng.shuffle(order)
json.dump({"eligible": elig, "shuffled": order}, open("data/sample.json", "w"), indent=1)
print(len(d["items"]), "in frame;", len(elig), "auto-eligible"); print("shuffled order:", order)
