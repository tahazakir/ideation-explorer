"""Data Visualization assignment: user journey and behavior visualization."""
from ..types import AssignmentSpec

SPEC = AssignmentSpec(
    title="Build visualizations to explore user journeys and behaviors on an app",
    description=(
        "Given a dataset of user events (clicks, page views, session starts/ends, "
        "conversions) from a mobile or web app, design and implement a visualization "
        "suite that reveals how users move through the product. The deliverable should "
        "help a product team answer: where do users drop off, which paths lead to "
        "conversion, and how do power users differ from casual ones. Deliver at least "
        "2 distinct visualization types and a 1-page written interpretation."
    ),
    constraints=[
        "At least 2 distinct visualization types (e.g. Sankey + heatmap, not two bar charts).",
        "Must handle real or realistic synthetic event-log data (not aggregated summaries).",
        "Visualizations must be readable without explanation — axis labels, legends, titles required.",
        "At least one visualization must show a temporal or sequential dimension (flows, funnels, paths).",
        "Written interpretation must reference specific visual features, not just restate the data.",
        "AI use must be documented: what was generated vs. designed manually.",
    ],
    deadline_days=10.0,
)
