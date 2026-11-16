// Reads cases.json on stdin; runs every (library, case) in a child process with a 10 s limit (TIMEOUT otherwise).
const fs = require('fs'); const { spawnSync } = require('child_process'); const path = require('path');
const D = JSON.parse(fs.readFileSync(0, 'utf8')); const out = {};
for (const lib of ['cron-parser', 'croner', 'cron']) {
  out[lib] = {};
  for (const c of D.cases) {
    const r = spawnSync(process.execPath, [path.join(__dirname, 'one.js'), lib, c.expr, D.start, String(D.n)], { timeout: 10000, encoding: 'utf8', cwd: __dirname });
    out[lib][c.id] = r.error || r.signal ? { ok: false, err: 'TIMEOUT' } : JSON.parse(r.stdout);
  }
}
process.stdout.write(JSON.stringify(out, null, 1) + '\n');
