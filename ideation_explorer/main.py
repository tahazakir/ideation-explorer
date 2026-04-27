"""Entrypoint: ideate over an assignment, dump trace + recommended plan.

Governance flags:
    --max-consultations N   hard cap on consultant LLM calls (cost ceiling)
    --min-margin F          if best - second-best root quality < F, the run
                            reports LOW_CONFIDENCE and refuses to recommend

Usage:
    python -m ideation_explorer.main \
        --assignment dummy --rooms 2 --depth 3 --options 3 \
        --out outputs/runs/dummy_run.json
"""
import argparse
import asyncio
import importlib
import json
import os
import time

from .consultant_pool import ConsultantPool
from .explorer import explore
from .recorder import RECORDER
from .types import AssignmentSpec, NodeResult


def load_assignment(name: str) -> AssignmentSpec:
    if name == "dummy":
        from .dummy_assignment import DUMMY
        return DUMMY
    mod = importlib.import_module(f"ideation_explorer.assignments.{name}")
    spec = getattr(mod, "SPEC", None)
    if spec is None:
        raise ValueError(f"module {mod.__name__} has no SPEC")
    return spec


def assess_confidence(root: NodeResult, min_margin: float) -> dict:
    """Inspect the root's branches and decide whether the recommendation
    is trustworthy. Returns a structured advisory record."""
    if not root.branches:
        return {"low_confidence": False, "refused": False, "reason": "no branching"}
    qs = sorted((b.verdict.quality for b in root.branches), reverse=True)
    margin = qs[0] - qs[1] if len(qs) > 1 else float("inf")
    budget_hit = root.verdict.budget_exhausted
    low = margin < min_margin or budget_hit
    reasons = []
    if margin < min_margin:
        reasons.append(f"top-two margin {margin:.3f} < threshold {min_margin:.3f}")
    if budget_hit:
        reasons.append("consultant budget exhausted; some leaves were not evaluated")
    return {
        "low_confidence": low,
        "refused": low,
        "margin": margin,
        "budget_exhausted": budget_hit,
        "reason": "; ".join(reasons) if reasons else "ok",
    }


def build_run_record(spec: AssignmentSpec, root: NodeResult, args, advisory: dict, pool: ConsultantPool) -> dict:
    return {
        "assignment": {
            "name": args.assignment,
            "title": spec.title,
            "description": spec.description,
            "constraints": spec.constraints,
            "deadline_days": spec.deadline_days,
        },
        "config": {
            "n_rooms": args.rooms,
            "max_depth": args.depth,
            "max_options": args.options,
            "max_consultations": args.max_consultations,
            "min_margin": args.min_margin,
        },
        "metrics": RECORDER.summary(),
        "pool": {"completed": pool.completed, "refused": pool.refused},
        "advisory": advisory,
        "recommended_plan": [] if advisory["refused"] else root.best_path(),
        "root": root.to_jsonable(),
        "llm_calls": RECORDER.to_jsonable(),
        "ts_finished": time.time(),
    }


async def main_async(args):
    spec = load_assignment(args.assignment)
    pool = ConsultantPool(spec, n_rooms=args.rooms, max_consultations=args.max_consultations)
    RECORDER.reset()

    print(f"=== Ideation explorer: {spec.title} ===\n")
    root = await explore(
        spec, pool, history=[],
        max_depth=args.depth, max_options=args.options,
    )

    effective_margin = max(args.min_margin, spec.min_margin)
    advisory = assess_confidence(root, effective_margin)
    record = build_run_record(spec, root, args, advisory, pool)

    print("\n=== Result ===")
    print(f"Consultations: completed={pool.completed} refused={pool.refused}"
          + (f"  (cap={args.max_consultations})" if args.max_consultations else ""))
    print(f"Wall time:     {record['metrics']['wall_time_s']:.2f}s")
    print(f"LLM calls:     {record['metrics']['total_calls']}  "
          f"(in_tok={record['metrics']['total_input_tokens']}, "
          f"out_tok={record['metrics']['total_output_tokens']})")
    print(f"Root quality:  {root.verdict.quality:.3f}  (stddev across root options: {root.verdict.quality_stddev:.3f})")
    print(f"Root est days: {root.verdict.scope_fit:.2f}")

    if root.branches:
        print("\nPer-option breakdown at root:")
        for b in sorted(root.branches, key=lambda x: -x.verdict.quality):
            tag = "  [BUDGET-HIT]" if b.verdict.budget_exhausted else ""
            print(f"  - {b.option}{tag}")
            print(f"      quality={b.verdict.quality:.3f}  scope_fit={b.verdict.scope_fit:.2f}  n={b.verdict.n_consultations}")
            print(f"      notes: {b.verdict.notes[:160]}")

    print()
    if advisory["refused"]:
        print(f"!! LOW CONFIDENCE -- recommendation withheld.")
        print(f"   reason: {advisory['reason']}")
    else:
        print("RECOMMENDED FULL PLAN:")
        for i, step in enumerate(root.best_path(), 1):
            print(f"  {i}. {step}")

    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w") as f:
            json.dump(record, f, indent=2)
        print(f"\nTrace written to {args.out}")

    if args.plan_out and not advisory["refused"]:
        os.makedirs(os.path.dirname(args.plan_out) or ".", exist_ok=True)
        plan = {
            "assignment": record["assignment"],
            "recommended_plan": record["recommended_plan"],
            "expected_quality": root.verdict.quality,
            "expected_days": root.verdict.scope_fit,
            "advisory": advisory,
        }
        with open(args.plan_out, "w") as f:
            json.dump(plan, f, indent=2)
        print(f"Plan written to {args.plan_out}")
    elif args.plan_out and advisory["refused"]:
        print(f"Plan NOT written to {args.plan_out} (low confidence).")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--assignment", default="dummy")
    p.add_argument("--rooms", type=int, default=2)
    p.add_argument("--depth", type=int, default=3)
    p.add_argument("--options", type=int, default=3)
    p.add_argument("--max-consultations", type=int, default=None,
                   help="hard cap on consultant LLM calls (cost ceiling). default: no cap")
    p.add_argument("--min-margin", type=float, default=0.05,
                   help="if top-two root quality margin is below this, refuse to recommend. default 0.05")
    p.add_argument("--out", default=None)
    p.add_argument("--plan-out", default=None)
    return p.parse_args()


if __name__ == "__main__":
    asyncio.run(main_async(parse_args()))
