"""Software Engineering assignment: campus dining web app."""
from ..types import AssignmentSpec

SPEC = AssignmentSpec(
    title="Design and develop a web app for campus dining information",
    description=(
        "Build a web application that helps students find and navigate campus "
        "dining options. The app should surface real-time or scheduled information "
        "about dining halls, menus, hours, and wait times. Students should be able "
        "to filter, search, and plan their meals. Deliver a working prototype with "
        "at least 3 core features, a brief design document explaining your "
        "architecture decisions, and a short demo."
    ),
    constraints=[
        "Must be a working prototype, not a mockup or wireframe.",
        "At least 3 distinct user-facing features (e.g. menu browsing, filtering, favorites).",
        "Must handle at least one external data source (scraped, API, or mocked dataset).",
        "Include a design document covering component structure and data flow.",
        "No specific framework required but choice must be justified.",
        "AI use must be documented: what was generated vs. written manually.",
    ],
    deadline_days=14.0,
)
