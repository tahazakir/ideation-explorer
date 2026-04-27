"""Simplified Anand-style assignment used for consultant calibration.

Stripped down to the core of both his assignments so he can evaluate
a plan in ~20 seconds without needing to re-read a full brief."""
from ..types import AssignmentSpec

SPEC = AssignmentSpec(
    title="Model AI's effect on one job category",
    description=(
        "Build a small agent-based simulation (15-20 workers) that models how AI "
        "adoption disrupts and reshapes one job category. The most critical early "
        "decision is your implementation tool: NetLogo (the standard ABM platform "
        "for this course), a general-purpose language (Python with Mesa), or a "
        "spreadsheet (Excel or Google Sheets). After choosing the tool, select "
        "a job category and define the emergent mechanism. Compare exactly two "
        "scenarios: high automation pressure vs. high worker support. Deliver a "
        "1-page memo and one figure (diagram or screenshot)."
    ),
    constraints=[
        "Must compare exactly two scenarios: high automation pressure vs. high worker support.",
        "15-20 worker agents, at least 3 discrete states, 1 explicit emergent mechanism.",
        "Must distinguish programmed behavior from emergent outcomes in the interpretation.",
        "Deliverable: 1-page memo + one simulation figure.",
        "AI use must be documented with exact prompts and what was changed manually.",
    ],
    deadline_days=7.0,
)
