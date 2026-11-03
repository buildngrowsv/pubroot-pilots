// Cloudflare Worker wrapper: POST the case set, get JSONL rows back. Slack Bolt is a Node server framework and is not run here.
import { runAll } from "./subjects.mjs";
export default {
  async fetch(req) {
    const { cases } = await req.json();
    const rows = await runAll(cases, { runtime: "workerd (Miniflare " + (globalThis.MF_VERSION || "") + ")" });
    return new Response(rows.map((r) => JSON.stringify(r)).join("\n") + "\n");
  },
};
