# Direct rule-body deletion pilots

Both selection designs completed on Hugging Face. Neither produced the declared increase in grounding loss on independent training audit facts. The benchmark model comparison was gated on that check, so there are no new ComplEx or AnyBURL accuracy results from these pilots.

| Design | Draw | Supported audit facts | Targeted loss | Matched loss | Difference (pp) | 95% interval (pp) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Additive edge incidence | 1 | 384 | 25.49% | 27.30% | -1.80 | [-4.06, +0.48] |
| Additive edge incidence | 2 | 384 | 24.81% | 27.25% | -2.44 | [-4.69, -0.18] |
| Additive edge incidence | 3 | 384 | 27.92% | 26.71% | +1.21 | [-1.10, +3.55] |
| Marginal grounding loss | 1 | 384 | 27.34% | 26.25% | +1.09 | [-0.80, +3.08] |
| Marginal grounding loss | 2 | 384 | 25.72% | 27.74% | -2.02 | [-4.12, +0.05] |
| Marginal grounding loss | 3 | 383 | 24.88% | 26.75% | -1.87 | [-3.71, -0.02] |

The estimate averages the fraction of original nontrivial rule-body groundings lost per originally supported audit fact. The 95% intervals resample paired audit facts within a draw. They are conditional on the graph, catalog and masks. The predeclared threshold was at least +5 percentage points in each draw.

## What the audits establish

I verified the saved training masks, exact quotas for each relation and pair of endpoint degree bins, disjoint fit and audit probes, and recomputed loss from per-fact counts. Each arm removed 3,289 edges. No validation or test triple was used to select those edges or score the audit. Version 2 also excluded all probes sampled by version 1.

In the revised pilot, the matched controls already removed 3,237 to 3,249 edges per draw that occurred in fit-probe rule bodies. The median supported audit observation had 898 original groundings. Each of the 1,151 supported audit fact-by-draw observations kept at least one grounding in both arms. This shows that membership in a rule body is common even in a matched random deletion and that losing some groundings left alternative support here. The audit leaves the effect on model accuracy unresolved.

The study concerns these selection objectives, the 90% retention rate and this frozen catalog. An intervention on a predeclared family of proofs with fewer alternatives would test whether removing the last available support changes predictions. It would require a fresh training-only audit before a benchmark comparison.

[Protocol](../../docs/RULE_EVIDENCE_INTERVENTION.md) · [First pilot audit](v1-prepared/audit.md) · [Revised pilot audit](v2-prepared/audit.md) · [Cloud job record](hf-submission.json)
