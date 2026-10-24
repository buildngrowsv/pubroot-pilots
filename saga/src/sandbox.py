"""Sandboxed stand-ins for tool side effects, with an explicit inverse per operation.

Every operation and every inverse advances a logical clock by one tick. On each tick:
  - emails pending for >= WINDOW ticks are dispatched (unsend then fails),
  - a consumer "mirror" clone runs `git fetch` without prune (it keeps refs it has seen).
The observable state used to judge rollback is `snapshot()`.
Repository effects use real git (subprocess); records use sqlite3; messaging is in-memory.
"""
import json, os, sqlite3, subprocess, tempfile, shutil

WINDOW = 3


class InverseUnavailable(Exception):
    """No inverse exists for this effect (irreversible)."""


class WindowClosed(Exception):
    """An inverse existed but its window has passed."""


def _git(cwd, *args):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


class Sandbox:
    def __init__(self, window=None):
        self.window = window if window is not None else WINDOW
        self.dir = tempfile.mkdtemp(prefix="saga-sbx-")
        env = {"GIT_AUTHOR_NAME": "sbx", "GIT_AUTHOR_EMAIL": "sbx@example.invalid",
               "GIT_COMMITTER_NAME": "sbx", "GIT_COMMITTER_EMAIL": "sbx@example.invalid",
               "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z", "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z"}
        os.environ.update(env)
        self.remote = os.path.join(self.dir, "remote.git")
        self.work = os.path.join(self.dir, "work")
        self.mirror = os.path.join(self.dir, "mirror")
        _git(self.dir, "init", "-q", "--bare", "-b", "main", self.remote)
        _git(self.dir, "init", "-q", "-b", "main", self.work)
        with open(os.path.join(self.work, "README"), "w") as f:
            f.write("seed\n")
        _git(self.work, "add", "README")
        _git(self.work, "commit", "-q", "-m", "seed")
        _git(self.work, "remote", "add", "origin", self.remote)
        _git(self.work, "push", "-q", "origin", "main")
        _git(self.dir, "clone", "-q", self.remote, self.mirror)
        self.db = sqlite3.connect(":memory:", check_same_thread=False)
        self.db.executescript(
            "create table records(tbl text, key text, val text, primary key(tbl,key));"
            "create table inventory(item text primary key, qty int);"
            "insert into inventory values('widget', 10);"
            "create table ledger(id integer primary key, amount int, kind text);"
            "create table account(id int primary key, balance int); insert into account values(1, 100);")
        self.clock = 0
        self.outbox_pending = []   # [ {id, to, body, sent_tick} ]
        self.outbox_delivered = []
        self.chat = []             # [ {id, text, deleted} ]
        self.calendar = {}
        self.sms_sent = []
        self.webhooks_sent = []
        self.effect_log = []       # ground truth: every applied effect, in order
        self._n = 0

    def close(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    # ---- clock ----
    def tick(self):
        self.clock += 1
        still = []
        for m in self.outbox_pending:
            (self.outbox_delivered if self.clock - m["sent_tick"] >= self.window else still).append(m)
        self.outbox_pending = still
        _git(self.mirror, "fetch", "-q", "origin")

    def _id(self):
        self._n += 1
        return self._n

    # ---- observable state ----
    def snapshot(self):
        def refs(cwd):
            out = _git(cwd, "for-each-ref", "--format=%(refname)")
            return sorted(out.splitlines())
        return {
            "work_refs": refs(self.work),
            "work_main_commits": int(_git(self.work, "rev-list", "--count", "main")),
            "work_main_tree": _git(self.work, "rev-parse", "main^{tree}"),
            "remote_refs": refs(self.remote),
            "mirror_refs": refs(self.mirror),
            "records": sorted(self.db.execute("select * from records").fetchall()),
            "inventory": sorted(self.db.execute("select * from inventory").fetchall()),
            "ledger_rows": self.db.execute("select count(*) from ledger").fetchone()[0],
            "balance": self.db.execute("select balance from account").fetchone()[0],
            "outbox_pending": len(self.outbox_pending),
            "outbox_delivered": len(self.outbox_delivered),
            "chat": [(c["text"] if not c["deleted"] else "<deleted>") for c in self.chat],
            "calendar": sorted(self.calendar),
            "sms_sent": len(self.sms_sent),
            "webhooks_sent": len(self.webhooks_sent),
        }

    # ---- operations: apply(arg) -> handle ; inverse(handle) ----
    def apply(self, op, arg):
        h = getattr(self, "op_" + op)(arg)
        self.effect_log.append({"op": op, "arg": arg, "handle": h, "tick": self.clock})
        self.tick()
        return h

    def invert(self, entry):
        try:
            getattr(self, "inv_" + entry["op"])(entry["handle"])
        finally:
            self.tick()

    def op_git_create_branch(self, name):
        _git(self.work, "branch", name); return name
    def inv_git_create_branch(self, name):
        _git(self.work, "branch", "-D", name)

    def op_git_commit_file(self, path):
        with open(os.path.join(self.work, path), "a") as f:
            f.write(f"line {self._id()}\n")
        _git(self.work, "add", path); _git(self.work, "commit", "-q", "-m", f"edit {path}")
        return _git(self.work, "rev-parse", "HEAD")
    def inv_git_commit_file(self, sha):  # shared-branch convention: revert, never rewrite
        _git(self.work, "revert", "--no-edit", sha)

    def op_git_push(self, branch):
        _git(self.work, "push", "-q", "origin", f"{branch}:{branch}"); return branch
    def inv_git_push(self, branch):
        _git(self.work, "push", "-q", "origin", "--delete", branch)

    def op_db_insert(self, key):
        tbl, k = key.split(":")
        self.db.execute("insert into records values(?,?,?)", (tbl, k, "v")); return key
    def inv_db_insert(self, key):
        tbl, k = key.split(":")
        self.db.execute("delete from records where tbl=? and key=?", (tbl, k))

    def op_db_update(self, item):
        old = self.db.execute("select qty from inventory where item=?", (item,)).fetchone()[0]
        self.db.execute("update inventory set qty=qty-1 where item=?", (item,)); return (item, old)
    def inv_db_update(self, h):
        self.db.execute("update inventory set qty=? where item=?", (h[1], h[0]))

    def op_pay_charge(self, amount):
        amount = int(amount)
        self.db.execute("insert into ledger(amount,kind) values(?, 'charge')", (amount,))
        self.db.execute("update account set balance=balance-? where id=1", (amount,)); return amount
    def inv_pay_charge(self, amount):  # refund: balance restored, ledger keeps both rows
        self.db.execute("insert into ledger(amount,kind) values(?, 'refund')", (-amount,))
        self.db.execute("update account set balance=balance+? where id=1", (amount,))

    def op_email_send(self, to):
        m = {"id": self._id(), "to": to, "sent_tick": self.clock}
        self.outbox_pending.append(m); return m["id"]
    def inv_email_send(self, mid):
        for m in self.outbox_pending:
            if m["id"] == mid:
                self.outbox_pending.remove(m); return
        raise WindowClosed(f"email {mid} already dispatched")

    def op_cal_create(self, name):
        self.calendar[name] = True; return name
    def inv_cal_create(self, name):
        self.calendar.pop(name)  # KeyError if already removed

    def op_chat_post(self, text):
        c = {"id": self._id(), "text": text, "deleted": False}
        self.chat.append(c); return c["id"]
    def inv_chat_post(self, cid):  # deletion leaves a tombstone
        for c in self.chat:
            if c["id"] == cid:
                c["deleted"] = True

    def op_sms_send(self, to):
        self.sms_sent.append(to); return to
    def inv_sms_send(self, h):
        raise InverseUnavailable("SMS cannot be recalled")

    def op_webhook_notify(self, url):
        self.webhooks_sent.append(url); return url
    def inv_webhook_notify(self, h):
        raise InverseUnavailable("partner already notified")


OPS = ["git_create_branch", "git_commit_file", "git_push", "db_insert", "db_update", "pay_charge",
       "email_send", "cal_create", "chat_post", "sms_send", "webhook_notify"]
ARGS = {"git_create_branch": "rel", "git_commit_file": "CHANGELOG", "git_push": "main",
        "db_insert": "orders:o1", "db_update": "widget", "pay_charge": "25", "email_send": "a@example.invalid",
        "cal_create": "slot1", "chat_post": "hello", "sms_send": "+10000000000", "webhook_notify": "https://partner.invalid/hook"}


def diff(a, b):
    return sorted(k for k in a if a[k] != b[k])


def label_operation(op, window=None):
    window = window if window is not None else WINDOW
    """Empirically label one operation: run it, invert immediately, then invert after the window."""
    out = {"op": op}
    sb = Sandbox(window)
    try:
        if op == "git_push":
            sb.apply("git_create_branch", "feat")
            arg = "feat"
        else:
            arg = ARGS[op]
        s0 = sb.snapshot()
        sb.apply(op, arg)
        try:
            sb.invert(sb.effect_log[-1])
            res = diff(s0, sb.snapshot())
            out["immediate"] = "restored" if not res else "residue"
            out["immediate_residue"] = res
        except InverseUnavailable as e:
            out["immediate"] = "no_inverse"; out["immediate_residue"] = [str(e)]
        except WindowClosed as e:
            out["immediate"] = "window_closed"; out["immediate_residue"] = [str(e)]
    finally:
        sb.close()
    sb = Sandbox(window)
    try:
        if op == "git_push":
            sb.apply("git_create_branch", "feat"); arg = "feat"
        else:
            arg = ARGS[op]
        s0 = sb.snapshot()
        sb.apply(op, arg)
        for _ in range(window + 1):
            sb.tick()
        try:
            sb.invert(sb.effect_log[-1])
            res = diff(s0, sb.snapshot())
            out["late"] = "restored" if not res else "residue"; out["late_residue"] = res
        except InverseUnavailable:
            out["late"] = "no_inverse"
        except WindowClosed as e:
            out["late"] = "window_closed"; out["late_residue"] = [str(e)]
    finally:
        sb.close()
    imm, late = out["immediate"], out["late"]
    if imm == "no_inverse":
        out["label"] = "irreversible"
    elif late == "window_closed":  # inverse exists only inside a window (possibly shorter than one tick)
        out["label"] = "windowed"
    elif imm == "restored" and late == "restored":
        out["label"] = "full"
    else:
        out["label"] = "partial"
    return out
