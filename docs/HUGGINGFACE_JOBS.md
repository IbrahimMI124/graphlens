# Hugging Face Jobs compute

The prepared Phase-5 replicated cohort can run as a Hugging Face Job. The
workflow uses the CPU XL flavor and the same pinned CPU PyTorch, Java, PyClause,
dataset, and handoff checks as the existing runner. CUDA stays disabled in the
experiment launcher. Job outputs and logs are written to a writable HF volume;
the submission uploads only the 82 MB whitelisted handoff archive and a small
entrypoint, rather than the workspace's previous runs and reports.

This setup does not submit a Job. Hugging Face Jobs use prepaid credits, and
submitting the command below starts paid compute. The prepared cohort includes
15 ComplEx fits, 10 fresh AnyBURL mining realizations, and frozen-rule
applications. Runtime depends on the available CPU flavor and queue.

## Prepare and submit

From the project root, after `hf auth login` with an account that has Jobs
permission:

```bash
python3 scripts/prepare_hf_job.py
hf jobs run \
  --name aid851-phase5-replicated \
  --flavor cpu-xl \
  --timeout 3d \
  --volume ./.hf-job-input:/input \
  --volume ./.hf-job-output:/output:rw \
  python:3.11 bash /input/run_phase5_hf_job.sh /input /output
```

The HF CLI syncs local volume directories to its private `jobs-artifacts`
Storage Bucket and mounts them in the Job. The output mount is writable so the
archive, experiment state, checkpoints, logs, and final report persist. The
launcher creates a unique directory named `phase5-$HF_JOB_ID` and refuses to
reuse an existing one. No retry is configured.

Follow the Job URL printed by the CLI or use `hf jobs logs <job-id>`. After the
Job ends, use the `hf buckets sync` command printed by the CLI to retrieve the
write-back volume to `.hf-job-output`. The final report is under
`phase5-$HF_JOB_ID/artifacts/phase5/replicated-report/report.md`.

## Safety and environment checks

The remote entrypoint installs the image's default headless Java runtime, a C++ compiler, the pinned CPU Torch
wheel, and the handoff's resolved Python requirements. It runs the existing
checksum/provenance verifier and backend preflight before any experiment stage.
The runner still rejects the laptop hostname, serializes all experiment stages,
sets one active Java processor, and records execution state under the unique
output directory. A failed job leaves its recorded state and artifacts in place;
inspect them before deciding whether to prepare a new cohort attempt.

To inspect the proposed hardware options without starting compute, run
`hf jobs hardware`. To cancel an active job, use `hf jobs cancel <job-id>`.

Hugging Face references: [Jobs guide](https://huggingface.co/docs/huggingface_hub/guides/jobs),
[CLI volume and Jobs configuration](https://huggingface.co/docs/hub/jobs-configuration).
