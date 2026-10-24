import json
from typing import Any
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import StructuredTool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent
from harness import next_step


class StubChat(BaseChatModel):
    n: int = 6
    calls: int = 0

    @property
    def _llm_type(self):
        return "deterministic-stub"

    def bind_tools(self, tools, **kw):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kw):
        self.calls += 1
        texts = [str(m.content) for m in messages if isinstance(m, ToolMessage)]
        nxt = next_step(texts, self.n)
        if nxt is None:
            msg = AIMessage(content="FINISHED")
        else:
            op = self._plan[nxt - 1][0]
            msg = AIMessage(content="", tool_calls=[{"name": op, "args": {"step": nxt}, "id": f"c{nxt}-{self.calls}"}])
        return ChatResult(generations=[ChatGeneration(message=msg)])


def run_langgraph(run):
    def mk(op):
        def f(step: int) -> str:
            return run.execute(op, step)
        return StructuredTool.from_function(f, name=op, description=f"sandbox op {op}")
    tools = [mk(op) for op, _ in run.plan]
    model = StubChat(n=len(run.plan))
    object.__setattr__(model, "_plan", run.plan)
    saver = InMemorySaver()
    agent = create_react_agent(model, tools, checkpointer=saver)
    cfg = {"configurable": {"thread_id": "t1"}, "recursion_limit": 50}
    native = {"raised": None}
    try:
        agent.invoke({"messages": [("user", "run the plan")]}, cfg)
    except Exception as e:  # record, do not hide
        native["raised"] = f"{type(e).__name__}: {str(e)[:200]}"
    state = agent.get_state(cfg)
    msgs = state.values.get("messages", [])
    trace = []
    for m in msgs:
        if isinstance(m, ToolMessage):
            trace.append({"tool": m.name, "status": getattr(m, "status", None), "content": str(m.content)[:160]})
    native["checkpoints"] = len(list(saver.list(cfg)))
    native["model_calls"] = model.calls
    return trace, native
