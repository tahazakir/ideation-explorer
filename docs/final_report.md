# Final Report — Ideation Explorer

**Team**: Mohammad Taha Zakir and Jason Liu
**Track**: A
**Phase**: 3
**Date**: 2026-04-26

---

## 1. Problem and user

Open-ended assignments — research projects, ML notebooks, web apps,
literature reviews, multi-agent systems — give a student a brief and a
deadline but leave most of the design space to them. The hard part is
not execution; it is choosing *which* version of the project to commit
to. Bad early decisions compound and surface only days later.

**Target user**: a student or researcher facing an open-ended brief
who wants to compare multiple plausible approaches *before* burning
the deadline on one. Secondarily, an instructor who wants to see the
design space a student considered and why they made a particular
trade-off.

**The need**: a system that fans out across plausible decision paths,
evaluates each completed plan for feasibility, aggregates the evidence
back, and recommends a direction with calibrated confidence.

## 2. Architecture and design choices

The system implements **recursive fan-out / fan-in over a decision
tree**, with one bounded resource (the consultant pool) doing the
expensive work.

Roles:

- **ExplorerAgent** (`explorer.py`) — recursive coroutine. One per
  node visited. If options exist at this node, fans out one child per
  option and awaits all of them. If no options, queues a request with
  the consultant pool. Carries the full decision history forward.
- **OptionGeneratorAgent** (`agents/option_generator.py`) — given the
  spec and the history, proposes the next landmark decision and a
  short list of mutually exclusive options. Returns `[]` to terminate.
- **ConsultantAgent** (`agents/consultant.py`) — given the spec and a
  full plan history, returns a structured Verdict
  (`quality`, `est_days`, `notes`).
- **ConsultantPool** (`consultant_pool.py`) — `asyncio.Semaphore` of
  size N (the "simulation rooms") plus an optional cost ceiling
  (`max_consultations`). The only concurrency-bounded resource.
- **Aggregator** (`aggregate.py`) — pure function. Computes
  consultation-weighted mean quality and est_days, propagates the best
  child's notes up, computes stddev across child branches, and
  poison-propagates `budget_exhausted`.
- **ExecutionPlannerAgent** (`executor.py`) — single LLM call that consumes
  the recommended plan and emits an ordered task DAG. Demonstrates
  ideation → execution handoff.

Why this shape:

- **Actor / fork-join model** matches the natural recursion of
  exploring a decision tree. Coroutines are cheap, so we can have
  hundreds of concurrent explorers without managing threads.
- **Bounded pool, not bounded explorers** — explorers are essentially
  free; the cost is in consultant LLM calls. Putting the bound there
  exactly matches where the money is spent and gives natural
  backpressure when the cap is hit.
- **History-carrying probes** — each child gets `history + [option]`
  before spawning. This makes every node self-sufficient: the
  consultant sees the full plan, not just the leaf decision. Matches
  the actor-model "messages carry their context" property.
- **Aggregate at every antenna, not just the root** — by the time the
  root sees results it has consultation-weighted estimates per
  first-decision branch, ready to compare.

See [architecture_diagram.md](architecture_diagram.md) for the
component and information-flow views.

## 3. Implementation summary

- ~750 lines of Python under [ideation_explorer/](../ideation_explorer/),
  plus eval files and docs.
- Async throughout (`asyncio.gather` for fan-out, `asyncio.Semaphore`
  for the pool, `AsyncAnthropic` for the model).
- Default model: `claude-haiku-4-5-20251001`. Switchable via
  `ideation_explorer/llm.py`.
- Process-wide `RECORDER` captures every LLM call (role, tokens,
  duration, depth, ok/error). Dumped into the trace JSON.
- Five distinct assignment specs under `assignments/`, with one
  deliberately under-constrained (`vague`) to exercise the governance
  path.
- v0.3 added the governance hooks (cost cap, margin gate, budget-hit
  propagation) after the v0.2 evaluation surfaced F1/F2/F3.

## 4. Evaluation setup

The evaluation has three distinct tiers with different levels of rigor.

**Tier 1 — Annotator calibration (external ground truth)**

Five separate evaluations, each pairing a real grader with a specific assignment type. This tier is the primary source of external validity. The annotators are the actual instructors for these assignment types — Professor Anand grades the AI workforce modeling assignment; the three TAs (Taha, Samee, Jason) each graded a course they teach or have TAed. Their ratings were collected independently on printed handouts produced by `calibrate.py`, with no model output visible at rating time. The ratings were not used to select which plans to show — every plan sampled from the ideation tree was rated, including the weakest ones. This design prevents selection bias.

