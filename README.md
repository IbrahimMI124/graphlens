# AID 851 — comparative knowledge graph completion

Research question: **which measurable graph conditions favor embeddings or relational rules?**

For a first-principles walkthrough of the study directions and current evidence,
see the [research directions and progress guide](docs/RESEARCH_DIRECTIONS.md).

See [current execution status](docs/STATUS.md) for completed runs and scope.
The CoDEx-S study includes the [validated baseline and frozen rule ablations](artifacts/next-phase/report.md),
the [five-condition cloud retraining comparison](artifacts/phase5/replicated-report/report.md),
and the [three independent matched graph draws](artifacts/removal-replication/report/report.md).
The [query evidence analysis](artifacts/evidence-advantage/report.md) compares
native ranking errors, rule-family disagreement, and a validation-trained
selector on the frozen CoDEx-S models.
The [final answer-blind comparison](artifacts/answer-blind-closeout/report.md)
tests whether rule evidence helps choose which model to trust before the
correct answer is known.
[Training-only evidence pilots](artifacts/evidence-intervention/report.md) and the
[last-proof protocol](docs/LAST_PROOF_PROTOCOL.md) document the checks used to
decide when a new perturbation warrants model fitting. The last-proof check
completed below its audit threshold. See the [verified evidence index](artifacts/closeout/verified-evidence.json).

The data, evaluation and analysis code uses real PyKEEN and AnyBURL/PyClause
backends. See the [repository audit](docs/AUDIT.md), the
[methodology](docs/METHODOLOGY.md), and [contribution guidance](CONTRIBUTING.md).
Reports distinguish development checks from benchmark runs and record native
rule ranking certification. CoDEx-S follow-up results are exploratory.

The completed exploratory CoDEx-S pilot uses three neural seeds, full official
evaluation splits, and a fixed mined rule model. Its report is at
[`artifacts/cpu-pilot-report/report.md`](artifacts/cpu-pilot-report/report.md).
These are ten-epoch/ten-second pilot budgets, not final benchmark settings;
symbolic ranking metrics retain their retrieval/censoring qualification.

For scalable runs, `anyburl.evidence_mode="references"` stores integer rule IDs
against each run's `rules/rule_catalog.json`. Selected case groundings are stored
separately; classification scores do not collect all groundings. A 256-entry
answer-blind prediction cache is enabled in supplied configurations, and its hits
and timing scope are recorded. Controlled experiments remove any pretrained-rule
setting and retrain both backends for each graph or rule-length variant.

The [HF compute setup](docs/HUGGINGFACE_JOBS.md) documents the cloud execution
environment used for the completed Phase 5 cohort. Training jobs require an explicit launch.

## Quick checks

From the repository root, with Python and NumPy available:

```bash
python -m unittest discover -s tests -v
python -m kgc validate --data tests/fixtures/codex-s-excerpt --excerpt
python -m kgc smoke --data tests/fixtures/codex-s-excerpt --excerpt --output artifacts/codex-s-smoke
python -m kgc report --runs artifacts --output artifacts/report
```

The fixture is the first 48 lines of each of the five **existing official** split
files, retrieved through the web tool. It is a source-provenanced loader smoke
fixture, not a new benchmark split. Its vocabulary is incomplete. It cannot be
used by comparative experiment commands. The synthetic graph is separately
identified under `tests/fixtures/synthetic`.

## Install and obtain the complete data

Follow [installation instructions](docs/INSTALL.md) for Python 3.11/3.12,
PyKEEN, Java, the real AnyBURL JAR, and PyClause.

With network access, `bash scripts/setup_cpu.sh` installs the CPU environment and
runs strict backend checks plus small smoke runs. It stops on failure and does
not launch full experiments. See `artifacts/backend-preflight.json` for the latest
readiness check.

```bash
python -m kgc doctor
python -m kgc download --data data/codex-s --size s --metadata
python -m kgc validate --data data/codex-s --size s
python -m kgc smoke --data data/codex-s --neural --output runs/neural-smoke
```

The downloader resolves an upstream revision to a commit and saves URLs and
checksums. Local full-dataset files without source metadata are explicitly marked
as having unverified provenance. For CoDEx-M, use `--data data/codex-m --size m`
on **each** applicable command. Identifiers retain their original Wikidata names;
one sorted training vocabulary is used across backends and perturbations.

