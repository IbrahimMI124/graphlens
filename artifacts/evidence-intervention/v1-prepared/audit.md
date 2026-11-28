# Training-only audit for direct rule-body removal

Method: additive edge incidence.

| draw | audit_supported_facts | targeted_loss_pct | matched_loss_pct | difference_pp | conditional_ci_low_pp | conditional_ci_high_pp | passed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 384 | 25.4948 | 27.2988 | -1.8041 | -4.0560 | 0.4841 | False |
| 2 | 384 | 24.8092 | 27.2524 | -2.4432 | -4.6851 | -0.1811 | False |
| 3 | 384 | 27.9205 | 26.7117 | 1.2089 | -1.0984 | 3.5458 | False |

The full matrix requires all three draws to meet the five-point training threshold. This design failed that criterion.

The 95% intervals pair the two masks for each audit fact and resample facts within each draw. They condition on the graph, catalog and prepared masks. The gate uses the point estimate. [Full audit table](verified-training-audit.csv)
