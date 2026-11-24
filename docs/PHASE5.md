# Controlled graph-structure experiments

The graph-only audit is in
[`artifacts/phase5/validation/validation-report.md`](../artifacts/phase5/validation/validation-report.md).
It reconstructs all masks from original training data (removal seed 11, target
seed 101), checks all five saved graphs, and preserves the original entity/relation
vocabulary and evaluator positive filters. Global and query-endpoint typed walk
counts are exact directed relation-labelled walks, allowing repeated entities.
They are structural diagnostics, not counts of native rule groundings.
They count consistently forward-directed walks and exclude inverse-oriented rule
bodies, so they do not measure total rule-path availability.

The project motivation is to measure how each system changes under the same
structural intervention, then compare those changes. The suggested explanation
involving redundant relational evidence remains a hypothesis. Link-ranking
robustness and hard-negative discrimination answer different evaluation
questions. Numerical claims below refer to saved experiment artifacts, not to
hypotheses or discussion notes.

## Experimental contract

The primary design is saved before evaluating interventions in
`runs/phase5-90/protocol.json`. It uses the earlier validation-selected reciprocal
ComplEx recipe, 40-epoch ceiling and validation checkpoints 5/10/20/40. The planned
primary comparison gives every graph a fresh neural initialization and fresh
60-second Java AnyBURL invocation
(one worker, same maximum lengths, support threshold and zero-rule setting).
Original-graph control models are retrained; established checkpoints/catalogs do
not substitute for those controls. This first bounded run requests one neural
seed and one mining realization per graph. Three neural seeds and independent
mining replication remain a later resource-dependent extension.

Removal changes the number of directional examples and updates per epoch:
65 original versus 58 modified. A predeclared 2,320-update checkpoint and a
last-epoch checkpoint accompany the validation-selected result, without extra
training or test-based model selection. Equal updates do not imply identical
numbers of examples or graph passes; those counters are saved explicitly.

The secondary experiment reapplies the established frozen **general-rule** catalog
to all five evidence graphs. Its confidences/support stay fixed; native frequency
ties are recomputed from the evidence graph. This is inference-time evidence
removal, not retraining. It is not an additive decomposition of the primary effect,
because the fresh original inventory is an independent learned realization. Full
frozen-constant evaluation is deferred. The case collector supports both general
and constant-bearing families. Full frozen-evidence witness cases use general
rules only; primary fresh-model cases remain pending. Missing witness edges are
checked against the actual modified training graphs.

H1–H5 each have an intervention, control, measurement and confound list in the
saved protocol. In particular, targeted and random relation-matched graphs have
exactly equal relation totals but intentionally different endpoint/path patterns.
That controls relation mix, not every entity-specific regularity. CoDEx-S analyses
are exploratory because its test set has been inspected repeatedly. CoDEx-M is a
later replication dataset after freezing the method, not an automatic next run.

## Vocabulary correction

Global removal eliminates the only training P840 edge. PyClause's implicit
indexing rejected the old frozen rules with an unknown-relation error. The
corrected adapter registers the original native loader's entity/relation order
before loading modified positive edges. Empty relations and isolated entities
remain valid vocabulary tokens; no removed or held-out triple becomes an edge.
This also fixes internal-ID tie order across interventions while keeping native
confidence smoothing, weights, maxplus and frequency ties unchanged.

The older attempt and protocol are preserved under
`runs/phase5-90/*/attempts/frozen-implicit-vocabulary` and
`protocol.before-native-vocabulary-fix.json`. Neural settings and mining budgets
were unchanged. A real backend unit test verifies empty-relation inference and
an isolated entity's zero-rule prediction. A real-data smoke covers all five
graphs and exactly reproduces old original-graph predictions; see
`artifacts/phase5/native-vocabulary-verification.json`. The initial paired smoke
in `runs/phase5-smoke` predates this correction and is retained as an execution
check, not a clean structural-effect estimate.

## Resource limits and interruption

The attempted 40-epoch/60-second cohort was **resource-stopped** after a
one-worker Java run reached 87°C and subsequent large-catalog metadata processing
also triggered repeated cooling. The original ComplEx control finished all
40 epochs and all three checkpoint evaluations. Its epoch losses/validation
selection exactly reproduce the earlier seed-0 run. Fresh original mining
completed (320,347 rules), but its prediction application is incomplete; no
full-budget perturbed graph was trained. See `runs/phase5-90/resource-stop.json`.
The `run` command refuses to restart that directory automatically. Adequate
cooling or another compute environment needs to be planned before deliberately
resuming this workload. Changing mining budgets requires a separate cohort.

The corrected-index paired smoke at `runs/phase5-smoke-indexed` completed all six
neural/rule cells for original, targeted-local and relation-matched-control graphs.
It uses one epoch, two seconds of mining, and 32 identical directional queries
per condition. This differs from the vocabulary-only check in
`runs/phase5-vocabulary-smoke`, which covers eight directional queries on all five
graphs without training.
Its stricter pacing uses three-second breaks per half-second active interval,
70°C checks and a 55°C resume threshold. Very short mining can yield empty
inventories; these cells validate execution and abstention handling only.

