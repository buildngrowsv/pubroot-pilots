import {Cite, plugins} from '@citation-js/core'
import '@citation-js/plugin-software-formats'; import '@citation-js/plugin-bibtex'; import '@citation-js/plugin-csl'
import fs from 'fs'
const [, , f, fmt] = process.argv
const c = await Cite.async(fs.readFileSync(f, 'utf8'))
console.log(fmt === 'apa' ? c.format('bibliography', {template: 'apa', format: 'text'}) : c.format('bibtex'))
