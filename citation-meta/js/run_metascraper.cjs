const fs = require('fs');
const path = require('path');
const metascraper = require('metascraper');
const title = require('metascraper-title');
const author = require('metascraper-author');
const url = require('metascraper-url');
const description = require('metascraper-description');
const publisher = require('metascraper-publisher');
let citation = null;
try { citation = require('metascraper-citation'); } catch {}
const pagesDir = path.join(__dirname, '..', 'pages');
const rules = [title(), author(), url(), description(), publisher()];
if (citation) rules.unshift(citation());
const scrape = metascraper(rules);
(async () => {
  const out = {};
  for (const fn of fs.readdirSync(pagesDir).filter(f=>f.endsWith('.html'))) {
    const html = fs.readFileSync(path.join(pagesDir, fn), 'utf8');
    out[fn] = await scrape({ html, url: 'https://example.com/landing/' + fn });
  }
  fs.writeFileSync(path.join(__dirname, '..', 'results', 'metascraper.json'), JSON.stringify(out, null, 2));
  console.log('metascraper', Object.keys(out).length, 'citationPlugin', !!citation);
})();
