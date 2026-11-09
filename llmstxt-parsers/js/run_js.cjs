const fs = require('fs');
const path = require('path');
const p25 = require('@25xcodes/llmstxt-parser');
const parseLlmsTxt = require('parse-llms-txt');
const dir = path.join(__dirname, '..', 'fixtures');
const out = { '25xcodes': {}, 'parse-llms-txt': {} };

function from25(parsed) {
  if (!parsed) return { ok:false };
  const sections = [];
  // possible shapes
  const raw = parsed.sections || [];
  if (Array.isArray(raw)) {
    for (const s of raw) {
      const links = (s.links || s.items || []).map(l => ({
        url: l.url || l.href || null,
        title: l.name || l.title || l.text || null,
        description: l.description || l.desc || l.notes || null,
      }));
      sections.push({ name: s.name || s.title || s.heading || null, links });
    }
  } else if (raw && typeof raw === 'object') {
    for (const [name, links] of Object.entries(raw)) {
      sections.push({ name, links: (links||[]).map(l => ({
        url: l.url || l.href || null,
        title: l.title || l.name || null,
        description: l.description || l.desc || l.notes || null,
      }))});
    }
  }
  return {
    ok: true,
    title: parsed.title || null,
    summary: parsed.summary || parsed.info || parsed.description || null,
    sections,
    optional: parsed.optional || null,
    raw_keys: Object.keys(parsed),
  };
}

function fromParse(parsed) {
  if (!parsed) return { ok:false };
  // discover shape dynamically
  const sections = [];
  if (Array.isArray(parsed.sections)) {
    for (const s of parsed.sections) {
      const linksSrc = s.files || s.links || s.items || s.entries || [];
      sections.push({
        name: s.name || s.title || s.heading || null,
        links: linksSrc.map(l => ({
          url: l.url || l.href || l.link || null,
          title: l.name || l.title || l.text || null,
          description: l.description || l.desc || l.notes || null,
        })),
      });
    }
  }
  // some parsers put links at top level lists
  if (!sections.length && Array.isArray(parsed.links)) {
    sections.push({ name: 'links', links: parsed.links.map(l => ({
      url: l.url || l.href || null, title: l.title || l.name || null, description: l.description || null
    }))});
  }
  return {
    ok: true,
    title: parsed.title || null,
    summary: parsed.summary || parsed.description || null,
    sections,
    raw_keys: Object.keys(parsed),
    raw: parsed,
  };
}

for (const fn of fs.readdirSync(dir).filter(f=>f.endsWith('.txt'))) {
  const text = fs.readFileSync(path.join(dir, fn), 'utf8');
  try { out['25xcodes'][fn] = from25(p25.parseLLMSTxt(text)); }
  catch (e) { out['25xcodes'][fn] = { ok:false, error:String(e) }; }
  try { out['parse-llms-txt'][fn] = fromParse(parseLlmsTxt.parseLlmsTxt(text)); }
  catch (e) { out['parse-llms-txt'][fn] = { ok:false, error:String(e) }; }
}
fs.writeFileSync(path.join(__dirname, '..', 'results', 'js.json'), JSON.stringify(out, null, 2));
console.log('js done');
