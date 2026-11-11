"""Werkzeug (Flask request.accept_mimetypes.best_match), Django HttpRequest.get_preferred_type, Falcon Request.client_prefers."""
import json, sys
import django
from django.conf import settings
settings.configure(ALLOWED_HOSTS=["*"]); django.setup()
from django.http import HttpRequest
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request as WRequest
import falcon.testing
cases = json.load(sys.stdin)
def guard(f):
    try: return f()
    except Exception as e: return "ERR " + type(e).__name__
def wz(c):
    h = {} if c["accept"] is None else {"Accept": c["accept"]}
    return WRequest(EnvironBuilder(headers=h).get_environ()).accept_mimetypes.best_match(c["offers"])
def dj(c):
    r = HttpRequest()
    if c["accept"] is not None: r.META["HTTP_ACCEPT"] = c["accept"]
    return r.get_preferred_type(c["offers"])
def fa(c):
    h = {} if c["accept"] is None else {"Accept": c["accept"]}
    return falcon.testing.create_req(headers=h).client_prefers(c["offers"])
out = {n: [{"id": c["id"], "choice": guard(lambda: f(c))} for c in cases] for n, f in (("werkzeug", wz), ("django", dj), ("falcon", fa))}
json.dump(out, sys.stdout, indent=1); print()
