// Repro for langchain-ai/langgraphjs#2040 (cross-thread contamination, singleton graph + concurrent invoke).
// Deterministic: no LLM; a scripted "model" node emits a tool call. Run from a lgjs-<version> dir:
//   node ../repro/lgjs_2040.mjs
import { createRequire } from "node:module";
const require = createRequire(process.cwd() + "/");
const lg = await import(require.resolve("@langchain/langgraph"));
const { MemorySaver } = await import(require.resolve("@langchain/langgraph-checkpoint"));
const { tool } = await import(require.resolve("@langchain/core/tools"));
const { AIMessage, HumanMessage } = await import(require.resolve("@langchain/core/messages"));
const prebuilt = await import(require.resolve("@langchain/langgraph/prebuilt"));
const { Annotation, StateGraph, START, END, getCurrentTaskInput } = lg;
const { ToolNode } = prebuilt;
const version = require("@langchain/langgraph/package.json").version;
const delay = (ms) => new Promise((r) => setTimeout(r, ms));

const State = Annotation.Root({
  messages: Annotation({ reducer: (l, r) => l.concat(r), default: () => [] }),
  customer: Annotation({ reducer: (_, r) => r, default: () => "" }),
  seen_tenant: Annotation({ reducer: (_, r) => r, default: () => "" }),
});

function build(checkpointer, sharedBound, modelDelay) {
  const record = tool(async (input, config) => `recorded:${input.name}:thread=${config?.configurable?.thread_id}`, {
    name: "record_customer", description: "Record customer name.",
    schema: { type: "object", properties: { name: { type: "string" } }, required: ["name"] },
  });
  const callModel = async (state) => {
    await delay(modelDelay(state.customer));
    const who = getCurrentTaskInput().customer;
    return { messages: [new AIMessage({ content: "", tool_calls: [{ name: "record_customer", args: { name: who }, id: `call-${who}` }] })] };
  };
  let g = new StateGraph(State).addNode("agent", callModel).addNode("tools", new ToolNode([record]))
    .addEdge(START, "agent").addEdge("agent", "tools").addEdge("tools", END).compile({ checkpointer });
  return sharedBound ? g.withConfig(sharedBound) : g;
}

async function scenarioA(n, jitter) {
  // Upstream regression scenario (PR #2552 test), scaled to n concurrent threads.
  const checkpointer = new MemorySaver();
  const sharedBound = { metadata: { graph_id: "agent" }, configurable: { ls_agent_type: "chatbot" } };
  const before = JSON.stringify(sharedBound);
  const graph = build(checkpointer, sharedBound, (c) => (jitter ? (c.charCodeAt(c.length - 1) * 7) % 40 : 50));
  const threads = Array.from({ length: n }, (_, i) => `customer-${i}`);
  const results = await Promise.all(threads.map((c) => graph.invoke({ messages: [new HumanMessage(`Order for ${c}`)], customer: c }, { configurable: { thread_id: c } })));
  let wrongTool = 0, wrongCkpt = 0, examples = [];
  for (let i = 0; i < n; i++) {
    const c = threads[i];
    const tm = results[i].messages.find((m) => m._getType() === "tool");
    if (tm?.content !== `recorded:${c}:thread=${c}`) { wrongTool++; if (examples.length < 3) examples.push({ thread: c, tool: tm?.content }); }
    const ck = await checkpointer.getTuple({ configurable: { thread_id: c } });
    if (ck?.checkpoint.channel_values?.customer !== c) wrongCkpt++;
  }
  return { n, jitter, wrongTool, wrongCkpt, boundConfigMutated: JSON.stringify(sharedBound) !== before, boundAfter: sharedBound, examples };
}

async function scenarioB() {
  // Stale ambient context: a root invoke for thread B is started from inside thread A's running node
  // (as a queue worker callback created in A's async chain would be). B passes only thread_id.
  const seen = {};
  let inner;
  const g2 = new StateGraph(State).addNode("n", async (_s, config) => {
    seen[config.configurable.thread_id] = { tenant_id: config.configurable.tenant_id ?? null, user_id: config.configurable.user_id ?? null };
    return { seen_tenant: String(config.configurable.tenant_id ?? "") };
  }).addEdge(START, "n").addEdge("n", END).compile({ checkpointer: new MemorySaver() });
  const g1 = new StateGraph(State).addNode("n", async (_s, config) => {
    seen[config.configurable.thread_id] = { tenant_id: config.configurable.tenant_id ?? null, user_id: config.configurable.user_id ?? null };
    inner = g2.invoke({ customer: "B" }, { configurable: { thread_id: "thread-B" } });
    await inner;
    return {};
  }).addEdge(START, "n").addEdge("n", END).compile({ checkpointer: new MemorySaver() });
  await g1.invoke({ customer: "A" }, { configurable: { thread_id: "thread-A", tenant_id: "tenant-A", user_id: "user-A" } });
  return { seen, leaked: seen["thread-B"]?.tenant_id === "tenant-A" || seen["thread-B"]?.user_id === "user-A" };
}

async function scenarioC(detached) {
  // Ambient context WITHOUT graph nesting keys: the job handler runs inside a LangChain runnable whose
  // config carries tenant/user keys (as a wrapper chain or a queue worker's runnable would), then starts a
  // fresh root invoke for another thread that passes only thread_id. detached=true: the invoke is started
  // in a timer created inside the wrapper (a stale continuation) and awaited outside.
  const { RunnableLambda } = await import(require.resolve("@langchain/core/runnables"));
  const seen = {};
  const g = new StateGraph(State).addNode("n", async (_s, config) => {
    seen[config.configurable.thread_id] = { tenant_id: config.configurable.tenant_id ?? null, user_id: config.configurable.user_id ?? null };
    return {};
  }).addEdge(START, "n").addEdge("n", END).compile({ checkpointer: new MemorySaver() });
  let pending;
  const wrapper = RunnableLambda.from(async () => {
    if (detached) {
      pending = new Promise((res, rej) => setTimeout(() => g.invoke({ customer: "B" }, { configurable: { thread_id: "thread-B" } }).then(res, rej), 10));
      return "scheduled";
    }
    return g.invoke({ customer: "B" }, { configurable: { thread_id: "thread-B" } });
  });
  await wrapper.invoke({}, { configurable: { thread_id: "thread-A", tenant_id: "tenant-A", user_id: "user-A" } });
  if (pending) await pending;
  return { detached, seen, leaked: seen["thread-B"]?.tenant_id === "tenant-A" || seen["thread-B"]?.user_id === "user-A" };
}

const out = { package: "@langchain/langgraph", version, core: require("@langchain/core/package.json").version, node: process.version, scenarioA: [], scenarioB: null };
for (const [n, j] of [[4, false], [50, true], [200, true]]) {
  try { out.scenarioA.push(await scenarioA(n, j)); } catch (e) { out.scenarioA.push({ n, error: String(e).slice(0, 300) }); }
}
try { out.scenarioB = await scenarioB(); } catch (e) { out.scenarioB = { error: String(e).slice(0, 300) }; }
out.scenarioC = [];
for (const d of [false, true]) { try { out.scenarioC.push(await scenarioC(d)); } catch (e) { out.scenarioC.push({ detached: d, error: String(e).slice(0, 300) }); } }
console.log(JSON.stringify(out, null, 1));
