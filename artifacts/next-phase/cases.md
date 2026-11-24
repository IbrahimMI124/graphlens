# Representative cases

Deterministic illustrative cases, not an estimate of group prevalence. All displayed grounding edges were checked against training positives. Original IDs are retained where labels were not downloaded.

## embedding_only_vs_general_rule: test:1006:head

Triple `Q948 P463 Q1043527`; predict **head**. Rule subset `general`; rule rank `4`, embedding seed-0 rank `1.0`. Raw scores: rule `0.650990099009901`, embedding `5.335060119628906`. These are not calibrated probabilities.

Rule top predictions: `[['Q1045', 0.6844106463878327], ['Q219060', 0.6844106463878327], ['Q241', 0.6844106463878327]]`. Embedding top predictions: `[['Q948', 5.335060119628906], ['Q1045', 5.312686443328857], ['Q230', 5.145418643951416]]`.

Training graph characteristics: `{'head_degree': 52, 'tail_degree': 163, 'head_in_degree': 17, 'head_out_degree': 35, 'tail_in_degree': 163, 'tail_out_degree': 0, 'known_degree_group': 'high', 'target_degree_group': 'high', 'directed_twohop_paths_to_truth': 12, 'undirected_common_neighbors_to_truth': 15, 'relation_frequency': 4985, 'tails_per_head': 7.9001584786053884, 'heads_per_tail': 56.64772727272727, 'cardinality': 'many-to-many', 'symmetry_strength': 0.0, 'symmetry_support': 0}`.

Prediction `Q948 P463 Q1043527`:

- `P463(X,Y) <= P463(X,A), P361(B,A), P463(B,Y)` (B, length 3, raw confidence 0.6537, support 789); training grounding examples: `[[['Q948', 'P463', 'Q7159'], ['Q1037', 'P361', 'Q7159'], ['Q1037', 'P463', 'Q1043527']]]`.
- `P463(X,Y) <= P463(X,A), P530(B,A), P463(B,Y)` (B, length 3, raw confidence 0.5737, support 588); training grounding examples: `[[['Q948', 'P463', 'Q7159'], ['Q155', 'P530', 'Q7159'], ['Q155', 'P463', 'Q1043527']], [['Q948', 'P463', 'Q7172'], ['Q159', 'P530', 'Q7172'], ['Q159', 'P463', 'Q1043527']]]`.
- `P463(X,Y) <= P37(X,A), P37(B,A), P463(B,Y)` (B, length 3, raw confidence 0.4950, support 990); training grounding examples: `[[['Q948', 'P37', 'Q13955'], ['Q398', 'P37', 'Q13955'], ['Q398', 'P463', 'Q1043527']], [['Q948', 'P37', 'Q13955'], ['Q1028', 'P37', 'Q13955'], ['Q1028', 'P463', 'Q1043527']]]`.

Prediction `Q1045 P463 Q1043527`:

- `P463(X,Y) <= P361(X,A), P361(B,A), P463(B,Y)` (B, length 3, raw confidence 0.6888, support 540); training grounding examples: `[[['Q1045', 'P361', 'Q27407'], ['Q1020', 'P361', 'Q27407'], ['Q1020', 'P463', 'Q1043527']], [['Q1045', 'P361', 'Q27407'], ['Q958', 'P361', 'Q27407'], ['Q958', 'P463', 'Q1043527']]]`.
- `P463(X,Y) <= P30(X,A), P138(B,A), P463(B,Y)` (B, length 3, raw confidence 0.6063, support 385); training grounding examples: `[[['Q1045', 'P30', 'Q15'], ['Q258', 'P138', 'Q15'], ['Q258', 'P463', 'Q1043527']]]`.
- `P463(X,Y) <= P463(X,A), P530(B,A), P463(B,Y)` (B, length 3, raw confidence 0.5737, support 588); training grounding examples: `[[['Q1045', 'P463', 'Q7172'], ['Q159', 'P530', 'Q7172'], ['Q159', 'P463', 'Q1043527']]]`.

Prediction `Q219060 P463 Q1043527`:

- `P463(X,Y) <= P361(X,A), P361(B,A), P463(B,Y)` (B, length 3, raw confidence 0.6888, support 540); training grounding examples: `[[['Q219060', 'P361', 'Q7204'], ['Q398', 'P361', 'Q7204'], ['Q398', 'P463', 'Q1043527']], [['Q219060', 'P361', 'Q7204'], ['Q43', 'P361', 'Q7204'], ['Q43', 'P463', 'Q1043527']]]`.
- `P463(X,Y) <= P463(X,A), P530(B,A), P463(B,Y)` (B, length 3, raw confidence 0.5737, support 588); training grounding examples: `[[['Q219060', 'P463', 'Q7172'], ['Q159', 'P530', 'Q7172'], ['Q159', 'P463', 'Q1043527']]]`.
- `P463(X,Y) <= P37(X,A), P37(B,A), P463(B,Y)` (B, length 3, raw confidence 0.4950, support 990); training grounding examples: `[[['Q219060', 'P37', 'Q13955'], ['Q398', 'P37', 'Q13955'], ['Q398', 'P463', 'Q1043527']], [['Q219060', 'P37', 'Q13955'], ['Q1028', 'P37', 'Q13955'], ['Q1028', 'P463', 'Q1043527']]]`.

## embedding_only_vs_general_rule: test:1016:tail

Triple `Q159 P530 Q27`; predict **tail**. Rule subset `general`; rule rank `2`, embedding seed-0 rank `1.0`. Raw scores: rule `0.8670062252405206`, embedding `6.786959648132324`. These are not calibrated probabilities.

Rule top predictions: `[['Q851', 0.8670062252405206], ['Q27', 0.8670062252405206], ['Q929', 0.8670062252405206]]`. Embedding top predictions: `[['Q27', 6.786959648132324], ['Q851', 6.443085670471191], ['Q230', 6.3300275802612305]]`.

Training graph characteristics: `{'head_degree': 345, 'tail_degree': 88, 'head_in_degree': 191, 'head_out_degree': 154, 'tail_in_degree': 35, 'tail_out_degree': 53, 'known_degree_group': 'high', 'target_degree_group': 'high', 'directed_twohop_paths_to_truth': 23, 'undirected_common_neighbors_to_truth': 43, 'relation_frequency': 5563, 'tails_per_head': 27.269607843137255, 'heads_per_tail': 26.364928909952607, 'cardinality': 'many-to-many', 'symmetry_strength': 0.8765054826532447, 'symmetry_support': 4876}`.