Critically, this evaluation is **not circular**. The annotators rated plans before seeing any consultant scores, and the consultant was never involved in grading the plans it evaluated. The LOO cross-validation then scored each plan with its own calibration anchor removed, so the model was always predicting on held-out ground truth it had never seen. The MAE numbers are therefore conservative estimates of generalization, not in-sample fit.

`calibrate.py` sampled the best and worst leaf per root branch, generated plain-English 2–3 sentence plan descriptions, and produced a printable handout. Each annotator rated plans on feasibility/5 and scope_fit/5 with one sentence of notes. Their grading philosophy and ratings were encoded as few-shot anchors in the consultant prompt; `holdout_eval.py` then re-scored each plan with that anchor removed.

| Case | Annotator | Role | Assignment | Plans | Method |
|---|---|---|---|---|---|
| CAL-1 | Professor Anand | Course instructor | AI workforce modeling | 4 | LOO cross-validation |
| CAL-2 | Taha | TA | Campus dining web app | 5 | LOO cross-validation |
| CAL-3 | Taha | TA | User journey dataviz | 4 | LOO cross-validation |
| CAL-4 | Samee | TA | Predictive ML pipeline | 4 | LOO cross-validation |
| CAL-5 | Jason | TA | Intro AI project | 4 | LOO cross-validation |

**Tier 2 — Governance boundary tests**

Three tests designed to trigger the system's safety properties rather than evaluate output quality.

| Case | Trigger | Expected behavior |
|---|---|---|
| GOV-1 | Near-tied root options (web_app, margin=0.014) | Governance gate withholds recommendation |
| GOV-2 | Under-specified brief (vague, margin=0.001) | Per-spec threshold (0.08) fires, withholds |
| GOV-3 | Budget cap hit (vague, --max-consultations 5) | budget_exhausted propagates, plan withheld |

**Tier 3 — System smoke tests (author-assessed)**

Two functional checks confirming the system runs end-to-end. These are not independent evaluations — outcomes reflect author judgment.

| Case | What it checks |
|---|---|
| SYS-1 | ml_notebook: hard constraint produces wide margin (0.100), sensible recommendation |
| SYS-2 | Executor handoff: recommended plan converts to 12-task DAG with deps and risk items |

Full per-case descriptions, expected vs. actual behavior, and outcomes are in
[test_cases.csv](../eval/test_cases.csv) and [evaluation_results.csv](../eval/evaluation_results.csv).

## 5. Results

**Calibration results (Tier 1)**

| Case | Annotator | Assignment | v1 MAE | LOO MAE | Δ MAE | Feasibility | Scope\_fit |
|---|---|---|---:|---:|---:|---|---|
| CAL-1 | Anand | AI workforce modeling | 0.25 | 0.18 | −28% | 5/5 | 5/5 |
| CAL-2 | Taha | Campus dining web app | 0.22 | 0.17 | −23% | 5/5 | 5/5 |
| CAL-3 | Taha | User journey dataviz | 0.18 | 0.11 | −42% | 5/5 | 5/5 |
| CAL-4 | Samee | Predictive ML pipeline | 0.17 | 0.10 | −42% | 3/5 | 5/5 |
| CAL-5 | Jason | Intro AI project | 0.23 | 0.12 | −48% | 5/5 | 5/5 |
| **Avg** | | | **0.21** | **0.14** | **−37%** | **4.6/5** | **5/5** |

Calibration improves predictions across all five annotator/assignment combinations. In every profile the ideation tree generated at least one plan rated 5/5 scope_fit by the annotator — meaning the system is surfacing ideas that real graders consider perfectly scoped. 4 out of 5 annotators also gave that same plan 5/5 feasibility (Anand, Taha ×2, Jason); Samee's best plan (NLP pipeline) received 5/5 scope_fit but 3/5 feasibility, reflecting that it is the right kind of project but carries execution risk.

**Governance boundary results (Tier 2)**

All three governance tests pass after their respective fixes. GOV-1 and GOV-2 were `pass_after_fix` (failures in v0.2/v0.3 that drove the governance work; confirmed passing in v0.3 and v0.5 respectively). GOV-3 passes cleanly: pool completed=5, refused=22, budget_exhausted propagated to root, plan withheld.

**System smoke test results (Tier 3 — author-assessed)**

SYS-1: ml_notebook returned the widest margin of any run (0.100), correctly preferring a simple CNN over ResNet-18 under the 30-minute Colab training budget. SYS-2: the execution planner converted the recommended plan to a 12-task DAG with correct prerequisite chains, 8.5h total, and 5 risk items in a single LLM call.

