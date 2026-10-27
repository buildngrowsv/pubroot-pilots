# pubroot-pilots

Code for the pilot studies submitted (or prepared for submission) to Pubroot. Repository: https://github.com/buildngrowsv/pubroot-pilots

| Folder | Paper | Submission |
|---|---|---|
| [`saga/`](saga/) | *Can Agent Sagas Roll Back? A Compensation-Coverage Benchmark Protocol with a Pilot on LangGraph, AG2 and CrewAI* (2026-251) | https://github.com/buildngrowsv/pubroot-website/issues/251 |
| [`isolation/`](isolation/) | *Do Session-Isolation Bug Reports in LLM Agent Frameworks Reproduce? A Case Study of Five Closed Issues, with a Mining Protocol* (2026-253) | https://github.com/buildngrowsv/pubroot-website/issues/253 |
| [`sdk-retry/`](sdk-retry/) | *Do Generative AI Client SDKs Make Retries Idempotent? A Local Audit of Nine Python SDKs Against a Failure-Injecting Stub* | not yet submitted |
| [`issue-form-parsers/`](issue-form-parsers/) | *Heading Collisions in GitHub Issue-Form Body Parsers: A Differential Test of Three Open-Source Parsers on Agent-Style Markdown* | not yet submitted |
| [`local-repro-study/`](local-repro-study/) | *Do Closed Workers Toolchain Bug Reports Still Reproduce Offline? A Pinned-Version Replay of Ten Sampled wrangler and Miniflare Issues* | not yet submitted |
| [`voice-approval-gate/`](voice-approval-gate/) | *Spoken Approval as a Human Gate for Agent Actions: How Often Do Streaming Transcripts Turn a Hesitant Reply into a False Yes?* | not yet submitted |

Everything runs offline (network is needed only to install packages; `issue-form-parsers/fetch_vendor.sh` also clones one parser from GitHub; `local-repro-study` fetches public GitHub issue data, one public repo and one public gist; `voice-approval-gate/fetch_model.sh` downloads one public speech model). **No API keys are needed and no model is called:** every model is a deterministic stub, every tool acts on a local sandbox, and storage is local (SQLite, local Qdrant, in-memory). No third-party code is vendored; frameworks are installed from PyPI/npm with the pinned versions below (or cloned at a pinned commit). No certificates or keys are committed: the `sdk-retry` stub generates a throwaway localhost certificate at run time. All paths are relative to the folder they are run from.

Original runs: saga and isolation 2026-10-23; sdk-retry and issue-form-parsers 2026-10-25; local-repro-study and voice-approval-gate 2026-10-26. Linux x86_64, Python 3.13.5, git 2.47.3, Node v20.19.2 (local-repro-study: Node v22.23.4 except issue 12929).

---

## 1. Saga pilot (`saga/`), paper 2026-251

### What it is

A compensation-coverage pilot. Three frameworks run three hand-written 6-step plans against a local sandbox in which each of 11 operations has an explicit inverse.

