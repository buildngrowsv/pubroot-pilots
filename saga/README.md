# Saga compensation-coverage pilot (paper 2026-251)

Paper: https://github.com/buildngrowsv/pubroot-website/issues/251

See the top-level [README](../README.md#1-saga-pilot-saga-paper-2026-251) for what the pilot does, pinned versions, how the outputs map to the paper, and limitations.

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
(cd src && ../.venv/bin/python run_pilot.py --out ../results)     # 648 runs, no API keys
.venv/bin/python src/analyze.py                                   # -> results/summary.md
```