## 6. Failure analysis

Four failure cases documented in
[failure_log.md](../eval/failure_log.md):

- **F1 (medium severity)**: confident recommendation under near-tied
  root options. Reproduced on three independent assignments. **Fix**:
  v0.3 `assess_confidence` + `--min-margin` gate withholds the
  recommendation and labels the trace `LOW CONFIDENCE`. Resolved on
  C1 (margin 0.014 < 0.05).
- **F2 (high severity)**: confident plan from an under-specified
  brief. The system ploughed through ambiguity instead of surfacing
  it. **Fix**: same gate covers part of this; calibration of
  `--min-margin` to ~0.08 closes the rest. Open item in
  [version_notes.md](../eval/version_notes.md).
- **F3 (medium severity)**: unbounded consultant cost. **Fix**:
  `ConsultantPool(max_consultations)` cap + `budget_exhausted`
  propagation + advisory refusal when any subtree was truncated.
  Reproducer command in F3's failure log entry.
- **F4 (high severity)**: consultant scope_fit miscalibrated without
  professor grounding. The generic persona had no basis for Anand's
  actual preferences, producing a mean absolute error of 0.25 on
  scope_fit vs. ground truth. **Fix**: v0.4 professor calibration
  session (see §6a below). Holdout MAE dropped to 0.18 (28% reduction).

### 6a. Annotator calibration (v0.4 — C7)

The most significant iteration in the project. After observing that the
consultant's scope_fit predictions diverged sharply from real grading
preferences, we built a calibration pipeline and ran it for three
annotators across three distinct assignment types.

**Method**: `calibrate.py` runs the ideation explorer on a given
assignment, samples the best and worst leaf plan per root branch,
generates plain-English 2-3 sentence descriptions, and produces a
printable handout. Each annotator rated plans on feasibility/5 and
scope_fit/5 with one sentence of notes. Their grading philosophy and
ratings were encoded as few-shot anchors in the consultant prompt.
Generalization was tested with leave-one-out cross-validation
(`holdout_eval.py`): each plan was scored with its own anchor removed,
so the model never had access to the answer it was predicting.

**Annotator 1 — Professor Anand** (assignment: AI workforce modeling, 4 plans)

Key signals: tool choice is first-class (NetLogo > Python > Excel/VBA);
scope fit penalizes too-easy as much as too-ambitious; emergence must
be genuine, not hard-coded.

| Plan | Anand | v1 | LOO | v1 err | LOO err |
|---|---|---|---|---|---|
| CLD / customer service | 0.60 | 0.85 | 0.85 | 0.25 | 0.25 |
| CLD / software devs (broad) | 0.80 | 0.55 | 0.68 | 0.25 | 0.12 |
| ABM / NetLogo | 1.00 | 0.82 | 0.72 | 0.18 | 0.28 |
| ABM / spreadsheet | 0.40 | 0.71 | 0.35 | 0.31 | 0.05 |
| **MAE** | | | | **0.25** | **0.18** |

28% LOO MAE reduction. Best plan generated: ABM/NetLogo rated 5/5 feasibility and 5/5 scope_fit by Anand. Evidence: [outputs/calibration/holdout_eval.csv](../outputs/calibration/holdout_eval.csv).

**Annotator 2 — Taha (TA)** (assignment: campus dining web app, 5 plans)

Key signals: framework choice is primary (React/Vue > vanilla JS);
data integration is secondary (live/scraped > mocked); external API
dependency without fallback drops feasibility; real-time stand-out
features = gold standard.

| Plan | Taha | v1 | LOO | v1 err | LOO err |
|---|---|---|---|---|---|
| React + 3rd-party API | 0.60 | 0.68 | 0.80 | 0.08 | 0.20 |
| React + scraping | 0.80 | 0.75 | 0.60 | 0.05 | 0.20 |
| Vue + Firebase real-time | 1.00 | 0.78 | 0.72 | 0.22 | 0.28 |
| Vanilla JS + uncertain API | 0.40 | 0.75 | 0.25 | 0.35 | 0.15 |
| Vanilla JS + hardcoded | 0.40 | 0.78 | 0.40 | 0.38 | 0.00 |
| **MAE** | | | | **0.22** | **0.17** |

23% LOO MAE reduction. Best plan generated: Vue + Firebase real-time rated 5/5 feasibility and 5/5 scope_fit by Taha. Evidence: [outputs/calibration/se_dining_taha_holdout.csv](../outputs/calibration/se_dining_taha_holdout.csv).

**Annotator 3 — Taha (TA)** (assignment: user journey visualization, 4 plans)

