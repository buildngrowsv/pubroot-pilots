#!/usr/bin/env python3
"""Turns realworld/strings.json into rw_cases.json (one case per distinct license string, with package counts)."""
import json, collections
d = json.load(open("realworld/strings.json"))
c = collections.Counter([x["license_expression"] for x in d["pypi"] if x.get("license_expression")] +
                        [x["license"] for x in d["npm"] if isinstance(x.get("license"), str)])
rows = [dict(id=f"RW{i + 1:02d}", group="realworld", expr=s, expect="OPEN", probes=[], packages=n)
        for i, (s, n) in enumerate(sorted(c.items(), key=lambda x: (-x[1], x[0])))]
json.dump(rows, open("rw_cases.json", "w"), indent=1); print(len(rows), "distinct strings,", sum(c.values()), "packages")
