# Implementation and verification status

## Continuation: compute target off-limits; matrix pending

The user clarified that the configured SSH target named `work` is off-limits.
Do not connect to it, transfer files there, or run experiments there. No
alternate compute target has been authorized, and full-budget local training
remains deferred due to the previous heat issue. The prepared 115-file handoff
is local only; it has not been transferred or executed. See
[WORK_EXECUTION.md](WORK_EXECUTION.md) for the corrected boundary and
[the continuation report](../artifacts/phase5/remaining-report/report.md) for
scientific completion details.

The frozen-constant extension has a separate immutable declaration, preserving
the original protocol. Its original-graph evaluation completed all 3,656 queries:
every raw candidate list/order, score, rank and Hit exactly matches the earlier
constant-rule baseline (Hits@1 0.3205689). It uses 2,015 answer-blind masked-query
calls with 1,641 cache hits. Metadata-light application omits unused explanation
dictionaries; native scoring is unchanged and witness collection retains metadata.
The modified-graph continuation was stopped after a host reading reached 81°C;
partial results are explicitly interrupted and excluded. The remaining four
constant evidence conditions are pending.

New code supports family-qualified frozen diagnostics, a direct paired change in
the general-minus-constant gap, and winner-change/complementary-success case
selection. The prospective cohort declares three neural seeds and two independent
miners across all five graphs. It remains unexecuted pending an authorized,
thermally suitable compute destination. CoDEx-M and larger retention sweeps
remain later work.

The latest local correctness suite passes **100 tests, 1 skipped (CoDEx-M),
38 subtests**; the curated summary is at
`artifacts/phase5/github-test-summary.json`. The server launcher and archive
tests are included in that count. The local handoff manifest checked all 114
packaged inputs and pinned dependency versions. The training matrix remains
unexecuted; preparation is not completion. The previous 81-test run remains
archived separately.

## Latest: controlled graph-structure follow-up

See the [Phase 5 report](../artifacts/phase5/report/report.md),
[training-only graph audit](../artifacts/phase5/validation/validation-report.md),
and [bounded execution/resume guide](PHASE5.md). All five prepared graphs reproduce
exactly; held-out queries, candidate vocabularies and positive evaluator filters
remain fixed. The targeted and matched-control graphs have identical relation
totals but different degrees and typed-walk availability.

The frozen general-rule evidence intervention is complete on all 3,656 official
queries for each graph. Candidate supports decrease monotonically, while gold
generation coverage remains unchanged. Fresh-model cells have a separate
execution table; incomplete epoch snapshots are excluded from results. Follow-up
analyses remain exploratory and intervals with a single learned model condition
on that model rather than estimating training/mining variability.

The full-budget cohort was **resource-stopped after the CPU reached 87°C**.
The original ComplEx control completed all 40 epochs and validation-best,
fixed-update and last-epoch evaluation on all 3,656 queries. Fresh original
AnyBURL mining completed with 320,347 rules; its prediction application is
incomplete and is not a completed rule baseline. No perturbed primary graph
was trained. The directory blocks automatic restart; see
`runs/phase5-90/resource-stop.json`. Completed frozen evidence is reported
separately, with [training-only witness cases](../artifacts/phase5/report/frozen-cases.md).
Fresh-model primary cases and relative-robustness conclusions remain pending.

The native vocabulary correction preserves absent relations without inserting
removed or held-out edges. Original-graph ranks, scores and complete candidate
lists are exactly unchanged for all 3,656 queries. The earlier failed application
and protocol are archived. CPU runs are serial and paced with thermal checks;
full optimizer/RNG epoch snapshots support exact continuation. External termination
attempts are preserved and never labelled completed.

Latest enabled suite: **59 passed, 1 skipped, 5 subtests passed** in
`artifacts/phase5/verified-final-tests.xml`; only CoDEx-M is unavailable. The initial
one-epoch/two-second paired smoke predates the native index correction and is
retained as an execution check. The vocabulary-only verification at
`runs/phase5-vocabulary-smoke` covers all five graphs. The separate corrected-index
paired smoke at `runs/phase5-smoke-indexed` completed all six neural/rule cells
across the original, targeted-local and relation-matched-control graphs, using
one epoch, two seconds of mining and 32 directional queries per condition.
See its [smoke report](../artifacts/phase5/smoke-indexed-report/report.md).
Very short mining can produce empty inventories; these checks are not final
replicated intervention findings.

