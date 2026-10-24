"""Shared pieces: fault injection, the deterministic planner policy, compensation and outcome classing."""
import re
from sandbox import Sandbox, InverseUnavailable, WindowClosed, diff


class InjectedFault(Exception):
    pass


OK_RE = re.compile(r"OK:step=(\d+)")
FAULT_RE = re.compile(r"FAULT:step=(\d+)")


class Run:
    """One run: a plan (list of (op,arg)), a fault step (1-based) and kind ('pre' | 'post')."""

    def __init__(self, plan, fault_step, fault_kind):
        self.plan, self.fault_step, self.fault_kind = plan, fault_step, fault_kind
        self.sb = Sandbox()
        self.s0 = self.sb.snapshot()
        self.exec_count = {}  # step -> number of times the tool body ran
        self.op_to_step = {op: i + 1 for i, (op, _) in enumerate(plan)}

    def execute(self, op, step):
        """Tool body shared by every framework adapter."""
        step = int(step)
        self.exec_count[step] = self.exec_count.get(step, 0) + 1
        exp_op, arg = self.plan[step - 1]
        assert exp_op == op, (op, step)
        if step == self.fault_step and self.fault_kind == "pre":
            raise InjectedFault(f"FAULT:step={step} injected before effect")
        self.sb.apply(op, arg)
        self.sb.effect_log[-1]["step"] = step
        if step == self.fault_step and self.fault_kind == "post":
            raise InjectedFault(f"FAULT:step={step} injected after effect (timeout)")
        return f"OK:step={step}"


def next_step(texts, n):
    """Deterministic stub-planner policy over the tool results visible in the framework's history.
    Returns the next step number, or None to finish (all done, or a fault was seen -> abort)."""
    joined = "\n".join(texts)
    if FAULT_RE.search(joined):
        return None
    oks = [int(x) for x in OK_RE.findall(joined)]
    nxt = (max(oks) if oks else 0) + 1
    return nxt if nxt <= n else None


def compensate(run, entries):
    """Saga compensation: invert the given effect-log entries in reverse order. Returns per-entry results."""
    results = []
    for e in reversed(entries):
        try:
            run.sb.invert(e)
            results.append({"step": e["step"], "op": e["op"], "result": "inverted"})
        except InverseUnavailable:
            results.append({"step": e["step"], "op": e["op"], "result": "irreversible"})
        except WindowClosed:
            results.append({"step": e["step"], "op": e["op"], "result": "window_closed"})
        except Exception as x:  # inverse itself failed (e.g. already undone)
            results.append({"step": e["step"], "op": e["op"], "result": f"inverse_error: {type(x).__name__}"})
    return results


def trace_entries(run, ok_steps):
    """One effect-log entry per step the framework trace reports as successful (first application)."""
    out = []
    for s in sorted(ok_steps):
        for e in run.sb.effect_log:
            if e.get("step") == s:
                out.append(e); break
    return out


def classify(run, comp):
    res = diff(run.s0, run.sb.snapshot())
    if any(c["result"] in ("irreversible", "window_closed") for c in comp):
        outcome = "stuck"
    elif not res:
        outcome = "clean"
    else:
        outcome = "residue"
    return outcome, res
