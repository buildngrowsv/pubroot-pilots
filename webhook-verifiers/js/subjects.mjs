// Shared JS subjects: each returns {verdict, detail}. verdict: accept | reject (typed verification failure or false) | crash (other exception).
import Stripe from "stripe";
import { Webhook as SWWebhook } from "standardwebhooks";
import { Webhook as SvixWebhook } from "svix";
import { verify as ghVerify } from "@octokit/webhooks-methods";
const stripe = new Stripe("sk_test_synthetic_not_a_key");
const VERIF = /SignatureVerification|WebhookVerification|Webhook.*Error|signature mismatch|Failed to verify|request is stale|unknown signature version|tolerance/i;
const classify = (e) => (VERIF.test((e && (e.name + " " + e.type + " " + e.message)) || "") ? "reject" : "crash");
async function run(fn) {
  try { const r = await fn(); return r === false ? { verdict: "reject", detail: "returned false" } : { verdict: "accept", detail: "ok" }; }
  catch (e) { return { verdict: classify(e), detail: `${e && e.name}: ${String(e && e.message).slice(0, 120)}` }; }
}
export function subjects(env) {
  const S = [
    ["js-stripe constructEvent", (c) => stripe.webhooks.constructEvent(c.body, c.headers["stripe-signature"], c.secret, c.tolerance)],
    ["js-stripe constructEventAsync", (c) => stripe.webhooks.constructEventAsync(c.body, c.headers["stripe-signature"], c.secret, c.tolerance)],
  ];
  const W = [
    ["js-standardwebhooks", (c) => new SWWebhook(c.secret).verify(c.body, { ...c.headers })],
    ["js-svix", (c) => new SvixWebhook(c.secret).verify(c.body, { ...c.headers })],
  ];
  const G = [["js-@octokit/webhooks-methods", (c) => ghVerify(c.secret, c.body, c.headers["x-hub-signature-256"])]];
  const K = env.slack ? [["js-@slack/bolt verifySlackRequest", (c) => env.slack({ signingSecret: c.secret, body: c.body, headers: { ...c.headers } })]] : [];
  return { S, W, G, K };
}
export async function runAll(cases, env) {
  const subj = subjects(env); const rows = [];
  for (const c of cases) for (const [name, fn] of subj[c.scheme]) {
    const r = await run(() => fn(c));
    rows.push({ runtime: env.runtime, subject: name, case: c.id, scheme: c.scheme, cls: c.cls, ref: c.ref, ...r });
  }
  return rows;
}
