#!/usr/bin/env python3
"""Generate synthetic, schema-valid CITATION.cff files (one construct varied per case from a shared base).
No real people: all names, DOIs (10.5281/zenodo.0000xxx-style fakes) and URLs are synthetic placeholders."""
import os, textwrap
BASE = dict(
 head='cff-version: 1.2.0\nmessage: "If you use this software, please cite it as below."\ntitle: "Demo Tool"\n',
 authors='authors:\n  - family-names: Rivera\n    given-names: Dana\n',
 rest='version: "2.1.0"\ndate-released: "2024-03-05"\n')
def case(head=None, authors=None, rest=None, extra=""):
    return (head or BASE["head"]) + (authors if authors is not None else BASE["authors"]) + (rest if rest is not None else BASE["rest"]) + extra
T = lambda t: BASE["head"].replace('"Demo Tool"', t)
A = lambda s: "authors:\n" + textwrap.indent(textwrap.dedent(s).strip("\n"), "  ") + "\n"
C = {
 "base": case(),
 "author-entity": case(authors=A('- name: "Open Demo Consortium"')),
 "author-entity-amp": case(authors=A('- name: "R&D Lab of Example"')),
 "author-mixed-person-entity": case(authors=A('- family-names: Rivera\n  given-names: Dana\n- name: "Open Demo Consortium"')),
 "author-particle": case(authors=A('- family-names: Berg\n  given-names: Lena\n  name-particle: van den')),
 "author-suffix": case(authors=A('- family-names: Okafor\n  given-names: Chidi\n  name-suffix: Jr.')),
 "author-nonascii": case(authors=A('- family-names: Schröder-Núñez\n  given-names: Åsa')),
 "author-cjk": case(authors=A('- family-names: 山田\n  given-names: 太郎')),
 "author-family-only": case(authors=A('- family-names: Plato')),
 "author-given-only": case(authors=A('- given-names: Quinn')),
 "author-alias-only": case(authors=A('- alias: demo-bot')),
 "author-two-word-family": case(authors=A('- family-names: Garcia Lopez\n  given-names: Maria')),
 "author-orcid": case(authors=A('- family-names: Rivera\n  given-names: Dana\n  orcid: "https://orcid.org/0000-0002-1825-0097"')),
 "authors-12": case(authors="authors:\n" + "".join(f"  - family-names: Author{i}\n    given-names: Test\n" for i in range(12))),
 "doi-top": case(extra='doi: 10.5281/zenodo.1000001\n'),
 "doi-identifiers": case(extra='identifiers:\n  - type: doi\n    value: 10.5281/zenodo.1000002\n'),
 "doi-both-differ": case(extra='doi: 10.5281/zenodo.1000001\nidentifiers:\n  - type: doi\n    value: 10.5281/zenodo.1000002\n'),
 "url-top": case(extra='url: "https://example.org/demo"\n'),
 "url-repo-code": case(extra='repository-code: "https://github.com/example/demo"\n'),
 "url-repo-artifact": case(extra='repository-artifact: "https://pypi.org/project/demo"\n'),
 "url-identifiers": case(extra='identifiers:\n  - type: url\n    value: "https://example.org/id-url"\n'),
 "url-all": case(extra='url: "https://example.org/demo"\nrepository-code: "https://github.com/example/demo"\nidentifiers:\n  - type: url\n    value: "https://example.org/id-url"\n'),
 "version-yaml-float": case(rest='version: 1.10\ndate-released: "2024-03-05"\n'),
 "version-yaml-int": case(rest='version: 2\ndate-released: "2024-03-05"\n'),
 "no-version": case(rest='date-released: "2024-03-05"\n'),
 "no-date": case(rest='version: "2.1.0"\n'),
 "date-unquoted": case(rest='version: "2.1.0"\ndate-released: 2024-03-05\n'),
 "date-jan1": case(rest='version: "2.1.0"\ndate-released: "2024-01-01"\n'),
 "title-latex-specials": case(head=T('"Fast 100% R&D_Tools for $5"')),
 "title-acronym": case(head=T('"BERT Embeddings for GPU Clusters in LLaMA Pipelines"')),
 "title-colon": case(head=T('"demo: a lowercase tool"')),
 "title-braces": case(head=T('"Set {x} Notation Helper"')),
 "type-dataset": case(extra='type: dataset\n'),
 "license-keywords-abstract": case(extra='license: MIT\nkeywords:\n  - demo\n  - test\nabstract: "A synthetic test tool."\n'),
 "pref-article": case(extra=textwrap.dedent('''\
   preferred-citation:
     type: article
     authors:
       - family-names: Rivera
         given-names: Dana
       - family-names: Chen
         given-names: Wei
     title: "A Paper About Demo Tool"
     journal: "Journal of Synthetic Software"
     volume: 7
     issue: 2
     start: 101
     end: 115
     year: 2023
     doi: 10.5281/zenodo.1000009
   ''')),
 "pref-conference": case(extra=textwrap.dedent('''\
   preferred-citation:
     type: conference-paper
     authors:
       - family-names: Chen
         given-names: Wei
     title: "Demo Tool at a Conference"
     collection-title: "Proceedings of the Synthetic Workshop"
     year: 2022
   ''')),
 "pref-software-other-version": case(extra=textwrap.dedent('''\
   preferred-citation:
     type: software
     authors:
       - family-names: Rivera
         given-names: Dana
     title: "Demo Tool"
     version: "1.0.0"
     year: 2020
   ''')),
 "cff-1.1.0": 'cff-version: 1.1.0\nmessage: "If you use this software, please cite it as below."\ntitle: "Demo Tool"\nauthors:\n  - family-names: Rivera\n    given-names: Dana\nversion: "2.1.0"\ndate-released: 2024-03-05\n',
}
if __name__ == "__main__":
    os.makedirs("cases", exist_ok=True)
    for k, v in C.items(): open(f"cases/{k}.cff", "w").write(v)
    print(len(C), "cases")
