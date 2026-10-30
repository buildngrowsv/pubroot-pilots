"""AT-SPI reader used as a stand-in for a computer-use agent's accessibility-tree observer.
Usage: python3 reader.py <app-name-substring> <fixture-id> <out.json> [--type]
Dumps the app's tree (role, name, description, states, interfaces, attributes, Text contents), scans every
string field for the synthetic canaries, and with --type focuses the field labelled 'Password' (2nd editable node),
clears it and types a fresh canary with xdotool while recording AT-SPI events (text-changed etc.)."""
import gi, json, sys, time, subprocess, os
gi.require_version("Atspi", "2.0"); from gi.repository import Atspi, GLib
NAME, FID, OUT = sys.argv[1:4]; TYPE = "--type" in sys.argv
C = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "canaries.json")))

def find_app(timeout=60):
    t0 = time.time()
    while time.time() - t0 < timeout:
        d = Atspi.get_desktop(0)
        for i in range(max(d.get_child_count(), 0)):
            a = d.get_child_at_index(i)
            try:
                if a and NAME.lower() in (a.get_name() or "").lower(): return a
            except Exception: pass
        time.sleep(1)
    return None

def safe(f, *a):
    try: return f(*a)
    except Exception as e: return None

def node_info(o, path):
    r = {"path": path, "role": safe(o.get_role_name), "name": safe(o.get_name), "description": safe(o.get_description)}
    ss = safe(o.get_state_set); r["states"] = sorted(s.value_nick for s in ss.get_states()) if ss else []
    r["interfaces"] = safe(o.get_interfaces) or []
    r["accessible_id"] = safe(o.get_accessible_id)
    r["attributes"] = safe(o.get_attributes) or {}
    if "Text" in r["interfaces"]:
        n = safe(Atspi.Text.get_character_count, o); r["char_count"] = n
        r["text"] = safe(Atspi.Text.get_text, o, 0, n if n and n > 0 else -1)
    if "Value" in r["interfaces"]: r["value"] = safe(Atspi.Value.get_current_value, o)
    rels = []
    for rel in safe(o.get_relation_set) or []:
        for j in range(rel.get_n_targets()):
            t = rel.get_target(j); rels.append([rel.get_relation_type().value_nick, safe(t.get_name), safe(t.get_role_name)])
    r["relations"] = rels
    return r

def walk(o, path="0", out=None, depth=0):
    out = [] if out is None else out
    if o is None or depth > 80 or len(out) > 20000: return out
    out.append(node_info(o, path)); out[-1]["_obj"] = o
    for i in range(max(safe(o.get_child_count) or 0, 0)):
        walk(safe(o.get_child_at_index, i), f"{path}.{i}", out, depth + 1)
    return out

def scan(nodes, events=()):
    hits = {k: [] for k in C}
    for n in nodes:
        for f in ("name", "description", "text", "attributes", "relations"):
            s = json.dumps(n.get(f), ensure_ascii=False)
            for k, v in C.items():
                if v in s: hits[k].append([n["path"], n["role"], f])
    for e in events:
        for k, v in C.items():
            if v in json.dumps(e, ensure_ascii=False): hits[k].append(["event", e["type"], e.get("src_role")])
    # keystroke-level reconstruction: concatenate per-source text-changed:insert payloads
    rec = {}
    for e in events:
        if e["type"].startswith("object:text-changed:insert") and isinstance(e["any_data"], str):
            rec.setdefault(f'{e.get("src_role")}|{e.get("src_name")}', []).append(e["any_data"])
    for src, parts in rec.items():
        s = "".join(parts)
        for k, v in C.items():
            if v in s: hits[k].append(["event-reconstructed", "object:text-changed:insert", src])
    return hits

def dump(app):
    ns = walk(app); 
    return ns

app = find_app()
if app is None: json.dump({"fixture": FID, "error": "app not found on a11y bus"}, open(OUT, "w"), indent=1); sys.exit(1)
time.sleep(1.5)
nodes = dump(app)
editable = [n for n in nodes if "editable" in n["states"] and n["role"] not in ("document web", "document frame")]
for n in editable:
    e = safe(Atspi.Component.get_extents, n["_obj"], Atspi.CoordType.SCREEN); n["extents"] = [e.x, e.y, e.width, e.height] if e else None
