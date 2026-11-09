#!/usr/bin/env python3
import json, os
from llms_txt import parse_llms_file
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = {}
for fn in sorted(os.listdir(os.path.join(HERE, "fixtures"))):
    if not fn.endswith(".txt"): continue
    text = open(os.path.join(HERE, "fixtures", fn), encoding="utf-8").read()
    try:
        p = parse_llms_file(text)
        sections = []
        for name, links in (p.get("sections") or {}).items():
            norm_links = []
            for l in links:
                if isinstance(l, dict):
                    norm_links.append({"url": l.get("url"), "title": l.get("title"), "description": l.get("desc") or l.get("description")})
                else:
                    norm_links.append({"url": getattr(l,"url",None), "title": getattr(l,"title",None), "description": getattr(l,"desc",None)})
            sections.append({"name": name, "links": norm_links})
        out[fn] = {
            "ok": True,
            "title": p.get("title"),
            "summary": p.get("summary") or p.get("info"),
            "sections": sections,
        }
    except Exception as e:
        out[fn] = {"ok": False, "error": str(e)}
json.dump({"llms-txt": out}, open(os.path.join(HERE, "results", "py.json"), "w"), indent=2)
print("py", len(out))
