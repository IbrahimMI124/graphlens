# Why does AnyBURL put the wrong answer first?

**Both mechanisms show up.** Strong rules sometimes support answers the benchmark verifies as false. Changing how AnyBURL combines those same rule scores also recovers some answers. The original ranking has the highest overall accuracy among the tested variants.

AnyBURL missed 2,410 of 3,656 CoDEx-S queries. It generated the correct candidate in 2,402 of those misses and failed to generate it in 8. So the main bottleneck is choosing among generated candidates.

In 2,158 generated misses, the wrong candidate had a higher confidence on its strongest rule. Later rule scores broke an initial tie in 243 cases. The full score sequences tied once. This comparison describes how the native ranking made its choice.

We also found 48 such misses where the first answer is explicitly verified false. In 31 of those, the leading rule still had adjusted confidence of at least .50. The verified false answers were led by 36 distinct rules. These cases directly show that reliable-looking rules can be wrong on new facts.

## Two changes to the same candidate lists

**Rule confidence.** We kept maxplus order and changed the individual confidences. Compared with native `unseen=5, B × 1, Uc/Ud × 1`, the selected setting was `unseen=5, B × 0.7, Uc/Ud × 1`. We chose it on validation by asking how often the best rule score favored the known true answer over the highest native-ranked verified false answer for the same masked query. Score ties receive half credit. Both candidates had to be generated. [Validation settings](validation-confidence-settings.csv)

**Candidate aggregation.** We kept the original individual confidences and replaced maxplus with noisy-or. Maxplus compares candidates’ rule scores from highest to lowest. Noisy-or pools all supporting rule scores, which can give repeated or correlated rules extra influence. The fourth variant combines both changes. The frozen native replay matched all saved candidate lists in their exact order. Every variant reranks precisely the same candidates. The evaluator applies the benchmark filter afterward.

| Group | Queries | Facts | Variant Hits@1 | Native Hits@1 | Δ pp (95% CI) | Left only / right only | Both / neither |
| --- | --- | --- | --- | --- | --- | --- | --- |
| native | 3656 | 1828 | 34.08% | 34.08% | +0.00 [+0.00, +0.00] | 0 / 0 | 1246 / 2410 |
| reweighted maxplus | 3656 | 1828 | 32.58% | 34.08% | -1.50 [-2.05, -0.96] | 15 / 70 | 1176 / 2395 |
| native confidence + noisy-or | 3656 | 1828 | 23.06% | 34.08% | -11.02 [-12.61, -9.46] | 134 / 537 | 709 / 2276 |
| reweighted + noisy-or | 3656 | 1828 | 22.95% | 34.08% | -11.13 [-12.72, -9.57] | 132 / 539 | 707 / 2278 |

| Group | Queries | Facts | Variant accuracy | Native accuracy | Δ pp (95% CI) | Left only / right only | Both / neither |
| --- | --- | --- | --- | --- | --- | --- | --- |
| native | 3656 | 1828 | 21.39% | 21.39% | +0.00 [+0.00, +0.00] | 0 / 0 | 782 / 2874 |
| reweighted maxplus | 3656 | 1828 | 21.12% | 21.39% | -0.27 [-0.57, +0.01] | 11 / 21 | 761 / 2863 |
| native confidence + noisy-or | 3656 | 1828 | 18.85% | 21.39% | -2.54 [-3.56, -1.53] | 128 / 221 | 561 / 2746 |
| reweighted + noisy-or | 3656 | 1828 | 18.82% | 21.39% | -2.57 [-3.61, -1.53] | 129 / 223 | 559 / 2745 |

The second table keeps the actual top answer after filtering training positives only. Intervals are paired 95% percentile intervals from 2,500 bootstrap samples of facts, with both directions kept together. The native benchmark Hits@1 was 34.08%. Compared with it, reweighting changed Hits@1 by -1.50 pp [-2.05, -0.96], pooling changed it by -11.02 pp [-12.61, -9.46], and the combined change shifted it by -11.13 pp [-12.72, -9.57].

## Which generated misses changed?

| Change that recovered the answer | Queries | Share (95% CI) |
| --- | --- | --- |
| Reweighting only among single changes | 7 / 2,402 | 0.29% [0.08%, 0.54%] |
| Aggregation only among single changes | 126 / 2,402 | 5.25% [4.36%, 6.15%] |
| Both single changes recover it | 8 / 2,402 | 0.33% [0.12%, 0.58%] |
| Only the combined change | 4 / 2,402 | 0.17% [0.04%, 0.34%] |
| None of the changes | 2,257 / 2,402 | 93.96% [92.95%, 94.89%] |

