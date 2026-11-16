#!/usr/bin/env python3
"""Writes cases.json: SPDX license-expression cases with the reading from SPDX spec 3.0.1 Annex B.
expect: "INVALID", "OPEN" (spec silent, or a document-field sentinel such as NONE/NOASSERTION outside the expression grammar), or a canonical tree: leaves `ID`, `ID+`, `ID WITH EXC`;
inner nodes `(AND a b ...)` / `(OR a b ...)`, same-operator chains flattened, ids compared case-insensitively.
probes: [allow-list, expected satisfied?] for the allow-list check (precedence group only)."""
import json
V = "INVALID"; O = "OPEN"
C = [
 # S: single terms and basic forms
 ("S01", "basic", "MIT", "MIT"),
 ("S02", "basic", "Apache-2.0", "Apache-2.0"),
 ("S03", "basic", "MIT OR Apache-2.0", "(OR MIT Apache-2.0)"),
 ("S04", "basic", "MIT AND Apache-2.0", "(AND MIT Apache-2.0)"),
 ("S05", "basic", "GPL-2.0-or-later WITH Classpath-exception-2.0", "GPL-2.0-or-later WITH Classpath-exception-2.0"),
 ("S06", "basic", "LicenseRef-Proprietary", "LicenseRef-Proprietary"),
 ("S07", "basic", "DocumentRef-spdx-tool-1.2:LicenseRef-MIT-Style-2", "DocumentRef-spdx-tool-1.2:LicenseRef-MIT-Style-2"),
 ("S08", "basic", "CDDL-1.0+", "CDDL-1.0+"),
 ("S09", "basic", "(MIT OR Apache-2.0) AND BSD-3-Clause", "(AND (OR MIT Apache-2.0) BSD-3-Clause)"),
 ("S10", "basic", "Apache-2.0 WITH LLVM-exception", "Apache-2.0 WITH LLVM-exception"),
 # P: precedence and parentheses
 ("P01", "precedence", "LGPL-2.1-only OR BSD-3-Clause AND MIT", "(OR LGPL-2.1-only (AND BSD-3-Clause MIT))"),
 ("P02", "precedence", "MIT AND BSD-3-Clause OR Apache-2.0", "(OR (AND MIT BSD-3-Clause) Apache-2.0)"),
 ("P03", "precedence", "MIT OR Apache-2.0 AND BSD-2-Clause OR ISC", "(OR MIT (AND Apache-2.0 BSD-2-Clause) ISC)"),
 ("P04", "precedence", "GPL-2.0-only WITH Classpath-exception-2.0 OR MIT", "(OR GPL-2.0-only WITH Classpath-exception-2.0 MIT)"),
 ("P05", "precedence", "MIT AND GPL-2.0-only WITH Classpath-exception-2.0", "(AND MIT GPL-2.0-only WITH Classpath-exception-2.0)"),
 ("P06", "precedence", "(MIT)", "MIT"),
 ("P07", "precedence", "((MIT))", "MIT"),
 ("P08", "precedence", "MIT AND (Apache-2.0 OR BSD-3-Clause)", "(AND MIT (OR Apache-2.0 BSD-3-Clause))"),
 ("P09", "precedence", "(MIT OR Apache-2.0) AND (BSD-2-Clause OR ISC)", "(AND (OR MIT Apache-2.0) (OR BSD-2-Clause ISC))"),
 ("P10", "precedence", "MIT AND Apache-2.0 AND BSD-3-Clause OR ISC", "(OR (AND MIT Apache-2.0 BSD-3-Clause) ISC)"),
 # K: operator keyword case (Annex B: all upper or all lower)
 ("K01", "op-case", "MIT or Apache-2.0", "(OR MIT Apache-2.0)"),
 ("K02", "op-case", "MIT and Apache-2.0", "(AND MIT Apache-2.0)"),
 ("K03", "op-case", "GPL-2.0-or-later with Classpath-exception-2.0", "GPL-2.0-or-later WITH Classpath-exception-2.0"),
 ("K04", "op-case", "MIT Or Apache-2.0", V),
 ("K05", "op-case", "MIT aNd Apache-2.0", V),
 ("K06", "op-case", "GPL-2.0-or-later With Classpath-exception-2.0", V),
 ("K07", "op-case", "MIT OR Apache-2.0 and BSD-3-Clause", "(OR MIT (AND Apache-2.0 BSD-3-Clause))"),
 # I: identifier case (Annex B: case-insensitive; LicenseRef- prefix case-sensitive)
 ("I01", "id-case", "mit", "MIT"),
 ("I02", "id-case", "apache-2.0 OR mit", "(OR Apache-2.0 MIT)"),
 ("I03", "id-case", "Gpl-2.0-Or-Later WITH classpath-exception-2.0", "GPL-2.0-or-later WITH Classpath-exception-2.0"),
 ("I04", "id-case", "BSD-3-CLAUSE", "BSD-3-Clause"),
 ("I05", "id-case", "licenseref-foo", V),
 ("I06", "id-case", "LICENSEREF-foo", V),
 ("I07", "id-case", "LicenseRef-FOO", "LicenseRef-FOO"),
 ("I08", "id-case", "documentref-a:LicenseRef-b", V),
 # D: deprecated and list membership
 ("D01", "list", "GPL-2.0", "GPL-2.0"),
 ("D02", "list", "GPL-2.0+", "GPL-2.0+"),
 ("D03", "list", "LGPL-2.1+", "LGPL-2.1+"),
 ("D04", "list", "GPL-2.0-with-classpath-exception", "GPL-2.0-with-classpath-exception"),
 ("D05", "list", "wxWindows", "wxWindows"),
 ("D06", "list", "Nokia-Qt-exception-1.1", V),
 ("D07", "list", "GPL-2.0-only WITH Nokia-Qt-exception-1.1", "GPL-2.0-only WITH Nokia-Qt-exception-1.1"),
 ("D08", "list", "Foo-License-1.0", V),
 ("D09", "list", "MIT OR Foo-License-1.0", V),
 # U: the + operator
 ("U01", "plus", "MIT+", "MIT+"),
 ("U02", "plus", "GPL-2.0-or-later+", "GPL-2.0-or-later+"),
 ("U03", "plus", "MIT +", V),
 ("U04", "plus", "LicenseRef-foo+", V),
 ("U05", "plus", "Apache-1.1+ WITH LLVM-exception", "Apache-1.1+ WITH LLVM-exception"),
 # W: WITH operand rules
 ("W01", "with", "MIT WITH Apache-2.0", V),
 ("W02", "with", "Classpath-exception-2.0", V),
 ("W03", "with", "GPL-2.0-only WITH LicenseRef-x", V),
 ("W04", "with", "GPL-2.0-only WITH AdditionRef-x", "GPL-2.0-only WITH AdditionRef-x"),
 ("W05", "with", "LicenseRef-x WITH Classpath-exception-2.0", "LicenseRef-x WITH Classpath-exception-2.0"),
 ("W06", "with", "GPL-2.0-only WITH Classpath-exception-2.0 WITH LLVM-exception", V),
 ("W07", "with", "(MIT OR Apache-2.0) WITH LLVM-exception", V),
 ("W08", "with", "GPL-2.0-only WITH", V),
 ("W09", "with", "WITH Classpath-exception-2.0", V),
 # X: syntax and whitespace
 ("X01", "syntax", "", V),
 ("X02", "syntax", "MIT OR", V),
 ("X03", "syntax", "OR MIT", V),
 ("X04", "syntax", "MIT AND AND Apache-2.0", V),
 ("X05", "syntax", "(MIT OR Apache-2.0", V),
 ("X06", "syntax", "MIT OR Apache-2.0)", V),
 ("X07", "syntax", "()", V),
 ("X08", "syntax", "MIT/Apache-2.0", V),
 ("X09", "syntax", "MIT, Apache-2.0", V),
 ("X10", "syntax", "MIT Apache-2.0", V),
 ("X11", "syntax", "MIT OR(Apache-2.0)", "(OR MIT Apache-2.0)"),
 ("X12", "syntax", "(MIT)OR(Apache-2.0)", "(OR MIT Apache-2.0)"),
 ("X13", "syntax", "MIT  OR  Apache-2.0", "(OR MIT Apache-2.0)"),
 ("X14", "syntax", " MIT ", O),
 ("X15", "syntax", "MIT\tOR Apache-2.0", O),
 ("X16", "syntax", "MIT ORApache-2.0", V),
 # R: LicenseRef idstring
 ("R01", "ref", "LicenseRef-my_license", V),
 ("R02", "ref", "LicenseRef-", V),
 ("R03", "ref", "LicenseRef-a.b-c", "LicenseRef-a.b-c"),
 ("R04", "ref", "LicenseRef-scancode-unknown-license-reference", "LicenseRef-scancode-unknown-license-reference"),
 ("R05", "ref", "MIT AND LicenseRef-Commercial", "(AND MIT LicenseRef-Commercial)"),
 # M: strings seen in package metadata
 ("M01", "metadata", "Apache 2.0", V),
 ("M02", "metadata", "MIT License", V),
 ("M03", "metadata", "BSD", V),
 ("M04", "metadata", "UNLICENSED", V),
 ("M05", "metadata", "SEE LICENSE IN LICENSE", V),
 ("M06", "metadata", "NONE", O),
 ("M07", "metadata", "NOASSERTION", O),
 ("M08", "metadata", "MIT OR Apache-2.0", "(OR MIT Apache-2.0)"),
 ("M09", "metadata", "Apache-2.0 WITH LLVM-exception OR MIT", "(OR Apache-2.0 WITH LLVM-exception MIT)"),
 ("M10", "metadata", "(MIT OR Apache-2.0) AND Unicode-3.0", "(AND (OR MIT Apache-2.0) Unicode-3.0)"),
 ("M11", "metadata", "GPL-3.0", "GPL-3.0"),
 ("M12", "metadata", "Python-2.0", "Python-2.0"),
]
PROBES = {  # allow-list, satisfied under the spec's precedence
 "P01": [(["LGPL-2.1-only"], True), (["BSD-3-Clause"], False), (["BSD-3-Clause", "MIT"], True)],
 "P02": [(["Apache-2.0"], True), (["MIT"], False), (["MIT", "BSD-3-Clause"], True)],
 "P03": [(["ISC"], True), (["Apache-2.0"], False), (["Apache-2.0", "BSD-2-Clause"], True)],
 "P08": [(["MIT"], False), (["MIT", "BSD-3-Clause"], True), (["Apache-2.0"], False)],
 "P10": [(["ISC"], True), (["MIT", "Apache-2.0"], False), (["MIT", "Apache-2.0", "BSD-3-Clause"], True)],
 "K07": [(["MIT"], True), (["Apache-2.0"], False)],
 "M09": [(["MIT"], True), (["Apache-2.0"], False)],
}
out = [dict(id=i, group=g, expr=e, expect=x, probes=[dict(allow=a, sat=s) for a, s in PROBES.get(i, [])]) for i, g, e, x in C]
assert len({c["id"] for c in out}) == len(out)
json.dump(out, open("cases.json", "w"), indent=1); print(len(out), "cases")
