"""Sample real native rule witnesses and check exactly which training edges vanished."""
from pathlib import Path
import csv
import json
import re
from itertools import permutations
from dataclasses import asdict
from ..evaluation import queries
from ..io import write_json,write_csv
from .runner import read
from .families import AuditedRules
from .resources import CoolingBreaks
from .structure_audit import prepared_graphs
from .structure_report import checked_rows
from ..backends.anyburl import ATOM


def valid_native_grounding(expression,edges,predicted_triple=None):
    """Verify a returned binary implication witness; never mine/predict rules."""
    head_text,body_text=expression.split("<=",1)
    head=ATOM.findall(head_text)[0];body=ATOM.findall(body_text)
    if len(body)!=len(edges):return False
    def unify(atom,edge,bindings):
        predicate,left,right=atom;h,r,t=edge
        if predicate!=r:return False
        for term,value in ((left,h),(right,t)):
            if re.fullmatch(r"[A-Z]",term):
                if term in bindings and bindings[term]!=value:return False
                bindings[term]=value
            elif term!=value:return False
        return True
    initial={}
    if predicted_triple is not None and not unify(head,predicted_triple,initial):return False
    for order in permutations(edges):
        bindings=dict(initial)
        if all(unify(atom,edge,bindings) for atom,edge in zip(body,order)):return True
    return False


def inspect_witnesses(items, original_edges, modified_edges,predicted_triple=None):
    """Exact checks on sampled witnesses only; never infer completeness from them."""
    inspected=[]
    for item in items:
        for grounding in item.get("groundings",[])[:2]:
            edges=[tuple(edge) for edge in grounding]
            if any(edge not in original_edges for edge in edges):
                raise ValueError("A purported grounding contains a non-training edge")
            if not valid_native_grounding(item["expression"],edges,predicted_triple):
                raise ValueError("Native grounding is inconsistent with its rule or predicted triple")
            missing=[edge for edge in edges if edge not in modified_edges]
            inspected.append({"expression":item["expression"],"grounding":edges,"missing_training_edges":missing,"survives":not missing})
    return inspected


def comparison_categories(before_neural,after_neural,before_rules,after_rules,after_general=None):
    """Truth-dependent illustrative case labels; never deployment features."""
    labels=[]
    if before_neural["hits1"] and not after_neural["hits1"]:labels.append("neural_success_lost")
    if before_rules["hits1"] and not after_rules["hits1"]:labels.append("rule_success_lost")
    if (bool(before_neural["hits1"]),bool(before_rules["hits1"]))!=(bool(after_neural["hits1"]),bool(after_rules["hits1"])):
        labels.append("relative_winner_changed")
    if after_neural["hits1"] and not after_rules["hits1"]:labels.append("embedding_success_all_rules_miss")
    if after_general is not None:
        if after_general["hits1"] and not after_neural["hits1"]:labels.append("general_rule_success_embedding_miss")
        if after_neural["hits1"] and not after_general["hits1"]:labels.append("embedding_success_general_rules_miss")
    return labels


