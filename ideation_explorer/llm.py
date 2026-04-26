"""Thin async Claude wrapper with token/latency instrumentation.

Every call is recorded into the module-level RECORDER so the run trace
can report cost and latency per agent role."""
import os
import json
import re
import time
from dotenv import load_dotenv
from anthropic import AsyncAnthropic

from .recorder import RECORDER, LLMCall

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

DEFAULT_MODEL = "claude-haiku-4-5-20251001"

_client: AsyncAnthropic | None = None


def _get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        key = os.environ.get("CLAUDE_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("CLAUDE_API_KEY / ANTHROPIC_API_KEY not set")
        _client = AsyncAnthropic(api_key=key)
    return _client


async def call_llm(
    system: str,
    user: str,
    *,
    agent_role: str,
    history_depth: int,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 2048,
) -> str:
    client = _get_client()
    started = time.time()
    try:
        resp = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
    except Exception as e:
        RECORDER.add(LLMCall(
            agent_role=agent_role, model=model, input_tokens=0, output_tokens=0,
            duration_s=time.time() - started, started_at=started,
            history_depth=history_depth, ok=False, error=str(e)[:300],
        ))
        raise

    RECORDER.add(LLMCall(
        agent_role=agent_role, model=model,
        input_tokens=getattr(resp.usage, "input_tokens", 0),
        output_tokens=getattr(resp.usage, "output_tokens", 0),
        duration_s=time.time() - started, started_at=started,
        history_depth=history_depth,
    ))
    return "\n".join(b.text for b in resp.content if b.type == "text").strip()


def extract_json(text: str) -> dict | list:
    """Pull the first JSON object/array out of a model response."""
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    start = next((i for i, c in enumerate(text) if c in "{["), None)
    if start is None:
        raise ValueError(f"no JSON found in: {text[:200]}")
    for end in range(len(text), start, -1):
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            continue
    raise ValueError(f"unparseable JSON in: {text[:200]}")
