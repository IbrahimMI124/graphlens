# AID 851: embedding–rule comparison

This report is generated from saved artifacts. Missing runs remain missing; smoke checks are not benchmark findings.

## Execution status


Evidence: `verification.json`

```json
{
  "checks": [
    "synthetic data/evaluation invariants",
    "train-only boundaries",
    "seeded perturbations",
    "pattern statistics",
    "paired and crossed bootstrap",
    "validation-only calibration with test doubles",
    "report orchestration with test doubles",
    "PNG/PDF exports",
    "official CoDEx-S excerpt loader/protocol smoke",
    "compileall"
  ],
  "command": "MPLCONFIGDIR=/tmp/kgc-matplotlib .analysis-venv/bin/python -m pytest -q --junitxml=artifacts/tests.xml",
  "full_training_launched": false,
  "junit_suite": {
    "errors": "0",
    "failures": "0",
    "hostname": "omarchyDumped",
    "name": "pytest",
    "skipped": "5",
    "tests": "37",
    "time": "4.806",
    "timestamp": "2026-11-19T20:25:23.618937+05:30"
  },
  "not_verified": [
    "real PyKEEN training",
    "real AnyBURL Java mining",
    "real PyClause query/grounding execution",
    "complete CoDEx-S/CoDEx-M loaders",
    "benchmark performance",
    "experiments A-F"
  ],
  "passed": 29,
  "real_data_smoke": {
    "masked_queries_checked": 16,
    "official_excerpt_rows": 240,
    "trained_backends": 0
  },
  "skipped": 5,
  "status": "passed_with_explicit_skips",
  "subtests_passed": 3
}
```


Evidence: `external_dependencies.json`

```json
{
  "attempts": [
    {
      "dependency": "complete_codex",
      "error": "<urlopen error [Errno -3] Temporary failure in name resolution>",
      "status": "blocked",
      "url": "https://api.github.com/repos/tsafavi/codex/commits/master"
    },
    {
      "dependency": "pykeen_index",
      "error": "<urlopen error [Errno -3] Temporary failure in name resolution>",
      "status": "blocked",
      "url": "https://pypi.org/pypi/pykeen/json"
    },
    {
      "dependency": "anyburl_jar",
      "error": "<urlopen error [Errno -3] Temporary failure in name resolution>",
      "status": "blocked",
      "url": "https://web.informatik.uni-mannheim.de/AnyBURL/AnyBURL-23-1x.jar"
    }
  ],
  "java": "/usr/bin/java",
  "note": "Web tool reads documentation and official text excerpts; shell downloads fail DNS. No model substitution."
}
```


Evidence: `backend-preflight.json`

```json
{
  "checks": [
    {
      "name": "numpy",
      "status": "available"
    },
    {
      "name": "torch",
      "status": "available"
    },
    {
      "name": "pykeen.models",
      "status": "available"
    },
    {
      "name": "pykeen.training",
      "status": "available"
    },
    {
      "name": "c_clause",
      "status": "available"
    },
    {
      "name": "clause",
      "status": "available"
    },
    {
      "name": "sklearn",
      "status": "available"
    },
    {
      "name": "matplotlib",
      "status": "available"
    },
    {
      "name": "java",
      "status": "available",
      "version": "openjdk version \"21.0.13\" 2026-10-20\nOpenJDK Runtime Environment (build 21.0.13+9)\nOpenJDK 64-Bit Server VM (build 21.0.13+9, mixed mode, sharing)"
    },
    {
      "name": "AnyBURL JAR",
      "sha256": "d1977ee0ffae3f715e48e32e91e8d46d0c5c243941a5a430fd132086160d06b5",
      "status": "available"
    },
    {
      "error": "[Errno 2] No such file or directory: 'data/codex-s/test.txt'",
      "name": "complete CoDEx-S",
      "status": "failed"
    }
  ],
  "environment": {
    "platform": "Linux-7.2.15-1-omarchy-x86_64-with-glibc2.44",
    "python": "3.11.16",
    "versions": {
      "PyClause": "0.0.1",
      "matplotlib": "3.11.2",
      "numpy": "2.4.6",
      "pandas": "3.1.1",
      "pykeen": "1.11.1",
      "scikit-learn": "1.9.1",
      "scipy": "1.17.1",
      "torch": "2.15.0+cpu"
    }
  },
  "status": "blocked",
  "training_launched": false
}
```


