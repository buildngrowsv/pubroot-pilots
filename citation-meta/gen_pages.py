#!/usr/bin/env python3
"""Synthetic landing pages where Highwire, DC, OG and JSON-LD disagree."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
PAGES = os.path.join(HERE, "pages")
os.makedirs(PAGES, exist_ok=True)

def page(name, highwire=None, dc=None, og=None, jsonld=None, extra=""):
    parts = ['<!doctype html><html><head><meta charset="utf-8">']
    hw = highwire or {}
    for k,v in hw.items():
        parts.append(f'<meta name="citation_{k}" content="{v}">')
    dc = dc or {}
    for k,v in dc.items():
        parts.append(f'<meta name="dc.{k}" content="{v}">')
        parts.append(f'<meta name="DC.{k}" content="{v}">')
    og = og or {}
    for k,v in og.items():
        parts.append(f'<meta property="og:{k}" content="{v}">')
    if jsonld:
        parts.append(f'<script type="application/ld+json">{json.dumps(jsonld)}</script>')
    parts.append(extra)
    parts.append('</head><body><h1>Landing</h1></body></html>')
    open(os.path.join(PAGES, f"{name}.html"), "w").write("\n".join(parts))
    return name

names = []
names.append(page("agree_all",
    highwire={"title":"Alpha Study","author":"Ann Author","doi":"10.1234/alpha","pdf_url":"https://ex.test/alpha.pdf"},
    dc={"title":"Alpha Study","creator":"Ann Author","identifier":"doi:10.1234/alpha"},
    og={"title":"Alpha Study","url":"https://ex.test/alpha"},
    jsonld={"@context":"https://schema.org","@type":"ScholarlyArticle","name":"Alpha Study","author":{"@type":"Person","name":"Ann Author"},"identifier":"https://doi.org/10.1234/alpha","url":"https://ex.test/alpha.pdf"},
))
names.append(page("title_conflict",
    highwire={"title":"Highwire Title","doi":"10.1234/t"},
    dc={"title":"Dublin Core Title"},
    og={"title":"Open Graph Title"},
    jsonld={"@context":"https://schema.org","@type":"ScholarlyArticle","name":"JSON-LD Title","headline":"JSON-LD Headline"},
))
names.append(page("doi_conflict",
    highwire={"title":"D","doi":"10.1234/hw"},
    dc={"title":"D","identifier":"doi:10.1234/dc"},
    og={"title":"D","url":"https://doi.org/10.1234/og"},
    jsonld={"@context":"https://schema.org","@type":"ScholarlyArticle","name":"D","identifier":["https://doi.org/10.1234/ld","doi:10.9999/other"]},
))
names.append(page("pdf_conflict",
    highwire={"title":"P","pdf_url":"https://ex.test/hw.pdf"},
    dc={"title":"P"},
    og={"title":"P","url":"https://ex.test/og.pdf"},
    jsonld={"@context":"https://schema.org","@type":"ScholarlyArticle","name":"P","url":"https://ex.test/ld.pdf","encoding":{"@type":"MediaObject","contentUrl":"https://ex.test/enc.pdf"}},
))
names.append(page("author_conflict",
    highwire={"title":"A","author":"Highwire A","author":"Highwire B"},  # duplicate key - fix below
    dc={"title":"A","creator":"DC Author"},
    og={"title":"A"},
    jsonld={"@context":"https://schema.org","@type":"ScholarlyArticle","name":"A","author":[{"@type":"Person","name":"LD One"},{"@type":"Person","name":"LD Two"}]},
))
# fix author_conflict with multi citation_author
open(os.path.join(PAGES,"author_conflict.html"),"w").write('''<!doctype html><html><head><meta charset="utf-8">
<meta name="citation_title" content="A">
<meta name="citation_author" content="Highwire A">
<meta name="citation_author" content="Highwire B">
<meta name="dc.creator" content="DC Author">
<meta property="og:title" content="A">
<script type="application/ld+json">{"@context":"https://schema.org","@type":"ScholarlyArticle","name":"A","author":[{"@type":"Person","name":"LD One"},{"@type":"Person","name":"LD Two"}]}</script>
</head><body></body></html>''')

names.append(page("hw_only",
    highwire={"title":"Only Highwire","doi":"10.1/hw","pdf_url":"https://ex.test/only.pdf"},
))
names.append(page("og_only",
    og={"title":"Only OG","url":"https://ex.test/og-only"},
))
names.append(page("jsonld_only",
    jsonld={"@context":"https://schema.org","@type":"ScholarlyArticle","name":"Only JSON-LD","identifier":"https://doi.org/10.1/ld"},
))
names.append(page("dc_only",
    dc={"title":"Only DC","identifier":"doi:10.1/dc","creator":"DC Only"},
))
names.append(page("emptyish",
    og={"title":""},
    highwire={"title":"  "},
))
names.append(page("relative_pdf",
    highwire={"title":"Rel","pdf_url":"/files/paper.pdf"},
    og={"title":"Rel","url":"/og/paper"},
    jsonld={"@context":"https://schema.org","@type":"ScholarlyArticle","name":"Rel","url":"files/paper.pdf"},
))
names.append(page("html_entities",
    highwire={"title":"Alpha &amp; Beta: a study"},
    og={"title":"Alpha & Beta: a study"},
    jsonld={"@context":"https://schema.org","@type":"ScholarlyArticle","name":"Alpha & Beta: a study"},
))

# also write a simple selector baseline expectation file
json.dump({"pages":[n for n in os.listdir(PAGES) if n.endswith('.html')]}, open(os.path.join(HERE,"pages","index.json"),"w"), indent=2)
print("pages", len([n for n in os.listdir(PAGES) if n.endswith('.html')]))
