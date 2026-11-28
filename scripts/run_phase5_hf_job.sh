#!/usr/bin/env bash
# Entrypoint inside a Hugging Face Job. Outputs stay on its writable volume.
set -euo pipefail

input_dir=${1:-/input}
output_dir=${2:-/output}
job_id=${HF_JOB_ID:-manual-$(date -u +%Y%m%dT%H%M%SZ)}
project_dir="$output_dir/phase5-$job_id"

if [[ ! -f "$input_dir/work-handoff.tar" ]]; then
    echo "Missing $input_dir/work-handoff.tar" >&2
    exit 2
fi
if [[ -e "$project_dir" ]]; then
    echo "Refusing to reuse an existing job directory: $project_dir" >&2
    exit 2
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends default-jre-headless g++
rm -rf /var/lib/apt/lists/*

mkdir -p "$project_dir"
tar -xf "$input_dir/work-handoff.tar" -C "$project_dir"
cd "$project_dir"

python -m pip install --upgrade pip
python -m pip install --index-url https://download.pytorch.org/whl/cpu 'torch==2.15.0+cpu'
sed '/^torch==/d' artifacts/phase5/work-requirements.txt > /tmp/kgc-requirements.txt
python -m pip install -r /tmp/kgc-requirements.txt
python -m pip install --no-deps -e .

export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export JAVA_TOOL_OPTIONS=-XX:ActiveProcessorCount=1

python scripts/run_phase5_work.py --execute --compute-host "$(hostname)"
