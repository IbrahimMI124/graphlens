# Audited next-phase protocol

Previous reports and checkpoints are preserved. The new entry point is
`python -m kgc.research.runner`; editable installation also exposes `kgc-research`.
Use `.backend-venv/bin/python` with the existing backend environment. No hybrid
or GAT component is involved.

## Reproduction commands

Run from the repository root. Set writable cache locations:

```bash
export MPLCONFIGDIR=/tmp/kgc-matplotlib
export PYSTOW_HOME=/tmp/kgc-pystow
export PYKEEN_HOME=/tmp/kgc-pykeen
export KGC_DATA_S="$PWD/data/codex-s"
export KGC_ANYBURL_JAR="$PWD/vendor/AnyBURL-23-1x.jar"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
# Optional cooling breaks, used for the resumed laptop run:
export KGC_COOLING_SECONDS=3 KGC_ACTIVE_SECONDS=5
.backend-venv/bin/python -m pytest -q
.backend-venv/bin/python -m kgc.research.runner audit --output artifacts/next-phase/audit
.backend-venv/bin/python -m kgc.research.runner curves --output runs/next-phase-neural --protocol configs/next_phase_curves.json
.backend-venv/bin/python -m kgc.research.runner mine --output runs/next-phase-frozen --seconds 60
.backend-venv/bin/python -m kgc.research.runner ablate --output runs/next-phase-frozen --conditions general constants zero all --limit 8
.backend-venv/bin/python -m kgc.research.runner ablate --output runs/next-phase-frozen
.backend-venv/bin/python -m kgc.research.runner prepare-sparsity --output runs/next-phase-sparsity-prepared
.backend-venv/bin/python -m kgc.research.runner report --output artifacts/next-phase
.backend-venv/bin/python -m kgc.research.runner cases --output artifacts/next-phase
```

Mining, training, subset creation and sparsity preparation refuse to overwrite
existing artifacts. Complete search/ablation runs can be resumed; interrupted
training directories require a fresh output path rather than silently restarting
with a possibly different optimizer/RNG state. Reports regenerate from saved
results. Existing `runs/next-phase-*` are the executed study; use new paths for
new mining/training. The current report/case generator reads those canonical run
paths explicitly; copy/change the generator configuration for another cohort.

## Audit corrections and retrieval policy

The initial single-rule probe returned 150 candidates with `topk=10`. That was
insufficient to establish exhaustive candidate enumeration: a two-rule test and
real validation queries show later rules can be skipped. Prior pilot labels
remain correctly censored. `artifacts/next-phase/audit/preliminary-audit.json`
preserves the rejected inference; `audit.json` and the real-query contract files
document its correction. The interrupted topk100 attempt contains no completed
full-test result; its smoke outputs are kept under `smoke-topk100-preserved`.

New audited subsets use `topk = |entities| + 1` and verify equality against
`2*|entities|+1` on eight masked validation queries. Native branching and stopping
controls are disabled. The threshold exceeds every possible candidate count,
preventing candidate-count early stopping. This explicitly changes retrieval
completeness, while retaining native confidence smoothing, rule-type weights,
maxplus lexicographic ordering and training-frequency ties. Certified Hits are
for the rule system's exhaustive supported-candidate ranking, with abstentions
counted as misses; unsupported entities are not assigned an arbitrary full rank.
Exact full-universe rule MRR remains null.

Reflexive XX-family candidate generation disagreed with native triple scoring in
synthetic probes, with observations depending on preceding native calls.
Certification is disabled for inventories containing these families; none occur
in the frozen CoDEx-S catalog. No custom replacement implementation was added.
Zero-body Z rules are distinct from nonempty-body constant implications.
PredictionHandler does not support Z classification. Every new subset therefore
uses native **tail-query** maxplus scalar scores for classification, validation
calibration and unsupported-case abstention; legacy scores are unchanged.

## Neural recipe and interpretation

The old sLCWA recipe remains intact. The new training path uses PyKEEN's ComplEx
parameters and checked interaction, explicit reciprocal relation IDs, and
per-triple cross entropy over all original entities. PyKEEN grouped LCWA is not
assumed equivalent to per-triple LibKGE 1vsAll. Two reciprocal cross-entropy
learning rates and an sLCWA control are compared at fixed validation budgets;
test data is first scored after the selected recipe is written. The strongest
checkpoint means highest validation MRR, not highest test score.