## Earlier: strengthened baseline and frozen-rule comparison

The next-phase study is documented in
[`artifacts/next-phase/report.md`](../artifacts/next-phase/report.md), with
reproduction commands in [NEXT_PHASE.md](NEXT_PHASE.md). All previous pilot
artifacts remain preserved. The three-recipe validation search selected reciprocal
ComplEx with per-triple cross entropy, 256 complex coordinates and at most 40
epochs. Three final seeds completed: mean test MRR **0.4535**, Hits@1 **0.3563**,
Hits@10 **0.6404**. This is a bounded port of the official recipe, not an exact
reproduction of historic LibKGE training, batching, tie policy or tuning budgets.
The strongest checkpoint is selected by validation and recorded with its hash,
original ID maps and load instructions in `artifacts/next-phase/strongest-complex.json`.

A frozen 60-second Java AnyBURL run produced 470,308 rules. Controlled physical
subsets preserve original expressions/statistics/scoring and hold all 467,989
constant implications fixed in the repaired length study. Standalone Hits@1:
constants **0.3206**, general variable-only rules **0.2749**, all rules **0.3408**.
Relational-only length caps 1/2/3 give **0.1214 / 0.2098 / 0.2749**; with fixed
constants these become **0.3400 / 0.3425 / 0.3408**. Length 3 versus 1 with fixed
constants gives 17 gains and 14 losses, delta 0.0008, paired 95% interval
[-0.0022, 0.0038]. These intervals condition on one learned inventory.

The audit identified native top-K early stopping even with nominal stopping
controls disabled. Old retrieved-list outcomes remain correctly censored. New
ablations use K greater than the entity universe and verify enlarged-limit
agreement. Certified rule Hits count abstentions as misses; exact full-universe
rule MRR remains null. Reflexive native-family inconsistencies are documented;
that family is absent from this catalog. Grounded-cyclic mining provenance cannot
be recovered from serialized rule text; native families and structural tags are
kept separate. Structural-proxy-only ablations remain inventory-level preparation.

The report includes paired seed/triple intervals, scenario sample sizes,
frequency-by-degree strata, relation-specific diagnostics and fourteen cases with
training-checked groundings. Latest full suite: **51 passed, 1 skipped, 5 subtests
passed** (`artifacts/next-phase/final-tests.xml`). Only complete CoDEx-M is skipped.

The user-requested thermal pause is archived. Partial seed 2 was preserved and
restarted from the original seed/recipe; its saved loss prefix reproduced exactly.
Completed runs were reused, and resumed jobs ran serially with one compute thread
and cooling breaks. Cache/pacing metadata qualify runtime comparisons.

At the close of that earlier stage, Phase 5 had five prepared 90%-retention
graph/control conditions, including an exact relation-count-matched control for
targeted removal; neither baseline had yet been retrained on them. Evaluator
filters retained original positive training facts under interventions and excluded
uncertain injected facts. Independent mining replication/convergence,
perturbed-model smoke runs, larger sparsity/noise studies, historic LibKGE
inheritance checks and CoDEx-M were pending. These statements describe that
earlier checkpoint; the latest Phase 5 status is above.

## Earlier: completed three-seed CPU pilot

The exploratory pilot is complete at `runs/codex-s-cpu-pilot-refined`: three
neural seeds, all 3,656 head/tail test queries per seed, and separate classification
on all official positive/verified-negative held-out examples. Validation selected
the settings, including an explicitly exploratory initialization follow-up.
Budgets were ten neural epochs and ten seconds for the mined rule snapshot.
The same checksum-verified symbolic model was held fixed across neural seeds;
intervals do not estimate mining randomness. Exact symbolic MRR is not reported.

