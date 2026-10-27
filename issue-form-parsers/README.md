# Pilot: differential test of GitHub issue-form body parsers (G16-B)

Run on 2026-10-25 (America/Chicago) on one Linux x86_64 machine with Node v20.19.2. Cost was $0. The test is fully local; network was used only to install packages and clone the repository.

- Subjects (`results/env.txt`):
  - stefanbuck/github-issue-parser at v3.2.4 (0d9ce93) and v3.2.5 (cb6e971, which includes fix cf55537), each with and without a template.
  - @github/issue-parser 2.0.0, with and without a template.
  - @zentered/issue-forms-body-parser 3.0.0.
  - A naive `split(/^### /m)` baseline.
  - A strict CommonMark-AST reference that we wrote as a hypothesis defense: it rejects a body when template labels are missing, duplicated or out of order.
- `src/differential.mjs` runs 19 synthetic bodies (3 of them controls) for a 4-field form (`src/template.yml`). Only the Description textarea varies. Results go to `results/differential.jsonl` (raw outputs) and `results/summary.md`.
- Outcome flags:
  - FIELD_CHANGED: Title, Priority or Agreement differs from the oracle.
  - DESC_ALTERED: Description content was lost or added.
  - DESC_ESCAPED and DESC_RESERIALIZED: content preserved apart from Markdown escaping or re-serialization. These are not counted as loss.
  - EXTRA_KEYS: keys outside the form's fields.
  - REJECT: only the strict reference can reject.

Limits:
- The body layout ("### Label", a blank line, then the value; `render:` textareas wrapped in a code fence) follows the GitHub form-schema docs and the parsers' own fixtures. No live GitHub issue was created.
- The cases were written by the same agent that wrote the strict reference, so its 0 silent changes are not evidence of general robustness.

## Install and run (no keys, no GitHub API calls)

```bash
cd issue-form-parsers
npm ci                    # @github/issue-parser 2.0.0, @zentered/issue-forms-body-parser 3.0.0 (package-lock.json); unified/remark-parse come in transitively
./fetch_vendor.sh         # clones stefanbuck/github-issue-parser at v3.2.5 (cb6e971) and v3.2.4 (0d9ce93) into vendor/ (git-ignored) and runs npm ci in each
node src/differential.mjs # -> results/differential.jsonl, results/summary.md
```

Third-party parser code is not vendored in this repository: `vendor/` is created by `fetch_vendor.sh`. A clean re-run on 2026-10-25 produced byte-identical `results/differential.jsonl` and `results/summary.md`. `src/probe.mjs` is a small exploratory probe and is not used for any reported number.
