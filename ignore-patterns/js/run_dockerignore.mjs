import fs from 'fs';
import path from 'path';
import dockerignore from '@balena/dockerignore';
const [,, ignoreFile, metaFile] = process.argv;
const patterns = fs.readFileSync(ignoreFile, 'utf8').split(/\r?\n/);
const ig = dockerignore().add(patterns);
const meta = JSON.parse(fs.readFileSync(metaFile, 'utf8'));
const out = {};
for (const [p, isDir] of meta.paths) {
  out[p] = ig.ignores(p); // balena API: ignores(path)
}
process.stdout.write(JSON.stringify(out));