The report at `artifacts/cpu-pilot-report/report.md` contains baseline comparisons,
scenario strata, paired bootstrap intervals, PNG/PDF figures, and illustrative
rules with checked training groundings. Its linked images and relation figure
were verified. See `artifacts/cpu-pilot-completion.json` and
`artifacts/cpu-pilot-protocol.json` for budgets, selection history, and limitations.
These pilot outcomes do not establish universal or final model-family superiority.

Grounding collection was separated from classification scoring to avoid retaining
all possible explanations in memory. Full query evidence uses integer references
to the learned-rule catalog; selected case groundings are sampled and labeled.
Default configurations now use this scalable evidence mode. Training can log
per-epoch loss, and interrupted paired runs are marked instead of appearing complete.

Experiment D's controlled maximum-cyclic-length sweep (1/2/3) is complete under
`runs/codex-s-rule-length-pilot-retry`, with a separate report at
`artifacts/rule-length-pilot-report/report.md`. Both baselines were retrained for
each length on unchanged official splits, and all paired neural metric differences
were zero. The first attempt was terminated before a trained model was saved and
remains marked interrupted. Latest verification: **42 passed, 1 skipped** (CoDEx-M).

The rule inventories expose an important confound: constant-rule counts were
111,292 / 49,808 / 558 even though their length cap stayed fixed at 1. The sweep
does not isolate a causal benefit or cost of longer path rules. It uses one seed
and one mining realization per setting; intervals describe query variation
conditional on those models, not mining stability. Independent mining repetitions
and a fixed-constant-inventory or path-only sensitivity analysis remain necessary.
Controlled sparsification/noise experiments and final-budget studies remain unexecuted.
Older stage notes below are historical.

## Current: complete CoDEx-S and paired development pipeline verified

All five official files are present and match the checksums saved for upstream
commit `3132e426c2a6b643b70bad679905a3a6270be440`. The loader verified
32,888/1,827/1,828 train/validation/test positives, 1,827/1,828 verified negatives,
2,034 entities, and 42 relations, with no split/ID/contradiction validation errors.
The latest suite has **36 passed, 1 skipped, 5 subtests passed**; only complete
CoDEx-M is unavailable. Backend preflight reports ready.

The paired development run at `runs/codex-s-development-check/seed-0` completed:
one ComplEx epoch, two seconds of real AnyBURL mining, 32 head/tail test query
rows per backend, validation-only calibration, and classification on all 3,656
test positive/verified-negative examples. Query diagnostics, rule evidence,
groundings, checkpoints, and runtimes were saved. Exact symbolic MRR remains
null because candidate lists may be truncated. This verifies execution, not
model quality at final training budgets. No full experiments were launched.

Current evidence: `artifacts/complete-environment-verification.json`,
`artifacts/complete-codex-s-validation.json`, `artifacts/backend-preflight.json`,
and `artifacts/complete-codex-s-tests.xml`. Older recovery notes below are historical.

## Recovery after the user's installation attempt

The CPU environment now has PyTorch, PyKEEN, PyClause, and the real AnyBURL JAR.
Actual backend integration tests passed for ComplEx, RotatE, PyClause query
application/groundings, and Java mining. Latest suite: **35 passed, 2 skipped,
5 subtests passed** (`artifacts/backend-tests.xml`). Only complete S/M dataset
integration checks remain skipped.

CoDEx-S currently has 32,888 training and 1,827 validation positives; test and
verified-negative files are missing. Source files have not yet been checked
against a pinned upstream revision. A one-epoch CPU ComplEx smoke ran on those
training edges and evaluated 16 validation queries. A two-second real AnyBURL
run mined 627 rules and evaluated 8 validation queries, preserving retrieved-list
qualification and null exact MRR. These are separate development smoke runs,
not a paired comparison or final scientific findings. Artifacts are under
`runs/installed-complex-smoke` and `runs/installed-anyburl-smoke`.

