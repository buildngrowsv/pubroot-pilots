# How often does an unpadded base64url signature crash (vs reject) the Python Standard Webhooks / Svix verifiers? 2000 random bodies.
import base64, hmac, hashlib, time, os, json, collections
from standardwebhooks.webhooks import Webhook as SW, WebhookVerificationError as SWE
from svix.webhooks import Webhook as SV, WebhookVerificationError as SVE
key = b"synthetic-standard-webhooks-key-0001"; secret = "whsec_" + base64.b64encode(key).decode()
out = collections.Counter()
for i in range(2000):
    body = json.dumps({"n": i, "r": os.urandom(6).hex()}); ts = str(int(time.time())); mid = f"msg_{i}"
    sig = base64.b64encode(hmac.new(key, f"{mid}.{ts}.{body}".encode(), hashlib.sha256).digest()).decode()
    u = sig.replace("+", "-").replace("/", "_").rstrip("=")
    h = {"webhook-id": mid, "webhook-timestamp": ts, "webhook-signature": "v1," + u}
    for name, W, E in (("standardwebhooks", SW, SWE), ("svix", SV, SVE)):
        try: W(secret).verify(body, h); v = "accept"
        except E: v = "reject"
        except Exception: v = "crash"
        out[(name, v, ("-" in u or "_" in u))] += 1
for k, n in sorted(out.items()): print(k, n)
