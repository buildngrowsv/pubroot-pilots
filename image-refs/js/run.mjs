// Node subjects. Usage: node run.mjs CASES.json -> {lib: {id: {"ref": [registry, repository, tag, digest]} | {"error"}}}
// - @swimlane/docker-reference 2.0.1: parseFamiliarName(s) (the parser its README gives for familiar names)
// - docker-parse-image 3.0.1: default export; {registry, namespace, repository, tag}; null means no match.
//   It has one field for tag and digest ("tag" holds whatever follows the first ':' or '@'); we treat it as a
//   digest when the input has '@' there.
// - parse-docker-image-name 3.0.0: default export (a GopherJS build of docker/distribution's reference.Parse);
//   {domain, path, tag, digest}; an empty object means an error.
import fs from 'node:fs'
import { createRequire } from 'node:module'
const require = createRequire(import.meta.url)
const { parseFamiliarName } = require('@swimlane/docker-reference')
const dpi = require('docker-parse-image')
const pdin = require('parse-docker-image-name')
const cases = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'))
const n = x => (x === undefined || x === null ? null : x)
const libs = {
  '@swimlane/docker-reference': s => { const r = parseFamiliarName(s); return [n(r.domain), n(r.repository), n(r.tag), n(r.digest)] },
  'docker-parse-image': s => {
    const r = dpi(s); if (!r) throw new Error('no match')
    const repo = (r.namespace ? r.namespace + '/' : '') + r.repository
    const m = /^(?:[^@:]*?)([@:])/.exec(s.slice(s.lastIndexOf('/') + 1))
    const isDigest = r.tag != null && m && m[1] === '@'
    return [n(r.registry), repo, isDigest ? null : n(r.tag), isDigest ? r.tag : null]
  },
  'parse-docker-image-name': s => { const r = pdin(s); if (!r || Object.keys(r).length === 0) throw new Error('empty result'); return [n(r.domain), n(r.path), n(r.tag), n(r.digest)] },
}
const out = {}
for (const [l, f] of Object.entries(libs)) {
  out[l] = {}
  for (const c of cases) {
    try { out[l][c.id] = { ref: f(c.s) } } catch (e) { out[l][c.id] = { error: String(e && e.message || e).slice(0, 200) } }
  }
}
process.stdout.write(JSON.stringify(out, null, 1))
