# git-config

Supports the Pubroot draft "Reading .gitconfig Like Git Does: Seven Config Libraries Checked Against git config --list"
(batch 9, 2026-11-24).

76 git config files (`cases.json`, written by `gen_cases.py`) are read by git itself and by seven libraries:

- Python: dulwich `ConfigFile`, GitPython `GitConfigParser`, pygit2 `Config` (libgit2)
- Node: parse-git-config `parse.sync` (built on the ini package), isomorphic-git `GitConfigManager.get`
  (exported `isomorphic-git/managers` subpath; entries read from the returned object's `parsedConfig` field)
- Go: go-git v5 `plumbing/format/config` Decoder
- Rust: gix-config `File::from_bytes_no_includes` (0.60.0, the newest release that builds with Rust 1.85)

The reference is `git config -f FILE --list -z` (`oracle.py`), with no system or global config and no includes.
Each reading is turned into a map from key (section and name lower-cased, subsection as reported) to the ordered list
of its values (`common.py`). Classes: A same as git; T same once git's implicit true (a name with no `=`) is read as
"true"; W different; R library error where git reads the file; L library reads a file git rejects.
Groups: B structure, K section and key names, S subsections, V values, L practical files. K09 and V19 are open.

Reproduce (Node 24, Python 3.13, Go 1.27, Rust 1.85, git 2.47):

    python3 -m venv .venv && .venv/bin/pip install -r py/requirements.txt
    cd js && npm ci && cd ..
    python3 realworld/fetch_gitconfigs.py --restore     # optional: rebuilds the real-world sample (network, read-only)
    PY=.venv/bin/python ./run_all.sh

Outputs: `results/git.json`, `results/libs.json`, `results/summary.json`, `results/report.txt` (full per-case matrix),
`results/realworld.{json,txt}`, `results/versions.txt`. No keys. Cost: $0.

`realworld/gitconfigs.list.json` pins 39 git config files (repository, commit, path, sha256) from the 100 most-starred
GitHub repositories named "dotfiles" plus the example repositories listed in webpro/awesome-dotfiles, snapshot
2026-11-24 (`realworld/fetch_gitconfigs.py`). The file texts are not committed, because personal config files carry
their owners' names and e-mail addresses; `--restore` re-reads them at the pinned commits and checks every hash, and
`results/realworld.json` records classes and the names of differing keys, not values.
