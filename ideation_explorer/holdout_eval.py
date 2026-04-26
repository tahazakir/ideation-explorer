"""Leave-one-out cross-validation for any annotator calibration profile.

For each plan, removes its anchor from the prompt, scores it, and compares
to the annotator's ground-truth rating. Works for any assignment + annotator
combination produced by calibrate.py.

Outputs a comparison table and writes:
  outputs/calibration/{assignment}_{annotator}_holdout.csv

Usage:
    # Anand's original calibration (default)
    python -m ideation_explorer.holdout_eval \
        --assignment calibration --annotator anand \
        --ratings outputs/calibration/anand_ratings.csv

    # Taha's SE dining profile (after filling in the ratings CSV)
    python -m ideation_explorer.holdout_eval \
        --assignment se_dining --annotator taha

    # Taha's dataviz profile
    python -m ideation_explorer.holdout_eval \
        --assignment dataviz_journeys --annotator taha
"""
import argparse
import asyncio
import csv
import importlib
import os

from .llm import call_llm, extract_json
from .recorder import RECORDER
from .types import Verdict


# ── prompt builder ────────────────────────────────────────────────────────────

PHILOSOPHY_TEMPLATE = """You are evaluating a student's project plan as {annotator} would.

{annotator_upper}'S GRADING PHILOSOPHY (learned from calibration):
{philosophy}

CALIBRATION ANCHORS (use these to set your scale — one has been withheld for this evaluation):
"""

SCORING_INSTRUCTIONS = """
SCORING:
- quality: 0.0-1.0, overall strength of the plan against the assignment rubric
- scope_fit: 0.0-1.0, how well the challenge level fits the deadline
  (1.0 = perfectly challenging, 0.0 = too easy or tool mismatch)
- notes: 1-2 sentences of the most important concern, written as {annotator} would say it

Respond with JSON only:
{{"quality": 0.0, "scope_fit": 0.0, "notes": "..."}}
"""


def _build_anchor(row: dict) -> str:
    scope = float(row["annotator_scope_fit"]) / 5.0
    return (
        f"Plan {row['plan_id']} - {row['history'][:80]}:\n"
        f"  scope_fit={scope:.2f}\n"
        f"  Why: {row['annotator_notes']}\n"
    )


EXPLICIT_PHILOSOPHIES: dict[tuple[str, str], str] = {
    ("se_dining", "taha"): (
        "Framework choice is the primary signal: React or Vue = good industry skill transfer "
        "and appropriate scope for 14 days. Vanilla HTML/CSS/JS = too minimal — students miss "
        "component architecture, state management, and modern tooling, making it under-scoped.\n"
        "Data integration is the secondary signal: real-time sync or web scraping = high scope "
        "because it teaches live data handling. Mocked or hardcoded datasets = low scope because "
        "it sidesteps the core integration learning objective.\n"
        "External API dependency without a known fallback = feasibility risk (drops feasibility "
        "score), not just a scope concern — if the API does not exist the plan collapses.\n"
        "Gold standard: modern framework + live or scraped data + a stand-out feature such as "
        "real-time crowdsourced wait times. That combination is perfectly scoped for 14 days."
    ),
    ("dataviz_journeys", "taha"): (
        "Tool choice is the primary signal: D3.js or Observable = gold standard for a dataviz "
        "course — students learn custom, interactive, publication-ready output. Tableau or PowerBI "
        "= solid but lower ceiling, less transferable skill.\n"
        "Data source matters: real public datasets = higher scope (data wrangling is part of the "
        "challenge). Synthetic data = lower scope unless the generation itself is sophisticated "
        "and validated.\n"
        "Interactivity is a differentiator: static charts are adequate but interactive filtering "
        "or linked views make a 10-day project stand out.\n"
        "Visualization type choice: Sankey or funnel = good fit for user journeys. Sunburst or "
        "icicle tree = poor fit — compresses sequential flow into hierarchy, hard to read.\n"
        "Gold standard: real dataset + D3.js + at least one interactive sequential visualization."
    ),
    ("intro_ai_project", "jason"): (
        "Dual-skill depth is the primary signal: the best plans require both theoretical AI "
        "knowledge (model design, training, evaluation) AND practical engineering problem solving "
        "(real-time inference, system integration, UI). Plans that hit both score 5/5 scope_fit.\n"
        "30-day feasibility gates scope_fit: plans that are computationally infeasible or simply "
        "too much to implement within the deadline are poorly scoped regardless of how novel they "
        "are. An ambitious plan that cannot be finished is not well-scoped — score scope_fit low (1-2).\n"
        "Annotation burden is a scope penalty: plans where the primary challenge is manually "
        "labeling data rather than designing a model score lower (2-3) because the assignment "
        "learning objective is AI modeling, not data entry. Simple classifiers with no deep "
        "learning also score lower because students miss modern AI skills.\n"
        "LLM wrappers with unclear evaluation are moderate scope (3/5): strong user need but "
        "the AI component is thin (existing model, no fine-tuning) and success is hard to measure "
        "objectively, which limits how much AI depth the project demonstrates.\n"
        "Gold standard: real-time CV with a pre-trained model plus a second meaningful scenario "
        "(form feedback, severity classification) — combines deep AI knowledge with tractable "
        "engineering and a clear, demo-able deliverable within 30 days."
    ),
    ("ml_course_project", "samee"): (
        "Framework is the first-order signal: plans must use PyTorch (or TensorFlow) to be "
        "well-scoped — scikit-learn-only pipelines miss deep learning and modern tooling.\n"
        "Breadth across ML skills is the second-order signal: the assignment covers data "
        "cleaning, feature engineering, baseline comparison, and neural modeling. Plans that "
        "skip data cleaning (e.g., pure image CNN on MNIST) score lower on scope even if the "
        "framework is right, because they only exercise one dimension of the pipeline.\n"
        "Gold standard: NLP pipeline (text data + TF-IDF/Word2Vec baseline vs PyTorch RNN/embedding) "
        "because it requires preprocessing, feature engineering, two architectures, and error "
        "analysis — exercising every aspect of the 14-day brief.\n"
        "Image CNN is a partial match: PyTorch is correct but image datasets like MNIST/CIFAR-10 "
        "have minimal data cleaning, which is a gap. Score scope_fit moderate (not gold standard).\n"
        "Tabular + scikit-learn: feasible but under-scoped — no deep learning component.\n"
        "Unsupervised (clustering/anomaly detection): misaligned with the brief's explicit "
        "requirement for predictive classification/regression with baseline evaluation on unseen "
        "data. Scope_fit should be low (0.3-0.4 range) regardless of technical quality."
    ),
}


