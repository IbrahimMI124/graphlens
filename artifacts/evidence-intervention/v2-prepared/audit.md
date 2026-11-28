# Training-only audit for direct rule-body removal

Method: marginal grounding loss.

| draw | audit_supported_facts | targeted_loss_pct | matched_loss_pct | difference_pp | conditional_ci_low_pp | conditional_ci_high_pp | passed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 384 | 27.3354 | 26.2467 | 1.0888 | -0.7997 | 3.0765 | False |
| 2 | 384 | 25.7169 | 27.7373 | -2.0204 | -4.1160 | 0.0498 | False |
| 3 | 383 | 24.8843 | 26.7531 | -1.8688 | -3.7056 | -0.0208 | False |

The full matrix requires all three draws to meet the five-point training threshold. This design failed that criterion.

The 95% intervals pair the two masks for each audit fact and resample facts within each draw. They condition on the graph, catalog and prepared masks. The gate uses the point estimate. [Full audit table](verified-training-audit.csv)
