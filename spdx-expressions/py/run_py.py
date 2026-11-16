#!/usr/bin/env python3
"""Reads cases.json on stdin; writes {impl: {case: {ok, tree|canon|err}}} via each library's public API.
license-expression: get_spdx_licensing().parse(expr, validate=True, strict=True) -> boolean.py tree.
packaging: packaging.licenses.canonicalize_license_expression(expr) -> canonical string (no tree exposed)."""
import json, sys
from license_expression import get_spdx_licensing, LicenseWithExceptionSymbol, LicenseSymbol
from packaging.licenses import canonicalize_license_expression
cases = json.load(sys.stdin)
lic = get_spdx_licensing()
def leaf(sym):
    if isinstance(sym, LicenseWithExceptionSymbol):
        return f"{sym.license_symbol.key} WITH {sym.exception_symbol.key}"
    return sym.key
def tree(n):
    if isinstance(n, (LicenseSymbol, LicenseWithExceptionSymbol)): return leaf(n)
    op = type(n).__name__.upper()  # AND / OR classes of license_expression
    return [op] + [tree(a) for a in n.args]
out = {"license-expression": {}, "packaging": {}}
for c in cases:
    try:
        t = lic.parse(c["expr"], validate=True, strict=True)
        out["license-expression"][c["id"]] = {"ok": t is not None, "tree": tree(t) if t is not None else None} if t is not None else {"ok": False, "err": "parse returned None"}
    except Exception as e:
        out["license-expression"][c["id"]] = {"ok": False, "err": f"{type(e).__name__}: {str(e)[:70]}"}
    try:
        out["packaging"][c["id"]] = {"ok": True, "canon": canonicalize_license_expression(c["expr"])}
    except Exception as e:
        out["packaging"][c["id"]] = {"ok": False, "err": f"{type(e).__name__}: {str(e)[:70]}"}
print(json.dumps(out, indent=1, ensure_ascii=False))