def _infer_philosophy(rows: list[dict], annotator: str, assignment: str) -> str:
    key = (assignment, annotator)
    if key in EXPLICIT_PHILOSOPHIES:
        return EXPLICIT_PHILOSOPHIES[key]
    high = max(rows, key=lambda r: int(r["annotator_scope_fit"]))
    low  = min(rows, key=lambda r: int(r["annotator_scope_fit"]))
    return (
        f"Based on ratings of {len(rows)} plans:\n"
        f"- Highest scope fit ({int(high['annotator_scope_fit'])}/5): {high['history'][:70]}\n"
        f"- Lowest scope fit  ({int(low['annotator_scope_fit'])}/5): {low['history'][:70]}\n"
        f"- Scope fit reflects how well the plan's difficulty matches the deadline."
    )


def build_system_prompt(rows: list[dict], held_out_id: str, annotator: str, assignment: str) -> str:
    philosophy = _infer_philosophy(rows, annotator, assignment)
    anchors = "".join(_build_anchor(r) for r in rows if r["plan_id"] != held_out_id)
    scoring = SCORING_INSTRUCTIONS.format(annotator=annotator)
    return (
        PHILOSOPHY_TEMPLATE.format(
            annotator=annotator,
            annotator_upper=annotator.upper(),
            philosophy=philosophy,
        )
        + anchors
        + scoring
    )


def load_spec(name: str):
    if name == "dummy":
        from .dummy_assignment import DUMMY
        return DUMMY
    mod = importlib.import_module(f"ideation_explorer.assignments.{name}")
    spec = getattr(mod, "SPEC", None)
    if spec is None:
        raise ValueError(f"module {mod.__name__} has no SPEC")
    return spec


async def score_plan(spec, history: list[str], held_out_id: str,
                     rows: list[dict], annotator: str, assignment: str) -> Verdict:
    system = build_system_prompt(rows, held_out_id, annotator, assignment)
    user = (
        f"ASSIGNMENT: {spec.title}\n"
        f"{spec.description}\n\n"
        f"CONSTRAINTS:\n- " + "\n- ".join(spec.constraints) + "\n"
        f"DEADLINE: {spec.deadline_days} days\n\n"
        f"PROPOSED PLAN:\n"
        + "\n".join(f"  {i+1}. {h}" for i, h in enumerate(history))
        + f"\n\nEvaluate this plan as {annotator} would."
    )
    raw = await call_llm(
        system, user,
        agent_role="consultant_holdout", history_depth=len(history), max_tokens=600,
    )
    data = extract_json(raw)
    return Verdict(
        quality=float(data.get("quality", 0.0)),
        scope_fit=float(data.get("scope_fit", 0.0)),
        notes=str(data.get("notes", "")),
        n_consultations=1,
    )


