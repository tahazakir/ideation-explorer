from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AssignmentSpec:
    title: str
    description: str
    constraints: list[str]
    deadline_days: float


@dataclass
class Verdict:
    """Result of evaluating a (possibly partial) plan history."""
    quality: float
    scope_fit: float          # 0-1, how well the plan fits the available time and constraints
    notes: str
    n_consultations: int = 1
    quality_stddev: float = 0.0       # spread across child branches at this antenna (0 for leaves)
    budget_exhausted: bool = False    # set when the consultant pool refused this request


@dataclass
class BranchReport:
    """A single child branch hanging off an antenna."""
    option: str
    verdict: Verdict
    child: "NodeResult"


@dataclass
class NodeResult:
    """What an explorer returns to its parent."""
    history: list[str]
    verdict: Verdict
    decision: Optional[str] = None              # the decision point this node split on (None if leaf)
    branches: list[BranchReport] = field(default_factory=list)
    chosen_best_option: Optional[str] = None
    is_leaf: bool = False

    def best_path(self) -> list[str]:
        """Walk down the tree following the highest-quality branch at every split."""
        path: list[str] = []
        node = self
        while node.branches and node.chosen_best_option:
            path.append(node.chosen_best_option)
            nxt = next((b.child for b in node.branches if b.option == node.chosen_best_option), None)
            if nxt is None:
                break
            node = nxt
        return path

    def to_jsonable(self) -> dict:
        return {
            "history": self.history,
            "decision": self.decision,
            "is_leaf": self.is_leaf,
            "verdict": {
                "quality": self.verdict.quality,
                "scope_fit": self.verdict.scope_fit,
                "notes": self.verdict.notes,
                "scope_fit": self.verdict.scope_fit,
                "n_consultations": self.verdict.n_consultations,
                "quality_stddev": self.verdict.quality_stddev,
                "budget_exhausted": self.verdict.budget_exhausted,
            },
            "chosen_best_option": self.chosen_best_option,
            "branches": [
                {"option": b.option, "child": b.child.to_jsonable()}
                for b in self.branches
            ],
        }
