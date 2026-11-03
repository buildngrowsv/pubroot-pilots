#!/usr/bin/env python3
"""Run the shared case set against official Python verifiers. Output: JSONL rows (subject, case, verdict, detail)."""
import json, sys, platform, importlib.metadata as md
cases = json.load(open(sys.argv[1]))["cases"]; out = open(sys.argv[2], "w")
def vers(p):
    try: return md.version(p)
    except Exception: return "?"
def stripe_v(c):
    import stripe
    tol = c.get("tolerance", stripe.Webhook.DEFAULT_TOLERANCE)
    stripe.WebhookSignature.verify_header(c["body"], c["headers"]["stripe-signature"], c["secret"], tolerance=tol); return True
def sw_v(c):
    from standardwebhooks.webhooks import Webhook
    Webhook(c["secret"]).verify(c["body"], dict(c["headers"])); return True
def svix_v(c):
    from svix.webhooks import Webhook
    Webhook(c["secret"]).verify(c["body"], dict(c["headers"])); return True
def slack_v(c):
    from slack_sdk.signature import SignatureVerifier
    h = c["headers"]; return SignatureVerifier(c["secret"]).is_valid(c["body"], h["x-slack-request-timestamp"], h["x-slack-signature"])
SUBJ = {"S": [("py-stripe " + vers("stripe"), stripe_v)], "W": [("py-standardwebhooks " + vers("standardwebhooks"), sw_v), ("py-svix " + vers("svix"), svix_v)],
        "K": [("py-slack_sdk " + vers("slack_sdk"), slack_v)], "G": []}
for c in cases:
    for name, fn in SUBJ[c["scheme"]]:
        try: r = fn(c); v, d = ("accept" if r else "reject"), ("returned " + str(r))
        except Exception as e:
            v = "reject" if "VerificationError" in type(e).__name__ else "crash"; d = f"{type(e).__name__}: {str(e)[:120]}"
        out.write(json.dumps(dict(runtime=f"CPython {platform.python_version()}", subject=name, case=c["id"], scheme=c["scheme"], cls=c["cls"], ref=c["ref"], verdict=v, detail=d)) + "\n")
print("done")
