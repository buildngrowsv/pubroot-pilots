#!/usr/bin/env python3
"""Reads cases.json on stdin; for each library writes the first N fire times strictly after START (UTC) or an error.
croniter: croniter(expr, start).get_next(datetime) (defaults: day_or=True, implement_cron_bug=False)
cronsim:  iter(CronSim(expr, start))
APScheduler: CronTrigger.from_crontab(expr, timezone=UTC).get_next_fire_time(prev, now) chained
Each case runs under a 10 s alarm; a library that is still searching is recorded as TIMEOUT."""
import json, sys, signal, datetime as dt
from croniter import croniter
from cronsim import CronSim
from apscheduler.triggers.cron import CronTrigger
D = json.load(sys.stdin); N = D["n"]; UTC = dt.timezone.utc
START = dt.datetime.fromisoformat(D["start"].replace("Z", "+00:00"))
fmt = lambda t: t.astimezone(UTC).strftime("%Y-%m-%dT%H:%MZ") + ("" if t.second == 0 and t.microsecond == 0 else f"+{t.second}s")
class Timeout(Exception): pass
def alarm(*_): raise Timeout()
signal.signal(signal.SIGALRM, alarm)
def keep(gen):  # if a library raises after at least one time, keep the times found so far (same rule in every adapter)
    out = []
    try:
        for t in gen:
            out.append(fmt(t))
            if len(out) == N: break
    except Timeout: raise
    except Exception:
        if not out: raise
    return out
def r_croniter(e):
    it = croniter(e, START); return keep(it.get_next(dt.datetime) for _ in range(N))
def r_cronsim(e):
    return keep(iter(CronSim(e, START)))
def r_aps(e):
    trig = CronTrigger.from_crontab(e, timezone=UTC); out = []; prev = None; now = START
    while len(out) < N:
        t = trig.get_next_fire_time(prev, now)
        if t is None: break
        out.append(fmt(t)); prev = t; now = t + dt.timedelta(microseconds=1)
    return out
LIBS = {"croniter": r_croniter, "cronsim": r_cronsim, "apscheduler": r_aps}
res = {k: {} for k in LIBS}
for c in D["cases"]:
    for k, f in LIBS.items():
        signal.alarm(10)
        try: res[k][c["id"]] = {"ok": True, "times": f(c["expr"])}
        except Timeout: res[k][c["id"]] = {"ok": False, "err": "TIMEOUT"}
        except Exception as ex: res[k][c["id"]] = {"ok": False, "err": f"{type(ex).__name__}: {str(ex)[:60]}"}
        finally: signal.alarm(0)
print(json.dumps(res, indent=1))
