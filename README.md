# Ideation Explorer

A multi-agent system that helps a user pick a strong approach to an
open-ended assignment by recursively exploring the tree of landmark
decisions and aggregating consultant feedback up to the root.

- **Team**: Mohammad Taha Zakir and Jason Liu
- **Track**: A (runnable system + traces + quantitative evaluation)
- **Phase**: 3

## What it does

Given an assignment spec (title, description, constraints, deadline),
the system:

1. Spawns a recursive **explorer agent** at the root.
2. At each non-terminal node, an **option-generator agent** proposes
   the next landmark decision and its mutually exclusive options.
3. The explorer fans out one child per option, each carrying the full
   decision history accumulated to reach that node.
4. At terminal nodes, the explorer queues a request with a bounded
   **consultant pool** (a fixed number of "simulation rooms"). A
   **consultant agent** evaluates the full plan and returns a verdict
   (quality, est_days, feasibility notes).
5. Antennas wait for all children, aggregate verdicts (consultation-
   weighted mean + stddev), and propagate the best child's notes upward.
6. The root reports per-first-decision quality, recommends a full
   end-to-end plan, and (governance) refuses to recommend when
   confidence is too low or the cost ceiling was hit.
7. A separate **execution planner agent** consumes the recommended plan and
   emits an ordered task DAG, closing the ideation → execution loop.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
uv pip install -r requirements.txt
echo "CLAUDE_API_KEY=sk-ant-..." > .env   # or ANTHROPIC_API_KEY
```

## How to run

Pick one of the bundled assignments (`web_app`, `ml_notebook`,
`lit_review`, `multi_agent`, `vague`) or pass `dummy` for the legacy alias.

```bash
# Ideate
python -m ideation_explorer.main --assignment ml_notebook \
    --rooms 3 --depth 2 --options 2 \
    --out outputs/sample_runs/ml_notebook.json \
    --plan-out outputs/recommended_plans/ml_notebook.json

# Hand off to the executor
python -m ideation_explorer.executor outputs/recommended_plans/ml_notebook.json \
    --out outputs/exec_plans/ml_notebook_tasks.json
```

Governance flags:
- `--max-consultations N` hard cap on consultant LLM calls (cost ceiling).
- `--min-margin F` (default 0.05) refuse to recommend when the gap
  between the best and second-best root option is below F. Per-assignment
  minimums can be set in the spec (e.g. `vague` uses 0.08 automatically).

## Folder guide

```
ideation_explorer/         # the multi-agent system itself
  agents/                    option_generator.py, consultant.py
  assignments/               web_app, ml_notebook, lit_review, multi_agent, vague
  explorer.py                recursive coroutine (probe / antenna)
  consultant_pool.py         bounded semaphore + cost cap + budget-exhausted handling
  aggregate.py               consultation-weighted mean, stddev, notes propagation
  executor.py                execution planner agent (ideation → task DAG handoff)
  main.py                    CLI entrypoint, governance gate
  recorder.py, llm.py        instrumentation + async Claude wrapper

eval/                       test_cases.csv, evaluation_results.csv,
                            failure_log.md, version_notes.md
outputs/                    runs/, recommended_plans/, exec_plans/
docs/                       final_report.md, architecture_diagram.md,
                            project_summary.md, submission_packet.md, screenshots/
media/                      demo_video_link.txt
AI_USAGE.md                 tools used, prompts, manual edits, verifications
```

## Evaluation summary

Three evaluation tiers:

- **CAL-1 through CAL-5** — annotator calibration with external ground truth. Five
  graders (Professor Anand + 4 TAs) across five assignment types rated plans on
  feasibility/5 and scope_fit/5. Leave-one-out cross-validation. v1 MAE=0.21 →
  LOO MAE=0.14 (37% average reduction). All five profiles generated a 5/5 scope plan.
- **GOV-1 through GOV-3** — governance boundary tests: near-tied root options,
  under-specified brief, and budget cap. All three pass after their respective fixes.
- **SYS-1 and SYS-2** — author-assessed smoke tests: ml_notebook ideation run
  (margin=0.100, widest of all runs) and executor handoff (12-task DAG).

Full results in [eval/evaluation_results.csv](eval/evaluation_results.csv);
test scenarios in [eval/test_cases.csv](eval/test_cases.csv); failures and
iteration in [eval/failure_log.md](eval/failure_log.md).

## Outputs

Full LLM-call traces (one JSON per run, includes the entire decision
tree, every consultant verdict, per-call tokens and latency) live under
[outputs/sample_runs/](outputs/sample_runs/). Recommended-plan handoffs in
[outputs/recommended_plans/](outputs/recommended_plans/). Executor task
DAGs in [outputs/exec_plans/](outputs/exec_plans/).

## Known limitations

- The default `--min-margin 0.05` calibrated for tightly-constrained
  briefs slips past the vague-spec failure case (margin 0.064). See
  the F2 entry in the failure log.
- Option generator is bounded by `--max-options` and `--max-depth` but
  can still hallucinate redundant options on rich briefs.
- Executor is a single LLM call producing a task list; not yet wired to
  real coder/writer agents.
- The underlying graph is treated as a tree per exploration; true DAGs
  with multiple paths to the same node are not deduplicated.
