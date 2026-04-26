# Version notes

Chronological log of system changes and the evaluation observations that
motivated each one.

---

## v0.1 — initial multi-agent skeleton

- Recursive `ExplorerAgent` (probe / antenna), `OptionGenerator` agent,
  `Consultant` agent, `ConsultantPool` (asyncio.Semaphore over the
  consultant role).
- Aggregator computed mean quality / mean est_days, but threw away
  consultant feasibility notes by overwriting them with a per-option
  summary string ("optA: q=0.82; optB: q=0.66").
- Single hard-coded dummy assignment.

**Observed problem**: After the first end-to-end run on the air-quality
spec, the per-branch notes shown at the root were `q=0.82; q=0.66`-style
quality summaries instead of the consultant's actual feasibility text.
Reviewers reading the trace had no qualitative reason for the choice.

**Action**: bumped to v0.2.

---

## v0.2 — useful trace + multi-assignment + executor

- `aggregate.py` now propagates the **best child branch's notes**
  upward, so feasibility commentary survives all the way to the root.
- Process-wide `RECORDER` captures every LLM call (role, model, tokens,
  latency, history depth, ok/error). Reset per run, dumped into the
  trace JSON.
- `BranchReport` now carries the full child `NodeResult`, enabling
  `NodeResult.best_path()` to walk the full chosen plan rather than
  just the first decision.
- CLI args (`--assignment --rooms --depth --options --out --plan-out`).
- Five assignment specs under `assignments/` (web_app, ml_notebook,
  lit_review, multi_agent, vague). The legacy `dummy` alias re-exports
  `web_app`.
- `executor.py` consumes a recommended-plan JSON and emits an ordered
  task list (single-shot LLM stub for handoff).

**Observed problems** (from the 5-case eval run, see [test_cases.csv](test_cases.csv)):
- **F1**: dummy / lit_review / multi_agent runs returned root options
  with margins of 0.014–0.052; system still emitted a confident-looking
  recommendation. False-confidence governance failure.
- **F2**: vague spec returned three completely different project
  families clustered within a 0.064 margin and consumed 11.15 of 14
  available days; system still recommended a concrete plan.
- **F3**: no cost ceiling; depth/options blowup is silent.

**Action**: bumped to v0.3.

---

## v0.3 — governance hooks (current)

- `Verdict` extended with `quality_stddev` (population stddev across an
  antenna's child branches) and `budget_exhausted: bool`.
- `aggregate.py` computes `quality_stddev` and propagates
  `budget_exhausted` upward (any branch budget-hit poisons the parent).
- `ConsultantPool` accepts `max_consultations`. When the cap is hit,
  additional leaves get back a `budget_exhausted=true` Verdict with
  `n_consultations=0` instead of an LLM call. Pool also tracks
  `refused`.
- `main.py:assess_confidence` computes the top-two margin at the root,
  combines it with `budget_exhausted`, and produces an advisory record.
  Below the `--min-margin` threshold (default 0.05), the system prints
  `LOW CONFIDENCE -- recommendation withheld`, omits the
  recommended-plan JSON, and records the reason in the trace.
- New CLI flags: `--max-consultations`, `--min-margin`.

**Verification**: smoke test in step 4 confirmed the gate fires on
narrow margin (0.020 < 0.05 → withheld), passes on wide margin
(0.16 → ok), and refuses on `budget_exhausted` even with wide margin.
Run-level verification on the existing 5 cases pending re-run with the
new defaults.

---

---

## v0.4 — professor calibration

**Observed problem** (C7, test_cases.csv): the generic consultant persona
had no grounding in Anand's actual preferences. Scope_fit MAE vs. ground
truth was 0.25 — largest error on Plan 1 (scope over-estimated, customer
service is too easy) and Plan 4 (scope over-estimated, spreadsheet is the
wrong tool).

**Action**:
- Built `calibrate.py`: runs the explorer on a simplified Anand-style
  brief, samples best + worst leaf per root branch, generates plain-English
  plan descriptions, and outputs a printable handout + blank CSV.
- Met with Professor Anand and collected feasibility/5 + scope_fit/5 + one
  sentence per plan for 4 representative plans.
- Updated `agents/consultant.py` system prompt with:
  - Anand's grading philosophy (tool choice as first-class signal; penalize
    too-easy as much as too-ambitious; emergence must be genuine not
    hard-coded).
  - 4 calibration anchors as few-shot examples with his scores and reasoning.
- Built `recalibrate.py`: re-scores the original 4 v1 plan histories through
  the calibrated consultant and computes before/after MAE.

**Result**: Generalization tested with leave-one-out cross-validation
(`holdout_eval.py`) across 3 annotators and 3 assignment types.
`calibrate.py` generalized to accept any `--assignment` and `--annotator`,
and `holdout_eval.py` accepts explicit grading philosophies keyed by
(assignment, annotator) for stronger signal than inferred philosophy.

| Annotator | Assignment | Best plan (scope) | v1 MAE | LOO MAE | Reduction |
|---|---|---|---|---|---|
| Anand | AI workforce modeling | ABM/NetLogo: 5/5 | 0.25 | 0.18 | 28% |
| Taha | Campus dining web app | Vue+Firebase: 5/5 | 0.22 | 0.17 | 23% |
| Taha | User journey dataviz | Real data+D3.js: 5/5 | 0.18 | 0.11 | 42% |
| Samee | Predictive ML pipeline | NLP pipeline: 5/5 | 0.17 | 0.10 | 42% |
| Jason | Intro AI project | Hand PT assistant: 5/5 | 0.23 | 0.12 | 48% |
| **Avg** | | **5/5 hit 5/5 scope** | **0.21** | **0.14** | **37%** |

**Evidence**: `outputs/calibration/holdout_eval.csv`,
`outputs/calibration/se_dining_taha_holdout.csv`,
`outputs/calibration/dataviz_journeys_taha_holdout.csv`.

---

## Open items (planned for v0.5+)

- Calibrate `--min-margin` per assignment style. F2 (vague) has margin
  0.064 which currently slips past the default 0.05 gate.
- Deadline-utilization gate: refuse plans consuming >80% of deadline window.
- Replace the executor stub with the real coder/writer/grader chain.
