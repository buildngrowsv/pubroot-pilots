// accepts@2 (Express 5, negotiator 1.x) and accepts@1.3.8 (Express 4, negotiator 0.6.3): req.accepts(offers) semantics
const accepts2 = require('accepts'), accepts1 = require('accepts1')
const cases = JSON.parse(require('fs').readFileSync(0, 'utf8'))
const run = (f) => cases.map(c => {
  const headers = c.accept === null ? {} : { accept: c.accept }
  let r; try { r = f({ headers }).type(c.offers) } catch (e) { r = 'ERR ' + e.name }
  return { id: c.id, choice: r === false ? null : r }
})
process.stdout.write(JSON.stringify({ accepts2: run(accepts2), accepts1: run(accepts1) }, null, 1) + '\n')
