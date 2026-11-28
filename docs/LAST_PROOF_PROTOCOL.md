# Final feasibility check for loss of the last proof

Use only the original CoDEx-S training graph and the frozen variable-only rules
with exactly two body atoms. An eligible probe is an observed training fact
with one to three native groundings in that family, counting distinct rule and
ordered body instances and excluding groundings that use the probe fact itself.

Across three draws, allocate disjoint pools of 768 fitting and 640 audit facts.
All six pools exclude the probes sampled in the two preceding evidence pilots.
Seeds are 1911, 1912, and 1913. Process eligible fitting facts in order of proof
count, breaking ties reproducibly. For each, choose the smallest additional set
of edges that destroys all remaining two-hop proofs. Stop adding edges at the
budget of 1% of training facts (329 edges at most). For each draw the control
removes exactly the targeted deletion counts within each stratum of relation,
head degree bin, and tail degree bin. Degrees are measured on the original
training graph and binned by floor log2 degree.

The primary diagnostic is the targeted minus control difference in the share of
eligible audit facts losing **all** the original two-hop proofs. The gate needs
at least 60 eligible audit facts and a difference of at least eight percentage
points in every draw. Record whether nontrivial surviving proofs from all
general rules and from the constant-bearing family remain where two-hop
support is exhausted. Selection and auditing do not use validation or test
facts. An unsuccessful gate closes the scoped intervention before retraining.
