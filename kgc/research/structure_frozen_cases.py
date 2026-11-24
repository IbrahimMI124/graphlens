"""Verified native witnesses for the fixed-catalog evidence intervention only."""
from pathlib import Path
import csv
import gc
import re
from dataclasses import asdict
from ..io import write_json,write_csv,digest,triple_digest
from .runner import read
from .structure_audit import prepared_graphs
from .structure_report import checked_rows
from .structure_cases import inspect_witnesses
from .families import AuditedRules
from .resources import CoolingBreaks
from .structure_extensions import frozen_source


def build(dataset,prepared,root,output="artifacts/phase5/report",family="general"):
    if family not in ("general","constants"):
        raise ValueError("Frozen witnesses support general or constants conditional-rule subsets only")
    prefix="frozen" if family=="general" else "frozen-constants"
    family_label="general relational" if family=="general" else "constant-bearing conditional"
    root=Path(root);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    protocol=read(root/"protocol.json");graphs=prepared_graphs(dataset,prepared)
    if protocol["query_limit_facts"] is not None:
        raise ValueError("Frozen evidence cases require the full predeclared query sequence")
    source_record=frozen_source(root,protocol,family)
    source=source_record["path"]
    if digest(source)!=source_record["sha256"]:raise ValueError("Frozen witness catalog changed")
    for condition in protocol["conditions"]:
        provenance=read(root/condition/"frozen"/family/"metrics.json")["provenance"]
        if provenance["rule_file_sha256"]!=source_record["sha256"] or provenance["training_graph_sha256"]!=triple_digest(graphs[condition][0].triples):
            raise ValueError("Frozen witness graph/catalog does not match the saved predictions")
    with Path("artifacts/phase5/validation/graph-query-features.csv").open() as f:
        features={(r["condition"],r["triple_id"]):r for r in csv.DictReader(f)}
    original=checked_rows(root/"original"/"frozen"/family,dataset,None)
    cases=[]
    top=lambda row:[e for e,_ in row["top_predictions"][:1]]
    for condition in protocol["conditions"]:
        if condition=="original":continue
        modified=checked_rows(root/condition/"frozen"/family,dataset,None)
        if not all(a["hits_certified"] and b["hits_certified"] and a["support_complete"] and b["support_complete"] for a,b in zip(original,modified)):
            raise ValueError("Candidate-support loss requires certified exhaustive enumeration in both graphs")
        buckets={}
        for i,(a,b) in enumerate(zip(original,modified)):
            if a["hits1"] and not b["hits1"]:buckets.setdefault("top1_success_lost",i)
            if b["hits1"] and not a["hits1"]:buckets.setdefault("top1_success_gained",i)
            if top(a)!=top(b):buckets.setdefault("top1_changed",i)
            if len(b["returned_candidates"])<len(a["returned_candidates"]):buckets.setdefault("candidate_support_lost",i)
        for category,i in buckets.items():
            a,b=original[i],modified[i]
            changed_ids={e for e,_ in b["returned_candidates"]}
            lost=[e for e,_ in a["returned_candidates"] if e not in changed_ids]
            truth=a["head"] if a["direction"]=="head" else a["tail"]
            selected=list(dict.fromkeys([truth]+top(a)+top(b)+lost[:1]))
            candidates=[{"entity":e,"is_truth":e==truth,"support_lost":e in lost} for e in selected]
            def compact(row):
                return {k:v for k,v in row.items() if k not in ("returned_candidates","candidate_evidence")}
            cases.append({"family":family,"condition":condition,"category":category,"query_id":a["query_id"],
                "triple":tuple(a[k] for k in ("head","relation","tail")),"direction":a["direction"],
                "original":compact(a),"modified":compact(b),"selected_candidates":candidates,
                "graph_changes":features[condition,a["triple_id"]],"witnesses":[],
                "sampling":"first official query per loss/gain/change category; first original-ranked lost candidate; illustrative, not prevalence"})
        del modified
        gc.collect()
    del original
    indices=read(root/"native-vocabulary.json")
    original_edges=set(dataset.graph.triples)
    def collect(backend,case,phase):
        h,r,t=case["triple"]
        targets=[(e["entity"],r,t) if case["direction"]=="head" else (h,r,e["entity"]) for e in case["selected_candidates"]]
        evidence,_=backend.explain(targets)
        edges=set(graphs[case["condition"]][0].triples)
        for target,candidate in zip(targets,case["selected_candidates"]):
            for item in evidence.get(target,[])[:3]:
                checked=inspect_witnesses([item],original_edges if phase=="before" else edges,edges,target)
                for witness in checked:
                    metadata=normalized.get(re.sub(r"\s+","",item["expression"]),{})
                    case["witnesses"].append({"family":family,"phase":phase,"predicted_triple":target,
                        "is_truth":candidate["is_truth"],"candidate_support_lost":candidate["support_lost"],
                        "raw_confidence":metadata.get("confidence"),"raw_support":metadata.get("support"),**witness})
    gate=CoolingBreaks();gate.thermal_rest()
    backend=AuditedRules(dataset.graph,source,metadata_callback=gate.rest,token_indices=indices)
    normalized={re.sub(r"\s+","",r.expression):asdict(r) for r in backend.rules}
    for case in cases:
        collect(backend,case,"before");gate.thermal_rest();gate.rest()
    del backend
    for condition in protocol["conditions"]:
        subset=[c for c in cases if c["condition"]==condition]
        if not subset:continue
        gate.thermal_rest()
        backend=AuditedRules(graphs[condition][0],source,metadata_callback=gate.rest,token_indices=indices)
        for case in subset:
            collect(backend,case,"after");gate.thermal_rest();gate.rest()
        del backend
    rows=[]
    for case in cases:
        for w in case["witnesses"]:
            rows.append({"family":family,"condition":case["condition"],"query_id":case["query_id"],"category":case["category"],**w})
    write_json(output/f"{prefix}-case-studies.json",cases);write_csv(output/f"{prefix}-witnesses.csv",rows)
    conflicts=[w for w in rows if w["candidate_support_lost"] and (w["phase"]=="after" or w["survives"])]
    write_json(output/f"{prefix}-witness-checks.json",{"family":family,"n_cases":len(cases),"n_sampled_witnesses":len(rows),
        "n_before_witnesses_lost":sum(w["phase"]=="before" and not w["survives"] for w in rows),
        "n_support_loss_witness_conflicts":len(conflicts),"sampling":"first three native rules, first two groundings per selected candidate/phase; not exhaustive"})
    lines=["# Frozen-catalog evidence cases" if family=="general" else "# Frozen constant-bearing rule evidence cases","",
        f"These compare the identical frozen {family_label}-rule catalog on original and modified training graphs. No model is re-mined here. All sampled witnesses are checked for training-edge membership, variable/constant consistency and the predicted head. Before-witness missing edges are verified against the actual modified graph. After witnesses use only modified training edges. Rankings also depend on native graph-frequency ties. No embedding response is inferred from this experiment.","",
        "Cases are selected by evaluation outcomes and are illustrative, not deployment features or a representative prevalence estimate. Raw rule confidences/support remain frozen; scores are not probabilities. Entity/relation label metadata was not downloaded, so original Wikidata identifiers are retained.",""]
    if family=="constants":
        lines += ["This subset contains learned constant-bearing implications with nonempty bodies. Unconditional zero-body entity priors are excluded. Native confidence smoothing and Uc/Ud family weights are unchanged; inventory size is not predictive contribution.",""]
    if conflicts:lines += ["**Witness/ranking inconsistency detected. Do not interpret the affected cases as evidence of complete support loss until investigated.**",""]
    for case in cases:
        a,b=case["original"],case["modified"];h,r,t=case["triple"];f=case["graph_changes"]
        query=f"(?, {r}, {t})" if case["direction"]=="head" else f"({h}, {r}, ?)"
        lines += [f"## {case['condition']} — {case['category']} — {case['query_id']}","",
            f"Query `{query}`, correct triple `{h} {r} {t}`. Frozen-rule rank {a['rank']} → {b['rank']}; Hits@1 {a['hits1']} → {b['hits1']}; correct-answer generation {a['true_returned']} → {b['true_returned']}.","",
            f"Filtered top predictions `{a['top_predictions'][:2]}` → `{b['top_predictions'][:2]}`.","",
            f"Training degrees (head/tail) {f['original_head_degree']}/{f['original_tail_degree']} → {f['modified_head_degree']}/{f['modified_tail_degree']}; relation frequency {f['original_relation_frequency']} → {f['modified_relation_frequency']}. Directed typed two-/three-hop walks to truth {f['original_typed_twohop_walks_to_truth']}/{f['original_typed_threehop_walks_to_truth']} → {f['modified_typed_twohop_walks_to_truth']}/{f['modified_typed_threehop_walks_to_truth']}. These walk counts are answer-dependent diagnostics, not counts of rule groundings.",""]
        for w in case["witnesses"]:
            lines += [f"- {w['phase']}: `{w['expression']}` supports `{w['predicted_triple']}`; raw confidence {w['raw_confidence']}, support {w['raw_support']}. Witness `{w['grounding']}`; removed training edges `{w['missing_training_edges']}`; survives={w['survives']}."]
        lines += ["","A lost sampled witness does not imply all support disappeared: redundant witnesses or other rules may retain the candidate.",""]
    (output/f"{prefix}-cases.md").write_text("\n".join(lines)+"\n")
    return cases
