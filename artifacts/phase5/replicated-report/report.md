# Phase 5: controlled graph-structure comparison

Exploratory CoDEx-S follow-up. The test set has been inspected repeatedly. Fresh contemporaneous original-graph controls are retrained under the same recipe/budget; established earlier results remain preserved.

The native loader explicitly registers the original training token order before loading modified positive edges. This preserves the candidate vocabulary and internal-ID tie order even when a relation loses every edge; removed and held-out facts are not inserted. The original implicit-index frozen attempt failed on absent relation P840 and is preserved under each condition's attempts directory. Confidence smoothing, weights, maxplus and frequency ties are unchanged.

## Execution

| condition | component | status |
| --- | --- | --- |
| original | neural-0 | complete |
| original | neural-1 | complete |
| original | neural-2 | complete |
| original | rules-0 | complete |
| original | rules-1 | complete |
| random_global | neural-0 | complete |
| random_global | neural-1 | complete |
| random_global | neural-2 | complete |
| random_global | rules-0 | complete |
| random_global | rules-1 | complete |
| random_relation_stratified | neural-0 | complete |
| random_relation_stratified | neural-1 | complete |
| random_relation_stratified | neural-2 | complete |
| random_relation_stratified | rules-0 | complete |
| random_relation_stratified | rules-1 | complete |
| targeted_local | neural-0 | complete |
| targeted_local | neural-1 | complete |
| targeted_local | neural-2 | complete |
| targeted_local | rules-0 | complete |
| targeted_local | rules-1 | complete |
| targeted_relation_matched_control | neural-0 | complete |
| targeted_relation_matched_control | neural-1 | complete |
| targeted_relation_matched_control | neural-2 | complete |
| targeted_relation_matched_control | rules-0 | complete |
| targeted_relation_matched_control | rules-1 | complete |

## Frozen-family execution

| condition | family | status |
| --- | --- | --- |
| original | general | complete |
| original | constants | complete |
| random_global | general | complete |
| random_global | constants | complete |
| random_relation_stratified | general | complete |
| random_relation_stratified | constants | complete |
| targeted_local | general | complete |
| targeted_local | constants | complete |
| targeted_relation_matched_control | general | complete |
| targeted_relation_matched_control | constants | complete |

Frozen families are separate fixed-catalog evidence interventions on the same held-out queries. Their query rows are not additional independent observations or learning realizations. An extension manifest adds families without rewriting the base protocol.

## Overall paired inputs

