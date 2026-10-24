"""Saga compensation-coverage pilot. Usage: python run_pilot.py [--frameworks langgraph ag2 crewai] --out ../results"""
import argparse, json, os, platform, subprocess, sys, time, traceback
from importlib.metadata import version
from sandbox import OPS, label_operation, WINDOW
from plans import PLANS, irreversible_last
from harness import Run, compensate, classify, trace_entries, OK_RE

ADAPTERS = {}


def load(name):
    if name == "langgraph":
        from fw_langgraph import run_langgraph as f
    elif name == "ag2":
        from fw_ag2 import run_ag2 as f
    else:
        from fw_crewai import run_crewai as f
    return f


def one(fw, plan_name, order, fault_step, fault_kind, recovery):
    plan = PLANS[plan_name] if order == "original" else irreversible_last(PLANS[plan_name])
    run = Run(plan, fault_step, fault_kind)
    t0 = time.time()
    try:
        trace, native = ADAPTERS[fw](run)
    except Exception as e:
        run.sb.close()
        return {"framework": fw, "plan": plan_name, "order": order, "fault_step": fault_step, "fault_kind": fault_kind,
                "recovery": recovery, "harness_error": f"{type(e).__name__}: {e}", "tb": traceback.format_exc()[-1500:]}
    truth = [e["step"] for e in run.sb.effect_log if "step" in e]
    seen_ok = sorted({int(m) for t in trace for m in OK_RE.findall(t["content"] or "")})
    pre_residue = sorted(k for k in run.s0 if run.s0[k] != run.sb.snapshot()[k])
    if recovery == "none":
        comp = []
    elif recovery == "trace":
        comp = compensate(run, trace_entries(run, seen_ok))
    else:  # effect-log (oracle)
        comp = compensate(run, [e for e in run.sb.effect_log if "step" in e])
    outcome, residue = classify(run, comp)
    rec = {"framework": fw, "plan": plan_name, "order": order, "plan_ops": [o for o, _ in plan],
           "fault_step": fault_step, "fault_op": plan[fault_step - 1][0], "fault_kind": fault_kind, "recovery": recovery,
           "native": native, "trace_ok_steps": seen_ok, "effect_steps": truth,
           "untracked_effects": sorted(set(truth) - set(seen_ok)), "duplicate_effects": len(truth) - len(set(truth)), "exec_count": run.exec_count,
           "residue_before_recovery": pre_residue, "compensation": comp, "outcome": outcome, "residue": residue,
           "seconds": round(time.time() - t0, 3)}
    run.sb.close()
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frameworks", nargs="+", default=["langgraph", "ag2", "crewai"])
    ap.add_argument("--out", default="../results")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--window", type=int, default=None, help="email unsend window in ticks (default 3)")
    a = ap.parse_args()
    import sandbox
    if a.window is not None:
        sandbox.WINDOW = a.window
    os.makedirs(a.out, exist_ok=True)
    env = {"python": sys.version, "platform": platform.platform(), "window_ticks": __import__("sandbox").WINDOW,
           "git": subprocess.run(["git", "--version"], capture_output=True, text=True).stdout.strip(), "packages": {}}
    for p in ["langgraph", "langgraph-prebuilt", "langchain-core", "ag2", "crewai"]:
        try:
            env["packages"][p] = version(p)
        except Exception:
            env["packages"][p] = None
    json.dump(env, open(os.path.join(a.out, "environment.json"), "w"), indent=1)
    if not a.smoke:
        labels = [label_operation(op) for op in OPS]
        with open(os.path.join(a.out, "operation_labels.jsonl"), "w") as f:
            for l in labels:
                f.write(json.dumps(l) + "\n")
    for fw in a.frameworks:
        ADAPTERS[fw] = load(fw)
    path = os.path.join(a.out, "runs.jsonl" if not a.smoke else "smoke.jsonl")
    with open(path, "w") as f:
        for fw in a.frameworks:
            for plan_name in PLANS:
                for order in ["original", "irreversible_last"]:
                    for kind in ["pre", "post"]:
                        for step in range(1, 7):
                            for recovery in ["none", "trace", "effect_log"]:
                                if a.smoke and (plan_name != "order" or step not in (3, 6) or order != "original"):
                                    continue
                                rec = one(fw, plan_name, order, step, kind, recovery)
                                f.write(json.dumps(rec, default=str) + "\n"); f.flush()
                                print(fw, plan_name, order, kind, step, recovery, rec.get("outcome"), rec.get("harness_error", ""), flush=True)


if __name__ == "__main__":
    main()
