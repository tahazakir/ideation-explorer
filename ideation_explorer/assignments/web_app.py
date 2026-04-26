from ..types import AssignmentSpec

SPEC = AssignmentSpec(
    title="Build a small web app that visualizes city air-quality data",
    description=(
        "Build a single-page web application that fetches public air-quality "
        "measurements for a chosen city and presents them visually. The app "
        "should let a user pick a city, see current AQI, and view a 7-day trend."
    ),
    constraints=[
        "Must be a single-page web app (no multi-page navigation).",
        "Must use a free public air-quality data source.",
        "Must run locally with a single command (no paid hosting required).",
        "Source code under 1500 lines total.",
        "Must include at least one chart/visualization.",
    ],
    deadline_days=7.0,
)