Prediction `Q159 P530 Q27`:

- `P530(X,Y) <= P530(Y,X)` (B, length 1, raw confidence 0.8695, support 1532); training grounding examples: `[[['Q27', 'P530', 'Q159']]]`.
- `P530(X,Y) <= P530(X,A), P361(B,A), P530(B,Y)` (B, length 3, raw confidence 0.3253, support 135); training grounding examples: `[[['Q159', 'P530', 'Q458'], ['Q145', 'P361', 'Q458'], ['Q145', 'P530', 'Q27']]]`.
- `P530(X,Y) <= P530(X,A), P530(A,B), P530(Y,B)` (B, length 3, raw confidence 0.3205, support 641); training grounding examples: `[[['Q159', 'P530', 'Q739'], ['Q739', 'P530', 'Q865'], ['Q27', 'P530', 'Q865']], [['Q159', 'P530', 'Q739'], ['Q739', 'P530', 'Q230'], ['Q27', 'P530', 'Q230']]]`.

Prediction `Q159 P530 Q851`:

- `P530(X,Y) <= P530(Y,X)` (B, length 1, raw confidence 0.8695, support 1532); training grounding examples: `[[['Q851', 'P530', 'Q159']]]`.
- `P530(X,Y) <= P530(X,A), P361(A,B), P361(Y,B)` (B, length 3, raw confidence 0.3270, support 566); training grounding examples: `[[['Q159', 'P530', 'Q398'], ['Q398', 'P361', 'Q7204'], ['Q851', 'P361', 'Q7204']], [['Q159', 'P530', 'Q43'], ['Q43', 'P361', 'Q7204'], ['Q851', 'P361', 'Q7204']]]`.
- `P530(X,Y) <= P530(X,A), P530(A,B), P530(Y,B)` (B, length 3, raw confidence 0.3205, support 641); training grounding examples: `[[['Q159', 'P530', 'Q739'], ['Q739', 'P530', 'Q865'], ['Q851', 'P530', 'Q865']], [['Q159', 'P530', 'Q739'], ['Q739', 'P530', 'Q213'], ['Q851', 'P530', 'Q213']]]`.

## general_only_vs_constant: test:1008:head

Triple `Q32 P530 Q148`; predict **head**. Rule subset `general`; rule rank `1`, embedding seed-0 rank `1.0`. Raw scores: rule `0.8670062252405206`, embedding `6.578068256378174`. These are not calibrated probabilities.

Rule top predictions: `[['Q32', 0.8670062252405206], ['Q15', 0.8670062252405206], ['Q142', 0.7127659574468085]]`. Embedding top predictions: `[['Q32', 6.578068256378174], ['Q865', 6.324450969696045], ['Q142', 6.2258195877075195]]`.

Training graph characteristics: `{'head_degree': 55, 'tail_degree': 282, 'head_in_degree': 12, 'head_out_degree': 43, 'tail_in_degree': 130, 'tail_out_degree': 152, 'known_degree_group': 'high', 'target_degree_group': 'high', 'directed_twohop_paths_to_truth': 6, 'undirected_common_neighbors_to_truth': 21, 'relation_frequency': 5563, 'tails_per_head': 27.269607843137255, 'heads_per_tail': 26.364928909952607, 'cardinality': 'many-to-many', 'symmetry_strength': 0.8765054826532447, 'symmetry_support': 4876}`.

Prediction `Q32 P530 Q148`:

- `P530(X,Y) <= P530(Y,X)` (B, length 1, raw confidence 0.8695, support 1532); training grounding examples: `[[['Q148', 'P530', 'Q32']]]`.
- `P530(X,Y) <= P530(A,X), P30(A,B), P530(Y,B)` (B, length 3, raw confidence 0.7528, support 67); training grounding examples: `[[['Q38', 'P530', 'Q32'], ['Q38', 'P30', 'Q15'], ['Q148', 'P530', 'Q15']], [['Q142', 'P530', 'Q32'], ['Q142', 'P30', 'Q15'], ['Q148', 'P530', 'Q15']]]`.
- `P530(X,Y) <= P530(X,A), P361(B,A), P530(B,Y)` (B, length 3, raw confidence 0.3253, support 135); training grounding examples: `[[['Q32', 'P530', 'Q458'], ['Q145', 'P361', 'Q458'], ['Q145', 'P530', 'Q148']]]`.

Prediction `Q15 P530 Q148`:

- `P530(X,Y) <= P530(Y,X)` (B, length 1, raw confidence 0.8695, support 1532); training grounding examples: `[[['Q148', 'P530', 'Q15']]]`.

## general_only_vs_constant: test:1011:tail

Triple `Q49001 P106 Q36180`; predict **tail**. Rule subset `general`; rule rank `1`, embedding seed-0 rank `2.0`. Raw scores: rule `0.27630922693266835`, embedding `6.567312240600586`. These are not calibrated probabilities.

Rule top predictions: `[['Q36180', 0.27630922693266835], ['Q33999', 0.27630922693266835], ['Q2526255', 0.27630922693266835]]`. Embedding top predictions: `[['Q33999', 7.274650573730469], ['Q36180', 6.567312240600586], ['Q639669', 5.946191787719727]]`.

Training graph characteristics: `{'head_degree': 24, 'tail_degree': 574, 'head_in_degree': 0, 'head_out_degree': 24, 'tail_in_degree': 574, 'tail_out_degree': 0, 'known_degree_group': 'high', 'target_degree_group': 'high', 'directed_twohop_paths_to_truth': 0, 'undirected_common_neighbors_to_truth': 0, 'relation_frequency': 10197, 'tails_per_head': 7.309677419354839, 'heads_per_tail': 86.41525423728814, 'cardinality': 'many-to-many', 'symmetry_strength': 0.0, 'symmetry_support': 0}`.

Prediction `Q49001 P106 Q36180`:

- `P106(X,Y) <= P101(X,A), P101(B,A), P106(B,Y)` (B, length 3, raw confidence 0.2770, support 554); training grounding examples: `[[['Q49001', 'P101', 'Q207628'], ['Q217427', 'P101', 'Q207628'], ['Q217427', 'P106', 'Q36180']], [['Q49001', 'P101', 'Q207628'], ['Q1744', 'P101', 'Q207628'], ['Q1744', 'P106', 'Q36180']]]`.
- `P106(X,Y) <= P1303(X,A), P1303(B,A), P106(B,Y)` (B, length 3, raw confidence 0.2730, support 546); training grounding examples: `[[['Q49001', 'P1303', 'Q17172850'], ['Q318509', 'P1303', 'Q17172850'], ['Q318509', 'P106', 'Q36180']], [['Q49001', 'P1303', 'Q17172850'], ['Q217427', 'P1303', 'Q17172850'], ['Q217427', 'P106', 'Q36180']]]`.
- `P106(X,Y) <= P264(X,A), P264(B,A), P106(B,Y)` (B, length 3, raw confidence 0.2660, support 532); training grounding examples: `[[['Q49001', 'P264', 'Q2338889'], ['Q1350303', 'P264', 'Q2338889'], ['Q1350303', 'P106', 'Q36180']], [['Q49001', 'P264', 'Q2338889'], ['Q726071', 'P264', 'Q2338889'], ['Q726071', 'P106', 'Q36180']]]`.

Prediction `Q49001 P106 Q33999`:

- `P106(X,Y) <= P101(X,A), P101(B,A), P106(B,Y)` (B, length 3, raw confidence 0.2770, support 554); training grounding examples: `[[['Q49001', 'P101', 'Q207628'], ['Q217427', 'P101', 'Q207628'], ['Q217427', 'P106', 'Q33999']], [['Q49001', 'P101', 'Q207628'], ['Q1624891', 'P101', 'Q207628'], ['Q1624891', 'P106', 'Q33999']]]`.
- `P106(X,Y) <= P1303(X,A), P1303(B,A), P106(B,Y)` (B, length 3, raw confidence 0.2730, support 546); training grounding examples: `[[['Q49001', 'P1303', 'Q17172850'], ['Q221364', 'P1303', 'Q17172850'], ['Q221364', 'P106', 'Q33999']], [['Q49001', 'P1303', 'Q17172850'], ['Q217427', 'P1303', 'Q17172850'], ['Q217427', 'P106', 'Q33999']]]`.
- `P106(X,Y) <= P264(X,A), P264(B,A), P106(B,Y)` (B, length 3, raw confidence 0.2660, support 532); training grounding examples: `[[['Q49001', 'P264', 'Q2338889'], ['Q12003', 'P264', 'Q2338889'], ['Q12003', 'P106', 'Q33999']], [['Q49001', 'P264', 'Q2338889'], ['Q162667', 'P264', 'Q2338889'], ['Q162667', 'P106', 'Q33999']]]`.

## general_rule_only_vs_embedding: test:1011:tail

Triple `Q49001 P106 Q36180`; predict **tail**. Rule subset `general`; rule rank `1`, embedding seed-0 rank `2.0`. Raw scores: rule `0.27630922693266835`, embedding `6.567312240600586`. These are not calibrated probabilities.

Rule top predictions: `[['Q36180', 0.27630922693266835], ['Q33999', 0.27630922693266835], ['Q2526255', 0.27630922693266835]]`. Embedding top predictions: `[['Q33999', 7.274650573730469], ['Q36180', 6.567312240600586], ['Q639669', 5.946191787719727]]`.

Training graph characteristics: `{'head_degree': 24, 'tail_degree': 574, 'head_in_degree': 0, 'head_out_degree': 24, 'tail_in_degree': 574, 'tail_out_degree': 0, 'known_degree_group': 'high', 'target_degree_group': 'high', 'directed_twohop_paths_to_truth': 0, 'undirected_common_neighbors_to_truth': 0, 'relation_frequency': 10197, 'tails_per_head': 7.309677419354839, 'heads_per_tail': 86.41525423728814, 'cardinality': 'many-to-many', 'symmetry_strength': 0.0, 'symmetry_support': 0}`.

Prediction `Q49001 P106 Q36180`:

- `P106(X,Y) <= P101(X,A), P101(B,A), P106(B,Y)` (B, length 3, raw confidence 0.2770, support 554); training grounding examples: `[[['Q49001', 'P101', 'Q207628'], ['Q217427', 'P101', 'Q207628'], ['Q217427', 'P106', 'Q36180']], [['Q49001', 'P101', 'Q207628'], ['Q1744', 'P101', 'Q207628'], ['Q1744', 'P106', 'Q36180']]]`.
- `P106(X,Y) <= P1303(X,A), P1303(B,A), P106(B,Y)` (B, length 3, raw confidence 0.2730, support 546); training grounding examples: `[[['Q49001', 'P1303', 'Q17172850'], ['Q318509', 'P1303', 'Q17172850'], ['Q318509', 'P106', 'Q36180']], [['Q49001', 'P1303', 'Q17172850'], ['Q217427', 'P1303', 'Q17172850'], ['Q217427', 'P106', 'Q36180']]]`.
- `P106(X,Y) <= P264(X,A), P264(B,A), P106(B,Y)` (B, length 3, raw confidence 0.2660, support 532); training grounding examples: `[[['Q49001', 'P264', 'Q2338889'], ['Q1350303', 'P264', 'Q2338889'], ['Q1350303', 'P106', 'Q36180']], [['Q49001', 'P264', 'Q2338889'], ['Q726071', 'P264', 'Q2338889'], ['Q726071', 'P106', 'Q36180']]]`.

Prediction `Q49001 P106 Q33999`:

- `P106(X,Y) <= P101(X,A), P101(B,A), P106(B,Y)` (B, length 3, raw confidence 0.2770, support 554); training grounding examples: `[[['Q49001', 'P101', 'Q207628'], ['Q217427', 'P101', 'Q207628'], ['Q217427', 'P106', 'Q33999']], [['Q49001', 'P101', 'Q207628'], ['Q1624891', 'P101', 'Q207628'], ['Q1624891', 'P106', 'Q33999']]]`.
- `P106(X,Y) <= P1303(X,A), P1303(B,A), P106(B,Y)` (B, length 3, raw confidence 0.2730, support 546); training grounding examples: `[[['Q49001', 'P1303', 'Q17172850'], ['Q221364', 'P1303', 'Q17172850'], ['Q221364', 'P106', 'Q33999']], [['Q49001', 'P1303', 'Q17172850'], ['Q217427', 'P1303', 'Q17172850'], ['Q217427', 'P106', 'Q33999']]]`.
- `P106(X,Y) <= P264(X,A), P264(B,A), P106(B,Y)` (B, length 3, raw confidence 0.2660, support 532); training grounding examples: `[[['Q49001', 'P264', 'Q2338889'], ['Q12003', 'P264', 'Q2338889'], ['Q12003', 'P106', 'Q33999']], [['Q49001', 'P264', 'Q2338889'], ['Q162667', 'P264', 'Q2338889'], ['Q162667', 'P106', 'Q33999']]]`.