| condition | backend | replicate | n_queries | hits_metric_status | hits1 | hits10 | mrr_exact | coverage | correct_answer_generation_coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| original | ComplEx validation-best | 0 | 3656 | exact | 0.3556 | 0.6403 | 0.4514 | 1.0000 | n/a |
| original | ComplEx fixed-updates | 0 | 3656 | exact | 0.3548 | 0.6338 | 0.4508 | 1.0000 | n/a |
| original | ComplEx last-epoch | 0 | 3656 | exact | 0.3556 | 0.6403 | 0.4514 | 1.0000 | n/a |
| original | ComplEx validation-best | 1 | 3656 | exact | 0.3578 | 0.6403 | 0.4564 | 1.0000 | n/a |
| original | ComplEx fixed-updates | 1 | 3656 | exact | 0.3479 | 0.6425 | 0.4480 | 1.0000 | n/a |
| original | ComplEx last-epoch | 1 | 3656 | exact | 0.3509 | 0.6409 | 0.4498 | 1.0000 | n/a |
| original | ComplEx validation-best | 2 | 3656 | exact | 0.3556 | 0.6406 | 0.4528 | 1.0000 | n/a |
| original | ComplEx fixed-updates | 2 | 3656 | exact | 0.3537 | 0.6392 | 0.4515 | 1.0000 | n/a |
| original | ComplEx last-epoch | 2 | 3656 | exact | 0.3556 | 0.6406 | 0.4528 | 1.0000 | n/a |
| original | AnyBURL all | 0 | 3656 | exact | 0.3411 | 0.6231 | n/a | 0.9989 | 0.9984 |
| original | AnyBURL general | 0 | 3656 | exact | 0.2683 | 0.5295 | n/a | 0.9986 | 0.9978 |
| original | AnyBURL constants | 0 | 3656 | exact | 0.3203 | 0.6182 | n/a | 0.9975 | 0.9869 |
| original | AnyBURL all | 1 | 3656 | exact | 0.3408 | 0.6242 | n/a | 0.9989 | 0.9978 |
| original | AnyBURL general | 1 | 3656 | exact | 0.2732 | 0.5284 | n/a | 0.9989 | 0.9973 |
| original | AnyBURL constants | 1 | 3656 | exact | 0.3197 | 0.6198 | n/a | 0.9975 | 0.9869 |
| original | Frozen general | 0 | 3656 | exact | 0.2749 | 0.5271 | n/a | 0.9989 | 0.9973 |
| original | Frozen constants | 0 | 3656 | exact | 0.3206 | 0.6187 | n/a | 0.9975 | 0.9869 |
| random_global | ComplEx validation-best | 0 | 3656 | exact | 0.3312 | 0.6190 | 0.4289 | 1.0000 | n/a |
| random_global | ComplEx fixed-updates | 0 | 3656 | exact | 0.3154 | 0.6143 | 0.4156 | 1.0000 | n/a |
| random_global | ComplEx last-epoch | 0 | 3656 | exact | 0.3154 | 0.6143 | 0.4156 | 1.0000 | n/a |
| random_global | ComplEx validation-best | 1 | 3656 | exact | 0.3206 | 0.6277 | 0.4233 | 1.0000 | n/a |
| random_global | ComplEx fixed-updates | 1 | 3656 | exact | 0.3042 | 0.6288 | 0.4119 | 1.0000 | n/a |
| random_global | ComplEx last-epoch | 1 | 3656 | exact | 0.3042 | 0.6288 | 0.4119 | 1.0000 | n/a |
| random_global | ComplEx validation-best | 2 | 3656 | exact | 0.3225 | 0.6201 | 0.4216 | 1.0000 | n/a |
| random_global | ComplEx fixed-updates | 2 | 3656 | exact | 0.3118 | 0.6214 | 0.4163 | 1.0000 | n/a |
| random_global | ComplEx last-epoch | 2 | 3656 | exact | 0.3118 | 0.6214 | 0.4163 | 1.0000 | n/a |
| random_global | AnyBURL all | 0 | 3656 | exact | 0.3187 | 0.6048 | n/a | 0.9992 | 0.9984 |
| random_global | AnyBURL general | 0 | 3656 | exact | 0.2650 | 0.5189 | n/a | 0.9992 | 0.9978 |
| random_global | AnyBURL constants | 0 | 3656 | exact | 0.2875 | 0.5990 | n/a | 0.9967 | 0.9869 |
| random_global | AnyBURL all | 1 | 3656 | exact | 0.3184 | 0.6042 | n/a | 0.9989 | 0.9978 |
| random_global | AnyBURL general | 1 | 3656 | exact | 0.2691 | 0.5170 | n/a | 0.9989 | 0.9978 |
| random_global | AnyBURL constants | 1 | 3656 | exact | 0.2875 | 0.5976 | n/a | 0.9967 | 0.9869 |
| random_global | Frozen general | 0 | 3656 | exact | 0.2653 | 0.5164 | n/a | 0.9989 | 0.9973 |
| random_global | Frozen constants | 0 | 3656 | exact | 0.3167 | 0.6111 | n/a | 0.9975 | 0.9869 |
| random_relation_stratified | ComplEx validation-best | 0 | 3656 | exact | 0.3219 | 0.6217 | 0.4241 | 1.0000 | n/a |
| random_relation_stratified | ComplEx fixed-updates | 0 | 3656 | exact | 0.3066 | 0.6162 | 0.4124 | 1.0000 | n/a |
| random_relation_stratified | ComplEx last-epoch | 0 | 3656 | exact | 0.3066 | 0.6162 | 0.4124 | 1.0000 | n/a |
| random_relation_stratified | ComplEx validation-best | 1 | 3656 | exact | 0.3266 | 0.6234 | 0.4274 | 1.0000 | n/a |
| random_relation_stratified | ComplEx fixed-updates | 1 | 3656 | exact | 0.3077 | 0.6201 | 0.4132 | 1.0000 | n/a |
| random_relation_stratified | ComplEx last-epoch | 1 | 3656 | exact | 0.3077 | 0.6201 | 0.4132 | 1.0000 | n/a |
| random_relation_stratified | ComplEx validation-best | 2 | 3656 | exact | 0.3236 | 0.6190 | 0.4242 | 1.0000 | n/a |
| random_relation_stratified | ComplEx fixed-updates | 2 | 3656 | exact | 0.2962 | 0.6195 | 0.4075 | 1.0000 | n/a |
| random_relation_stratified | ComplEx last-epoch | 2 | 3656 | exact | 0.2962 | 0.6195 | 0.4075 | 1.0000 | n/a |
| random_relation_stratified | AnyBURL all | 0 | 3656 | exact | 0.3132 | 0.6015 | n/a | 0.9989 | 0.9973 |
| random_relation_stratified | AnyBURL general | 0 | 3656 | exact | 0.2705 | 0.5142 | n/a | 0.9986 | 0.9967 |
| random_relation_stratified | AnyBURL constants | 0 | 3656 | exact | 0.2793 | 0.5916 | n/a | 0.9975 | 0.9869 |
| random_relation_stratified | AnyBURL all | 1 | 3656 | exact | 0.3137 | 0.6023 | n/a | 0.9989 | 0.9978 |
| random_relation_stratified | AnyBURL general | 1 | 3656 | exact | 0.2637 | 0.5118 | n/a | 0.9989 | 0.9967 |
| random_relation_stratified | AnyBURL constants | 1 | 3656 | exact | 0.2787 | 0.5894 | n/a | 0.9975 | 0.9869 |
| random_relation_stratified | Frozen general | 0 | 3656 | exact | 0.2623 | 0.5153 | n/a | 0.9989 | 0.9973 |
| random_relation_stratified | Frozen constants | 0 | 3656 | exact | 0.3083 | 0.6072 | n/a | 0.9975 | 0.9869 |
| targeted_local | ComplEx validation-best | 0 | 3656 | exact | 0.3288 | 0.6119 | 0.4245 | 1.0000 | n/a |
| targeted_local | ComplEx fixed-updates | 0 | 3656 | exact | 0.3173 | 0.6083 | 0.4165 | 1.0000 | n/a |
| targeted_local | ComplEx last-epoch | 0 | 3656 | exact | 0.3173 | 0.6083 | 0.4165 | 1.0000 | n/a |
| targeted_local | ComplEx validation-best | 1 | 3656 | exact | 0.3260 | 0.6217 | 0.4279 | 1.0000 | n/a |
| targeted_local | ComplEx fixed-updates | 1 | 3656 | exact | 0.3181 | 0.6231 | 0.4224 | 1.0000 | n/a |
| targeted_local | ComplEx last-epoch | 1 | 3656 | exact | 0.3181 | 0.6231 | 0.4224 | 1.0000 | n/a |
| targeted_local | ComplEx validation-best | 2 | 3656 | exact | 0.3301 | 0.6080 | 0.4235 | 1.0000 | n/a |
| targeted_local | ComplEx fixed-updates | 2 | 3656 | exact | 0.3274 | 0.6097 | 0.4232 | 1.0000 | n/a |
| targeted_local | ComplEx last-epoch | 2 | 3656 | exact | 0.3274 | 0.6097 | 0.4232 | 1.0000 | n/a |
| targeted_local | AnyBURL all | 0 | 3656 | exact | 0.3113 | 0.6018 | n/a | 0.9989 | 0.9973 |
| targeted_local | AnyBURL general | 0 | 3656 | exact | 0.2609 | 0.5085 | n/a | 0.9989 | 0.9962 |
| targeted_local | AnyBURL constants | 0 | 3656 | exact | 0.2913 | 0.5922 | n/a | 0.9975 | 0.9869 |
| targeted_local | AnyBURL all | 1 | 3656 | exact | 0.3135 | 0.6072 | n/a | 0.9992 | 0.9973 |
| targeted_local | AnyBURL general | 1 | 3656 | exact | 0.2626 | 0.5112 | n/a | 0.9992 | 0.9962 |
| targeted_local | AnyBURL constants | 1 | 3656 | exact | 0.2916 | 0.5935 | n/a | 0.9975 | 0.9869 |
| targeted_local | Frozen general | 0 | 3656 | exact | 0.2577 | 0.5175 | n/a | 0.9989 | 0.9973 |
| targeted_local | Frozen constants | 0 | 3656 | exact | 0.3151 | 0.6119 | n/a | 0.9975 | 0.9869 |
| targeted_relation_matched_control | ComplEx validation-best | 0 | 3656 | exact | 0.3187 | 0.6154 | 0.4182 | 1.0000 | n/a |
| targeted_relation_matched_control | ComplEx fixed-updates | 0 | 3656 | exact | 0.3187 | 0.6154 | 0.4182 | 1.0000 | n/a |
| targeted_relation_matched_control | ComplEx last-epoch | 0 | 3656 | exact | 0.3187 | 0.6154 | 0.4182 | 1.0000 | n/a |
| targeted_relation_matched_control | ComplEx validation-best | 1 | 3656 | exact | 0.3277 | 0.6231 | 0.4266 | 1.0000 | n/a |
| targeted_relation_matched_control | ComplEx fixed-updates | 1 | 3656 | exact | 0.3066 | 0.6190 | 0.4130 | 1.0000 | n/a |
| targeted_relation_matched_control | ComplEx last-epoch | 1 | 3656 | exact | 0.3066 | 0.6190 | 0.4130 | 1.0000 | n/a |
| targeted_relation_matched_control | ComplEx validation-best | 2 | 3656 | exact | 0.3403 | 0.6214 | 0.4333 | 1.0000 | n/a |
| targeted_relation_matched_control | ComplEx fixed-updates | 2 | 3656 | exact | 0.3219 | 0.6253 | 0.4222 | 1.0000 | n/a |
| targeted_relation_matched_control | ComplEx last-epoch | 2 | 3656 | exact | 0.3219 | 0.6253 | 0.4222 | 1.0000 | n/a |
| targeted_relation_matched_control | AnyBURL all | 0 | 3656 | exact | 0.3135 | 0.6015 | n/a | 0.9989 | 0.9978 |
| targeted_relation_matched_control | AnyBURL general | 0 | 3656 | exact | 0.2492 | 0.5134 | n/a | 0.9989 | 0.9973 |
| targeted_relation_matched_control | AnyBURL constants | 0 | 3656 | exact | 0.2853 | 0.5952 | n/a | 0.9975 | 0.9869 |
| targeted_relation_matched_control | AnyBURL all | 1 | 3656 | exact | 0.3126 | 0.5993 | n/a | 0.9989 | 0.9978 |
| targeted_relation_matched_control | AnyBURL general | 1 | 3656 | exact | 0.2607 | 0.5145 | n/a | 0.9989 | 0.9973 |
| targeted_relation_matched_control | AnyBURL constants | 1 | 3656 | exact | 0.2828 | 0.5922 | n/a | 0.9975 | 0.9869 |
| targeted_relation_matched_control | Frozen general | 0 | 3656 | exact | 0.2604 | 0.5109 | n/a | 0.9989 | 0.9973 |
| targeted_relation_matched_control | Frozen constants | 0 | 3656 | exact | 0.3137 | 0.6111 | n/a | 0.9975 | 0.9869 |

