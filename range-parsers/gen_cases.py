#!/usr/bin/env python3
"""Generate the fixed Range-header case list (cases.json) and the two fixture files (data/r100.txt, data/r0.txt)."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
C = []
def add(g, v, size=100, note=""):
    C.append({"id": f"R{len(C)+1:02d}", "group": g, "size": size, "range": v, "note": note})
# A. single well-formed ranges
add("single", "bytes=0-9"); add("single", "bytes=10-19"); add("single", "bytes=0-0"); add("single", "bytes=99-99")
add("single", "bytes=50-", note="open-ended"); add("single", "bytes=-10", note="suffix")
add("single", "bytes=-100", note="suffix == length"); add("single", "bytes=-200", note="suffix > length")
add("single", "bytes=0-199", note="last-pos past end"); add("single", "bytes=0-3145727", note="real-world: crawler cap")
# B. unsatisfiable
add("unsat", "bytes=100-", note="first-pos == length"); add("unsat", "bytes=100-150"); add("unsat", "bytes=200-300")
add("unsat", "bytes=-0", note="zero-length suffix")
# C. invalid single
add("invalid", "bytes=10-5", note="last < first"); add("invalid", "bytes="); add("invalid", "bytes=-")
add("invalid", "bytes=abc"); add("invalid", "bytes=--5"); add("invalid", "bytes=5--10"); add("invalid", "bytes=-5-10")
add("invalid", "bytes=0-9;x"); add("invalid", "bytes=0-9x")
# D. multi-range
add("multi", "bytes=0-9,20-29"); add("multi", "bytes=0-9,5-14", note="overlap"); add("multi", "bytes=0-9,10-19", note="adjacent")
add("multi", "bytes=20-29,0-9", note="descending"); add("multi", "bytes=0-9,200-300", note="one unsatisfiable")
add("multi", "bytes=200-300,300-400", note="all unsatisfiable"); add("multi", "bytes=0-9,10-5", note="one invalid")
add("multi", "bytes=0-9,0-9,0-9", note="three identical"); add("multi", "bytes=-10,0-9", note="suffix + first")
add("multi", "bytes=" + ",".join(f"{i}-{i}" for i in range(0, 40, 2)), note="20 small ranges")
# E. syntax and whitespace
add("syntax", "Bytes=0-9", note="unit case"); add("syntax", "BYTES=0-9", note="unit upper")
add("syntax", "items=0-9", note="unknown unit"); add("syntax", "bytes 0-9", note="no equals")
add("syntax", "bytes = 0-9", note="space around ="); add("syntax", "bytes= 0-9", note="space after =")
add("syntax", "bytes=0 - 9", note="space inside spec"); add("syntax", "bytes=0-9, 20-29", note="OWS after comma")
add("syntax", "bytes=0-9 ,20-29", note="OWS before comma"); add("syntax", "bytes=0-9,,20-29", note="empty list element")
add("syntax", "bytes=0-9,", note="trailing comma"); add("syntax", "bytes=,0-9", note="leading comma")
# F. numerals
add("numeral", "bytes=+0-9", note="plus sign"); add("numeral", "bytes=0x0-0x9", note="hex prefix")
add("numeral", "bytes=00-09", note="leading zeros"); add("numeral", "bytes=1_0-19", note="underscore digit separator")
add("numeral", "bytes=0-99999999999999999999", note="last-pos > 2^64"); add("numeral", "bytes=99999999999999999999-", note="first-pos > 2^64")
add("numeral", "bytes=-99999999999999999999", note="suffix > 2^64"); add("numeral", "bytes=0.0-9", note="decimal point")
add("numeral", "bytes=1e1-19", note="exponent")
# G. empty representation
add("empty", "bytes=0-0", size=0); add("empty", "bytes=0-", size=0); add("empty", "bytes=-1", size=0); add("empty", "bytes=-0", size=0)
json.dump(C, open(os.path.join(HERE, "cases.json"), "w"), indent=1)
os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
open(os.path.join(HERE, "data", "r100.txt"), "wb").write(("0123456789" * 10).encode())
open(os.path.join(HERE, "data", "r0.txt"), "wb").write(b"")
for f in ("r100.txt", "r0.txt"): os.utime(os.path.join(HERE, "data", f), (1700000000, 1700000000))
print(len(C), "cases")
