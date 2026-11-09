#!/usr/bin/env python3
import json, os, re
from html.parser import HTMLParser
import extruct

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = os.path.join(HERE, "pages")
BASE_URL = "https://example.com/landing/"

class MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.metas = []
        self.jsonlds = []
        self._in_ld = False
        self._ld_buf = []
    def handle_starttag(self, tag, attrs):
        ad = dict(attrs)
        if tag == "meta":
            self.metas.append(ad)
        if tag == "script" and ad.get("type") == "application/ld+json":
            self._in_ld = True
            self._ld_buf = []
    def handle_endtag(self, tag):
        if tag == "script" and self._in_ld:
            self._in_ld = False
            try:
                self.jsonlds.append(json.loads("".join(self._ld_buf)))
            except Exception:
                pass
    def handle_data(self, data):
        if self._in_ld:
            self._ld_buf.append(data)

def select_hw_dc_og(html):
    p = MetaParser(); p.feed(html)
    def all_content(pred):
        return [m.get("content") for m in p.metas if pred(m) and m.get("content") is not None]
    hw_title = all_content(lambda m: m.get("name","").lower()=="citation_title")
    hw_doi = all_content(lambda m: m.get("name","").lower()=="citation_doi")
    hw_pdf = all_content(lambda m: m.get("name","").lower()=="citation_pdf_url")
    hw_authors = all_content(lambda m: m.get("name","").lower()=="citation_author")
    dc_title = all_content(lambda m: m.get("name","").lower() in ("dc.title","dcterms.title"))
    dc_id = all_content(lambda m: m.get("name","").lower() in ("dc.identifier","dcterms.identifier"))
    dc_creator = all_content(lambda m: m.get("name","").lower() in ("dc.creator","dcterms.creator"))
    og_title = all_content(lambda m: m.get("property")=="og:title")
    og_url = all_content(lambda m: m.get("property")=="og:url")
    title = next((t for t in hw_title+dc_title+og_title if t and str(t).strip()), None)
    doi = None
    for d in hw_doi+dc_id:
        if not d: continue
        m = re.search(r"10\.\d+/[^\s]+", d)
        if m: doi = m.group(0); break
    pdf = next((u for u in hw_pdf+og_url if u), None)
    return {"title": title, "doi": doi, "pdf_or_url": pdf, "authors": hw_authors or dc_creator, "source_pref": "hw>dc>og"}

out = {"selector": {}, "extruct": {}}
for fn in sorted(os.listdir(PAGES)):
    if not fn.endswith(".html"): continue
    html = open(os.path.join(PAGES, fn), encoding="utf-8").read()
    out["selector"][fn] = select_hw_dc_og(html)
    try:
        data = extruct.extract(html, base_url=BASE_URL, syntaxes=["json-ld","opengraph","dublincore","microdata"])
        title = None; doi=None; url=None; authors=[]
        for item in data.get("json-ld") or []:
            if not isinstance(item, dict):
                continue
            title = title or item.get("name") or item.get("headline")
            ident = item.get("identifier")
            if isinstance(ident, list): ident = ident[0] if ident else None
            if isinstance(ident, str) and "10." in ident:
                m=re.search(r"10\.\d+/[^\s]+", ident); doi = doi or (m.group(0) if m else None)
            url = url or item.get("url")
            a = item.get("author")
            if isinstance(a, dict): authors.append(a.get("name"))
            elif isinstance(a, list):
                for x in a:
                    if isinstance(x, dict): authors.append(x.get("name"))
                    else: authors.append(str(x))
        for og in data.get("opengraph") or []:
            if isinstance(og, dict):
                props = og.get("properties") or og
                if isinstance(props, list):
                    props = dict(props)
                if isinstance(props, dict):
                    title = title or props.get("og:title") or props.get("title")
                    url = url or props.get("og:url") or props.get("url")
        out["extruct"][fn] = {"title": title, "doi": doi, "pdf_or_url": url, "authors": [a for a in authors if a], "raw_keys": list(data.keys())}
    except Exception as e:
        out["extruct"][fn] = {"error": str(e)}

os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
json.dump(out, open(os.path.join(HERE, "results", "py.json"), "w"), indent=2)
print("py extracted", len(out["selector"]))
