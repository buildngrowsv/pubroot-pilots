// Differential test of open-source GitHub issue-form body parsers. Local only, no network.
// Each case = a synthetic issue body in GitHub's issue-form rendering ("### <Label>\n\n<value>")
// for a 4-field form (Title, Description, Priority dropdown [Low|High|Critical], Agreement checkbox).
// Only the Description textarea value varies. Oracle: Title=Hello, Priority=Low, Agreement=[I agree],
// Description = the submitted text, no extra keys.
import fs from "node:fs";
import path from "node:path";
import { parseIssue } from "@github/issue-parser";
import zentered from "@zentered/issue-forms-body-parser";
import { unified } from "unified";
import remarkParse from "remark-parse";
import { run as sb325 } from "../vendor/stefanbuck/index.js";
import { run as sb324 } from "../vendor/stefanbuck-v3.2.4/index.js";

const here = path.dirname(new URL(import.meta.url).pathname);
const TPL_PATH = path.join(here, "template.yml");
const TPL = fs.readFileSync(TPL_PATH, "utf8");
const LABELS = ["Title", "Description", "Priority", "Agreement"];
const SPOOF = "Urgent-Override";
const F3 = "```", F4 = "````";

const CASES = [
  ["C00", "control: plain text", "Some text"],
  ["C01", "accidental: ### subsection with unknown label", "Intro\n\n### Steps\n\n1. run it"],
  ["C02", "accidental: ## and #### headings", "## Overview\n\ntext\n\n#### Detail\n\nmore"],
  ["C03", "injection: bare ### Priority line", `Intro\n\n### Priority\n\n${SPOOF}`],
  ["C04", "injection inside ``` fence", `${F3}\n### Priority\n\n${SPOOF}\n${F3}`],
  ["C05", "injection inside ~~~ fence", `~~~\n### Priority\n\n${SPOOF}\n~~~`],
  ["C06", "injection inside ```` fence that contains ``` lines", `${F4}\n${F3}\n### Priority\n\n${SPOOF}\n${F3}\n${F4}`],
  ["C07", "injection inside 4-space indented code", `Intro\n\n    ### Priority\n\n    ${SPOOF}`],
  ["C08", "injection as 2-space-indented ATX heading", `Intro\n\n  ### Priority\n\n${SPOOF}`],
  ["C09", "accidental: unterminated ``` fence", `see:\n${F3}\nunterminated`],
  ["C10", "injection inside HTML comment", `Intro\n\n<!--\n### Priority\n\n${SPOOF}\n-->`],
  ["C11", "injection of a new key", "Intro\n\n### is_admin\n\ntrue"],
  ["C12", "control: '###Priority' without space (not a heading)", `###Priority ${SPOOF}`],
  ["C13", "control: CRLF line endings", "Some text\r\nsecond line"],
  ["C14", "fence break-out from a render:-wrapped textarea", `${F3}\n\n### Priority\n\n${SPOOF}\n\n${F3}`, "wrap"],
  // Same injections, but the Description textarea is the LAST field (form order Title, Priority, Agreement,
  // Description), so the injected heading comes after the real one: tests first-wins vs last-wins.
  ["L03", "desc-last: bare ### Priority line", `Intro\n\n### Priority\n\n${SPOOF}`, "", "last"],
  ["L05", "desc-last: injection inside ~~~ fence", `~~~\n### Priority\n\n${SPOOF}\n~~~`, "", "last"],
  ["L10", "desc-last: injection inside HTML comment", `Intro\n\n<!--\n### Priority\n\n${SPOOF}\n-->`, "", "last"],
  ["L14", "desc-last: fence break-out from render:-wrapped textarea", `${F3}\n\n### Priority\n\n${SPOOF}\n\n${F3}`, "wrap", "last"],
];

let ORDER = LABELS;
function body(desc, wrap, order) {
  const d = wrap ? `${F3}text\n${desc}\n${F3}` : desc;
  const val = { Title: "Hello", Description: d, Priority: "Low", Agreement: "- [X] I agree" };
  return order.map((l) => `### ${l}\n\n${val[l]}`).join("\n\n") + "\n";
}
const norm = (s) => (s ?? "").toString().replace(/\r/g, "").replace(/\s+/g, " ").trim();

