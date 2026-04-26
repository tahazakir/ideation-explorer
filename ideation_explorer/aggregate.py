"""Aggregate child branch verdicts into a single verdict for an antenna.

The rolled-up Verdict carries:
  - quality         : consultation-weighted mean across child branches
  - scope_fit        : consultation-weighted mean
  - notes           : the best child's notes (preserves consultant feasibility text up the tree)
  - quality_stddev  : population stddev of child branch qualities, used downstream
                      as a confidence signal at this antenna
"""
import math
from .types import BranchReport, Verdict


def aggregate(branches: list[BranchReport]) -> tuple[Verdict, str]:
    assert branches, "aggregate called with no branches"
    total_consults = sum(b.verdict.n_consultations for b in branches)
    qualities = [b.verdict.quality for b in branches]
    if total_consults == 0:
        avg_quality = sum(qualities) / len(qualities)
        avg_days = sum(b.verdict.scope_fit for b in branches) / len(branches)
    else:
        avg_quality = sum(b.verdict.quality * b.verdict.n_consultations for b in branches) / total_consults
        avg_days = sum(b.verdict.scope_fit * b.verdict.n_consultations for b in branches) / total_consults

    if len(qualities) > 1:
        mu = sum(qualities) / len(qualities)
        stddev = math.sqrt(sum((q - mu) ** 2 for q in qualities) / len(qualities))
    else:
        stddev = 0.0

    best = max(branches, key=lambda b: b.verdict.quality)
    return Verdict(
        quality=avg_quality,
        scope_fit=avg_days,
        notes=best.verdict.notes,
        n_consultations=total_consults,
        quality_stddev=stddev,
        budget_exhausted=any(b.verdict.budget_exhausted for b in branches),
    ), best.option
