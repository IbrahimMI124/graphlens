# CoDEx-S structural sensitivity across three matched graph draws

Each draw pairs targeted deletion with a random deletion with exactly the same retained relation counts. Each arm has three fitted ComplEx seeds and two independently mined rule inventories. The validation-selected models are used for the primary contrast. The official evaluation contains 1,828 facts and 3,656 directional queries shared by all draws.

## Change in the neural versus rule gap

Positive values mean targeted removal favors ComplEx relative to all-rule AnyBURL more than the matched deletion does. Effects and interval endpoints in the table are proportions. The per-draw intervals share paired head and tail clusters and resample the fitted learning replicates. The aggregate also resamples graph draws. Three graph draws give limited uncertainty information. These estimates are exploratory on CoDEx-S.

| draw | difference | low | high | n_triples |
| --- | --- | --- | --- | --- |
| 1 | 0.0103 | -0.0017 | 0.0222 | 1828 |
| 2 | 0.0035 | -0.0114 | 0.0177 | 1828 |
| 3 | 0.0015 | -0.0159 | 0.0190 | 1828 |
| averaged | 0.0051 | -0.0065 | 0.0171 | 1828 |


All ranks used in Hits outcomes were certified for the available supported candidates.

### Targeted minus matched Hits@1 for each method

| method | difference | low | high |
| --- | --- | --- | --- |
| neural | -0.0011 | -0.0125 | 0.0105 |
| fixed_updates | 0.0075 | -0.0040 | 0.0194 |
| fresh_all | -0.0062 | -0.0186 | 0.0067 |
| frozen_general | -0.0077 | -0.0164 | 0.0005 |
| frozen_constants | -0.0017 | -0.0090 | 0.0057 |


[Arm-level metrics](arm-means.csv) · [All paired effects](paired-effects.csv) · [Graph audit](graph-audit.csv) · [Gap plot](paired-gap.pdf)

## Frozen general-rule groundings

| draw | n_facts | n_original_supported | n_original_groundings | targeted_lost | matched_lost | targeted_any | matched_any | targeted_all | matched_all | targeted_mean_loss | matched_mean_loss | difference | low | high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1828 | 1823 | 4938548 | 1240751 | 1339129 | 1807 | 1819 | 0 | 0 | 0.2283 | 0.2638 | -0.0355 | -0.0447 | -0.0265 |
| 2 | 1828 | 1823 | 4938548 | 1174302 | 1293489 | 1800 | 1819 | 0 | 0 | 0.2219 | 0.2677 | -0.0458 | -0.0557 | -0.0362 |
| 3 | 1828 | 1823 | 4938548 | 1145032 | 1328159 | 1802 | 1822 | 1 | 0 | 0.2215 | 0.2605 | -0.0390 | -0.0491 | -0.0288 |


Across draws, the mean per-fact loss fraction changed by -0.0401 for targeted minus matched deletion, with exploratory 95% interval [-0.0491, -0.0317]. The denominator includes 1823 originally supported facts per draw. All retained groundings were verified against independent native enumeration on the modified graphs.

Fixed-catalog ranking responses also reflect native frequency tie breaking. Matching relation totals leaves local degree, particular endpoints and paths free to change. The intervention cannot identify independent mediating effects of those variables on either model.

[Grounding counts](grounding-summary.csv) · [Grounding loss plot](grounding-loss.pdf)

## Interpretation

The interval for the primary change in the ComplEx–AnyBURL gap includes zero. The comparison leaves the relative Hits@1 advantage uncertain. Relation-matched random removal erased a larger share of general-rule body groundings in every draw. Local targeting therefore cannot be used as a proxy for stronger removal of rule evidence in this design. Across the 10,938 originally supported fact-by-arm-by-draw observations, 1 lost every general-rule grounding. These observations reuse the same benchmark facts across draws and arms. A replication with an intervention defined by training rule-body edges would test sensitivity to evidence more directly.
