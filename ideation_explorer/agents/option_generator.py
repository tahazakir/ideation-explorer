"""Option generator: given the assignment + decisions made so far,
proposes the next landmark decisions to branch on. Returns [] if the
plan is complete enough to send to a consultant."""
from ..llm import call_llm, extract_json
from ..types import AssignmentSpec

SYSTEM = """You are a planning assistant for student assignments.

Given an assignment spec and the landmark decisions already made, identify
the SINGLE next landmark decision point and list the distinct, mutually
exclusive options for it. Skip trivial choices.

If the plan so far is concrete enough to evaluate end-to-end (i.e. a
consultant could judge feasibility), return an empty list to terminate.

Hard limits:
- At most {max_options} options per decision point.
- Return [] once depth reaches a natural plan (typically 3-5 decisions).

Respond with JSON only:
{{"decision": "<short name of the decision point>", "options": ["opt1", "opt2", ...]}}
or
{{"decision": null, "options": []}}
"""


async def generate_options(
    spec: AssignmentSpec,
    history: list[str],
    max_options: int = 3,
    max_depth: int = 3,
) -> tuple[str | None, list[str]]:
    if len(history) >= max_depth:
        return None, []

    user = (
        f"ASSIGNMENT: {spec.title}\n"
        f"{spec.description}\n\n"
        f"CONSTRAINTS:\n- " + "\n- ".join(spec.constraints) + "\n\n"
        f"DEADLINE: {spec.deadline_days} days\n\n"
        f"DECISIONS MADE SO FAR ({len(history)}):\n"
        + ("\n".join(f"  {i+1}. {h}" for i, h in enumerate(history)) or "  (none)")
        + "\n\nWhat is the next landmark decision and its options?"
    )
    raw = await call_llm(
        SYSTEM.format(max_options=max_options), user,
        agent_role="option_generator", history_depth=len(history), max_tokens=800,
    )
    data = extract_json(raw)
    decision = data.get("decision")
    options = data.get("options") or []
    return decision, options[:max_options]