editable.sort(key=lambda n: (n["extents"] or [0, 1e9])[1])  # document (top-to-bottom) order
res = {"fixture": FID, "app_name": safe(app.get_name), "toolkit": safe(app.get_toolkit_name), "toolkit_version": safe(app.get_toolkit_version),
       "n_nodes": len(nodes), "editable": [{k: v for k, v in n.items() if k != "_obj"} for n in editable],
       "static_hits": scan(nodes)}
def typed_phase(tgt):
    events = []
    def cb(ev):
        d = ev.any_data
        try: d = d if isinstance(d, (str, int, float, bool)) or d is None else str(d)
        except Exception: d = "?"
        events.append({"type": ev.type, "detail1": ev.detail1, "detail2": ev.detail2, "any_data": d,
                       "src_role": safe(ev.source.get_role_name) if ev.source else None, "src_name": safe(ev.source.get_name) if ev.source else None})
    lst = Atspi.EventListener.new(cb)
    TYPES = ["object:text-changed", "object:text-caret-moved", "object:property-change:accessible-name",
             "object:property-change:accessible-description", "object:property-change:accessible-value", "object:text-selection-changed",
             "object:state-changed", "window:activate", "object:announcement"]
    for t in TYPES: lst.register(t)
    comp = tgt["_obj"]; info = {"grab_focus": safe(Atspi.Component.grab_focus, comp), "focus_method": "grab_focus"}
    def focused():
        ss = safe(comp.get_state_set); return bool(ss and ss.contains(Atspi.StateType.FOCUSED))
    def act():
        if not focused():
            info["focus_method"] = "click"
            wext = safe(Atspi.Component.get_extents, comp, Atspi.CoordType.WINDOW)
            title = safe(app.get_child_at_index(0).get_name) if safe(app.get_child_count) else None
            wid = subprocess.run(["xdotool", "search", "--name", title or FID], capture_output=True, text=True).stdout.split()
            if wid and wext:
                g = subprocess.run(["xdotool", "getwindowgeometry", "--shell", wid[-1]], capture_output=True, text=True).stdout
                gx = dict(l.split("=") for l in g.split() if "=" in l)
                subprocess.run(["xdotool", "windowactivate", "--sync", wid[-1]])
                subprocess.run(["xdotool", "mousemove", str(int(gx["X"]) + wext.x + wext.width // 2), str(int(gx["Y"]) + wext.y + wext.height // 2), "click", "1"])
            time.sleep(0.3)
            for _ in range(8):  # correct with Tab / shift+Tab until the AT-SPI target reports focus
                if focused(): break
                info["focus_method"] = "click+tab"; subprocess.run(["xdotool", "key", "Tab"]); time.sleep(0.25)
        info["focused_before_typing"] = focused()
        if info["focused_before_typing"]:
            subprocess.run(["xdotool", "key", "--delay", "60", "ctrl+a", "BackSpace"]); time.sleep(0.3)
            subprocess.run(["xdotool", "type", "--delay", "60", C["typed"]])
        return False
    loop = GLib.MainLoop(); GLib.timeout_add(400, act); GLib.timeout_add(5000, lambda: loop.quit() or False); loop.run()
    for t in TYPES: lst.deregister(t)
    after = next((n for n in dump(app) if n["path"] == tgt["path"]), None)
    info.update({"target_path": tgt["path"], "target_role": tgt["role"], "events": events, "n_events": len(events), "event_hits": scan([], events),
                 "target_text_after": after.get("text") if after else None})
    return info

if TYPE:
    res["typed"] = [typed_phase(t) for t in editable[1:]]
json.dump(res, open(OUT, "w"), indent=1, ensure_ascii=False, default=str)
print(FID, "nodes", len(nodes), "editable", len(editable), "static", {k: len(v) for k, v in res["static_hits"].items()},
      "typed", [(t["target_role"], t["focused_before_typing"], [k for k, v in t["event_hits"].items() if v]) for t in res.get("typed", [])])
