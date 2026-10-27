// Repro copied from cloudflare/workers-sdk#12929 (public issue body).
import { Miniflare } from "miniflare";
const mf = new Miniflare({
  modules: true,
  script: `
    export default {
      async fetch() {
        using x = { value: "hello", [Symbol.dispose]() {} };
        return new Response(x.value);
      }
    };
  `,
});
try {
  const r = await mf.dispatchFetch("http://localhost");
  console.log("RESULT status", r.status, "body", await r.text());
} catch (e) { console.log("RESULT error", e.code || "", String(e.message).split("\n")[0]); }
await mf.dispose();
