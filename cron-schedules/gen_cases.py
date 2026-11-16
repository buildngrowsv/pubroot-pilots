#!/usr/bin/env python3
"""Writes cases.json: five-field cron expressions and the reading of cronie's crontab(5) (cronie-crond/cronie
@ cb49729da91af528805aadf2faa4da27cb36edec, man/crontab.5), which extends POSIX crontab (IEEE Std 1003.1-2024)
with steps, names, 7 = Sunday and @-macros. expect: "INVALID", "OPEN" (the man page is silent or contradicts
the reference daemon; also Quartz/Jenkins extensions L, W, #, ?, H, which crontab(5) does not define and
which are reported in a separate support table), "NEVER" (valid but matches no date: either an empty schedule or a parse-time rejection is accepted), or the first N fire times strictly after START, in UTC, computed by reading() below,
a brute-force day/minute scan written directly from the man page (DOM/DOW: if both fields are restricted,
i.e. neither contains "*", a day matches when either matches; otherwise both must match)."""
import json, re, datetime as dt
START = "2026-01-01T00:00:30Z"; N = 5; HORIZON_YEARS = 40
MON = "jan feb mar apr may jun jul aug sep oct nov dec".split(); DOW = "sun mon tue wed thu fri sat".split()
MACRO = {"@yearly": "0 0 1 1 *", "@annually": "0 0 1 1 *", "@monthly": "0 0 1 * *", "@weekly": "0 0 * * 0",
         "@daily": "0 0 * * *", "@hourly": "0 * * * *"}
class Invalid(Exception): pass
class Open(Exception): pass  # crontab(5) is silent (e.g. a step after a single value)
def val(tok, lo, hi, names, base):
    if tok.isdigit(): v = int(tok)
    elif names and len(tok) == 3 and tok.lower() in names: v = names.index(tok.lower()) + base
    else: raise Invalid(tok)
    if not lo <= v <= hi: raise Invalid(tok)
    return v
def field(s, lo, hi, names=None, base=0, dow=False):
    out = set()
    for e in s.split(","):
        m = re.fullmatch(r"(\*|([0-9A-Za-z]+)(?:-([0-9A-Za-z]+))?)(?:/([0-9]+))?", e)
        if not m: raise Invalid(e)
        top = 7 if dow else hi
        if m.group(1) == "*": a, b = lo, hi
        else:
            a = val(m.group(2), lo, top, names, base); b = val(m.group(3), lo, top, names, base) if m.group(3) else None
            if b is None:
                if m.group(4): raise Open("step after single value")
                b = a
            if a > b: raise Invalid("reversed range")
        st = int(m.group(4)) if m.group(4) else 1
        if st == 0: raise Open("zero step")
        out |= {v % 7 if dow else v for v in range(a, b + 1, st)}
    return out
def reading(expr):
    e = MACRO.get(expr, expr)
    f = e.split(" ")
    if len(f) != 5 or any(x == "" for x in f): raise Invalid("field count")
    mi, ho = field(f[0], 0, 59), field(f[1], 0, 23)
    dom, mo = field(f[2], 1, 31), field(f[3], 1, 12, MON, 1)
    dw = field(f[4], 0, 6, DOW, 0, dow=True)
    restricted = "*" not in f[2] and "*" not in f[4]
    start = dt.datetime.fromisoformat(START.replace("Z", "+00:00")); day = start.date(); res = []
    end = day.replace(year=day.year + HORIZON_YEARS)
    while day < end and len(res) < N:
        if day.month in mo:
            dm, wm = day.day in dom, (day.isoweekday() % 7) in dw
            if (dm or wm) if restricted else (dm and wm):
                for h in sorted(ho):
                    for m in sorted(mi):
                        t = dt.datetime(day.year, day.month, day.day, h, m, tzinfo=dt.timezone.utc)
                        if t > start and len(res) < N: res.append(t.strftime("%Y-%m-%dT%H:%MZ"))
        day += dt.timedelta(days=1)
    return res
