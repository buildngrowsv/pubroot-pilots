"""Repro for mem0ai/mem0#6277: update(metadata=...) can overwrite user_id/agent_id/run_id.
Offline: a deterministic hash embedder replaces the embedding provider; add(infer=False) skips the LLM.
No network calls are made (OPENAI_API_KEY is a dummy value only so the default LLM client can be constructed)."""
import hashlib, json, os, sys, tempfile, inspect
os.environ.setdefault("OPENAI_API_KEY", "unused-placeholder")
os.environ["MEM0_TELEMETRY"] = "False"
from importlib.metadata import version
import mem0.utils.factory as factory
from mem0.embeddings.base import EmbeddingBase


class HashEmbedder(EmbeddingBase):
    def __init__(self, config=None):
        super().__init__(config)
    def embed(self, text, memory_action=None):
        h = hashlib.sha256(text.encode()).digest()
        return [b / 255.0 for b in h] * 4  # 128 dims


factory.EmbedderFactory.create = classmethod(lambda cls, *a, **k: HashEmbedder())
from mem0 import Memory

d = tempfile.mkdtemp(prefix="mem0-repro-")
cfg = {"vector_store": {"provider": "qdrant", "config": {"path": os.path.join(d, "q"), "embedding_model_dims": 128, "collection_name": "repro"}},
       "history_db_path": os.path.join(d, "history.db")}
m = Memory.from_config(cfg)


def get_all(uid):
    try:
        r = m.get_all(user_id=uid)
    except Exception as e:  # newer API wants filters
        r = m.get_all(filters={"user_id": uid})
    return [x["id"] for x in (r.get("results", r) if isinstance(r, dict) else r)]


def add(text, uid):
    try:
        return m.add(text, user_id=uid, infer=False)
    except Exception:
        return m.add(text, filters={"user_id": uid}, infer=False)


out = {"mem0ai": version("mem0ai"), "update_signature": str(inspect.signature(m.update))}
res = add("I love pizza", "alice")
mid = res["results"][0]["id"]
out["memory_id"] = mid
out["alice_before"] = get_all("alice")
m.update(mid, metadata={"category": "food", "user_id": "bob"})
out["alice_after"] = get_all("alice")
out["bob_after"] = get_all("bob")
stored = m.get(mid)
out["stored_user_id"] = stored.get("user_id")
out["stored_metadata"] = stored.get("metadata")
try:
    m.delete_all(user_id="alice")
except Exception as e:
    m.delete_all(filters={"user_id": "alice"}) if "filters" in str(e) else None
out["exists_after_alice_delete_all"] = m.get(mid) is not None
out["reproduced"] = (mid not in out["alice_after"]) and (mid in out["bob_after"])
print(json.dumps(out, indent=1, default=str))
