"""Execution planner: consumes a recommended-plan JSON produced by main.py
and emits a concrete, ordered task list a downstream implementation
agent can carry out. This closes the loop:

    ideation explorer  -->  recommended_plan.json  -->  executor  -->  task DAG

Usage:
    python -m ideation_explorer.executor outputs/recommended_plans/dummy.json \
        --out outputs/exec_plans/dummy_tasks.json
"""
import argparse
import asyncio
import json
import os

from .llm import call_llm, extract_json
from .recorder import RECORDER

SYSTEM = """You are an execution planner. Given an assignment spec and a
sequence of landmark decisions already made by an upstream ideation
agent, produce a concrete ordered task list that an implementation
agent could carry out without further design work.

Each task should be specific (one sitting of work), name any artifact
it produces, and list its prerequisite task ids.

Respond with JSON only:
{
  "tasks": [
    {"id": 1, "title": "...", "deliverable": "...", "depends_on": []},
    ...
  ],
  "estimated_total_hours": <number>,
  "open_risks": ["...", "..."]
}
"""


async def plan_execution(plan_record: dict) -> dict:
    a = plan_record["assignment"]
    user = (
        f"ASSIGNMENT: {a['title']}\n"
        f"{a['description']}\n\n"
        f"CONSTRAINTS:\n- " + "\n- ".join(a['constraints']) + "\n"
        f"DEADLINE: {a['deadline_days']} days\n\n"
        f"LANDMARK DECISIONS (chosen by ideation explorer):\n"
        + "\n".join(f"  {i+1}. {s}" for i, s in enumerate(plan_record["recommended_plan"]))
        + f"\n\nIdeation expected quality: {plan_record.get('expected_quality')}\n"
        f"Ideation expected days:    {plan_record.get('expected_days')}\n\n"
        "Produce the execution task list."
    )
    raw = await call_llm(
        SYSTEM, user,
        agent_role="executor", history_depth=len(plan_record["recommended_plan"]),
        max_tokens=1500,
    )
    return extract_json(raw)


async def main_async(args):
    with open(args.plan_in) as f:
        plan_record = json.load(f)

    RECORDER.reset()
    print(f"=== Executor: {plan_record['assignment']['title']} ===")
    print("Plan handed off from ideation explorer:")
    for i, s in enumerate(plan_record["recommended_plan"], 1):
        print(f"  {i}. {s}")

    tasks = await plan_execution(plan_record)

    print("\n=== Execution task list ===")
    for t in tasks.get("tasks", []):
        deps = f"  (deps: {t['depends_on']})" if t.get("depends_on") else ""
        print(f"  [{t['id']}] {t['title']}{deps}")
        print(f"        -> {t['deliverable']}")
    print(f"\nEstimated total: {tasks.get('estimated_total_hours')} hours")
    if tasks.get("open_risks"):
        print("Open risks:")
        for r in tasks["open_risks"]:
            print(f"  - {r}")

    out = {
        "assignment": plan_record["assignment"],
        "recommended_plan": plan_record["recommended_plan"],
        "execution": tasks,
        "executor_metrics": RECORDER.summary(),
    }
    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w") as f:
            json.dump(out, f, indent=2)
        print(f"\nExecution plan written to {args.out}")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("plan_in", help="path to recommended_plan.json from main.py --plan-out")
    p.add_argument("--out", default=None, help="path to write the execution task list JSON")
    return p.parse_args()


if __name__ == "__main__":
    asyncio.run(main_async(parse_args()))
