"""llama_index #21774: AgentWorkflow reused across run() calls leaks initial_state mutations between runs.
Follows the issue's script, with a scripted function-calling stub LLM (no network) so the tool is called exactly once per run.
Also checks a nested value (list) and the single-agent path. Prints JSON."""
import asyncio, json, importlib.metadata as md, os
from llama_index.core.agent.workflow import AgentWorkflow, FunctionAgent
from llama_index.core.workflow import Context
from llama_index.core.llms.mock import MockFunctionCallingLLM
from llama_index.core.llms import ChatMessage, ChatResponse
from llama_index.core.llms.llm import ToolSelection
from llama_index.core.base.llms.types import ChatResponseAsyncGen

class ScriptedLLM(MockFunctionCallingLLM):
    """First turn of each run: call bump_counter once. After a tool result: reply 'done'."""
    async def astream_chat_with_tools(self, tools, user_msg=None, chat_history=None, **kw):
        msgs = list(chat_history or [])
        called = any(getattr(getattr(m, "role", None), "value", str(getattr(m, "role", ""))).lower() == "tool" for m in msgs)
        async def gen():
            if called:
                yield ChatResponse(message=ChatMessage(role="assistant", content="done"), delta="done")
            else:
                m = ChatMessage(role="assistant", content="")
                m.additional_kwargs["tool_calls"] = [{"id": "c1", "name": "bump_counter", "args": {}}]
                yield ChatResponse(message=m, delta="")
        return gen()
    async def achat_with_tools(self, tools, user_msg=None, chat_history=None, **kw):
        last = None
        async for r in await self.astream_chat_with_tools(tools, user_msg, chat_history, **kw): last = r
        return last
    def get_tool_calls_from_response(self, response, error_on_no_tool_call=True, **kw):
        tc = response.message.additional_kwargs.get("tool_calls", [])
        return [ToolSelection(tool_id=t["id"], tool_name=t["name"], tool_kwargs=t["args"]) for t in tc]

CALLS = {"n": 0}
async def bump_counter(ctx: Context) -> str:
    """Increment the counter in workflow state."""
    CALLS["n"] += 1
    async with ctx.store.edit_state() as state:
        state["state"]["counter"] += 1
        state["state"]["log"].append(CALLS["n"])
    return "bumped"

async def two_runs(wf):
    await wf.run(user_msg="bump it")
    h = wf.run(user_msg="bump it"); await h
    return await h.ctx.store.get("state")

async def main():
    out = {"llama-index-core": md.version("llama-index-core")}
    init = {"counter": 0, "log": []}
    wf = AgentWorkflow.from_tools_or_functions([bump_counter], llm=ScriptedLLM(), system_prompt="Call bump_counter once.", initial_state=init)
    out["multi_agent_path"] = {"agent_class": type(wf).__name__, "second_run_state": await two_runs(wf), "initial_state_after": init, "tool_calls_total": CALLS["n"]}
    CALLS["n"] = 0
    init2 = {"counter": 0, "log": []}
    ag = FunctionAgent(tools=[bump_counter], llm=ScriptedLLM(), system_prompt="Call bump_counter once.", initial_state=init2)
    out["single_agent_path"] = {"agent_class": type(ag).__name__, "second_run_state": await two_runs(ag), "initial_state_after": init2, "tool_calls_total": CALLS["n"]}
    for k in ("multi_agent_path", "single_agent_path"):
        s = out[k]["second_run_state"]
        out[k]["expected_second_run"] = {"counter": 1, "log": [2]}
        out[k]["leaked"] = (s.get("counter") != 1) or (len(s.get("log", [])) != 1) or out[k]["initial_state_after"] != {"counter": 0, "log": []}
    print(json.dumps(out, indent=1, default=str))
asyncio.run(main())
