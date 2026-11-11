// Express 5 res.sendFile (send + range-parser) serving data/ on 127.0.0.1:PORT
import express from 'express'; import path from 'node:path'; import { fileURLToPath } from 'node:url'
const DATA = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'data')
const app = express()
app.get('/:f', (req, res) => res.sendFile(path.join(DATA, req.params.f)))
app.listen(Number(process.argv[2]), '127.0.0.1')
