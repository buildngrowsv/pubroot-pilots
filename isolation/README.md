# Session-isolation repros (paper 2026-253)

Paper: https://github.com/buildngrowsv/pubroot-website/issues/253

Five offline reproductions: mem0 #6277, agno #9319, llama_index #21774, google/adk-python #6167 (+ PR #6380 race), langgraphjs #2040. See the top-level [README](../README.md#2-isolation-repros-isolation-paper-2026-253) for versions, commands, expected outputs and limitations.

Example (no API keys):

```bash
python3 -m venv .venv-agno-2.8.6 && .venv-agno-2.8.6/bin/pip install -r requirements/agno-2.8.6.txt
.venv-agno-2.8.6/bin/python repro/agno_9319.py
```