def build(dataset,prepared,root,output=None):
    root=Path(root);protocol=read(root/"protocol.json");smoke=protocol["stage"]=="SMOKE ONLY"
    ns_id=protocol["neural_seeds"][0];rs_id=protocol["mining_realizations"][0]
    smoke_output="artifacts/phase5/smoke-indexed-report" if protocol.get("native_index_policy") else "artifacts/phase5/smoke-report"
    output=Path(output or (smoke_output if smoke else "artifacts/phase5/report"))
    output.mkdir(parents=True,exist_ok=True)
    graphs=prepared_graphs(dataset,prepared)
    limit=protocol["query_limit_facts"]
    baseline_n=root/"original"/f"neural-{ns_id}"/"validation-best"
    baseline_r=root/"original"/f"rules-{rs_id}"/"all"
    if not (baseline_n/"metrics.json").exists() or not (baseline_r/"metrics.json").exists():
        raise ValueError("Complete fresh original-control predictions required for cases")
    neural=checked_rows(baseline_n,dataset,limit);rules=checked_rows(baseline_r,dataset,limit)
    original_general_path=baseline_r.parent/"general"
    original_general=checked_rows(original_general_path,dataset,limit) if (original_general_path/"metrics.json").exists() else None
    frozen_path=root/"original/frozen/general"
    frozen_original=checked_rows(frozen_path,dataset,limit) if (frozen_path/"metrics.json").exists() else None
    targets=set(graphs["original"][1]["targets"])
    with Path("artifacts/phase5/validation/graph-query-features.csv").open() as f:
        graph_features={(r["condition"],r["triple_id"]):r for r in csv.DictReader(f)}
    selected=[]
    for condition in protocol["conditions"]:
        if condition=="original":continue
        pn=root/condition/f"neural-{ns_id}"/"validation-best";pr=root/condition/f"rules-{rs_id}"/"all"
        if not (pn/"metrics.json").exists() or not (pr/"metrics.json").exists():continue
        modified_n=checked_rows(pn,dataset,limit);modified_r=checked_rows(pr,dataset,limit)
        general_path=pr.parent/"general"
        modified_general=checked_rows(general_path,dataset,limit) if (general_path/"metrics.json").exists() else None
        pf=root/condition/"frozen/general"
        frozen=checked_rows(pf,dataset,limit) if (pf/"metrics.json").exists() else None
        top=lambda row:[x[0] for x in row["top_predictions"][:1]]
        buckets={}
        for i,(e,r) in enumerate(zip(modified_n,modified_r)):
            for label in comparison_categories(neural[i],e,rules[i],r,modified_general[i] if modified_general else None):
                buckets.setdefault(label,i)
            if frozen and frozen_original and frozen_original[i]["true_returned"] and not frozen[i]["true_returned"]:
                buckets.setdefault("frozen_gold_support_lost",i)
            known=e["tail"] if e["direction"]=="head" else e["head"]
            if known in targets and (top(e)!=top(neural[i]) or top(r)!=top(rules[i])):
                buckets.setdefault("targeted_known_endpoint_changed",i)
        if not buckets:buckets["first_queried_control_case"]=0
        for category,i in buckets.items():
            selected.append({"condition":condition,"category":category,"query_id":modified_n[i]["query_id"],"direction":modified_n[i]["direction"],
                "triple":tuple(modified_n[i][k] for k in ("head","relation","tail")),
                "neural_before":neural[i],"neural_after":modified_n[i],"rule_before":rules[i],"rule_after":modified_r[i],
                "general_before":original_general[i] if original_general else None,"general_after":modified_general[i] if modified_general else None,
                "frozen_before":frozen_original[i] if frozen_original else None,"frozen_after":frozen[i] if frozen else None,
                "graph_changes":graph_features[condition,modified_n[i]["triple_id"]],
                "witnesses":[],"sampling":f"first official query per predeclared loss/change category; neural seed{ns_id}/mining realization{rs_id}; illustrative not prevalence"})
    original_edges=set(dataset.graph.triples)
    original_catalog=read(root/"original"/f"rules-{rs_id}"/"catalog/inventory.json")["families"]
    source_models=[("fresh original constant implications",original_catalog["constants"]["path"]),
                   ("fresh original general rules",original_catalog["general"]["path"])]
    if not smoke:
        source_models.append(("established frozen general rules",read("runs/next-phase-frozen/subsets/subsets.json")["subsets"]["general"]["path"]))
    for source_name,path in source_models:
        gate=CoolingBreaks();gate.thermal_rest()
        backend=AuditedRules(dataset.graph,path,metadata_callback=gate.rest)
        normalized={re.sub(r"\s+","",r.expression):asdict(r) for r in backend.rules}
        for case in selected:
            h,r,t=case["triple"]
            candidates=[h if case["direction"]=="head" else t]
            candidates += [x[0] for key in ("rule_before","rule_after") for x in case[key]["top_predictions"][:1]]
            triples=[(e,r,t) if case["direction"]=="head" else (h,r,e) for e in dict.fromkeys(candidates)]
            evidence,_=backend.explain(triples)
            for triple in triples:
                native=evidence.get(triple,[])[:3]
                witnesses=inspect_witnesses(native,original_edges,set(graphs[case["condition"]][0].triples),triple)
                for witness in witnesses:
                    metadata=normalized.get(re.sub(r"\s+","",witness["expression"]),{})
                    case["witnesses"].append({"catalog":source_name,"predicted_triple":triple,
                        "is_correct_answer":triple==case["triple"],"raw_confidence":metadata.get("confidence"),"raw_support":metadata.get("support"),
                        **witness,"check":"all edges verified in original training graph; missing edges checked against this modified training graph"})
            gate.thermal_rest();gate.rest()
        del backend
    # Explain the actual modified-model predictions as well. These witnesses
    # come only from modified training edges and are labelled separately from
    # original-catalog samples used to demonstrate vanished evidence.
    if not smoke:
        indices=read(root/"native-vocabulary.json")
        for condition in protocol["conditions"]:
            cases=[c for c in selected if c["condition"]==condition]
            if not cases:continue
            catalog=read(root/condition/f"rules-{rs_id}"/"catalog/inventory.json")["families"]
            graph=graphs[condition][0];edges=set(graph.triples)
            for family in ("general","constants"):
                gate=CoolingBreaks();gate.thermal_rest()
                backend=AuditedRules(graph,catalog[family]["path"],metadata_callback=gate.rest,token_indices=indices)
                normalized={re.sub(r"\s+","",r.expression):asdict(r) for r in backend.rules}
                for case in cases:
                    h,r,t=case["triple"]
                    candidates=[h if case["direction"]=="head" else t]+[x[0] for x in case["rule_after"]["top_predictions"][:1]]
                    triples=[(e,r,t) if case["direction"]=="head" else (h,r,e) for e in dict.fromkeys(candidates)]
                    evidence,_=backend.explain(triples)
                    for triple in triples:
                        witnesses=inspect_witnesses(evidence.get(triple,[])[:3],edges,edges,triple)
                        for witness in witnesses:
                            metadata=normalized.get(re.sub(r"\s+","",witness["expression"]),{})
                            case["witnesses"].append({"catalog":f"fresh modified {family} rules ({condition})","predicted_triple":triple,
                                "is_correct_answer":triple==case["triple"],"raw_confidence":metadata.get("confidence"),"raw_support":metadata.get("support"),
                                **witness,"check":"all witness edges verified in this modified training graph; this is after-intervention evidence"})
                    gate.thermal_rest();gate.rest()
                del backend
    write_json(output/"case-studies.json",selected)
    losses=[]
    for case in selected:
        witnesses=case["witnesses"]
        losses.append({"condition":case["condition"],"query_id":case["query_id"],"category":case["category"],
            "neural_seed":ns_id,"mining_realization_id":rs_id,
            "n_sampled_groundings":len(witnesses),"n_sampled_groundings_lost":sum(not w["survives"] for w in witnesses),
            "sampled_grounding_loss":any(not w["survives"] for w in witnesses) if witnesses else None,
            "assessment":"sampled native witnesses; surviving samples do not prove that no other grounding disappeared"})
    write_csv(output/"witness-loss.csv",losses)
    if (output/"query-joins.csv").exists():
        index={(r["condition"],r["query_id"],str(r["neural_seed"]),str(r["mining_realization_id"])):r for r in losses}
        with (output/"query-joins.csv").open() as f:joined=list(csv.DictReader(f))
        for row in joined:
            sample=index.get((row["condition"],row["query_id"],row["neural_seed"],row["mining_realization_id"]))
            if sample:
                row.update({"sampled_grounding_loss":sample["sampled_grounding_loss"],"sampled_grounding_assessment":sample["assessment"],
                            "n_sampled_groundings":sample["n_sampled_groundings"],"n_sampled_groundings_lost":sample["n_sampled_groundings_lost"]})
        write_csv(output/"query-joins-with-witnesses.csv",joined)
    lines=["# Phase 5: measured changes and training-only rule witnesses","",
           "Cases are illustrative. Predictions come from the fresh paired experiment, while witness catalogs are explicitly labelled. A missing training edge is not a false fact: original positives remain evaluator filters. Neural rank changes are measured sensitivity, not invented internal explanations. Zero-body priors have no body grounding and are excluded from this witness collection.",""]
    for c in selected:
        h,r,t=c["triple"];q=f"(?, {r}, {t})" if c["direction"]=="head" else f"({h}, {r}, ?)"
        lines += [f"## {c['condition']} — {c['category']} — {c['query_id']}","",f"Query `{q}`; correct triple `{h} {r} {t}`.","",
            f"ComplEx rank: {c['neural_before']['rank']} → {c['neural_after']['rank']}; all-rule rank: {c['rule_before']['rank']} → {c['rule_after']['rank']}. Native rule abstentions have no rank.","",
            f"Original/new neural top predictions: `{c['neural_before']['top_predictions'][:2]}` → `{c['neural_after']['top_predictions'][:2]}`.","",
            f"Original/new rule top predictions: `{c['rule_before']['top_predictions'][:2]}` → `{c['rule_after']['top_predictions'][:2]}`.",""]
        f=c["graph_changes"]
        if c["general_after"]:
            before=c["general_before"];after=c["general_after"]
            lines += [f"General-rule rank {before['rank'] if before else 'unavailable'} → {after['rank']}; general-rule Hits@1 {before['hits1'] if before else 'unavailable'} → {after['hits1']}. Success labels use filtered Hits@1, independently of candidate coverage.",""]
        lines += [f"Training head/tail degrees: {f['original_head_degree']}/{f['original_tail_degree']} → {f['modified_head_degree']}/{f['modified_tail_degree']}; relation frequency {f['original_relation_frequency']} → {f['modified_relation_frequency']}. Directed typed two-/three-hop walks to the correct endpoint: {f['original_typed_twohop_walks_to_truth']}/{f['original_typed_threehop_walks_to_truth']} → {f['modified_typed_twohop_walks_to_truth']}/{f['modified_typed_threehop_walks_to_truth']}. Endpoint walk counts use the answer and are evaluation diagnostics.",""]
        if c["frozen_before"]:
            lines += [f"Frozen general-catalog correct-answer generation: {c['frozen_before']['true_returned']} → {c['frozen_after']['true_returned']}.",""]
        for w in c["witnesses"]:
            lines += [f"- {w['catalog']}: `{w['expression']}` supporting `{w['predicted_triple']}`; raw confidence {w['raw_confidence']}, support {w['raw_support']}. Training witness `{w['grounding']}`. Missing edges `{w['missing_training_edges']}`; survives={w['survives']}."]
        if not c["witnesses"]:lines += ["No sampled native conditional-rule witness was available; this is not a negative logical judgment."]
        lines += ["","Witnesses are sampled (first three rules, first two groundings per candidate/catalog), not a complete count of supporting instantiations.",""]
    (output/"cases.md").write_text("\n".join(lines)+"\n")
    return selected
