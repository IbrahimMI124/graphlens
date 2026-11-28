# CoDEx-S matched removal replication

This exploratory follow-up repeats the Phase 5 local edge removal comparison on three new graph draws. It uses 90% retention and pairs each targeted deletion with a random deletion that removes exactly the same number of edges per relation. The fixed seed pairs (removal, target selection) are (231, 940), (232, 941), and (233, 942). The previous (11, 101) graph pair remains an earlier pilot and is outside this summary. Targets are uniformly sampled from original training entities. A 16-fact smoke run is excluded from the study. Graphs, catalog hashes, dataset split hashes, and the selected recipe hash are saved before training.

## Primary comparison

On each draw and arm, fit the validated CPU ComplEx recipe for seeds 0, 1, and 2 and mine two independent 60-second AnyBURL inventories with the Phase 5 settings. The Java miner's random stream is uncontrolled. The primary performance estimand is the change in the neural minus all-rule filtered Hits@1 gap between targeted removal and its matched control. Both arms have the same training size, epoch ceiling, and updates per epoch. Validation-selected checkpoints determine the primary result. A common-update checkpoint is a separate sensitivity check. Head and tail outcomes are paired within each of the 1,828 test triples. The vocabulary, held-out sets, and evaluator filters are those of the original graph.

Report the effect for each draw and an equally weighted average. The exploratory bootstrap resamples paired graph draws, shares the sampled test triple clusters across draws and arms, pairs the ComplEx seeds, and resamples independent miner realizations within arm and draw. With only three graph draws, the individual effects and their spread carry more information than a nominal 95% interval. Three models on the same graph do not provide three independent interventions.

## Grounding measurement

Reapply the previously frozen general and constant-bearing catalogs on the original graph and both deletions. The primary evidence measure is the mean per-fact fraction of original **general-rule body groundings** removed, restricted to test triples having at least one such grounding in the original graph. Compare targeted minus matched. Also report total groundings, facts losing any grounding, and facts losing all groundings. Each grounding is a canonical native rule expression and ordered tuple of training edges. The same ground fact enters once even though ranking evaluates it in two directions.

The pinned PyClause `PredictionHandler` enumerates explanations without a rule count cap. For the general B inventory it traverses valid body substitutions and records every found grounding. Each output is checked against its rule and predicted triple. Surviving original groundings must exactly match re-enumeration on the modified graph. Grounding diagnostics bind the correct answer only after masked ranking. The answer cannot enter graph selection, training, or candidate scoring. Constant-bearing rules participate in the frozen ranking comparisons. The primary grounding measurement is restricted to the general B inventory.

The design controls relation totals within a draw, with endpoint frequencies, neighbourhoods and body instantiations changing together. Native frequency tie breaking also changes with the graph. The grounding diagnostic connects deletions to actual rule-body instances. It cannot identify the separate causal contributions of each co-changing quantity to model rankings. The prior phase has already examined the CoDEx-S test set. Independent dataset replication remains later work.

## Execution and artifacts

The [graph audit](../artifacts/removal-replication/planned-graph-audit.csv) records each graph's hash, degrees, size, isolated entities, and directed two-hop walk count. All six graphs contain 29,599 training triples and isolate zero entities. Targeted deletions removed 3,289 edges incident to sampled entities in each draw. The matched controls removed 620, 666, and 649 incident edges respectively. Targeted graphs retained more global directed two-hop walks in all three new draws. The global count is a structural diagnostic distinct from the native rule grounding count.

The [job record](../artifacts/removal-replication/hf-submission.json) lists the separated smoke and full run IDs. Full graph training uses the CPU Upgrade Hugging Face Jobs flavor with a 150-minute limit for each draw. Checkpoints and output artifacts are persisted by job ID. The smoke results have a separate job ID and are excluded from the report.

After the jobs complete, `scripts/collect_removal_replication_hf.py <draw-1-id> <draw-2-id> <draw-3-id>` downloads the compact outputs and builds the combined report. The collector verifies the recorded output and protocol hashes, draw identities, and paired query sequence before aggregating. Use the Python environment with Hugging Face CLI and the project dependencies installed.