## Baselines and validation selection

```bash
python -m kgc train --backend embedding --data data/codex-s --config configs/development.json --output runs/complex-dev
python -m kgc train --backend rules --data data/codex-s --config configs/development.json --output runs/anyburl-dev
```

`train` evaluates validation only. Change `embedding.model` to `RotatE` in a new
configuration to use the secondary baseline. Development defaults train one
epoch, mine for two seconds, and evaluate the first 16 positive triples per split.
These runs are labeled development, not final benchmark results.

For an explicitly requested full validation search, then fixed-config testing:

```bash
python -m kgc tune --data data/codex-s --config configs/full.json --candidates configs/validation_candidates.json --output runs/selection
python -m kgc run --data data/codex-s --config runs/selection/selected_config.json --output runs/baselines
```

These commands can be expensive. `full.json` uses three neural seeds and complete
evaluation. Its hyperparameters are starting settings, not claimed optimal or a
reproduction of published tuned results. The explicit candidate search selects
each backend by validation Hits@1, averaged over configured seeds; the symbolic
metric retains its retrieval qualification. No test score is used for selection.
No early stopping is implemented; epoch count is a fixed configurable budget.

## Experiments and reporting

```bash
python -m kgc analyze A --runs runs/baselines
python -m kgc analyze C --runs runs/baselines
python -m kgc analyze F --runs runs/baselines
python -m kgc experiment B --config configs/development.json --output runs/sparsity
python -m kgc experiment D --config configs/development.json --output runs/length
python -m kgc experiment E --config configs/development.json --output runs/noise
```

`experiment` saves a plan by default. Append `--execute --data data/codex-s` to
retrain both backends for the specified B/D/E variants. Choose `configs/full.json`
for final budgets and repeated perturbation seeds. A/C/F analyze completed paired
runs. D varies maximum **cyclic** body length; constant-rule length stays fixed.
E includes separate verified-negative classification and uncertain corruption
interventions. Failed variants stop execution and stay recorded.

```bash
python -m kgc report --runs runs --output artifacts/final-report
```

The report exports tables, scenario intervals, rule inventories, intervention
effects, complementarity, and deterministic first case studies from saved results.
Figures are PNG and PDF with sample counts and confidence intervals when real
runs exist. An empty report states that experiments are unexecuted.

## Layout and outputs

The shareable project files are the Python source, configs, documentation,
tests/fixtures, official CoDEx-S splits and selected report artifacts. Local
virtual environments, credentials, the project-context transcript, trained
checkpoints, generated run directories, and large mined rule inventories are
excluded from version control. Dataset provenance and reproducibility details
are documented alongside the reports; rerunning experiments requires the
dependencies in `docs/INSTALL.md` and the official AnyBURL download.

| Module | Responsibility |
| --- | --- |
| `kgc/data.py` | Official split loading, validation, ID mapping, train-only backend views |
| `kgc/backends/` | PyKEEN training and real AnyBURL Java/PyClause integration |
| `kgc/evaluation.py` | Masked queries, evaluator-only filtering, full versus censored ranks |
| `kgc/diagnostics.py` | Degrees, relation cardinality, empirical patterns, query comparisons |
| `kgc/perturbations.py` | Seeded removal/noise and split hygiene gate |
| `kgc/experiments.py`, `tuning.py` | Paired execution, A–F plans, validation-only selection |
| `kgc/statistics.py`, `robustness.py` | Paired and crossed-seed bootstrap analyses |
| `kgc/classification.py` | Hard negatives, validation calibration, explicit abstention |
| `kgc/reporting.py` | Reproducible Markdown, tables, plots, and prediction cases |

Each paired run stores configuration, versions, seed, graph/split hashes,
vocabulary, model checkpoint/configuration or rule file, runtimes, validation/test
query rows, scores, coverage, evidence, groundings, diagnostics CSV/JSON, and a
completion/failure manifest. Embedding top-10 candidates and target scores are
saved; rule candidate lists are preserved in full as returned by the backend.
Scores and calibrated probabilities occupy separate fields.

The integration tests can be enabled with `KGC_DATA_S`, `KGC_DATA_M`, and
`KGC_ANYBURL_JAR`; installed PyKEEN/PyTorch and PyClause enable their own tests.
Skipped external tests do not establish backend correctness.
