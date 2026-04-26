"""Calibration script: sample plans and generate a rating handout for any annotator.

Workflow:
  1. Runs the ideation explorer on the given assignment.
  2. Samples a diverse set of leaf plans from across the tree
     (2 per root branch: highest-quality leaf + most-different-from-best).
  3. For each sampled plan, calls the LLM to generate a 2-3 sentence
     plain-English description of what the plan actually is.
  4. Writes two output files:
       --handout   a markdown doc you can print/show the annotator (plan + rating fields)
       --collect   a CSV with one row per plan for recording their ratings afterward

Usage:
    # Anand's calibration assignment (default)
    python -m ideation_explorer.calibrate \
        --assignment calibration --annotator anand \
        --rooms 3 --depth 3 --options 3

    # Taha's SE dining assignment
    python -m ideation_explorer.calibrate \
        --assignment se_dining --annotator taha \
        --rooms 3 --depth 2 --options 3

    # Taha's dataviz assignment
    python -m ideation_explorer.calibrate \
        --assignment dataviz_journeys --annotator taha \
        --rooms 3 --depth 2 --options 3
"""
import argparse
import asyncio
import csv
import json
import os

from .consultant_pool import ConsultantPool
from .explorer import explore
from .llm import call_llm
from .recorder import RECORDER
from .types import NodeResult


# ── helpers ──────────────────────────────────────────────────────────────────

def collect_leaves(node: NodeResult) -> list[NodeResult]:
    if node.is_leaf:
        return [node]
    leaves = []
    for b in node.branches:
        leaves.extend(collect_leaves(b.child))
    return leaves


def leaves_under_branch(branch_child: NodeResult) -> list[NodeResult]:
    return collect_leaves(branch_child)


def sample_plans(root: NodeResult, n_per_branch: int = 2) -> list[NodeResult]:
    """Pick n_per_branch diverse leaves per root branch.

    Strategy: from each root branch take the highest-quality leaf and
    the lowest-quality leaf. That maximises the range of verdicts Anand
    sees without cherry-picking only good plans."""
    sampled: list[NodeResult] = []
    for b in root.branches:
        leaves = sorted(leaves_under_branch(b.child), key=lambda n: n.verdict.quality)
        if not leaves:
            continue
        picks: list[NodeResult] = []
        picks.append(leaves[-1])                     # best
        if len(leaves) > 1 and n_per_branch > 1:
            picks.append(leaves[0])                  # worst (most different)
        for extra in range(2, n_per_branch):
            mid = len(leaves) // (extra + 1)
            if leaves[mid] not in picks:
                picks.append(leaves[mid])
        sampled.extend(picks)
    return sampled


def load_spec(name: str):
    import importlib
    if name == "dummy":
        from .dummy_assignment import DUMMY
        return DUMMY
    mod = importlib.import_module(f"ideation_explorer.assignments.{name}")
    spec = getattr(mod, "SPEC", None)
    if spec is None:
        raise ValueError(f"module {mod.__name__} has no SPEC")
    return spec


DESCRIBE_SYSTEM = """You are writing a brief plain-English description of a
project plan for an instructor to evaluate quickly.

Given the assignment brief and the sequence of decisions that define
the plan, write exactly 2-3 sentences that:
  1. Name the modeling approach and the domain chosen.
  2. Describe the core mechanism or emergent feature the plan centres on.
  3. Note how the two scenarios are distinguished.

No jargon the professor would not already know. No evaluation language
("this is a good plan"). Just describe what the student would actually build."""


async def describe_plan(spec, history: list[str]) -> str:
    user = (
        f"ASSIGNMENT: {spec.title}\n{spec.description}\n\n"
        f"PLAN DECISIONS:\n"
        + "\n".join(f"  {i+1}. {h}" for i, h in enumerate(history))
        + "\n\nWrite the 2-3 sentence description."
    )
    return await call_llm(
        DESCRIBE_SYSTEM, user,
        agent_role="calibration_describer", history_depth=len(history),
        max_tokens=300,
    )


# ── output writers ────────────────────────────────────────────────────────────

