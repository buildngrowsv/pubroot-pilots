# cff-converters: differential test of CITATION.cff converters

Supports the Pubroot paper "One CITATION.cff, Three Citations: A Differential Test of Citation File Format Converters" (2026-11-04).

- `gen_cases.py` writes 38 synthetic, schema-valid CITATION.cff files to `cases/` (all names, DOIs and URLs are invented placeholders).
- `run_all.sh` converts each file with ruby-cff (`rb/conv.rb`), cffconvert (`py/`) and citation-js (`js/conv.mjs`) to BibTeX and APA-like text, and validates with ruby-cff and cffconvert. Outputs: `results/raw/<case>/<tool>.{bib,apa,validate}`.
- `analyze.py` parses the BibTeX (bibtexparser 1.4.4, pylatexenc 2.11), compares fields across tools and flags BibTeX/LaTeX hazards. Outputs: `results/fields.csv`, `results/hazards.csv`, `results/summary.json`.
- `results/versions.txt`: ruby-cff 1.3.0 (Ruby 3.3.6), cffconvert 2.0.0, @citation-js/core 0.9.0 + plugin-software-formats 0.7.3, plugin-bibtex 0.9.0, plugin-csl 0.9.0, Node 24.22.1. Pins: `py/requirements.lock.txt`, `js/package-lock.json`, `js/npm-ls.txt`.
- `results/stability.diff` is empty: a second full run produced byte-identical outputs.

Reproduce:

    python3 gen_cases.py
    python3 -m venv py/.venv && py/.venv/bin/pip install -r py/requirements.lock.txt
    (cd js && npm ci)
    gem install cff -v 1.3.0
    RUBY=ruby CFFCONVERT=py/.venv/bin/cffconvert ./run_all.sh
    py/.venv/bin/python analyze.py

No accounts, keys or network calls to any service are used after installation. Cost: $0.