These counts measure sensitivity to the specific interventions. The paired accuracy table shows new errors elsewhere as native-only successes. Failures that remain can reflect the rules, the ranking policy, or both.

## Check against verified false answers

On 1,482 test comparisons from 1,094 facts, the native leading rule scored the verified false candidate higher in 531 comparisons and tied it in 126. Giving ties half credit, the best rule scores favored the correct candidate 59.92% of the time with native confidences and 62.89% with reweighting (+2.97 pp [+1.99, +4.00]). This comparison targets the hardest available verified rival under the original ranker. It estimates performance on that selected cohort. Many other benchmark misses lack independent false labels. [Per-query verified comparisons](verified-negative-pairs.csv)

## Concrete queries

### A strong rule supports a verified false answer

`test:1242:tail` · (Guinea-Bissau (Q1007), diplomatic relation (P530), ?). The benchmark independently verifies the native top as false.

The held-out answer is **People's Republic of China (Q148)**.

| Ranking | First answer |
| --- | --- |
| native | Taiwan (Q865) |
| reweighted maxplus | Taiwan (Q865) |
| native confidence + noisy-or | Taiwan (Q865) |
| reweighted + noisy-or | Taiwan (Q865) |

- **People's Republic of China (Q148)** had leading score 0.867. `P530(X,Y) <= P530(Y,X)` had 1532 supported training predictions. Training witness (People's Republic of China (Q148), diplomatic relation (P530), Guinea-Bissau (Q1007)).
- **Taiwan (Q865)** had leading score 0.871. `P530(X,Q865) <= P463(X,Q656801)` had 148 supported training predictions. Training witness (Guinea-Bissau (Q1007), member of (P463), International Finance Corporation (Q656801)).

### Changing aggregation alone picks the correct answer

`test:37:tail` · (Carl Orff (Q44086), country of citizenship (P27), ?). The benchmark independently verifies the native top as false.

The held-out answer is **German Empire (Q43287)**.

| Ranking | First answer |
| --- | --- |
| native | United States of America (Q30) |
| reweighted maxplus | United States of America (Q30) |
| native confidence + noisy-or | German Empire (Q43287) |
| reweighted + noisy-or | German Empire (Q43287) |

- **German Empire (Q43287)** had leading score 0.467. `P27(X,Q43287) <= P27(X,Q7318)` had 7 supported training predictions. Training witness (Carl Orff (Q44086), country of citizenship (P27), Nazi Germany (Q7318)).
- **United States of America (Q30)** had leading score 0.616. `P27(X,Q30) <= P106(X,Q639669)` had 274 supported training predictions. Training witness (Carl Orff (Q44086), occupation (P106), musician (Q639669)).

### Changing rule weights alone picks the correct answer

`test:1788:head` · (?, residence (P551), Berlin (Q64)). The native top misses this target. The hard-negative file does not label that candidate.

The held-out answer is **Angela Merkel (Q567)**.

| Ranking | First answer |
| --- | --- |
| native | Wilhelm von Humboldt (Q77888) |
| reweighted maxplus | Angela Merkel (Q567) |
| native confidence + noisy-or | Wilhelm von Humboldt (Q77888) |
| reweighted + noisy-or | Angela Merkel (Q567) |

- **Angela Merkel (Q567)** had leading score 0.182. `P551(Q567,Y) <= P17(Y,Q7318)` had 2 supported training predictions. Training witness (Berlin (Q64), country (P17), Nazi Germany (Q7318)).
- **Wilhelm von Humboldt (Q77888)** had leading score 0.222. `P551(X,Y) <= P3373(X,A), P19(A,Y)` had 4 supported training predictions. Training witness (Wilhelm von Humboldt (Q77888), sibling (P3373), Alexander von Humboldt (Q6694)) · (Alexander von Humboldt (Q6694), place of birth (P19), Berlin (Q64)).

## Scope

The experiment separates changes to confidence from changes to aggregation while holding rule applicability fixed. The two mechanisms can act on the same query, and a tested reranker’s gains and losses cannot assign a unique cause to every miss. This is a follow-up on the previously examined CoDEx-S test split.

Reproduce from the project root with the existing frozen rules, saved rankings, and the English labels cached by the query evidence analysis.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .backend-venv/bin/python -m kgc.research.rule_error_diagnosis
```
