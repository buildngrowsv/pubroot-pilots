// @fastify/send (the engine behind @fastify/static) on a plain node:http server, 127.0.0.1:PORT
import http from 'node:http'; import path from 'node:path'; import { fileURLToPath } from 'node:url'; import { createRequire } from 'node:module'
const send = createRequire(import.meta.url)('@fastify/send')
const DATA = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'data')
http.createServer(async (req, res) => {
  const { statusCode, headers, stream } = await send(req, req.url, { root: DATA })
  res.writeHead(statusCode, headers); stream.pipe(res)
}).listen(Number(process.argv[2]), '127.0.0.1')
