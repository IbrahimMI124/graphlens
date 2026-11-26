# Knowledge Graph Completion Research Directions and Progress

This study asks when embedding models and symbolic rules are reliable for
completing missing facts in a knowledge graph, and how graph structure changes
that reliability. The work has established CoDEx-S baselines, separated several
rule families, and tested how a fixed rule catalog responds to training-edge
removal. The central retraining comparison across altered graphs remains
unfinished, so the current evidence does not yet show which approach is more
robust to structural change.

## Background and terms

A knowledge graph is a set of directed, labeled facts. Each fact is a triple
`(head, relation, tail)`. For example, `(Paris, capital_of, France)` says that
Paris is the head entity, `capital_of` is the relation, and France is the tail
entity.

Knowledge graph completion (KGC) asks a model to fill in a missing entity. A
tail query might be `(Paris, capital_of, ?)`, while a head query might be
`(?, capital_of, France)`. The benchmark supplies a known correct answer, and
the model ranks possible entities from the dataset's entity vocabulary.

The two method families in this study work differently:

- **Embedding models** assign vectors to entities and relations. A scoring
  function estimates how plausible a candidate triple is. ComplEx is the main
  embedding baseline; RotatE is available as a secondary configured model.
- **Symbolic rule systems** learn relational implications and apply them to
  queries. A simple path rule has the form
  `(h, parent, z) AND (z, born_in, t) => (h, related_to, t)`. If the body facts
  are present in training, the rule can produce a candidate answer.

Several terms matter for interpreting the results:

- **Filtered ranking** removes other known correct answers from the candidate
  list before measuring the rank of the target. The target itself is never
  removed. Validation filtering uses training and validation positives; test
  filtering uses training, validation, and test positives. The model does not
  receive those held-out filter facts.
- **Hits@1** is the fraction of queries where the correct entity ranks first.
  **Hits@10** is the fraction where it appears among the first ten. **MRR** is
  mean reciprocal rank: a rank of 1 contributes 1, rank 2 contributes 1/2,
  and so on.
- **Coverage** asks whether a system returned any candidates. It is distinct
  from correctness. Conditional accuracy measures results only where a system
  returned candidates; overall accuracy counts uncovered queries as misses.
- A rule's **support** records how much observed training evidence supports
  it under the miner's definition. **Confidence** summarizes its empirical
  reliability under that rule type. These are learned-rule statistics, not
  calibrated probabilities for a specific prediction.
- **Candidate generation** means that the rule system returned the known answer
  somewhere in its candidate list. It does not mean the answer ranked first.
- A **constant-bearing rule** contains a named entity in a conditional rule.
  It still requires a rule body. A **zero-body rule** has no relational
  condition and acts like an entity prior. Those two cases are kept separate.

CoDEx-S has 2,034 entities and 42 relations. Its official positive splits
contain 32,888 training, 1,827 validation, and 1,828 test triples. CoDEx also
provides verified validation and test negatives for a separate classification
task. They are never inserted as graph edges. The test set has been inspected
repeatedly during this development, so CoDEx-S findings are exploratory. The
planned CoDEx-M replication has not run because its complete data is unavailable
in this workspace.

## How to read the coverage diagnostics

The pilot contains legacy labels whose names can be misleading if read as
formal rule families. `rule_covered` means that at least one candidate was
returned before evaluator filtering; it says nothing about whether the answer
was among them. `relational_path` was assigned from a syntactic test that all
rule terms were variables. It can include reflexive rule syntax and does not
mean that the rule is a native AnyBURL `B` rule. `mixed` means that more than
one coarse legacy evidence kind was attributed to returned candidates; it is
not an intrinsic category of the query. The newer family analyses distinguish
native `B`, `Uc`, `Ud`, reflexive `XX`, and zero-body `Z` evidence where the
catalog supports that distinction. Truth-dependent labels are evaluation
diagnostics, never deployment-time features.

## 1. Dataset and evaluation foundation

The loader preserves official entity and relation identifiers across models,
keeps positive and negative splits separate, and validates split counts,
overlap, formatting, and provenance metadata. Both head and tail queries use
the same entity candidate universe. Under graph interventions, the official
held-out queries and evaluator filters remain fixed; only the training graph
changes.

The evaluator and model APIs separate the answer from the query presented to a
model. This prevents validation or test targets from being used as input. Known
held-out positives are used only by the evaluator to filter alternative correct
answers. Verified negatives are used only in the separate classification task.

