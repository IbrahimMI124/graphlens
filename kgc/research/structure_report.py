"""Paired Phase-5 statistics, graph/query joins and reproducible report outputs."""
from collections import defaultdict
from pathlib import Path
import csv
import json
import numpy as np
from ..evaluation import queries
from ..diagnostics import GraphDiagnostics
from ..io import write_json, write_csv, triple_digest
from .runner import read, load_rows
from .structure_audit import CONDITIONS
from .report import table


def checked_rows(path, dataset, limit):
    rows=load_rows(path/"queries.json.gz")
    expected=list(queries(dataset.test[:limit] if limit is not None else dataset.test))
    if len(rows)!=len(expected):
        raise ValueError("Incomplete intervention query sequence")
    for row,q in zip(rows,expected):
        if (row["query_id"],row["head"],row["relation"],row["tail"],row["direction"])!=(q.query_id,*q.triple,q.direction):
            raise ValueError("Intervention/control query identities differ")
    return rows


def effect(treat, control, metric="hits1", independent_models=False, repetitions=1000, seed=2026):
    """Shared triples; neural seeds paired, miner realizations drawn independently.

    Arrays are lists of model-replicate query rows. A single replicate gives
    query-conditional uncertainty only, not an estimate of learning variability.
    """
    if not treat or not control:
        raise ValueError("Missing treatment or control models")
    reference=control[0]
    identity=lambda rows:[(r["query_id"],r["triple_id"],r["head"],r["relation"],r["tail"],r["direction"]) for r in rows]
    if any(identity(rows)!=identity(reference) for rows in treat+control):
        raise ValueError("Paired query identities are inconsistent")
    if len({r["query_id"] for r in reference})!=len(reference):
        raise ValueError("Duplicate query IDs")
    if not independent_models and len(treat)!=len(control):
        raise ValueError("Paired neural seeds must form a complete grid")
    blocks=defaultdict(list)
    for i,row in enumerate(reference): blocks[row["triple_id"]].append(i)
    groups=list(blocks.values());sizes=np.array([len(g) for g in groups])
    arrays=[]
    for models in (treat,control):
        arrays.append(np.array([[sum(float(rows[i][metric]) for i in group) for group in groups] for rows in models]))
    a,b=arrays;rng=np.random.default_rng(seed);samples=[]
    for _ in range(repetitions):
        ids=rng.integers(0,len(groups),size=len(groups))
        ia=rng.integers(0,len(a),size=len(a))
        ib=rng.integers(0,len(b),size=len(b)) if independent_models else ia
        samples.append((a[np.ix_(ia,ids)].sum()/len(ia)-b[np.ix_(ib,ids)].sum()/len(ib))/sizes[ids].sum())
    low,high=np.quantile(samples,[.025,.975])
    certified=all(r.get("hits_certified",False) for model in treat+control for r in model)
    return {"difference":float(a.sum()/len(a)/len(reference)-b.sum()/len(b)/len(reference)),"ci_low":float(low),"ci_high":float(high),
        "all_rankings_certified":certified,"ranking_scope":"certified available-candidate outcomes" if certified else "observed retrieved outcomes; uncertified rankings are censored",
        "n_unique_queries":len(reference),"n_triples":len(groups),"n_treatment_models":len(a),"n_control_models":len(b),
        "bootstrap":"paired test-triple clusters; independent graph-specific mining draws" if independent_models else "paired test-triple clusters and paired neural seeds/fixed catalog",
        "uncertainty_scope":("query-conditional only with one model per graph; no intervention-draw or unreplicated mining/training variability" if len(a)==len(b)==1 else "resamples available model realizations and paired test triples; conditional on one graph/removal draw, with limited learning replications"),
        "repetitions":repetitions}


def gap_effect(neural_t,neural_c,rules_t,rules_c,repetitions=1000,seed=2026):
    """Change in neural-minus-rule gap; sample factors separately, not a fake seed cross product."""
    all_models=neural_t+neural_c+rules_t+rules_c
    reference=all_models[0]
    identity=lambda m:[tuple(r[k] for k in ("query_id","triple_id","head","relation","tail","direction")) for r in m]
    if any(identity(m)!=identity(reference) for m in all_models): raise ValueError("Gap comparison query mismatch")
    blocks=defaultdict(list)
    for i,r in enumerate(reference): blocks[r["triple_id"]].append(i)
    groups=list(blocks.values());sizes=np.array([len(g) for g in groups])
    vals=[np.array([[sum(row[i]["hits1"] for i in g) for g in groups] for row in models]) for models in (neural_t,neural_c,rules_t,rules_c)]
    if len(vals[0])!=len(vals[1]): raise ValueError("Missing paired neural seeds")
    rng=np.random.default_rng(seed);out=[]
    for _ in range(repetitions):
        q=rng.integers(len(groups),size=len(groups));n=rng.integers(len(vals[0]),size=len(vals[0]))
        rt=rng.integers(len(vals[2]),size=len(vals[2]));rc=rng.integers(len(vals[3]),size=len(vals[3]))
        terms=[vals[k][np.ix_(m,q)].sum()/len(m) for k,m in enumerate((n,n,rt,rc))]
        out.append((terms[0]-terms[1]-terms[2]+terms[3])/sizes[q].sum())
    lo,hi=np.quantile(out,[.025,.975])
    point=(vals[0].mean(axis=0)-vals[1].mean(axis=0)-vals[2].mean(axis=0)+vals[3].mean(axis=0)).sum()/len(reference)
    return {"difference":float(point),"ci_low":float(lo),"ci_high":float(hi),"n_unique_queries":len(reference),"n_triples":len(groups),
        "rule_rankings_certified":all(r.get("hits_certified",False) for model in rules_t+rules_c for r in model),
        "n_neural_seeds":len(neural_t),"n_treatment_miners":len(rules_t),"n_control_miners":len(rules_c),
        "bootstrap":"paired query/triple and neural seeds; independent graph-specific miner draws", "repetitions":repetitions}


