#!/usr/bin/env python3
import json, sys, re
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.testclient import TestClient
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from flask import Flask
from flask_cors import CORS

cases = json.load(sys.stdin)
out_starlette, out_flask = [], []

def starlette_check(c):
    opts = c["options"]
    kwargs = {"allow_origins": []}
    if opts.get("origin") == "__REGEX__":
        kwargs["allow_origin_regex"] = opts["origin_regex"]
    elif opts.get("origin") == "*":
        kwargs["allow_origins"] = ["*"]
    elif isinstance(opts.get("origin"), list):
        kwargs["allow_origins"] = opts["origin"]
    elif isinstance(opts.get("origin"), str):
        kwargs["allow_origins"] = [opts["origin"]]
    if opts.get("credentials"):
        kwargs["allow_credentials"] = True
    async def homepage(request):
        return PlainTextResponse("ok")
    app = Starlette(routes=[Route("/", homepage)])
    app.add_middleware(CORSMiddleware, **kwargs)
    client = TestClient(app)
    headers = {}
    if c.get("origin") is not None:
        headers["Origin"] = c["origin"]
    r = client.get("/", headers=headers)
    return {"id": c["id"], "acao": r.headers.get("access-control-allow-origin"), "acac": r.headers.get("access-control-allow-credentials"), "status": r.status_code}

def flask_check(c):
    app = Flask(c["id"])
    opts = c["options"]
    cors_kwargs = {}
    if opts.get("origin") == "__REGEX__":
        cors_kwargs["origins"] = opts["origin_regex"]
    elif opts.get("origin") is not None:
        cors_kwargs["origins"] = opts["origin"]
    if opts.get("credentials"):
        cors_kwargs["supports_credentials"] = True
    CORS(app, **cors_kwargs)
    @app.get("/")
    def index():
        return "ok"
    client = app.test_client()
    headers = {}
    if c.get("origin") is not None:
        headers["Origin"] = c["origin"]
    r = client.get("/", headers=headers)
    return {"id": c["id"], "acao": r.headers.get("Access-Control-Allow-Origin"), "acac": r.headers.get("Access-Control-Allow-Credentials"), "status": r.status_code}

for c in cases:
    try:
        out_starlette.append(starlette_check(c))
    except Exception as e:
        out_starlette.append({"id": c["id"], "error": str(e), "acao": None, "acac": None})
    try:
        out_flask.append(flask_check(c))
    except Exception as e:
        out_flask.append({"id": c["id"], "error": str(e), "acao": None, "acac": None})
json.dump({"starlette": out_starlette, "flask_cors": out_flask}, sys.stdout)
