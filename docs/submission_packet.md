# Submission Packet — Ideation Explorer

**Course**: Agentic Technologies (Phase 3)
**Team**: Mohammad Taha Zakir and Jason Liu
**Track**: A (runnable system + traces + quantitative evaluation)
**Date**: 2026-04-26

---

## Project title

**Ideation Explorer** — a multi-agent system for calibrated plan recommendation on open-ended assignments.

---

## One-paragraph project summary

Ideation Explorer takes an open-ended assignment spec (title, description, constraints, deadline) and recursively fans out across the space of plausible design decisions. An `OptionGeneratorAgent` proposes the next landmark decision and a set of mutually exclusive options at each node; the system spawns one child explorer per option, each carrying the full decision history forward. At the leaves, a bounded `ConsultantPool` runs `ConsultantAgent` evaluations concurrently, returning structured verdicts (quality, scope_fit, feasibility notes). An `Aggregator` rolls verdicts back up the tree using consultation-weighted means, and a governance gate withholds the recommendation if the top-two margin is below a per-assignment threshold or if the consultant budget was exhausted. A final execution planner converts the recommended plan into an ordered task DAG. The system was evaluated across five annotator/assignment calibration pairs (external ground truth, LOO cross-validation), three governance boundary tests, and two author-assessed smoke tests.

---

## Repository link

> **[Paste GitHub repository URL here]**
>
> If not using GitHub: submit the compressed project folder alongside this PDF.

---

## 5-minute project video

> **https://drive.google.com/file/d/13AFDcPngodV_vhHk16BETSBbqrJtkUft/view?usp=sharing**

Video covers: problem and user (0:00), architecture (0:35), main workflow demo — AI workforce modeling live dashboard with 3-way tool-choice split (1:10), trace/coordination evidence (2:30), failure case — budget cap + governance refusal (3:00), evaluation and calibration results (3:45), execution planner handoff (4:30).

---

## Final report

Attached: **[final_report.pdf](final_report.pdf)**

Contents: problem and user, architecture and design choices, implementation summary, evaluation setup (3 tiers), results, failure analysis (F1–F4), governance and safety reflection, lessons learned, and future improvements.

---

## Architecture diagram

Attached: **[architecture_diagram.pdf](architecture_diagram.pdf)**

Two views:

1. **Component / coordination view** — how `main.py`, `ExplorerAgent`, `OptionGeneratorAgent`, `ConsultantPool`, `ConsultantAgent`, `Aggregator`, governance gate, and execution planner connect and exchange messages.
2. **Information-flow view (probe / antenna)** — how the recursive fan-out and fan-in of verdicts works across a depth-2 tree with 3 options at root.

---

## Screenshot index

| File | What it shows | Report section |
|---|---|---|
| `01_home.png` | CLI help — full flag surface | §3 Implementation |
| `02_main_flow.png` | Rich live dashboard mid-run: tree half-built, consulting nodes, pool progress bar | §2 Architecture |
| `03_evidence_view.png` | Completed result panel: per-option quality, margin, recommendation, propagated notes | §2 Aggregator; §5 Results |
| `04_history_or_state.png` | Trace JSON open in terminal — per-call role, tokens, latency | §7 Governance |
| `05_export_or_artifact.png` | Execution planner output: 12-task DAG with deps, time, risk items | §2 Executor; SYS-2 |
| `06_evaluation_view.png` | `eval/evaluation_results.csv` as a table — all 11 cases with outcomes | §4 Evaluation; §5 Results |
| `07_failure_case.png` | F3 budget cap: pool completed=5 refused=22, LOW CONFIDENCE withheld | §6 Failure analysis |

Screenshots are in `docs/screenshots/`. Reproduce commands are in `docs/screenshots/screenshot_index.md`.

---

## Evaluation summary

**Three evaluation tiers:**

**Tier 1 — Annotator calibration (external ground truth, 5 cases)**

Five graders (Professor Anand + 4 TAs) across five distinct assignment types rated ideation-tree plans on feasibility/5 and scope_fit/5. Leave-one-out cross-validation ensured the model never predicted an answer it had seen.

| Case | Annotator | Assignment | v1 MAE | LOO MAE | Reduction | Best scope_fit |
|---|---|---|---|---|---|---|
| CAL-1 | Anand | AI workforce modeling | 0.25 | 0.18 | 28% | 5/5 |
| CAL-2 | Taha | Campus dining web app | 0.22 | 0.17 | 23% | 5/5 |
| CAL-3 | Taha | User journey dataviz | 0.18 | 0.11 | 42% | 5/5 |
| CAL-4 | Samee | Predictive ML pipeline | 0.17 | 0.10 | 42% | 5/5 |
| CAL-5 | Jason | Intro AI project | 0.23 | 0.12 | 48% | 5/5 |
| **Avg** | | | **0.21** | **0.14** | **37%** | **5/5 all profiles** |