def frozen_family_gap(general_t,general_c,constants_t,constants_c,repetitions=1000,seed=2026):
    """Change in general-minus-constant success for two fixed rule subsets.

    All four rankings must address the identical query sequence and be certified.
    The signed within-query family contrast is formed before resampling shared
    original-triple clusters, so families never double the query sample size.
    """
    collections=(general_t,general_c,constants_t,constants_c)
    if any(not rows for rows in collections):
        raise ValueError("Complete frozen-family query sets required")
    fields=("query_id","triple_id","head","relation","tail","direction")
    identity=lambda rows:[tuple(row[k] for k in fields) for row in rows]
    reference=identity(general_c)
    if any(identity(rows)!=reference for rows in collections):
        raise ValueError("Frozen-family query identities are inconsistent")
    if not all(row.get("hits_certified",False) for rows in collections for row in rows):
        raise ValueError("Frozen-family gap requires certified rankings in all four query sets")
    if any(row["hits1"] not in (0,1) for rows in collections for row in rows):
        raise ValueError("Frozen-family gap requires binary Hits@1 outcomes")
    def contrast(general,constants):
        return [{**{k:g[k] for k in fields},"family_success_gap":int(g["hits1"])-int(c["hits1"]),"hits_certified":True}
                for g,c in zip(general,constants)]
    result=effect([contrast(general_t,constants_t)],[contrast(general_c,constants_c)],
        metric="family_success_gap",independent_models=False,repetitions=repetitions,seed=seed)
    result.update({"estimand":"(general Hits@1 - constant Hits@1) treatment minus the same gap in control",
        "bootstrap":"shared original-test-triple clusters; fixed family subsets; no independent model resampling",
        "uncertainty_scope":"conditional on these fixed family subsets and graph draws; no catalog-learning or perturbation-population replication",
        "n_fixed_family_subsets":2,"sample_unit":"unique directional query, clustered by its original triple; families are paired outcomes"})
    return result


def _compact(rows,entity_index=None):
    for r in rows:
        if entity_index is not None:
            mask=0
            for entity,_ in r["returned_candidates"]:
                mask |= 1 << entity_index[entity]
            r["_candidate_mask"]=mask
        r.pop("candidate_evidence",None)
        r.pop("returned_candidates",None)
    return rows


def _frozen_gold_loss(before,after):
    """A family-specific diagnostic, unavailable for censored/inconsistent support."""
    if before is None or after is None:return None
    if not (before["hits_certified"] and after["hits_certified"]):return None
    if after["_candidate_mask"] & ~before["_candidate_mask"]:return None
    return bool(before["true_returned"] and not after["true_returned"])