Rule Hits use the native supported-candidate order, with abstentions counted as misses. They are not full-universe zero-score tie rankings. If any native family cannot be certified, that row and its paired differences remain retrieved-list outcomes; bootstrap intervals do not resolve censoring. Exact full-universe rule MRR is never reported.

## Intervention minus matched control

Negative differences indicate degradation.

| treatment | control | backend | difference | ci_low | ci_high | all_rankings_certified | n_unique_queries | n_triples |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random_global | original | embedding:fixed-updates | -0.0417 | -0.0522 | -0.0317 | True | 3656 | 1828 |
| random_global | original | embedding:last-epoch | -0.0436 | -0.0547 | -0.0333 | True | 3656 | 1828 |
| random_global | original | embedding:validation-best | -0.0315 | -0.0436 | -0.0204 | True | 3656 | 1828 |
| random_global | original | frozen:constants | -0.0038 | -0.0093 | 0.0016 | True | 3656 | 1828 |
| random_global | original | frozen:general | -0.0096 | -0.0172 | -0.0016 | True | 3656 | 1828 |
| random_global | original | rules:all | -0.0224 | -0.0315 | -0.0131 | True | 3656 | 1828 |
| random_global | original | rules:constants | -0.0325 | -0.0424 | -0.0226 | True | 3656 | 1828 |
| random_global | original | rules:general | -0.0037 | -0.0140 | 0.0064 | True | 3656 | 1828 |
| random_relation_stratified | original | embedding:fixed-updates | -0.0486 | -0.0616 | -0.0342 | True | 3656 | 1828 |
| random_relation_stratified | original | embedding:last-epoch | -0.0505 | -0.0628 | -0.0377 | True | 3656 | 1828 |
| random_relation_stratified | original | embedding:validation-best | -0.0323 | -0.0414 | -0.0224 | True | 3656 | 1828 |
| random_relation_stratified | original | frozen:constants | -0.0123 | -0.0178 | -0.0066 | True | 3656 | 1828 |
| random_relation_stratified | original | frozen:general | -0.0126 | -0.0211 | -0.0038 | True | 3656 | 1828 |
| random_relation_stratified | original | rules:all | -0.0275 | -0.0369 | -0.0176 | True | 3656 | 1828 |
| random_relation_stratified | original | rules:constants | -0.0410 | -0.0514 | -0.0298 | True | 3656 | 1828 |
| random_relation_stratified | original | rules:general | -0.0037 | -0.0139 | 0.0071 | True | 3656 | 1828 |
| targeted_local | original | embedding:fixed-updates | -0.0312 | -0.0428 | -0.0205 | True | 3656 | 1828 |
| targeted_local | original | embedding:last-epoch | -0.0331 | -0.0440 | -0.0227 | True | 3656 | 1828 |
| targeted_local | original | embedding:validation-best | -0.0280 | -0.0375 | -0.0181 | True | 3656 | 1828 |
| targeted_local | original | frozen:constants | -0.0055 | -0.0104 | -0.0003 | True | 3656 | 1828 |
| targeted_local | original | frozen:general | -0.0172 | -0.0254 | -0.0093 | True | 3656 | 1828 |
| targeted_local | original | rules:all | -0.0286 | -0.0386 | -0.0186 | True | 3656 | 1828 |
| targeted_local | original | rules:constants | -0.0286 | -0.0388 | -0.0183 | True | 3656 | 1828 |
| targeted_local | original | rules:general | -0.0090 | -0.0181 | 0.0011 | True | 3656 | 1828 |
| targeted_relation_matched_control | original | embedding:fixed-updates | -0.0364 | -0.0473 | -0.0257 | True | 3656 | 1828 |
| targeted_relation_matched_control | original | embedding:last-epoch | -0.0383 | -0.0495 | -0.0284 | True | 3656 | 1828 |
| targeted_relation_matched_control | original | embedding:validation-best | -0.0274 | -0.0410 | -0.0138 | True | 3656 | 1828 |
| targeted_relation_matched_control | original | frozen:constants | -0.0068 | -0.0115 | -0.0022 | True | 3656 | 1828 |
| targeted_relation_matched_control | original | frozen:general | -0.0145 | -0.0227 | -0.0074 | True | 3656 | 1828 |
| targeted_relation_matched_control | original | rules:all | -0.0279 | -0.0372 | -0.0186 | True | 3656 | 1828 |
| targeted_relation_matched_control | original | rules:constants | -0.0360 | -0.0458 | -0.0264 | True | 3656 | 1828 |
| targeted_relation_matched_control | original | rules:general | -0.0159 | -0.0291 | -0.0040 | True | 3656 | 1828 |
| targeted_local | targeted_relation_matched_control | embedding:fixed-updates | 0.0052 | -0.0075 | 0.0179 | True | 3656 | 1828 |
| targeted_local | targeted_relation_matched_control | embedding:last-epoch | 0.0052 | -0.0075 | 0.0179 | True | 3656 | 1828 |
| targeted_local | targeted_relation_matched_control | embedding:validation-best | -0.0005 | -0.0137 | 0.0143 | True | 3656 | 1828 |
| targeted_local | targeted_relation_matched_control | frozen:constants | 0.0014 | -0.0052 | 0.0082 | True | 3656 | 1828 |
| targeted_local | targeted_relation_matched_control | frozen:general | -0.0027 | -0.0129 | 0.0071 | True | 3656 | 1828 |
| targeted_local | targeted_relation_matched_control | rules:all | -0.0007 | -0.0120 | 0.0120 | True | 3656 | 1828 |
| targeted_local | targeted_relation_matched_control | rules:constants | 0.0074 | -0.0049 | 0.0192 | True | 3656 | 1828 |
| targeted_local | targeted_relation_matched_control | rules:general | 0.0068 | -0.0052 | 0.0217 | True | 3656 | 1828 |

