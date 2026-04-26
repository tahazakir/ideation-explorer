from ..types import AssignmentSpec

SPEC = AssignmentSpec(
    title="Train and evaluate a small image classifier on CIFAR-10",
    description=(
        "Produce a Jupyter notebook that loads CIFAR-10, trains an image "
        "classifier from scratch, and reports test accuracy with a confusion "
        "matrix and at least one ablation comparing two design choices."
    ),
    constraints=[
        "Single notebook, runnable end-to-end on a free Colab T4 in under 30 minutes.",
        "No pretrained weights; the model must be trained from scratch.",
        "Final reported test accuracy must exceed 70%.",
        "Include one ablation study (e.g. with vs. without data augmentation).",
        "All hyperparameters declared in a single config cell at the top.",
    ],
    deadline_days=5.0,
)
