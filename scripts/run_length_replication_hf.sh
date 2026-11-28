#!/usr/bin/env bash
set -euo pipefail
catalog=$1
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq --no-install-recommends g++ git
project=$(mktemp -d /tmp/aid851-length.XXXXXX)
tar -xf /base/work-handoff.tar -C "$project"
cp /input/length_replication.py "$project/kgc/research/length_replication.py"
cd "$project"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONUNBUFFERED=1
python -m pip install --quiet 'numpy==2.4.6' 'PyClause @ git+https://github.com/symbolic-kg/PyClause.git@87c82ec3dd904767741a493dcbdf7605377d4535'
out="/output/length-${HF_JOB_ID:?Missing Hugging Face job ID}"
source="/previous/runs/phase5-replicated-prepared/original/rules-$catalog/mining"
python -m kgc.research.length_replication --mining "$source" --limit 16 --output "$out/smoke"
exec python -m kgc.research.length_replication --mining "$source" --output "$out"