## Change in relative neural–rule gap

Positive values mean the neural-minus-rule Hits@1 gap increased; negative values mean it decreased. Neither sign alone establishes that either model improved.

| treatment | control | difference | ci_low | ci_high | rule_rankings_certified | n_neural_seeds | n_treatment_miners | n_control_miners |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random_global | original | -0.0091 | -0.0223 | 0.0034 | True | 3 | 2 | 2 |
| random_relation_stratified | original | -0.0048 | -0.0170 | 0.0073 | True | 3 | 2 | 2 |
| targeted_local | original | 0.0006 | -0.0120 | 0.0126 | True | 3 | 2 | 2 |
| targeted_relation_matched_control | original | 0.0005 | -0.0155 | 0.0153 | True | 3 | 2 | 2 |
| targeted_local | targeted_relation_matched_control | 0.0001 | -0.0152 | 0.0144 | True | 3 | 2 | 2 |

## Paired frozen-family gap

This separate diagnostic estimates [(general Hits@1 − constant Hits@1) in the treatment graph] − [the same family gap in the control graph]. Positive values favor general rules in relative sensitivity; either family may still degrade in absolute accuracy. Both families use the same paired held-out queries, clustered by original triple, with no independent model resampling. The sample size is the number of unique directional queries, not the sum of family rows. This is conditional evidence for these fixed subsets and graph draws, not catalog-population or perturbation-population replication, additive prediction credit, or the primary neural–rule comparison.

| treatment | control | difference | ci_low | ci_high | n_unique_queries | n_triples | n_fixed_family_subsets |
| --- | --- | --- | --- | --- | --- | --- | --- |
| random_global | original | -0.0057 | -0.0142 | 0.0027 | 3656 | 1828 | 2 |
| random_relation_stratified | original | -0.0003 | -0.0088 | 0.0090 | 3656 | 1828 | 2 |
| targeted_local | original | -0.0118 | -0.0197 | -0.0038 | 3656 | 1828 | 2 |
| targeted_relation_matched_control | original | -0.0077 | -0.0153 | -0.0005 | 3656 | 1828 | 2 |
| targeted_local | targeted_relation_matched_control | -0.0041 | -0.0134 | 0.0057 | 3656 | 1828 | 2 |

![Performance degradation](degradation.png)

![General and constant rule sensitivity](family-sensitivity.png)

## Resource and optimization controls

| condition | backend | replicate | training_seconds | training_cpu_seconds | best_epoch | completed_epochs | optimizer_updates | effective_training_facts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| original | ComplEx | 0 | 311.3724 | 311.1773 | 40 | 40 | 2600 | 32888 |
| original | ComplEx | 1 | 328.9455 | 328.7592 | 20 | 40 | 2600 | 32888 |
| original | ComplEx | 2 | 321.9430 | 321.5291 | 40 | 40 | 2600 | 32888 |
| original | AnyBURL | 0 | 62.6038 | 66.3164 | n/a | n/a | n/a | n/a |
| original | AnyBURL | 1 | 62.5890 | 65.5441 | n/a | n/a | n/a | n/a |
| random_global | ComplEx | 0 | 258.1835 | 257.9729 | 20 | 40 | 2320 | 29599 |
| random_global | ComplEx | 1 | 236.7426 | 236.5736 | 20 | 40 | 2320 | 29599 |
| random_global | ComplEx | 2 | 239.9774 | 239.8040 | 20 | 40 | 2320 | 29599 |
| random_global | AnyBURL | 0 | 62.5411 | 64.5839 | n/a | n/a | n/a | n/a |
| random_global | AnyBURL | 1 | 62.5778 | 65.4404 | n/a | n/a | n/a | n/a |
| random_relation_stratified | ComplEx | 0 | 237.2910 | 237.1138 | 20 | 40 | 2320 | 29599 |
| random_relation_stratified | ComplEx | 1 | 250.4742 | 250.3112 | 20 | 40 | 2320 | 29599 |
| random_relation_stratified | ComplEx | 2 | 253.2535 | 253.0623 | 20 | 40 | 2320 | 29599 |
| random_relation_stratified | AnyBURL | 0 | 62.5811 | 65.1882 | n/a | n/a | n/a | n/a |
| random_relation_stratified | AnyBURL | 1 | 62.6327 | 67.0754 | n/a | n/a | n/a | n/a |
| targeted_local | ComplEx | 0 | 311.0738 | 310.8990 | 20 | 40 | 2320 | 29599 |
| targeted_local | ComplEx | 1 | 341.6221 | 341.4252 | 20 | 40 | 2320 | 29599 |
| targeted_local | ComplEx | 2 | 363.4760 | 363.2807 | 20 | 40 | 2320 | 29599 |
| targeted_local | AnyBURL | 0 | 62.8181 | 67.3423 | n/a | n/a | n/a | n/a |
| targeted_local | AnyBURL | 1 | 62.7605 | 67.8865 | n/a | n/a | n/a | n/a |
| targeted_relation_matched_control | ComplEx | 0 | 320.0143 | 319.8165 | 40 | 40 | 2320 | 29599 |
| targeted_relation_matched_control | ComplEx | 1 | 328.0834 | 327.9202 | 10 | 40 | 2320 | 29599 |
| targeted_relation_matched_control | ComplEx | 2 | 333.3318 | 333.1216 | 20 | 40 | 2320 | 29599 |
| targeted_relation_matched_control | AnyBURL | 0 | 62.7309 | 66.5769 | n/a | n/a | n/a | n/a |
| targeted_relation_matched_control | AnyBURL | 1 | 62.6363 | 67.0481 | n/a | n/a | n/a | n/a |

