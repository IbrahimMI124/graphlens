# Phase 5 compute status

**The configured SSH target named `work` is off-limits. Do not connect to it,
transfer files there, restore its key for this project, or launch experiments
there.** The earlier server plan has been withdrawn per the user's clarification.
No alternate compute destination has been authorized. The laptop is also not
being used for the remaining full-budget matrix because of the previous heat
issue. No additional training was started.

## Local handoff artifact

The checksum-verified archive at `artifacts/phase5/work-handoff.tar` is a local
preparation artifact only; it has not been transferred or executed. It contains
115 whitelisted regular files, including the public CoDEx-S data, source, audited
graph plans, frozen-rule inputs and AnyBURL JAR. It contains no checkpoints or
credentials. Its SHA-256 is recorded in
`artifacts/phase5/work-handoff.tar.sha256`; the JSON manifest verifies each of
the 114 input files. The launcher passed local verify-only checks without
importing model backends or starting execution. **This package does not grant
permission to use the off-limits host.**

The prospective cohort describes five audited 90%-retention graphs, three
ComplEx seeds and two independent rule-mining realizations per graph. Completing
it would require 15 neural fits, 10 Java mining runs and the corresponding rule
applications. The four modified-graph frozen-constant applications also remain
pending. No primary intervention conclusion can be drawn from this unexecuted
cohort.

If a different compute target is designated later, reassess its authorization,
resource limits and access before transferring or executing anything. Do not
run `scripts/run_phase5_work.py --execute` on the off-limits host. The launcher
is not permission to use a machine.

## Previously completed local inference work

The inference-only supervisor was tested with 50 ms active windows followed by
450 ms stopped windows (about 10% of one allowed core). General and constant
prefix predictions exactly matched prior native candidate lists/ranks/scores.
A later 20% duty-cycle attempt completed the original constant-rule control on
all 3,656 queries, again exactly reproducing the prior results, but a host CPU
reading reached 81°C and the controller stopped the remaining local work.
These readings cover the host, not a causal attribution of all heat to the child.

The original constant control uses an answer-blind cache: 2,015 masked inputs
for 3,656 directional queries. Filtering remains answer-specific in the
evaluator. Unused explanation dictionaries can be omitted for prediction-only
application; post-hoc witnesses require retained metadata. These optimizations
do not change native scoring. Paused/cached wall timings are not algorithmic
speed comparisons with older runs.