**Progress:** CoDEx-S loading, ID mapping, filtering, split checks, query
generation, and leakage guards are implemented and tested. CoDEx-M support is
designed into the loader, but a complete-dataset integration test is skipped
until those files are available. The latest local suite passed 100 tests and 38
subtests, with one CoDEx-M skip; see
[`STATUS.md`](STATUS.md) and the curated [test summary](../artifacts/phase5/github-test-summary.json).

## 2. Embedding baseline: ComplEx

ComplEx represents entities and relations with complex-valued embeddings and
scores a triple by combining the head, relation, and tail representations. The
selected recipe uses reciprocal relations and a 1-vs-all cross-entropy
objective: for each training example, it scores all candidate entities for the
prediction direction. The validation search selected embedding dimension 256,
Adam learning rate 0.003, batch size 1,024, 40 training epochs, entity dropout
about 0.079, relation dropout about 0.056, and no explicit regularizer. Validation
performance selected the configuration; test scores were not used for tuning.

The three-seed CoDEx-S result is mean Hits@1 **0.3563** and mean MRR **0.4535**.
This is below the approximate published CoDEx-S ComplEx reference in the
project brief (Hits@1 0.372, MRR 0.465). The pilot's ten-epoch budget was too
short to be a strong comparison; the later search and 40-epoch recipe improved
the baseline, but do not exactly reproduce the published training recipe,
compute budget, or tuning procedure. The best reproducible checkpoint and
validation diagnostics are preserved in the earlier experiment artifacts.

**Progress:** ComplEx is the principal neural baseline and has three completed
development seeds. RotatE has configuration and one-epoch backend test support,
but no comparative result is part of the main findings. A separate Phase 5
original-graph ComplEx run completed one seed and 40 epochs, with test Hits@1
0.3556 and MRR 0.4514. It is a contemporaneous control for that incomplete
cohort, not a replacement for the three-seed baseline.

See the [strengthened baseline report](../artifacts/next-phase/report.md) and
[methodology](METHODOLOGY.md).

## 3. AnyBURL baseline and rule availability

AnyBURL is a real Java rule miner; PyClause applies its learned rules to
head- and tail-prediction queries. For example, a two-edge body can connect the
known query entity to a candidate answer. A query is **rule-covered** if
application returns at least one candidate. Rules can cover a query and still
omit the correct answer, or they can generate the correct answer but rank it
below other candidates. The study tracks these cases separately.

The main frozen 60-second AnyBURL catalog contained 470,308 learned rules:
2,249 general variable-only `B` rules, 444,628 conditional constant-bearing
`Uc` rules, 23,361 conditional constant-bearing `Ud` rules, and 70 zero-body
`Z` rules. Counts describe the inventory, not its predictive contribution.
The all-rule Hits@1 was **0.3408**. An exploratory pilot also breaks results
down by rule coverage, evidence type, and whether a rule retrieves the truth.

Rule candidate lists can be truncated. A missing answer in a truncated list
does not prove that the rule system could not rank it; its full rank is unknown.
The framework preserves this censoring and does not present top-K reciprocal
rank as exact full-universe MRR. For the complete frozen-catalog Phase 5
applications, supported-candidate Hits@1 and Hits@10 are certified under the
native candidate order; these are still not full-universe rule MRR. Uncovered
queries count as misses in overall Hits, and an unsupported rule prediction is
an abstention, not a negative judgment.

The embedding and rule Hits@1 values are informative but are not perfectly
equivalent ranking summaries: ComplEx scores the full entity universe, whereas
the certified AnyBURL Hits here use the returned supported-candidate order and
count abstentions as misses. Exact full-universe rule MRR is not available.
This distinction is retained rather than reconstructing missing rule ranks.

**Progress:** The real AnyBURL adapter, rule inventory parsing, native scoring,
candidate coverage, and training-grounding checks are implemented. Fresh
original-graph Phase 5 mining completed with 320,347 rules, but applying that
fresh catalog to evaluation queries did not complete. Therefore, it is not a
completed fresh-rule baseline for the intervention matrix.

## 4. Rule-family contribution and constant rules

An inventory can contain many rules that are redundant or never useful on the
test queries. To measure contribution, the same frozen rule catalog and query
set were evaluated with different rule subsets. The main family-level Hits@1
results are:

| Rule subset | Hits@1 | What it includes |
| --- | ---: | --- |
| All rules | 0.3408 | General relational, conditional constant-bearing, and zero-body families |
| Constant-bearing | 0.3206 | Conditional `Uc` and `Ud` rules; excludes zero-body `Z` priors |
| General relational | 0.2749 | Variable-only relational `B` rules |

