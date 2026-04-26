# Screenshot index

| screenshot_file | what_it_shows | why_it_matters | where_it_is_discussed_in_the_report |
|---|---|---|---|
| 01_home.png | CLI help output (`python -m ideation_explorer.main --help`) showing all flags: --assignment, --rooms, --depth, --options, --max-consultations, --min-margin, --out, --plan-out | Entry point for new users; shows the full parameter surface without reading source code | §3 Implementation summary |
| 02_main_flow.png | Rich live dashboard mid-run (ml_notebook, depth=3 options=2): decision tree half-built with yellow "consulting..." leaf nodes and pool progress bar at ~50% | Shows the fan-out / fan-in structure and real-time agentic behavior as it happens | §2 Architecture — ExplorerAgent, ConsultantPool |
| 03_evidence_view.png | Completed result panel: per-option quality scores, top-two margin, recommended first decision, and consultant feasibility notes propagated to the root | Shows the aggregated evidence a user actually acts on; feasibility notes are the "why" behind the recommendation | §2 Aggregator; §5 Results |
| 04_history_or_state.png | Trace JSON (outputs/sample_runs/ml_notebook.json) open in terminal — per-call log with role, tokens, latency, history depth for every LLM call in the run | Demonstrates the auditable trail property: every decision is logged and reconstructible | §7 Governance — auditable trail |
| 05_export_or_artifact.png | Executor task DAG output: 12 ordered tasks with dependencies, time estimates, and 5 risk items generated from the recommended ml_notebook plan | Shows the ideation-to-execution handoff; the DAG is the exported artifact a student would act on | §2 Executor stub; C6 in eval |
| 06_evaluation_view.png | eval/evaluation_results.csv rendered as a table — all 7 cases (C1-C7) with outcome, margin, and calibration MAE reduction | The primary evaluation summary view; shows pass/fail/fail_governance distribution and C7 calibration results at a glance | §4 Evaluation setup; §5 Results |

## Reproduce commands

```bash
# 01 — help screen
python -m ideation_explorer.main --help

# 02/03 — live dashboard (mid-run and completed)
python -m ideation_explorer.dashboard \
  --assignment ml_notebook --rooms 3 --depth 3 --options 2

# 04 — trace JSON
cat outputs/sample_runs/ml_notebook.json | python -m json.tool | head -80

# 05 — executor task DAG
python -m ideation_explorer.executor \
  --plan outputs/exported_artifacts/ml_notebook.json \
  --out outputs/exported_artifacts/ml_notebook_tasks.json

# 06 — evaluation CSV
column -t -s, eval/evaluation_results.csv
```
