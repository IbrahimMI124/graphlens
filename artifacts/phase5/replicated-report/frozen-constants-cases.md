# Frozen constant-bearing rule evidence cases

These compare the identical frozen constant-bearing conditional-rule catalog on original and modified training graphs. No model is re-mined here. All sampled witnesses are checked for training-edge membership, variable/constant consistency and the predicted head. Before-witness missing edges are verified against the actual modified graph. After witnesses use only modified training edges. Rankings also depend on native graph-frequency ties. No embedding response is inferred from this experiment.

Cases are selected by evaluation outcomes and are illustrative, not deployment features or a representative prevalence estimate. Raw rule confidences/support remain frozen; scores are not probabilities. Entity/relation label metadata was not downloaded, so original Wikidata identifiers are retained.

This subset contains learned constant-bearing implications with nonempty bodies. Unconditional zero-body entity priors are excluded. Native confidence smoothing and Uc/Ud family weights are unchanged; inventory size is not predictive contribution.

## random_global — candidate_support_lost — test:1:head

Query `(?, P106, Q19723482)`, correct triple `Q319374 P106 Q19723482`. Frozen-rule rank 143 → 143; Hits@1 0 → 0; correct-answer generation True → True.

Filtered top predictions `[['Q219631', 0.5714285714285714], ['Q201656', 0.5714285714285714]]` → `[['Q219631', 0.5714285714285714], ['Q201656', 0.5714285714285714]]`.

Training degrees (head/tail) 16/16 → 15/16; relation frequency 10197 → 9187. Directed typed two-/three-hop walks to truth 0/0 → 0/0. These walk counts are answer-dependent diagnostics, not counts of rule groundings.