These scores are not additive. Rule subsets can generate overlapping
candidates, and the native aggregation and ordering operate across evidence.
The result shows that the constant-bearing subset is strong in this catalog;
it does not prove that the numerically dominant rule count caused the all-rule
score. Unconditional zero-body priors are treated separately from conditional
rules that mention entity constants.

**Progress:** The original-graph frozen-constant evaluation completed all 3,656
directional test queries. Its candidate lists, scores, ranks, and Hits exactly
match the prior constant-rule baseline, with Hits@1 **0.3206** and Hits@10
**0.6187**. Four modified-graph constant applications remain incomplete. Thus,
the current evidence does not yet show how constant rules respond to edge
removal compared with general relational rules.

The family and query-level analyses are documented in the
[rule-family report](../artifacts/next-phase/report.md) and the
[Phase 5 continuation report](../artifacts/phase5/remaining-report/report.md).

## 5. Rule complexity

Rule length is the number of relations in the body of an implication. A
length-three rule may use a longer path than a length-one rule, but longer
patterns also require more search and can produce lower-confidence rules.
Changing the mining length cap can change many other aspects of the learned
inventory, so raw comparisons between separate mining runs do not isolate the
effect of length.

The earlier short-budget sweep changed the constant-rule inventory sharply:
the reported constant counts were 111,292 at length 1, 49,808 at length 2, and
558 at length 3. Its performance changes therefore mixed rule length with
inventory composition. The corrected analysis mines once and holds the
constant inventory fixed while applying relational subsets from the same
catalog.

With only relational rules, Hits@1 rises from **0.1214** at length 1 to
**0.2098** at length 2 and **0.2749** at length 3. When the same constant rules
are added to each condition, Hits@1 is **0.3400**, **0.3425**, and **0.3408**.
The length-3 versus length-1 difference with constants is **0.0008**, with a
paired 95% interval from **−0.0022 to 0.0038**; the observed query comparison
had 17 gains and 14 losses across 3,656 directional queries (1,828 test
triples). This interval conditions on one learned catalog. The longer
relational rules are useful on their own in this catalog, but show little net
gain on top of constants.

**Progress:** The inference-time fixed-inventory ablation is complete for the
available catalog. It does not establish that longer rules are generally
better, nor that the result is stable across independently mined inventories.
Independent mining replications are still needed. The initial short-budget
sweep remains exploratory.

See the [rule-length report](../artifacts/rule-length-pilot-report/report.md)
and [corrected analysis](../artifacts/next-phase/report.md).

## 6. Sparsity and controlled graph interventions

Sparsity asks what happens when the training graph contains fewer observed
edges. The main Phase 5 design fixes the official validation/test facts and
candidate vocabulary, then removes training edges in four ways at 90% edge
retention:

1. **Global random removal** samples edges without preserving relation counts.
2. **Relation-stratified removal** samples within relation groups to preserve
   relation proportions as closely as integer counts allow.
3. **Targeted local removal** prioritizes edges incident to training-selected
   target entities and fills the removal budget as specified by the protocol.
4. **Relation-count-matched control** removes the exact same number of edges per
   relation as targeted removal, but selects them randomly within those counts.

The original training graph is the 100% retention condition. The targeted and
matched-control graphs have identical per-relation totals but intentionally
differ in which entities and local paths lose edges. The audit reconstructed
all five graphs from training-only seeds and verified that the held-out query
set, candidate universe, and evaluator filters remain unchanged. No entities
were isolated in this prepared 90% experiment. This is one perturbation draw,
not a repeated sample of all possible graph removals.

The wider sparsity plan also names 70% and 50% retention conditions. Those
larger removals have not been executed; current Phase 5 evidence concerns the
original graph and the four prepared 90% conditions only.

There are two different questions:

- **Evidence availability:** Apply the same already learned rule catalog to
  each modified graph. This changes available training evidence without
  relearning the rules.
- **Retrained-system response:** Retrain ComplEx and mine AnyBURL separately
  on each modified training graph. This includes both changed evidence and
  changed learning.

Only the first question is complete for general relational rules. In the
fixed-catalog experiment, Hits@1 changed from **0.2749** on the original graph
to **0.2653** after global random removal, **0.2623** after relation-stratified
removal, **0.2577** after targeted removal, and **0.2604** after the
relation-count-matched removal. The paired targeted-minus-matched difference
was **−0.0027**, with a 95% interval from **−0.0129 to 0.0071**, so this
particular contrast is inconclusive. Correct-answer generation stayed at about
**99.73%** across these general-rule conditions, while candidate coverage was
about **99.89%**.

