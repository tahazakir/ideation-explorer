from ..types import AssignmentSpec

SPEC = AssignmentSpec(
    title="Build a Predictive ML Pipeline",
    description=(
        "Given a specific dataset (textual, tabular, or image-based), design and implement "
        "a machine learning pipeline that cleans data, performs feature engineering, and trains "
        "a predictive model. The deliverable should help a stakeholder understand: the predictive "
        "power of the features, the model's performance against a baseline, and how it handles "
        "unseen data."
    ),
    constraints=[
        "Deliver a documented Jupyter Notebook (or Python script) with training/evaluation loops",
        "At least 2 distinct model architectures",
        "1-page report on error analysis",
        "Compare performance against a baseline",
        "Evaluate on unseen (held-out) test data",
    ],
    deadline_days=14.0,
)
