"""Deliberately under-constrained spec. Used to stress the system: option
generators tend to fan out wildly and consultant verdicts cluster near
the middle with high variance, exposing where confident recommendation
breaks down. Drives one of the failure cases."""
from ..types import AssignmentSpec

SPEC = AssignmentSpec(
    title="Make something cool with AI",
    description=(
        "Build a project that uses AI in some interesting way. The exact "
        "scope, audience, and form of the deliverable are up to you."
    ),
    constraints=[
        "Should be 'interesting'.",
        "Should use AI.",
    ],
    deadline_days=14.0,
)