Key signals: D3.js/Observable > Tableau/PowerBI; real datasets > synthetic;
interactivity differentiates; Sankey/funnel = good fit for journey flows;
sunburst/icicle = poor fit.

| Plan | Taha | v1 | LOO | v1 err | LOO err |
|---|---|---|---|---|---|
| Real data + Tableau | 0.80 | 0.68 | 0.72 | 0.12 | 0.08 |
| Real data + D3.js | 1.00 | 0.58 | 0.80 | 0.42 | 0.20 |
| Synthetic + Sankey/heatmap | 0.60 | 0.68 | 0.65 | 0.08 | 0.05 |
| Synthetic + funnel/sequence | 0.60 | 0.72 | 0.50 | 0.12 | 0.10 |
| **MAE** | | | | **0.18** | **0.11** |

42% LOO MAE reduction. Best plan generated: Real data + D3.js rated 5/5 feasibility and 5/5 scope_fit by Taha. Evidence: [outputs/calibration/dataviz_journeys_taha_holdout.csv](../outputs/calibration/dataviz_journeys_taha_holdout.csv).

**Annotator 4 — Samee (TA)** (assignment: predictive ML pipeline, 4 plans)

Key signals: PyTorch/TensorFlow required (scikit-learn-only = under-scoped); breadth across ML skills
matters (data cleaning + feature engineering + neural modeling); NLP = gold standard because it
exercises every pipeline stage; image-only CNN = partial match (framework correct, minimal data
cleaning); unsupervised plans = brief mismatch (no predictive evaluation on unseen data).

| Plan | Samee | v1 | LOO | v1 err | LOO err |
|---|---|---|---|---|---|
| Tabular + scikit-learn | 0.60 | 0.68 | 0.50 | 0.08 | 0.10 |
| NLP (TF-IDF vs RNN) | 1.00 | 0.75 | 0.80 | 0.25 | 0.20 |
| Image CNN + transfer learning | 0.60 | 0.78 | 0.65 | 0.18 | 0.05 |
| Unsupervised clustering | 0.40 | 0.58 | 0.35 | 0.18 | 0.05 |
| **MAE** | | | | **0.17** | **0.10** |

42% LOO MAE reduction. Best plan generated: NLP pipeline (TF-IDF vs RNN) rated 3/5 feasibility and 5/5 scope_fit by Samee. Evidence: [outputs/calibration/ml_course_project_samee_holdout.csv](../outputs/calibration/ml_course_project_samee_holdout.csv).

**Annotator 5 — Jason (TA)** (assignment: intro AI project, 4 plans)

Key signals: dual-skill depth is primary (theory + engineering both required); annotation burden
penalizes plans where data labeling is the main challenge; novel architectures (Tree-LSTM) are
respected for ambition and score high on scope_fit even when feasibility is uncertain; user-centered
applications with a clear AI component score well regardless of implementation difficulty.

| Plan | Jason | v1 | LOO | v1 err | LOO err |
|---|---|---|---|---|---|
| Hand PT assistant (YOLO-pose) | 1.00 | 0.75 | 0.78 | 0.25 | 0.22 |
| Pothole severity classifier | 0.60 | 0.72 | 0.65 | 0.12 | 0.05 |
| Tree-LSTM (sentiment/NLI) | 0.40 | 0.72 | 0.25 | 0.32 | 0.15 |
| Adaptive AAC board | 0.60 | 0.82 | 0.55 | 0.22 | 0.05 |
| **MAE** | | | | **0.23** | **0.12** |

48% LOO MAE reduction. Best plan generated: hand PT assistant (YOLO-pose) rated 5/5 feasibility and 5/5 scope_fit by Jason. Evidence: [outputs/calibration/intro_ai_project_jason_holdout.csv](../outputs/calibration/intro_ai_project_jason_holdout.csv).

**Cross-annotator summary**

| Annotator | Assignment | Plans | Best plan (scope) | v1 MAE | LOO MAE | Reduction |
|---|---|---|---|---|---|---|
| Anand (professor) | AI workforce modeling | 4 | ABM/NetLogo: 5/5 | 0.25 | 0.18 | 28% |
| Taha (TA) | Campus dining web app | 5 | Vue+Firebase realtime: 5/5 | 0.22 | 0.17 | 23% |
| Taha (TA) | User journey dataviz | 4 | Real data+D3.js: 5/5 | 0.18 | 0.11 | 42% |
| Samee (TA) | Predictive ML pipeline | 4 | NLP pipeline: 5/5 | 0.17 | 0.10 | 42% |
| Jason (TA) | Intro AI project | 4 | Hand PT assistant: 5/5 | 0.23 | 0.12 | 48% |
| **Average** | | | **5/5 profiles hit 5/5 scope** | **0.21** | **0.14** | **37%** |

