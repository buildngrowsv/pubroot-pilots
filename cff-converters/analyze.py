#!/usr/bin/env python3
"""Compare the three converters' BibTeX/APA output per case. Writes results/fields.csv, results/hazards.csv, results/summary.json."""
import csv, glob, json, os, re
import bibtexparser
from bibtexparser.bparser import BibTexParser
from pylatexenc.latex2text import LatexNodes2Text
TOOLS = ["ruby-cff", "cffconvert", "citation-js"]
L2T = LatexNodes2Text()
MON = {m: i + 1 for i, m in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split())}
FULL = {"january","february","march","april","may","june","july","august","september","october","november","december"}
def txt(v): return re.sub(r"\s+", " ", L2T.latex_to_text(v)).strip() if v else ""
def month(v):
    v = (v or "").strip().lower()
    if v.isdigit(): return int(v)
    return MON.get(v[:3]) if v[:3] in MON else (v or None)
def parse(path):
    raw = open(path).read()
    p = BibTexParser(common_strings=True, ignore_nonstandard_types=False, interpolate_strings=True)
    db = bibtexparser.loads(raw, p)
    return raw, db.entries
def fields(e):
    return dict(type=e.get("ENTRYTYPE"), authors=" | ".join(txt(a) for a in re.split(r"\s+and\s+", e.get("author", "")) if a.strip()),
                title=txt(e.get("title", "")), year=e.get("year"), month=month(e.get("month")), doi=e.get("doi"),
                url=e.get("url"), version=e.get("version"), journal=txt(e.get("journal", "")))
SPECIAL = re.compile(r"(?<!\\)[&%$#_]")
def hazards(raw, entries, case):
    h = []
    for e in entries:
        for k, v in e.items():
            if k in ("url", "doi", "ID", "ENTRYTYPE", "howpublished"): continue
            if SPECIAL.search(v): h.append(f"unescaped LaTeX special in {k}")
        a = e.get("author", "")
        for name in re.split(r"\s+and\s+", a):
            n = name.strip()
            if n.startswith(","): h.append("empty family name (', given')")
        if "author" not in e: h.append("no author field")
        m = e.get("month")
        if m and not (m.strip().isdigit() and 1 <= int(m) <= 12) and m.strip().lower() not in MON and m.strip().lower() not in FULL: h.append(f"non-standard month value '{m}'")
    if case.startswith("author-entity") or case == "author-mixed-person-entity":
        if re.search(r"author = \{(?:[^{}]*and )?(Open Demo Consortium|R\\?&D Lab of Example)", raw): h.append("multi-word entity author not brace-protected (BibTeX reads last word as family name)")
    return sorted(set(h))
rows, hz, summ = [], [], {}
cases = sorted(os.path.basename(d) for d in glob.glob("results/raw/*"))
for c in cases:
    F = {}
    for t in TOOLS:
        raw, ents = parse(f"results/raw/{c}/{t}.bib")
        F[t] = dict(fields(ents[0]) if ents else {}, n_entries=len(ents))
        F[t]["apa"] = re.sub(r"\s+", " ", open(f"results/raw/{c}/{t}.apa").read()).strip()
        for x in hazards(raw, ents, c): hz.append(dict(case=c, tool=t, hazard=x))
    for k in ["type", "authors", "title", "year", "month", "doi", "url", "version", "journal", "n_entries", "apa"]:
        vals = {t: F[t].get(k) for t in TOOLS}
        rows.append(dict(case=c, field=k, agree=len({json.dumps(v) for v in vals.values()}) == 1, **{t: vals[t] for t in TOOLS}))
with open("results/fields.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["case", "field", "agree"] + TOOLS); w.writeheader(); w.writerows(rows)
with open("results/hazards.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["case", "tool", "hazard"]); w.writeheader(); w.writerows(hz)
sem = ["authors", "title", "year", "doi", "url"]
per_field = {k: sum(1 for r in rows if r["field"] == k and not r["agree"]) for k in ["type", "authors", "title", "year", "month", "doi", "url", "version", "journal", "n_entries", "apa"]}
case_dis = sorted({r["case"] for r in rows if r["field"] in sem and not r["agree"]})
pair = {}
for i, a in enumerate(TOOLS):
    for b in TOOLS[i + 1:]:
        pair[f"{a} vs {b}"] = sum(1 for c in cases if any(r[a] != r[b] for r in rows if r["case"] == c and r["field"] in sem))
hzc = {}
for x in hz: hzc.setdefault(x["tool"], {}).setdefault(x["hazard"].split(" in ")[0].split(" '")[0], set()).add(x["case"])
summ = dict(cases=len(cases), disagree_per_field=per_field, cases_with_semantic_disagreement=len(case_dis), semantic_disagreement_cases=case_dis,
            pairwise_cases_differing_on_semantic_fields=pair, hazards={t: {k: len(v) for k, v in d.items()} for t, d in hzc.items()})
json.dump(summ, open("results/summary.json", "w"), indent=1); print(json.dumps(summ, indent=1))
