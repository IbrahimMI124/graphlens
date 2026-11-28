#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq --no-install-recommends git g++
project=$(mktemp -d /tmp/aid851-closeout.XXXXXX)
tar -xf /base/work-handoff.tar -C "$project"
tar -xf /input/last-proof-overlay.tar -C "$project"
cd "$project"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONUNBUFFERED=1
python -m pip install --quiet 'numpy==2.4.6' 'pytest==9.2.0' 'PyClause @ git+https://github.com/symbolic-kg/PyClause.git@87c82ec3dd904767741a493dcbdf7605377d4535'
python -m pytest -q tests/test_last_proof.py
exec python -m kgc.research.last_proof --output "/output/last-proof-${HF_JOB_ID:?Missing Hugging Face job ID}"
