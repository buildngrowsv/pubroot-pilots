#!/usr/bin/env python3
"""Generate one shared, synthetic case set for four webhook signing schemes.
All secrets and bodies are synthetic. Timestamps are relative to NOW (the generation time), so run the
verifiers within a minute of generating; boundary cases sit 30 s inside/outside the 300 s tolerance.
Each case has: scheme, id, cls (control | canonicalization | config | parsing), headers, body, secret, ref
(the verdict a strict reading of the scheme's own documentation implies: accept | reject | unspecified)."""
import base64, hashlib, hmac, json, sys, time
NOW = int(time.time())
BODY = '{"id":"evt_synthetic_0001","type":"test.event","data":{"amount":1234}}'
BODY_ALT = BODY.replace("1234", "1235")
BODY_RESER = json.dumps(json.loads(BODY), indent=1)
S_SECRET = "whsec_synthetic_stripe_secret_0001"
W_KEY = b"synthetic-standard-webhooks-key-0001"
W_SECRET = "whsec_" + base64.b64encode(W_KEY).decode()
K_SECRET = "synthetic_slack_signing_secret_0001"
G_SECRET = "synthetic_github_secret_0001"
OTHER = "whsec_some_other_secret_0002"
def hm(key, msg): return hmac.new(key, msg.encode(), hashlib.sha256).digest()
def s_sig(ts, body=BODY, secret=S_SECRET): return hm(secret.encode(), f"{ts}.{body}").hex()
def w_sig(mid, ts, body=BODY, key=W_KEY): return base64.b64encode(hm(key, f"{mid}.{ts}.{body}")).decode()
def k_sig(ts, body=BODY, secret=K_SECRET): return "v0=" + hm(secret.encode(), f"v0:{ts}:{body}").hex()
def g_sig(body=BODY, secret=G_SECRET): return "sha256=" + hm(secret.encode(), body).hex()
cases = []
def add(scheme, cid, cls, ref, headers, body=BODY, secret=None, note="", tolerance=None):
    c = dict(scheme=scheme, id=f"{scheme}-{cid}", cls=cls, ref=ref, headers=headers, body=body,
             secret=secret if secret is not None else dict(S=S_SECRET, W=W_SECRET, K=K_SECRET, G=G_SECRET)[scheme], note=note)
    if tolerance is not None: c["tolerance"] = tolerance
    cases.append(c)
# ---------- Stripe (Stripe-Signature: t=<ts>,v1=<hex>) ----------
def S(cid, cls, ref, header, **kw): add("S", cid, cls, ref, {"stripe-signature": header}, **kw)
T = NOW
S("valid", "control", "accept", f"t={T},v1={s_sig(T)}")
S("age_270", "control", "accept", f"t={T-270},v1={s_sig(T-270)}")
S("age_330", "control", "reject", f"t={T-330},v1={s_sig(T-330)}")
S("future_330", "control", "unspecified", f"t={T+330},v1={s_sig(T+330)}", note="docs only say to reject a timestamp that is 'too old'; tolerance 'between the timestamp and the current time' is ambiguous on direction")
S("future_1d", "control", "unspecified", f"t={T+86400},v1={s_sig(T+86400)}")
S("body_altered", "control", "reject", f"t={T},v1={s_sig(T)}", body=BODY_ALT)
S("body_reserialized", "control", "reject", f"t={T},v1={s_sig(T)}", body=BODY_RESER)
S("wrong_secret", "control", "reject", f"t={T},v1={s_sig(T, secret=OTHER)}")
S("multi_valid_last", "control", "accept", f"t={T},v1={s_sig(T, secret=OTHER)},v1={s_sig(T)}")
S("multi_none_valid", "control", "reject", f"t={T},v1={s_sig(T, secret=OTHER)},v1={'0'*64}")
S("scheme_v0_only", "control", "reject", f"t={T},v0={s_sig(T)}")
S("empty_v1", "control", "reject", f"t={T},v1=")
S("ts_ms", "control", "unspecified", f"t={T*1000},v1={s_sig(T*1000)}", note="milliseconds = far future; direction unspecified by Stripe docs")
S("tolerance_0_old", "config", "unspecified", f"t={T-86400*30},v1={s_sig(T-86400*30)}", tolerance=0, note="docs: 0 disables recency check")
S("empty_secret", "config", "reject", f"t={T},v1={hm(b'', f'{T}.{BODY}').hex()}", secret="")
for cid, tsh in [("ts_plus", f"+{T}"), ("ts_leading_zero", f"0{T}"), ("ts_float_0", f"{T}.0"), ("ts_underscore", f"{T//1000000}_{T%1000000:06d}"),
                 ("ts_space", f" {T}"), ("ts_exp", f"{T/1e9:.9f}e9")]:
    S(cid + "_sig_canonical", "canonicalization", "reject", f"t={tsh},v1={s_sig(T)}", note=f"header t={tsh!r}, signature over canonical {T}")