These are controlled inference-time changes for one fixed catalog and one
removal draw. Candidate support and native graph-frequency tie-breaking both
change, so the Hits differences cannot be assigned solely to missing rule
bodies. They do not compare retrained embedding and rule systems.

**Progress:** The graph audit, frozen-general reapplication, paired tables,
and training-only witness checks are complete. The retrained five-graph
comparison is not. A corrected-index CPU smoke ran six cells using one epoch,
two seconds of mining, and 32 directional queries per condition. It checks
execution only and is not scientific evidence about relative reliability.

See the [graph audit](../artifacts/phase5/validation/validation-report.md),
[Phase 5 report](../artifacts/phase5/report/report.md), and
[continuation report](../artifacts/phase5/remaining-report/report.md).

## 7. Relation properties

Relations differ in frequency and in their observed patterns. For example,
`born_in` may have many tails per head, while `capital_of` may be close to
one-to-one in a particular graph. The project measures relation frequency,
one-to-one/one-to-many/many-to-one/many-to-many cardinality, empirical
symmetry, inverse relations, relation subsumption, and two-hop composition.

In practical terms, symmetry checks whether observed `(h, r, t)` facts tend to
have `(t, r, h)` counterparts. Inversion checks whether another relation tends
to express the swapped endpoints. Subsumption checks whether the facts of one
relation are often contained within those of another. Composition checks
whether a two-relation path `(h, r1, z), (z, r2, t)` is often accompanied by a
direct `(h, r, t)` fact. Cardinality uses observed average tails per head and
heads per tail, with a 1.5 grouping cutoff. All of these are empirical
training-graph patterns, not extra true/false labels supplied to a model.

These are estimated from training triples only. A high observed symmetry or
composition rate is an empirical regularity in this dataset, not a universal
logical law. Low counts can make estimates unstable. The code also limits
expensive composition searches and records when a pattern is skipped. Relation
frequency and entity degree strata are used as descriptive checks for
confounding; they do not turn observational slicing into causal adjustment.

**Progress:** The train-only pattern and relation diagnostics are implemented,
tested on synthetic structures, and used in exploratory baseline reports.
Relation-specific performance summaries and frequency/degree strata exist.
There has not been a controlled intervention that changes one relation
property while holding the other graph characteristics fixed. These findings
remain exploratory and do not establish that a specific pattern causes a
method to win.

## 8. Verified negatives and robustness

CoDEx supplies verified hard negatives: triples selected and checked by the
benchmark as negative examples. They support a separate triple-classification
question—whether a score distinguishes verified positives from these verified
negatives. They are not used as positive graph edges, and an unobserved triple
is never automatically labeled false.

The planned classification analysis reports AUROC and average precision from
raw scores, then selects calibration and a decision threshold using validation
data. It keeps raw ranking scores distinct from calibrated probabilities and
distinguishes an unsupported rule prediction from a negative judgment. The
robustness extension injects uncertain edges into training at 1%, 5%, and 10%
under random and type-consistent corruption protocols while leaving the
evaluation graph untouched. Injected edges are intervention inputs, not
verified facts.

**Progress:** Split handling, classification code, validation-only calibration
logic, and unit/smoke coverage are present; pilot classification outputs are
preserved. The complete noise-level by corruption-strategy retraining matrix
has not run. Results from the existing pilot should not be interpreted as a
full robustness study.

## 9. Error complementarity

Two systems can have similar average scores but make different mistakes. For
each query, the comparison assigns one of four outcomes: both correct, only
ComplEx correct, only rules correct, or both wrong. It also reports error
overlap and an **oracle union**: the fraction of queries where at least one
system succeeded.

The oracle is only a ceiling for diagnosis. It uses the correct answer to
choose whichever system succeeded, so it is not a model that can be selected
at deployment time. Rule-candidate truncation also limits how confidently a
rule miss can be classified.

**Progress:** Query-level aggregation, complementary-success categories,
winner changes, and representative case selection are implemented and tested.
Exploratory baseline cases have been produced. The fresh Phase 5 comparison
cannot yet characterize which structures predict complementary success because
the perturbed-model predictions are missing. Any present correlation between
graph features and errors is descriptive, not a causal explanation.

## 10. Statistics and reporting

Head and tail queries from one original triple are related observations. The
analysis therefore clusters them by triple when bootstrapping query outcomes.
Baseline comparisons also pair models on the same queries. When several
training seeds or independently mined catalogs exist, those are separate
sources of variability and should be resampled separately from test triples.