Run one experiment process at a time. Threads, pacing and temperature checks are
configurable. Training checks temperature inside epochs; rule-metadata loading
also yields at bounded intervals. A software check threshold is not a guaranteed
hardware temperature ceiling between checks. Java mining is gated before/after
each bounded invocation, not suspended inside its wall-clock snapshot budget.
The JVM uses one active processor and the miner one worker.

Optimizer, scheduler, model, best state, Python/NumPy/Torch RNG states and counters
are atomically saved after each full epoch. Interrupted partial epochs are
discarded and replayed from the committed snapshot. Only complete models enter
the paired tables. Interrupted/failed manifests and mining attempts are retained;
partial Java mining restarts as a new invocation rather than a claimed exact
continuation. The interruption/resume unit test reproduces dropout-training losses
and weights exactly. Snapshots retain the latest committed epoch; archived
interruption checkpoints are preserved separately when needed.

Training time/CPU counters cover committed epochs and exclude validation/cooling.
Discarded partial-epoch work and previous-session cooling are not fully captured
in those counters. Native inference wall times may include cooling and metadata
loading. Do not interpret paced/unpaced timing differences as algorithmic speed.
The CLI catches SIGTERM and records an interrupted run. SIGKILL or a machine
shutdown cannot execute cleanup; the last atomic epoch remains resumable and a
stale running manifest must be checked against the actual process before resuming.

```bash
export MPLCONFIGDIR=/tmp/kgc-matplotlib
export PYSTOW_HOME=/tmp/kgc-pystow
export PYKEEN_HOME=/tmp/kgc-pykeen
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export KGC_COOLING_SECONDS=3 KGC_ACTIVE_SECONDS=0.5
export KGC_MAX_CPU_C=70 KGC_RESUME_CPU_C=55
export KGC_MAX_THERMAL_WAIT_SECONDS=180
export JAVA_TOOL_OPTIONS=-XX:ActiveProcessorCount=1
export KGC_DATA_S=data/codex-s KGC_ANYBURL_JAR=vendor/AnyBURL-23-1x.jar

.backend-venv/bin/python -m pytest -q
.backend-venv/bin/python -m kgc.research.structure audit --output artifacts/phase5/validation
# Existing complete smoke cells are checked/reused; use a new directory for a new realization.
.backend-venv/bin/python -m kgc.research.structure smoke --output runs/phase5-smoke-indexed
.backend-venv/bin/python -m kgc.research.structure frozen --output runs/phase5-90
# The full-budget directory is now resource-stopped; do not restart automatically.
.backend-venv/bin/python -m kgc.research.structure report --output runs/phase5-90
.backend-venv/bin/python -m kgc.research.structure frozen-cases --output runs/phase5-90
.backend-venv/bin/python -m kgc.research.structure report --output runs/phase5-smoke-indexed
.backend-venv/bin/python -m kgc.research.structure cases --output runs/phase5-smoke-indexed
```

For cohorts without a resource-stop marker, `run` resumes incomplete cells and
skips checksum-verified complete ones. It cannot change a started protocol. To request
three seeds or additional independent mining realizations, use `--seeds 0 1 2`
and `--rule-repetitions 2` with a **fresh output directory**, before observing
that cohort's outcomes. These flags are training seeds/miner counts, not new
perturbation draws; this prepared graph cohort has one removal/target draw.

## Reports and statistical interpretation

The [primary report](../artifacts/phase5/report/report.md) is in
`artifacts/phase5/report`; the corrected-index
[smoke report](../artifacts/phase5/smoke-indexed-report/report.md) is in
`artifacts/phase5/smoke-indexed-report`. The older
`artifacts/phase5/smoke-report` remains preserved. Outputs include overall/resource tables,
paired-effects and relative-gap intervals, general/constant/frozen sensitivity
plots, rule support/confidence distributions, query joins, exploratory original
degree/frequency/target strata, and sampled training-only witness cases.
Frozen candidate-support losses count query–candidate pairs that cease to be
generated. They do not count individual groundings or the miner's support
statistic. The full original-vocabulary equivalence check is saved in
`artifacts/phase5/native-vocabulary-full-original-verification.json`.
[Frozen witness cases](../artifacts/phase5/report/frozen-cases.md) and
`frozen-witnesses.csv` document independently verified
before/after native witnesses for the frozen evidence intervention. They do not
infer a neural response. Primary fresh-model cases require completed paired
fresh predictions and remain pending for the resource-stopped cohort.

Head/tail queries stay in the same original-triple bootstrap cluster. Neural
seeds are paired across graphs. Independently mined catalogs are resampled
independently by graph rather than paired by arbitrary realization IDs. A single
model/inventory gives conditional query uncertainty, not training or mining
stability. Seed×miner query joins are not treated as independent replications.
Shared entities, relations and masked inputs create additional graph dependence.

Graph selection, strata and any deployment-relevant features use original training
information only. Gold ranks, target degrees, paths to truth and winner/support
labels are evaluation diagnostics. Candidate masks check that frozen positive-body
support does not increase after deletions; violations block a clean missing-body
interpretation. Witness losses are sampled unless exhaustive frozen gold support
disappears. Surviving samples do not prove that no other grounding was lost.
Neural prediction changes are measured sensitivity, not invented mechanistic
explanations. Unsupported rule outcomes remain abstentions; exact full-universe
rule MRR remains unavailable.
