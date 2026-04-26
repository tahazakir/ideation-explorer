from ..types import AssignmentSpec

SPEC = AssignmentSpec(
    title="Build an AI-Powered Application",
    description=(
        "Design and implement an original AI application that applies one or more techniques "
        "from the course (computer vision, NLP, deep learning, structured prediction) to a "
        "real-world problem. The system must go beyond a tutorial re-implementation: it should "
        "address a genuine user need, demonstrate working inference on real inputs, and include "
        "a written reflection on limitations and failure cases."
    ),
    constraints=[
        "Working demo on real-world inputs (not just toy examples)",
        "At least one trained or fine-tuned model component (not pure rule-based)",
        "Written reflection: limitations, failure modes, ethical considerations",
        "Clear articulation of the user or stakeholder the system serves",
        "Code and model weights submitted with reproducible setup instructions",
    ],
    deadline_days=30.0,
)