async def main_async(args):
    RECORDER.reset()
    spec = load_spec(args.assignment)
    annotator = args.annotator
    ratings_path = args.ratings or f"outputs/calibration/{args.assignment}_{annotator}_ratings.csv"
    out_path = f"outputs/calibration/{args.assignment}_{annotator}_holdout.csv"

    rows = []
    with open(ratings_path) as f:
        for row in csv.DictReader(f):
            if not row.get("annotator_scope_fit"):
                print(f"[skip] Plan {row['plan_id']} — no {annotator} rating yet")
                continue
            rows.append(row)

    if len(rows) < 2:
        print(f"Need at least 2 rated plans for LOO. Found {len(rows)}.")
        return

    print(f"Leave-one-out holdout: {spec.title}")
    print(f"Annotator: {annotator}  |  Rated plans: {len(rows)}\n")

    results = []
    for row in rows:
        plan_id = row["plan_id"]
        history = [h.strip() for h in row["history"].split("→")]
        gt_scope = float(row["annotator_scope_fit"]) / 5.0
        v1_scope = float(row["consultant_scope_fit"])

        print(f"Plan {plan_id} (held out): {' → '.join(h[:40] for h in history)}")
        verdict = await score_plan(spec, history, plan_id, rows, annotator, args.assignment)

        print(f"  {annotator} scope_fit : {gt_scope:.2f}")
        print(f"  uncalibrated        : {v1_scope:.2f}   err={abs(v1_scope - gt_scope):.2f}")
        print(f"  LOO holdout         : {verdict.scope_fit:.2f}   err={abs(verdict.scope_fit - gt_scope):.2f}")
        print(f"  notes: {verdict.notes[:120]}\n")

        results.append({
            "plan_id": plan_id,
            "annotator": annotator,
            "history": row["history"],
            "gt_scope_fit": round(gt_scope, 2),
            "v1_scope_fit": round(v1_scope, 3),
            "loo_scope_fit": round(verdict.scope_fit, 3),
            "v1_err": round(abs(v1_scope - gt_scope), 3),
            "loo_err": round(abs(verdict.scope_fit - gt_scope), 3),
            "loo_notes": verdict.notes,
        })

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results)
    print(f"Results written to {out_path}\n")

    print(f"=== LOO holdout summary: {annotator} / {args.assignment} ===")
    print(f"{'Plan':<8} {'GT':>6} {'v1':>6} {'LOO':>6} {'v1 err':>8} {'LOO err':>8}")
    for r in results:
        print(f"{r['plan_id']:<8} {r['gt_scope_fit']:>6.2f} {r['v1_scope_fit']:>6.2f} "
              f"{r['loo_scope_fit']:>6.2f} {r['v1_err']:>8.2f} {r['loo_err']:>8.2f}")

    mae_v1  = sum(r["v1_err"]  for r in results) / len(results)
    mae_loo = sum(r["loo_err"] for r in results) / len(results)
    print(f"{'MAE':<8} {'':>6} {'':>6} {'':>6} {mae_v1:>8.2f} {mae_loo:>8.2f}")

    reduction = (mae_v1 - mae_loo) / mae_v1 * 100 if mae_v1 > 0 else 0
    print(f"\n{reduction:.0f}% MAE reduction on held-out plans ({mae_v1:.2f} -> {mae_loo:.2f})")

    m = RECORDER.summary()
    print(f"LLM calls: {m['total_calls']}  "
          f"tokens: {m['total_input_tokens']} in / {m['total_output_tokens']} out")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--assignment", default="calibration",
                   help="assignment spec name (default: calibration)")
    p.add_argument("--annotator", default="anand",
                   help="annotator name (default: anand)")
    p.add_argument("--ratings", default=None,
                   help="path to filled-in ratings CSV "
                        "(default: outputs/calibration/{assignment}_{annotator}_ratings.csv)")
    return p.parse_args()


if __name__ == "__main__":
    asyncio.run(main_async(parse_args()))
