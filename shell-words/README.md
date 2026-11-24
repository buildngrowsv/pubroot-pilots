# shell-words

Supports the Pubroot draft "Splitting Command Lines Without a Shell: Ten Word-Splitting Libraries Measured Against dash"
(batch 9, 2026-11-24).

87 command-line strings (`cases.json`, written by `gen_cases.py`) are split by ten libraries that turn a string into an
argument vector the way a POSIX shell would, and 29 strings (`quote_cases.json`) are quoted by eight libraries:

- Python: `shlex.split` / `shlex.quote` (standard library, CPython 3.13)
- Node: shell-quote `parse` / `quote`, string-argv, shlex (npm) `split` / `quote`, shell-escape (quote only)
- Go: google/shlex `Split`, kballard/go-shellquote `Split` / `Join`, mattn/go-shellwords `Parse`,
  mvdan.cc/sh/v3 `shell.Fields` / `syntax.Quote(LangPOSIX)`
- Rust: shlex `split` / `try_quote`, shell-words `split` / `quote`

The reference is a real POSIX shell. `oracle.py` runs each string as the arguments of a shell function in dash and in
`bash --posix`, with an empty environment (only PATH and HOME set, both pointing nowhere), globbing off and a throwaway
working directory; the function writes its arguments NUL-separated to a side file descriptor. A quoted form passes
only if both shells, with globbing on and decoy files present, turn it back into exactly the original string.

Groups: B basic, S single quotes, D double quotes, E backslash outside quotes, Q mixed, U Unicode and control
whitespace, L practical command lines (scored); C comments, O operators and newlines, X expansions (shell-only:
reported, not scored, since a word splitter is not expected to run a shell). E06 (trailing backslash) is open.
`analyze.py` classes each output: A same vector as dash, W different vector, R library error where dash parses,
L vector where dash reports a syntax error.

Note: yargs-parser was tried and dropped; its string tokenizer is internal and leaves quotes for a later stage.

Reproduce (Node 24, Python 3.13, Go 1.27, Rust 1.85, dash and bash installed):

    cd js && npm ci && cd ..
    PY=python3 ./run_all.sh

Outputs: `results/split.json`, `results/quote.json`, `results/sh_split.json`, `results/sh_quote.json`,
`results/summary.json`, `results/report.txt` (full per-case matrix), `results/realworld.{json,txt}`, `results/versions.txt`.
No network, no keys. Cost: $0.

`realworld/npm_scripts.json` is a snapshot (2026-11-24) of the `scripts` of the first 500 names in npmTopDownloads
from npm-high-impact 1.13.0, made by `realworld/fetch_npm_scripts.py`; `--verify` re-reads the pinned name@version
manifests from the npm registry. `realworld/analyze_rw.py` (run by `run_all.sh`) splits the 1,402 distinct strings.
