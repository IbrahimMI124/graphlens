# Installation and backend contract

## One-command resumption

Once GitHub, PyPI, the CPU wheel index, and the AnyBURL host are reachable, run:

```bash
bash scripts/setup_cpu.sh
```

This creates a local `.backend-venv`, resolves and records an immutable PyClause
commit, installs CPU dependencies, saves the resolved Python requirements, checks
the real JAR class, obtains full CoDEx-S, and performs strict import/data preflight.
Only then does it run integration tests, one CPU ComplEx epoch, and two seconds
of AnyBURL mining with validation-only prediction. It does not launch full studies.
Existing run directories are not overwritten by the rule training command.
The script stops on any failed step; a failed setup is not a verified integration.
The setup script uses `download --resume`: it verifies legacy partial files against
one pinned upstream revision and then records checksums for reuse. A mismatching
existing split is preserved and causes an error rather than being overwritten.
Downloads show byte progress and use socket/transfer time budgets. Package imports
are checked before installation so successful installations are reused.

The default environment-creation interpreter is `python3.11`. Override
`KGC_PYTHON` to use another supported interpreter, or
`KGC_BACKEND_ENV` for the backend environment location. The standalone check is:

```bash
.backend-venv/bin/python scripts/check_backend_environment.py
```

It exits nonzero for missing or broken imports, Java, the real JAR, or complete
data; the structured result is saved in `artifacts/backend-preflight.json`.

## Manual installation

Use Python 3.11 or 3.12 for the initial neural environment. The project core also
runs on the supplied Python 3.14. PyKEEN's stable API consulted was **1.11.1**;
the adapter pins that release. The complete neural dependency combination is
now passes small CPU integration tests here. Full benchmark execution still
requires complete CoDEx files and a fixed validation-selection protocol.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install -e '.[neural,analysis,test]'
```

CPU is the default in every supplied configuration. Choose the appropriate wheel
using the [official PyTorch installer](https://pytorch.org/get-started/locally/)
if the CPU wheel is unavailable. See also
[PyKEEN installation](https://pykeen.readthedocs.io/en/stable/installation.html).
Capture the resolved environment after successful backend integration:

```bash
python -m pip freeze > requirements-resolved.txt
python -m kgc doctor --output artifacts/backend-environment.json
```

`pyproject.toml` provides dependency constraints, not a claimed verified neural
lockfile. `artifacts/analysis-versions.json` captures the exact offline analysis
packages exercised here. Local `.analysis-venv` reads compatible cached packages
through a `.pth` file; it is an environment-specific verification convenience,
not a portable installer or a modification of the shared cache.

## Real AnyBURL

Obtain the JAR from the [official distribution](https://web.informatik.uni-mannheim.de/AnyBURL/).
The current documented release consulted was 23-1x. Java is required; if the JAR
and local Java are incompatible, use the source-build instructions on that page.
The adapter saves the actual JAR SHA256 and `learn.properties` for every run.

```bash
mkdir -p vendor
curl --fail --location https://web.informatik.uni-mannheim.de/AnyBURL/AnyBURL-23-1x.jar --output vendor/AnyBURL-23-1x.jar
java -version
python -m pip install 'git+https://github.com/symbolic-kg/PyClause.git'
```

PyClause requires a C++14 compiler and builds its `c_clause` extension. Its
[installation and query examples](https://github.com/symbolic-kg/PyClause)
document the `Loader`, `QAHandler`, and `PredictionHandler` interfaces used here.
Record its resolved Git commit (`pip freeze` / distribution direct URL metadata)
and pin that commit for all study runs. The current upstream adapter is
documented, but its compatibility remains unverified in this environment.

```bash
KGC_ANYBURL_JAR="$PWD/vendor/AnyBURL-23-1x.jar" python -m unittest discover -s tests -v
KGC_DATA_S="$PWD/data/codex-s" python -m unittest discover -s tests -v
```

Mining executes `de.unima.ki.anyburl.Learn` with a train-only file, a fixed snapshot
budget, and configurable cyclic length. Snapshots, logs, counts, expressions,
raw confidence/support, and hashes are retained. Mining is stochastic and
wall-clock driven: **Java seed control has not been verified**. Python seeds
control neural training and graph interventions, not the JAR's random generator.

Application loads only the training graph and learned rules into PyClause.
`QAHandler.calculate_answers` accepts `(known_entity, relation)` pairs and a
direction. It receives no held-out targets or filter graph. `PredictionHandler`
extracts explanations for the resulting candidate triples; every grounding edge
is checked against training edges. Triple classification deliberately scores
complete input triples, without labels or insertion into the graph.

Standard Java `Apply` is not used because its documented benchmark interface
loads held-out files for filtering. The common evaluator owns that filtering.
Native maxplus order is preserved, including its training-frequency tie policy;
scalar confidence cannot reconstruct its lexicographic rule ordering. Candidate
completeness is conservatively unverified even if fewer than K items return.
Missing output is abstention, not proof of falsity. Unknown tokens after a
perturbation are marked backend-unrepresentable, not evidence that no rule exists.

No custom miner stands in for AnyBURL. Missing Java/JAR/PyClause raises an explicit
error. The real Java mining and PyClause explanation tests must run before claiming
successful symbolic backend integration.
