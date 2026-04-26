"""Simplified Anand-style assignment used for consultant calibration.

Stripped down to the core of both his assignments so he can evaluate
a plan in ~20 seconds without needing to re-read a full brief."""
from ..types import AssignmentSpec

SPEC = AssignmentSpec(
    title="Model AI's effect on one job category",
    description=(
        "Pick one job category and model how AI adoption disrupts and reshapes "
        "that workforce. Use either a causal loop diagram (8-10 variables) or a "
        "small agent-based simulation (15-20 workers). Compare exactly two "
        "scenarios: high automation pressure vs. high worker support. Deliver a "
        "1-page memo and one figure (diagram or screenshot)."
    ),
    constraints=[
        "Must compare exactly two scenarios: high automation pressure vs. high worker support.",
        "CLD option: 8-10 variables, at least 1 reinforcing loop, 1 balancing loop, 1 delay.",
        "Agent sim option: 15-20 workers, at least 3 states, 1 explicit emergent mechanism.",
        "Deliverable: 1-page memo + one figure. No code submission required for CLD track.",
        "Must distinguish programmed behavior from emergent outcomes in the interpretation.",
        "AI use must be documented with exact prompts and what was changed manually.",
    ],
    deadline_days=7.0,
)
