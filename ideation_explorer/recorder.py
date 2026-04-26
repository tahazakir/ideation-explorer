"""Process-wide recorder for LLM calls. Reset at the start of each run,
snapshot at the end, dumped into the trace JSON."""
from dataclasses import dataclass, field, asdict
from typing import Any
import time


@dataclass
class LLMCall:
    agent_role: str          # "option_generator" | "consultant"
    model: str
    input_tokens: int
    output_tokens: int
    duration_s: float
    started_at: float        # unix time
    history_depth: int       # for context
    ok: bool = True
    error: str | None = None


@dataclass
class Recorder:
    calls: list[LLMCall] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)

    def reset(self) -> None:
        self.calls.clear()
        self.started_at = time.time()

    def add(self, call: LLMCall) -> None:
        self.calls.append(call)

    def summary(self) -> dict[str, Any]:
        by_role: dict[str, dict[str, float]] = {}
        for c in self.calls:
            r = by_role.setdefault(c.agent_role, {"n": 0, "input_tokens": 0, "output_tokens": 0, "duration_s": 0.0})
            r["n"] += 1
            r["input_tokens"] += c.input_tokens
            r["output_tokens"] += c.output_tokens
            r["duration_s"] += c.duration_s
        return {
            "wall_time_s": time.time() - self.started_at,
            "total_calls": len(self.calls),
            "by_role": by_role,
            "total_input_tokens": sum(c.input_tokens for c in self.calls),
            "total_output_tokens": sum(c.output_tokens for c in self.calls),
        }

    def to_jsonable(self) -> list[dict[str, Any]]:
        return [asdict(c) for c in self.calls]


RECORDER = Recorder()
