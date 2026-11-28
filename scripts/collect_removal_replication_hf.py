"""Download compact outputs for three completed Hugging Face draws and report."""
import argparse
from pathlib import Path
import subprocess
import sys


REQUIRED = (
    "replication-status.json", "replication-protocol.json", "outcomes.npz",
    "grounding-loss.csv", "grounding-examples.json", "overall.csv",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("job_ids", nargs=3, help="Full experiment job IDs, in draw order")
    parser.add_argument("--bucket", default="ibrahimmi124/jobs-artifacts")
    parser.add_argument("--prefix")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--evidence", action="store_true", help="Collect direct rule-body deletion runs")
    parser.add_argument("--greedy", action="store_true", help="Use the second evidence intervention design")
    parser.add_argument("--hf", default=str(Path(sys.executable).with_name("hf")))
    args = parser.parse_args()
    if args.greedy and not args.evidence:
        parser.error("--greedy requires --evidence")
    if len(set(args.job_ids)) != 3 or any(
        len(j) != 24 or any(c not in "0123456789abcdef" for c in j) for j in args.job_ids
    ):
        parser.error("Three distinct Hugging Face job IDs are required")
    cloud_folder = "evidence-intervention" if args.evidence else "removal-replication"
    prefix = args.prefix or f"{cloud_folder}/jobs"
    output = args.output or Path("artifacts") / cloud_folder
    run_label = "evidence" if args.evidence else "removal"
    paths = []
    patterns = [arg for filename in REQUIRED for arg in ("--include", filename)]
    for index, job_id in enumerate(args.job_ids, 1):
        path = output / f"draw-{index}-{job_id}"
        path.mkdir(parents=True, exist_ok=True)
        remote = f"hf://buckets/{args.bucket}/{prefix}/{run_label}-{job_id}"
        subprocess.run([args.hf, "buckets", "sync", remote, str(path), *patterns],
                       check=True, timeout=120)
        paths.append(str(path))
    command = [sys.executable, "-m", "kgc.research.removal_replication_report",
               *paths, "--output", str(output / "report")]
    if args.evidence:
        command.append("--evidence")
    if args.greedy:
        command.append("--greedy")
    subprocess.run(command, check=True, timeout=240)


if __name__ == "__main__":
    main()