The same 40-epoch ceiling/checkpoints and validation selection apply to each primary graph. Removal changes 65 to 58 optimizer updates per epoch. A predeclared checkpoint at 2,320 updates adds an equal-update diagnostic; last-epoch outputs separate validation stopping effects. Neither diagnostic is tuned on test outcomes. Smoke uses a one-epoch analogue. Training resource counters cover committed epochs, excluding cooling and validation; discarded partial-epoch work is not included. Native application wall times can include cooling and metadata loading.

## Rule inventory and application resources

| condition | backend | replicate | catalog_rule_count | native_loaded_count | application_cpu_seconds | application_seconds_including_loading_and_cooling |
| --- | --- | --- | --- | --- | --- | --- |
| original | AnyBURL all | 0 | 462153 | 462153 | 171.0509 | 171.1399 |
| original | AnyBURL general | 0 | 1794 | 1794 | 30.1293 | 30.2056 |
| original | AnyBURL constants | 0 | 460289 | 460289 | 155.1379 | 155.2480 |
| original | AnyBURL all | 1 | 448719 | 448719 | 141.7776 | 141.8818 |
| original | AnyBURL general | 1 | 2053 | 2053 | 29.6084 | 29.6781 |
| original | AnyBURL constants | 1 | 446596 | 446596 | 147.9472 | 148.0339 |
| original | Frozen general | 0 | 2249 | 2249 | 30.2233 | 30.2927 |
| original | Frozen constants | 0 | 467989 | 467989 | 210.8176 | 211.0469 |
| random_global | AnyBURL all | 0 | 404377 | 404377 | 140.1138 | 140.2121 |
| random_global | AnyBURL general | 0 | 1793 | 1793 | 26.6784 | 26.7426 |
| random_global | AnyBURL constants | 0 | 402519 | 402519 | 130.9184 | 131.0340 |
| random_global | AnyBURL all | 1 | 457338 | 457338 | 147.4801 | 147.5700 |
| random_global | AnyBURL general | 1 | 1907 | 1907 | 26.3331 | 26.3942 |
| random_global | AnyBURL constants | 1 | 455366 | 455366 | 141.9964 | 142.0741 |
| random_global | Frozen general | 0 | 2249 | 2249 | 26.9680 | 27.0305 |
| random_global | Frozen constants | 0 | 467989 | 467989 | 162.7369 | 162.8520 |
| random_relation_stratified | AnyBURL all | 0 | 436840 | 436840 | 222.7452 | 222.9324 |
| random_relation_stratified | AnyBURL general | 0 | 1779 | 1779 | 28.8942 | 28.9942 |
| random_relation_stratified | AnyBURL constants | 0 | 434996 | 434996 | 201.7828 | 201.9196 |
| random_relation_stratified | AnyBURL all | 1 | 290545 | 290545 | 160.5063 | 160.7132 |
| random_relation_stratified | AnyBURL general | 1 | 1650 | 1650 | 31.4362 | 31.5564 |
| random_relation_stratified | AnyBURL constants | 1 | 288830 | 288830 | 140.4494 | 140.5779 |
| random_relation_stratified | Frozen general | 0 | 2249 | 2249 | 29.9499 | 30.0591 |
| random_relation_stratified | Frozen constants | 0 | 467989 | 467989 | 172.1061 | 172.2508 |
| targeted_local | AnyBURL all | 0 | 324874 | 324874 | 166.1810 | 166.3403 |
| targeted_local | AnyBURL general | 0 | 1523 | 1523 | 42.5593 | 42.6698 |
| targeted_local | AnyBURL constants | 0 | 323289 | 323289 | 145.3707 | 145.4988 |
| targeted_local | AnyBURL all | 1 | 373465 | 373465 | 196.1764 | 196.3331 |
| targeted_local | AnyBURL general | 1 | 1490 | 1490 | 33.6708 | 33.7680 |
| targeted_local | AnyBURL constants | 1 | 371913 | 371913 | 173.9770 | 174.3551 |
| targeted_local | Frozen general | 0 | 2249 | 2249 | 40.9061 | 41.0647 |
| targeted_local | Frozen constants | 0 | 467989 | 467989 | 162.9400 | 163.0983 |
| targeted_relation_matched_control | AnyBURL all | 0 | 260989 | 260989 | 145.2820 | 145.4338 |
| targeted_relation_matched_control | AnyBURL general | 0 | 1865 | 1865 | 42.0963 | 42.2684 |
| targeted_relation_matched_control | AnyBURL constants | 0 | 259060 | 259060 | 142.7539 | 142.8709 |
| targeted_relation_matched_control | AnyBURL all | 1 | 314791 | 314791 | 166.9205 | 167.0982 |
| targeted_relation_matched_control | AnyBURL general | 1 | 2224 | 2224 | 32.1252 | 32.2400 |
| targeted_relation_matched_control | AnyBURL constants | 1 | 312503 | 312503 | 136.0416 | 136.2385 |
| targeted_relation_matched_control | Frozen general | 0 | 2249 | 2249 | 33.4324 | 33.5121 |
| targeted_relation_matched_control | Frozen constants | 0 | 467989 | 467989 | 199.9554 | 200.5384 |

CPU and wall application times include loading/scoring; wall time also includes deliberate cooling. Mining wall budgets do not guarantee identical CPU use, sampling throughput or learned inventories. Parsing/catalog export has no separate end-to-end resource counter.