// ---- parser adapters: each returns {title, description, priority, agreement[], keys[]}
function sbAdapter(run, withTpl) {
  return async (b) => {
    let json = null;
    const core = { getInput: (n) => (n === "template-path" && withTpl ? TPL_PATH : ""), error: () => {},
      setOutput: (k, v) => { if (k === "jsonString") json = JSON.parse(v); } };
    const fakeFs = { readFileSync: fs.readFileSync, writeFileSync: () => {} };
    await run({ HOME: "/tmp" }, b, fakeFs, core);
    const r = json || {};
    return { raw: r, title: r.title, description: r.description, priority: r.priority,
      agreement: Array.isArray(r.agreement) ? r.agreement : r.agreement ? [r.agreement] : [], keys: Object.keys(r) };
  };
}
function ghAdapter(withTpl) {
  return async (b) => {
    const r = withTpl ? parseIssue(b, TPL) : parseIssue(b);
    const g = (k) => (withTpl ? r[k.toLowerCase()] : r[k]);
    let pr = g("Priority"); if (Array.isArray(pr)) pr = pr.join(",");
    let ag = g("Agreement");
    ag = ag && typeof ag === "object" && ag.selected ? ag.selected
       : typeof ag === "string" ? [...ag.matchAll(/^- \[[xX]\] (.*)$/gm)].map((m) => m[1].trim()) : [];
    return { raw: r, title: g("Title"), description: g("Description"), priority: pr, agreement: ag, keys: Object.keys(r) };
  };
}
async function zAdapter(b) {
  const r = await zentered(b);
  const t = (k) => (r[k] ? (r[k].content && r[k].content.length ? r[k].content.join("\n\n") : r[k].text) : undefined);
  const ag = r.agreement && r.agreement.list ? r.agreement.list.filter((x) => x.checked).map((x) => x.text) : [];
  return { raw: r, title: t("title"), description: t("description"), descriptionText: r.description && r.description.text,
    priority: t("priority"), agreement: ag, keys: Object.keys(r) };
}
async function naive(b) { // reference baseline: split on lines starting "### "
  const r = {};
  for (const sec of b.split(/^### /m).slice(1)) { const i = sec.indexOf("\n"); r[sec.slice(0, i).trim()] = sec.slice(i + 1).trim(); }
  return { raw: r, title: r.Title, description: r.Description, priority: r.Priority,
    agreement: [...(r.Agreement || "").matchAll(/^- \[[xX]\] (.*)$/gm)].map((m) => m[1].trim()), keys: Object.keys(r) };
}
// Hypothesis defense (reference, ours): CommonMark AST; accept only depth-3 headings whose text is a template
// label; REJECT the body if any label is missing, duplicated, or out of template order.
async function strictRef(b) {
  const tree = unified().use(remarkParse).parse(b);
  const heads = tree.children.filter((n) => n.type === "heading" && n.depth === 3)
    .map((n) => ({ text: n.children.map((c) => c.value ?? "").join("").trim(), start: n.position.start.offset, end: n.position.end.offset }))
    .filter((h) => LABELS.includes(h.text));
  const seq = heads.map((h) => h.text);
  if (seq.join("|") !== ORDER.join("|")) return { rejected: true, raw: { seq }, keys: [] };
  const r = {};
  heads.forEach((h, i) => { r[h.text] = b.slice(h.end, i + 1 < heads.length ? heads[i + 1].start : b.length).trim(); });
  return { raw: r, title: r.Title, description: r.Description, priority: r.Priority,
    agreement: [...(r.Agreement || "").matchAll(/^- \[[xX]\] (.*)$/gm)].map((m) => m[1].trim()), keys: Object.keys(r) };
}

const PARSERS = [
  ["stefanbuck/github-issue-parser v3.2.4", sbAdapter(sb324, false)],
  ["stefanbuck/github-issue-parser v3.2.5", sbAdapter(sb325, false)],
  ["stefanbuck/github-issue-parser v3.2.5 +template", sbAdapter(sb325, true)],
  ["@github/issue-parser 2.0.0", ghAdapter(false)],
  ["@github/issue-parser 2.0.0 +template", ghAdapter(true)],
  ["@zentered/issue-forms-body-parser 3.0.0", zAdapter],
  ["baseline: naive split /^### /m (reference)", naive],
  ["strict-AST reference (hypothesis defense, ours)", strictRef],
];

const rows = [];
for (const [cid, desc, value, wrap, pos] of CASES) {
  ORDER = pos === "last" ? ["Title", "Priority", "Agreement", "Description"] : LABELS;
  const b = body(value, wrap, ORDER);
  const expectedDesc = wrap ? `${F3}text\n${value}\n${F3}` : value;
  for (const [pname, fn] of PARSERS) {
    let out, err = null;
    try { out = await fn(b); } catch (e) { err = String(e).slice(0, 200); }
    const row = { case: cid, case_desc: desc, parser: pname };
    if (err) Object.assign(row, { outcome: "ERROR", error: err });
    else if (out.rejected) Object.assign(row, { outcome: "REJECT", raw: out.raw });
    else {
      const spoofed = norm(out.priority) !== "Low" || norm(out.title) !== "Hello" || JSON.stringify(out.agreement) !== '["I agree"]';
      const extra = out.keys.filter((k) => !LABELS.map((l) => l.toLowerCase()).includes(k.toLowerCase()));
      const descOk = norm(out.description) === norm(expectedDesc) || (out.descriptionText !== undefined && norm(out.descriptionText) === norm(expectedDesc));
      const escOnly = !descOk && out.description != null && norm(String(out.description).replace(/\\/g, "")) === norm(expectedDesc);
      const unfence = (x) => norm(String(x).replace(/\\/g, "").replace(/^(```|~~~)\w*$/gm, ""));
      const reser = !descOk && !escOnly && out.description != null && unfence(out.description) === unfence(expectedDesc);
      const flags = [spoofed && "FIELD_CHANGED", !descOk && (escOnly ? "DESC_ESCAPED" : reser ? "DESC_RESERIALIZED" : "DESC_ALTERED"), extra.length && "EXTRA_KEYS"].filter(Boolean);
      Object.assign(row, { body: b, outcome: flags.length ? flags.join("+") : "OK", priority: out.priority ?? null, title: out.title ?? null,
        agreement: out.agreement, extra_keys: extra, description: out.description ?? null, raw: out.raw });
    }
    rows.push(row);
  }
}
fs.mkdirSync(path.join(here, "../results"), { recursive: true });
fs.writeFileSync(path.join(here, "../results/differential.jsonl"), rows.map((r) => JSON.stringify(r)).join("\n") + "\n");
// summary table
const pnames = PARSERS.map((p) => p[0]);
let md = `| case | ${pnames.map((_, i) => "P" + (i + 1)).join(" | ")} |\n|---|${pnames.map(() => "---").join("|")}|\n`;
for (const [cid, desc] of CASES) md += `| ${cid} ${desc} | ${pnames.map((p) => rows.find((r) => r.case === cid && r.parser === p).outcome).join(" | ")} |\n`;
md += "\nCounts over the 16 non-control cases (C00, C12, C13 are controls):\n\n| parser | FIELD_CHANGED | DESC_ALTERED (content lost/added) | EXTRA_KEYS | REJECT | fully OK |\n|---|---|---|---|---|---|\n";
const CONTROLS = ["C00", "C12", "C13"];
pnames.forEach((p, i) => { const rs = rows.filter((r) => r.parser === p && !CONTROLS.includes(r.case));
  const c = (f) => rs.filter((r) => r.outcome.includes(f)).length;
  md += `| P${i + 1} | ${c("FIELD_CHANGED")} | ${c("DESC_ALTERED")} | ${c("EXTRA_KEYS")} | ${c("REJECT")} | ${rs.filter((r) => r.outcome === "OK").length} |\n`; });
md += "\n" + pnames.map((p, i) => `P${i + 1} = ${p}`).join("\n") + "\n";
fs.writeFileSync(path.join(here, "../results/summary.md"), md);
console.log(md);