## general_rule_only_vs_embedding: test:1025:tail

Triple `Q430922 P106 Q36180`; predict **tail**. Rule subset `general`; rule rank `1`, embedding seed-0 rank `3.0`. Raw scores: rule `0.20099750623441395`, embedding `5.3720293045043945`. These are not calibrated probabilities.

Rule top predictions: `[['Q36180', 0.20099750623441395], ['Q177220', 0.20099750623441395], ['Q639669', 0.20099750623441395]]`. Embedding top predictions: `[['Q177220', 6.1238603591918945], ['Q639669', 5.948569297790527], ['Q36180', 5.3720293045043945]]`.

Training graph characteristics: `{'head_degree': 11, 'tail_degree': 574, 'head_in_degree': 0, 'head_out_degree': 11, 'tail_in_degree': 574, 'tail_out_degree': 0, 'known_degree_group': 'low', 'target_degree_group': 'high', 'directed_twohop_paths_to_truth': 0, 'undirected_common_neighbors_to_truth': 0, 'relation_frequency': 10197, 'tails_per_head': 7.309677419354839, 'heads_per_tail': 86.41525423728814, 'cardinality': 'many-to-many', 'symmetry_strength': 0.0, 'symmetry_support': 0}`.

Prediction `Q430922 P106 Q36180`:

- `P106(X,Y) <= P106(X,A), P106(B,A), P106(B,Y)` (B, length 3, raw confidence 0.2015, support 403); training grounding examples: `[[['Q430922', 'P106', 'Q33999'], ['Q217427', 'P106', 'Q33999'], ['Q217427', 'P106', 'Q36180']], [['Q430922', 'P106', 'Q33999'], ['Q443995', 'P106', 'Q33999'], ['Q443995', 'P106', 'Q36180']]]`.
- `P106(X,Y) <= P172(X,A), P172(B,A), P106(B,Y)` (B, length 3, raw confidence 0.1860, support 372); training grounding examples: `[[['Q430922', 'P172', 'Q678551'], ['Q25089', 'P172', 'Q678551'], ['Q25089', 'P106', 'Q36180']], [['Q430922', 'P172', 'Q678551'], ['Q186485', 'P172', 'Q678551'], ['Q186485', 'P106', 'Q36180']]]`.
- `P106(X,Y) <= P106(X,A), P101(B,A), P106(B,Y)` (B, length 3, raw confidence 0.1634, support 198); training grounding examples: `[[['Q430922', 'P106', 'Q33999'], ['Q47899', 'P101', 'Q33999'], ['Q47899', 'P106', 'Q36180']], [['Q430922', 'P106', 'Q36834'], ['Q154770', 'P101', 'Q36834'], ['Q154770', 'P106', 'Q36180']]]`.

Prediction `Q430922 P106 Q177220`:

- `P106(X,Y) <= P106(X,A), P106(B,A), P106(B,Y)` (B, length 3, raw confidence 0.2015, support 403); training grounding examples: `[[['Q430922', 'P106', 'Q33999'], ['Q221364', 'P106', 'Q33999'], ['Q221364', 'P106', 'Q177220']], [['Q430922', 'P106', 'Q33999'], ['Q217427', 'P106', 'Q33999'], ['Q217427', 'P106', 'Q177220']]]`.
- `P106(X,Y) <= P172(X,A), P172(B,A), P106(B,Y)` (B, length 3, raw confidence 0.1860, support 372); training grounding examples: `[[['Q430922', 'P172', 'Q678551'], ['Q186485', 'P172', 'Q678551'], ['Q186485', 'P106', 'Q177220']], [['Q430922', 'P172', 'Q678551'], ['Q362332', 'P172', 'Q678551'], ['Q362332', 'P106', 'Q177220']]]`.
- `P106(X,Y) <= P106(X,A), P101(B,A), P106(B,Y)` (B, length 3, raw confidence 0.1634, support 198); training grounding examples: `[[['Q430922', 'P106', 'Q33999'], ['Q11637', 'P101', 'Q33999'], ['Q11637', 'P106', 'Q177220']], [['Q430922', 'P106', 'Q33999'], ['Q47899', 'P101', 'Q33999'], ['Q47899', 'P106', 'Q177220']]]`.

## constant_only_vs_general: test:1018:head

Triple `Q945 P463 Q7159`; predict **head**. Rule subset `constants`; rule rank `1`, embedding seed-0 rank `1.0`. Raw scores: rule `0.7407407407407407`, embedding `5.714731216430664`. These are not calibrated probabilities.

Rule top predictions: `[['Q945', 0.7407407407407407], ['Q29', 0.7241379310344828], ['Q142', 0.7241379310344828]]`. Embedding top predictions: `[['Q945', 5.714731216430664], ['Q858', 4.829095363616943], ['Q878', 4.815865516662598]]`.

Training graph characteristics: `{'head_degree': 28, 'tail_degree': 51, 'head_in_degree': 3, 'head_out_degree': 25, 'tail_in_degree': 51, 'tail_out_degree': 0, 'known_degree_group': 'high', 'target_degree_group': 'high', 'directed_twohop_paths_to_truth': 1, 'undirected_common_neighbors_to_truth': 1, 'relation_frequency': 4985, 'tails_per_head': 7.9001584786053884, 'heads_per_tail': 56.64772727272727, 'cardinality': 'many-to-many', 'symmetry_strength': 0.0, 'symmetry_support': 0}`.

Prediction `Q945 P463 Q7159`:

- `P463(X,Q7159) <= P463(X,Q3348506)` (Uc, length 1, raw confidence 0.9091, support 20); training grounding examples: `[[['Q945', 'P463', 'Q3348506']]]`.
- `P463(X,Q7159) <= P30(X,Q15)` (Uc, length 1, raw confidence 0.7925, support 42); training grounding examples: `[[['Q945', 'P30', 'Q15']]]`.
- `P463(Q945,Y) <= P463(Q967,Y)` (Uc, length 1, raw confidence 0.8750, support 14); training grounding examples: `[[['Q967', 'P463', 'Q7159']]]`.

Prediction `Q29 P463 Q7159`:

- `P463(X,Q7159) <= P30(X,Q15)` (Uc, length 1, raw confidence 0.7925, support 42); training grounding examples: `[[['Q29', 'P30', 'Q15']]]`.
- `P463(Q29,Y) <= P463(Q986,Y)` (Uc, length 1, raw confidence 0.9167, support 11); training grounding examples: `[[['Q986', 'P463', 'Q7159']]]`.
- `P463(Q29,Y) <= P463(Q1036,Y)` (Uc, length 1, raw confidence 0.8235, support 14); training grounding examples: `[[['Q1036', 'P463', 'Q7159']]]`.

## constant_only_vs_general: test:1018:tail

Triple `Q945 P463 Q7159`; predict **tail**. Rule subset `constants`; rule rank `1`, embedding seed-0 rank `1.0`. Raw scores: rule `0.7407407407407407`, embedding `6.532474994659424`. These are not calibrated probabilities.

Rule top predictions: `[['Q7159', 0.7407407407407407], ['Q5611262', 0.6538461538461539], ['Q816706', 0.625]]`. Embedding top predictions: `[['Q7159', 6.532474994659424], ['Q5611262', 6.015997886657715], ['Q496967', 5.222217559814453]]`.

Training graph characteristics: `{'head_degree': 28, 'tail_degree': 51, 'head_in_degree': 3, 'head_out_degree': 25, 'tail_in_degree': 51, 'tail_out_degree': 0, 'known_degree_group': 'high', 'target_degree_group': 'high', 'directed_twohop_paths_to_truth': 1, 'undirected_common_neighbors_to_truth': 1, 'relation_frequency': 4985, 'tails_per_head': 7.9001584786053884, 'heads_per_tail': 56.64772727272727, 'cardinality': 'many-to-many', 'symmetry_strength': 0.0, 'symmetry_support': 0}`.

Prediction `Q945 P463 Q7159`:

- `P463(X,Q7159) <= P463(X,Q3348506)` (Uc, length 1, raw confidence 0.9091, support 20); training grounding examples: `[[['Q945', 'P463', 'Q3348506']]]`.
- `P463(X,Q7159) <= P30(X,Q15)` (Uc, length 1, raw confidence 0.7925, support 42); training grounding examples: `[[['Q945', 'P30', 'Q15']]]`.
- `P463(Q945,Y) <= P463(Q967,Y)` (Uc, length 1, raw confidence 0.8750, support 14); training grounding examples: `[[['Q967', 'P463', 'Q7159']]]`.

Prediction `Q945 P463 Q5611262`:

- `P463(Q945,Y) <= P463(Q912,Y)` (Uc, length 1, raw confidence 0.8095, support 17); training grounding examples: `[[['Q912', 'P463', 'Q5611262']]]`.
- `P463(Q945,Y) <= P463(Q1041,Y)` (Uc, length 1, raw confidence 0.8333, support 15); training grounding examples: `[[['Q1041', 'P463', 'Q5611262']]]`.
- `P463(Q945,Y) <= P463(Q965,Y)` (Uc, length 1, raw confidence 0.8000, support 16); training grounding examples: `[[['Q965', 'P463', 'Q5611262']]]`.

## longer_general_1_to_3_improves: test:0:tail

Triple `Q206832 P27 Q142`; predict **tail**. Rule subset `general_le3`; rule rank `1`, embedding seed-0 rank `1.0`. Raw scores: rule `0.5429864253393665`, embedding `7.451595306396484`. These are not calibrated probabilities.

Rule top predictions: `[['Q142', 0.5429864253393665], ['Q30', 0.3687258687258687], ['Q145', 0.3687258687258687]]`. Embedding top predictions: `[['Q142', 7.451595306396484], ['Q29', 6.6829609870910645], ['Q183', 5.8928914070129395]]`.

Training graph characteristics: `{'head_degree': 13, 'tail_degree': 325, 'head_in_degree': 0, 'head_out_degree': 13, 'tail_in_degree': 203, 'tail_out_degree': 122, 'known_degree_group': 'low', 'target_degree_group': 'high', 'directed_twohop_paths_to_truth': 2, 'undirected_common_neighbors_to_truth': 2, 'relation_frequency': 1648, 'tails_per_head': 1.3068992862807296, 'heads_per_tail': 20.6, 'cardinality': 'many-to-one', 'symmetry_strength': 0.0, 'symmetry_support': 0}`.

Length-1-capped rule rank: `None`; top predictions: `[]`.

Prediction `Q206832 P27 Q142`:

- `P27(X,Y) <= P20(X,A), P159(B,A), P17(B,Y)` (B, length 3, raw confidence 0.5556, support 120); training grounding examples: `[[['Q206832', 'P20', 'Q90'], ['Q161806', 'P159', 'Q90'], ['Q161806', 'P17', 'Q142']], [['Q206832', 'P20', 'Q90'], ['Q188771', 'P159', 'Q90'], ['Q188771', 'P17', 'Q142']]]`.
- `P27(X,Y) <= P20(X,A), P17(A,Y)` (B, length 2, raw confidence 0.4444, support 148); training grounding examples: `[[['Q206832', 'P20', 'Q90'], ['Q90', 'P17', 'Q142']]]`.
- `P27(X,Y) <= P20(X,A), P20(B,A), P27(B,Y)` (B, length 3, raw confidence 0.3723, support 191); training grounding examples: `[[['Q206832', 'P20', 'Q90'], ['Q16409', 'P20', 'Q90'], ['Q16409', 'P27', 'Q142']], [['Q206832', 'P20', 'Q90'], ['Q1698', 'P20', 'Q90'], ['Q1698', 'P27', 'Q142']]]`.

Prediction `Q206832 P27 Q30`:

- `P27(X,Y) <= P20(X,A), P20(B,A), P27(B,Y)` (B, length 3, raw confidence 0.3723, support 191); training grounding examples: `[[['Q206832', 'P20', 'Q90'], ['Q44301', 'P20', 'Q90'], ['Q44301', 'P27', 'Q30']]]`.
- `P27(X,Y) <= P20(X,A), P19(B,A), P27(B,Y)` (B, length 3, raw confidence 0.3694, support 133); training grounding examples: `[[['Q206832', 'P20', 'Q90'], ['Q230068', 'P19', 'Q90'], ['Q230068', 'P27', 'Q30']], [['Q206832', 'P20', 'Q90'], ['Q110462', 'P19', 'Q90'], ['Q110462', 'P27', 'Q30']]]`.
- `P27(X,Y) <= P119(X,A), P119(B,A), P27(B,Y)` (B, length 3, raw confidence 0.3611, support 65); training grounding examples: `[[['Q206832', 'P119', 'Q311'], ['Q44301', 'P119', 'Q311'], ['Q44301', 'P27', 'Q30']], [['Q206832', 'P119', 'Q311'], ['Q313281', 'P119', 'Q311'], ['Q313281', 'P27', 'Q30']]]`.