| condition | native_family | body_length | n_rules | application_complete | median_raw_confidence | median_raw_support |
| --- | --- | --- | --- | --- | --- | --- |
| original | B | 1 | 70 | True | 0.0370 | 3.5000 |
| original | B | 2 | 614 | True | 0.1084 | 4.0000 |
| original | B | 3 | 1110 | True | 0.1189 | 26.0000 |
| original | Uc | 1 | 436995 | True | 0.4167 | 4.0000 |
| original | Ud | 1 | 23294 | True | 0.0415 | 4.0000 |
| original | Z | 0 | 70 | True | 0.0307 | 166.5000 |
| original | B | 1 | 70 | True | 0.0427 | 4.0000 |
| original | B | 2 | 697 | True | 0.0930 | 4.0000 |
| original | B | 3 | 1286 | True | 0.1114 | 23.0000 |
| original | Uc | 1 | 423335 | True | 0.4167 | 4.0000 |
| original | Ud | 1 | 23261 | True | 0.0415 | 4.0000 |
| original | Z | 0 | 70 | True | 0.0307 | 166.5000 |
| random_global | B | 1 | 61 | True | 0.0606 | 4.0000 |
| random_global | B | 2 | 649 | True | 0.1026 | 4.0000 |
| random_global | B | 3 | 1083 | True | 0.1022 | 21.0000 |
| random_global | Uc | 1 | 381320 | True | 0.4000 | 4.0000 |
| random_global | Ud | 1 | 21199 | True | 0.0408 | 4.0000 |
| random_global | Z | 0 | 65 | True | 0.0316 | 155.0000 |
| random_global | B | 1 | 65 | True | 0.0476 | 3.0000 |
| random_global | B | 2 | 603 | True | 0.1154 | 4.0000 |
| random_global | B | 3 | 1239 | True | 0.0985 | 20.0000 |
| random_global | Uc | 1 | 433823 | True | 0.4000 | 4.0000 |
| random_global | Ud | 1 | 21543 | True | 0.0412 | 4.0000 |
| random_global | Z | 0 | 65 | True | 0.0316 | 155.0000 |
| random_relation_stratified | B | 1 | 61 | True | 0.0508 | 4.0000 |
| random_relation_stratified | B | 2 | 582 | True | 0.0984 | 4.0000 |
| random_relation_stratified | B | 3 | 1136 | True | 0.0951 | 22.0000 |
| random_relation_stratified | Uc | 1 | 413664 | True | 0.4000 | 4.0000 |
| random_relation_stratified | Ud | 1 | 21332 | True | 0.0426 | 4.0000 |
| random_relation_stratified | Z | 0 | 65 | True | 0.0312 | 156.0000 |
| random_relation_stratified | B | 1 | 64 | True | 0.0435 | 3.0000 |
| random_relation_stratified | B | 2 | 609 | True | 0.0909 | 4.0000 |
| random_relation_stratified | B | 3 | 977 | True | 0.1117 | 25.0000 |
| random_relation_stratified | Uc | 1 | 268689 | True | 0.4000 | 4.0000 |
| random_relation_stratified | Ud | 1 | 20141 | True | 0.0426 | 5.0000 |
| random_relation_stratified | Z | 0 | 65 | True | 0.0312 | 156.0000 |
| targeted_local | B | 1 | 73 | True | 0.0282 | 3.0000 |
| targeted_local | B | 2 | 553 | True | 0.1254 | 4.0000 |
| targeted_local | B | 3 | 897 | True | 0.0948 | 28.0000 |
| targeted_local | Uc | 1 | 302952 | True | 0.4000 | 4.0000 |
| targeted_local | Ud | 1 | 20337 | True | 0.0426 | 5.0000 |
| targeted_local | Z | 0 | 62 | True | 0.0321 | 161.0000 |
| targeted_local | B | 1 | 66 | True | 0.0372 | 3.0000 |
| targeted_local | B | 2 | 588 | True | 0.1096 | 4.0000 |
| targeted_local | B | 3 | 836 | True | 0.1014 | 31.0000 |
| targeted_local | Uc | 1 | 351137 | True | 0.4000 | 4.0000 |
| targeted_local | Ud | 1 | 20776 | True | 0.0426 | 4.0000 |
| targeted_local | Z | 0 | 62 | True | 0.0321 | 161.0000 |
| targeted_relation_matched_control | B | 1 | 58 | True | 0.0478 | 3.5000 |
| targeted_relation_matched_control | B | 2 | 541 | True | 0.1176 | 4.0000 |
| targeted_relation_matched_control | B | 3 | 1266 | True | 0.0954 | 19.0000 |
| targeted_relation_matched_control | Uc | 1 | 239640 | True | 0.4000 | 4.0000 |
| targeted_relation_matched_control | Ud | 1 | 19420 | True | 0.0435 | 5.0000 |
| targeted_relation_matched_control | Z | 0 | 64 | True | 0.0313 | 155.0000 |
| targeted_relation_matched_control | B | 1 | 64 | True | 0.0339 | 3.0000 |
| targeted_relation_matched_control | B | 2 | 631 | True | 0.0870 | 4.0000 |
| targeted_relation_matched_control | B | 3 | 1529 | True | 0.0899 | 17.0000 |
| targeted_relation_matched_control | Uc | 1 | 292406 | True | 0.4000 | 4.0000 |
| targeted_relation_matched_control | Ud | 1 | 20097 | True | 0.0433 | 5.0000 |
| targeted_relation_matched_control | Z | 0 | 64 | True | 0.0313 | 155.0000 |

`rule-statistics.csv` stores full 0/25/50/75/100 percentiles, and `rule-inventory-summary.csv` exposes interquartile statistics. Inventories from completed mining may be shown even when application is incomplete; they carry no claimed prediction result. These are raw learned-rule confidence/support, not calibrated probabilities; native smoothing and family weights remain those recorded in each application. Inventory size alone is not predictive contribution.

## Hypotheses, controls and confounds

| hypothesis | intervention | control | measurement | confounds |
| --- | --- | --- | --- | --- |
| H1 | 90% removal | fresh original graph | paired accuracy/gap/coverage and fixed-update sensitivity | fewer examples, gradient updates, validation selection, mining stochasticity |
| H2 | same frozen B catalog applied to missing-edge graphs | same catalog on original | candidate/gold-support losses, witnessed groundings lost | native frequency ties and binding constraints; raw typed walks are a structural proxy |
| H3 | fresh constant-rule learning/application on each graph | fresh original constant rules | constant versus general coverage/quality and sampled anchored witnesses | changed inventories/confidence, entity-local frequencies; full frozen-constant evaluation deferred |
| H4 | targeted_local | targeted_relation_matched_control | paired outcomes, difference in embedding-rule gap and paths | single target/removal draw; degree/entity distributions intentionally differ; independent miner samples |
| H5 | same removal conditions | same test facts/original-graph strata | original known-node degree/frequency strata and target incidence | observational effect heterogeneity, graph dependence, repeated CoDEx-S inspection |

## Current evidential status

