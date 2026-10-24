import asyncio, json
from ag2 import Agent
from ag2.config import LLMClient, ModelConfig
from ag2.events import ModelMessage, ModelResponse, ToolCallEvent, ToolCallsEvent, ToolResultEvent, ToolErrorEvent
from harness import next_step


class StubClient(LLMClient):
    def __init__(self, plan):
        self.plan, self.calls, self.last_messages = plan, 0, []

    async def __call__(self, messages, context, **kwargs):
        self.calls += 1
        self.last_messages = list(messages)
        texts = []
        for m in messages:
            for r in getattr(m, "results", None) or ([m] if isinstance(m, ToolResultEvent) else []):
                texts.append(str(getattr(r, "error", "") or "") + " " + str(r.result))
        nxt = next_step(texts, len(self.plan))
        if nxt is None:
            msg = ModelMessage("FINISHED")
            await context.send(msg)
            return ModelResponse(msg)
        return ModelResponse(tool_calls=ToolCallsEvent([ToolCallEvent(self.plan[nxt - 1][0], arguments=json.dumps({"step": nxt}))]))


class StubConfig(ModelConfig):
    def __init__(self, plan):
        self.client = StubClient(plan)
    @property
    def provider(self):
        raise NotImplementedError
    @property
    def model(self):
        return "deterministic-stub"
    def copy(self):
        return self
    def create(self):
        return self.client
    def create_files_client(self):
        raise NotImplementedError


def run_ag2(run):
    def mk(op):
        def f(step: int) -> str:
            return run.execute(op, step)
        f.__name__ = op
        f.__doc__ = f"sandbox op {op}"
        return f
    cfg = StubConfig(run.plan)
    agent = Agent("planner", "run the plan", config=cfg, tools=[mk(op) for op, _ in run.plan])
    native = {"raised": None}
    async def go():
        r = agent.ask("run the plan")
        if asyncio.iscoroutine(r) or hasattr(r, "__await__"):
            r = await r
        return r
    try:
        asyncio.run(go())
    except Exception as e:
        native["raised"] = f"{type(e).__name__}: {str(e)[:200]}"
    trace = []
    for m in cfg.client.last_messages:
        for r in getattr(m, "results", None) or ([m] if isinstance(m, ToolResultEvent) else []):
            trace.append({"tool": r.name, "status": "error" if isinstance(r, ToolErrorEvent) else "success",
                          "content": (str(getattr(r, "error", "")) or str(r.result))[:160]})
    native["model_calls"] = cfg.client.calls
    return trace, native