S("ts_leading_zero_sig_literal", "canonicalization", "unspecified", f"t=0{T},v1={s_sig('0'+str(T))}", note="signature over the literal header string")
S("upper_hex", "canonicalization", "unspecified", f"t={T},v1={s_sig(T).upper()}")
S("multi_empty_then_valid", "parsing", "accept", f"t={T},v1=,v1={s_sig(T)}", note="an empty v1 entry before the valid one")
S("space_after_comma", "parsing", "unspecified", f"t={T}, v1={s_sig(T)}")
O = T - 86400
S("dup_t_old_first", "parsing", "reject", f"t={O},v1={s_sig(O)},t={T}", note="replayed old delivery with a fresh t appended")
S("dup_t_new_first", "parsing", "reject", f"t={T},t={O},v1={s_sig(O)}", note="fresh t prepended to an old delivery")
# ---------- Standard Webhooks (webhook-id / webhook-timestamp / webhook-signature: v1,<b64>) ----------
MID = "msg_synthetic_0001"
def W(cid, cls, ref, ts_hdr, sig_hdr, mid=MID, **kw):
    add("W", cid, cls, ref, {"webhook-id": mid, "webhook-timestamp": ts_hdr, "webhook-signature": sig_hdr}, **kw)
W("valid", "control", "accept", str(T), "v1," + w_sig(MID, T))
W("age_270", "control", "accept", str(T-270), "v1," + w_sig(MID, T-270))
W("age_330", "control", "reject", str(T-330), "v1," + w_sig(MID, T-330))
W("future_330", "control", "reject", str(T+330), "v1," + w_sig(MID, T+330))
W("future_1d", "control", "reject", str(T+86400), "v1," + w_sig(MID, T+86400))
W("body_altered", "control", "reject", str(T), "v1," + w_sig(MID, T), body=BODY_ALT)
W("body_reserialized", "control", "reject", str(T), "v1," + w_sig(MID, T), body=BODY_RESER)
W("wrong_key", "control", "reject", str(T), "v1," + w_sig(MID, T, key=b"other-key-0002"))
W("id_swapped", "control", "reject", str(T), "v1," + w_sig("msg_other", T))
W("multi_valid_last", "control", "accept", str(T), "v1," + w_sig(MID, T, key=b"other-key-0002") + " v1," + w_sig(MID, T))
W("multi_none_valid", "control", "reject", str(T), "v1," + w_sig(MID, T, key=b"other-key-0002") + " v1," + base64.b64encode(b"\0"*32).decode())
W("scheme_v2", "control", "reject", str(T), "v2," + w_sig(MID, T))
W("scheme_v1a_only", "control", "reject", str(T), "v1a," + w_sig(MID, T), note="v1a is the asymmetric scheme; an HMAC value under v1a must not verify")
W("empty_sig", "control", "reject", str(T), "v1,")
W("ts_ms", "control", "reject", str(T*1000), "v1," + w_sig(MID, T*1000))
W("ts_nonnumeric", "control", "reject", "abc", "v1," + w_sig(MID, "abc"))
for cid, tsh in [("ts_plus", f"+{T}"), ("ts_leading_zero", f"0{T}"), ("ts_float_0", f"{T}.0"), ("ts_float_9", f"{T}.9"), ("ts_underscore", f"{T//1000000}_{T%1000000:06d}"),
                 ("ts_space", f" {T}"), ("ts_exp", f"{T/1e9:.9f}e9")]:
    W(cid + "_sig_canonical", "canonicalization", "reject", tsh, "v1," + w_sig(MID, T), note=f"header {tsh!r}, signature over canonical {T}")
