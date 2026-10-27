# Pilot: offline replay of closed Workers toolchain issues

Code for *Do Closed Workers Toolchain Bug Reports Still Reproduce Offline? A Pinned-Version Replay of Ten Sampled wrangler and Miniflare Issues*.

Run on 2026-10-26 (America/Chicago) on one Linux x86_64 machine. Cost was $0: public GitHub issue text, public npm packages, and localhost servers only. **No Cloudflare account, no deployment and no API key.**

## Layout
- `fetch_frame.sh`: re-fetches the sampling frame from the public GitHub search API (query in `data/frame_query.txt`) into `data/frame_raw.json`.
- `data/frame.json`: a slim copy of the frame as used. It has 77 issues: number, title, URL and dates, plus the two body-derived eligibility flags. Issue bodies are not redistributed.
- `sample.py`: applies the auto-eligibility rule (21 issues) and shuffles them with seed `20261026` → `data/sample.json`. The first 10 were drawn. It runs on either frame file.
- `runs/<issue>/run.sh`: each script writes the minimal repro, installs the "before" or "after" versions into a subfolder and runs the repro on localhost. Every edit to the reporter's text is commented in the script and recorded in `data/results.jsonl`.
  - 10170: `run_old.sh` clones the reporter's public repo at `81eaadf` (`fetch_repo.sh`). `run_min.sh` is the maintainer's minimal repro.
  - 13609: `fetch_gist.sh` clones the public gist linked from the issue and checks its SHA-256 sums.
- `data/results.jsonl`: one line per drawn issue (status, versions, edits, observed before/after).
- `results/logs/`: the original test, dev and vite logs. Local paths were replaced with `<local-path>`, and install logs are omitted.

## Results (`data/results.jsonl`)
| Outcome | Issues |
|---|---|
| Reproduced before, fixed after (5) | 12929, 13578, 10170, 14107, 14255 |
| Closed without a code change: behaviour unchanged (2) | 13609, 13790 |
| Not reproduced at the reported version (1) | 12706 |
| Excluded: needs Docker / interactive HMR (2) | 11625, 12731 |

- 2 of the 8 replays ran verbatim.
- "After" is the current npm release on 2026-10-26, **not** the fixing commit: wrangler 4.152.0, miniflare 4.20260730.0, @cloudflare/vite-plugin 1.65.0, vitest 4.1.12, vite 8.3.5.
- 12929 ran on Node 20.19.2; the rest ran on Node 22.23.4.

## Run
Requirements: Node 22 (`npm` with `--legacy-peer-deps`), plus `pnpm` for 10170's "before" run, `curl`, `git` and `setsid` (util-linux). Each install is about 200 MB, so run in a scratch directory.

```bash
cd local-repro-study/runs/12929 && ./run.sh 4.20260312.1 && ./run.sh 4.20260730.0   # before / after
cd ../14255 && ./run.sh 4.99.0 && ./run.sh 4.98.0 && ./run.sh 4.152.0
cd ../12706 && ./run.sh 4.69.0 && ./run.sh 4.152.0
cd ../13609 && ./run.sh 4.84.0 && ./run.sh 4.152.0
cd ../13578 && ./run.sh 1.31.2 7.3.2 4.81.1 && ./run.sh 1.65.0 8.3.5 4.152.0
cd ../13790 && ./run.sh old && ./run.sh new
cd ../14107 && ./run.sh old && ./run.sh new
cd ../10170 && ./run_old.sh && ./run_min.sh 1.30.2 4.1.2 7.3.2 && ./run_min.sh 1.65.0 4.1.12 8.3.5
```

Each server-based script starts `wrangler dev` or `vite` on a fixed local port in its own process group. Afterwards it stops only that group: no `pkill` and no system-wide kills.

Re-run check (2026-10-26, from a clean copy of this folder): 12929 gave `ERR_MODULE_PARSE … Unexpected token (4:14)` on miniflare 4.20260312.1 and `200 hello` on 4.20260730.0. 14255 on wrangler 4.99.0 gave `GET / -> 404, /projects -> 200`. Both match `data/results.jsonl`, and no listener or `workerd` process was left behind. The other issues were not re-run in this check.

**Not committed:** `node_modules/`, the `v_*` / `min_*` / `old` / `new` install folders, `.wrangler/` state, the cloned repo and the gist. All of them are recreated by the scripts.
