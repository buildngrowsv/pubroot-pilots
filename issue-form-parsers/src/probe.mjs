import { parseIssue } from "@github/issue-parser";
import zentered from "@zentered/issue-forms-body-parser";
import fs from "node:fs";
const tpl = fs.readFileSync(new URL("./template.yml", import.meta.url), "utf8");
const body = "### Title\n\nHello\n\n### Description\n\nSome text\n\n### Priority\n\nLow\n\n### Agreement\n\n- [X] I agree\n";
console.log(JSON.stringify(parseIssue(body), null, 1));
console.log(JSON.stringify(parseIssue(body, tpl), null, 1));
console.log(JSON.stringify(await zentered(body), null, 1));
