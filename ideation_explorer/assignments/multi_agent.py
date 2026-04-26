"""The meta assignment: this is the brief our own project (the ideation
explorer) is built against. Including it lets us dogfood the system."""
from ..types import AssignmentSpec

SPEC = AssignmentSpec(
    title="Design and build a multi-agent system for a real task",
    description=(
        "Design, implement, and evaluate a multi-agent system that solves a "
        "concrete task. The system should exhibit meaningful coordination "
        "among agents (planning, branching, delegation, or aggregation) and "
        "ship with a runnable artifact, evaluation evidence, and a written report."
    ),
    constraints=[
        "Must include at least two distinct agent roles with different responsibilities.",
        "Must produce traceable logs showing inter-agent communication.",
        "Must include >=5 evaluation cases and >=2 documented failure cases.",
        "Total cost per representative run should remain reasonable (token-bounded).",
        "Must be reproducible from the repo with a single documented command.",
    ],
    deadline_days=14.0,
)
