// Usage: node|bun run_node.mjs cases.json out.jsonl
import fs from "node:fs";
import { runAll } from "./subjects.mjs";
import * as bolt from "@slack/bolt";
const runtime = typeof Bun !== "undefined" ? `Bun ${Bun.version}` : `Node ${process.version}`;
const cases = JSON.parse(fs.readFileSync(process.argv[2], "utf8")).cases;
const rows = await runAll(cases, { runtime, slack: bolt.verifySlackRequest });
fs.writeFileSync(process.argv[3], rows.map((r) => JSON.stringify(r)).join("\n") + "\n");
console.log(runtime, rows.length, "rows");
