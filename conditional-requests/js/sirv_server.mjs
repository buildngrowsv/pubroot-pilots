// sirv (the static handler behind Vite's dev/preview servers and Polka) on node:http, 127.0.0.1:PORT; etag enabled
import http from 'node:http'; import path from 'node:path'; import { fileURLToPath } from 'node:url'; import sirv from 'sirv'
const DATA = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'data')
const h = sirv(DATA, { etag: true, dev: false })
http.createServer((req, res) => h(req, res, () => { res.statusCode = 404; res.end() })).listen(Number(process.argv[2]), '127.0.0.1')
