"""agno #9319 (dup #8334): per-user entity memory collides across users. Local SQLite, no LLM, no network.
Script follows the issue's reproduction; prints JSON."""
import json, os, sys, tempfile, sqlite3, importlib.metadata as md
os.environ.setdefault("AGNO_TELEMETRY", "false")
from agno.db.sqlite import SqliteDb
from agno.learn import EntityMemoryConfig
from agno.learn.stores.entity_memory import EntityMemoryStore
d = tempfile.mkdtemp(); f = os.path.join(d, "repro_entity.db")
db = SqliteDb(db_file=f)
store = EntityMemoryStore(config=EntityMemoryConfig(namespace="user", db=db))
out = {"agno": md.version("agno")}
out["a_write"] = str(store.remember_about(entity="Acme", entity_type="company", facts=["CANARY-ALICE renewal at $50k"], user_id="alice@corp.com"))
out["b_write"] = str(store.remember_about(entity="Acme", entity_type="company", facts=["CANARY-BOB they churned"], user_id="bob@corp.com"))
reads = {}
for u in ("alice@corp.com", "bob@corp.com"):
    e = store.get(entity_id="acme", entity_type="company", user_id=u, namespace="user")
    reads[u] = None if e is None else [x.get("content") if isinstance(x, dict) else str(x) for x in (e.facts or [])]
out["reads"] = reads
con = sqlite3.connect(f)
tabs = [r[0] for r in con.execute("select name from sqlite_master where type='table'")]
rows = []
for t in tabs:
    cols = [c[1] for c in con.execute(f"pragma table_info({t})")]
    if "learning_id" in cols:
        for r in con.execute(f"select * from {t}"):
            r = dict(zip(cols, r)); c = r.get("content")
            rows.append({"table": t, "learning_id": r["learning_id"], "user_id": r.get("user_id"),
                         "content_has_alice": "CANARY-ALICE" in str(c), "content_has_bob": "CANARY-BOB" in str(c)})
out["rows"] = rows
alice, bob = reads["alice@corp.com"] or [], reads["bob@corp.com"] or []
out["alice_sees_bob_canary"] = any("CANARY-BOB" in str(x) for x in alice)
out["alice_lost_own_canary"] = not any("CANARY-ALICE" in str(x) for x in alice)
out["bob_cannot_read_own"] = not any("CANARY-BOB" in str(x) for x in bob)
out["reproduced"] = out["alice_sees_bob_canary"] or out["alice_lost_own_canary"] or out["bob_cannot_read_own"]
print(json.dumps(out, indent=1))
