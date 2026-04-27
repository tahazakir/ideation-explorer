# Failure log

Each entry uses the rubric template:
`failure_id, date, version_tested, what_triggered_the_problem, what_happened, severity, fix_attempted, current_status`.

---

## F1 — Confident recommendation under near-tied root options

- **failure_id**: F1
- **date**: 2026-04-21
- **version_tested**: v0.2 (after step 2: assignments + executor stub)
- **what_triggered_the_problem**: Run `ideation_explorer.main --assignment dummy --rooms 2 --depth 3 --options 3` (see GOV-1). Same shape also reproduced on lit_review and multi_agent runs.
- **what_happened**: All three root options came back at qualities `0.752 / 0.744 / 0.759`, a margin of 0.014. The system reported a single "RECOMMENDED FIRST DECISION" with no signal that the three options were essentially indistinguishable. A reviewer following the recommendation would attribute false weight to a coin-flip decision.
- **severity**: medium. The system is functioning as designed but communicates more confidence than the underlying evidence supports. This is a governance/trust failure rather than a correctness failure.
- **fix_attempted**: v0.3 added confidence assessment in `main.py:assess_confidence`. The aggregator now also returns `quality_stddev` across child branches, and the pool-level `Verdict` carries a `budget_exhausted` flag. CLI flag `--min-margin` (default 0.05) gates whether the system commits to a recommendation. When the top-two margin falls below the threshold, the run prints `LOW CONFIDENCE -- recommendation withheld`, the recommended-plan JSON is not written, and the trace records `advisory.refused = true` with the reason.
- **current_status**: Resolved on the dummy/web_app run (margin 0.014 < 0.05 → withheld). The `--min-margin` threshold is a tunable; teams that want raw output can pass `--min-margin 0.0`.
- **evidence**: [outputs/sample_runs/dummy.json](../outputs/sample_runs/dummy.json), [outputs/sample_runs/lit_review.json](../outputs/sample_runs/lit_review.json)

---

## F2 — Confident plan from an under-specified assignment

- **failure_id**: F2
- **date**: 2026-04-21
- **version_tested**: v0.2
- **what_triggered_the_problem**: Run on the deliberately vague spec (GOV-2: `Make something cool with AI`, two trivial constraints). Designed to stress the system: when the brief contains no real constraints, every option looks roughly viable to the consultant.
- **what_happened**: 27 leaf consultations produced root qualities `0.629 / 0.692 / 0.693` — three completely different project families (creative generator vs. interactive app vs. research analysis) clustered within 0.064. The system still emitted a confident-looking 3-step plan ("Analysis or research project / Public datasets / Environmental insights") that a downstream executor would have committed real effort to. Estimated days = 11.15 of 14 available (83%) — the system also chose a near-deadline plan from a vague brief, which is the worst time to overcommit.
- **severity**: high. Specifically the failure mode the rubric's governance category targets: the system ploughs through ambiguity instead of surfacing it.
- **fix_attempted**: v0.3 added the `--min-margin` gate. v0.5 added a `min_margin` field to `AssignmentSpec` so each spec can declare its own threshold without requiring users to pass a flag. `vague.py` sets `min_margin=0.08`. `main.py` and `dashboard.py` take `max(cli_min_margin, spec.min_margin)`, so the vague spec automatically uses the tighter threshold.
- **current_status**: Resolved in v0.5. Running the vague assignment at default CLI settings now correctly fires the gate: margin 0.064 < spec threshold 0.08 → `LOW CONFIDENCE -- recommendation withheld`.
- **evidence**: [outputs/sample_runs/vague.json](../outputs/sample_runs/vague.json)

---

## F3 — Unbounded consultant cost on deep/wide trees

