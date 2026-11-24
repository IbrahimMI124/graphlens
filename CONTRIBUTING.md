# Contributing to the AID 851 KGC study

This repository compares embedding-based completion with AnyBURL rule-based
completion. Scientific validity and traceable evidence take priority over a
larger score or an unqualified claim.

## Before changing an experiment

- Read `docs/METHODOLOGY.md`, `docs/STATUS.md`, and the report for the result you
  plan to modify.
- Keep official train, validation, test, and verified-negative files in their
  separate roles. Never add verified negatives as graph edges.
- Do not tune hyperparameters or thresholds on test outcomes. Use validation
  data for selection and preserve test outcomes for evaluation.
- Keep exploratory hypotheses distinct from measured results. Never replace an
  incomplete run with a partial checkpoint or a smoke-test score.
- Give each intervention a new output directory and record its configuration,
  source split hashes, seeds, and completion status.
- Ask the project lead before starting a long run or using a shared compute
  resource. The previously configured SSH target `work` is off-limits.

## Local checks

Use Python 3.11 or 3.12 and follow `docs/INSTALL.md`. CPU is supported. With the
official CoDEx-S files and real AnyBURL/PyClause dependencies installed:

```bash
export PYSTOW_HOME=/tmp/kgc-pystow
export PYKEEN_HOME=/tmp/kgc-pykeen
export KGC_DATA_S=data/codex-s
export KGC_ANYBURL_JAR=vendor/AnyBURL-23-1x.jar
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
python -m pytest -q
```

Missing external data or backends may cause their integration tests to skip;
report those skips explicitly. Keep local environments, generated runs, model
checkpoints, and large mined catalogs out of commits. Commit code, configurations,
tests, concise report artifacts, and provenance metadata needed to review a
change.

## Research changes

For new analyses, state the intervention, comparison group, outcome, sample
size, and known confounds. Keep query-level results paired across conditions,
cluster head/tail queries from the same triple, and distinguish rule abstention
from a negative judgment. Do not describe correlations as causal mechanisms.
