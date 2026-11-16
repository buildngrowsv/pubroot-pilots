# spdx-expressions

Supports the Pubroot draft "Same License Expression, Different Verdict" (batch 7, 2026-11-16).

91 SPDX license-expression cases (`cases.json`, written by `gen_cases.py`, each with the reading of SPDX
Specification 3.0.1 Annex B) are run in-process through six parsers using only their public APIs:
spdx-expression-parse 5.0.0 and 3.0.1 (npm; 3.0.1 is the copy spdx-satisfies depends on), license-expression 30.4.4
(`get_spdx_licensing().parse(validate=True, strict=True)`), packaging 26.3 (`canonicalize_license_expression`, PEP 639),
github/go-spdx v2.8.0 (`ValidateAndNormalizeLicensesWithOptions`, `ExtractLicenses`, `Satisfies`) and the Rust
`spdx` crate 0.13.6 (`Expression::parse`, `iter`, `evaluate`). Seven precedence cases also carry allow-list probes
for spdx-satisfies 6.0.1, go-spdx `Satisfies` and spdx `evaluate`. `analyze.py` compares acceptance, leaf sets and
trees against the Annex B readings and between implementations.

Real-world sample: `realworld/strings.json` is a committed snapshot (2026-11-16) of `license_expression` for the
top 300 PyPI projects (hugovk/top-pypi-packages, 30-day list) and `license` for the top 300 npm packages by
downloads (npm-high-impact 1.13.0). `realworld/fetch.py` made it with unauthenticated public GETs; the run itself
uses only the snapshot.

Reproduce (Node 24, Python 3.13, Go 1.27, Rust 1.85; Go modules pinned in go/go.mod and go/go.sum, crates in rs/Cargo.lock):

    cd js && npm ci && cd ..
    python3 -m venv .venv && .venv/bin/pip install -r py/requirements.txt
    PY=.venv/bin/python ./run_all.sh

Outputs: `results/{node,py,go,rs}.json`, `results/rw_*.json`, `results/summary.json`, `results/rw_summary.json`,
`results/report.txt`, `results/versions.txt`. No network at run time, no keys. Cost: $0.