- **failure_id**: F3
- **date**: 2026-04-21
- **version_tested**: v0.2
- **what_triggered_the_problem**: With `depth=3 options=3` the explorer always fans out to 27 leaf consultations, 13 option-generator calls, and ~14k input + 5k output tokens per run regardless of how trivial the assignment is. There was no cost ceiling: a misconfigured run could escalate (e.g. depth=4 options=4 = 256 leaves) without warning, and a malformed option generator that returned more options than requested would compound the blowup.
- **what_happened**: No production incident, but a clear cost-governance gap. The web_app run (SYS-1) burned 40 LLM calls / 19k tokens for a 7-day brief; that's fine, but the system offered no way to say "spend at most 10 consultations and tell me what you got."
- **severity**: medium. Predictable cost is a basic responsible-AI requirement, especially when the user is delegating ideation to an LLM that they don't fully observe.
- **fix_attempted**: v0.3 added `ConsultantPool(max_consultations=N)` and CLI `--max-consultations N`. When the cap is reached, additional leaf requests return a `Verdict` with `budget_exhausted=true, n_consultations=0`. The aggregator propagates the flag up the tree, and `assess_confidence` refuses to recommend any plan that depended on a budget-truncated subtree.
- **current_status**: Resolved. Demo command to reproduce the budget-hit + governance refusal:
  ```
  python -m ideation_explorer.main --assignment vague --rooms 3 --depth 3 --options 3 \
      --max-consultations 5 --min-margin 0.05 \
      --out outputs/sample_runs/vague_budget_capped.json --plan-out outputs/recommended_plans/vague_budget_capped.json
  ```
  Expected: pool reports `completed=5, refused=22`; root verdict has `budget_exhausted=true`; advisory withholds the plan; no `vague_budget_capped.json` plan file is written.
- **evidence**: Run the command above to produce the trace. Reproducer verified in smoke tests (see eval/version_notes.md v0.3).

---

## F4 — Consultant scope_fit miscalibrated without professor grounding

- **failure_id**: F4
- **date**: 2026-04-25
- **version_tested**: v0.3
- **what_triggered_the_problem**: Comparing consultant v1 scope_fit predictions against Professor Anand's ground-truth ratings on 4 calibration plans (CAL-1).
- **what_happened**: The generic consultant persona had no grounding in Anand's actual grading philosophy. It systematically over-estimated scope_fit for plans that were too easy (Plan 1: CLD on customer service, 0.85 predicted vs 0.60 actual) and under-estimated for plans that were appropriately complex (Plan 2: broad CLD on software devs, 0.55 predicted vs 0.80 actual). Most critically, it over-estimated the spreadsheet ABM (Plan 4: 0.71 vs 0.40) — failing to penalize the wrong tool choice. Mean absolute error across 4 plans: **0.25**.
- **severity**: high. The consultant is the system's primary evaluation signal. Miscalibrated scope_fit means the ideation tree recommends plans the professor would not endorse, defeating the system's core purpose.
- **fix_attempted**: v0.4 conducted a professor calibration session. 4 tree-sampled plans were shown to Anand using `calibrate.py` output. His ratings were collected and used to rewrite the consultant system prompt with: (a) explicit grading philosophy (tool choice is first-class; penalize too-easy as much as too-ambitious; emergence must be genuine); (b) 4 few-shot anchors with his scores and reasoning. `recalibrate.py` re-scored the original 4 plans through the calibrated prompt.
- **current_status**: Resolved. Generalization tested with leave-one-out cross-validation across 5 annotators and 5 assignment types (`holdout_eval.py`). Calibration improved all 5 profiles; average reduction 37% (Anand 28%, Taha/SE 23%, Taha/dataviz 42%, Samee 42%, Jason 48%). All 5 profiles had at least one 5/5 scope_fit plan generated by the ideation tree.
- **evidence**: [outputs/calibration/holdout_eval.csv](../outputs/calibration/holdout_eval.csv), [outputs/calibration/se_dining_taha_holdout.csv](../outputs/calibration/se_dining_taha_holdout.csv), [outputs/calibration/dataviz_journeys_taha_holdout.csv](../outputs/calibration/dataviz_journeys_taha_holdout.csv), [outputs/calibration/ml_course_project_samee_holdout.csv](../outputs/calibration/ml_course_project_samee_holdout.csv), [outputs/calibration/intro_ai_project_jason_holdout.csv](../outputs/calibration/intro_ai_project_jason_holdout.csv)
