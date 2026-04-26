"""Re-score the v1 calibration plans using the calibrated (v2) consultant.

Reads plan histories and Anand's ground-truth ratings from anand_ratings.csv,
runs each history through the current consultant prompt, and writes a comparison
table to outputs/calibration/calibration_comparison.csv.

Usage:
    python -m ideation_explorer.recalibrate
"""
import asyncio
import csv
import os

from .agents.consultant import consult
from .assignments.calibration import SPEC
from .recorder import RECORDER


async def main_async():
    RECORDER.reset()

    # Read v1 plans + Anand's ground truth
    rows = []
    with open("outputs/calibration/anand_ratings.csv") as f:
        for row in csv.DictReader(f):
            rows.append(row)

    print(f"Re-scoring {len(rows)} plans with calibrated consultant...\n")

    results = []
    for row in rows:
        history = [h.strip() for h in row["history"].split("→")]
        print(f"Plan {row['plan_id']}: {' → '.join(h[:40] for h in history)}")
        verdict = await consult(SPEC, history)
        print(f"  v1  quality={row['consultant_quality']}  scope_fit={row['consultant_scope_fit']}")
        print(f"  v2  quality={verdict.quality:.3f}          scope_fit={verdict.scope_fit:.3f}")
        print(f"  anand feasibility={row['anand_feasibility']}  scope_fit={row['anand_scope_fit']}")
        print(f"  notes: {verdict.notes[:120]}\n")
        results.append({
            "plan_id": row["plan_id"],
            "history": row["history"],
            "anand_feasibility": row["anand_feasibility"],
            "anand_scope_fit": row["anand_scope_fit"],
            "anand_notes": row["anand_notes"],
            "consultant_v1_quality": row["consultant_quality"],
            "consultant_v1_scope_fit": row["consultant_scope_fit"],
            "consultant_v2_quality": round(verdict.quality, 3),
            "consultant_v2_scope_fit": round(verdict.scope_fit, 3),
            "consultant_v2_notes": verdict.notes,
        })

    out = "outputs/calibration/calibration_comparison.csv"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results)
    print(f"Comparison written to {out}")

    # Print summary table
    print("\n=== Scope fit comparison (Anand /5 → 0-1, consultant 0-1) ===")
    print(f"{'Plan':<8} {'Anand':>8} {'v1':>8} {'v2':>8} {'v1 err':>8} {'v2 err':>8}")
    for r in results:
        anand = int(r["anand_scope_fit"]) / 5
        v1 = float(r["consultant_v1_scope_fit"])
        v2 = float(r["consultant_v2_scope_fit"])
        print(f"{r['plan_id']:<8} {anand:>8.2f} {v1:>8.2f} {v2:>8.2f} {abs(v1-anand):>8.2f} {abs(v2-anand):>8.2f}")

    errs_v1 = [abs(int(r["anand_scope_fit"])/5 - float(r["consultant_v1_scope_fit"])) for r in results]
    errs_v2 = [abs(int(r["anand_scope_fit"])/5 - float(r["consultant_v2_scope_fit"])) for r in results]
    print(f"{'MAE':<8} {'':>8} {sum(errs_v1)/len(errs_v1):>8.2f} {sum(errs_v2)/len(errs_v2):>8.2f}")

    print(f"\nLLM calls: {RECORDER.summary()['total_calls']}  "
          f"tokens: {RECORDER.summary()['total_input_tokens']} in / "
          f"{RECORDER.summary()['total_output_tokens']} out")


if __name__ == "__main__":
    asyncio.run(main_async())
