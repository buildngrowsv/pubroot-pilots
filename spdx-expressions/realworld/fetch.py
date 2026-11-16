#!/usr/bin/env python3
"""Snapshot of real license strings (public, unauthenticated GETs; run once, output committed as strings.json).
PyPI: info.license_expression (PEP 639) of the top 300 projects in hugovk's top-pypi-packages 30-day list.
npm: `license` of the latest version of the top 300 packages by downloads in npm-high-impact@1.13.0 (lib/top-download.js)."""
import json, re, sys, time, urllib.request, tarfile, io
UA = {"User-Agent": "pubroot-research-pilot (no-contact; read-only)"}
def get(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30) as r: return r.read()
top = json.loads(get("https://hugovk.dev/top-pypi-packages/top-pypi-packages-30-days.min.json"))
py = []
for row in top["rows"][:300]:
    try: info = json.loads(get(f"https://pypi.org/pypi/{row['project']}/json"))["info"]
    except Exception as e: py.append(dict(name=row["project"], err=str(e)[:60])); continue
    py.append(dict(name=row["project"], version=info.get("version"), license_expression=info.get("license_expression")))
    time.sleep(0.2)
tgz = tarfile.open(fileobj=io.BytesIO(get("https://registry.npmjs.org/npm-high-impact/-/npm-high-impact-1.13.0.tgz")))
src = tgz.extractfile("package/lib/top-download.js").read().decode()
names = re.findall(r"'([^']+)'", src)[:300]
npm = []
for n in names:
    try: m = json.loads(get(f"https://registry.npmjs.org/{n.replace('/', '%2F')}/latest"))
    except Exception as e: npm.append(dict(name=n, err=str(e)[:60])); continue
    lic = m.get("license")
    if isinstance(lic, dict): lic = {"_object": lic.get("type")}
    npm.append(dict(name=n, version=m.get("version"), license=lic)); time.sleep(0.1)
json.dump(dict(fetched=time.strftime("%Y-%m-%dT%H:%M:%S%z"), pypi_list_update=top["last_update"],
               npm_list="npm-high-impact@1.13.0 lib/top-download.js", pypi=py, npm=npm),
          open("realworld/strings.json", "w"), indent=1)
print(len(py), len(npm))