def build(dataset,prepared,root,output=None):
    root=Path(root);protocol=read(root/"protocol.json")
    from .structure_extensions import frozen_families, frozen_source
    secondary_families=frozen_families(root,protocol)
    sources={family:frozen_source(root,protocol,family) for family in secondary_families}
    native_order_hash=None
    if secondary_families and protocol.get("native_index_policy"):
        vocab=read(root/"native-vocabulary.json")
        native_order_hash=triple_digest(tuple((str(i),"entity",e) for i,e in enumerate(vocab["entities"]))+tuple((str(i),"relation",r) for i,r in enumerate(vocab["relations"])))
    smoke=protocol["stage"]=="SMOKE ONLY"
    smoke_output="artifacts/phase5/smoke-indexed-report" if protocol.get("native_index_policy") else "artifacts/phase5/smoke-report"
    output=Path(output or (smoke_output if smoke else "artifacts/phase5/report"))
    output.mkdir(parents=True,exist_ok=True)
    limit=protocol["query_limit_facts"]
    data={};overall=[];status=[];frozen_status=[];training=[];inventories=[]
    for condition in protocol["conditions"]:
        data[condition]={}
        for seed in protocol["neural_seeds"]:
            cell=root/condition/f"neural-{seed}"
            complete=(cell/"manifest.json").exists() and read(cell/"manifest.json")["status"]=="complete"
            status.append({"condition":condition,"component":f"neural-{seed}","status":"complete" if complete else "pending/incomplete"})
            if not complete: continue
            record=read(cell/"embedding/curve.json")
            training.append({"condition":condition,"backend":"ComplEx","replicate":seed, **{k:record[k] for k in ("best_epoch","completed_epochs","training_seconds","training_cpu_seconds","optimizer_updates","examples_seen","effective_training_facts")}})
            for policy in ("validation-best","fixed-updates","last-epoch"):
                path=cell/policy
                if not (path/"metrics.json").exists():continue
                metrics=read(path/"metrics.json")
                rows=_compact(checked_rows(path,dataset,limit))
                data[condition].setdefault(f"embedding:{policy}",[]).append(rows)
                overall.append({"condition":condition,"backend":"ComplEx "+policy,"replicate":seed,**metrics})
        for realization in protocol["mining_realizations"]:
            cell=root/condition/f"rules-{realization}"
            complete=(cell/"manifest.json").exists() and read(cell/"manifest.json")["status"]=="complete"
            status.append({"condition":condition,"component":f"rules-{realization}","status":"complete" if complete else "pending/incomplete"})
            if (cell/"mining/training.json").exists():
                record=read(cell/"mining/training.json")
                training.append({"condition":condition,"backend":"AnyBURL","replicate":realization,"training_seconds":record["training_seconds"],
                    "training_cpu_seconds":record.get("child_cpu_seconds"),"mining_seconds_requested":record["config"]["seconds"],"java_seed_controlled":False,
                    "stage_status":"mining and application complete" if complete else "mining complete; application incomplete"})
            if (cell/"catalog/inventory.json").exists():
                inventory=read(cell/"catalog/inventory.json")
                inventories.extend({"condition":condition,"mining_realization":realization,"application_complete":complete,**r} for r in inventory["statistics"])
            if not complete:continue
            for family in protocol["rule_families"]:
                path=cell/family;metrics=read(path/"metrics.json")
                if metrics["mrr_exact"] is not None: raise ValueError("Rule MRR must remain unavailable")
                rows=_compact(checked_rows(path,dataset,limit))
                data[condition].setdefault("rules:"+family,[]).append(rows)
                overall.append({"condition":condition,"backend":"AnyBURL "+family,"replicate":realization,**metrics})
        for family in secondary_families:
            path=root/condition/"frozen"/family
            available=(path/"metrics.json").exists()
            frozen_status.append({"condition":condition,"family":family,"status":"complete" if available else "pending/incomplete"})
            if not available:continue
            metrics=read(path/"metrics.json")
            provenance=metrics["provenance"]
            if provenance["rule_file_sha256"]!=sources[family]["sha256"] or provenance["training_graph_sha256"]!=protocol["source_graph_sha256"][condition]:
                raise ValueError("Frozen report inputs do not match the declared family catalog and training graph")
            if native_order_hash is not None and provenance.get("native_token_order_sha256")!=native_order_hash:
                raise ValueError("Frozen report input uses another native vocabulary order")
            if metrics["mrr_exact"] is not None:raise ValueError("Frozen rule MRR must remain unavailable")
            data[condition]["frozen:"+family]=[_compact(checked_rows(path,dataset,limit),dataset.graph.entity_to_id)]
            overall.append({"condition":condition,"backend":"Frozen "+family,"replicate":0,**metrics})
    effects=[];gaps=[];frozen_gaps=[];frozen_gap_status=[]
    comparisons=[(c,"original") for c in protocol["conditions"] if c!="original"]
    comparisons.append(("targeted_local","targeted_relation_matched_control"))
    for treatment,control in comparisons:
        if treatment not in data or control not in data:continue
        for role in sorted(set(data[treatment]) & set(data[control])):
            a,b=data[treatment][role],data[control][role]
            expected=len(protocol["neural_seeds"]) if role.startswith("embedding:") else 1 if role.startswith("frozen:") else len(protocol["mining_realizations"])
            if len(a)!=expected or len(b)!=expected:continue
            metrics=("hits1","hits10","reciprocal_rank") if role.startswith("embedding:") else ("hits1","hits10","covered","true_returned")
            for metric in metrics:
                effects.append({"treatment":treatment,"control":control,"backend":role,"metric":metric,
                    **effect(a,b,metric,independent_models=role.startswith("rules:"))})
        n="embedding:validation-best";r="rules:all"
        if all(key in data[c] and len(data[c][key])==(len(protocol["neural_seeds"]) if key==n else len(protocol["mining_realizations"]))
               for c in (treatment,control) for key in (n,r)):
            gaps.append({"treatment":treatment,"control":control,"estimand":"change in neural-minus-all-rules Hits@1 gap",
                **gap_effect(data[treatment][n],data[control][n],data[treatment][r],data[control][r])})
        needed=("frozen:general","frozen:constants")
        available=all(key in data[c] and len(data[c][key])==1 for c in (treatment,control) for key in needed)
        if not available:
            frozen_gap_status.append({"treatment":treatment,"control":control,"status":"pending/not declared",
                "reason":"Both frozen families and both graph conditions are required"})
        else:
            gt,gc=data[treatment][needed[0]][0],data[control][needed[0]][0]
            ct,cc=data[treatment][needed[1]][0],data[control][needed[1]][0]
            if not all(row["hits_certified"] for rows in (gt,gc,ct,cc) for row in rows):
                frozen_gap_status.append({"treatment":treatment,"control":control,"status":"unavailable: uncertified ranking",
                    "reason":"A numerical certified family gap is not inferred from censored retrieved outcomes"})
            else:
                frozen_gaps.append({"treatment":treatment,"control":control,**frozen_family_gap(gt,gc,ct,cc)})
                frozen_gap_status.append({"treatment":treatment,"control":control,"status":"complete",
                    "reason":"Four certified paired query sequences; fixed catalog subsets"})
    original_diag=GraphDiagnostics(dataset.graph)
    frequency_cutoffs=np.quantile(list(original_diag.frequency.values()),[1/3,2/3])
    targets=set(read(Path(prepared)/"plan.json")["interventions"]["original"]["targets"])
    scenarios=[]
    for treatment,control in comparisons:
        if treatment not in data or control not in data:continue
        for role in ("embedding:validation-best","rules:all","rules:general","rules:constants"):
            if role not in data[treatment] or role not in data[control]:continue
            a,b=data[treatment][role],data[control][role]
            expected=len(protocol["neural_seeds"]) if role.startswith("embedding:") else len(protocol["mining_realizations"])
            if len(a)!=expected or len(b)!=expected:continue
            groups=defaultdict(list)
            for i,row in enumerate(b[0]):
                known=row["tail"] if row["direction"]=="head" else row["head"]
                groups["original_known_degree",original_diag.degree_group(known)].append(i)
                f=original_diag.frequency[row["relation"]]
                groups["original_relation_frequency","low" if f<=frequency_cutoffs[0] else "medium" if f<=frequency_cutoffs[1] else "high"].append(i)
                groups["known_endpoint_targeted",str(known in targets)].append(i)
            for (feature,value),indices in groups.items():
                aa=[[row[i] for i in indices] for row in a];bb=[[row[i] for i in indices] for row in b]
                scenarios.append({"treatment":treatment,"control":control,"backend":role,"feature":feature,"value":value,
                    **effect(aa,bb,independent_models=role.startswith("rules:"),repetitions=500),
                    "interpretation":"exploratory effect heterogeneity; strata fixed using original train-observable known-node/relation features only"})
    # Query joins retain targets only for evaluation diagnostics, never inference.
    features={}
    with Path("artifacts/phase5/validation/graph-query-features.csv").open() as f:
        for row in csv.DictReader(f):features[row["condition"],row["triple_id"]]=row
    frozen_join=[]
    for family in secondary_families:
        role="frozen:"+family
        if role not in data.get("original",{}):continue
        for condition,models in data.items():
            if role not in models:continue
            for before,after in zip(data["original"][role][0],models[role][0]):
                added=(after["_candidate_mask"] & ~before["_candidate_mask"]).bit_count()
                lost=(before["_candidate_mask"] & ~after["_candidate_mask"]).bit_count()
                frozen_join.append({**features[condition,after["triple_id"]],"family":family,"query_id":after["query_id"],"direction":after["direction"],
                    "candidate_supports_lost":lost,"candidate_supports_newly_added":added,"support_monotone":added==0,
                    "original_covered":before["covered"],"modified_covered":after["covered"],
                    "original_truth_generated":before["true_returned"],"modified_truth_generated":after["true_returned"],
                    "original_rank":before["rank"],"modified_rank":after["rank"],"original_hits1":before["hits1"],"modified_hits1":after["hits1"],
                    "original_hits10":before["hits10"],"modified_hits10":after["hits10"],
                    "original_hits_certified":before["hits_certified"],"modified_hits_certified":after["hits_certified"],
                    "gold_support_disappeared":_frozen_gold_loss(before,after),
                    "top1_changed":[x[0] for x in before["top_predictions"][:1]]!=[x[0] for x in after["top_predictions"][:1]],
                    "scope":"same frozen positive-body rules/confidences; native frequency tie breaking recomputed; paths/targets are evaluation diagnostics"})
    write_csv(output/"frozen-query-joins.csv",frozen_join)
    family_checks=[]
    for family in secondary_families:
        group=[r for r in frozen_join if r["family"]==family]
        family_checks.append({"family":family,"n_condition_query_records":len(group),
            "n_unique_queries":len({r["query_id"] for r in group}),"n_triples":len({r["triple_id"] for r in group}),
            "n_candidate_support_monotonicity_violations":sum(not r["support_monotone"] for r in group)})
    write_json(output/"frozen-support-checks.json",{"n_queries":len(frozen_join),"n_family_condition_query_records":len(frozen_join),
        "n_unique_queries":len({r["query_id"] for r in frozen_join}),"n_triples":len({r["triple_id"] for r in frozen_join}),
        "families":family_checks,"n_candidate_support_monotonicity_violations":sum(not r["support_monotone"] for r in frozen_join),
        "count_scope":"n_queries is a compatibility alias for family-condition-query records, not an independent sample size; inference is paired separately within each family",
        "interpretation":"positive-body rule candidate support should not increase under deletions; violations require backend investigation before interpreting grounding loss"})
    frozen_summary=[]
    for family in secondary_families:
        for condition in protocol["conditions"]:
            group=[r for r in frozen_join if r["condition"]==condition and r["family"]==family]
            if group:
                frozen_summary.append({"family":family,"condition":condition,"n_queries":len(group),
                    "n_unique_queries":len({r["query_id"] for r in group}),"n_triples":len({r["triple_id"] for r in group}),
                    "candidate_supports_lost":sum(r["candidate_supports_lost"] for r in group),
                    "new_candidate_supports":sum(r["candidate_supports_newly_added"] for r in group),
                    "queries_losing_candidate_support":sum(r["candidate_supports_lost"]>0 for r in group),
                    "certified_gold_support_disappeared":sum(r["gold_support_disappeared"] is True for r in group),
                    "uncertified_gold_support_loss":sum(r["gold_support_disappeared"] is None for r in group),
                    "top1_changed":sum(r["top1_changed"] for r in group)})
    write_csv(output/"frozen-support-summary.csv",frozen_summary)
    joined=[]
    base=data.get("original",{})
    winner=lambda e,r:"both_correct" if e and r else "only_embeddings" if e else "only_rules" if r else "both_incorrect"
    for condition,models in data.items():
        needed=("embedding:validation-best","rules:all","rules:general","rules:constants")
        if not all(k in models and k in base and len(models[k])==len(base[k])==(len(protocol["neural_seeds"]) if k.startswith("embedding:") else len(protocol["mining_realizations"])) for k in needed):continue
        for ns,neural in enumerate(models[needed[0]]):
            for rs,rules in enumerate(models[needed[1]]):
                for i,(e,r) in enumerate(zip(neural,rules)):
                    be,br=base[needed[0]][ns][i],base[needed[1]][rs][i]
                    g,c=models[needed[2]][rs][i],models[needed[3]][rs][i]
                    bg,bc=base[needed[2]][rs][i],base[needed[3]][rs][i]
                    f=features[condition,e["triple_id"]]
                    known=e["tail"] if e["direction"]=="head" else e["head"]
                    frozen_losses={}
                    for family in ("general","constants"):
                        role="frozen:"+family
                        frozen=models.get(role,[None])[0]
                        original_frozen=base.get(role,[None])[0]
                        frozen_losses[family]=_frozen_gold_loss(original_frozen[i],frozen[i]) if frozen and original_frozen else None
                    top=lambda row:[v[0] for v in row["top_predictions"][:1]]
                    joined.append({**f,"query_id":e["query_id"],"direction":e["direction"],"neural_seed":protocol["neural_seeds"][ns],
                        "mining_realization_id":protocol["mining_realizations"][rs],"perturbation_seed":protocol["perturbation_seed"],
                        "known_endpoint_targeted":f["tail_targeted"] if e["direction"]=="head" else f["head_targeted"],
                        "embedding_original_rank":be["rank"],"embedding_modified_rank":e["rank"],"embedding_hits1":e["hits1"],"rule_hits1":r["hits1"],
                        "embedding_hits10":e["hits10"],"rule_hits10":r["hits10"],
                        "rule_original_hits_certified":br["hits_certified"],"rule_modified_hits_certified":r["hits_certified"],
                        "general_original_hits_certified":bg["hits_certified"],"general_modified_hits_certified":g["hits_certified"],
                        "constant_original_hits_certified":bc["hits_certified"],"constant_modified_hits_certified":c["hits_certified"],
                        "general_original_rank":bg["rank"],"general_modified_rank":g["rank"],
                        "constant_original_rank":bc["rank"],"constant_modified_rank":c["rank"],
                        "general_original_hits1":bg["hits1"],"general_modified_hits1":g["hits1"],
                        "general_original_hits10":bg["hits10"],"general_modified_hits10":g["hits10"],
                        "constant_original_hits1":bc["hits1"],"constant_modified_hits1":c["hits1"],
                        "constant_original_hits10":bc["hits10"],"constant_modified_hits10":c["hits10"],
                        "rule_original_covered":br["covered"],"rule_modified_covered":r["covered"],
                        "rule_original_truth_generated":br["true_returned"],"rule_modified_truth_generated":r["true_returned"],
                        "embedding_original_top1":top(be),"embedding_modified_top1":top(e),
                        "rule_original_top1":top(br),"rule_modified_top1":top(r),
                        "rule_original_rank":br["rank"],"rule_modified_rank":r["rank"],"embedding_top1_changed":top(e)!=top(be),"rule_top1_changed":top(r)!=top(br),
                        "general_covered_original":bg["covered"],"general_covered_modified":g["covered"],
                        "constant_covered_original":bc["covered"],"constant_covered_modified":c["covered"],
                        "general_truth_generated_original":bg["true_returned"],"general_truth_generated_modified":g["true_returned"],
                        "constant_truth_generated_original":bc["true_returned"],"constant_truth_generated_modified":c["true_returned"],
                        "frozen_general_gold_support_lost":frozen_losses["general"],"frozen_constant_gold_support_lost":frozen_losses["constants"],
                        "grounding_loss_status":"family-qualified certified frozen gold-support disappearance; see separate family fields" if any(v is True for v in frozen_losses.values()) else "not inferred; individual witnesses may still disappear",
                        "sampled_grounding_loss":None,"sampled_grounding_assessment":"not assessed; see case-witness report for sampled queries",
                        "original_winner":winner(be["hits1"],br["hits1"]),"modified_winner":winner(e["hits1"],r["hits1"]),
                        "relative_winner_changed":winner(be["hits1"],br["hits1"])!=winner(e["hits1"],r["hits1"]),
                        "interpretation":"truth-dependent ranks/path/support labels are evaluation-only; no selector trained"})
    write_csv(output/"overall.csv",overall);write_csv(output/"training-resources.csv",training);write_csv(output/"rule-statistics.csv",inventories)
    write_json(output/"paired-effects.json",effects);write_csv(output/"paired-effects.csv",effects)
    write_json(output/"gap-changes.json",gaps);write_csv(output/"gap-changes.csv",gaps)
    write_json(output/"frozen-family-gap.json",frozen_gaps);write_csv(output/"frozen-family-gap.csv",frozen_gaps)
    write_csv(output/"frozen-family-gap-status.csv",frozen_gap_status)
    write_csv(output/"query-joins.csv",joined);write_csv(output/"execution-status.csv",status)
    write_csv(output/"scenario-effects.csv",scenarios)
    write_csv(output/"frozen-execution-status.csv",frozen_status)
    applications=[{k:r.get(k) for k in ("condition","backend","replicate","catalog_rule_count","native_loaded_count","application_cpu_seconds","application_seconds_including_loading_and_cooling","inference_seconds")} for r in overall if "catalog_rule_count" in r]
    inventory_summary=[{**{k:r[k] for k in ("condition","mining_realization","native_family","body_length","n_rules","application_complete")},
        "median_raw_confidence":r["confidence_quantiles"][2],"median_raw_support":r["support_quantiles"][2],
        "raw_confidence_q25":r["confidence_quantiles"][1],"raw_confidence_q75":r["confidence_quantiles"][3],
        "raw_support_q25":r["support_quantiles"][1],"raw_support_q75":r["support_quantiles"][3]} for r in inventories]
    write_csv(output/"rule-application-resources.csv",applications)
    write_csv(output/"rule-inventory-summary.csv",inventory_summary)
    plots(output,overall,effects,smoke)
    text="# Phase 5: controlled graph-structure comparison\n\n"
    text+="**SMOKE OUTPUTS ONLY. One training epoch, two seconds of mining, first 16 official test facts. These validate execution and pairing, not the established 40-epoch baselines or scientific robustness.**\n\n" if smoke else "Exploratory CoDEx-S follow-up. The test set has been inspected repeatedly. Fresh contemporaneous original-graph controls are retrained under the same recipe/budget; established earlier results remain preserved.\n\n"
    if (root/"resource-stop.json").exists():
        stop=read(root/"resource-stop.json")
        text+="**Full-budget cohort resource-stopped and incomplete.** "+stop["reason"]+" Completed original-control checkpoints and mining output are retained, but incomplete rule application is not a rule baseline. No perturbed full-budget model is substituted with old weights or smoke results. A smaller corrected-index paired smoke has its own directory and report. See `runs/phase5-90/resource-stop.json` and `docs/PHASE5.md`.\n\n"
    if not protocol.get("native_index_policy"):
        text+="**Legacy smoke index policy:** these saved outputs predate the explicit original-native-vocabulary correction. They are retained as execution checks and must not be interpreted as clean structural effects. The corrected loader has separate synthetic and real-data checks; the primary study uses the corrected policy.\n\n"
    else:
        text+="The native loader explicitly registers the original training token order before loading modified positive edges. This preserves the candidate vocabulary and internal-ID tie order even when a relation loses every edge; removed and held-out facts are not inserted. The original implicit-index frozen attempt failed on absent relation P840 and is preserved under each condition's attempts directory. Confidence smoothing, weights, maxplus and frequency ties are unchanged.\n\n"
    text+="## Execution\n\n"+table(status,["condition","component","status"])
    if frozen_status:
        text+="\n## Frozen-family execution\n\n"+table(frozen_status,["condition","family","status"])
        text+="\nFrozen families are separate fixed-catalog evidence interventions on the same held-out queries. Their query rows are not additional independent observations or learning realizations. An extension manifest adds families without rewriting the base protocol.\n"
    text+="\n## Overall paired inputs\n\n"+table(overall,["condition","backend","replicate","n_queries","hits_metric_status","hits1","hits10","mrr_exact","coverage","correct_answer_generation_coverage"])
    text+="\nRule Hits use the native supported-candidate order, with abstentions counted as misses. They are not full-universe zero-score tie rankings. If any native family cannot be certified, that row and its paired differences remain retrieved-list outcomes; bootstrap intervals do not resolve censoring. Exact full-universe rule MRR is never reported.\n"
    if smoke and any(r.get("catalog_rule_count")==0 for r in overall):
        text+="\n**Some smoke rule inventories are empty.** Two seconds can be insufficient for mining startup and useful learning. Empty inventories correctly abstain; differences between these smoke cells are not model-family or structural-reliability findings.\n"
    selected=[r for r in effects if r["metric"]=="hits1"]
    text+="\n## Intervention minus matched control\n\nNegative differences indicate degradation.\n\n"+table(selected,["treatment","control","backend","difference","ci_low","ci_high","all_rankings_certified","n_unique_queries","n_triples"])
    text+="\n## Change in relative neural–rule gap\n\nPositive values mean the neural-minus-rule Hits@1 gap increased; negative values mean it decreased. Neither sign alone establishes that either model improved.\n\n"+table(gaps,["treatment","control","difference","ci_low","ci_high","rule_rankings_certified","n_neural_seeds","n_treatment_miners","n_control_miners"])
    text+="\n## Paired frozen-family gap\n\nThis separate diagnostic estimates [(general Hits@1 − constant Hits@1) in the treatment graph] − [the same family gap in the control graph]. Positive values favor general rules in relative sensitivity; either family may still degrade in absolute accuracy. Both families use the same paired held-out queries, clustered by original triple, with no independent model resampling. The sample size is the number of unique directional queries, not the sum of family rows. This is conditional evidence for these fixed subsets and graph draws, not catalog-population or perturbation-population replication, additive prediction credit, or the primary neural–rule comparison.\n\n"+table(frozen_gaps,["treatment","control","difference","ci_low","ci_high","n_unique_queries","n_triples","n_fixed_family_subsets"])
    if not frozen_gaps or any(row["status"]!="complete" for row in frozen_gap_status):
        text+="\nUncomputed family contrasts remain explicitly pending or uncertified:\n\n"+table(frozen_gap_status,["treatment","control","status","reason"])
    text+="\n![Performance degradation](degradation.png)\n\n![General and constant rule sensitivity](family-sensitivity.png)\n\n"
    text+="## Resource and optimization controls\n\n"+table(training,["condition","backend","replicate","training_seconds","training_cpu_seconds","best_epoch","completed_epochs","optimizer_updates","effective_training_facts"])
    text+="\nThe same 40-epoch ceiling/checkpoints and validation selection apply to each primary graph. Removal changes 65 to 58 optimizer updates per epoch. A predeclared checkpoint at 2,320 updates adds an equal-update diagnostic; last-epoch outputs separate validation stopping effects. Neither diagnostic is tuned on test outcomes. Smoke uses a one-epoch analogue. Training resource counters cover committed epochs, excluding cooling and validation; discarded partial-epoch work is not included. Native application wall times can include cooling and metadata loading.\n\n"
    text+="## Rule inventory and application resources\n\n"+table(applications,["condition","backend","replicate","catalog_rule_count","native_loaded_count","application_cpu_seconds","application_seconds_including_loading_and_cooling"])
    text+="\nCPU and wall application times include loading/scoring; wall time also includes deliberate cooling. Mining wall budgets do not guarantee identical CPU use, sampling throughput or learned inventories. Parsing/catalog export has no separate end-to-end resource counter.\n\n"
    text+=table(inventory_summary,["condition","native_family","body_length","n_rules","application_complete","median_raw_confidence","median_raw_support"])
    text+="\n`rule-statistics.csv` stores full 0/25/50/75/100 percentiles, and `rule-inventory-summary.csv` exposes interquartile statistics. Inventories from completed mining may be shown even when application is incomplete; they carry no claimed prediction result. These are raw learned-rule confidence/support, not calibrated probabilities; native smoothing and family weights remain those recorded in each application. Inventory size alone is not predictive contribution.\n\n"
    text+="## Hypotheses, controls and confounds\n\n"+table([{"hypothesis":k,**v} for k,v in protocol["hypotheses"].items()],["hypothesis","intervention","control","measurement","confounds"])
    complete_matrix=all(s["status"]=="complete" for s in status)
    frozen_complete=all("frozen:general" in data[c] for c in protocol["conditions"])
    frozen_constant_complete="constants" in secondary_families and all("frozen:constants" in data[c] for c in protocol["conditions"])
    h3_status="fresh family comparisons available" if complete_matrix else "fresh family comparisons pending/incomplete"
    h3_boundary="confidences, learned inventory and mining realization change together; frozen-constant experiment deferred"
    if "constants" in secondary_families:
        h3_status+="; frozen general/constants comparisons "+("complete" if frozen_complete and frozen_constant_complete else "pending/incomplete")
        h3_boundary="frozen-family evidence availability is measured separately from fresh learning; fixed-catalog differences do not replace the fresh-learning comparison or give an additive causal decomposition"
    evidence_status=[
        {"question":"H1: differential sensitivity to removal","status":"bounded paired matrix complete" if complete_matrix else "fresh-model matrix incomplete","boundary":f"declared {len(protocol['neural_seeds'])} neural seeds and {len(protocol['mining_realizations'])} miners per graph; singleton factors cannot estimate learning variability; fixed-update outputs address only one optimization confound"},
        {"question":"H2: general-rule body evidence","status":"frozen-catalog intervention complete" if frozen_complete else "frozen-catalog intervention incomplete","boundary":"candidate-pair support losses are measured; sampled groundings are separate; ranking also uses graph-frequency ties"},
        {"question":"H3: constant versus general rules","status":h3_status,"boundary":h3_boundary},
        {"question":"H4: targeted versus relation-matched removal","status":"paired primary comparison available" if any(r['control']=='targeted_relation_matched_control' for r in gaps) else "primary comparison pending; consult frozen evidence separately","boundary":"exact relation totals matched; endpoint frequencies, degrees and paths jointly change; one removal draw"},
        {"question":"H5: query characteristics and robustness","status":"exploratory strata available" if scenarios else "fresh-model strata pending","boundary":"strata use original train-observable features; no causal mediation or deployment selector established"}]
    write_csv(output/"hypothesis-status.csv",evidence_status)
    text+="\n## Current evidential status\n\n"+table(evidence_status,["question","status","boundary"])
    text+="\n## Evidence intervention versus retraining\n\nFrozen-family results reapply subsets of the established original catalog with original confidence/support on modified training facts. General rules are variable-only relational implications; the constant subset contains constant-bearing conditional implications and excludes unconditional zero-body entity priors. This is not re-mining and does not replace the primary rule baseline. Native training-frequency tie breaking changes with the graph, so ranking changes cannot all be attributed to missing bodies. The catalog also differs from the fresh primary original inventory; primary/secondary differences and differences between families are not an additive causal decomposition. Gold-support disappearance is inferred separately by family only where candidate enumeration is certified and its support check is consistent; observed witness loss can occur even when redundant support keeps a prediction available.\n\n"
    if "constants" not in secondary_families:
        text+="Constant frozen-catalog full-query evaluation is not declared in this cohort.\n\n"
    elif not frozen_constant_complete:
        text+="The frozen-constant extension is declared but incomplete; unavailable conditions remain pending and are not replaced by general-rule results.\n\n"
    text+="## Query-level explanations\n\n`query-joins.csv` pairs ranks, coverage, winner changes and original/modified degrees/frequencies for completed fresh-model comparison cells. Forward-directed typed two-/three-hop walk counts follow h → … → t using existing edge directions and permit revisiting entities. They exclude inverse-oriented native rule bodies, such as h ← a → t, and are a restricted structural proxy rather than total relational-path availability or native grounding counts. Truth endpoints/ranks/winner labels are strictly diagnostic. Neural changes are measured sensitivities, not invented explanations of internal representations.\n\n"
    if not complete_matrix:
        text+="**Primary fresh-model explanations remain pending for incomplete cells.** Any partial `query-joins.csv` rows represent only completed comparison cells, not the full planned cohort. Missing joins and `cases.md` must not be replaced by frozen-rule or smoke outputs.\n\n"
    if (output/"cases.md").exists():
        text+="[Fresh-model case studies](cases.md) document sampled training-only witnesses for available completed comparisons; unassessed witness fields remain unknown.\n\n"
    else:
        text+="Primary `cases.md` has not been generated for this cohort; it requires completed fresh original and modified predictions.\n\n"
    if (output/"frozen-cases.md").exists():
        text+="[Frozen-catalog case studies](frozen-cases.md) and `frozen-witnesses.csv` document checked before/after training-edge witnesses for the separate inference-time evidence intervention. They do not establish a retrained embedding response.\n\n"
    elif not smoke:
        text+="The `frozen-cases` command generates separate [frozen-catalog case studies](frozen-cases.md); these have not yet been generated in this report directory. They concern inference-time evidence only and do not substitute for primary fresh-model cases.\n\n"
    if (output/"frozen-constants-cases.md").exists():
        text+="[Frozen constant-bearing case studies](frozen-constants-cases.md) provide separately checked conditional-rule witnesses for that fixed family. They do not turn constant-bearing learned implications into unconditional entity-frequency priors.\n\n"
    text+="## Limitations and research conclusion\n\nDirect observations are the graph/path changes and recorded paired outcomes. Controlled evidence concerns these exact missing-edge protocols and contemporaneous trained systems. A single removal/target draw does not establish population-level structural effects. When a comparison has one neural seed or one independently learned inventory per graph, intervals cannot estimate variation in that singleton learning factor. Replicated comparisons resample the available seed and miner factors separately; few repetitions still give limited learning-variability estimates. Neural seed indices are paired across graphs; miner realizations are independently resampled by graph when replicated, never treated as paired deterministic seeds. Shared entities/relations create additional graph dependence.\n\nTargeted versus relation-count-matched removal controls relation totals but still changes endpoint frequencies, local degree and paths together. Retrained-rule changes combine evidence loss, changed learned confidences/inventories and mining stochasticity. Mechanisms behind embedding sensitivity remain hypotheses. Replication counts and completion are recorded above; additional perturbation draws remain future work. CoDEx-M is a later replication dataset after methodology freeze. No larger retention sweep or expensive published-budget reproduction is automatically launched.\n"
    text+="\n`scenario-effects.csv` reports intervals and sample sizes within original known-node degree, relation-frequency and target-incidence strata. Groups use original training information, not post-removal or answer-dependent features. These are exploratory effect heterogeneity, not causal mediation or a deployment selector. `query-joins-with-witnesses.csv`, when generated by the case command, adds verified sampled witness losses.\n"
    if not smoke and not all(s["status"]=="complete" for s in status):text+="\n**Primary matrix incomplete: missing cells are not conclusions and are not replaced with partial checkpoints or established models.**\n"
    frozen_text="## Frozen support checks\n\nHere a lost candidate support means one (directional query, candidate entity) pair is no longer generated by the specified frozen family. These counts are not numbers of rule groundings, learned rules, or the miner's rule-support statistic. Top-1 changes use evaluator-filtered rankings. Sample sizes are reported within family and condition; the same queries appearing across families or conditions are paired observations, not independent replications.\n\n"+table(frozen_summary,["family","condition","n_unique_queries","n_triples","candidate_supports_lost","queries_losing_candidate_support","certified_gold_support_disappeared","new_candidate_supports","top1_changed"])
    if frozen_summary:
        violations=sum(r["new_candidate_supports"] for r in frozen_summary)
        frozen_text+=("\n**Unexpected new frozen candidates were observed: investigate the native backend before interpreting missing-body effects.**\n\n" if violations else "\nNo new candidate support was observed under deletions in these frozen-catalog queries. This is consistent with positive-body evidence loss, not a generalization across learned catalogs or graph draws.\n\n")
        if any(r["backend"].startswith("frozen:") and r["metric"] in ("covered","true_returned") and r["ci_low"]==r["ci_high"]==0 for r in effects):
            frozen_text+="A degenerate coverage interval [0, 0] reflects unchanged outcomes in the observed empirical query pairs. It does not establish zero loss probability on unseen queries, other learned catalogs or other perturbation draws.\n\n"
    frozen_text+="![Frozen evidence sensitivity](frozen-sensitivity.png)\n\n"
    text=text.replace("## Query-level explanations",frozen_text+"## Query-level explanations",1)
    findings=[]
    for row in selected:
        if row["control"]=="original" and row["backend"] in ("embedding:validation-best","rules:all"):
            findings.append({"evidence_class":"Direct paired observation, conditional learned models","comparison":row["treatment"]+" vs original; "+row["backend"],
                "observation":f"{'Certified' if row['all_rankings_certified'] else 'Retrieved-list'} Hits@1 change {row['difference']:+.4f}, conditional 95% interval [{row['ci_low']:+.4f}, {row['ci_high']:+.4f}]",
                "boundary":"Fresh-training sensitivity; not a universal structural mechanism or replicated causal effect; any censoring persists"})
    for row in effects:
        if not row["backend"].startswith("frozen:"):continue
        family=row["backend"].split(":",1)[1]
        family_label={"general":"general","constants":"constant-bearing conditional"}.get(family,family)
        if row["metric"]=="hits1" and row["control"]=="original":
            findings.append({"evidence_class":"Controlled inference-time graph intervention","family":family,"comparison":row["treatment"]+" vs original; fixed "+family_label+" catalog",
                "observation":f"Hits@1 change {row['difference']:+.4f}, conditional 95% interval [{row['ci_low']:+.4f}, {row['ci_high']:+.4f}]",
                "boundary":"Ranking responds to missing supports and native graph-frequency ties; this does not isolate their separate contributions; any uncertified ranking remains censored"})
        if row["metric"]=="true_returned" and row["control"]=="original":
            findings.append({"evidence_class":"Controlled inference-time evidence intervention","family":family,"comparison":row["treatment"]+" vs original; fixed "+family_label+" catalog",
                "observation":f"Gold-generation coverage change {row['difference']:+.4f}, conditional 95% interval [{row['ci_low']:+.4f}, {row['ci_high']:+.4f}]",
                "boundary":"Fixed implications, analyzed within family; no catalog/perturbation population replication or additive decomposition; uncertified generation outcomes remain observed retrievals"})
    write_csv(output/"research-findings.csv",findings)
    text=text.replace("## Limitations and research conclusion","## Observations and evidential boundaries\n\n"+table(findings,["evidence_class","comparison","observation","boundary"])+"\n## Limitations and research conclusion",1)
    (output/"report.md").write_text(text)
    write_json(output/"report-status.json",{"smoke":smoke,"n_joined_rows":len(joined),"cells":status,"all_primary_cells_complete":all(s["status"]=="complete" for s in status),
        "frozen_families":secondary_families,"frozen_family_cells":frozen_status,"all_declared_frozen_cells_complete":all(s["status"]=="complete" for s in frozen_status),
        "frozen_support_counts_by_family":family_checks,"neural_seeds":protocol["neural_seeds"],"independent_miners_per_graph":len(protocol["mining_realizations"]),"root":str(root)})
    return output


