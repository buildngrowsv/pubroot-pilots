#!/usr/bin/env python3
"""Writes cases.json (split cases) and quote_cases.json (strings for quote round trips).
Groups scored against POSIX sh (dash): B basic, S single quotes, D double quotes, E backslash escapes, Q mixed quoting,
U non-blank whitespace / Unicode, L practical command lines. Shell-only groups reported but not scored against libraries
built only to split words: C comments, O operators and newlines, X expansions."""
import json
NL = "\n"
C = [
 # B basic
 ("B01","a b c"),("B02","  a   b  "),("B03","a\tb"),("B04",""),("B05","   "),("B06","a"),
 # S single quotes
 ("S01","'a b'"),("S02","'a'b'c'"),("S03","''"),("S04","a''b"),("S05","'a\\b'"),("S06","'it'\\''s'"),("S07","'a\"b'"),("S08","'abc"),
 ("S09","x '' y"),
 # D double quotes
 ("D01",'"a b"'),("D02",'""'),("D03",'"a\\"b"'),("D04",'"a\\\\b"'),("D05",'"a\\b"'),("D06",'"a\\$b"'),("D07",'"a\\`b"'),
 ("D08",'"a\\nb"'),("D09","\"a'b\""),("D10",'"\\x"'),("D11",'"a\\'+NL+'b"'),("D12",'"abc'),("D13",'x "" y'),("D14",'"a'+NL+'b"'),
 # E escapes outside quotes
 ("E01","a\\ b"),("E02","\\a"),("E03","\\\\"),("E04","\\'"),("E05",'\\"'),("E06","a\\"),("E07","a\\"+NL+"b"),("E08","\\#a"),
 ("E09","a\\tb"),("E10","\\ "),("E11","a\\\\ b"),("E12","\\$x"),
 # Q mixed
 ("Q01",'a"b c"d'),("Q02","\"a\"'b'c"),("Q03",'--opt="x y"'),("Q04","-c 'echo \"hi\"'"),("Q05","\"'\"'\"'"),("Q06","\"\"''"),
 ("Q07","'a'\"b\"\\ c"),("Q08","--k='v w' --j=\"x\\\"y\""),
 # U whitespace other than space/tab, Unicode
 ("U01","h\u00e9llo w\u00f6rld"),("U02","a\u00a0b"),("U03","a\u3000b"),("U04","a\rb"),("U05","a\x0bb"),("U06","a\x0cb"),("U07","\u65e5\u672c '\u8a9e \u6587'"),
 # L practical command lines
 ("L01","git commit -m \"fix: it's done\""),("L02","python -c 'print(\"a b\")'"),("L03","curl -H \"Accept: */*\" https://example.com/a?b=c"),
 ("L04","ssh home 'ls -l '\"'\"'a b'\"'\"''"),("L05","docker run -e \"A=b c\" img"),("L06","grep -E '^(a|b)+$' file.txt"),
 ("L07","node -e \"console.log('x y')\""),("L08","find . -name '*.py' -print0"),
 # C comments (shell-only)
 ("C01","a #b"),("C02","a#b"),("C03","#a"),("C04","a \"#b\""),("C05","a '#'b"),
 # O operators and newlines (shell-only)
 ("O01","a;b"),("O02","a|b"),("O03","a&&b"),("O04","a >b"),("O05","a 2>&1"),("O06","(a)"),("O07","a"+NL+"b"),("O08","a & b"),
 # X expansions (shell-only; run with an empty environment)
 ("X01","$HOME"),("X02",'"$HOME"'),("X03","'$HOME'"),("X04","${X}y"),("X05","$(echo x)"),("X06","`echo x`"),("X07","~"),("X08","~/x"),
 ("X09","*.txt"),("X10","a=b c"),
]
GROUP = {"B":"basic","S":"single quotes","D":"double quotes","E":"backslash escapes","Q":"mixed quoting","U":"non-blank whitespace and Unicode",
         "L":"practical command lines","C":"comments (shell-only)","O":"operators and newlines (shell-only)","X":"expansions (shell-only)"}
OPEN = {"E06": "backslash as the last character of the input: POSIX gives it nothing to quote; dash and bash keep it"}
cases = [dict(id=i, s=s, group=GROUP[i[0]], scored=i[0] in "BSDEQUL" and i not in OPEN, open=OPEN.get(i)) for i, s in C]
assert len({c["id"] for c in cases}) == len(cases)
Q = ["", "a b", "it's", 'a"b', "$HOME", "`x`", "\\", "a\nb", "!", "*", "~", "-n", "h\u00e9llo", "\t", "'", '"', " lead", "#x", ";",
     "a\\'b", "$(x)", "{a,b}", "a\rb", "\u00a0", "=x", "[a]", "a*", "?", "é b"]
json.dump(cases, open("cases.json", "w"), indent=1, ensure_ascii=False)
json.dump([dict(id=f"R{k+1:02d}", s=s) for k, s in enumerate(Q)], open("quote_cases.json", "w"), indent=1, ensure_ascii=False)
print(len(cases), "split cases,", sum(c["scored"] for c in cases), "scored;", len(Q), "quote strings")
