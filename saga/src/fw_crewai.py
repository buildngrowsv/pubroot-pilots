import os, re
os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")
os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew
from crewai.llms.base_llm import BaseLLM
from crewai.tools import BaseTool
from harness import next_step


class StubLLM(BaseLLM):
    plan: list = []
    calls: int = 0
    last_messages: list = []

    def call(self, messages, tools=None, callbacks=None, available_functions=None, from_task=None,
             from_agent=None, response_model=None):
        self.calls += 1
        msgs = messages if isinstance(messages, list) else [{"role": "user", "content": messages}]
        self.last_messages = msgs
        texts = [str(m.get("content", "")) for m in msgs if m.get("role") != "system"]
        nxt = next_step(texts, len(self.plan))
        if nxt is None:
            return "Thought: I now know the final answer\nFinal Answer: FINISHED"
        op = self.plan[nxt - 1][0]
        return f'Thought: run step {nxt}\nAction: {op}\nAction Input: {{"step": {nxt}}}'

    def supports_function_calling(self):
        return False

    def supports_stop_words(self):
        return False

    def get_context_window_size(self):
        return 8192


class StepArgs(BaseModel):
    step: int = Field(..., description="plan step number")


def run_crewai(run):
    tools = []
    for op, _ in run.plan:
        def _run(self, step: int, _op=op) -> str:
            return run.execute(_op, step)
        cls = type(f"T_{op}", (BaseTool,), {"__module__": __name__, "__annotations__": {"name": str, "description": str, "args_schema": type},
                                            "name": op, "description": f"sandbox op {op}", "args_schema": StepArgs,
                                            "_run": _run})
        tools.append(cls())
    llm = StubLLM(model="deterministic-stub", plan=run.plan)
    agent = Agent(role="planner", goal="run the plan", backstory="stub", llm=llm, tools=tools,
                  allow_delegation=False, max_iter=25, verbose=False)
    task = Task(description="Run the plan step by step.", expected_output="FINISHED", agent=agent)
    native = {"raised": None}
    try:
        Crew(agents=[agent], tasks=[task], verbose=False).kickoff()
    except Exception as e:
        native["raised"] = f"{type(e).__name__}: {str(e)[:200]}"
    joined = "\n".join(str(m.get("content", "")) for m in llm.last_messages)
    trace = []
    for m in re.finditer(r"OK:step=(\d+)|FAULT:step=(\d+)", joined):
        trace.append({"tool": None, "status": "success" if m.group(1) else "error", "content": m.group(0)})
    native["model_calls"] = llm.calls
    return trace, native