- **Frameworks:** LangGraph (`create_react_agent` + `InMemorySaver`), AG2 (`Agent` API with a stub `LLMClient`), CrewAI (one agent, stub `BaseLLM` in ReAct text mode). Adapters: `src/fw_langgraph.py`, `src/fw_ag2.py`, `src/fw_crewai.py`.
- **Sandbox** (`src/sandbox.py`): a real git repo in a temporary directory (bare remote, work tree, and a mirror that fetches without prune on every tick), in-memory SQLite, and an outbox, chat, calendar, SMS, webhooks and a payment ledger. A logical clock ticks once per operation and once per inverse. Email is dispatched once it has been pending for `WINDOW` ticks (default 3).
- **Plans** (`src/plans.py`): release, order and meeting, each in the original order and in `irreversible_last` order (a stable move of `sms_send` and `webhook_notify` to the end).
- **Faults** (`src/harness.py`): each step in turn is faulted, `pre` (raises before its effect) or `post` (applies the effect, then raises).
- **Recovery modes:** `none`; `trace` (saga over the steps the framework's own history reports as successful); `effect_log` (saga over an oracle log of every applied effect).
- **Outcomes:** `clean` (snapshot equals the pre-plan state), `residue`, `stuck` (an irreversible inverse or a closed window was hit).
- **Size:** 3 frameworks × 3 plans × 2 orders × 6 steps × 2 fault kinds × 3 recovery modes = **648 runs**.

### Pinned versions

`saga/requirements.txt` (direct dependencies): langgraph 1.2.17, langgraph-prebuilt 1.1.1, langchain-core 1.7.0, ag2 1.2.1, crewai 1.15.30. `saga/requirements.lock.txt` is the full `pip freeze` of the original environment.

### Install and run (no keys)

```bash
cd saga
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt        # or: -r requirements.lock.txt for the exact original environment
(cd src && ../.venv/bin/python run_pilot.py --out ../results)          # all 648 runs -> results/runs.jsonl
.venv/bin/python src/analyze.py                                        # -> results/summary.md
for W in 1 6 12; do (cd src && ../.venv/bin/python run_pilot.py --frameworks langgraph --window $W --out ../results/window_sweep_W$W); done
.venv/bin/python src/window_sweep.py                                   # -> results/window_sweep.md
```

Single-framework run: `(cd src && ../.venv/bin/python run_pilot.py --frameworks langgraph --out ../results)` (216 runs). `--smoke` runs a small subset.

### Expected outputs and the paper's numbers

The committed `saga/results/summary.md`, `window_sweep.md`, `environment.json` and `operation_labels.jsonl` are the outputs of the original run. The raw `runs.jsonl` files are not committed; they are regenerated by the commands above. Runs are deterministic, so a re-run should give the same counts.

| Paper number | Where it comes from |
|---|---|
| Operation labels: full 4, partial 4, windowed 1, irreversible 2 | `operation_labels.jsonl`; "Label counts" in `summary.md` |
| Native behaviour on an injected exception: LangGraph raised in 72/72 runs, AG2 in 0/72, CrewAI in 8/72; CrewAI re-executed the faulting tool (mean 8.67, max 30) with duplicate effects in 28 runs | "Native framework behaviour" table |
| Post-effect faults: the framework trace omitted an applied effect in 108/108 runs (36/36 per framework) | "Aggregates" |
| Trace-based saga, original order, non-trivial runs: clean 12/99 (12.1%), stuck 37 (37.4%); `irreversible_last`: clean 12/99, stuck 31 (31.3%) | "Aggregates" |
| Effect-log saga, original order, non-trivial runs: clean 23/99 (23.2%), stuck 47 (47.5%); `irreversible_last`: clean 23/99, stuck 41 (41.4%) | "Aggregates" |
| Window-closed inverses: 154, all on `email_send` | "Compensation action results" |
| Window sensitivity (LangGraph, effect-log): window 1/3/6/12 → window-closed inverses 16/12/4/0 | `window_sweep.md` |

---

## 2. Isolation repros (`isolation/`), paper 2026-253

### What it is

Offline reproductions of five closed session/memory-isolation issues, each run on the affected version and on a fixed or current version.

| Script | Issue | Versions run | Result in the original run |
|---|---|---|---|
| `repro/mem0_6277.py` | mem0ai/mem0#6277, `update(metadata=…)` overwrites `user_id` | mem0ai 2.0.12, 2.0.13, 2.2.1 | Reproduced on 2.0.12 (memory moved to bob; `delete_all(alice)` left it); not on 2.0.13 / 2.2.1 |
| `repro/agno_9319.py` | agno-agi/agno#9319, per-user entity memory collides across users | agno 2.8.6, 3.0.0, 3.1.10 | Reproduced on 2.8.6 (one row owned by alice holding bob's canary; bob reads `None`); not on 3.x |
| `repro/llamaidx_21774.py` | run-llama/llama_index#21774, `AgentWorkflow` leaks `initial_state` mutations | llama-index-core 0.14.19, 0.14.22, 0.14.23 with llama-index-workflows 2.20.0; 0.14.19–0.14.25 with workflows 2.26.1 | Reproduced on 0.14.19 and 0.14.22 with workflows 2.20.0 (2nd run counter 2, log [1, 2]); not on 0.14.23; not on any version with workflows 2.26.1 |
| `repro/adk_6167.py` | google/adk-python#6167 (closed as not a bug) and the race fixed by PR #6380 | google-adk 2.3.0, 2.13.0 | Isolation claim not reproduced (0 cross-user hits, 200 users). Race reproduced on 2.3.0 (201, 139, 118 RuntimeErrors in 3 runs of 8 s); 0 on 2.13.0 |
| `repro/lgjs_2040.mjs` | langchain-ai/langgraphjs#2040, concurrent-thread contamination | @langchain/langgraph 1.2.0, 1.4.2, 1.4.4, 1.5.2 | Not reproduced in scenarios A and C. Scenario B (nested invoke from inside a node) inherits the parent's configurable on 1.4.4+; this is the documented change from PR #2531, not the #2040 bug |

Stubs and harness changes: mem0 uses a SHA-256 hash embedder monkeypatched into `EmbedderFactory.create` and `add(..., infer=False)` (no LLM call; `OPENAI_API_KEY` is set to a placeholder only so the default client can be constructed, and it is never used). LlamaIndex uses a scripted subclass of `MockFunctionCallingLLM`. Agno, ADK and LangGraph.js make no model calls.

### Pinned versions

`isolation/requirements/<pkg>-<version>.txt` holds the direct pins for each environment, and `<pkg>-<version>.lock.txt` the full `pip freeze` of the original venv. LangGraph.js pins are in `requirements/langgraphjs-<version>.package.json` (@langchain/core 1.3.0, @langchain/langgraph-checkpoint 1.2.1).

### Install and run (no keys)

From `isolation/`:

```bash
# Python: one venv per version
for v in 2.0.12 2.0.13 2.2.1; do python3 -m venv .venv-mem0-$v && .venv-mem0-$v/bin/pip install -r requirements/mem0-$v.txt; done
for v in 2.0.12 2.0.13 2.2.1; do .venv-mem0-$v/bin/python repro/mem0_6277.py > results/mem0_6277_$v.json; done

for v in 2.8.6 3.0.0 3.1.10; do python3 -m venv .venv-agno-$v && .venv-agno-$v/bin/pip install -r requirements/agno-$v.txt; done
for v in 2.8.6 3.0.0 3.1.10; do .venv-agno-$v/bin/python repro/agno_9319.py > results/agno_9319_$v.json; done

for e in 0.14.19-wf2.20.0 0.14.22-wf2.20.0 0.14.23-wf2.20.0 0.14.19-wf2.26.1 0.14.22-wf2.26.1 0.14.23-wf2.26.1 0.14.25-wf2.26.1; do
  python3 -m venv .venv-llamaidx-$e && .venv-llamaidx-$e/bin/pip install -r requirements/llamaindex-$e.txt
  .venv-llamaidx-$e/bin/python repro/llamaidx_21774.py > results/llamaidx_21774_$e.json
done

for v in 2.3.0 2.13.0; do python3 -m venv .venv-adk-$v && .venv-adk-$v/bin/pip install -r requirements/adk-$v.txt; done
for v in 2.3.0 2.13.0; do .venv-adk-$v/bin/python repro/adk_6167.py > results/adk_6167_$v.json; done   # takes ~8 s each; repeats were saved as _rep2, _rep3

# Node (tested with v20.19.2)
for v in 1.2.0 1.4.2 1.4.4 1.5.2; do
  mkdir -p lgjs-$v && cp requirements/langgraphjs-$v.package.json lgjs-$v/package.json && (cd lgjs-$v && npm install)
  (cd lgjs-$v && node ../repro/lgjs_2040.mjs > ../results/lgjs_2040_lgjs-$v.json)
done
```

### Expected outputs and the paper's numbers

The committed `isolation/results/*.json` are the original outputs.

| Paper claim | Field(s) to check |
|---|---|
| 3 of 5 issues reproduced as reported (mem0, agno, llama_index), all fixed | see rows below |
| mem0 #6277 on 2.0.12 | `mem0_6277_2.0.12.json`: `reproduced: true`, `stored_user_id: "bob"`, `exists_after_alice_delete_all: true`; 2.0.13 / 2.2.1: `reproduced: false` |
| agno #9319 on 2.8.6 | `agno_9319_2.8.6.json`: one row, owner alice, content holding `CANARY-BOB`; bob reads `null`. 3.x: two rows, each user reads own canary |
| llama_index #21774 with workflows 2.20.0 | `llamaidx_21774_0.14.19-wf2.20.0.json`, `..._0.14.22-wf2.20.0.json`: `multi_agent_path.leaked: true`, `single_agent_path.leaked: true`; `0.14.23-wf2.20.0` and every `-wf2.26.1` file: not leaked |
| ADK: 0 cross-user hits; race 201/139/118 on 2.3.0, 0/0/0 on 2.13.0 | `part1_isolation.cross_user_or_cross_app_hits`, `part2_concurrent_read_write.runtime_errors` in `adk_6167_<v>[ _rep2 | _rep3 ].json` |
| LangGraph.js #2040 not reproduced | `scenarioA[*].wrongTool == 0`, `wrongCkpt == 0`, `boundConfigMutated == false`; `scenarioC[*].leaked == false`; `scenarioB.leaked` is `true` on 1.4.4 and 1.5.2 only |

---

---

## 3. SDK retry audit (`sdk-retry/`)

Nine generative-AI Python SDKs (openai 3.37.0, anthropic 2.3.0, groq 1.7.0, together 3.0.0, mistralai 3.5.0, cohere 7.3.0, google-genai 2.33.0, replicate 1.0.7, fal-client 1.0.3) make one logical call each against a local failure-injecting stub on 127.0.0.1, with fake keys. The failure modes are HTTP 500, timeout, and connection drop, with 3 reps of each. The stub logs every attempt. See [`sdk-retry/README.md`](sdk-retry/README.md) for install and run, the run-time localhost certificate, and limits.

| Paper number | Where it comes from |
|---|---|
| 81 logical calls produced 219 attempts, 138 of them duplicate POSTs; 48/81 calls retried | `sdk-retry/results/summary.md` (sum of the attempts column; raw rows in `attempts.jsonl`) |
| 0 attempts carried an idempotency header by default | `summary.md` (idempotency-header column) |
| A caller key passed via `extra_headers` was re-sent unchanged on every attempt in 12/12 runs | `sdk-retry/results/summary_callerkey.md` |

## 4. Issue-form parser differential (`issue-form-parsers/`)

19 synthetic issue-form bodies (3 controls) for a 4-field form, run through 8 subjects:
- stefanbuck/github-issue-parser v3.2.4 and v3.2.5, with and without a template;
- @github/issue-parser 2.0.0, with and without a template;
- @zentered/issue-forms-body-parser 3.0.0;
- a naive split baseline;
- a strict-AST reference.

See [`issue-form-parsers/README.md`](issue-form-parsers/README.md).

| Paper number | Where it comes from |
|---|---|
| Per-subject outcome counts (FIELD_CHANGED, DESC_ALTERED, EXTRA_KEYS, REJECT, OK) over 16 non-control cases | `issue-form-parsers/results/summary.md` |
| Raw outputs per case and subject (152 rows) | `issue-form-parsers/results/differential.jsonl` |

## 5. Workers toolchain issue replay (`local-repro-study/`)

10 issues were drawn with a fixed seed from 21 auto-eligible closed `cloudflare/workers-sdk` issues (frame of 77, from a public GitHub search). 8 were replayed on localhost at the reported ("before") and current ("after") package versions; 2 were excluded (Docker, interactive HMR). No Cloudflare account or deployment is used. Issue bodies, the reporter's repo and gist, and all `node_modules` installs are **not** included. Fetch scripts recreate them. See [`local-repro-study/README.md`](local-repro-study/README.md).

| Paper number | Where it comes from |
|---|---|
| 77 in frame, 21 auto-eligible, seed 20261026, first 10 drawn | `local-repro-study/data/frame.json`, `sample.py` → `data/sample.json` |
| 5 reproduced and fixed, 2 closed without code change, 1 not reproduced, 2 excluded; 2 of 8 replays verbatim | `local-repro-study/data/results.jsonl` (`class`, `edits`) |
| Observed before/after behaviour per issue | `data/results.jsonl` and `results/logs/` |

## 6. Spoken approval gate (`voice-approval-gate/`)

24 scripted replies × 6 espeak-ng voice settings = 144 synthetic clips, streamed into Vosk (small English model) in 100 ms chunks; four gate policies decide on the partial/final transcripts. No human voices and no personal data. The model and the generated audio are not included (`fetch_model.sh` downloads and checksums the model; `pilot.py` regenerates the clips). See [`voice-approval-gate/README.md`](voice-approval-gate/README.md).

| Paper number | Where it comes from |
|---|---|
| False approvals 51/45/2/5 of 96 and false rejections 14/18/18/37 of 48 for P1–P4 | `voice-approval-gate/results/summary.json` |
| Final transcript exact match 66/144; per-clip partials and finals | `summary.json`, `results/clips.jsonl` |

## Limitations

- **Stubs, not models.** All agents are driven by deterministic stub models. The pilots measure framework and harness mechanics, not how real LLMs behave under faults.
- **Saga sandbox is synthetic.** The 11 operations and their inverses are local simulations (with a real local git repo); real services have different windows and side effects. The email window (3 ticks) is a chosen parameter; `window_sweep.md` shows how results move with it. The three plans are hand-written, not sampled from real workloads.
- **Effect-log recovery uses an oracle** log of every applied effect, which real deployments may not have.
- **Isolation sample is small and a convenience sample:** five closed issues, not a random or exhaustive sample of agent frameworks.
- **Timing-dependent results.** The ADK race counts vary run to run (3 runs per version were recorded). The LlamaIndex leak depends on the llama-index-workflows version: it appears with 2.20.0 and not with 2.26.1; the change in between was not bisected.
- **Not reproduced ≠ not a bug.** LangGraph.js #2040 did not reproduce in three scenarios; the reporter's exact environment was not available.
- **sdk-retry** measures client behaviour against a stub only. Whether a real provider deduplicates or bills retried calls was not tested. **issue-form-parsers** uses synthetic bodies written by the same author as the strict reference.
- **local-repro-study** is a small seeded sample from one repository; "after" is the current npm release, not the fixing commit, and 6 of 8 replays needed recorded edits. **voice-approval-gate** uses synthetic TTS speech and one small ASR model, so the error counts say nothing about real human speakers.
- Results were produced on one Linux machine with Python 3.13.5 / Node 20.19.2; other platforms were not tested.

## License

MIT, see [LICENSE](LICENSE). Third-party frameworks are installed from their registries under their own licenses and are not included here.
