// Reads cases.json on stdin; writes {impl: {case: {ok, tree|err, probes}}}; tree = leaf string or [OP, child, ...] using each library's public API only.
const fs = require('fs');
const cases = JSON.parse(fs.readFileSync(0, 'utf8'));
const IMPLS = { 'spdx-expression-parse@5': require('spdx-expression-parse'), 'spdx-expression-parse@3': require('sep3') };
const satisfies = require('spdx-satisfies');
function leaf(n) { let s = n.license + (n.plus ? '+' : ''); if (n.exception) s += ' WITH ' + n.exception; return s; }
// Emit the library's tree as nested JSON; flattening and rendering happen once, in analyze.py, for every implementation.
function tree(n) { if (n.license) return leaf(n); return [n.conjunction.toUpperCase(), tree(n.left), tree(n.right)]; }
const out = {};
for (const [name, parse] of Object.entries(IMPLS)) {
  out[name] = {};
  for (const c of cases) {
    try { out[name][c.id] = { ok: true, tree: tree(parse(c.expr)) }; }
    catch (e) { out[name][c.id] = { ok: false, err: String(e.message).slice(0, 80) }; }
  }
}
out['spdx-satisfies@6'] = {};
for (const c of cases) {
  if (!c.probes.length) continue;
  out['spdx-satisfies@6'][c.id] = { probes: c.probes.map(p => { try { return satisfies(c.expr, p.allow); } catch (e) { return 'ERR'; } }) };
}
process.stdout.write(JSON.stringify(out, null, 1) + '\n');
