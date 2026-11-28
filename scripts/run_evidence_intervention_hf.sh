#!/usr/bin/env bash
set -euo pipefail

stage=$1
shift
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq --no-install-recommends default-jre-headless g++ git
project_dir=$(mktemp -d /tmp/aid851-evidence.XXXXXX)
tar -xf /base/work-handoff.tar -C "$project_dir"
tar -xf /input/evidence-overlay.tar -C "$project_dir"
cd "$project_dir"
python -m pip install --quiet --index-url https://download.pytorch.org/whl/cpu 'torch==2.15.0+cpu'
sed '/^torch==/d' artifacts/phase5/work-requirements.txt >/tmp/aid851-evidence-requirements.txt
python -m pip install --quiet -r /tmp/aid851-evidence-requirements.txt
python -m pip install --quiet --no-deps -e .

export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export JAVA_TOOL_OPTIONS=-XX:ActiveProcessorCount=1
export KGC_COOLING_SECONDS=0 KGC_MAX_CPU_C=0 PYTHONUNBUFFERED=1
export KGC_DATA_S="$project_dir/data/codex-s" KGC_ANYBURL_JAR="$project_dir/vendor/AnyBURL-23-1x.jar"
run_dir="/output/evidence-${HF_JOB_ID:?Missing Hugging Face job ID}"
if [[ "$stage" == "prepare" ]]; then
    python -m pytest -q tests/test_evidence_intervention.py tests/test_removal_replication.py tests/test_structure.py
    python -m kgc.research.evidence_intervention prepare --output "$run_dir/prepared" "$@"
    if python -c 'import json,sys; p=json.load(open(sys.argv[1])); sys.exit(not p["draws"][0]["audit"]["passed"])' "$run_dir/prepared/preparation-status.json"; then
        exec python -m kgc.research.evidence_intervention smoke --draw 0 --prepared "$run_dir/prepared" --output "$run_dir/smoke" "$@"
    fi
else
    exec python -m kgc.research.evidence_intervention run --prepared /prepared --output "$run_dir" "$@"
fi