## longer_general_1_to_3_hurts: test:51:head

Triple `Q29 P530 Q183`; predict **head**. Rule subset `general_le3`; rule rank `2`, embedding seed-0 rank `1.0`. Raw scores: rule `0.8670062252405206`, embedding `7.274780750274658`. These are not calibrated probabilities.

Rule top predictions: `[['Q159583', 0.8670062252405206], ['Q29', 0.8670062252405206], ['Q34266', 0.6571428571428571]]`. Embedding top predictions: `[['Q29', 7.274780750274658], ['Q183', 6.640718936920166], ['Q970', 5.715208053588867]]`.

Training graph characteristics: `{'head_degree': 137, 'tail_degree': 480, 'head_in_degree': 60, 'head_out_degree': 77, 'tail_in_degree': 279, 'tail_out_degree': 201, 'known_degree_group': 'high', 'target_degree_group': 'high', 'directed_twohop_paths_to_truth': 41, 'undirected_common_neighbors_to_truth': 74, 'relation_frequency': 5563, 'tails_per_head': 27.269607843137255, 'heads_per_tail': 26.364928909952607, 'cardinality': 'many-to-many', 'symmetry_strength': 0.8765054826532447, 'symmetry_support': 4876}`.

Length-1-capped rule rank: `1`; top predictions: `[['Q29', 0.8670062252405206], ['Q159583', 0.8670062252405206]]`.

Prediction `Q29 P530 Q183`:

- `P530(X,Y) <= P530(A,X), P495(B,A), P495(B,Y)` (B, length 3, raw confidence 0.6644, support 299); training grounding examples: `[[['Q408', 'P530', 'Q29'], ['Q220192', 'P495', 'Q408'], ['Q220192', 'P495', 'Q183']]]`.
- `P530(X,Y) <= P530(Y,X)` (B, length 1, raw confidence 0.8695, support 1532); training grounding examples: `[[['Q183', 'P530', 'Q29']]]`.
- `P530(X,Y) <= P530(X,A), P119(B,A), P27(B,Y)` (B, length 3, raw confidence 0.3333, support 84); training grounding examples: `[[['Q29', 'P530', 'Q36'], ['Q61863', 'P119', 'Q36'], ['Q61863', 'P27', 'Q183']]]`.

Prediction `Q159583 P530 Q183`:

- `P530(X,Y) <= P530(A,X), P495(B,A), P495(B,Y)` (B, length 3, raw confidence 0.6644, support 299); training grounding examples: `[[['Q408', 'P530', 'Q159583'], ['Q220192', 'P495', 'Q408'], ['Q220192', 'P495', 'Q183']]]`.
- `P530(X,Y) <= P530(Y,X)` (B, length 1, raw confidence 0.8695, support 1532); training grounding examples: `[[['Q183', 'P530', 'Q159583']]]`.
- `P530(X,Y) <= P530(A,X), P551(B,A), P27(B,Y)` (B, length 3, raw confidence 0.3339, support 182); training grounding examples: `[[['Q38', 'P530', 'Q159583'], ['Q7302', 'P551', 'Q38'], ['Q7302', 'P27', 'Q183']]]`.

## longer_fixed_constants_general_1_to_3_improves: test:12:head

Triple `Q210172 P264 Q387539`; predict **head**. Rule subset `fixed_constants_general_le3`; rule rank `1`, embedding seed-0 rank `1.0`. Raw scores: rule `0.3793103448275862`, embedding `6.941536903381348`. These are not calibrated probabilities.

Rule top predictions: `[['Q210172', 0.3793103448275862], ['Q34086', 0.34146341463414637], ['Q26876', 0.3142857142857143]]`. Embedding top predictions: `[['Q210172', 6.941536903381348], ['Q122020', 6.060158729553223], ['Q242792', 6.012055397033691]]`.

Training graph characteristics: `{'head_degree': 23, 'tail_degree': 15, 'head_in_degree': 2, 'head_out_degree': 21, 'tail_in_degree': 13, 'tail_out_degree': 2, 'known_degree_group': 'low', 'target_degree_group': 'high', 'directed_twohop_paths_to_truth': 2, 'undirected_common_neighbors_to_truth': 3, 'relation_frequency': 879, 'tails_per_head': 1.8583509513742071, 'heads_per_tail': 27.46875, 'cardinality': 'many-to-many', 'symmetry_strength': 0.0, 'symmetry_support': 0}`.

Length-1-capped rule rank: `2`; top predictions: `[['Q294144', 0.2631578947368421], ['Q210172', 0.2631578947368421], ['Q230943', 0.2631578947368421]]`.

Prediction `Q210172 P264 Q387539`:

- `P264(X,Y) <= P3373(A,X), P451(A,B), P264(B,Y)` (B, length 3, raw confidence 0.4583, support 11); training grounding examples: `[[['Q201656', 'P3373', 'Q210172'], ['Q201656', 'P451', 'Q83287'], ['Q83287', 'P264', 'Q387539']], [['Q191088', 'P3373', 'Q210172'], ['Q191088', 'P451', 'Q41173'], ['Q41173', 'P264', 'Q387539']]]`.
- `P264(X,Y) <= P3373(X,A), P264(A,Y)` (B, length 2, raw confidence 0.3871, support 24); training grounding examples: `[[['Q210172', 'P3373', 'Q201656'], ['Q201656', 'P264', 'Q387539']], [['Q210172', 'P3373', 'Q191088'], ['Q191088', 'P264', 'Q387539']]]`.
- `P264(X,Y) <= P3373(A,X), P264(A,Y)` (B, length 2, raw confidence 0.3509, support 20); training grounding examples: `[[['Q201656', 'P3373', 'Q210172'], ['Q201656', 'P264', 'Q387539']], [['Q191088', 'P3373', 'Q210172'], ['Q191088', 'P264', 'Q387539']]]`.

Prediction `Q34086 P264 Q387539`:

