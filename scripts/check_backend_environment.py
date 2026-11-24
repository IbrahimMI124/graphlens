"""Strict preflight: missing backends/data fail instead of silently skipped tests."""
import argparse
import importlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kgc.io import digest, environment, write_json
from kgc.data import load_dataset


def check(data, jar):
    checks = []
    for module in ("numpy", "torch", "pykeen.models", "pykeen.training", "c_clause", "clause", "sklearn", "matplotlib"):
        try:
            importlib.import_module(module)
            checks.append({"name": module, "status": "available"})
        except Exception as exc:
            checks.append({"name": module, "status": "failed", "error": f"{type(exc).__name__}: {exc}"})
    try:
        proc = subprocess.run(["java", "-version"], capture_output=True, text=True, timeout=10, check=True)
        checks.append({"name": "java", "status": "available", "version": (proc.stderr or proc.stdout).strip()})
    except (OSError, subprocess.SubprocessError) as exc:
        checks.append({"name": "java", "status": "failed", "error": str(exc)})
    try:
        with zipfile.ZipFile(jar) as archive:
            if "de/unima/ki/anyburl/Learn.class" not in archive.namelist():
                raise ValueError("JAR lacks de.unima.ki.anyburl.Learn")
        checks.append({"name": "AnyBURL JAR", "status": "available", "sha256": digest(jar)})
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        checks.append({"name": "AnyBURL JAR", "status": "failed", "error": str(exc)})
    try:
        dataset = load_dataset(data, "s")
        checks.append({"name": "complete CoDEx-S", "status": "available", "provenance": dataset.provenance})
    except (OSError, ValueError, KeyError) as exc:
        checks.append({"name": "complete CoDEx-S", "status": "failed", "error": str(exc)})
    return {"status": "ready" if all(c["status"] == "available" for c in checks) else "blocked",
            "checks": checks, "environment": environment(), "training_launched": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default="data/codex-s")
    parser.add_argument("--jar", default="vendor/AnyBURL-23-1x.jar")
    parser.add_argument("--output", default="artifacts/backend-preflight.json")
    args = parser.parse_args()
    record = check(args.data, args.jar)
    write_json(args.output, record)
    print(json.dumps(record, indent=2))
    return 0 if record["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
