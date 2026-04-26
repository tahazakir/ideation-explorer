from ..types import AssignmentSpec

SPEC = AssignmentSpec(
    title="Write a focused literature review on retrieval-augmented generation",
    description=(
        "Produce a literature review surveying the development of "
        "retrieval-augmented generation (RAG) for large language models. "
        "Identify major design families, representative papers, and open "
        "research questions, with a clear thesis about where the field is heading."
    ),
    constraints=[
        "Maximum 8 pages, single column, 11pt font.",
        "Cite at least 20 peer-reviewed or arXiv papers, all post-2019.",
        "Must include a taxonomy diagram of RAG architectures.",
        "Must end with a section identifying at least 3 open research questions.",
        "All claims about empirical results must be cited to a specific paper.",
    ],
    deadline_days=10.0,
)
