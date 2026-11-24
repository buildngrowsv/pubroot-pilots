// Split and quote runners for Node.js libraries. Usage: node js/run.mjs split|quote CASES.json > out.json
import fs from 'node:fs'
import { parse as sqParse, quote as sqQuote } from 'shell-quote'
import stringArgv from 'string-argv'
import { split as shlexSplit, quote as shlexQuote } from 'shlex'
import shellEscape from 'shell-escape'
const [mode, file] = process.argv.slice(2)
const cases = JSON.parse(fs.readFileSync(file, 'utf8'))
const wrap = (f) => (s) => { try { return { argv: f(s) } } catch (e) { return { error: String(e.message || e).slice(0, 120) } } }
// shell-quote returns strings plus objects for operators ({op}), globs ({op:'glob', pattern}) and comments ({comment}).
// We keep strings, render glob objects as their pattern, and record operators/comments as markers.
const sq = (s) => sqParse(s).map(t => typeof t === 'string' ? t : t.op === 'glob' ? t.pattern : t.comment !== undefined ? `<comment:${t.comment}>` : `<op:${t.op}>`)
const SPLIT = {
  'shell-quote': wrap(s => sq(s)),
  'string-argv': wrap(s => stringArgv(s)),
  'shlex (npm)': wrap(s => shlexSplit(s)),
}
const QUOTE = {
  'shell-quote': wrap(s => sqQuote([s])),
  'shell-escape': wrap(s => shellEscape([s])),
  'shlex (npm)': wrap(s => shlexQuote(s)),
}
const T = mode === 'split' ? SPLIT : QUOTE
const out = {}
for (const [name, f] of Object.entries(T)) { out[name] = {}; for (const c of cases) out[name][c.id] = f(c.s) }
process.stdout.write(JSON.stringify(out, null, 1) + '\n')
