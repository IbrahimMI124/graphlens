# Comparative protocol and research grounding

The next-phase audit and versioned corrections are documented in
[NEXT_PHASE.md](NEXT_PHASE.md). In particular, new frozen rule ablations use a
candidate limit above the entire entity universe with executable completeness
checks; prior pilot retrieval lists remain censored. Graph interventions retain
the original positive training facts for evaluator filtering, excluding uncertain
injected edges. Completed unperturbed results are unchanged. The original
short-budget length sweep below remains exploratory; the new length experiment
holds a frozen constant-rule inventory fixed at inference time.

## Literature relationship

[Meilicke et al. (2018)](https://web.informatik.uni-mannheim.de/RuleN/meilicke18.pdf)
motivate fine-grained evaluation using rule explanations and subsets associated
with strong relational paths or uncovered tasks. We reproduce that style of
analysis and the comparison of top-1 and top-10 successes. Changing the systems
to ComplEx/RotatE and AnyBURL on CoDEx makes this a conceptual replication, not a
numerical reproduction of their RuleN/AMIE and earlier embedding experiments.

[Safavi and Koutra (2020)](https://aclanthology.org/2020.emnlp-main.669/)
provide CoDEx's official positives, verified hard negatives, relation-pattern
analysis, and separate ranking/classification tasks. We retain those tasks and
splits. Our validation logistic calibration and global threshold differ from
their relation-specific threshold selection. The supplied fixed budgets do not
reproduce their extensive tuning or published scores.

[Anil et al. (2024)](https://aclanthology.org/2024.lrec-main.792/)
identify unranked zero-confidence entities and evidence aggregation as important
limitations of rules in inductive completion. We explicitly measure abstention,
truth retrieval, and supporting evidence. Their disjoint-entity inductive setting
and GNN comparisons are not reproduced by this transductive embedding study.
We do not infer that their findings must hold for CoDEx transductive embeddings.

Controlled removals/noise, crossed-seed uncertainty, and combined diagnostics are
extensions of this project's comparison protocol. A broader literature review
would be required to claim novelty; **no novelty claim is made**.

## Hypotheses fixed before benchmark execution

1. H1: learned path-rule coverage moderates the embedding–rule Hits@1 difference.
2. H2: removing local incident edges changes rule coverage and prediction quality
   more than count-matched random removals on queries with the targeted known node.
3. H3: observed relation pattern strength associates with relative performance
   after stratifying by frequency and known-node degree.
4. H4: increasing maximum cyclic rule length improves coverage but need not improve
   precision or hard-negative discrimination at the same mining time budget.

These are unverified hypotheses, not results. Other slicing, examples, and
complementarity descriptions are exploratory. No significance-based claim is
made from these unexecuted plans; many related groups would require a separately
specified multiple-comparison policy for confirmatory tests.

## Data and leakage boundaries

Original `train`, `valid`, `test`, `valid_negatives`, and `test_negatives` files are
kept separate. The complete CoDEx-S expected positive counts are 32,888 / 1,827 /
1,828; CoDEx-M uses 185,584 / 10,310 / 10,311. Each negative split matches its
corresponding held-out positive count. Loader checks cover counts, formatting,
duplicates, positive split overlap, verified-negative contradictions, and ID
coverage. Counts alone cannot authenticate user-supplied files: retain downloader
commit/URL provenance and checksums when making benchmark claims.

Backends receive `TrainGraph` (positive training edges and vocabulary) and masked
`ModelQuery` objects. The evaluator receives gold targets and positives solely to
filter other correct candidates. Validation selection filters train+validation;
test evaluation filters train+validation+test. Verified negatives never enter
either filter index or the ordinary training graph.

Interventions are explicitly labeled and never repartition held-out splits.
Noise candidates are generated without held-out knowledge. A separate split
hygiene gate rejects the entire planned variant before training if an injected
edge collides with a held-out positive or verified negative. This gate uses split
membership only, never test scores, inference, or automatic adaptive resampling.
It is an explicit data-integrity exception to evaluator-only held-out access.
Rejected cells remain failures; replacement seeds must not be selected to improve
test performance. Corrupted edges are uncertain intervention inputs, not asserted
false triples or independently verified graph facts.

## Shared ranking protocol

Both prediction directions use the same original training-entity vocabulary,
including entities isolated by an intervention. No relation/type restriction
shrinks the evaluation universe. Neural scores cover every entity; realistic
average-score tie ranks determine exact filtered MRR and Hits. Rule candidates
preserve PyClause's native maxplus ordering, with frequency tie breaking. Both
policies are recorded because their treatment of ties differs.

Rule lists may be truncated before evaluator filtering. A target missing from
such a list has **unknown full rank**. Even a target found in a retrieved list has
only a retrieved-list rank unless completeness is established. The framework
records retrieved Hits@1/Hits@10 and reciprocal-rank proxy, marks these censored,
and sets `mrr_exact` to null. These values must not be relabeled exact full-ranking
performance or used alone to declare full-ranking superiority. More candidates
or a verified complete-ranking backend is required to resolve censoring. No
optimistic reconstruction of missing ranks is provided.

Coverage is a nonempty candidate list before evaluator filtering, independently
of correctness. Conditional Hits are computed only on covered queries; overall
Hits count uncovered cases as misses. Rules are classified as relational path,
constant, or zero-body entity prior. The default disables learning zero rules;
constant rules remain identifiable. Raw support/confidence and application scores
are distinct; smoothing and backend rule-type weights can change application
confidence from its saved mining value.

## A–F and graph measurements

| Experiment | Implementation and interpretation |
| --- | --- |
| A | Query-level coverage, rule kind, truth retrieval, and strong evidence (raw confidence ≥0.5 and support ≥5, fixed in config). Embedding successes without rule candidates are counted. Truncated omissions remain unknown; unrepresentable queries are separate. |
| B | In/out/total degrees and train-derived tertiles. The completed retraining cohorts compare the original graph with 90% retention, including three new targeted versus relation-matched graph draws. The framework also prepares broader 70% and 50% variants. |
| C | Train-only symmetry, ordered inversion/subsumption ratios, distinct endpoint two-hop composition ratios, frequency, and average tails/head and heads/tail. Cardinality uses a stated 1.5 cutoff. Frequency×known-degree strata provide descriptive confounding control, not causal adjustment. |
| D | The corrected comparison filters a frozen inventory to general body length caps of 1, 2, and 3, with and without the same constant-bearing subset. The earlier cap-by-remine sweep is separate because changes in mining also changed inventory composition. |
| E | Completed verified hard-negative AUROC/AP and validation-calibrated classification. The planned uncertain edge additions were checked separately at 1%, 5%, and 10%. Seventeen of 18 CoDEx-S graph proposals failed the held-out collision gate, so the noise matrix has no performance results. The audited type-consistent generator uses empirical relation domain/range as a type proxy. |
| F | Four error categories, proportions, error Jaccard overlap, and oracle union of recorded successes. The oracle is not deployable; censoring of symbolic outcomes also qualifies this diagnostic. |

Composition computation explicitly marks relation-pair bodies exceeding the
configured wedge budget as skipped. Reported ratios count observed confirmations;
unobserved heads are not proven false. Queries include directed two-hop paths to
the truth and common-neighbor counts as **answer-dependent diagnostics**. Degree
and frequency averages are included in scenario summaries. Sparse group counts,
empty tertiles, and skipped patterns must remain visible.

Truth-dependent rule categories, target degrees, truth-path features, comparative
error categories, and oracle outcomes are never deployment-time selectors. Case
studies choose the first query IDs per error category and preserve actual rules
and checked training groundings; human labels are used when downloaded.

## Classification, statistics, and inference limits

Validation raw scores fit a StandardScaler and regularized logistic calibrator.
The decision threshold maximizes covered validation balanced accuracy. Test scores
are first requested after calibration and threshold selection. Classification
reports raw-score AUROC/AP, calibrated Brier score, covered accuracy/F1, and
overall accuracy counting abstentions as misses. Unsupported rule scores use a
documented zero convention for discrimination and abstain for decisions. That
zero is not a symbolic negative judgment. Calibration diagnostics are exploratory
when covered validation lacks both classes; no relation-specific calibration or
nested calibration split is implemented.

Baseline differences use a paired hierarchical bootstrap over training seeds and
triple clusters, preserving both directions and pairing models within queries.
Intervention effects pair the same query to its matched unperturbed control and
resample training seeds, perturbation seeds, and triples as crossed factors.
Intervals are percentile 95% intervals; repeated seeds must have identical query
identities. A single-seed interval represents query variability, not training
stability. Neural final configuration requests three seeds; Java stochasticity
remains a limitation until reproducible JAR seeding is verified.

Current scenario analyses are descriptive; there is no multivariable causal model,
formal hypothesis test, or learned selector. Interventions support conclusions
only about the specified removal/addition process, targets, budgets, and controls.
They do not establish universal graph laws. Full datasets, real backend integration
tests, validation search, and completed benchmark runs are prerequisites for any
answer about which family is more reliable.
