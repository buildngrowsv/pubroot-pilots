# cron-schedules

Supports the Pubroot draft "Same Cron Line, Different Next Run" (batch 7, 2026-11-16).

83 five-field cron expressions (`cases.json`, written by `gen_cases.py`) are run through nine libraries, each asked
for the first five fire times strictly after 2026-01-01T00:00:30Z in UTC: croniter 7.0.0, cronsim 2.8 and
APScheduler 3.11.3 (`CronTrigger.from_crontab`) in Python; cron-parser 5.10.6, croner 11.0.1 and cron 4.4.0 in
Node.js; robfig/cron v3.0.1 (`ParseStandard`), adhocore/gronx v1.20.7 and hashicorp/cronexpr v1.1.3 in Go.
The reading is cronie's crontab(5) (cronie-crond/cronie @ cb49729da91af528805aadf2faa4da27cb36edec), computed by the
brute-force scan `reading()` in `gen_cases.py`; 17 cases are marked OPEN (man page silent, Quartz/Jenkins extensions,
whitespace variants). Every (library, case) runs with a 10 s limit. cron-parser gets a fixed `hashSeed` so `H` is
reproducible. Note: the `cron` package caps its search at wall-clock now + 8 years, so far-future results depend on
the date of the run.

Real-world sample: `realworld/gha_cron.json` holds 137 distinct `schedule: - cron:` expressions (267 file
occurrences) from GitHub code search on 2026-11-16 (expressions and counts only; no repository names).

Reproduce (Node 24, Python 3.13, Go 1.27; Go modules pinned in go/go.mod and go/go.sum):

    cd js && npm ci && cd ..
    python3 -m venv .venv && .venv/bin/pip install -r py/requirements.txt
    PY=.venv/bin/python ./run_all.sh

Outputs: `results/{py,node,go}.json`, `results/rw_*.json`, `results/summary.json`, `results/rw_summary.json`,
`results/report.txt`, `results/versions.txt`. No network at run time, no keys. Cost: $0.
