"""Check for google/adk-python#6167 (closed by reporter as not a bug) and the later PR #6380 race.
Part 1 (isolation claim from #6167): many users write sessions concurrently; each user's search must return only its own data.
Part 2 (#6380): writer threads add sessions for one user while reader threads search the same user; count
'dictionary changed size during iteration' errors. Offline; no model calls."""
import asyncio, json, sys, threading, time, uuid
from importlib.metadata import version
from google.adk.memory import InMemoryMemoryService
from google.adk.sessions import Session
from google.adk.events import Event
from google.genai import types


def mk_session(app, user, sid, words):
    ev = [Event(author="user", invocation_id=str(uuid.uuid4()), content=types.Content(role="user", parts=[types.Part(text=w)])) for w in words]
    return Session(app_name=app, user_id=user, id=sid, events=ev, state={})


async def part1(n_users=200):
    mem = InMemoryMemoryService()
    canaries = {f"user-{i}": f"canary{i:04d}" for i in range(n_users)}
    await asyncio.gather(*[mem.add_session_to_memory(mk_session("app", u, f"s-{u}", [s, "shared"])) for u, s in canaries.items()])
    # threaded writers too
    def tw(i):
        asyncio.run(mem.add_session_to_memory(mk_session("app2", f"user-{i}", f"t-{i}", [f"tcanary{i:04d}"])))
    ths = [threading.Thread(target=tw, args=(i,)) for i in range(n_users)]
    [t.start() for t in ths]; [t.join() for t in ths]
    cross = 0; own_missing = 0
    for u, s in canaries.items():
        r = await mem.search_memory(app_name="app", user_id=u, query=" ".join(list(canaries.values())[:50] + [s]))
        texts = [p.text for m in r.memories for p in m.content.parts]
        cross += sum(1 for t in texts if t.startswith("canary") and t != s)
        own_missing += 0 if s in texts else 1
        r2 = await mem.search_memory(app_name="app2", user_id=u, query=s)  # other app must not see app data
        cross += len(r2.memories)
    return {"users": n_users, "cross_user_or_cross_app_hits": cross, "own_missing": own_missing}


def part2(seconds=8.0, writers=4, readers=4):
    mem = InMemoryMemoryService()
    stop = time.time() + seconds
    errors, searches, adds = [], [0], [0]
    lock = threading.Lock()
    def w(k):
        i = 0
        while time.time() < stop:
            asyncio.run(mem.add_session_to_memory(mk_session("app", "u", f"w{k}-{i}", ["alpha"])))
            i += 1
            with lock: adds[0] += 1
    def r():
        while time.time() < stop:
            try:
                asyncio.run(mem.search_memory(app_name="app", user_id="u", query="alpha"))
            except RuntimeError as e:
                with lock: errors.append(str(e)[:80])
            with lock: searches[0] += 1
    ts = [threading.Thread(target=w, args=(k,)) for k in range(writers)] + [threading.Thread(target=r) for _ in range(readers)]
    [t.start() for t in ts]; [t.join() for t in ts]
    return {"seconds": seconds, "adds": adds[0], "searches": searches[0], "runtime_errors": len(errors), "error_samples": sorted(set(errors))[:3]}


out = {"google-adk": version("google-adk"), "python": sys.version.split()[0]}
out["part1_isolation"] = asyncio.run(part1())
out["part2_concurrent_read_write"] = part2()
print(json.dumps(out, indent=1))