Calibration improves predictions across all five annotator/assignment combinations. The dataviz and ML pipeline profiles generalized most cleanly (42%) because the grading signals are binary and transferable. The intro AI profile saw the largest improvement (48%) because the uncalibrated model systematically over-estimated scope_fit for plans that fall outside the deadline window. The SE dining and Anand profiles show moderate generalization; signals like "real-time stand-out feature = gold standard" and "too-easy domain" are specific enough to require their own anchor. In all five profiles the ideation tree generated at least one plan rated 5/5 scope_fit by the annotator.

## 7. Governance and safety reflection

Three concrete safety properties the v0.3 system holds:

1. **Cost ceiling**. `--max-consultations N` is a hard cap on
   consultant LLM spend per run. Once hit, further leaves return a
   synthetic budget-exhausted Verdict instead of an LLM call.
2. **Calibrated confidence**. The system never silently passes a
   coin-flip recommendation downstream. If the top-two root margin is
   below `--min-margin`, the recommended-plan JSON is not written and
   the trace records the reason. The plan-receiving executor is
   therefore protected from acting on noise.
3. **Auditable trail**. Every LLM call is logged with role, tokens,
   latency, and history depth. Every consultant verdict survives in
   the trace. A reviewer can reconstruct exactly why the system
   recommended what it did, which is the basic precondition for trust
   in an agentic system.

**Responsible use and academic integrity**

Ideation Explorer assists with the *planning* phase of an assignment, not the execution. The output is a recommended decision path and an ordered task list — not a finished submission. Several implications follow:

- **Appropriate use**: The system is appropriate when a student uses the recommended plan as a starting point and then does the work — choosing the direction is their decision, not an LLM's. It is not appropriate as a substitute for engaging with the design problem at all.
- **What the student must verify**: The recommended plan reflects a consultant calibrated on one professor's grading philosophy. The student should read the propagated feasibility notes, check that the recommended approach is actually available to them (tools, compute, time), and consciously decide to accept or override the recommendation before committing.
- **Human-in-the-loop checkpoint**: The execution planner's task DAG is explicitly framed as a checkpoint artifact, not a work order. The student reviews it before acting. The recommended-plan JSON is never silently handed to a downstream executor.
- **Misrepresentation boundary**: The system surfaces design options a student might not have considered. It does not produce written deliverables. Using the ideation output to inform your project direction is structurally the same as discussing options with a peer or TA; using the executor output as a project plan to submit verbatim is not.

Open governance work: deadline-utilization gate (refuse plans that
consume >80% of the deadline window), margin gate calibrated by
assignment style, and option-deduplication when the option generator
produces near-paraphrases of the same idea.

## 8. Lessons learned

- **The aggregator is the trust boundary**. Our first version
  overwrote consultant feasibility notes with a quality-summary
  string, which made the trace useless for human review. Preserving
  the best-leaf notes upward was a one-line change that made the
  whole system legible.
- **Bounded resources go on the resource, not on the workers**. Once
  we bounded the consultant pool with a semaphore, we stopped having
  to think about explorer concurrency at all.
- **Build the failure cases into the test set on purpose**. The
  `vague` assignment was added knowing it would fail, and that single
  case did more to motivate the governance work than any of the
  successful runs.
- **Confidence is a feature, not a flag**. Returning a "best" answer
  with no measure of how much better it was than the alternatives is
  the actual failure; the recommendation itself is downstream of that.

## 9. Future improvements / next steps

- **Calibrated `--min-margin`** that weights the raw gap by
  `quality_stddev` so the threshold adapts to assignment difficulty.
- **Deadline-utilization gate** that refuses plans consuming most of
  the available time on an under-specified brief.
- **Multi-agent executor**, replacing the single-shot execution planner with a
  real coder/writer/grader agent chain.
- **Memoization on canonical histories**, so two paths to the same
  effective plan share one consultant call. Important for true DAGs.
- **Streaming aggregation** at the root so the user can watch
  per-branch quality firm up in real time and cut the run early when
  a clear winner emerges.
- **Cross-model evaluation**: re-run all five cases with
  sonnet-4-6 and compare margins, scope_fit, and recommendation
  stability. Currently haiku-4-5 only.
- **Multi-professor calibration**: the system architecture already
  supports per-professor consultant profiles (swap the system prompt).
  Running `calibrate.py` for additional instructors would produce
  independent ground-truth samples and make the MAE result more
  robust than the current N=1 professor calibration in the live prompt.