Evidence: `resumption-2026-11-22.json`

```json
{
  "attempted": [
    "GitHub/PyPI/AnyBURL HTTPS requests",
    "search available local caches for required backends/data",
    "CPU setup script",
    "complete CoDEx-S downloader",
    "strict backend preflight"
  ],
  "backend_installation_verified": false,
  "blocker": "Shell DNS resolution fails for external download hosts; required packages and full data are not cached",
  "date": "2026-11-22",
  "full_experiments_launched": false,
  "preflight": {
    "artifact": "artifacts/backend-preflight.json",
    "command": "python scripts/check_backend_environment.py",
    "exit_code": 1
  },
  "real_training_launched": false,
  "resume_command": "bash scripts/setup_cpu.sh",
  "resume_requirement": "Run in an environment able to reach the dependency and dataset hosts",
  "setup_attempt": {
    "command": "bash scripts/setup_cpu.sh",
    "exit_code": 128,
    "log": "artifacts/backend-setup-attempt.log"
  },
  "status": "blocked_external_downloads",
  "test_result": {
    "junit": "artifacts/tests-2026-11-22.xml",
    "passed": 29,
    "skipped": 5,
    "subtests_passed": 3
  }
}
```


Evidence: `installation-recovery.json`

```json
{
  "data_files_missing": [
    "test.txt",
    "valid_negatives.txt",
    "test_negatives.txt"
  ],
  "data_files_present": [
    "train.txt",
    "valid.txt"
  ],
  "next_command": ".backend-venv/bin/python -u -m kgc download --data data/codex-s --resume",
  "real_backends_verified": [
    "ComplEx",
    "RotatE",
    "AnyBURL Java mining",
    "PyClause candidate scoring and training groundings"
  ],
  "scientific_status": "separate development smoke runs; no paired benchmark conclusions",
  "smoke_runs": {
    "anyburl": "runs/installed-anyburl-smoke/validation-smoke.json",
    "complex": "runs/installed-complex-smoke/validation-smoke.json"
  },
  "status": "backends_verified_data_incomplete",
  "tests": {
    "passed": 35,
    "skipped": 2,
    "subtests_passed": 5
  }
}
```

No observations available.


### Protocol smoke checks


- passed: CoDEx-S; excerpt=True; 16 masked queries checked. Backend execution: none; loader, mapping, filtering, degrees, and masked-query checks only.


## Overall baselines

No observations available.


Exact MRR is shown only for complete entity rankings. Rule Hits and reciprocal-rank proxies from retrieval lists remain censored; they cannot establish full-ranking superiority. Scores are not probabilities.


## Scenario performance and complementarity


No paired benchmark runs completed. Experiments A–F are **unexecuted**; no claim about which model wins is justified.


## Robustness and hard negatives

No observations available.


No observations available.


Paired changes against matched unperturbed controls:


No observations available.


## Learned rule inventory and complexity

No observations available.


## Representative cases


Prediction examples require actual trained backends; none are invented here.


## Interpretation limits

Head/tail outcomes share triples; paired bootstrap clusters them together and resamples training seeds when available. A single-seed interval captures query variation only. Scenario groups and frequency/degree strata are exploratory correlations. Controlled removal/noise requires retraining both models, matching evaluation queries and budgets, and reporting changed graph statistics. Truth-dependent rule categories, path-to-truth counts, and oracle outcomes are evaluation diagnostics, never selection features. See `docs/METHODOLOGY.md` for hypotheses, literature grounding, intervention controls, and unverified capabilities.
