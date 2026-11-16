// node js/one.js <lib> <expr> <startISO> <n>  -> prints JSON {ok, times|err} for one library and one expression.
// cron-parser gets a fixed hashSeed (documented option) so that `H` fields are reproducible.
// If a library throws after returning at least one time, the times found so far are kept (same rule in every adapter).
const [lib, expr, start, nStr] = process.argv.slice(2); const n = +nStr;
const fmt = d => { const t = new Date(d); const s = t.getUTCSeconds(), ms = t.getUTCMilliseconds();
  return t.toISOString().slice(0, 16) + 'Z' + (s || ms ? `+${s}s` : ''); };
const run = {
  'cron-parser': () => { const { CronExpressionParser } = require('cron-parser');
    const it = CronExpressionParser.parse(expr, { currentDate: new Date(start), tz: 'UTC', hashSeed: 'pubroot' });
    const out = []; for (let i = 0; i < n; i++) { try { out.push(fmt(it.next().toDate())); } catch (e) { if (out.length) break; throw e; } } return out; },
  'croner': () => { const { Cron } = require('croner');
    return new Cron(expr, { timezone: 'UTC', paused: true }).nextRuns(n, new Date(start)).map(fmt); },
  'cron': () => { const { CronTime } = require('cron'); const { DateTime } = require('luxon');
    const ct = new CronTime(expr, 'UTC'); const out = []; let prev = DateTime.fromISO(start, { zone: 'UTC' });
    for (let i = 0; i < n; i++) { let t; try { t = ct.getNextDateFrom(prev, 'UTC'); } catch (e) { if (out.length) break; throw e; } out.push(fmt(t.toJSDate())); prev = t; } return out; },
}[lib];
try { process.stdout.write(JSON.stringify({ ok: true, times: run() })); }
catch (e) { process.stdout.write(JSON.stringify({ ok: false, err: (e && e.message ? e.message : String(e)).slice(0, 70) })); }
