// Node subjects: parse-git-config 3.0.0 (parse.sync, which uses the ini package) and isomorphic-git 1.44.19
// (GitConfigManager.get from the exported "isomorphic-git/managers" subpath; entries read from the returned object's
// parsedConfig field). Usage: node run.mjs CASES.json  -> {lib: {id: {entries}|{error}}}
import fs from 'node:fs'; import os from 'node:os'; import path from 'node:path'
import { createRequire } from 'node:module'
import { GitConfigManager } from 'isomorphic-git/managers'
import { FileSystem } from 'isomorphic-git/models'
const require = createRequire(import.meta.url)
const pgc = require('parse-git-config')
const cases = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'))
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'gc-'))
const key = (sec, sub, name) => sec.toLowerCase() + (sub == null ? '' : '.' + sub) + '.' + name.toLowerCase()
const SUB = /^(\S+)\s+"(.*)"$/
const libs = {
  'parse-git-config': async (file) => {
    // ini turns "true"/"false" into booleans and splits dotted section names into nested objects; we turn booleans
    // back into strings and join nested objects with dots
    const o = pgc.sync({ path: file }); const out = []
    const str = x => (x === true ? 'true' : x === false ? 'false' : x)
    const walk = (prefix, body) => {
      for (const [k, v] of Object.entries(body)) {
        if (v !== null && typeof v === 'object' && !Array.isArray(v)) walk(prefix + k + '.', v)
        else for (const x of (Array.isArray(v) ? v : [v])) out.push([prefix + k, str(x)])
      }
    }
    for (const [sec, body] of Object.entries(o)) {
      const m = SUB.exec(sec); const [s, sub] = m ? [m[1], m[2]] : [sec, null]
      if (body === null || typeof body !== 'object') { out.push([sec, str(body)]); continue }
      const before = out.length; walk('', body)
      for (let i = before; i < out.length; i++) {
        const parts = out[i][0].split('.'); const name = parts.pop()
        const sec2 = [s, ...parts]; out[i][0] = key(sec2.shift(), sub != null ? sub : (sec2.length ? sec2.join('.') : null), name)
      }
    }
    return out
  },
  'isomorphic-git': async (file, dir) => {
    const cfg = await GitConfigManager.get({ fs: new FileSystem(fs), gitdir: dir })
    return cfg.parsedConfig.filter(e => e.name != null).map(e => [e.path, e.value])
  },
}
const res = {}
for (const [l, f] of Object.entries(libs)) {
  res[l] = {}
  for (const c of cases) {
    const dir = path.join(tmp, `${l.replace(/\W/g, '')}-${c.id}`); fs.mkdirSync(dir)
    const file = path.join(dir, 'config'); fs.writeFileSync(file, c.text)
    try { res[l][c.id] = { entries: await f(file, dir) } }
    catch (e) { res[l][c.id] = { error: String(e && e.message || e).split(tmp).join('<dir>').slice(0, 300) } }
  }
}
fs.rmSync(tmp, { recursive: true, force: true })
process.stdout.write(JSON.stringify(res, null, 1))
