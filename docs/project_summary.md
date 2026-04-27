# Project summary (one-pager)

**Project**: Ideation Explorer
**Team**: Mohammad Taha Zakir and Jason Liu
**Track**: A

## What it is

A multi-agent system that helps a user pick a strong approach to an
open-ended assignment. It recursively explores the tree of landmark
decisions, has a bounded pool of "consultant" LLM agents evaluate
fully-specified plans at the leaves, aggregates feasibility verdicts
back up the tree, and recommends an end-to-end plan with calibrated
confidence — or refuses to recommend when the evidence is thin.

## Why it matters

Open-ended assignments fail not at the keyboard but at the design
table. Bad early decisions compound. The system makes the cost of
exploring multiple plausible plans cheap (they run concurrently), and
makes the comparison legible (every leaf gets a structured verdict
that aggregates upward).

## Architecture in one sentence

A recursive `ExplorerAgent` fans out one child per option from an
`OptionGeneratorAgent`, leaf nodes queue evaluation through a
semaphore-bounded `ConsultantPool` of `ConsultantAgent`s, and an
`Aggregator` rolls verdicts up the tree under a governance gate that
refuses low-confidence or budget-exhausted recommendations.

## Evidence at a glance

- 5 ideation cases + 1 executor handoff case + 1 governance reproducer.
- Per-case metrics: tree size, calls split by role, wall time, tokens,
  root quality, top-two margin, recommended decision, pass/fail.
- 3 documented failure cases driving the v0.1 → v0.3 changelog.
- Full LLM-call traces (one JSON per run) reproducible from a single
  `python -m ideation_explorer.main ...` command.

## Headline result

The system correctly discriminates when constraints bite hard (margin 0.100 on
the CIFAR-10 case) and *withholds its recommendation* when evidence is thin
(governance gate fires on both near-tied and vague-spec cases). Annotator
calibration across 5 graders reduced consultant scope_fit MAE from 0.21 to
0.14 (37%), with every grader rating at least one generated plan 5/5 scope_fit.

## Where to look

- **Run it**: [README.md](../README.md)
- **Architecture**: [architecture_diagram.md](architecture_diagram.md)
- **Full report**: [final_report.md](final_report.md)
- **Evaluation**: [eval/test_cases.csv](../eval/test_cases.csv),
  [eval/evaluation_results.csv](../eval/evaluation_results.csv)
- **Failures**: [eval/failure_log.md](../eval/failure_log.md)
- **Traces**: [outputs/sample_runs/](../outputs/sample_runs/)
