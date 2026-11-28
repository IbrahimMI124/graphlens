# When does ComplEx rescue a strongly supported AnyBURL error?

ComplEx recovered **224 of 1,767** CoDEx-S errors where AnyBURL’s wrong answer had a leading native rule score of at least .50. It picked the same wrong answer in **489** cases. Among the 31 explicitly verified false top answers in this group, ComplEx was correct in **5**, repeated the same verified false answer in **11**, and missed with a different answer in **15**.

**The rule score gap best separated the two groups among the contrasts tested.** ComplEx recovered 23.54% of strong errors when the wrong and correct candidates’ leading scores were within .05, and 8.01% when the gap was larger. After matching on relation, direction and known-entity degree, the estimate was +19.25 percentage points [+14.94, +22.74]. Both leading scores come from rule evidence. The gap is available once the correct answer is known.

The reverse pattern also occurs. In **108** queries, AnyBURL alone was correct and a strong general rule directly supported the held-out answer. These comparisons describe when the models differ on this benchmark. They leave the mechanisms inside ComplEx unresolved.

## Strongly supported AnyBURL errors

| Group | Queries (facts) | ComplEx correct | Same wrong top | Different miss |
| --- | --- | --- | --- | --- |
| All generated misses | 2,402 (1,519) | 280 · 11.66% [10.34%, 13.01%] | 598 · 24.90% | 1,524 |
| Leading wrong rule ≥ .50 | 1,767 (1,222) | 224 · 12.68% [11.08%, 14.34%] | 489 · 27.67% | 1,054 |
| Leading wrong rule ≥ .75 | 701 (641) | 89 · 12.70% [10.31%, 15.18%] | 271 · 38.66% | 341 |
| Leading wrong rule < .50 | 635 (401) | 56 · 8.82% [6.69%, 11.19%] | 109 · 17.17% | 470 |
| Leading wrong rule ≥ .50, verified false | 31 (31) | 5 · 16.13% [3.70%, 29.68%] | 11 · 35.48% | 15 |

All rows use the same 2,402 generated-miss population or a subset of it. Strong errors use the highest rule score for AnyBURL’s benchmark-filtered top wrong answer. The instances without a generated gold answer had no leading score reaching .50. Correctness uses the benchmark-filtered rankings. ComplEx seed 2 was selected by validation MRR in the original study. Some wrong answers have independent false labels from the hard-negative file. The other misses simply differ from the benchmark target. The verified cohort is small. Each interval is a pointwise 95% paired fact-bootstrap interval with 2,500 draws. [Other ComplEx seeds](seed-sensitivity.csv) · [Query-level results](query-level-outcomes.csv)

## What distinguishes rescues from shared failures?

| Group | Queries (facts) | ComplEx correct | Same wrong top | Different miss |
| --- | --- | --- | --- | --- |
| Wrong–correct leading score gap ≤ .05 | 531 (491) | 125 · 23.54% [19.77%, 27.18%] | 154 · 29.00% | 252 |
| Wrong–correct leading score gap > .05 | 1,236 (817) | 99 · 8.01% [6.49%, 9.64%] | 335 · 27.10% | 802 |
| Wrong answer led by a general rule | 179 (173) | 35 · 19.55% [13.85%, 25.80%] | 19 · 10.61% | 125 |
| Wrong answer led by a constant rule | 1,588 (1,097) | 189 · 11.90% [10.28%, 13.60%] | 470 · 29.60% | 929 |
| One near leader from all rules | 438 (416) | 67 · 15.30% [11.95%, 18.82%] | 195 · 44.52% | 176 |
| Two to four near leaders from all rules | 406 (363) | 75 · 18.47% [14.82%, 22.30%] | 96 · 23.65% | 235 |
| Five or more near leaders from all rules | 923 (913) | 82 · 8.88% [6.99%, 10.74%] | 198 · 21.45% | 643 |
| General and constant train-only tops agree | 272 (257) | 51 · 18.75% [14.18%, 23.44%] | 115 · 42.28% | 106 |
| General and constant train-only tops disagree | 1,495 (1,126) | 173 · 11.57% [9.93%, 13.34%] | 374 · 25.02% | 948 |

A near leader has a native scalar score within .05 of the strongest all-rule candidate after removing training positives. The score-gap comparison instead uses the two benchmark candidates in the error diagnosis. Groups can overlap across features.

| Within-stratum contrast | Strata | Queries first / second | Adjusted rescue first / second | Difference pp (95% CI) |
| --- | --- | --- | --- | --- |
| Score gap ≤ .05 versus > .05 | 49 | 493 / 1119 | 23.89% / 4.64% | +19.25 [+14.94, +22.74] |
| 1–4 near leaders versus 5 or more | 24 | 663 / 341 | 8.82% / 12.56% | -3.74 [-9.10, +1.73] |

