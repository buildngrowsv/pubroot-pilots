import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import metascraper from 'metascraper';
import title from 'metascraper-title';
import author from 'metascraper-author';
import url from 'metascraper-url';
import description from 'metascraper-description';
import publisher from 'metascraper-publisher';
let citation;
try { citation = (await import('metascraper-citation')).default; } catch { citation = null; }

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const pagesDir = path.join(__dirname, '..', 'pages');
const rules = [title(), author(), url(), description(), publisher()];
if (citation) rules.unshift(citation());
const scrape = metascraper(rules);
const out = {};
for (const fn of fs.readdirSync(pagesDir).filter(f=>f.endsWith('.html'))) {
  const html = fs.readFileSync(path.join(pagesDir, fn), 'utf8');
  const meta = await scrape({ html, url: 'https://ex.test/landing/' + fn });
  out[fn] = meta;
}
fs.writeFileSync(path.join(__dirname, '..', 'results', 'metascraper.json'), JSON.stringify(out, null, 2));
console.log('metascraper', Object.keys(out).length, 'citationPlugin', !!citation);
