#!/usr/bin/env python3
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
py = json.load(open(os.path.join(HERE, "results", "py.json")))
ms = json.load(open(os.path.join(HERE, "results", "metascraper.json")))
pages = sorted(py["selector"])
rows = []
disagree = 0
for fn in pages:
    sel = py["selector"][fn]
    ex = py["extruct"][fn]
    m = ms.get(fn, {})
    titles = {
        "selector": sel.get("title"),
        "extruct": ex.get("title"),
        "metascraper": m.get("title"),
    }
    # normalize whitespace
    def n(x):
        if x is None: return None
        return re.sub(r"\s+", " ", str(x)).strip() or None
    titles = {k:n(v) for k,v in titles.items()}
    vals = [v for v in titles.values() if v is not None]
    agree = len(set(vals)) <= 1 if vals else True
    # also compare when all present
    all_present = all(titles.values())
    if all_present and len(set(titles.values())) > 1:
        disagree += 1
        flag = "title_conflict"
    elif not agree and len(vals) > 1:
        disagree += 1
        flag = "partial_conflict"
    else:
        flag = "ok"
    rows.append({"page": fn, "titles": titles, "flag": flag, "metascraper_full": m})
summary = {"n_pages": len(pages), "pages_title_disagree": disagree, "rows": rows}
json.dump(summary, open(os.path.join(HERE, "results", "summary.json"), "w"), indent=2)
print(f"pages={len(pages)} title_disagree={disagree}")
for r in rows:
    if r["flag"] != "ok":
        print(r["page"], r["titles"])
