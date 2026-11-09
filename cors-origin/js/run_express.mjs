import cors from 'cors';

const cases = JSON.parse(await new Promise((res)=>{let d=''; process.stdin.on('data',c=>d+=c); process.stdin.on('end',()=>res(d));}));
const out = [];
for (const c of cases) {
  let options = { ...c.options };
  if (options.origin === '__REGEX__' && options.origin_regex) {
    options.origin = new RegExp(options.origin_regex);
    delete options.origin_regex;
  } else {
    delete options.origin_regex;
  }
  // map credentials key
  if (options.credentials) {
    options.credentials = true;
  }
  const middleware = cors(options);
  const headersIn = {};
  if (c.origin !== null && c.origin !== undefined) {
    headersIn.origin = c.origin;
  }
  const req = { method: 'GET', headers: headersIn };
  let headers = {};
  const resObj = {
    setHeader(k,v){ headers[String(k).toLowerCase()] = v; },
    getHeader(k){ return headers[String(k).toLowerCase()]; },
    end(){},
  };
  await new Promise((resolve) => middleware(req, resObj, resolve));
  out.push({ id: c.id, acao: headers['access-control-allow-origin'] ?? null, acac: headers['access-control-allow-credentials'] ?? null });
}
process.stdout.write(JSON.stringify(out));
