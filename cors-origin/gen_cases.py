#!/usr/bin/env python3
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
CASES = []
def add(id, req_origin, **options):
    CASES.append({"id": id, "origin": req_origin, "options": options})

add("exact_allow", "https://app.example.com", origin=["https://app.example.com", "https://other.example.com"])
add("exact_deny", "https://evil.example.com", origin=["https://app.example.com"])
add("exact_allow_other", "https://other.example.com", origin=["https://app.example.com", "https://other.example.com"])
add("star_allow", "https://app.example.com", origin="*")
add("star_null", None, origin="*")
add("trail_slash_req", "https://app.example.com/", origin=["https://app.example.com"])
add("trail_slash_cfg", "https://app.example.com", origin=["https://app.example.com/"])
add("port_mismatch", "https://app.example.com:443", origin=["https://app.example.com"])
add("http_vs_https", "http://app.example.com", origin=["https://app.example.com"])
add("subdomain", "https://api.app.example.com", origin=["https://app.example.com"])
add("null_in_list", "null", origin=["null", "https://app.example.com"])
add("null_not_in_list", "null", origin=["https://app.example.com"])
add("regex_subdomain_allow", "https://foo.app.example.com", origin="__REGEX__", origin_regex=r"https://.*\.app\.example\.com")
add("regex_subdomain_deny", "https://evil.example.com", origin="__REGEX__", origin_regex=r"https://.*\.app\.example\.com")
add("regex_partial_vs_full", "https://app.example.com.evil.com", origin="__REGEX__", origin_regex=r"https://app\.example\.com")
add("regex_unanchored", "https://app.example.com.evil.com", origin="__REGEX__", origin_regex=r"app\.example\.com")
add("cred_exact", "https://app.example.com", origin=["https://app.example.com"], credentials=True)
add("cred_star", "https://app.example.com", origin="*", credentials=True)
add("missing_origin", None, origin=["https://app.example.com"])
add("case_scheme", "HTTPS://app.example.com", origin=["https://app.example.com"])
add("case_host", "https://APP.example.com", origin=["https://app.example.com"])

json.dump(CASES, open(os.path.join(HERE, "cases.json"), "w"), indent=2)
print(len(CASES), "cases")