W("ts_float_9_sig_literal", "canonicalization", "unspecified", f"{T}.9", "v1," + w_sig(MID, f"{T}.9"), note="signature over the literal header")
W("b64url_nopad", "canonicalization", "unspecified", str(T), "v1," + w_sig(MID, T).replace("+", "-").replace("/", "_").rstrip("="))
W("double_space", "parsing", "unspecified", str(T), "v1," + w_sig(MID, T, key=b"other-key-0002") + "  v1," + w_sig(MID, T))
W("dup_ts_joined", "parsing", "reject", f"{T-86400}, {T}", "v1," + w_sig(MID, T-86400), note="two timestamp headers joined by the HTTP stack; old signature")
W("secret_no_prefix", "config", "unspecified", str(T), "v1," + w_sig(MID, T), secret=base64.b64encode(W_KEY).decode())
W("empty_secret", "config", "reject", str(T), "v1," + base64.b64encode(hm(b"", f"{MID}.{T}.{BODY}")).decode(), secret="whsec_")
# ---------- Slack (X-Slack-Signature: v0=<hex>, X-Slack-Request-Timestamp) ----------
def K(cid, cls, ref, ts_hdr, sig, **kw): add("K", cid, cls, ref, {"x-slack-request-timestamp": ts_hdr, "x-slack-signature": sig}, **kw)
K("valid", "control", "accept", str(T), k_sig(T))
K("age_270", "control", "accept", str(T-270), k_sig(T-270))
K("age_330", "control", "reject", str(T-330), k_sig(T-330))
K("future_330", "control", "reject", str(T+330), k_sig(T+330), note="docs: 'more than five minutes from local time'")
K("future_1d", "control", "reject", str(T+86400), k_sig(T+86400))
K("body_altered", "control", "reject", str(T), k_sig(T), body=BODY_ALT)
K("wrong_secret", "control", "reject", str(T), k_sig(T, secret="other"))
K("empty_sig", "control", "reject", str(T), "v0=")
K("ts_ms", "control", "reject", str(T*1000), k_sig(T*1000))
K("ts_nonnumeric", "control", "reject", "abc", k_sig("abc"))
for cid, tsh in [("ts_plus", f"+{T}"), ("ts_leading_zero", f"0{T}"), ("ts_float_0", f"{T}.0"), ("ts_space", f" {T}")]:
    K(cid + "_sig_literal", "canonicalization", "unspecified", tsh, k_sig(tsh), note="signature over the literal header string")
K("upper_hex", "canonicalization", "unspecified", str(T), "v0=" + k_sig(T)[3:].upper())
K("empty_secret", "config", "reject", str(T), "v0=" + hm(b"", f"v0:{T}:{BODY}").hex(), secret="")
# ---------- GitHub (X-Hub-Signature-256: sha256=<hex>; no timestamp) ----------
def G(cid, cls, ref, sig, **kw): add("G", cid, cls, ref, {"x-hub-signature-256": sig}, **kw)
G("valid", "control", "accept", g_sig())
G("body_altered", "control", "reject", g_sig(), body=BODY_ALT)
G("wrong_secret", "control", "reject", g_sig(secret="other"))
G("sha1_prefix", "control", "reject", "sha1=" + hmac.new(G_SECRET.encode(), BODY.encode(), hashlib.sha1).hexdigest())
G("no_prefix", "control", "unspecified", g_sig()[7:])
G("empty_sig", "control", "reject", "sha256=")
G("upper_hex", "canonicalization", "unspecified", "sha256=" + g_sig()[7:].upper())
G("trailing_garbage", "canonicalization", "unspecified", g_sig() + " junk", note="non-hex text after the digest")
G("prefix_upper", "canonicalization", "unspecified", "SHA256=" + g_sig()[7:])
G("replay_old", "control", "unspecified", g_sig(), note="scheme has no timestamp: any captured delivery verifies forever")
G("empty_secret", "config", "reject", "sha256=" + hm(b"", BODY).hex(), secret="")
json.dump(dict(generated_at=NOW, n=len(cases), cases=cases), open(sys.argv[1] if len(sys.argv) > 1 else "cases.json", "w"), indent=1)
print(len(cases), "cases; NOW", NOW)
