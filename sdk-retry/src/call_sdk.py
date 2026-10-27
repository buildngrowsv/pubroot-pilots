#!/usr/bin/env python3
"""Make ONE logical generation request with one SDK against the local stub, using the SDK's default
retry policy. Only the per-attempt timeout is lowered (to TIMEOUT_S) so the timeout scenario runs fast.
Usage: call_sdk.py <sdk> <run_id> <scenario>. Prints one JSON line: sdk, version, exception type, elapsed."""
import importlib.metadata as md, json, os, sys, time
sdk, run_id, scen = sys.argv[1:4]
T = float(os.environ.get("TIMEOUT_S", "1.0"))
B = f"http://127.0.0.1:8765/{run_id}/{scen}"
KEY = "stub-key-not-real"
XH = {"Idempotency-Key": f"caller-{run_id}"} if os.environ.get("CALLER_KEY") else None  # mitigation run: caller supplies a key
MSG = [{"role": "user", "content": "Render a 5-second clip of a lighthouse at dusk."}]
def run():
    if sdk == "openai":
        from openai import OpenAI; OpenAI(api_key=KEY, base_url=B + "/v1", timeout=T).chat.completions.create(model="stub", messages=MSG, extra_headers=XH)
    elif sdk == "anthropic":
        from anthropic import Anthropic; Anthropic(api_key=KEY, base_url=B, timeout=T).messages.create(model="stub", max_tokens=8, messages=MSG, extra_headers=XH)
    elif sdk == "groq":
        from groq import Groq; Groq(api_key=KEY, base_url=B, timeout=T).chat.completions.create(model="stub", messages=MSG, extra_headers=XH)
    elif sdk == "together":
        from together import Together; Together(api_key=KEY, base_url=B + "/v1", timeout=T).chat.completions.create(model="stub", messages=MSG, extra_headers=XH)
    elif sdk == "mistralai":
        from mistralai.client import Mistral; Mistral(api_key=KEY, server_url=B, timeout_ms=int(T * 1000)).chat.complete(model="stub", messages=MSG)
    elif sdk == "cohere":
        import cohere; cohere.ClientV2(api_key=KEY, base_url=B, timeout=T).chat(model="stub", messages=MSG)
    elif sdk == "google-genai":
        from google import genai; from google.genai import types
        client = genai.Client(api_key=KEY, http_options=types.HttpOptions(base_url=B, timeout=int(T * 1000)))  # keep a reference (v1 harness let it be GC-closed)
        client.models.generate_content(model="stub", contents=MSG[0]["content"])
    elif sdk == "replicate":
        import replicate; replicate.Client(api_token=KEY, base_url=B, timeout=T).predictions.create(version="0" * 64, input={"prompt": MSG[0]["content"]})
    elif sdk == "fal-client":
        os.environ["FAL_RUN_HOST"] = "127.0.0.1:8766"; os.environ["FAL_QUEUE_RUN_HOST"] = f"127.0.0.1:8766/{run_id}/{scen}"
        import fal_client; fal_client.SyncClient(key=KEY, default_timeout=T).submit("stub/model", arguments={"prompt": MSG[0]["content"]})
    else: raise SystemExit(f"unknown sdk {sdk}")
dist = {"mistralai": "mistralai", "google-genai": "google-genai", "fal-client": "fal-client"}.get(sdk, sdk)
t0 = time.time(); err = None
try: run()
except Exception as e: err = f"{type(e).__module__}.{type(e).__name__}: {str(e)[:160]}"
print(json.dumps(dict(sdk=sdk, version=md.version(dist), run_id=run_id, scenario=scen, timeout_s=T, elapsed_s=round(time.time() - t0, 2), error=err)))
