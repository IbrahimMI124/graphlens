#!/usr/bin/env bash
set -euo pipefail

input_dir=$1
output_dir=$2
draw=$3
shift 3

export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq --no-install-recommends default-jre-headless g++ git
project_dir=$(mktemp -d /tmp/aid851-removal.XXXXXX)
tar -xf /base/work-handoff.tar -C "$project_dir"
tar -xf "$input_dir/removal-replication-overlay.tar" -C "$project_dir"
cd "$project_dir"
python -m pip install --quiet --index-url https://download.pytorch.org/whl/cpu 'torch==2.15.0+cpu'
sed '/^torch==/d' artifacts/phase5/work-requirements.txt > /tmp/aid851-removal-requirements.txt
python -m pip install --quiet -r /tmp/aid851-removal-requirements.txt
python -m pip install --quiet --no-deps -e .

export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export JAVA_TOOL_OPTIONS=-XX:ActiveProcessorCount=1
export KGC_COOLING_SECONDS=0 KGC_MAX_CPU_C=0
export PYTHONUNBUFFERED=1
export KGC_DATA_S="$project_dir/data/codex-s" KGC_ANYBURL_JAR="$project_dir/vendor/AnyBURL-23-1x.jar"
run_dir="$output_dir/removal-${HF_JOB_ID:?Missing Hugging Face job ID}"
if [[ "${1:-}" == "--smoke" ]]; then
    python -m pytest -q tests/test_removal_replication.py tests/test_structure.py
fi
exec python -m kgc.research.removal_replication --draw "$draw" --output "$run_dir" "$@"
