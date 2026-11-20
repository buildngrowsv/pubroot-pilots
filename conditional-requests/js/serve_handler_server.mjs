// serve-handler (the engine of Vercel's `serve` CLI) on node:http, 127.0.0.1:PORT; etag enabled
import http from 'node:http'; import path from 'node:path'; import { fileURLToPath } from 'node:url'; import handler from 'serve-handler'
const DATA = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'data')
http.createServer((req, res) => handler(req, res, { public: DATA, etag: true })).listen(Number(process.argv[2]), '127.0.0.1')