- `P264(X,Y) <= P451(X,A), P264(A,Y)` (B, length 2, raw confidence 0.3889, support 14); training grounding examples: `[[['Q34086', 'P451', 'Q83287'], ['Q83287', 'P264', 'Q387539']]]`.
- `P264(X,Y) <= P451(A,X), P264(A,Y)` (B, length 2, raw confidence 0.2308, support 12); training grounding examples: `[[['Q83287', 'P451', 'Q34086'], ['Q83287', 'P264', 'Q387539']]]`.
- `P264(X,Q387539) <= P136(X,Q850412)` (Uc, length 1, raw confidence 0.0794, support 5); training grounding examples: `[[['Q34086', 'P136', 'Q850412']]]`.

Prediction `Q294144 P264 Q387539`:

- `P264(X,Y) <= P136(X,A), P136(B,A), P264(B,Y)` (B, length 3, raw confidence 0.0675, support 135); training grounding examples: `[[['Q294144', 'P136', 'Q850412'], ['Q201656', 'P136', 'Q850412'], ['Q201656', 'P264', 'Q387539']], [['Q294144', 'P136', 'Q850412'], ['Q123174', 'P136', 'Q850412'], ['Q123174', 'P264', 'Q387539']]]`.
- `P264(X,Q387539) <= P264(X,Q54860)` (Uc, length 1, raw confidence 0.3571, support 5); training grounding examples: `[[['Q294144', 'P264', 'Q54860']]]`.
- `P264(Q294144,Y) <= P17(Y,Q30)` (Uc, length 1, raw confidence 0.1143, support 4); training grounding examples: `[[['Q387539', 'P17', 'Q30']]]`.

## longer_fixed_constants_general_1_to_3_hurts: test:37:head

Triple `Q44086 P27 Q43287`; predict **head**. Rule subset `fixed_constants_general_le3`; rule rank `5`, embedding seed-0 rank `1.0`. Raw scores: rule `0.4666666666666667`, embedding `6.874216079711914`. These are not calibrated probabilities.

Rule top predictions: `[['Q61597', 0.5333333333333333], ['Q77109', 0.5333333333333333], ['Q214191', 0.5333333333333333]]`. Embedding top predictions: `[['Q44086', 6.874216079711914], ['Q9387', 6.830778121948242], ['Q77060', 6.674202919006348]]`.

Training graph characteristics: `{'head_degree': 17, 'tail_degree': 27, 'head_in_degree': 0, 'head_out_degree': 17, 'tail_in_degree': 25, 'tail_out_degree': 2, 'known_degree_group': 'high', 'target_degree_group': 'medium', 'directed_twohop_paths_to_truth': 1, 'undirected_common_neighbors_to_truth': 2, 'relation_frequency': 1648, 'tails_per_head': 1.3068992862807296, 'heads_per_tail': 20.6, 'cardinality': 'many-to-one', 'symmetry_strength': 0.0, 'symmetry_support': 0}`.

Length-1-capped rule rank: `1`; top predictions: `[['Q44086', 0.4666666666666667], ['Q77060', 0.4666666666666667], ['Q157318', 0.4666666666666667]]`.

Prediction `Q44086 P27 Q43287`:

- `P27(X,Y) <= P19(X,A), P17(A,Y)` (B, length 2, raw confidence 0.4712, support 147); training grounding examples: `[[['Q44086', 'P19', 'Q1726'], ['Q1726', 'P17', 'Q43287']]]`.
- `P27(X,Q43287) <= P27(X,Q7318)` (Uc, length 1, raw confidence 0.7000, support 7); training grounding examples: `[[['Q44086', 'P27', 'Q7318']]]`.
- `P27(X,Y) <= P20(X,A), P17(A,Y)` (B, length 2, raw confidence 0.4444, support 148); training grounding examples: `[[['Q44086', 'P20', 'Q1726'], ['Q1726', 'P17', 'Q43287']]]`.

Prediction `Q61597 P27 Q43287`:

- `P27(X,Y) <= P40(A,X), P27(A,Y)` (B, length 2, raw confidence 0.6400, support 16); training grounding examples: `[[['Q37030', 'P40', 'Q61597'], ['Q37030', 'P27', 'Q43287']]]`.
- `P27(X,Y) <= P3373(X,A), P27(A,Y)` (B, length 2, raw confidence 0.5714, support 20); training grounding examples: `[[['Q61597', 'P3373', 'Q77087'], ['Q77087', 'P27', 'Q43287']]]`.
- `P27(X,Y) <= P19(X,A), P17(A,Y)` (B, length 2, raw confidence 0.4712, support 147); training grounding examples: `[[['Q61597', 'P19', 'Q1726'], ['Q1726', 'P17', 'Q43287']]]`.

Prediction `Q77109 P27 Q43287`:

- `P27(X,Y) <= P40(A,X), P27(A,Y)` (B, length 2, raw confidence 0.6400, support 16); training grounding examples: `[[['Q37030', 'P40', 'Q77109'], ['Q37030', 'P27', 'Q43287']]]`.
- `P27(X,Y) <= P3373(X,A), P27(A,Y)` (B, length 2, raw confidence 0.5714, support 20); training grounding examples: `[[['Q77109', 'P3373', 'Q77087'], ['Q77087', 'P27', 'Q43287']]]`.
- `P27(X,Y) <= P19(X,A), P17(A,Y)` (B, length 2, raw confidence 0.4712, support 147); training grounding examples: `[[['Q77109', 'P19', 'Q1726'], ['Q1726', 'P17', 'Q43287']]]`.

## longer_fixed_constants_general_2_to_3_improves: test:568:tail

Triple `Q17455 P27 Q28`; predict **tail**. Rule subset `fixed_constants_general_le3`; rule rank `1`, embedding seed-0 rank `7.0`. Raw scores: rule `0.5333333333333333`, embedding `6.613022327423096`. These are not calibrated probabilities.

Rule top predictions: `[['Q28', 0.5333333333333333], ['Q183', 0.5], ['Q142', 0.4492753623188406]]`. Embedding top predictions: `[['Q41304', 8.360123634338379], ['Q183', 7.840424537658691], ['Q36', 6.957963943481445]]`.

Training graph characteristics: `{'head_degree': 23, 'tail_degree': 200, 'head_in_degree': 0, 'head_out_degree': 23, 'tail_in_degree': 82, 'tail_out_degree': 118, 'known_degree_group': 'high', 'target_degree_group': 'high', 'directed_twohop_paths_to_truth': 2, 'undirected_common_neighbors_to_truth': 2, 'relation_frequency': 1648, 'tails_per_head': 1.3068992862807296, 'heads_per_tail': 20.6, 'cardinality': 'many-to-one', 'symmetry_strength': 0.0, 'symmetry_support': 0}`.

