"""Summarise reader outputs: per masked field, what AT-SPI exposes and whether redaction heuristics would catch it.
Heuristics evaluated (applied to the field's AT-SPI node):
  H_role : role name == 'password text'
  H_orca : reimplementation of stablyai/orca native/computer-use-linux/runtime.py is_secure_node @24cebf03:
           terms (password, passcode, secret, one-time code, verification code) or \\bpin\\b over role+name+accessible_id,
           or Atspi.StateType.PROTECTED (absent in libatspi 2.56 -> never true)
  H_orca_label : H_orca plus the names of labelled-by relation targets."""
import json, re, sys, os, glob, gi
gi.require_version("Atspi", "2.0"); from gi.repository import Atspi
H = os.path.dirname(os.path.abspath(__file__)); C = json.load(open(f"{H}/fixtures/canaries.json"))
MASKED = {"Password": "pw", "Account key": "ak"}
TERMS = ("password", "passcode", "secret", "one-time code", "verification code")
PROTECTED = getattr(Atspi.StateType, "PROTECTED", None)
def kw(s): return any(t in s for t in TERMS) or bool(re.search(r"(^|[^a-z0-9])pin([^a-z0-9]|$)", s))
WIDGET = {"gtk3": {"pw": "Gtk.Entry visibility=False", "ak": "Gtk.Entry visibility=False"},
          "gtk4": {"pw": "Gtk.PasswordEntry", "ak": "Gtk.Entry visibility=False"},
          "chrome": {"pw": "<input type=password>", "ak": "<input type=password>"},
          "firefox": {"pw": "<input type=password>", "ak": "<input type=password>"}}
reps = sorted(glob.glob(f"{H}/results/rep*")); rows = []
for rep in reps:
    for f in ["gtk3", "gtk4", "chrome", "firefox"]:
        r = json.load(open(f"{rep}/{f}.json")); typed = {t["target_path"]: t for t in r.get("typed", [])}
        for n in r["editable"]:
            labels = [x[1] for x in n["relations"] if x[0] == "labelled-by"]
            key = MASKED.get(n["name"]) or next((MASKED[l] for l in labels if l in MASKED), None)
            if not key: continue
            base = " ".join([(n["role"] or "").lower(), (n["name"] or "").lower(), (n.get("accessible_id") or "").lower()])
            h_orca = kw(base)  # PROTECTED branch is dead: Atspi has no such state
            t = typed.get(n["path"], {})
            ev = t.get("event_hits", {})
            ev_roles = sorted({e["src_role"] for e in t.get("events", []) if e["type"].startswith("object:text-changed")})
            rows.append({"rep": os.path.basename(rep), "toolkit": f, "toolkit_version": r.get("toolkit_version"), "widget": WIDGET[f][key],
                "label": labels[0] if labels else n["name"], "role": n["role"], "name": n["name"], "accessible_id": n.get("accessible_id"),
                "states": n["states"], "text_len": len(n.get("text") or ""), "canary_len": len(C[key]),
                "static_plaintext": C[key] in (n.get("text") or ""),
                "typed_focused": t.get("focused_before_typing"),
                "event_plaintext_old": bool(ev.get(key)), "event_plaintext_typed": bool(ev.get("typed")),
                "event_src_roles": ev_roles,
                "H_role": n["role"] == "password text", "H_orca": h_orca, "H_orca_label": h_orca or any(kw(l.lower()) for l in labels)})
for x in rows:
    x["snapshot_plaintext_missed_by_H_orca"] = x["static_plaintext"] and not x["H_orca"]
    x["event_plaintext"] = x["event_plaintext_old"] or x["event_plaintext_typed"]
    x["event_residual_if_filter_by_src_role"] = x["event_plaintext"] and "password text" not in x["event_src_roles"]
json.dump({"protected_state_in_libatspi": PROTECTED is not None, "atspi_version": str(Atspi.get_version()), "rows": rows},
          open(f"{H}/results/summary.json", "w"), indent=1)
# Markdown table from rep1 + reproducibility check
r1 = [x for x in rows if x["rep"] == "rep1"]
same = all(json.dumps({k: v for k, v in a.items() if k != "rep"}, sort_keys=True) == json.dumps({k: v for k, v in b.items() if k != "rep"}, sort_keys=True)
           for a, b in zip(r1, [x for x in rows if x["rep"] == "rep2"]))
L = ["| toolkit | widget | label | AT-SPI role | name | Text.get_text plaintext | text-changed plaintext | H_role | H_orca | H_orca+label |", "|---|---|---|---|---|---|---|---|---|---|"]
for x in r1:
    L.append(f'| {x["toolkit"]} {x["toolkit_version"]} | {x["widget"]} | {x["label"]} | {x["role"]} | {x["name"]!r} | {"PLAINTEXT" if x["static_plaintext"] else "masked"} | {"PLAINTEXT" if x["event_plaintext"] else "masked"} | {x["H_role"]} | {x["H_orca"]} | {x["H_orca_label"]} |')
L.append(f"\nrep1 == rep2 (all fields identical): {same}; Atspi.StateType.PROTECTED present: {PROTECTED is not None}; libatspi {Atspi.get_version()}")
L.append(f"masked fields: {len(r1)}; fields with plaintext in Text.get_text: {sum(x['static_plaintext'] for x in r1)}; fields with plaintext in events: {sum(x['event_plaintext'] for x in r1)}; "
         f"snapshot plaintext missed by H_orca: {sum(x['snapshot_plaintext_missed_by_H_orca'] for x in r1)}; event plaintext missed by a source-role filter: {sum(x['event_residual_if_filter_by_src_role'] for x in r1)}; "
         f"masked text length == secret length: {sum(x['text_len']==x['canary_len'] for x in r1)}/{len(r1)}")
open(f"{H}/results/summary.md", "w").write("\n".join(L) + "\n"); print("\n".join(L))
