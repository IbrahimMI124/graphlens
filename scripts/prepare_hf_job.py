"""Stage the verified Phase-5 handoff and HF Jobs entrypoint for upload."""
import argparse
from pathlib import Path
import shutil


PROJECT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=PROJECT / ".hf-job-input")
    parser.add_argument("--output-volume", type=Path, default=PROJECT / ".hf-job-output")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    args.output_volume.resolve().mkdir(parents=True, exist_ok=True)
    sources = {
        PROJECT / "artifacts/phase5/work-handoff.tar": output / "work-handoff.tar",
        PROJECT / "scripts/run_phase5_hf_job.sh": output / "run_phase5_hf_job.sh",
    }
    for source, destination in sources.items():
        if not source.is_file():
            raise FileNotFoundError(f"Required HF Jobs input is missing: {source}")
        shutil.copy2(source, destination)
    print(f"Staged {len(sources)} inputs in {output}")


if __name__ == "__main__":
    main()