Fixed PyStow cache configuration and the verified AnyBURL JAR's normal exit-1
behavior (confirmed by its Learn bytecode). Only the known JAR fingerprint,
fresh parseable output, and successful completion log markers permit this code;
other nonzero exits still fail. Dataset downloads now support `--resume`, keep a
pinned revision/checksums across failures, preserve existing mismatched files,
show byte progress, and bound stalled transfers. Successful package imports skip
reinstallation. Resume only data downloading from a normal network-enabled
terminal with `.backend-venv/bin/python -u -m kgc download --data data/codex-s --resume`.

Earlier status entries below describe the initial blocked environment.

## Resumption on 2026-11-22

Retried actual setup and complete CoDEx-S download. Both failed because this
session's shell cannot resolve external hosts. Java remains available, but no
usable cached PyKEEN/PyClause/JAR or full dataset was found. There has still been
no real backend training or benchmark evaluation.

Added `scripts/setup_cpu.sh` for local CPU installation, revision recording,
strict readiness checks, real integration tests, and small smoke runs once
downloads are available. It was attempted here and stopped at the GitHub lookup;
its successful installation path is **not verified**. The standalone preflight
correctly returned a failing exit status for unavailable dependencies and data.

Evidence: `artifacts/backend-setup-attempt.log`,
`artifacts/backend-preflight.json`, `artifacts/resumption-2026-11-22.json`, and
`artifacts/tests-2026-11-22.xml`. The existing suite was rerun: **29 passed,
5 skipped, 3 subtests passed**. The skips are still the external integration
checks, not new completed validations.

## Framework status

This is the first working experimental framework, not a completed empirical study.
All artifacts distinguish implementation tests, real-data excerpts, and actual
benchmark runs. No expensive full training was launched.

| Area | Implemented | Verification / limitation |
| --- | --- | --- |
| Audit | Empty supplied workspace documented before edits | No existing implementation changed |
| Official loader | S/M paths, five splits, provenance, IDs and validation | S excerpt checked; full S/M unavailable |
| Evaluation | Both directions, masked inference, filtering, exact/censored metrics | Synthetic invariant tests pass |
| Neural baseline | PyKEEN ComplEx / RotatE, CPU, seeds, checkpoint, runtimes | External backend not installed; integration skipped |
| Symbolic baseline | Real Java mining plus PyClause QA/scoring/explanations | JAR/PyClause unavailable; API documented, not executed |
| Diagnostics | Degrees, cardinality, empirical patterns, evidence and errors | Known synthetic pattern tests pass |
| A–D | Analyses, random/local sparsification and cyclic-length plans | No benchmark runs; composition has explicit resource budget |
| E–F | Calibration, hard negatives, corruption, complementarity | Analysis tested with explicit synthetic test doubles; real runs absent |
| Statistics | Paired query/triple/seed and crossed intervention bootstrap | Reproducibility and known-difference tests pass |
| Reporting | Markdown, CSV, PNG/PDF export, cases and empty-result handling | Synthetic export/driver tests; status report generated |

Direct downloads failed DNS for the CoDEx commit API, PyPI, and the AnyBURL host.
An offline PyKEEN installation attempt also failed because the package was not
cached. `artifacts/external_dependencies.json` records these failures. No simpler
rule miner or hand-coded embedding replaces the requested backends.

The real-data smoke uses **240 official CoDEx-S excerpt triples**: 48 from each
original split, including the two verified-negative files. Sixteen masked test
queries were checked for mapping, direction, filtering, and degree consistency.
It did not train a model or measure predictive performance. Full original files
must be downloaded or supplied before a real benchmark smoke/train run.

The local analysis environment uses compatible cached Python 3.12 packages.
`artifacts/tests.xml`, `artifacts/verification.json`, and
`artifacts/analysis-versions.json` contain the final test evidence and versions.
Tests using model doubles are orchestration tests, not evidence that external
model APIs executed successfully.

Remaining verification work: install and pin backend dependencies, pass the real
Java/PyClause and neural integration tests (including groundings and ranks), run
full S/M loader tests, perform a validation search, then explicitly run the planned
baseline/intervention studies. Censored rule ranking, unknown tokens after
perturbation, Java random-seed control, and limited confounding adjustment must
remain reported even after installation succeeds. The code does not yet provide
complete symbolic rankings, causal identification, or final research findings.
