#!/usr/bin/env python3
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
js = json.load(open(os.path.join(HERE, "results", "js.json")))
py = json.load(open(os.path.join(HERE, "results", "py.json")))["llms-txt"]
a = js["25xcodes"]; b = js["parse-llms-txt"]; c = py
files = sorted(set(a)|set(b)|set(c))
rows = []
disagree = 0
for fn in files:
    ta = (a.get(fn) or {}).get("title")
    tb = (b.get(fn) or {}).get("title")
    tc = (c.get(fn) or {}).get("title")
    sa = len(((a.get(fn) or {}).get("sections") or []))
    sb = len(((b.get(fn) or {}).get("sections") or []))
    sc = len(((c.get(fn) or {}).get("sections") or []))
    def urls(obj):
        u=[]
        for s in (obj or {}).get("sections") or []:
            for l in s.get("links") or []:
                if l.get("url"): u.append(l["url"])
        return u
    ua, ub, uc = urls(a.get(fn)), urls(b.get(fn)), urls(c.get(fn))
    ok = ((a.get(fn) or {}).get("ok"), (b.get(fn) or {}).get("ok"), (c.get(fn) or {}).get("ok"))
    title_agree = len(set([x for x in [ta,tb,tc] if x is not None])) <= 1
    sec_agree = sa==sb==sc
    url_agree = ua==ub==uc
    flag_ok = title_agree and sec_agree and url_agree and all(ok)
    if not flag_ok: disagree += 1
    rows.append({"file": fn, "titles":[ta,tb,tc], "n_sections":[sa,sb,sc], "n_urls":[len(ua),len(ub),len(uc)], "urls":[ua,ub,uc], "ok": ok, "agree": flag_ok})
summary={"n_files":len(files),"disagree_any":disagree,"rows":rows}
json.dump(summary, open(os.path.join(HERE,"results","summary.json"),"w"), indent=2)
print(f"files={len(files)} disagree={disagree}")
for r in rows:
    if not r["agree"]:
        print(r["file"], "titles", r["titles"], "secs", r["n_sections"], "urls", r["n_urls"], "ok", r["ok"])