def write_handout(plans: list[tuple[int, NodeResult, str]], path: str, spec, annotator: str) -> None:
    """Write a compact handout designed to fit 2 plans per page as a PDF."""
    sections = []
    sections.append(
        f"% Calibration handout — {annotator}\n"
        f"% {spec.title}\n\n"
        f"**Annotator:** {annotator}\n\n"
        f"**Brief:** {spec.description}\n\n"
        f"**Rate each plan:** Feasibility 1-5 (1=not viable, 5=clearly doable) | "
        f"Scope fit 1-5 (1=wrong size, 5=perfectly scoped for {int(spec.deadline_days)} days) | One sentence.\n\n"
        f"\\bigskip\n"
    )
    for pid, node, description in plans:
        decisions = " → ".join(node.history)
        sections.append(
            f"**Plan {pid}:** {decisions}\n\n"
            f"{description}\n\n"
            f"Feasibility: \\_\\_\\_ / 5 \\quad Scope fit: \\_\\_\\_ / 5\n\n"
            f"Notes: \\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\n\n"
            f"\\medskip\n"
        )
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        f.write("\n".join(sections))


def write_collect_csv(plans: list[tuple[int, NodeResult, str]], path: str, annotator: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "plan_id", "history", "description",
            "consultant_quality", "consultant_scope_fit", "consultant_notes",
            "annotator", "annotator_feasibility", "annotator_scope_fit", "annotator_notes",
        ])
        w.writeheader()
        for pid, node, description in plans:
            w.writerow({
                "plan_id": pid,
                "history": " → ".join(node.history),
                "description": description,
                "consultant_quality": round(node.verdict.quality, 3),
                "consultant_scope_fit": round(node.verdict.scope_fit, 3),
                "consultant_notes": node.verdict.notes,
                "annotator": annotator,
                "annotator_feasibility": "",   # to be filled in
                "annotator_scope_fit": "",
                "annotator_notes": "",
            })


# ── main ─────────────────────────────────────────────────────────────────────

async def main_async(args):
    spec = load_spec(args.assignment)
    annotator = args.annotator
    slug = f"{args.assignment}_{annotator}"

    handout = args.handout or f"outputs/calibration/{slug}_handout.md"
    collect  = args.collect  or f"outputs/calibration/{slug}_ratings.csv"
    trace    = args.trace    or f"outputs/calibration/{slug}_trace.json"

    pool = ConsultantPool(spec, n_rooms=args.rooms)
    RECORDER.reset()

    print(f"=== Calibration run: {spec.title} ===")
    print(f"    Annotator: {annotator}\n")
    root = await explore(
        spec, pool, history=[],
        max_depth=args.depth, max_options=args.options,
    )

    sampled = sample_plans(root, n_per_branch=args.per_branch)
    print(f"\nSampled {len(sampled)} plans across {len(root.branches)} root branches.")

    print("Generating plain-English descriptions...")
    descriptions = await asyncio.gather(*(describe_plan(spec, n.history) for n in sampled))

    plans = [(i + 1, node, desc) for i, (node, desc) in enumerate(zip(sampled, descriptions))]

    write_handout(plans, handout, spec, annotator)
    print(f"Handout written to {handout}")

    write_collect_csv(plans, collect, annotator)
    print(f"Collection CSV written to {collect}")

    os.makedirs(os.path.dirname(trace) or ".", exist_ok=True)
    record = {
        "assignment": spec.title,
        "annotator": annotator,
        "config": {"rooms": args.rooms, "depth": args.depth, "options": args.options},
        "metrics": RECORDER.summary(),
        "root": root.to_jsonable(),
        "sampled_plan_ids": [p[0] for p in plans],
    }
    with open(trace, "w") as f:
        json.dump(record, f, indent=2)
    print(f"Trace written to {trace}")

    print(f"\n=== Plans for {annotator} to rate ===")
    for pid, node, desc in plans:
        print(f"\nPlan {pid}: {' → '.join(node.history)}")
        print(f"  {desc}")
        print(f"  [consultant q={node.verdict.quality:.2f} scope={node.verdict.scope_fit:.2f}]")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--assignment", default="calibration",
                   help="assignment spec name (default: calibration)")
    p.add_argument("--annotator", default="anand",
                   help="annotator name used in filenames and CSV (default: anand)")
    p.add_argument("--rooms", type=int, default=3)
    p.add_argument("--depth", type=int, default=2)
    p.add_argument("--options", type=int, default=3)
    p.add_argument("--per-branch", type=int, default=2,
                   help="leaves to sample per root branch (default 2: best + worst)")
    p.add_argument("--handout", default=None, help="override handout path")
    p.add_argument("--collect", default=None, help="override ratings CSV path")
    p.add_argument("--trace", default=None, help="override trace path")
    return p.parse_args()


if __name__ == "__main__":
    asyncio.run(main_async(parse_args()))