Length-2-capped rule rank: `2`; top predictions: `[['Q183', 0.5], ['Q28', 0.4637223974763407], ['Q142', 0.4492753623188406]]`.

Prediction `Q17455 P27 Q28`:

- `P27(X,Y) <= P19(X,A), P159(B,A), P17(B,Y)` (B, length 3, raw confidence 0.5455, support 120); training grounding examples: `[[['Q17455', 'P19', 'Q1781'], ['Q265058', 'P159', 'Q1781'], ['Q265058', 'P17', 'Q28']]]`.
- `P27(X,Y) <= P19(X,A), P17(A,Y)` (B, length 2, raw confidence 0.4712, support 147); training grounding examples: `[[['Q17455', 'P19', 'Q1781'], ['Q1781', 'P17', 'Q28']]]`.
- `P27(X,Q28) <= P19(X,Q1781)` (Uc, length 1, raw confidence 0.6667, support 6); training grounding examples: `[[['Q17455', 'P19', 'Q1781']]]`.

Prediction `Q17455 P27 Q183`:

- `P27(X,Y) <= P19(X,A), P19(B,A), P27(B,Y)` (B, length 3, raw confidence 0.4159, support 183); training grounding examples: `[[['Q17455', 'P19', 'Q1781'], ['Q76823', 'P19', 'Q1781'], ['Q76823', 'P27', 'Q183']], [['Q17455', 'P19', 'Q1781'], ['Q153238', 'P19', 'Q1781'], ['Q153238', 'P27', 'Q183']]]`.
- `P27(X,Q183) <= P69(X,Q152838)` (Uc, length 1, raw confidence 0.5862, support 17); training grounding examples: `[[['Q17455', 'P69', 'Q152838']]]`.
- `P27(X,Q183) <= P108(X,Q152087)` (Uc, length 1, raw confidence 0.5000, support 14); training grounding examples: `[[['Q17455', 'P108', 'Q152087']]]`.

## longer_fixed_constants_general_2_to_3_hurts: test:50:head

Triple `Q574 P37 Q5146`; predict **head**. Rule subset `fixed_constants_general_le3`; rule rank `42`, embedding seed-0 rank `96.0`. Raw scores: rule `0.4117647058823529`, embedding `3.6937665939331055`. These are not calibrated probabilities.

Rule top predictions: `[['Q117', 0.4382716049382716], ['Q739', 0.4382716049382716], ['Q414', 0.4382716049382716]]`. Embedding top predictions: `[['Q1041', 6.278402805328369], ['Q1025', 6.134648323059082], ['Q962', 6.106264114379883]]`.

Training graph characteristics: `{'head_degree': 35, 'tail_degree': 28, 'head_in_degree': 12, 'head_out_degree': 23, 'tail_in_degree': 28, 'tail_out_degree': 0, 'known_degree_group': 'high', 'target_degree_group': 'high', 'directed_twohop_paths_to_truth': 3, 'undirected_common_neighbors_to_truth': 3, 'relation_frequency': 182, 'tails_per_head': 1.1666666666666667, 'heads_per_tail': 13.0, 'cardinality': 'many-to-one', 'symmetry_strength': 0.0, 'symmetry_support': 0}`.

Length-2-capped rule rank: `1`; top predictions: `[['Q574', 0.4117647058823529], ['Q244', 0.4117647058823529], ['Q117', 0.4117647058823529]]`.

Prediction `Q574 P37 Q5146`:

- `P37(X,Y) <= P17(X,A), P17(B,A), P37(B,Y)` (B, length 3, raw confidence 0.2097, support 13); training grounding examples: `[[['Q574', 'P17', 'Q200464'], ['Q1007', 'P17', 'Q200464'], ['Q1007', 'P37', 'Q5146']], [['Q574', 'P17', 'Q200464'], ['Q983', 'P17', 'Q200464'], ['Q983', 'P37', 'Q5146']]]`.
- `P37(X,Q5146) <= P17(X,Q200464)` (Uc, length 1, raw confidence 0.5833, support 7); training grounding examples: `[[['Q574', 'P17', 'Q200464']]]`.
- `P37(X,Y) <= P530(A,X), P37(A,Y)` (B, length 2, raw confidence 0.1933, support 92); training grounding examples: `[[['Q45', 'P530', 'Q574'], ['Q45', 'P37', 'Q5146']], [['Q155', 'P530', 'Q574'], ['Q155', 'P37', 'Q5146']]]`.

Prediction `Q117 P37 Q5146`:

- `P37(X,Y) <= P361(X,A), P361(B,A), P37(B,Y)` (B, length 3, raw confidence 0.4522, support 71); training grounding examples: `[[['Q117', 'P361', 'Q4412'], ['Q1007', 'P361', 'Q4412'], ['Q1007', 'P37', 'Q5146']], [['Q117', 'P361', 'Q4412'], ['Q1011', 'P361', 'Q4412'], ['Q1011', 'P37', 'Q5146']]]`.
- `P37(X,Q5146) <= P17(X,Q200464)` (Uc, length 1, raw confidence 0.5833, support 7); training grounding examples: `[[['Q117', 'P17', 'Q200464']]]`.
- `P37(X,Y) <= P17(X,A), P17(B,A), P37(B,Y)` (B, length 3, raw confidence 0.2097, support 13); training grounding examples: `[[['Q117', 'P17', 'Q200464'], ['Q1007', 'P17', 'Q200464'], ['Q1007', 'P37', 'Q5146']], [['Q117', 'P17', 'Q200464'], ['Q983', 'P17', 'Q200464'], ['Q983', 'P37', 'Q5146']]]`.

Prediction `Q739 P37 Q5146`:

- `P37(X,Y) <= P361(X,A), P361(B,A), P37(B,Y)` (B, length 3, raw confidence 0.4522, support 71); training grounding examples: `[[['Q739', 'P361', 'Q12585'], ['Q155', 'P361', 'Q12585'], ['Q155', 'P37', 'Q5146']]]`.
- `P37(X,Y) <= P27(A,X), P1412(A,Y)` (B, length 2, raw confidence 0.3790, support 47); training grounding examples: `[[['Q34424', 'P27', 'Q739'], ['Q34424', 'P1412', 'Q5146']]]`.
- `P37(X,Y) <= P530(A,X), P37(A,Y)` (B, length 2, raw confidence 0.1933, support 92); training grounding examples: `[[['Q155', 'P530', 'Q739'], ['Q155', 'P37', 'Q5146']]]`.