| question | status | boundary |
| --- | --- | --- |
| H1: differential sensitivity to removal | bounded paired matrix complete | declared 3 neural seeds and 2 miners per graph; singleton factors cannot estimate learning variability; fixed-update outputs address only one optimization confound |
| H2: general-rule body evidence | frozen-catalog intervention complete | candidate-pair support losses are measured; sampled groundings are separate; ranking also uses graph-frequency ties |
| H3: constant versus general rules | fresh family comparisons available; frozen general/constants comparisons complete | frozen-family evidence availability is measured separately from fresh learning; fixed-catalog differences do not replace the fresh-learning comparison or give an additive causal decomposition |
| H4: targeted versus relation-matched removal | paired primary comparison available | exact relation totals matched; endpoint frequencies, degrees and paths jointly change; one removal draw |
| H5: query characteristics and robustness | exploratory strata available | strata use original train-observable features; no causal mediation or deployment selector established |

## Evidence intervention versus retraining

Frozen-family results reapply subsets of the established original catalog with original confidence/support on modified training facts. General rules are variable-only relational implications; the constant subset contains constant-bearing conditional implications and excludes unconditional zero-body entity priors. This is not re-mining and does not replace the primary rule baseline. Native training-frequency tie breaking changes with the graph, so ranking changes cannot all be attributed to missing bodies. The catalog also differs from the fresh primary original inventory; primary/secondary differences and differences between families are not an additive causal decomposition. Gold-support disappearance is inferred separately by family only where candidate enumeration is certified and its support check is consistent; observed witness loss can occur even when redundant support keeps a prediction available.

## Frozen support checks

Here a lost candidate support means one (directional query, candidate entity) pair is no longer generated by the specified frozen family. These counts are not numbers of rule groundings, learned rules, or the miner's rule-support statistic. Top-1 changes use evaluator-filtered rankings. Sample sizes are reported within family and condition; the same queries appearing across families or conditions are paired observations, not independent replications.

| family | condition | n_unique_queries | n_triples | candidate_supports_lost | queries_losing_candidate_support | certified_gold_support_disappeared | new_candidate_supports | top1_changed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| general | original | 3656 | 1828 | 0 | 0 | 0 | 0 | 0 |
| general | random_global | 3656 | 1828 | 71950 | 3401 | 0 | 0 | 792 |
| general | random_relation_stratified | 3656 | 1828 | 72963 | 3201 | 0 | 0 | 795 |
| general | targeted_local | 3656 | 1828 | 104354 | 3382 | 0 | 0 | 771 |
| general | targeted_relation_matched_control | 3656 | 1828 | 67473 | 3088 | 0 | 0 | 1043 |
| constants | original | 3656 | 1828 | 0 | 0 | 0 | 0 | 0 |
| constants | random_global | 3656 | 1828 | 28082 | 1602 | 0 | 0 | 319 |
| constants | random_relation_stratified | 3656 | 1828 | 27301 | 2300 | 0 | 0 | 398 |
| constants | targeted_local | 3656 | 1828 | 32447 | 2785 | 0 | 0 | 225 |
| constants | targeted_relation_matched_control | 3656 | 1828 | 24799 | 2270 | 0 | 0 | 361 |

No new candidate support was observed under deletions in these frozen-catalog queries. This is consistent with positive-body evidence loss, not a generalization across learned catalogs or graph draws.

A degenerate coverage interval [0, 0] reflects unchanged outcomes in the observed empirical query pairs. It does not establish zero loss probability on unseen queries, other learned catalogs or other perturbation draws.

![Frozen evidence sensitivity](frozen-sensitivity.png)

## Query-level explanations

`query-joins.csv` pairs ranks, coverage, winner changes and original/modified degrees/frequencies for completed fresh-model comparison cells. Forward-directed typed two-/three-hop walk counts follow h → … → t using existing edge directions and permit revisiting entities. They exclude inverse-oriented native rule bodies, such as h ← a → t, and are a restricted structural proxy rather than total relational-path availability or native grounding counts. Truth endpoints/ranks/winner labels are strictly diagnostic. Neural changes are measured sensitivities, not invented explanations of internal representations.

[Fresh-model case studies](cases.md) document sampled training-only witnesses for available completed comparisons; unassessed witness fields remain unknown.

[Frozen-catalog case studies](frozen-cases.md) and `frozen-witnesses.csv` document checked before/after training-edge witnesses for the separate inference-time evidence intervention. They do not establish a retrained embedding response.

[Frozen constant-bearing case studies](frozen-constants-cases.md) provide separately checked conditional-rule witnesses for that fixed family. They do not turn constant-bearing learned implications into unconditional entity-frequency priors.

## Observations and evidential boundaries