Strata match exact relation and direction and the same log₂ degree bin. Each stratum contributes in proportion to its smaller group. Matched estimates apply to groups with shared strata. The matched interval for the number of near leaders spans zero.

## When strong general rules support the correct answer

| Group | Queries | Facts | AnyBURL Hits@1 | ComplEx Hits@1 | Δ pp (95% CI) | Left only / right only | Both / neither |
| --- | --- | --- | --- | --- | --- | --- | --- |
| General rule supports gold at ≥ .50 | 1042 | 521 | 70.83% | 68.62% | +2.21 [-0.57, +4.86] | 108 / 85 | 630 / 219 |
| General support for gold is weaker or absent | 2614 | 1307 | 19.43% | 22.38% | -2.95 [-4.36, -1.61] | 118 / 195 | 390 / 1911 |
| Strong general support and general rules alone rank gold first | 694 | 459 | 91.50% | 85.01% | +6.48 [+3.60, +9.31] | 74 / 29 | 561 / 30 |

The strongest applicable general rule for the held-out answer must score at least .50. This is a retrospective test of direct support. The final row further requires that general rules alone ranked the gold first.

## Worked examples

### ComplEx avoids a verified false answer

`test:1242:tail` · (Guinea-Bissau (Q1007), diplomatic relation (P530), ?). The held-out answer is **People's Republic of China (Q148)**. AnyBURL puts **Taiwan (Q865)** first and ComplEx puts **People's Republic of China (Q148)** first.

The benchmark explicitly labels AnyBURL’s top answer false.

- **People's Republic of China (Q148)** had leading score 0.867. `P530(X,Y) <= P530(Y,X)`. Training witness (People's Republic of China (Q148), diplomatic relation (P530), Guinea-Bissau (Q1007)).
- **Taiwan (Q865)** had leading score 0.871. `P530(X,Q865) <= P463(X,Q656801)`. Training witness (Guinea-Bissau (Q1007), member of (P463), International Finance Corporation (Q656801)).

### Both models choose the same verified false answer

`test:1321:tail` · (Malta (Q233), member of (P463), ?). The held-out answer is **Visa Waiver Program (Q45177)**. AnyBURL puts **International Development Association (Q827525)** first and ComplEx puts **International Development Association (Q827525)** first.

The benchmark explicitly labels AnyBURL’s top answer false.

- **Visa Waiver Program (Q45177)** had leading score 0.759. `P463(X,Q45177) <= P463(X,Q1969730)`. Training witness (Malta (Q233), member of (P463), Schengen Area (Q1969730)).
- **International Development Association (Q827525)** had leading score 0.802. `P463(X,Q827525) <= P463(X,Q5611262)`. Training witness (Malta (Q233), member of (P463), Group on Earth Observations (Q5611262)).

### Both models miss and choose different answers

`test:1569:tail` · (Romain Gary (Q157322), occupation (P106), ?). The held-out answer is **science fiction writer (Q18844224)**. AnyBURL puts **actor (Q33999)** first and ComplEx puts **poet (Q49757)** first.

The benchmark explicitly labels AnyBURL’s top answer false.

- **science fiction writer (Q18844224)** had leading score 0.286. `P106(Q157322,Y) <= P106(Q298761,Y)`. Training witness (Clive Barker (Q298761), occupation (P106), science fiction writer (Q18844224)).
- **actor (Q33999)** had leading score 0.758. `P106(X,Q33999) <= P106(X,Q2526255)`. Training witness (Romain Gary (Q157322), occupation (P106), film director (Q2526255)).

### A general rule supports AnyBURL’s correct answer

`test:1302:head` · (?, sibling (P3373), Marlon Jackson (Q319392)). The held-out answer is **Jackie Jackson (Q44855)**. AnyBURL puts **Jackie Jackson (Q44855)** first and ComplEx puts **Marlon Jackson (Q319392)** first.

`P3373(X,Y) <= P3373(A,X), P40(B,A), P40(B,Y)` had a native score of 0.880 and general rules alone also put the correct answer first. Training witness (La Toya Jackson (Q217427), sibling (P3373), Jackie Jackson (Q44855)) · (Joe Jackson (Q361297), child (P40), La Toya Jackson (Q217427)) · (Joe Jackson (Q361297), child (P40), Marlon Jackson (Q319392)).

## Ranking experiment correction

In the previous recovery table, the eight queries in “Both single changes recover it” were recovered by either intervention independently. The 7 and 126 rows count queries recovered by exactly one of the two interventions. The reweighted scores improved the selected true-versus-false matchup from 59.92% to 62.89%. Full ranking requires beating all eligible rivals, and Hits@1 fell from 34.08% to 32.58%. [Corrected ranking experiment](../rule-error-diagnosis/report.md)

Reproduce the analysis with the saved runs and English labels using `OPENBLAS_NUM_THREADS=1 .backend-venv/bin/python -m kgc.research.rule_rescues`.
