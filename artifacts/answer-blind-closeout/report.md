# Can we choose between AnyBURL and ComplEx before knowing the answer?

**The measured rule evidence did not establish a reliable way to choose.** On CoDEx-S, the selector with rule evidence and the controls-only selector each returned the correct answer on 22.98% of queries. Their paired difference was +0.00 percentage points [-0.49, +0.52]. The top-two gap policy scored 22.68% by choosing ComplEx in both validation groups.

## What we can measure before answering

The earlier error analysis used the rule scores of the correct answer and AnyBURL’s first wrong answer. ComplEx rescued 23.54% of strong errors with a close gap and 8.01% with a wider gap. Identifying both candidates in that comparison requires the correct answer. The final check uses the scores of AnyBURL’s first and second candidates after removing known training positives. Both scores are available from the masked query.

When the models disagree and AnyBURL returns at least two candidates, a fixed cutoff of .05 separates close and wide scores. The stronger model in each validation group is selected for that group. ComplEx handles validation ties and queries with fewer than two candidates. If the models agree, their shared answer is returned. Choices were written using masked test profiles before joining test outcomes.

| Top-two score gap | Validation disagreements | ComplEx correct | AnyBURL correct | Selected |
| --- | --- | --- | --- | --- |
| close | 2010 | 202 | 165 | ComplEx |
| wide | 374 | 57 | 55 | ComplEx |

The saved controls-only selector uses relation, direction, entity degree, training relation frequency and answer multiplicity. Its evidence-aware counterpart also uses native rule confidence, candidate competition, family agreement and applicable rule structures. Both were fit on validation disagreements. [Selector methods](../evidence-advantage/report.md)

## Test results

The models disagree on 2,341 of 3,656 train-only top answers. Among those disagreements, only ComplEx was right on 237, only AnyBURL was right on 190, and both missed on 1,914.

| Model or comparison | Test queries | Left | Right | Gap pp (95% CI) |
| --- | --- | --- | --- | --- |
| AnyBURL vs ComplEx | 3656 | 21.39% | 22.68% | -1.29 [-2.43, -0.11] |
| controls vs ComplEx | 3656 | 22.98% | 22.68% | +0.30 [-0.27, +0.85] |
| controls + rule evidence vs ComplEx | 3656 | 22.98% | 22.68% | +0.30 [-0.30, +0.93] |
| top-two gap vs ComplEx | 3656 | 22.68% | 22.68% | +0.00 [+0.00, +0.00] |
| controls + rule evidence vs controls | 3656 | 22.98% | 22.98% | +0.00 [-0.49, +0.52] |
| top-two gap vs controls | 3656 | 22.68% | 22.98% | -0.30 [-0.85, +0.27] |

Each accuracy in this table scores the actual answer returned from a training-only candidate list. Intervals are paired 95% fact-bootstrap intervals with both directions from each fact kept together. The two fitted selectors each solved 44 queries missed by the other.

| Top-two score gap | Test disagreements | ComplEx correct | AnyBURL correct | ComplEx minus AnyBURL pp (95% CI) |
| --- | --- | --- | --- | --- |
| close | 1966 | 9.05% | 7.12% | +1.93 [+0.05, +3.75] |
| wide | 371 | 15.90% | 13.48% | +2.43 [-3.09, +7.90] |

The ComplEx advantage in the close group minus its advantage in the wide group was -0.49 percentage points [-6.17, +5.47].

As a check for repeated masked questions, the following comparisons use test questions whose masked inputs never appeared in validation.

| Model or comparison | Test queries | Left | Right | Gap pp (95% CI) |
| --- | --- | --- | --- | --- |
| controls + rule evidence vs controls | 1475 | 41.63% | 41.42% | +0.20 [-0.62, +1.03] |
| top-two gap vs controls | 1475 | 40.95% | 41.42% | -0.47 [-1.55, +0.61] |

The standard benchmark also scores the selected model’s ranking after filtering other known positive facts. That endpoint can promote a lower candidate in the chosen ranking. The two comparisons below use this benchmark endpoint.

| Model or comparison | Test queries | Left | Right | Gap pp (95% CI) |
| --- | --- | --- | --- | --- |
| controls + rule evidence vs controls | 3656 | 36.11% | 36.43% | -0.33 [-0.82, +0.19] |
| top-two gap vs controls | 3656 | 35.56% | 36.43% | -0.88 [-1.53, -0.25] |

Rule evidence lowered three-class Brier loss from 0.268 to 0.262 (paired change interval [-0.012, -0.001]). Among disagreements with exactly one correct model, winner AUC was 0.603 for controls and 0.591 after adding rule evidence. The probability scores improved on the Brier measure while the selected answers had equal overall accuracy.

## Final research conclusion

1. Strong general rules directly supported the correct answers in 108 cases that only AnyBURL solved.
2. ComplEx recovered some strongly supported AnyBURL errors, especially when the wrong answer and the held-out answer had similar rule scores. [Comparative error and rule examples](../rule-rescues/report.md)
3. The answer-blind gap and the richer rule-evidence selector yielded no improvement over the controls-only selector in actual answer accuracy on this split.

The CoDEx-S test has been examined throughout the study, so these results are exploratory. Independent CoDEx-M confirmation remains open.

[Per-query choices](locked-test-choices.csv) · [Paired results](test-comparisons.csv) · [Protocol and input hashes](decision-protocol.json)

Reproduce from the project root with `OPENBLAS_NUM_THREADS=1 .backend-venv/bin/python -m kgc.research.answer_blind_closeout`.