def plots(output,overall,effects,smoke=False):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    observed_conditions={r["condition"] for r in overall}
    conditions=[c for c in CONDITIONS if c!="original" and (not smoke or c in observed_conditions)]
    def sample_label(roles):
        sizes=sorted({r["n_unique_queries"] for r in effects if r["backend"] in roles and r["control"]=="original"})
        return f"n={sizes[0]} directional queries" if len(sizes)==1 else "variable query counts" if sizes else "no completed paired comparisons"
    names={"random_global":"Global random","random_relation_stratified":"Relation-stratified","targeted_local":"Targeted local","targeted_relation_matched_control":"Relation-matched"}
    plt.rcParams.update({"font.size":9,"axes.spines.top":False,"axes.spines.right":False,"savefig.dpi":200})
    fig,ax=plt.subplots(figsize=(8,4))
    for color,(offset,role,label) in enumerate(((-.13,"embedding:validation-best","ComplEx"),(.13,"rules:all","All rules"))):
        for i,c in enumerate(conditions):
            row=next((r for r in effects if r["treatment"]==c and r["control"]=="original" and r["backend"]==role and r["metric"]=="hits1"),None)
            if row:
                ax.errorbar(i+offset,row["difference"],yerr=[[row["difference"]-row["ci_low"]],[row["ci_high"]-row["difference"]]],fmt="o" if row["all_rankings_certified"] else "x",color=f"C{color}",capsize=3,label=label if i==next((j for j,x in enumerate(conditions) if any(r["treatment"]==x and r["backend"]==role for r in effects)),i) else None)
    ax.axhline(0,color="grey",lw=.8);ax.set_xticks(range(len(conditions)),[names[c] for c in conditions],rotation=15)
    prefix="SMOKE ONLY; " if smoke else "Exploratory; "
    ax.set(ylabel="Change in filtered Hits@1 vs fresh original control",title=prefix+sample_label(("embedding:validation-best","rules:all"))+"\nPaired triple-cluster 95% intervals; conditional on learned models")
    if ax.get_legend_handles_labels()[0]:ax.legend()
    else:ax.text(.5,.5,"Fresh retraining comparison pending",transform=ax.transAxes,ha="center")
    if any(not r["all_rankings_certified"] for r in effects):fig.text(.5,.01,"× marks uncertified retrieved-list outcomes; intervals do not resolve censoring",ha="center",fontsize=8)
    fig.tight_layout(rect=(0,.04,1,1));fig.savefig(output/"degradation.png");fig.savefig(output/"degradation.pdf");plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10,4),sharey=True)
    for ax,role,label in zip(axes,("rules:general","rules:constants"),("General relational rules","Constant-bearing implications")):
        for color,(offset,metric,desc) in enumerate(((-.14,"covered","Candidate coverage"),(0.,"true_returned","Gold generation"),(.14,"hits1","Hits@1"))):
            seen=False
            for i,c in enumerate(conditions):
                row=next((r for r in effects if r["treatment"]==c and r["control"]=="original" and r["backend"]==role and r["metric"]==metric),None)
                if row:
                    ax.errorbar(i+offset,row["difference"],yerr=[[row["difference"]-row["ci_low"]],[row["ci_high"]-row["difference"]]],fmt="o" if row["all_rankings_certified"] else "x",color=f"C{color}",capsize=2,label=desc if not seen else None);seen=True
        ax.axhline(0,color="grey",lw=.8);ax.set_xticks(range(len(conditions)),[names[c] for c in conditions],rotation=25,ha="right");ax.set_title(label)
        if ax.get_legend_handles_labels()[0]:ax.legend(fontsize=8)
        else:ax.text(.5,.5,"Fresh family comparison pending",transform=ax.transAxes,ha="center")
    axes[0].set_ylabel("Change vs fresh original control (95% paired CI)")
    fig.suptitle(prefix+sample_label(("rules:general","rules:constants"))+"; conditional 95% intervals",fontsize=10)
    fig.tight_layout();fig.savefig(output/"family-sensitivity.png");fig.savefig(output/"family-sensitivity.pdf");plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(12,4.5),sharey=True)
    frozen_roles=("frozen:general","frozen:constants")
    for ax,role,label in zip(axes,frozen_roles,("General relational catalog","Constant-bearing conditional catalog")):
        for color,(offset,metric,desc) in enumerate(((-.14,"covered","Candidate coverage"),(0.,"true_returned","Gold generation"),(.14,"hits1","Hits@1"))):
            seen=False
            for i,c in enumerate(conditions):
                row=next((r for r in effects if r["treatment"]==c and r["control"]=="original" and r["backend"]==role and r["metric"]==metric),None)
                if row:
                    ax.errorbar(i+offset,row["difference"],yerr=[[row["difference"]-row["ci_low"]],[row["ci_high"]-row["difference"]]],fmt="o" if row["all_rankings_certified"] else "x",color=f"C{color}",capsize=3,label=desc if not seen else None);seen=True
        ax.axhline(0,color="grey",lw=.8);ax.set_xticks(range(len(conditions)),[names[c] for c in conditions],rotation=25,ha="right")
        ax.set_title(label+"\n"+sample_label((role,)),fontsize=10)
        if ax.get_legend_handles_labels()[0]:ax.legend(fontsize=8)
        else:ax.text(.5,.5,"Frozen-family comparison pending / not declared",transform=ax.transAxes,ha="center",fontsize=8)
    axes[0].set_ylabel("Change vs same catalog on original training graph")
    fig.suptitle(prefix+"separate fixed-family evidence interventions\nPaired triple-cluster 95% intervals; conditional on each catalog",fontsize=10)
    if any(not r["all_rankings_certified"] for r in effects if r["backend"] in frozen_roles):
        fig.text(.5,.01,"× marks uncertified retrieved-list outcomes; intervals do not resolve censoring",ha="center",fontsize=8)
    fig.tight_layout(rect=(0,.04,1,1));fig.savefig(output/"frozen-sensitivity.png");fig.savefig(output/"frozen-sensitivity.pdf");plt.close(fig)