The published 512-real-coordinate representation corresponds to 256 complex
coordinates. Dropout is applied to real/imaginary components. Initializer
scaling, random number streams, training batching, objective scaling and
validation cadence differ from historic LibKGE, so this is a documented port,
not an exact reproduction. The official configuration sets an empty regularizer
selector; CoDEx paper Table 11 confirms no regularization and CE loss. The new
recipes disable regularization explicitly. The old recipe
retains its default PyKEEN regularizer. Forty epochs and three recipes are a
bounded development comparison, not the published 400-epoch tuning budget.

The official setup pins LibKGE commit
`a9ecd249ec2d205df59287f64553a1536add4a43`. The official configuration and current
LibKGE implementation/defaults were inspected online; the historical source
could not be fetched. Historic inherited defaults remain unverified. Sources:

- [Official model configuration](https://github.com/tsafavi/codex/blob/master/models/link-prediction/codex-s/complex/config.yaml)
- [Official setup/version pin](https://github.com/tsafavi/codex/blob/master/libkge_setup.sh)
- [Current LibKGE defaults](https://github.com/uma-pi1/kge/blob/master/kge/config-default.yaml)
- [Current per-triple 1vsAll](https://github.com/uma-pi1/kge/blob/master/kge/job/train_1vsAll.py)
- [PyKEEN LCWA API](https://pykeen.readthedocs.io/en/stable/api/pykeen.training.LCWATrainingLoop.html)
- [Native PyClause defaults](https://github.com/symbolic-kg/PyClause/blob/master/clause/config-default.yaml)

## Frozen families, length and sparsity

One 60-second Java mining run supplies every subset. Original rule expressions,
statistics and order are preserved in physical files with source indices/hashes.
The fixed-constant length conditions retain identical constant-rule indices;
only native B rules with body lengths up to 1/2/3 change. Native family counts,
loaded counts, filtered rankings, candidate coverage and correct-answer coverage
are recorded independently. Identical subset hashes reuse results, not training.
Grounded-cyclic mining provenance is not encoded by serialized rules; explicit
structural tags are available without pretending to recover that provenance.

Intervals cluster head/tail by test triple. Neural/rule comparison additionally
resamples the three neural seeds. No interval estimates mining variation from
the one frozen catalog. Case studies use deterministic query-ID ordering and
native groundings checked against training positives; they are illustrative.

Prepared 90%-retention graphs include global random removal, relation-stratified
removal, targeted removal and an exact per-relation-count-matched random control.
Targets/masks use training information only. Both systems must be retrained
before reporting graph-intervention performance. Fresh AnyBURL rules and neural
parameters are required for each graph; prepared graphs do not constitute a
completed sparsity experiment. Larger matrices and mining repeats remain pending.

Evaluator filtering is fixed across graph interventions. `Dataset.with_graph`
now preserves the original positive training facts for the evaluator: removed
edges remain known positives, while injected uncertain edges do not become
filtering positives. Validation still excludes test positives for model selection.
This corrects future intervention semantics; all completed pilot and next-phase
model comparisons use the unchanged original graph and are unaffected. The
prepared cohort's `filter-protocol-correction.json` records this clarification.

## Resuming after the user-requested thermal pause

The original pause record is retained in `artifacts/next-phase/pause-state.json`.
Seeds 0/1 and seven rule conditions were already complete. The partial seed-2
directory is archived under `runs/next-phase-neural/interrupted`; its restart
uses the same seed, recipe and budgets from scratch. No optimizer/RNG continuation
is claimed. The incomplete rule-union directory is archived separately. Run one
job at a time on the laptop, with the optional cooling variables above; they
change duty cycle, not scores, random seeds or selection criteria. Training time
excludes epoch cooling; native prediction wall times can include cooling breaks.
Resource policies are saved, so paced and unpaced runtimes remain distinguishable.

Remaining ablations reuse raw, unfiltered masked tail-query outputs from the same
backend instance for classification when available. A real-backend unit test
checks cached/uncached raw scores and support flags are identical. Cache keys
contain only the known entity/relation/direction; they contain no answer, rank,
or positive/negative label. Validation-only calibration is unchanged. Timing
records identify this reuse; inference speed cannot be compared fairly without
accounting for caching and cooling. Completed classifications are preserved.
