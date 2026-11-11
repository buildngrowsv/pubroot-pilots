#!/usr/bin/env python3
"""Generate the fixed Accept-header case list (cases.json). accept=None means the header is absent."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
HJ = ["text/html", "application/json"]; JH = ["application/json", "text/html"]
FF = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
CHROME = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
C = []
def add(g, accept, offers, note=""):
    C.append({"id": f"A{len(C)+1:02d}", "group": g, "accept": accept, "offers": offers, "note": note})
# basic
add("basic", "application/json", HJ); add("basic", "text/html", HJ); add("basic", "*/*", HJ, "wildcard only")
add("basic", None, HJ, "header absent"); add("basic", "", HJ, "header present but empty")
# q ordering and ties
add("q", "text/html;q=0.5, application/json", HJ); add("q", "text/html;q=0.5, application/json;q=0.5", HJ, "tie, header lists html first")
add("q", "application/json;q=0.5, text/html;q=0.5", HJ, "tie, header lists json first"); add("q", "text/html, application/json", JH, "tie at q=1, server prefers json")
# q=0 refusals
add("q0", "text/html;q=0", HJ, "only listed type refused"); add("q0", "text/html;q=0, */*", HJ); add("q0", "*/*;q=0.1, text/html;q=0", HJ)
add("q0", "text/*;q=0, text/html", HJ, "specific beats wildcard refusal"); add("q0", "text/html;q=0, text/*", HJ, "specific refusal beats wildcard")
add("q0", "*/*;q=0", HJ, "refuse everything"); add("q0", "application/json;q=0.9, application/json;q=0", HJ, "same type accepted then refused")
add("q0", "text/markdown;q=0", ["text/markdown", "text/html"], "anything but markdown")
# qvalue syntax
add("qsyntax", "application/json;q=1.0, text/html;q=0.9", HJ); add("qsyntax", "application/json;q=1.000, text/html;q=0.9", HJ)
add("qsyntax", "application/json;q=1.0001, text/html;q=0.9", HJ, "4 decimals"); add("qsyntax", "application/json;q=1.5, text/html;q=0.9", HJ, "q > 1")
add("qsyntax", "application/json;q=-1, text/html;q=0.1", HJ, "negative q"); add("qsyntax", "application/json;q=abc, text/html;q=0.1", HJ, "non-numeric q")
add("qsyntax", "application/json;q=, text/html;q=0.1", HJ, "empty q"); add("qsyntax", "application/json;q=.5, text/html;q=0.4", HJ, "no leading zero")
add("qsyntax", "application/json;q=0.0001, text/html;q=0.00001", HJ, "sub-0.001 q values"); add("qsyntax", "application/json;q=0.001", HJ, "minimum positive q")
add("qsyntax", "application/json; q=0.5, text/html; q=0.4", HJ, "OWS before q"); add("qsyntax", "application/json;Q=0.1, text/html;q=0.2", HJ, "upper-case Q")
add("qsyntax", "application/json;q = 0.1, text/html;q=0.2", HJ, "spaces around ="); add("qsyntax", 'application/json;q="0.1", text/html;q=0.2', HJ, "quoted q")
add("qsyntax", "text/html;q=0.9, application/json;q=0.9;q=0.1", HJ, "duplicate q param"); add("qsyntax", "application/json;q=0.1, application/json;q=0.9, text/html;q=0.5", HJ, "type listed twice")
add("qsyntax", "application/json;q=1e-1, text/html;q=0.2", HJ, "exponent q"); add("qsyntax", "application/json;q=0x1, text/html;q=0.2", HJ, "hex q")
# wildcards and specificity
add("wild", "text/*, application/json;q=0.5", JH); add("wild", "*/*;q=0.5, application/json", HJ)
add("wild", "*", ["application/json"], "bare *"); add("wild", "*/json", HJ, "wildcard type with concrete subtype")
add("wild", "application/*+json", ["text/html", "application/vnd.api+json"], "structured-suffix wildcard")
add("wild", "TEXT/HTML", JH, "upper-case type"); add("wild", "text/html", ["application/json", "TEXT/HTML"], "upper-case offer")
# parameters
add("params", "text/html;level=1, text/html;q=0.5", ["text/html"], "offer has no level"); add("params", "text/html;level=1;q=0.5, text/html", ["text/html;level=1"], "offer with level")
add("params", "application/json;charset=utf-8", ["application/json"], "param in header only"); add("params", "application/json", ["application/json;charset=utf-8"], "param in offer only")
add("params", "application/vnd.api+json, application/json;q=0.9", ["application/json", "application/vnd.api+json"])
add("params", "text/plain;format=flowed;q=0.9, text/plain;q=0.5", ["text/plain;format=fixed", "text/plain;format=flowed"], "offer param values")
# malformed lists
add("malformed", "application/json, , text/html;q=0.5", HJ, "empty element"); add("malformed", "application/json,", HJ, "trailing comma")
add("malformed", ",application/json", HJ, "leading comma"); add("malformed", "application", JH, "no slash")
add("malformed", "application/json;", HJ, "trailing semicolon"); add("malformed", "application/json;;q=0.5, text/html;q=0.9", HJ, "empty parameter")
add("malformed", "application/json garbage, text/html;q=0.5", HJ, "junk after type"); add("malformed", "text/html;q=0.5 , application/json;q=0.4", HJ, "space before comma")
# real-world request headers (MDN default values; JDK 8 HttpURLConnection; axios defaults; curl/requests */*)
add("real", FF, JH, "Firefox 132+ / Safari default"); add("real", FF, ["application/json", "text/markdown"], "Firefox default, no html offered")
add("real", CHROME, JH, "Chrome 131+ default"); add("real", CHROME, ["application/json", "text/markdown"], "Chrome default, no html offered")
add("real", "text/html, application/xhtml+xml, image/jxr, */*", ["application/json", "text/html"], "Edge (legacy) default")
add("real", "text/html, application/xml;q=0.9, application/xhtml+xml, image/png, image/webp, image/jpeg, image/gif, image/x-xbitmap, */*;q=0.1", ["application/json", "application/xml"], "Opera default")
add("real", "text/html, image/gif, image/jpeg, *; q=.2, */*; q=.2", ["application/json", "text/html"], "JDK 8 HttpURLConnection default")
add("real", "text/html, image/gif, image/jpeg, *; q=.2, */*; q=.2", ["application/json"], "JDK 8 default, json only")
add("real", "application/json, text/plain, */*", ["text/html", "application/json"], "axios default")
add("real", "*/*", ["text/markdown", "text/html"], "curl / python-requests default")
add("real", "text/markdown, text/html;q=0.9, */*;q=0.1", ["text/html", "text/markdown"], "markdown-preferring agent")
add("real", "image/avif,image/webp,image/apng,image/*,*/*;q=0.8", ["image/png", "image/webp"], "Chrome image default")
json.dump(C, open(os.path.join(HERE, "cases.json"), "w"), indent=1)
print(len(C), "cases")