The existing frozen-general Phase 5 intervals condition on one learned catalog
and one removal realization. Their 3,656 directional queries come from 1,828
test triples; they do not estimate variation across independent training or
mining runs. One-seed intervals quantify query variation conditional on that
model, not model-training stability.

Reports retain sample sizes, uncertainty intervals, rule coverage, candidate
and answer-generation coverage, runtimes, inventory size, and evidence limits.
Raw rule scores are not described as calibrated probabilities. Case studies
show training-only supporting facts and distinguish measured prediction
changes from hypotheses about why an embedding changed.

**Progress:** Paired bootstrap and reporting code are implemented and tested.
The baseline reports include three ComplEx seeds and query-level comparisons.
For Phase 5, learning/mining uncertainty is not estimable until the fresh
replicated matrix runs. Since CoDEx-S test outcomes have already been examined
repeatedly, all follow-up results remain exploratory; CoDEx-M should be used
for replication after the protocol is frozen.

## 11. Phase 5 mechanism hypotheses

These hypotheses concern the full retrained intervention, not just fixed-rule
reapplication:

| Hypothesis | Planned test | Progress and current limit |
| --- | --- | --- |
| **H1: Neighborhood removal affects embeddings and rules differently.** | Retrain both systems on each removal graph; compare paired Hits, coverage, degrees, and paths against fresh original-graph controls. | Graph conditions and the original ComplEx control exist. The modified-graph primary fits are missing, so differential sensitivity is untested. |
| **H2: General rules depend on edges that instantiate their bodies.** | Reapply the same general-rule catalog to graphs with removed edges; track candidate-support and verified grounding loss, then compare with fresh-mined rules. | Fixed-catalog candidate support loss and witness checks are measured. Native frequency tie-breaking also changes; the fresh mining comparison is pending. |
| **H3: Constant-bearing rules respond differently from general rules.** | Compare their coverage, correctness, and training-grounding changes under the same interventions, first with fixed inventories and then with fresh mining. | The original frozen-constant control is complete. Four modified frozen-constant applications and fresh retraining comparisons are pending. |
| **H4: Targeted removal differs from a relation-matched random control.** | Compare targeted-local removal with a control that removes the same number of edges per relation. | The graph manipulation is exactly relation-count-matched. The frozen-general Hits difference is small and uncertain; entity degrees and paths also differ, and only one target/removal draw exists. |
| **H5: Relative robustness varies by query structure.** | Join each query across conditions and compare outcomes by original training degree, relation frequency, path availability, and target incidence. | Train-observable features and frozen-rule joins exist. Fresh paired neural/rule outcomes are missing; any current strata cannot identify causal mechanisms or a deployable selector. |

The prospective full cohort declares three ComplEx seeds and two independent
AnyBURL mining realizations across five graph conditions. It has not run. The
earlier Phase 5 process was stopped after the host CPU reached 87°C; the
configured SSH target is off-limits, and no alternate compute destination has
been authorized. The project therefore has no completed retrained
embedding-versus-rule structural comparison yet.

## Overall answer so far

The strongest direct structural evidence is about **fixed general rules**:
under the tested 90%-retention edge removals, answer generation remained high,
but ranking declined. Separate frozen-family results show that constant-bearing
rules perform well on the original graph, and fixed-inventory length tests show
that longer relational rules add little beyond those constants in that catalog.
These facts do not yet explain the relative performance of freshly trained
embeddings and freshly mined rules under changed graph structure.

To answer the main question, the next research result must come from paired,
freshly trained models on the same original and perturbed graphs, with repeated
neural seeds and independent rule-mining realizations. Until then, claims about
which model family is more robust, or why, remain unresolved. Graph neural
network/GAT comparisons are outside this phase's scope.

## Relationship to earlier research

The fine-grained comparison of rule coverage, evidence, and query subsets is a
conceptual replication of the evaluation style in Meilicke et al. (2018), using
CoDEx-S, ComplEx, and AnyBURL rather than their earlier systems. The use of
CoDEx's verified negatives and separate ranking/classification tasks follows
Safavi and Koutra (2020), but this project does not reproduce their extensive
hyperparameter tuning or relation-specific classifier thresholds. The rule
abstention and evidence limitations discussed by Anil et al. (2024) motivate
tracking unsupported queries and rule groundings; that paper's inductive GNN
setting is not reproduced here. Controlled edge interventions and joint
query-level diagnostics extend this comparison. No novelty claim is made
without a broader literature review. Full citations and scope notes are in
[`METHODOLOGY.md`](METHODOLOGY.md).
