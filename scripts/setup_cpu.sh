#!/usr/bin/env bash
# Run from any directory. Installs locally, tests real backends, then one CPU epoch.
# No full experimental runs or hyperparameter searches are launched.
set -euo pipefail
project_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$project_root"
python_bin=${KGC_PYTHON:-python3.11}
backend_env=${KGC_BACKEND_ENV:-.backend-venv}
export PIP_CACHE_DIR="$project_root/.download-cache/pip"
export MPLCONFIGDIR="$project_root/.download-cache/matplotlib"
export PYKEEN_HOME="$project_root/.download-cache/pykeen"
export PYSTOW_HOME="$project_root/.download-cache/pystow"
export XDG_CACHE_HOME="$project_root/.download-cache/xdg"
mkdir -p artifacts vendor "$MPLCONFIGDIR"
for tool in git curl java c++; do
    command -v "$tool" >/dev/null || { echo "Missing prerequisite: $tool" >&2; exit 1; }
done
# Resolve PyClause once, then install by immutable commit and retain the lock.
if [[ ! -f artifacts/pyclause-revision.txt ]]; then
    revision_line=$(git ls-remote https://github.com/symbolic-kg/PyClause.git HEAD)
    read -r pyclause_commit _ <<< "$revision_line"
    [[ "$pyclause_commit" =~ ^[0-9a-f]{40}$ ]] || { echo 'Cannot resolve PyClause commit' >&2; exit 1; }
    printf '%s\n' "$pyclause_commit" > artifacts/pyclause-revision.txt
fi
read -r pyclause_commit < artifacts/pyclause-revision.txt
[[ "$pyclause_commit" =~ ^[0-9a-f]{40}$ ]] || { echo 'Invalid saved PyClause commit' >&2; exit 1; }
if [[ ! -x "$backend_env/bin/python" ]]; then
    "$python_bin" -m venv "$backend_env"
fi
backend_python="$backend_env/bin/python"
export PIP_DEFAULT_TIMEOUT=20
export PIP_RETRIES=1
if ! "$backend_python" -c 'import torch; assert torch.version.cuda is None' >/dev/null 2>&1; then
    "$backend_python" -m pip install 'torch>=2.2,<3' --index-url https://download.pytorch.org/whl/cpu
fi
if ! "$backend_python" -c 'import pykeen.models, pykeen.training, sklearn, matplotlib, pytest' >/dev/null 2>&1; then
    "$backend_python" -m pip install -e '.[neural,analysis,test]'
fi
if ! "$backend_python" -c 'import c_clause, clause' >/dev/null 2>&1; then
    "$backend_python" -m pip install "git+https://github.com/symbolic-kg/PyClause.git@$pyclause_commit"
fi
"$backend_python" -m pip freeze > artifacts/backend-requirements-resolved.txt
if [[ ! -f vendor/AnyBURL-23-1x.jar ]]; then
    curl --fail --location --connect-timeout 15 --max-time 120 \
        https://web.informatik.uni-mannheim.de/AnyBURL/AnyBURL-23-1x.jar \
        --output vendor/AnyBURL-23-1x.jar.part
    "$backend_python" - <<'PY'
import zipfile
with zipfile.ZipFile('vendor/AnyBURL-23-1x.jar.part') as archive:
    if 'de/unima/ki/anyburl/Learn.class' not in archive.namelist():
        raise SystemExit('Downloaded JAR lacks the real AnyBURL Learn class')
PY
    mv vendor/AnyBURL-23-1x.jar.part vendor/AnyBURL-23-1x.jar
fi
if [[ ! -f data/codex-s/source.json ]]; then
    "$backend_python" -m kgc download --data data/codex-s --size s --resume
fi
"$backend_python" scripts/check_backend_environment.py
export KGC_DATA_S="$project_root/data/codex-s"
export KGC_ANYBURL_JAR="$project_root/vendor/AnyBURL-23-1x.jar"
"$backend_python" -m pytest -q --junitxml=artifacts/backend-tests.xml
"$backend_python" -m kgc smoke --data data/codex-s --neural --output runs/complete-codex-s-smoke
"$backend_python" -m kgc train --backend rules --data data/codex-s \
    --config configs/development.json --output runs/anyburl-codex-s-smoke
echo 'Backend tests and small CPU smoke runs completed. Full experiments remain unlaunched.'