O = "OPEN"; I = "INVALID"; C = "cronie"
CASES = [
 ("B01", "basic", "* * * * *", C), ("B02", "basic", "0 * * * *", C), ("B03", "basic", "30 4 * * *", C),
 ("B04", "basic", "0 0 1 1 *", C), ("B05", "basic", "15,45 * * * *", C), ("B06", "basic", "0 9-17 * * *", C),
 ("B07", "basic", "0 0 * * 0", C), ("B08", "basic", "00 05 * * *", C), ("B09", "basic", "0 0 01 01 *", C),
 ("S01", "step", "*/15 * * * *", C), ("S02", "step", "0 */6 * * *", C), ("S03", "step", "0-30/10 * * * *", C),
 ("S04", "step", "0 0 */10 * *", C), ("S05", "step", "0 0 1-31/10 * *", C), ("S06", "step", "*/7 * * * *", C),
 ("S07", "step", "0 */23 * * *", C), ("S08", "step", "0 0 */45 * *", C), ("S09", "step", "0 0 1 */5 *", C),
 ("S10", "step", "0 23/2,1-10/2 * * *", O), ("S11", "step", "5/15 * * * *", O), ("S12", "step", "*/0 * * * *", O),
 ("S13", "step", "20-59/5 1-1 * * *", C), ("S14", "step", "0 0 */3 * *", C),
 ("D01", "dom-dow", "30 4 1,15 * 5", C), ("D02", "dom-dow", "0 0 13 * 5", C), ("D03", "dom-dow", "0 9 1-7 * 1", C),
 ("D04", "dom-dow", "0 9 */2 * 1", C), ("D05", "dom-dow", "0 0 1 * 1-5", C), ("D06", "dom-dow", "0 0 * 6 1", C),
 ("D07", "dom-dow", "0 0 31 * *", C), ("D08", "dom-dow", "0 0 30 2 *", "never"), ("D09", "dom-dow", "0 0 29 2 *", C),
 ("D10", "dom-dow", "0 0 29 2 1", C), ("D11", "dom-dow", "1 1 */32,1-7 * 2", O), ("D12", "dom-dow", "0 10 */14 * 3", C),
 ("D13", "dom-dow", "0 4 1-7 * */7", C),
 ("N01", "names", "0 0 * * MON", C), ("N02", "names", "0 0 * * mon", C), ("N03", "names", "0 0 * * Mon-Fri", C),
 ("N04", "names", "0 0 1 JAN,JUL *", C), ("N05", "names", "0 0 1 jan-mar *", C), ("N06", "names", "0 0 * * SUN-SAT", C),
 ("N07", "names", "0 0 * * MONDAY", C), ("N08", "names", "0 0 * * FRI-MON", C), ("N09", "names", "0 0 * * 1-5/2", C),
 ("N10", "names", "0 0 * * MON-FRI/2", C), ("N11", "names", "0 0 1 Jan *", C),
 ("W01", "sunday7", "0 0 * * 7", C), ("W02", "sunday7", "0 0 * * 0,7", C), ("W03", "sunday7", "0 0 * * 5-7", C),
 ("W04", "sunday7", "0 0 * * 8", C), ("W05", "sunday7", "0 0 * * 6-0", C),
 ("R01", "range", "60 * * * *", C), ("R02", "range", "* 24 * * *", C), ("R03", "range", "* * 0 * *", C),
 ("R04", "range", "* * 32 * *", C), ("R05", "range", "* * * 13 *", C), ("R06", "range", "* * * 0 *", C),
 ("R07", "range", "5-1 * * * *", C), ("R08", "range", "* * * *", C), ("R09", "range", "* * * * * *", O),
 ("R10", "range", "", C), ("R11", "range", "1,,2 * * * *", C), ("R12", "range", "1- * * * *", C), ("R13", "range", "+5 * * * *", C),
 ("M01", "macro", "@daily", C), ("M02", "macro", "@hourly", C), ("M03", "macro", "@weekly", C), ("M04", "macro", "@monthly", C),
 ("M05", "macro", "@yearly", C), ("M06", "macro", "@annually", C), ("M07", "macro", "@midnight", O), ("M08", "macro", "@reboot", O),
 ("X01", "extension", "0 0 L * *", O), ("X02", "extension", "0 0 * * 5L", O), ("X03", "extension", "0 0 * * 1#2", O),
 ("X04", "extension", "0 0 ? * *", O), ("X05", "extension", "H * * * *", O), ("X06", "extension", "0 0 15W * *", O),
 ("F01", "format", "0  0 * * *", O), ("F02", "format", " 0 0 * * *", O), ("F03", "format", "0 0 * * * ", O), ("F04", "format", "0\t0 * * *", O),
]
def main():
    out = []
    for cid, g, e, how in CASES:
        if how == O: exp = O
        elif how == "never": exp = "NEVER"; assert reading(e) == []
        else:
            try: exp = reading(e)
            except Invalid: exp = I
        out.append(dict(id=cid, group=g, expr=e, expect=exp))
    assert len({c["id"] for c in out}) == len(out)
    json.dump(dict(start=START, n=N, cases=out), open("cases.json", "w"), indent=1)
    print(len(out), "cases;", sum(c["expect"] == I for c in out), "invalid;", sum(c["expect"] == O for c in out), "open")
if __name__ == "__main__": main()