- before: `P106(Q319374,Y) <= P106(Q272031,Y)` supports `('Q319374', 'P106', 'Q19723482')`; raw confidence 0.625, support 5. Witness `[('Q272031', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.
- before: `P106(Q319374,Y) <= P106(Q1373347,Y)` supports `('Q319374', 'P106', 'Q19723482')`; raw confidence 0.5714285714285714, support 4. Witness `[('Q1373347', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.
- before: `P106(Q319374,Y) <= P106(Q270935,Y)` supports `('Q319374', 'P106', 'Q19723482')`; raw confidence 0.5, support 5. Witness `[('Q270935', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.
- before: `P106(Q219631,Y) <= P106(Q233946,Y)` supports `('Q219631', 'P106', 'Q19723482')`; raw confidence 0.8888888888888888, support 8. Witness `[('Q233946', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.
- before: `P106(Q219631,Y) <= P106(Q210172,Y)` supports `('Q219631', 'P106', 'Q19723482')`; raw confidence 0.7272727272727273, support 8. Witness `[('Q210172', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.
- before: `P106(Q219631,Y) <= P106(Q194045,Y)` supports `('Q219631', 'P106', 'Q19723482')`; raw confidence 0.75, support 6. Witness `[('Q194045', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.
- before: `P106(X,Q19723482) <= P172(X,A)` supports `('Q36', 'P106', 'Q19723482')`; raw confidence 0.0058997050147492625, support 2. Witness `[('Q36', 'P172', 'Q42884')]`; removed training edges `[('Q36', 'P172', 'Q42884')]`; survives=False.
- after: `P106(Q319374,Y) <= P106(Q272031,Y)` supports `('Q319374', 'P106', 'Q19723482')`; raw confidence 0.625, support 5. Witness `[('Q272031', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.
- after: `P106(Q319374,Y) <= P106(Q1373347,Y)` supports `('Q319374', 'P106', 'Q19723482')`; raw confidence 0.5714285714285714, support 4. Witness `[('Q1373347', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.
- after: `P106(Q319374,Y) <= P106(Q270935,Y)` supports `('Q319374', 'P106', 'Q19723482')`; raw confidence 0.5, support 5. Witness `[('Q270935', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.
- after: `P106(Q219631,Y) <= P106(Q233946,Y)` supports `('Q219631', 'P106', 'Q19723482')`; raw confidence 0.8888888888888888, support 8. Witness `[('Q233946', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.
- after: `P106(Q219631,Y) <= P106(Q210172,Y)` supports `('Q219631', 'P106', 'Q19723482')`; raw confidence 0.7272727272727273, support 8. Witness `[('Q210172', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.
- after: `P106(Q219631,Y) <= P106(Q194045,Y)` supports `('Q219631', 'P106', 'Q19723482')`; raw confidence 0.75, support 6. Witness `[('Q194045', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.

A lost sampled witness does not imply all support disappeared: redundant witnesses or other rules may retain the candidate.

## random_global — top1_changed — test:5:head

Query `(?, P1303, Q6607)`, correct triple `Q122003 P1303 Q6607`. Frozen-rule rank 30 → 28; Hits@1 0 → 0; correct-answer generation True → True.

Filtered top predictions `[['Q4028', 0.8356164383561644], ['Q144622', 0.8356164383561644]]` → `[['Q144622', 0.8356164383561644], ['Q425821', 0.8356164383561644]]`.

Training degrees (head/tail) 21/276 → 20/253; relation frequency 1443 → 1287. Directed typed two-/three-hop walks to truth 1/0 → 1/0. These walk counts are answer-dependent diagnostics, not counts of rule groundings.

- before: `P1303(X,Q6607) <= P136(X,Q217191)` supports `('Q122003', 'P1303', 'Q6607')`; raw confidence 0.8, support 20. Witness `[('Q122003', 'P136', 'Q217191')]`; removed training edges `[]`; survives=True.
- before: `P1303(X,Q6607) <= P136(X,Q83440)` supports `('Q122003', 'P1303', 'Q6607')`; raw confidence 0.647887323943662, support 46. Witness `[('Q122003', 'P136', 'Q83440')]`; removed training edges `[]`; survives=True.
- before: `P1303(X,Q6607) <= P264(X,Q330629)` supports `('Q122003', 'P1303', 'Q6607')`; raw confidence 0.5517241379310345, support 16. Witness `[('Q122003', 'P264', 'Q330629')]`; removed training edges `[]`; survives=True.
- before: `P1303(X,Q6607) <= P106(X,Q855091)` supports `('Q4028', 'P1303', 'Q6607')`; raw confidence 0.8551401869158879, support 183. Witness `[('Q4028', 'P106', 'Q855091')]`; removed training edges `[('Q4028', 'P106', 'Q855091')]`; survives=False.
- before: `P1303(X,Q6607) <= P1303(X,Q46185)` supports `('Q4028', 'P1303', 'Q6607')`; raw confidence 0.8285714285714286, support 58. Witness `[('Q4028', 'P1303', 'Q46185')]`; removed training edges `[]`; survives=True.
- before: `P1303(X,Q6607) <= P136(X,Q217191)` supports `('Q4028', 'P1303', 'Q6607')`; raw confidence 0.8, support 20. Witness `[('Q4028', 'P136', 'Q217191')]`; removed training edges `[]`; survives=True.
- before: `P1303(X,Q6607) <= P106(X,Q855091)` supports `('Q144622', 'P1303', 'Q6607')`; raw confidence 0.8551401869158879, support 183. Witness `[('Q144622', 'P106', 'Q855091')]`; removed training edges `[]`; survives=True.
- before: `P1303(X,Q6607) <= P1303(X,Q46185)` supports `('Q144622', 'P1303', 'Q6607')`; raw confidence 0.8285714285714286, support 58. Witness `[('Q144622', 'P1303', 'Q46185')]`; removed training edges `[]`; survives=True.
- before: `P1303(X,Q6607) <= P136(X,Q217191)` supports `('Q144622', 'P1303', 'Q6607')`; raw confidence 0.8, support 20. Witness `[('Q144622', 'P136', 'Q217191')]`; removed training edges `[]`; survives=True.
- before: `P1303(X,Q6607) <= P740(X,A)` supports `('Q165745', 'P1303', 'Q6607')`; raw confidence 0.11764705882352941, support 2. Witness `[('Q165745', 'P740', 'Q1297')]`; removed training edges `[('Q165745', 'P740', 'Q1297')]`; survives=False.
- after: `P1303(X,Q6607) <= P136(X,Q217191)` supports `('Q122003', 'P1303', 'Q6607')`; raw confidence 0.8, support 20. Witness `[('Q122003', 'P136', 'Q217191')]`; removed training edges `[]`; survives=True.
- after: `P1303(X,Q6607) <= P136(X,Q83440)` supports `('Q122003', 'P1303', 'Q6607')`; raw confidence 0.647887323943662, support 46. Witness `[('Q122003', 'P136', 'Q83440')]`; removed training edges `[]`; survives=True.
- after: `P1303(X,Q6607) <= P264(X,Q330629)` supports `('Q122003', 'P1303', 'Q6607')`; raw confidence 0.5517241379310345, support 16. Witness `[('Q122003', 'P264', 'Q330629')]`; removed training edges `[]`; survives=True.
- after: `P1303(X,Q6607) <= P1303(X,Q46185)` supports `('Q4028', 'P1303', 'Q6607')`; raw confidence 0.8285714285714286, support 58. Witness `[('Q4028', 'P1303', 'Q46185')]`; removed training edges `[]`; survives=True.
- after: `P1303(X,Q6607) <= P136(X,Q217191)` supports `('Q4028', 'P1303', 'Q6607')`; raw confidence 0.8, support 20. Witness `[('Q4028', 'P136', 'Q217191')]`; removed training edges `[]`; survives=True.
- after: `P1303(X,Q6607) <= P136(X,Q11399)` supports `('Q4028', 'P1303', 'Q6607')`; raw confidence 0.6376811594202898, support 88. Witness `[('Q4028', 'P136', 'Q11399')]`; removed training edges `[]`; survives=True.
- after: `P1303(X,Q6607) <= P106(X,Q855091)` supports `('Q144622', 'P1303', 'Q6607')`; raw confidence 0.8551401869158879, support 183. Witness `[('Q144622', 'P106', 'Q855091')]`; removed training edges `[]`; survives=True.
- after: `P1303(X,Q6607) <= P1303(X,Q46185)` supports `('Q144622', 'P1303', 'Q6607')`; raw confidence 0.8285714285714286, support 58. Witness `[('Q144622', 'P1303', 'Q46185')]`; removed training edges `[]`; survives=True.
- after: `P1303(X,Q6607) <= P136(X,Q217191)` supports `('Q144622', 'P1303', 'Q6607')`; raw confidence 0.8, support 20. Witness `[('Q144622', 'P136', 'Q217191')]`; removed training edges `[]`; survives=True.

A lost sampled witness does not imply all support disappeared: redundant witnesses or other rules may retain the candidate.

## random_global — top1_success_lost — test:10:head

Query `(?, P463, Q656801)`, correct triple `Q1019 P463 Q656801`. Frozen-rule rank 1 → 2; Hits@1 1 → 0; correct-answer generation True → True.

Filtered top predictions `[['Q1019', 0.875], ['Q55', 0.875]]` → `[['Q55', 0.875], ['Q1019', 0.875]]`.

Training degrees (head/tail) 36/165 → 32/148; relation frequency 4985 → 4522. Directed typed two-/three-hop walks to truth 6/804 → 3/444. These walk counts are answer-dependent diagnostics, not counts of rule groundings.

- before: `P463(X,Q656801) <= P463(X,Q340195)` supports `('Q1019', 'P463', 'Q656801')`; raw confidence 0.9333333333333333, support 70. Witness `[('Q1019', 'P463', 'Q340195')]`; removed training edges `[]`; survives=True.
- before: `P463(X,Q656801) <= P463(X,Q1043527)` supports `('Q1019', 'P463', 'Q656801')`; raw confidence 0.8957055214723927, support 146. Witness `[('Q1019', 'P463', 'Q1043527')]`; removed training edges `[('Q1019', 'P463', 'Q1043527')]`; survives=False.
- before: `P463(X,Q656801) <= P463(X,Q5611262)` supports `('Q1019', 'P463', 'Q656801')`; raw confidence 0.90625, support 87. Witness `[('Q1019', 'P463', 'Q5611262')]`; removed training edges `[]`; survives=True.
- before: `P463(X,Q656801) <= P463(X,Q340195)` supports `('Q55', 'P463', 'Q656801')`; raw confidence 0.9333333333333333, support 70. Witness `[('Q55', 'P463', 'Q340195')]`; removed training edges `[]`; survives=True.
- before: `P463(X,Q656801) <= P463(X,Q1043527)` supports `('Q55', 'P463', 'Q656801')`; raw confidence 0.8957055214723927, support 146. Witness `[('Q55', 'P463', 'Q1043527')]`; removed training edges `[]`; survives=True.
- before: `P463(X,Q656801) <= P463(X,Q5611262)` supports `('Q55', 'P463', 'Q656801')`; raw confidence 0.90625, support 87. Witness `[('Q55', 'P463', 'Q5611262')]`; removed training edges `[]`; survives=True.
- before: `P463(X,Q656801) <= P530(Q17,X)` supports `('Q12585', 'P463', 'Q656801')`; raw confidence 0.7941176470588235, support 54. Witness `[('Q17', 'P530', 'Q12585')]`; removed training edges `[('Q17', 'P530', 'Q12585')]`; survives=False.
- before: `P463(X,Q656801) <= P530(A,X)` supports `('Q12585', 'P463', 'Q656801')`; raw confidence 0.7819905213270142, support 165. Witness `[('Q17', 'P530', 'Q12585')]`; removed training edges `[('Q17', 'P530', 'Q12585')]`; survives=False.
- after: `P463(X,Q656801) <= P463(X,Q340195)` supports `('Q1019', 'P463', 'Q656801')`; raw confidence 0.9333333333333333, support 70. Witness `[('Q1019', 'P463', 'Q340195')]`; removed training edges `[]`; survives=True.
- after: `P463(X,Q656801) <= P463(X,Q5611262)` supports `('Q1019', 'P463', 'Q656801')`; raw confidence 0.90625, support 87. Witness `[('Q1019', 'P463', 'Q5611262')]`; removed training edges `[]`; survives=True.
- after: `P463(X,Q656801) <= P463(X,Q899770)` supports `('Q1019', 'P463', 'Q656801')`; raw confidence 0.8863636363636364, support 117. Witness `[('Q1019', 'P463', 'Q899770')]`; removed training edges `[]`; survives=True.
- after: `P463(X,Q656801) <= P463(X,Q340195)` supports `('Q55', 'P463', 'Q656801')`; raw confidence 0.9333333333333333, support 70. Witness `[('Q55', 'P463', 'Q340195')]`; removed training edges `[]`; survives=True.
- after: `P463(X,Q656801) <= P463(X,Q1043527)` supports `('Q55', 'P463', 'Q656801')`; raw confidence 0.8957055214723927, support 146. Witness `[('Q55', 'P463', 'Q1043527')]`; removed training edges `[]`; survives=True.
- after: `P463(X,Q656801) <= P463(X,Q5611262)` supports `('Q55', 'P463', 'Q656801')`; raw confidence 0.90625, support 87. Witness `[('Q55', 'P463', 'Q5611262')]`; removed training edges `[]`; survives=True.

A lost sampled witness does not imply all support disappeared: redundant witnesses or other rules may retain the candidate.

## random_global — top1_success_gained — test:12:head

Query `(?, P264, Q387539)`, correct triple `Q210172 P264 Q387539`. Frozen-rule rank 2 → 1; Hits@1 0 → 1; correct-answer generation True → True.

Filtered top predictions `[['Q294144', 0.2631578947368421], ['Q210172', 0.2631578947368421]]` → `[['Q210172', 0.2631578947368421], ['Q230943', 0.2631578947368421]]`.

Training degrees (head/tail) 23/15 → 21/13; relation frequency 879 → 803. Directed typed two-/three-hop walks to truth 2/5 → 2/5. These walk counts are answer-dependent diagnostics, not counts of rule groundings.

- before: `P264(X,Q387539) <= P264(X,Q54860)` supports `('Q210172', 'P264', 'Q387539')`; raw confidence 0.35714285714285715, support 5. Witness `[('Q210172', 'P264', 'Q54860')]`; removed training edges `[]`; survives=True.
- before: `P264(X,Q387539) <= P551(X,Q65)` supports `('Q210172', 'P264', 'Q387539')`; raw confidence 0.1111111111111111, support 5. Witness `[('Q210172', 'P551', 'Q65')]`; removed training edges `[]`; survives=True.
- before: `P264(X,Q387539) <= P106(X,Q2405480)` supports `('Q210172', 'P264', 'Q387539')`; raw confidence 0.03896103896103896, support 6. Witness `[('Q210172', 'P106', 'Q2405480')]`; removed training edges `[]`; survives=True.
- before: `P264(X,Q387539) <= P264(X,Q54860)` supports `('Q294144', 'P264', 'Q387539')`; raw confidence 0.35714285714285715, support 5. Witness `[('Q294144', 'P264', 'Q54860')]`; removed training edges `[]`; survives=True.
- before: `P264(Q294144,Y) <= P17(Y,Q30)` supports `('Q294144', 'P264', 'Q387539')`; raw confidence 0.11428571428571428, support 4. Witness `[('Q387539', 'P17', 'Q30')]`; removed training edges `[('Q387539', 'P17', 'Q30')]`; survives=False.
- before: `P264(X,Q387539) <= P136(X,Q850412)` supports `('Q294144', 'P264', 'Q387539')`; raw confidence 0.07936507936507936, support 5. Witness `[('Q294144', 'P136', 'Q850412')]`; removed training edges `[]`; survives=True.
- before: `P264(X,Q387539) <= P172(X,A)` supports `('Q36', 'P264', 'Q387539')`; raw confidence 0.008849557522123894, support 3. Witness `[('Q36', 'P172', 'Q42884')]`; removed training edges `[('Q36', 'P172', 'Q42884')]`; survives=False.
- after: `P264(X,Q387539) <= P264(X,Q54860)` supports `('Q210172', 'P264', 'Q387539')`; raw confidence 0.35714285714285715, support 5. Witness `[('Q210172', 'P264', 'Q54860')]`; removed training edges `[]`; survives=True.
- after: `P264(X,Q387539) <= P551(X,Q65)` supports `('Q210172', 'P264', 'Q387539')`; raw confidence 0.1111111111111111, support 5. Witness `[('Q210172', 'P551', 'Q65')]`; removed training edges `[]`; survives=True.
- after: `P264(X,Q387539) <= P106(X,Q2405480)` supports `('Q210172', 'P264', 'Q387539')`; raw confidence 0.03896103896103896, support 6. Witness `[('Q210172', 'P106', 'Q2405480')]`; removed training edges `[]`; survives=True.
- after: `P264(X,Q387539) <= P264(X,Q54860)` supports `('Q294144', 'P264', 'Q387539')`; raw confidence 0.35714285714285715, support 5. Witness `[('Q294144', 'P264', 'Q54860')]`; removed training edges `[]`; survives=True.
- after: `P264(X,Q387539) <= P136(X,Q850412)` supports `('Q294144', 'P264', 'Q387539')`; raw confidence 0.07936507936507936, support 5. Witness `[('Q294144', 'P136', 'Q850412')]`; removed training edges `[]`; survives=True.
- after: `P264(X,Q387539) <= P136(X,Q37073)` supports `('Q294144', 'P264', 'Q387539')`; raw confidence 0.03669724770642202, support 8. Witness `[('Q294144', 'P136', 'Q37073')]`; removed training edges `[]`; survives=True.

A lost sampled witness does not imply all support disappeared: redundant witnesses or other rules may retain the candidate.

## random_relation_stratified — candidate_support_lost — test:0:head

Query `(?, P27, Q142)`, correct triple `Q206832 P27 Q142`. Frozen-rule rank 3 → 3; Hits@1 0 → 0; correct-answer generation True → True.

Filtered top predictions `[['Q8772', 0.7162162162162162], ['Q37327', 0.7162162162162162]]` → `[['Q8772', 0.7162162162162162], ['Q37327', 0.7162162162162162]]`.

Training degrees (head/tail) 13/325 → 13/298; relation frequency 1648 → 1483. Directed typed two-/three-hop walks to truth 2/3 → 2/3. These walk counts are answer-dependent diagnostics, not counts of rule groundings.

- before: `P27(X,Q142) <= P20(X,Q90)` supports `('Q206832', 'P27', 'Q142')`; raw confidence 0.7681159420289855, support 53. Witness `[('Q206832', 'P20', 'Q90')]`; removed training edges `[]`; survives=True.
- before: `P27(X,Q142) <= P69(X,Q273626)` supports `('Q206832', 'P27', 'Q142')`; raw confidence 0.7777777777777778, support 14. Witness `[('Q206832', 'P69', 'Q273626')]`; removed training edges `[]`; survives=True.
- before: `P27(X,Q142) <= P119(X,Q311)` supports `('Q206832', 'P27', 'Q142')`; raw confidence 0.7142857142857143, support 15. Witness `[('Q206832', 'P119', 'Q311')]`; removed training edges `[]`; survives=True.
- before: `P27(X,Q142) <= P20(X,Q90)` supports `('Q8772', 'P27', 'Q142')`; raw confidence 0.7681159420289855, support 53. Witness `[('Q8772', 'P20', 'Q90')]`; removed training edges `[]`; survives=True.
- before: `P27(X,Q142) <= P172(X,Q121842)` supports `('Q8772', 'P27', 'Q142')`; raw confidence 0.8461538461538461, support 22. Witness `[('Q8772', 'P172', 'Q121842')]`; removed training edges `[('Q8772', 'P172', 'Q121842')]`; survives=False.
- before: `P27(X,Q142) <= P463(X,Q161806)` supports `('Q8772', 'P27', 'Q142')`; raw confidence 0.8095238095238095, support 17. Witness `[('Q8772', 'P463', 'Q161806')]`; removed training edges `[]`; survives=True.
- before: `P27(X,Q142) <= P136(X,A)` supports `('Q208909', 'P27', 'Q142')`; raw confidence 0.038978494623655914, support 29. Witness `[('Q208909', 'P136', 'Q11399')]`; removed training edges `[('Q208909', 'P136', 'Q11399')]`; survives=False.
- after: `P27(X,Q142) <= P20(X,Q90)` supports `('Q206832', 'P27', 'Q142')`; raw confidence 0.7681159420289855, support 53. Witness `[('Q206832', 'P20', 'Q90')]`; removed training edges `[]`; survives=True.
- after: `P27(X,Q142) <= P69(X,Q273626)` supports `('Q206832', 'P27', 'Q142')`; raw confidence 0.7777777777777778, support 14. Witness `[('Q206832', 'P69', 'Q273626')]`; removed training edges `[]`; survives=True.
- after: `P27(X,Q142) <= P119(X,Q311)` supports `('Q206832', 'P27', 'Q142')`; raw confidence 0.7142857142857143, support 15. Witness `[('Q206832', 'P119', 'Q311')]`; removed training edges `[]`; survives=True.
- after: `P27(X,Q142) <= P20(X,Q90)` supports `('Q8772', 'P27', 'Q142')`; raw confidence 0.7681159420289855, support 53. Witness `[('Q8772', 'P20', 'Q90')]`; removed training edges `[]`; survives=True.
- after: `P27(X,Q142) <= P463(X,Q161806)` supports `('Q8772', 'P27', 'Q142')`; raw confidence 0.8095238095238095, support 17. Witness `[('Q8772', 'P463', 'Q161806')]`; removed training edges `[]`; survives=True.
- after: `P27(X,Q142) <= P119(X,Q311)` supports `('Q8772', 'P27', 'Q142')`; raw confidence 0.7142857142857143, support 15. Witness `[('Q8772', 'P119', 'Q311')]`; removed training edges `[]`; survives=True.

A lost sampled witness does not imply all support disappeared: redundant witnesses or other rules may retain the candidate.

## random_relation_stratified — top1_changed — test:20:head

Query `(?, P106, Q14915627)`, correct triple `Q9387 P106 Q14915627`. Frozen-rule rank 1017 → 987; Hits@1 0 → 0; correct-answer generation True → True.

Filtered top predictions `[['Q8011', 0.6666666666666666], ['Q7604', 0.6666666666666666]]` → `[['Q7604', 0.6666666666666666], ['Q299138', 0.5]]`.

Training degrees (head/tail) 25/38 → 22/35; relation frequency 10197 → 9177. Directed typed two-/three-hop walks to truth 0/0 → 0/0. These walk counts are answer-dependent diagnostics, not counts of rule groundings.

- before: `P106(Q9387,Y) <= P106(Q79025,Y)` supports `('Q9387', 'P106', 'Q14915627')`; raw confidence 0.16666666666666666, support 2. Witness `[('Q79025', 'P106', 'Q14915627')]`; removed training edges `[]`; survives=True.
- before: `P106(X,Q14915627) <= P27(X,Q41304)` supports `('Q9387', 'P106', 'Q14915627')`; raw confidence 0.1111111111111111, support 2. Witness `[('Q9387', 'P27', 'Q41304')]`; removed training edges `[]`; survives=True.
- before: `P106(X,Q14915627) <= P106(X,Q1622272)` supports `('Q9387', 'P106', 'Q14915627')`; raw confidence 0.08205128205128205, support 16. Witness `[('Q9387', 'P106', 'Q1622272')]`; removed training edges `[]`; survives=True.
- before: `P106(X,Q14915627) <= P106(X,Q16031530)` supports `('Q8011', 'P106', 'Q14915627')`; raw confidence 0.8421052631578947, support 16. Witness `[('Q8011', 'P106', 'Q16031530')]`; removed training edges `[('Q8011', 'P106', 'Q16031530')]`; survives=False.
- before: `P106(Q8011,Y) <= P106(Q153232,Y)` supports `('Q8011', 'P106', 'Q14915627')`; raw confidence 0.5555555555555556, support 5. Witness `[('Q153232', 'P106', 'Q14915627')]`; removed training edges `[]`; survives=True.
- before: `P106(Q8011,Y) <= P106(Q182046,Y)` supports `('Q8011', 'P106', 'Q14915627')`; raw confidence 0.5, support 5. Witness `[('Q182046', 'P106', 'Q14915627')]`; removed training edges `[]`; survives=True.
- before: `P106(X,Q14915627) <= P106(X,Q16031530)` supports `('Q7604', 'P106', 'Q14915627')`; raw confidence 0.8421052631578947, support 16. Witness `[('Q7604', 'P106', 'Q16031530')]`; removed training edges `[]`; survives=True.
- before: `P106(Q7604,Y) <= P106(Q153232,Y)` supports `('Q7604', 'P106', 'Q14915627')`; raw confidence 0.5555555555555556, support 5. Witness `[('Q153232', 'P106', 'Q14915627')]`; removed training edges `[]`; survives=True.
- before: `P106(Q7604,Y) <= P106(Q76738,Y)` supports `('Q7604', 'P106', 'Q14915627')`; raw confidence 0.46153846153846156, support 6. Witness `[('Q76738', 'P106', 'Q14915627')]`; removed training edges `[]`; survives=True.
- before: `P106(X,Q14915627) <= P136(X,A)` supports `('Q208909', 'P106', 'Q14915627')`; raw confidence 0.03225806451612903, support 24. Witness `[('Q208909', 'P136', 'Q11399')]`; removed training edges `[('Q208909', 'P136', 'Q11399')]`; survives=False.
- after: `P106(Q9387,Y) <= P106(Q79025,Y)` supports `('Q9387', 'P106', 'Q14915627')`; raw confidence 0.16666666666666666, support 2. Witness `[('Q79025', 'P106', 'Q14915627')]`; removed training edges `[]`; survives=True.
- after: `P106(X,Q14915627) <= P27(X,Q41304)` supports `('Q9387', 'P106', 'Q14915627')`; raw confidence 0.1111111111111111, support 2. Witness `[('Q9387', 'P27', 'Q41304')]`; removed training edges `[]`; survives=True.
- after: `P106(X,Q14915627) <= P106(X,Q1622272)` supports `('Q9387', 'P106', 'Q14915627')`; raw confidence 0.08205128205128205, support 16. Witness `[('Q9387', 'P106', 'Q1622272')]`; removed training edges `[]`; survives=True.
- after: `P106(Q8011,Y) <= P106(Q153232,Y)` supports `('Q8011', 'P106', 'Q14915627')`; raw confidence 0.5555555555555556, support 5. Witness `[('Q153232', 'P106', 'Q14915627')]`; removed training edges `[]`; survives=True.
- after: `P106(Q8011,Y) <= P106(Q182046,Y)` supports `('Q8011', 'P106', 'Q14915627')`; raw confidence 0.5, support 5. Witness `[('Q182046', 'P106', 'Q14915627')]`; removed training edges `[]`; survives=True.
- after: `P106(Q8011,Y) <= P106(Q9047,Y)` supports `('Q8011', 'P106', 'Q14915627')`; raw confidence 0.35714285714285715, support 5. Witness `[('Q9047', 'P106', 'Q14915627')]`; removed training edges `[]`; survives=True.
- after: `P106(X,Q14915627) <= P106(X,Q16031530)` supports `('Q7604', 'P106', 'Q14915627')`; raw confidence 0.8421052631578947, support 16. Witness `[('Q7604', 'P106', 'Q16031530')]`; removed training edges `[]`; survives=True.
- after: `P106(Q7604,Y) <= P106(Q153232,Y)` supports `('Q7604', 'P106', 'Q14915627')`; raw confidence 0.5555555555555556, support 5. Witness `[('Q153232', 'P106', 'Q14915627')]`; removed training edges `[]`; survives=True.
- after: `P106(Q7604,Y) <= P106(Q76738,Y)` supports `('Q7604', 'P106', 'Q14915627')`; raw confidence 0.46153846153846156, support 6. Witness `[('Q76738', 'P106', 'Q14915627')]`; removed training edges `[]`; survives=True.

A lost sampled witness does not imply all support disappeared: redundant witnesses or other rules may retain the candidate.

## random_relation_stratified — top1_success_lost — test:37:head

Query `(?, P27, Q43287)`, correct triple `Q44086 P27 Q43287`. Frozen-rule rank 1 → 2; Hits@1 1 → 0; correct-answer generation True → True.

Filtered top predictions `[['Q44086', 0.4666666666666667], ['Q77060', 0.4666666666666667]]` → `[['Q77060', 0.4666666666666667], ['Q44086', 0.4666666666666667]]`.

Training degrees (head/tail) 17/27 → 15/26; relation frequency 1648 → 1483. Directed typed two-/three-hop walks to truth 2/1 → 2/1. These walk counts are answer-dependent diagnostics, not counts of rule groundings.

- before: `P27(X,Q43287) <= P27(X,Q7318)` supports `('Q44086', 'P27', 'Q43287')`; raw confidence 0.7, support 7. Witness `[('Q44086', 'P27', 'Q7318')]`; removed training edges `[]`; survives=True.
- before: `P27(X,Q43287) <= P27(X,Q41304)` supports `('Q44086', 'P27', 'Q43287')`; raw confidence 0.5555555555555556, support 10. Witness `[('Q44086', 'P27', 'Q41304')]`; removed training edges `[('Q44086', 'P27', 'Q41304')]`; survives=False.
- before: `P27(Q44086,Y) <= P27(Q57535,Y)` supports `('Q44086', 'P27', 'Q43287')`; raw confidence 0.8, support 4. Witness `[('Q57535', 'P27', 'Q43287')]`; removed training edges `[]`; survives=True.
- before: `P27(X,Q43287) <= P27(X,Q7318)` supports `('Q77060', 'P27', 'Q43287')`; raw confidence 0.7, support 7. Witness `[('Q77060', 'P27', 'Q7318')]`; removed training edges `[]`; survives=True.
- before: `P27(X,Q43287) <= P27(X,Q41304)` supports `('Q77060', 'P27', 'Q43287')`; raw confidence 0.5555555555555556, support 10. Witness `[('Q77060', 'P27', 'Q41304')]`; removed training edges `[]`; survives=True.
- before: `P27(Q77060,Y) <= P17(Q1726,Y)` supports `('Q77060', 'P27', 'Q43287')`; raw confidence 0.6, support 3. Witness `[('Q1726', 'P17', 'Q43287')]`; removed training edges `[]`; survives=True.
- before: `P27(X,Q43287) <= P136(X,A)` supports `('Q208909', 'P27', 'Q43287')`; raw confidence 0.002688172043010753, support 2. Witness `[('Q208909', 'P136', 'Q11399')]`; removed training edges `[('Q208909', 'P136', 'Q11399')]`; survives=False.
- after: `P27(X,Q43287) <= P27(X,Q7318)` supports `('Q44086', 'P27', 'Q43287')`; raw confidence 0.7, support 7. Witness `[('Q44086', 'P27', 'Q7318')]`; removed training edges `[]`; survives=True.
- after: `P27(Q44086,Y) <= P27(Q57535,Y)` supports `('Q44086', 'P27', 'Q43287')`; raw confidence 0.8, support 4. Witness `[('Q57535', 'P27', 'Q43287')]`; removed training edges `[]`; survives=True.
- after: `P27(Q44086,Y) <= P17(Q1726,Y)` supports `('Q44086', 'P27', 'Q43287')`; raw confidence 0.8, support 4. Witness `[('Q1726', 'P17', 'Q43287')]`; removed training edges `[]`; survives=True.
- after: `P27(X,Q43287) <= P27(X,Q7318)` supports `('Q77060', 'P27', 'Q43287')`; raw confidence 0.7, support 7. Witness `[('Q77060', 'P27', 'Q7318')]`; removed training edges `[]`; survives=True.
- after: `P27(X,Q43287) <= P27(X,Q41304)` supports `('Q77060', 'P27', 'Q43287')`; raw confidence 0.5555555555555556, support 10. Witness `[('Q77060', 'P27', 'Q41304')]`; removed training edges `[]`; survives=True.
- after: `P27(Q77060,Y) <= P17(Q1726,Y)` supports `('Q77060', 'P27', 'Q43287')`; raw confidence 0.6, support 3. Witness `[('Q1726', 'P17', 'Q43287')]`; removed training edges `[]`; survives=True.

A lost sampled witness does not imply all support disappeared: redundant witnesses or other rules may retain the candidate.

## random_relation_stratified — top1_success_gained — test:294:head

Query `(?, P463, Q376150)`, correct triple `Q783 P463 Q376150`. Frozen-rule rank 2 → 1; Hits@1 0 → 1; correct-answer generation True → True.

Filtered top predictions `[['Q884', 0.8545454545454545], ['Q783', 0.8545454545454545]]` → `[['Q783', 0.8545454545454545], ['Q884', 0.8545454545454545]]`.

Training degrees (head/tail) 30/167 → 29/149; relation frequency 4985 → 4486. Directed typed two-/three-hop walks to truth 4/747 → 3/492. These walk counts are answer-dependent diagnostics, not counts of rule groundings.

- before: `P463(X,Q376150) <= P463(X,Q17495)` supports `('Q783', 'P463', 'Q376150')`; raw confidence 0.88125, support 141. Witness `[('Q783', 'P463', 'Q17495')]`; removed training edges `[]`; survives=True.
- before: `P463(X,Q376150) <= P463(X,Q899770)` supports `('Q783', 'P463', 'Q376150')`; raw confidence 0.8712121212121212, support 115. Witness `[('Q783', 'P463', 'Q899770')]`; removed training edges `[]`; survives=True.
- before: `P463(X,Q376150) <= P463(X,Q7809)` supports `('Q783', 'P463', 'Q376150')`; raw confidence 0.8614457831325302, support 143. Witness `[('Q783', 'P463', 'Q7809')]`; removed training edges `[]`; survives=True.
- before: `P463(X,Q376150) <= P463(X,Q17495)` supports `('Q884', 'P463', 'Q376150')`; raw confidence 0.88125, support 141. Witness `[('Q884', 'P463', 'Q17495')]`; removed training edges `[]`; survives=True.
- before: `P463(X,Q376150) <= P463(X,Q899770)` supports `('Q884', 'P463', 'Q376150')`; raw confidence 0.8712121212121212, support 115. Witness `[('Q884', 'P463', 'Q899770')]`; removed training edges `[]`; survives=True.
- before: `P463(X,Q376150) <= P463(X,Q7809)` supports `('Q884', 'P463', 'Q376150')`; raw confidence 0.8614457831325302, support 143. Witness `[('Q884', 'P463', 'Q7809')]`; removed training edges `[]`; survives=True.
- before: `P463(X,Q376150) <= P172(X,Q42884)` supports `('Q567', 'P463', 'Q376150')`; raw confidence 0.05405405405405406, support 2. Witness `[('Q567', 'P172', 'Q42884')]`; removed training edges `[('Q567', 'P172', 'Q42884')]`; survives=False.
- before: `P463(X,Q376150) <= P172(X,A)` supports `('Q567', 'P463', 'Q376150')`; raw confidence 0.017699115044247787, support 6. Witness `[('Q567', 'P172', 'Q42884')]`; removed training edges `[('Q567', 'P172', 'Q42884')]`; survives=False.
- before: `P463(X,Q376150) <= P140(X,A)` supports `('Q567', 'P463', 'Q376150')`; raw confidence 0.005649717514124294, support 2. Witness `[('Q567', 'P140', 'Q75809')]`; removed training edges `[('Q567', 'P140', 'Q75809')]`; survives=False.
- after: `P463(X,Q376150) <= P463(X,Q17495)` supports `('Q783', 'P463', 'Q376150')`; raw confidence 0.88125, support 141. Witness `[('Q783', 'P463', 'Q17495')]`; removed training edges `[]`; survives=True.
- after: `P463(X,Q376150) <= P463(X,Q899770)` supports `('Q783', 'P463', 'Q376150')`; raw confidence 0.8712121212121212, support 115. Witness `[('Q783', 'P463', 'Q899770')]`; removed training edges `[]`; survives=True.
- after: `P463(X,Q376150) <= P463(X,Q7809)` supports `('Q783', 'P463', 'Q376150')`; raw confidence 0.8614457831325302, support 143. Witness `[('Q783', 'P463', 'Q7809')]`; removed training edges `[]`; survives=True.
- after: `P463(X,Q376150) <= P463(X,Q17495)` supports `('Q884', 'P463', 'Q376150')`; raw confidence 0.88125, support 141. Witness `[('Q884', 'P463', 'Q17495')]`; removed training edges `[]`; survives=True.
- after: `P463(X,Q376150) <= P463(X,Q899770)` supports `('Q884', 'P463', 'Q376150')`; raw confidence 0.8712121212121212, support 115. Witness `[('Q884', 'P463', 'Q899770')]`; removed training edges `[]`; survives=True.
- after: `P463(X,Q376150) <= P463(X,Q7809)` supports `('Q884', 'P463', 'Q376150')`; raw confidence 0.8614457831325302, support 143. Witness `[('Q884', 'P463', 'Q7809')]`; removed training edges `[]`; survives=True.

A lost sampled witness does not imply all support disappeared: redundant witnesses or other rules may retain the candidate.

## targeted_local — candidate_support_lost — test:0:head

Query `(?, P27, Q142)`, correct triple `Q206832 P27 Q142`. Frozen-rule rank 3 → 3; Hits@1 0 → 0; correct-answer generation True → True.

Filtered top predictions `[['Q8772', 0.7162162162162162], ['Q37327', 0.7162162162162162]]` → `[['Q8772', 0.7162162162162162], ['Q37327', 0.7162162162162162]]`.

Training degrees (head/tail) 13/325 → 12/176; relation frequency 1648 → 1198. Directed typed two-/three-hop walks to truth 2/3 → 1/1. These walk counts are answer-dependent diagnostics, not counts of rule groundings.

- before: `P27(X,Q142) <= P20(X,Q90)` supports `('Q206832', 'P27', 'Q142')`; raw confidence 0.7681159420289855, support 53. Witness `[('Q206832', 'P20', 'Q90')]`; removed training edges `[]`; survives=True.
- before: `P27(X,Q142) <= P69(X,Q273626)` supports `('Q206832', 'P27', 'Q142')`; raw confidence 0.7777777777777778, support 14. Witness `[('Q206832', 'P69', 'Q273626')]`; removed training edges `[]`; survives=True.
- before: `P27(X,Q142) <= P119(X,Q311)` supports `('Q206832', 'P27', 'Q142')`; raw confidence 0.7142857142857143, support 15. Witness `[('Q206832', 'P119', 'Q311')]`; removed training edges `[]`; survives=True.
- before: `P27(X,Q142) <= P20(X,Q90)` supports `('Q8772', 'P27', 'Q142')`; raw confidence 0.7681159420289855, support 53. Witness `[('Q8772', 'P20', 'Q90')]`; removed training edges `[]`; survives=True.
- before: `P27(X,Q142) <= P172(X,Q121842)` supports `('Q8772', 'P27', 'Q142')`; raw confidence 0.8461538461538461, support 22. Witness `[('Q8772', 'P172', 'Q121842')]`; removed training edges `[]`; survives=True.
- before: `P27(X,Q142) <= P463(X,Q161806)` supports `('Q8772', 'P27', 'Q142')`; raw confidence 0.8095238095238095, support 17. Witness `[('Q8772', 'P463', 'Q161806')]`; removed training edges `[('Q8772', 'P463', 'Q161806')]`; survives=False.
- before: `P27(X,Q142) <= P136(X,A)` supports `('Q208909', 'P27', 'Q142')`; raw confidence 0.038978494623655914, support 29. Witness `[('Q208909', 'P136', 'Q11399')]`; removed training edges `[('Q208909', 'P136', 'Q11399')]`; survives=False.
- after: `P27(X,Q142) <= P20(X,Q90)` supports `('Q206832', 'P27', 'Q142')`; raw confidence 0.7681159420289855, support 53. Witness `[('Q206832', 'P20', 'Q90')]`; removed training edges `[]`; survives=True.
- after: `P27(X,Q142) <= P69(X,Q273626)` supports `('Q206832', 'P27', 'Q142')`; raw confidence 0.7777777777777778, support 14. Witness `[('Q206832', 'P69', 'Q273626')]`; removed training edges `[]`; survives=True.
- after: `P27(X,Q142) <= P119(X,Q311)` supports `('Q206832', 'P27', 'Q142')`; raw confidence 0.7142857142857143, support 15. Witness `[('Q206832', 'P119', 'Q311')]`; removed training edges `[]`; survives=True.
- after: `P27(X,Q142) <= P20(X,Q90)` supports `('Q8772', 'P27', 'Q142')`; raw confidence 0.7681159420289855, support 53. Witness `[('Q8772', 'P20', 'Q90')]`; removed training edges `[]`; survives=True.
- after: `P27(X,Q142) <= P172(X,Q121842)` supports `('Q8772', 'P27', 'Q142')`; raw confidence 0.8461538461538461, support 22. Witness `[('Q8772', 'P172', 'Q121842')]`; removed training edges `[]`; survives=True.
- after: `P27(X,Q142) <= P119(X,Q311)` supports `('Q8772', 'P27', 'Q142')`; raw confidence 0.7142857142857143, support 15. Witness `[('Q8772', 'P119', 'Q311')]`; removed training edges `[]`; survives=True.

A lost sampled witness does not imply all support disappeared: redundant witnesses or other rules may retain the candidate.

## targeted_local — top1_changed — test:1:tail

Query `(Q319374, P106, ?)`, correct triple `Q319374 P106 Q19723482`. Frozen-rule rank 8 → 7; Hits@1 0 → 0; correct-answer generation True → True.

Filtered top predictions `[['Q36834', 0.6787564766839378], ['Q33999', 0.6528776978417267]]` → `[['Q33999', 0.6528776978417267], ['Q36834', 0.5616438356164384]]`.

Training degrees (head/tail) 16/16 → 7/16; relation frequency 10197 → 9248. Directed typed two-/three-hop walks to truth 0/0 → 0/0. These walk counts are answer-dependent diagnostics, not counts of rule groundings.

- before: `P106(Q319374,Y) <= P106(Q272031,Y)` supports `('Q319374', 'P106', 'Q19723482')`; raw confidence 0.625, support 5. Witness `[('Q272031', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.
- before: `P106(Q319374,Y) <= P106(Q1373347,Y)` supports `('Q319374', 'P106', 'Q19723482')`; raw confidence 0.5714285714285714, support 4. Witness `[('Q1373347', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.
- before: `P106(Q319374,Y) <= P106(Q270935,Y)` supports `('Q319374', 'P106', 'Q19723482')`; raw confidence 0.5, support 5. Witness `[('Q270935', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.
- before: `P106(X,Q36834) <= P106(X,Q486748)` supports `('Q319374', 'P106', 'Q36834')`; raw confidence 0.6968085106382979, support 131. Witness `[('Q319374', 'P106', 'Q486748')]`; removed training edges `[('Q319374', 'P106', 'Q486748')]`; survives=False.
- before: `P106(X,Q36834) <= P1303(X,Q5994)` supports `('Q319374', 'P106', 'Q36834')`; raw confidence 0.6487603305785123, support 157. Witness `[('Q319374', 'P1303', 'Q5994')]`; removed training edges `[('Q319374', 'P1303', 'Q5994')]`; survives=False.
- before: `P106(X,Q36834) <= P106(X,Q488205)` supports `('Q319374', 'P106', 'Q36834')`; raw confidence 0.5725593667546174, support 217. Witness `[('Q319374', 'P106', 'Q488205')]`; removed training edges `[('Q319374', 'P106', 'Q488205')]`; survives=False.
- before: `P106(X,Q33999) <= P1303(X,Q17172850)` supports `('Q319374', 'P106', 'Q33999')`; raw confidence 0.6588021778584392, support 363. Witness `[('Q319374', 'P1303', 'Q17172850')]`; removed training edges `[]`; survives=True.
- before: `P106(X,Q33999) <= P106(X,Q177220)` supports `('Q319374', 'P106', 'Q33999')`; raw confidence 0.6586715867158671, support 357. Witness `[('Q319374', 'P106', 'Q177220')]`; removed training edges `[]`; survives=True.
- before: `P106(X,Q33999) <= P106(X,Q488205)` supports `('Q319374', 'P106', 'Q33999')`; raw confidence 0.6253298153034301, support 237. Witness `[('Q319374', 'P106', 'Q488205')]`; removed training edges `[('Q319374', 'P106', 'Q488205')]`; survives=False.
- before: `P106(Q319374,Y) <= P106(Q363371,Y)` supports `('Q319374', 'P106', 'Q11399')`; raw confidence 0.375, support 3. Witness `[('Q363371', 'P106', 'Q11399')]`; removed training edges `[('Q363371', 'P106', 'Q11399')]`; survives=False.
- before: `P106(Q319374,Y) <= P106(A,Y)` supports `('Q319374', 'P106', 'Q11399')`; raw confidence 0.0423728813559322, support 5. Witness `[('Q363371', 'P106', 'Q11399')]`; removed training edges `[('Q363371', 'P106', 'Q11399')]`; survives=False.
- after: `P106(Q319374,Y) <= P106(Q272031,Y)` supports `('Q319374', 'P106', 'Q19723482')`; raw confidence 0.625, support 5. Witness `[('Q272031', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.
- after: `P106(Q319374,Y) <= P106(Q1373347,Y)` supports `('Q319374', 'P106', 'Q19723482')`; raw confidence 0.5714285714285714, support 4. Witness `[('Q1373347', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.
- after: `P106(Q319374,Y) <= P106(Q270935,Y)` supports `('Q319374', 'P106', 'Q19723482')`; raw confidence 0.5, support 5. Witness `[('Q270935', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.
- after: `P106(X,Q36834) <= P106(X,Q855091)` supports `('Q319374', 'P106', 'Q36834')`; raw confidence 0.5747663551401869, support 123. Witness `[('Q319374', 'P106', 'Q855091')]`; removed training edges `[]`; survives=True.
- after: `P106(X,Q36834) <= P106(X,Q177220)` supports `('Q319374', 'P106', 'Q36834')`; raw confidence 0.511070110701107, support 277. Witness `[('Q319374', 'P106', 'Q177220')]`; removed training edges `[]`; survives=True.
- after: `P106(X,Q36834) <= P1303(X,Q17172850)` supports `('Q319374', 'P106', 'Q36834')`; raw confidence 0.5027223230490018, support 277. Witness `[('Q319374', 'P1303', 'Q17172850')]`; removed training edges `[]`; survives=True.
- after: `P106(X,Q33999) <= P1303(X,Q17172850)` supports `('Q319374', 'P106', 'Q33999')`; raw confidence 0.6588021778584392, support 363. Witness `[('Q319374', 'P1303', 'Q17172850')]`; removed training edges `[]`; survives=True.
- after: `P106(X,Q33999) <= P106(X,Q177220)` supports `('Q319374', 'P106', 'Q33999')`; raw confidence 0.6586715867158671, support 357. Witness `[('Q319374', 'P106', 'Q177220')]`; removed training edges `[]`; survives=True.
- after: `P106(X,Q33999) <= P27(X,Q30)` supports `('Q319374', 'P106', 'Q33999')`; raw confidence 0.5227272727272727, support 322. Witness `[('Q319374', 'P27', 'Q30')]`; removed training edges `[]`; survives=True.

A lost sampled witness does not imply all support disappeared: redundant witnesses or other rules may retain the candidate.

## targeted_local — top1_success_gained — test:12:head

Query `(?, P264, Q387539)`, correct triple `Q210172 P264 Q387539`. Frozen-rule rank 2 → 1; Hits@1 0 → 1; correct-answer generation True → True.

Filtered top predictions `[['Q294144', 0.2631578947368421], ['Q210172', 0.2631578947368421]]` → `[['Q210172', 0.2631578947368421], ['Q230943', 0.2631578947368421]]`.

Training degrees (head/tail) 23/15 → 23/13; relation frequency 879 → 833. Directed typed two-/three-hop walks to truth 2/5 → 2/5. These walk counts are answer-dependent diagnostics, not counts of rule groundings.

- before: `P264(X,Q387539) <= P264(X,Q54860)` supports `('Q210172', 'P264', 'Q387539')`; raw confidence 0.35714285714285715, support 5. Witness `[('Q210172', 'P264', 'Q54860')]`; removed training edges `[]`; survives=True.
- before: `P264(X,Q387539) <= P551(X,Q65)` supports `('Q210172', 'P264', 'Q387539')`; raw confidence 0.1111111111111111, support 5. Witness `[('Q210172', 'P551', 'Q65')]`; removed training edges `[]`; survives=True.
- before: `P264(X,Q387539) <= P106(X,Q2405480)` supports `('Q210172', 'P264', 'Q387539')`; raw confidence 0.03896103896103896, support 6. Witness `[('Q210172', 'P106', 'Q2405480')]`; removed training edges `[]`; survives=True.
- before: `P264(X,Q387539) <= P264(X,Q54860)` supports `('Q294144', 'P264', 'Q387539')`; raw confidence 0.35714285714285715, support 5. Witness `[('Q294144', 'P264', 'Q54860')]`; removed training edges `[]`; survives=True.
- before: `P264(Q294144,Y) <= P17(Y,Q30)` supports `('Q294144', 'P264', 'Q387539')`; raw confidence 0.11428571428571428, support 4. Witness `[('Q387539', 'P17', 'Q30')]`; removed training edges `[('Q387539', 'P17', 'Q30')]`; survives=False.
- before: `P264(X,Q387539) <= P136(X,Q850412)` supports `('Q294144', 'P264', 'Q387539')`; raw confidence 0.07936507936507936, support 5. Witness `[('Q294144', 'P136', 'Q850412')]`; removed training edges `[('Q294144', 'P136', 'Q850412')]`; survives=False.
- before: `P264(X,Q387539) <= P136(X,A)` supports `('Q208909', 'P264', 'Q387539')`; raw confidence 0.016150740242261104, support 12. Witness `[('Q208909', 'P136', 'Q11399')]`; removed training edges `[('Q208909', 'P136', 'Q11399')]`; survives=False.
- after: `P264(X,Q387539) <= P264(X,Q54860)` supports `('Q210172', 'P264', 'Q387539')`; raw confidence 0.35714285714285715, support 5. Witness `[('Q210172', 'P264', 'Q54860')]`; removed training edges `[]`; survives=True.
- after: `P264(X,Q387539) <= P551(X,Q65)` supports `('Q210172', 'P264', 'Q387539')`; raw confidence 0.1111111111111111, support 5. Witness `[('Q210172', 'P551', 'Q65')]`; removed training edges `[]`; survives=True.
- after: `P264(X,Q387539) <= P106(X,Q2405480)` supports `('Q210172', 'P264', 'Q387539')`; raw confidence 0.03896103896103896, support 6. Witness `[('Q210172', 'P106', 'Q2405480')]`; removed training edges `[]`; survives=True.
- after: `P264(X,Q387539) <= P264(X,Q54860)` supports `('Q294144', 'P264', 'Q387539')`; raw confidence 0.35714285714285715, support 5. Witness `[('Q294144', 'P264', 'Q54860')]`; removed training edges `[]`; survives=True.
- after: `P264(X,Q387539) <= P106(X,Q2405480)` supports `('Q294144', 'P264', 'Q387539')`; raw confidence 0.03896103896103896, support 6. Witness `[('Q294144', 'P106', 'Q2405480')]`; removed training edges `[]`; survives=True.
- after: `P264(X,Q387539) <= P136(X,Q37073)` supports `('Q294144', 'P264', 'Q387539')`; raw confidence 0.03669724770642202, support 8. Witness `[('Q294144', 'P136', 'Q37073')]`; removed training edges `[]`; survives=True.

A lost sampled witness does not imply all support disappeared: redundant witnesses or other rules may retain the candidate.

## targeted_local — top1_success_lost — test:72:tail

Query `(Q30, P530, ?)`, correct triple `Q30 P530 Q142`. Frozen-rule rank 1 → 5; Hits@1 1 → 0; correct-answer generation True → True.

Filtered top predictions `[['Q142', 0.88125], ['Q929', 0.88125]]` → `[['Q929', 0.88125], ['Q241', 0.82]]`.

Training degrees (head/tail) 1008/325 → 501/176; relation frequency 5563 → 5137. Directed typed two-/three-hop walks to truth 66/2589 → 19/600. These walk counts are answer-dependent diagnostics, not counts of rule groundings.

- before: `P530(Q30,Y) <= P530(Y,Q30)` supports `('Q30', 'P530', 'Q142')`; raw confidence 0.9096774193548387, support 141. Witness `[('Q142', 'P530', 'Q30')]`; removed training edges `[('Q142', 'P530', 'Q30')]`; survives=False.
- before: `P530(X,Q142) <= P530(Q142,X)` supports `('Q30', 'P530', 'Q142')`; raw confidence 0.891566265060241, support 74. Witness `[('Q142', 'P530', 'Q30')]`; removed training edges `[('Q142', 'P530', 'Q30')]`; survives=False.
- before: `P530(Q30,Y) <= P530(Y,Q29)` supports `('Q30', 'P530', 'Q142')`; raw confidence 0.9111111111111111, support 41. Witness `[('Q142', 'P530', 'Q29')]`; removed training edges `[]`; survives=True.
- before: `P530(Q30,Y) <= P530(Y,Q30)` supports `('Q30', 'P530', 'Q929')`; raw confidence 0.9096774193548387, support 141. Witness `[('Q929', 'P530', 'Q30')]`; removed training edges `[]`; survives=True.
- before: `P530(Q30,Y) <= P530(Q423,Y)` supports `('Q30', 'P530', 'Q929')`; raw confidence 0.8823529411764706, support 45. Witness `[('Q423', 'P530', 'Q929')]`; removed training edges `[]`; survives=True.
- before: `P530(Q30,Y) <= P530(Y,Q423)` supports `('Q30', 'P530', 'Q929')`; raw confidence 0.8775510204081632, support 43. Witness `[('Q929', 'P530', 'Q423')]`; removed training edges `[]`; survives=True.
- before: `P530(Q30,Y) <= P530(Q148,Y)` supports `('Q30', 'P530', 'Q15')`; raw confidence 0.8257575757575758, support 109. Witness `[('Q148', 'P530', 'Q15')]`; removed training edges `[('Q148', 'P530', 'Q15')]`; survives=False.
- before: `P530(Q30,Y) <= P530(A,Y)` supports `('Q30', 'P530', 'Q15')`; raw confidence 0.7571428571428571, support 159. Witness `[('Q148', 'P530', 'Q15')]`; removed training edges `[('Q148', 'P530', 'Q15')]`; survives=False.
- after: `P530(Q30,Y) <= P530(Y,Q29)` supports `('Q30', 'P530', 'Q142')`; raw confidence 0.9111111111111111, support 41. Witness `[('Q142', 'P530', 'Q29')]`; removed training edges `[]`; survives=True.
- after: `P530(Q30,Y) <= P463(Y,Q1043527)` supports `('Q30', 'P530', 'Q142')`; raw confidence 0.8148148148148148, support 132. Witness `[('Q142', 'P463', 'Q1043527')]`; removed training edges `[]`; survives=True.
- after: `P530(Q30,Y) <= P463(Y,Q340195)` supports `('Q30', 'P530', 'Q142')`; raw confidence 0.8378378378378378, support 62. Witness `[('Q142', 'P463', 'Q340195')]`; removed training edges `[]`; survives=True.
- after: `P530(Q30,Y) <= P530(Y,Q30)` supports `('Q30', 'P530', 'Q929')`; raw confidence 0.9096774193548387, support 141. Witness `[('Q929', 'P530', 'Q30')]`; removed training edges `[]`; survives=True.
- after: `P530(Q30,Y) <= P530(Q423,Y)` supports `('Q30', 'P530', 'Q929')`; raw confidence 0.8823529411764706, support 45. Witness `[('Q423', 'P530', 'Q929')]`; removed training edges `[]`; survives=True.
- after: `P530(Q30,Y) <= P530(Y,Q423)` supports `('Q30', 'P530', 'Q929')`; raw confidence 0.8775510204081632, support 43. Witness `[('Q929', 'P530', 'Q423')]`; removed training edges `[]`; survives=True.

A lost sampled witness does not imply all support disappeared: redundant witnesses or other rules may retain the candidate.

## targeted_relation_matched_control — candidate_support_lost — test:0:head

Query `(?, P27, Q142)`, correct triple `Q206832 P27 Q142`. Frozen-rule rank 3 → 2; Hits@1 0 → 0; correct-answer generation True → True.

Filtered top predictions `[['Q8772', 0.7162162162162162], ['Q37327', 0.7162162162162162]]` → `[['Q8772', 0.7162162162162162], ['Q206832', 0.7162162162162162]]`.

Training degrees (head/tail) 13/325 → 13/289; relation frequency 1648 → 1198. Directed typed two-/three-hop walks to truth 2/3 → 2/3. These walk counts are answer-dependent diagnostics, not counts of rule groundings.

- before: `P27(X,Q142) <= P20(X,Q90)` supports `('Q206832', 'P27', 'Q142')`; raw confidence 0.7681159420289855, support 53. Witness `[('Q206832', 'P20', 'Q90')]`; removed training edges `[]`; survives=True.
- before: `P27(X,Q142) <= P69(X,Q273626)` supports `('Q206832', 'P27', 'Q142')`; raw confidence 0.7777777777777778, support 14. Witness `[('Q206832', 'P69', 'Q273626')]`; removed training edges `[]`; survives=True.
- before: `P27(X,Q142) <= P119(X,Q311)` supports `('Q206832', 'P27', 'Q142')`; raw confidence 0.7142857142857143, support 15. Witness `[('Q206832', 'P119', 'Q311')]`; removed training edges `[]`; survives=True.
- before: `P27(X,Q142) <= P20(X,Q90)` supports `('Q8772', 'P27', 'Q142')`; raw confidence 0.7681159420289855, support 53. Witness `[('Q8772', 'P20', 'Q90')]`; removed training edges `[]`; survives=True.
- before: `P27(X,Q142) <= P172(X,Q121842)` supports `('Q8772', 'P27', 'Q142')`; raw confidence 0.8461538461538461, support 22. Witness `[('Q8772', 'P172', 'Q121842')]`; removed training edges `[('Q8772', 'P172', 'Q121842')]`; survives=False.
- before: `P27(X,Q142) <= P463(X,Q161806)` supports `('Q8772', 'P27', 'Q142')`; raw confidence 0.8095238095238095, support 17. Witness `[('Q8772', 'P463', 'Q161806')]`; removed training edges `[]`; survives=True.
- before: `P27(X,Q142) <= P737(A,X)` supports `('Q21', 'P27', 'Q142')`; raw confidence 0.1115702479338843, support 27. Witness `[('Q7302', 'P737', 'Q21')]`; removed training edges `[('Q7302', 'P737', 'Q21')]`; survives=False.
- after: `P27(X,Q142) <= P20(X,Q90)` supports `('Q206832', 'P27', 'Q142')`; raw confidence 0.7681159420289855, support 53. Witness `[('Q206832', 'P20', 'Q90')]`; removed training edges `[]`; survives=True.
- after: `P27(X,Q142) <= P69(X,Q273626)` supports `('Q206832', 'P27', 'Q142')`; raw confidence 0.7777777777777778, support 14. Witness `[('Q206832', 'P69', 'Q273626')]`; removed training edges `[]`; survives=True.
- after: `P27(X,Q142) <= P119(X,Q311)` supports `('Q206832', 'P27', 'Q142')`; raw confidence 0.7142857142857143, support 15. Witness `[('Q206832', 'P119', 'Q311')]`; removed training edges `[]`; survives=True.
- after: `P27(X,Q142) <= P20(X,Q90)` supports `('Q8772', 'P27', 'Q142')`; raw confidence 0.7681159420289855, support 53. Witness `[('Q8772', 'P20', 'Q90')]`; removed training edges `[]`; survives=True.
- after: `P27(X,Q142) <= P463(X,Q161806)` supports `('Q8772', 'P27', 'Q142')`; raw confidence 0.8095238095238095, support 17. Witness `[('Q8772', 'P463', 'Q161806')]`; removed training edges `[]`; survives=True.
- after: `P27(X,Q142) <= P119(X,Q311)` supports `('Q8772', 'P27', 'Q142')`; raw confidence 0.7142857142857143, support 15. Witness `[('Q8772', 'P119', 'Q311')]`; removed training edges `[]`; survives=True.

A lost sampled witness does not imply all support disappeared: redundant witnesses or other rules may retain the candidate.

## targeted_relation_matched_control — top1_changed — test:1:head

Query `(?, P106, Q19723482)`, correct triple `Q319374 P106 Q19723482`. Frozen-rule rank 143 → 120; Hits@1 0 → 0; correct-answer generation True → True.

Filtered top predictions `[['Q219631', 0.5714285714285714], ['Q201656', 0.5714285714285714]]` → `[['Q484523', 0.5625], ['Q144622', 0.5625]]`.

Training degrees (head/tail) 16/16 → 15/13; relation frequency 10197 → 9248. Directed typed two-/three-hop walks to truth 0/0 → 0/0. These walk counts are answer-dependent diagnostics, not counts of rule groundings.

- before: `P106(Q319374,Y) <= P106(Q272031,Y)` supports `('Q319374', 'P106', 'Q19723482')`; raw confidence 0.625, support 5. Witness `[('Q272031', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.
- before: `P106(Q319374,Y) <= P106(Q1373347,Y)` supports `('Q319374', 'P106', 'Q19723482')`; raw confidence 0.5714285714285714, support 4. Witness `[('Q1373347', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.
- before: `P106(Q319374,Y) <= P106(Q270935,Y)` supports `('Q319374', 'P106', 'Q19723482')`; raw confidence 0.5, support 5. Witness `[('Q270935', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.
- before: `P106(Q219631,Y) <= P106(Q233946,Y)` supports `('Q219631', 'P106', 'Q19723482')`; raw confidence 0.8888888888888888, support 8. Witness `[('Q233946', 'P106', 'Q19723482')]`; removed training edges `[('Q233946', 'P106', 'Q19723482')]`; survives=False.
- before: `P106(Q219631,Y) <= P106(Q210172,Y)` supports `('Q219631', 'P106', 'Q19723482')`; raw confidence 0.7272727272727273, support 8. Witness `[('Q210172', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.
- before: `P106(Q219631,Y) <= P106(Q194045,Y)` supports `('Q219631', 'P106', 'Q19723482')`; raw confidence 0.75, support 6. Witness `[('Q194045', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.
- before: `P106(Q484523,Y) <= P106(Q210172,Y)` supports `('Q484523', 'P106', 'Q19723482')`; raw confidence 0.8181818181818182, support 9. Witness `[('Q210172', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.
- before: `P106(Q484523,Y) <= P106(Q194045,Y)` supports `('Q484523', 'P106', 'Q19723482')`; raw confidence 0.75, support 6. Witness `[('Q194045', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.
- before: `P106(Q484523,Y) <= P106(Q1373347,Y)` supports `('Q484523', 'P106', 'Q19723482')`; raw confidence 0.5714285714285714, support 4. Witness `[('Q1373347', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.
- before: `P106(X,Q19723482) <= P136(X,A)` supports `('Q387539', 'P106', 'Q19723482')`; raw confidence 0.021505376344086023, support 16. Witness `[('Q387539', 'P136', 'Q38848')]`; removed training edges `[('Q387539', 'P136', 'Q38848')]`; survives=False.
- after: `P106(Q319374,Y) <= P106(Q272031,Y)` supports `('Q319374', 'P106', 'Q19723482')`; raw confidence 0.625, support 5. Witness `[('Q272031', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.
- after: `P106(Q319374,Y) <= P106(Q1373347,Y)` supports `('Q319374', 'P106', 'Q19723482')`; raw confidence 0.5714285714285714, support 4. Witness `[('Q1373347', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.
- after: `P106(Q319374,Y) <= P106(Q270935,Y)` supports `('Q319374', 'P106', 'Q19723482')`; raw confidence 0.5, support 5. Witness `[('Q270935', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.
- after: `P106(Q219631,Y) <= P106(Q210172,Y)` supports `('Q219631', 'P106', 'Q19723482')`; raw confidence 0.7272727272727273, support 8. Witness `[('Q210172', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.
- after: `P106(Q219631,Y) <= P106(Q194045,Y)` supports `('Q219631', 'P106', 'Q19723482')`; raw confidence 0.75, support 6. Witness `[('Q194045', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.
- after: `P106(Q219631,Y) <= P106(Q270935,Y)` supports `('Q219631', 'P106', 'Q19723482')`; raw confidence 0.5, support 5. Witness `[('Q270935', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.
- after: `P106(Q484523,Y) <= P106(Q210172,Y)` supports `('Q484523', 'P106', 'Q19723482')`; raw confidence 0.8181818181818182, support 9. Witness `[('Q210172', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.
- after: `P106(Q484523,Y) <= P106(Q194045,Y)` supports `('Q484523', 'P106', 'Q19723482')`; raw confidence 0.75, support 6. Witness `[('Q194045', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.
- after: `P106(Q484523,Y) <= P106(Q1373347,Y)` supports `('Q484523', 'P106', 'Q19723482')`; raw confidence 0.5714285714285714, support 4. Witness `[('Q1373347', 'P106', 'Q19723482')]`; removed training edges `[]`; survives=True.

A lost sampled witness does not imply all support disappeared: redundant witnesses or other rules may retain the candidate.

## targeted_relation_matched_control — top1_success_lost — test:37:head

Query `(?, P27, Q43287)`, correct triple `Q44086 P27 Q43287`. Frozen-rule rank 1 → 3; Hits@1 1 → 0; correct-answer generation True → True.

Filtered top predictions `[['Q44086', 0.4666666666666667], ['Q77060', 0.4666666666666667]]` → `[['Q77060', 0.4666666666666667], ['Q157318', 0.4666666666666667]]`.

Training degrees (head/tail) 17/27 → 16/25; relation frequency 1648 → 1198. Directed typed two-/three-hop walks to truth 2/1 → 2/1. These walk counts are answer-dependent diagnostics, not counts of rule groundings.

- before: `P27(X,Q43287) <= P27(X,Q7318)` supports `('Q44086', 'P27', 'Q43287')`; raw confidence 0.7, support 7. Witness `[('Q44086', 'P27', 'Q7318')]`; removed training edges `[('Q44086', 'P27', 'Q7318')]`; survives=False.
- before: `P27(X,Q43287) <= P27(X,Q41304)` supports `('Q44086', 'P27', 'Q43287')`; raw confidence 0.5555555555555556, support 10. Witness `[('Q44086', 'P27', 'Q41304')]`; removed training edges `[]`; survives=True.
- before: `P27(Q44086,Y) <= P27(Q57535,Y)` supports `('Q44086', 'P27', 'Q43287')`; raw confidence 0.8, support 4. Witness `[('Q57535', 'P27', 'Q43287')]`; removed training edges `[]`; survives=True.
- before: `P27(X,Q43287) <= P27(X,Q7318)` supports `('Q77060', 'P27', 'Q43287')`; raw confidence 0.7, support 7. Witness `[('Q77060', 'P27', 'Q7318')]`; removed training edges `[]`; survives=True.
- before: `P27(X,Q43287) <= P27(X,Q41304)` supports `('Q77060', 'P27', 'Q43287')`; raw confidence 0.5555555555555556, support 10. Witness `[('Q77060', 'P27', 'Q41304')]`; removed training edges `[]`; survives=True.
- before: `P27(Q77060,Y) <= P17(Q1726,Y)` supports `('Q77060', 'P27', 'Q43287')`; raw confidence 0.6, support 3. Witness `[('Q1726', 'P17', 'Q43287')]`; removed training edges `[]`; survives=True.
- before: `P27(X,Q43287) <= P737(A,X)` supports `('Q21', 'P27', 'Q43287')`; raw confidence 0.012345679012345678, support 3. Witness `[('Q7302', 'P737', 'Q21')]`; removed training edges `[('Q7302', 'P737', 'Q21')]`; survives=False.
- after: `P27(X,Q43287) <= P27(X,Q41304)` supports `('Q44086', 'P27', 'Q43287')`; raw confidence 0.5555555555555556, support 10. Witness `[('Q44086', 'P27', 'Q41304')]`; removed training edges `[]`; survives=True.
- after: `P27(Q44086,Y) <= P27(Q57535,Y)` supports `('Q44086', 'P27', 'Q43287')`; raw confidence 0.8, support 4. Witness `[('Q57535', 'P27', 'Q43287')]`; removed training edges `[]`; survives=True.
- after: `P27(Q44086,Y) <= P17(Q1726,Y)` supports `('Q44086', 'P27', 'Q43287')`; raw confidence 0.8, support 4. Witness `[('Q1726', 'P17', 'Q43287')]`; removed training edges `[]`; survives=True.
- after: `P27(X,Q43287) <= P27(X,Q7318)` supports `('Q77060', 'P27', 'Q43287')`; raw confidence 0.7, support 7. Witness `[('Q77060', 'P27', 'Q7318')]`; removed training edges `[]`; survives=True.
- after: `P27(X,Q43287) <= P27(X,Q41304)` supports `('Q77060', 'P27', 'Q43287')`; raw confidence 0.5555555555555556, support 10. Witness `[('Q77060', 'P27', 'Q41304')]`; removed training edges `[]`; survives=True.
- after: `P27(Q77060,Y) <= P17(Q1726,Y)` supports `('Q77060', 'P27', 'Q43287')`; raw confidence 0.6, support 3. Witness `[('Q1726', 'P17', 'Q43287')]`; removed training edges `[]`; survives=True.

A lost sampled witness does not imply all support disappeared: redundant witnesses or other rules may retain the candidate.

## targeted_relation_matched_control — top1_success_gained — test:99:tail

Query `(Q180962, P106, ?)`, correct triple `Q180962 P106 Q28389`. Frozen-rule rank 2 → 1; Hits@1 0 → 1; correct-answer generation True → True.

Filtered top predictions `[['Q10800557', 0.7969924812030075], ['Q28389', 0.7261146496815286]]` → `[['Q28389', 0.7261146496815286], ['Q10800557', 0.6698113207547169]]`.

Training degrees (head/tail) 35/313 → 30/271; relation frequency 10197 → 9248. Directed typed two-/three-hop walks to truth 6/3 → 4/3. These walk counts are answer-dependent diagnostics, not counts of rule groundings.

- before: `P106(X,Q28389) <= P106(X,Q2526255)` supports `('Q180962', 'P106', 'Q28389')`; raw confidence 0.75, support 114. Witness `[('Q180962', 'P106', 'Q2526255')]`; removed training edges `[]`; survives=True.
- before: `P106(X,Q28389) <= P106(X,Q7042855)` supports `('Q180962', 'P106', 'Q28389')`; raw confidence 0.8695652173913043, support 20. Witness `[('Q180962', 'P106', 'Q7042855')]`; removed training edges `[]`; survives=True.
- before: `P106(X,Q28389) <= P106(X,Q3282637)` supports `('Q180962', 'P106', 'Q28389')`; raw confidence 0.5652173913043478, support 117. Witness `[('Q180962', 'P106', 'Q3282637')]`; removed training edges `[]`; survives=True.
- before: `P106(X,Q10800557) <= P106(X,Q2259451)` supports `('Q180962', 'P106', 'Q10800557')`; raw confidence 0.828125, support 106. Witness `[('Q180962', 'P106', 'Q2259451')]`; removed training edges `[('Q180962', 'P106', 'Q2259451')]`; survives=False.
- before: `P106(X,Q10800557) <= P106(X,Q3282637)` supports `('Q180962', 'P106', 'Q10800557')`; raw confidence 0.6859903381642513, support 142. Witness `[('Q180962', 'P106', 'Q3282637')]`; removed training edges `[]`; survives=True.
- before: `P106(X,Q10800557) <= P106(X,Q2526255)` supports `('Q180962', 'P106', 'Q10800557')`; raw confidence 0.6513157894736842, support 99. Witness `[('Q180962', 'P106', 'Q2526255')]`; removed training edges `[]`; survives=True.
- after: `P106(X,Q28389) <= P106(X,Q2526255)` supports `('Q180962', 'P106', 'Q28389')`; raw confidence 0.75, support 114. Witness `[('Q180962', 'P106', 'Q2526255')]`; removed training edges `[]`; survives=True.
- after: `P106(X,Q28389) <= P106(X,Q7042855)` supports `('Q180962', 'P106', 'Q28389')`; raw confidence 0.8695652173913043, support 20. Witness `[('Q180962', 'P106', 'Q7042855')]`; removed training edges `[]`; survives=True.
- after: `P106(X,Q28389) <= P106(X,Q3282637)` supports `('Q180962', 'P106', 'Q28389')`; raw confidence 0.5652173913043478, support 117. Witness `[('Q180962', 'P106', 'Q3282637')]`; removed training edges `[]`; survives=True.
- after: `P106(X,Q10800557) <= P106(X,Q3282637)` supports `('Q180962', 'P106', 'Q10800557')`; raw confidence 0.6859903381642513, support 142. Witness `[('Q180962', 'P106', 'Q3282637')]`; removed training edges `[]`; survives=True.
- after: `P106(X,Q10800557) <= P106(X,Q2526255)` supports `('Q180962', 'P106', 'Q10800557')`; raw confidence 0.6513157894736842, support 99. Witness `[('Q180962', 'P106', 'Q2526255')]`; removed training edges `[]`; survives=True.
- after: `P106(X,Q10800557) <= P106(X,Q33999)` supports `('Q180962', 'P106', 'Q10800557')`; raw confidence 0.5716845878136201, support 319. Witness `[('Q180962', 'P106', 'Q33999')]`; removed training edges `[]`; survives=True.

A lost sampled witness does not imply all support disappeared: redundant witnesses or other rules may retain the candidate.