| evidence_class | comparison | observation | boundary |
| --- | --- | --- | --- |
| Direct paired observation, conditional learned models | random_global vs original; embedding:validation-best | Certified Hits@1 change -0.0315, conditional 95% interval [-0.0436, -0.0204] | Fresh-training sensitivity; not a universal structural mechanism or replicated causal effect; any censoring persists |
| Direct paired observation, conditional learned models | random_global vs original; rules:all | Certified Hits@1 change -0.0224, conditional 95% interval [-0.0315, -0.0131] | Fresh-training sensitivity; not a universal structural mechanism or replicated causal effect; any censoring persists |
| Direct paired observation, conditional learned models | random_relation_stratified vs original; embedding:validation-best | Certified Hits@1 change -0.0323, conditional 95% interval [-0.0414, -0.0224] | Fresh-training sensitivity; not a universal structural mechanism or replicated causal effect; any censoring persists |
| Direct paired observation, conditional learned models | random_relation_stratified vs original; rules:all | Certified Hits@1 change -0.0275, conditional 95% interval [-0.0369, -0.0176] | Fresh-training sensitivity; not a universal structural mechanism or replicated causal effect; any censoring persists |
| Direct paired observation, conditional learned models | targeted_local vs original; embedding:validation-best | Certified Hits@1 change -0.0280, conditional 95% interval [-0.0375, -0.0181] | Fresh-training sensitivity; not a universal structural mechanism or replicated causal effect; any censoring persists |
| Direct paired observation, conditional learned models | targeted_local vs original; rules:all | Certified Hits@1 change -0.0286, conditional 95% interval [-0.0386, -0.0186] | Fresh-training sensitivity; not a universal structural mechanism or replicated causal effect; any censoring persists |
| Direct paired observation, conditional learned models | targeted_relation_matched_control vs original; embedding:validation-best | Certified Hits@1 change -0.0274, conditional 95% interval [-0.0410, -0.0138] | Fresh-training sensitivity; not a universal structural mechanism or replicated causal effect; any censoring persists |
| Direct paired observation, conditional learned models | targeted_relation_matched_control vs original; rules:all | Certified Hits@1 change -0.0279, conditional 95% interval [-0.0372, -0.0186] | Fresh-training sensitivity; not a universal structural mechanism or replicated causal effect; any censoring persists |
| Controlled inference-time graph intervention | random_global vs original; fixed constant-bearing conditional catalog | Hits@1 change -0.0038, conditional 95% interval [-0.0093, +0.0016] | Ranking responds to missing supports and native graph-frequency ties; this does not isolate their separate contributions; any uncertified ranking remains censored |
| Controlled inference-time evidence intervention | random_global vs original; fixed constant-bearing conditional catalog | Gold-generation coverage change +0.0000, conditional 95% interval [+0.0000, +0.0000] | Fixed implications, analyzed within family; no catalog/perturbation population replication or additive decomposition; uncertified generation outcomes remain observed retrievals |
| Controlled inference-time graph intervention | random_global vs original; fixed general catalog | Hits@1 change -0.0096, conditional 95% interval [-0.0172, -0.0016] | Ranking responds to missing supports and native graph-frequency ties; this does not isolate their separate contributions; any uncertified ranking remains censored |
| Controlled inference-time evidence intervention | random_global vs original; fixed general catalog | Gold-generation coverage change +0.0000, conditional 95% interval [+0.0000, +0.0000] | Fixed implications, analyzed within family; no catalog/perturbation population replication or additive decomposition; uncertified generation outcomes remain observed retrievals |
| Controlled inference-time graph intervention | random_relation_stratified vs original; fixed constant-bearing conditional catalog | Hits@1 change -0.0123, conditional 95% interval [-0.0178, -0.0066] | Ranking responds to missing supports and native graph-frequency ties; this does not isolate their separate contributions; any uncertified ranking remains censored |
| Controlled inference-time evidence intervention | random_relation_stratified vs original; fixed constant-bearing conditional catalog | Gold-generation coverage change +0.0000, conditional 95% interval [+0.0000, +0.0000] | Fixed implications, analyzed within family; no catalog/perturbation population replication or additive decomposition; uncertified generation outcomes remain observed retrievals |
| Controlled inference-time graph intervention | random_relation_stratified vs original; fixed general catalog | Hits@1 change -0.0126, conditional 95% interval [-0.0211, -0.0038] | Ranking responds to missing supports and native graph-frequency ties; this does not isolate their separate contributions; any uncertified ranking remains censored |
| Controlled inference-time evidence intervention | random_relation_stratified vs original; fixed general catalog | Gold-generation coverage change +0.0000, conditional 95% interval [+0.0000, +0.0000] | Fixed implications, analyzed within family; no catalog/perturbation population replication or additive decomposition; uncertified generation outcomes remain observed retrievals |
| Controlled inference-time graph intervention | targeted_local vs original; fixed constant-bearing conditional catalog | Hits@1 change -0.0055, conditional 95% interval [-0.0104, -0.0003] | Ranking responds to missing supports and native graph-frequency ties; this does not isolate their separate contributions; any uncertified ranking remains censored |
| Controlled inference-time evidence intervention | targeted_local vs original; fixed constant-bearing conditional catalog | Gold-generation coverage change +0.0000, conditional 95% interval [+0.0000, +0.0000] | Fixed implications, analyzed within family; no catalog/perturbation population replication or additive decomposition; uncertified generation outcomes remain observed retrievals |
| Controlled inference-time graph intervention | targeted_local vs original; fixed general catalog | Hits@1 change -0.0172, conditional 95% interval [-0.0254, -0.0093] | Ranking responds to missing supports and native graph-frequency ties; this does not isolate their separate contributions; any uncertified ranking remains censored |
| Controlled inference-time evidence intervention | targeted_local vs original; fixed general catalog | Gold-generation coverage change +0.0000, conditional 95% interval [+0.0000, +0.0000] | Fixed implications, analyzed within family; no catalog/perturbation population replication or additive decomposition; uncertified generation outcomes remain observed retrievals |
| Controlled inference-time graph intervention | targeted_relation_matched_control vs original; fixed constant-bearing conditional catalog | Hits@1 change -0.0068, conditional 95% interval [-0.0115, -0.0022] | Ranking responds to missing supports and native graph-frequency ties; this does not isolate their separate contributions; any uncertified ranking remains censored |
| Controlled inference-time evidence intervention | targeted_relation_matched_control vs original; fixed constant-bearing conditional catalog | Gold-generation coverage change +0.0000, conditional 95% interval [+0.0000, +0.0000] | Fixed implications, analyzed within family; no catalog/perturbation population replication or additive decomposition; uncertified generation outcomes remain observed retrievals |
| Controlled inference-time graph intervention | targeted_relation_matched_control vs original; fixed general catalog | Hits@1 change -0.0145, conditional 95% interval [-0.0227, -0.0074] | Ranking responds to missing supports and native graph-frequency ties; this does not isolate their separate contributions; any uncertified ranking remains censored |
| Controlled inference-time evidence intervention | targeted_relation_matched_control vs original; fixed general catalog | Gold-generation coverage change +0.0000, conditional 95% interval [+0.0000, +0.0000] | Fixed implications, analyzed within family; no catalog/perturbation population replication or additive decomposition; uncertified generation outcomes remain observed retrievals |

## Limitations and research conclusion

Direct observations are the graph/path changes and recorded paired outcomes. Controlled evidence concerns these exact missing-edge protocols and contemporaneous trained systems. A single removal/target draw does not establish population-level structural effects. When a comparison has one neural seed or one independently learned inventory per graph, intervals cannot estimate variation in that singleton learning factor. Replicated comparisons resample the available seed and miner factors separately; few repetitions still give limited learning-variability estimates. Neural seed indices are paired across graphs; miner realizations are independently resampled by graph when replicated, never treated as paired deterministic seeds. Shared entities/relations create additional graph dependence.

Targeted versus relation-count-matched removal controls relation totals but still changes endpoint frequencies, local degree and paths together. Retrained-rule changes combine evidence loss, changed learned confidences/inventories and mining stochasticity. Mechanisms behind embedding sensitivity remain hypotheses. Replication counts and completion are recorded above; additional perturbation draws remain future work. CoDEx-M is a later replication dataset after methodology freeze. No larger retention sweep or expensive published-budget reproduction is automatically launched.

`scenario-effects.csv` reports intervals and sample sizes within original known-node degree, relation-frequency and target-incidence strata. Groups use original training information, not post-removal or answer-dependent features. These are exploratory effect heterogeneity, not causal mediation or a deployment selector. `query-joins-with-witnesses.csv`, when generated by the case command, adds verified sampled witness losses.