Every annotator found at least one generated plan rated 5/5 scope_fit; 4 out of 5 also gave 5/5 feasibility.

**Tier 2 — Governance boundary tests (3 cases)**

| Case | Trigger | Outcome |
|---|---|---|
| GOV-1 | Near-tied root options (margin=0.014) | Gate fires → withheld. pass_after_fix (v0.3) |
| GOV-2 | Vague spec (margin=0.001 < spec threshold 0.08) | Gate fires → withheld. pass_after_fix (v0.5) |
| GOV-3 | Budget cap (5 of 27 consultations used) | budget_exhausted propagated → withheld. pass |

**Tier 3 — System smoke tests (2 cases, author-assessed)**

| Case | Result |
|---|---|
| SYS-1 | ml_notebook: margin=0.100, simple CNN preferred over ResNet under Colab T4 budget |
| SYS-2 | Executor handoff: 12-task DAG, 8.5h, 5 risk items, 1 LLM call |

Full data: `eval/evaluation_results.csv`, `eval/test_cases.csv`.

---

## List of submitted files and folders

```
README.md                          top-level guide; setup + run instructions
AI_USAGE.md                        tools used, prompts, manual edits, verifications
requirements.txt                   Python dependencies (anthropic, rich, Pillow, etc.)
.env                               API key (not committed; reviewer must supply)

docs/
  submission_packet.pdf            ← this document
  final_report.pdf                 full report (also .md source)
  architecture_diagram.pdf         component + flow diagrams (also .md + PNG sources)
  project_summary.pdf              one-pager (also .md source)
  arch_component.png               mermaid render: component/coordination view
  arch_flow.png                    mermaid render: probe/antenna flow view
  screenshots/
    01_home.png                    CLI help screen
    02_main_flow.png               live dashboard mid-run
    03_evidence_view.png           completed result panel
    04_history_or_state.png        trace JSON audit trail
    05_export_or_artifact.png      execution planner task DAG
    06_evaluation_view.png         evaluation results table
    07_failure_case.png            F3 budget-cap governance refusal
    screenshot_index.md            captions + reproduce commands

ideation_explorer/
  main.py                          CLI entrypoint, governance gate
  explorer.py                      recursive probe/antenna coroutine
  consultant_pool.py               bounded semaphore + cost cap
  aggregate.py                     consultation-weighted aggregator
  executor.py                      execution planner agent
  llm.py, recorder.py              async Claude wrapper + call recorder
  types.py                         AssignmentSpec, Verdict, NodeResult, BranchReport
  agents/
    option_generator.py            OptionGeneratorAgent
    consultant.py                  ConsultantAgent (calibrated prompt)
  assignments/
    web_app.py, ml_notebook.py, lit_review.py, multi_agent.py, vague.py, calibration.py
  calibrate.py                     annotator calibration pipeline
  recalibrate.py                   before/after MAE scorer
  holdout_eval.py                  LOO cross-validation runner

eval/
  test_cases.csv                   11 cases (CAL-1–5, GOV-1–3, SYS-1–2)
  evaluation_results.csv           per-case metrics and outcomes
  failure_log.md                   F1–F4: trigger, what happened, fix, status
  version_notes.md                 v0.1 → v0.5 changelog

outputs/
  sample_runs/                     trace JSONs: calibration, dummy, ml_notebook, lit_review, multi_agent, vague, vague_budget_capped
  recommended_plans/               recommended plan JSONs passed to the execution planner
  exported_artifacts/              execution planner task DAG JSONs
  demo_outputs/                    calibration workfiles: handouts, ratings CSVs, annotator traces
  calibration/                     holdout CSVs for all 5 annotator LOO evaluations

media/
  demo_video_link.txt              shareable video URL
```

---

## Team member contributions

**Mohammad Taha Zakir**: system architecture, ExplorerAgent recursion, ConsultantPool, Aggregator, governance gate, annotator calibration pipeline (calibrate.py, recalibrate.py, holdout_eval.py), evaluation design, professor calibration session with Anand, final report.

**Jason Liu**: OptionGeneratorAgent, ConsultantAgent prompt design and calibration, assignment specs, executor/execution planner, evaluation runs, failure analysis documentation.
