"""Controlled Phase-5 graphs: audit, bounded smoke, fresh paired runs, reporting."""
import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path
import gc
import json
import os
import resource
import signal
import time
import numpy as np
from ..data import load_dataset
from ..evaluation import evaluate
from ..backends.anyburl import mine, ATOM
from ..io import write_json, write_csv, digest, triple_digest, environment
from .runner import read, save_rows, load_rows
from .curves import load_curve
from .families import AuditedRules, describe
from .intervention_training import fit, atomic_json
from .resources import CoolingBreaks
from .structure_audit import audit, prepared_graphs, CONDITIONS


def native_vocabulary(graph):
    """Registry only: preserve original training-loader ID order, not its edges."""
    from c_clause import Loader
    from clause import Options
    options=Options();options.set("loader.verbose",False)
    loader=Loader(options=options.get("loader"));loader.load_data(list(graph.triples))
    entities=[x for x,i in sorted(loader.get_entity_index().items(),key=lambda item:item[1])]
    relations=[x for x,i in sorted(loader.get_relation_index().items(),key=lambda item:item[1])]
    if set(entities)!=set(graph.entities) or set(relations)!=set(graph.relations):
        raise ValueError("Original registry does not cover the benchmark vocabulary")
    return {"entities":entities,"relations":relations,"source_training_graph_sha256":triple_digest(graph.triples)}


def design(dataset, graphs, smoke=False, threads=1, seeds=(0,), rule_repetitions=1):
    if threads < 1 or rule_repetitions < 1 or not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("Positive threads/realizations and distinct neural seeds required")
    selected = read("runs/next-phase-neural/selection.json")["winner"]["path"]
    recipe = deepcopy(read(Path(selected)/"curve.json")["config"])
    recipe["threads"] = threads
    if smoke:
        recipe["budgets"] = [1]
    # Save a second checkpoint at an identical number of updates across graphs.
    common = min(int(np.ceil(2*len(g.triples)/recipe["batch_size"])) for g, _ in graphs.values()) * max(recipe["budgets"])
    recipe["diagnostic_common_updates"] = common
    return {"stage": "SMOKE ONLY" if smoke else "exploratory first 90%-retention paired comparison",
        "conditions": ["original", "targeted_local", "targeted_relation_matched_control"] if smoke else list(CONDITIONS),
        "neural_seeds": list(seeds), "mining_realizations": list(range(rule_repetitions)), "perturbation_seed": 11, "target_seed": 101,
        "embedding_recipe": recipe, "query_limit_facts": 16 if smoke else None,
        "mining_config": {"jar": "vendor/AnyBURL-23-1x.jar", "seconds": 2 if smoke else 60, "max_length": 3,
                          "threads": 1, "heap": "2G", "min_support": 2, "zero_rules": True},
        "rule_families": ["all", "general", "constants"], "secondary_frozen_families": [] if smoke else ["general"],
        "source_graph_sha256": {k: triple_digest(v[0].triples) for k, v in graphs.items()},
        "official_split_hashes": dataset.provenance["sha256"], "test_used_for_selection": False,
        "selection": "unchanged earlier validated recipe; same epoch ceiling/checkpoints/mining seconds across graphs; no intervention-result tuning",
        "compute_control": "capture fixed-update checkpoint as well as validation-best and last-epoch models; no extra training; different effective passes documented",
        "replication": ("first bounded one-neural-seed/one-mining-realization study; three neural seeds and independent mining repeats remain planned" if len(seeds)==1 and rule_repetitions==1 else f"declared {len(seeds)} paired neural seeds and {rule_repetitions} independent graph-specific mining realizations; one prepared removal/target draw"),
        "java_randomness": "not controlled by Python seed; graph differences confounded with learning realization in the primary rule comparison",
        "resource_policy": "serial jobs, configurable torch threads; Java ActiveProcessorCount=1; cooling before/after mining (never SIGSTOP during wall-clock mining)",
        "native_index_policy":"explicit original training-loader token order before loading modified positive edges; no removed or held-out edges inserted",
        "hypotheses": {
          "H1": {"intervention": "90% removal", "control": "fresh original graph", "measurement": "paired accuracy/gap/coverage and fixed-update sensitivity", "confounds": "fewer examples, gradient updates, validation selection, mining stochasticity"},
          "H2": {"intervention": "same frozen B catalog applied to missing-edge graphs", "control": "same catalog on original", "measurement": "candidate/gold-support losses, witnessed groundings lost", "confounds": "native frequency ties and binding constraints; raw typed walks are a structural proxy"},
          "H3": {"intervention": "fresh constant-rule learning/application on each graph", "control": "fresh original constant rules", "measurement": "constant versus general coverage/quality and sampled anchored witnesses", "confounds": "changed inventories/confidence, entity-local frequencies; full frozen-constant evaluation deferred"},
          "H4": {"intervention": "targeted_local", "control": "targeted_relation_matched_control", "measurement": "paired outcomes, difference in embedding-rule gap and paths", "confounds": "single target/removal draw; degree/entity distributions intentionally differ; independent miner samples"},
          "H5": {"intervention": "same removal conditions", "control": "same test facts/original-graph strata", "measurement": "original known-node degree/frequency strata and target incidence", "confounds": "observational effect heterogeneity, graph dependence, repeated CoDEx-S inspection"}},
        "later_replication": "CoDEx-M after protocol freeze; never launch automatically"}


def inventory(source, output):
    output = Path(output)
    if (output/"inventory.json").exists():
        record = read(output/"inventory.json")
        if record["source_sha256"] != digest(source):
            raise ValueError("Inventory source changed")
        return record
    output.mkdir(parents=True, exist_ok=True)
    groups = defaultdict(list)
    general, constants = [], []
    for line in Path(source).read_text().splitlines():
        if not line.strip():
            continue
        r = describe(line)
        groups[(r["native_family"], r["length"])].append((r["confidence"], r["support"]))
        if r["general_relational"]:
            general.append(line)
        if r["constant_bearing"] and not r["unconditional_prior"]:
            constants.append(line)
    families = {"all": {"path": str(source), "sha256": digest(source)}}
    for name, lines in (("general", general), ("constants", constants)):
        path=output/f"{name}.rules"
        path.write_text("".join(x+"\n" for x in lines))
        families[name]={"path": str(path), "sha256": digest(path), "n_rules": len(lines)}
    families["all"]["n_rules"] = sum(len(x) for x in groups.values())
    statistics=[]
    for (family,length), values in sorted(groups.items()):
        values=np.array(values)
        statistics.append({"native_family":family,"body_length":length,"n_rules":len(values),
            "confidence_quantiles":np.quantile(values[:,0],[0,.25,.5,.75,1]).tolist(),
            "support_quantiles":np.quantile(values[:,1],[0,.25,.5,.75,1]).tolist(),
            "mean_confidence":float(values[:,0].mean()),"mean_support":float(values[:,1].mean())})
    record={"source":str(source),"source_sha256":digest(source),"families":families,"statistics":statistics,
            "scope":"raw mining statistics; original lines/order and native smoothing/weights unchanged"}
    atomic_json(output/"inventory.json",record)
    write_csv(output/"rule-statistics.csv",statistics)
    return record


def apply_rules(dataset, source, output, limit=None, token_indices=None,retain_catalog_metadata=True,cache_size=256,progress_every=1000):
    output=Path(output)
    expected={"training_graph_sha256":triple_digest(dataset.graph.triples),"rule_file_sha256":digest(source),"limit":limit}
    if token_indices is not None:
        expected["native_token_order_sha256"]=triple_digest(tuple((str(i),"entity",e) for i,e in enumerate(token_indices["entities"]))+tuple((str(i),"relation",r) for i,r in enumerate(token_indices["relations"])))
    if (output/"metrics.json").exists():
        saved=read(output/"metrics.json")
        if saved["provenance"] != expected:
            raise ValueError("Completed rule application belongs to another graph/catalog")
        return saved
    output.mkdir(parents=True,exist_ok=True)
    atomic_json(output/"state.json",{"status":"running","provenance":expected})
    gate=CoolingBreaks()
    try:
        gate.thermal_rest()
        start,cpu=time.perf_counter(),time.process_time()
        def metadata_break():
            gate.thermal_rest()
            gate.rest()
        backend=AuditedRules(dataset.graph,source,certify_support=True,metadata_callback=metadata_break,token_indices=token_indices,retain_catalog_metadata=retain_catalog_metadata)
        gate.thermal_rest()
        # N+1 cannot be reached by a candidate count bounded by N. Check several
        # actual masked inputs against 2N+1 without constructing a second loader.
        from c_clause import QAHandler
        from clause import Options
        from ..evaluation import ModelQuery
        opts=Options()
        for key,value in backend.effective_qa_options.items():
            opts.set("qa_handler."+key,value)
        opts.set("qa_handler.topk",2*len(dataset.graph.entities)+1)
        wider=QAHandler(options=opts.get("qa_handler"))
        checked=True
        for h,r,t in dataset.valid[:2]:
            for q in (ModelQuery(h,r,"tail"),ModelQuery(t,r,"head")):
                if q.known not in backend.seen_entities or q.relation not in backend.seen_relations:
                    continue
                wider.calculate_answers(queries=[(q.known,q.relation)],loader=backend.loader,direction=q.direction)
                other=[(str(e),float(s)) for e,s in wider.get_answers(as_string=True)[0]]
                checked &= backend.predict(q).candidates==other
        if not checked:
            backend.certify_support=False
        rows,metrics=evaluate(backend,dataset.test,dataset.graph.entities,dataset.positives_for_filter("test"),limit=limit,cache_size=cache_size,progress_every=progress_every)
        save_rows(output/"queries.json.gz.tmp",rows)
        os.replace(output/"queries.json.gz.tmp",output/"queries.json.gz")
        metrics.update({"provenance":expected,"correct_answer_generation_coverage":float(np.mean([r["true_returned"] for r in rows])),
            "native_loaded_count":backend.native_loaded_count,"catalog_rule_count":len(backend.rules),
            "n_unrepresentable_queries":sum(r["backend_metadata"].get("query_representable",True) is False for r in rows),
            "certified_query_fraction":float(np.mean([r["hits_certified"] for r in rows])),
            "larger_limit_contract_equal":bool(checked),"application_seconds_including_loading_and_cooling":time.perf_counter()-start,
            "application_cpu_seconds":time.process_time()-cpu,"resource_policy":backend.cooling.record(),
            "effective_qa_options":backend.effective_qa_options,"effective_loader_options":backend.effective_loader_options,
            "catalog_metadata_retained":backend.retain_catalog_metadata,
            "metrics_policy":"certified supported-candidate ranking where possible; unsupported=abstention/miss; never full-universe rule MRR"})
        atomic_json(output/"metrics.json",metrics)
        atomic_json(output/"state.json",{"status":"complete","provenance":expected})
        del backend,wider,rows
        gc.collect()
        return metrics
    except BaseException as e:
        atomic_json(output/"state.json",{"status":"interrupted" if isinstance(e,KeyboardInterrupt) else "failed","provenance":expected,"error":repr(e)})
        raise


def evaluate_embedding(model,dataset,output,limit=None,provenance=None):
    output=Path(output)
    if (output/"metrics.json").exists():
        saved=read(output/"metrics.json")
        if saved.get("provenance") is not None and saved["provenance"]!=provenance:
            raise ValueError("Completed embedding evaluation has different checkpoint provenance")
        return saved
    output.mkdir(parents=True,exist_ok=True)
    rows,metrics=evaluate(model,dataset.test,dataset.graph.entities,dataset.positives_for_filter("test"),limit=limit,cache_size=256)
    metrics["provenance"]=provenance
    save_rows(output/"queries.json.gz.tmp",rows)
    os.replace(output/"queries.json.gz.tmp",output/"queries.json.gz")
    atomic_json(output/"metrics.json",metrics)
    return metrics


def frozen_evidence(dataset,prepared,output,conditions=None,families=None):
    """Run the predeclared lightweight inference-only component independently.

    This never changes or completes the primary fresh-training cell manifests.
    """
    output=Path(output);protocol=read(output/"protocol.json")
    from .structure_extensions import declare_frozen_extension,frozen_families,frozen_source
    if families:declare_frozen_extension(output,families)
    selected_families=families or frozen_families(output,protocol)
    graphs=prepared_graphs(dataset,prepared)
    indices=native_vocabulary(dataset.graph)
    trained=read("runs/next-phase-frozen/mining/training.json")
    if trained["training_graph_sha256"]!=triple_digest(dataset.graph.triples):
        raise ValueError("Established frozen inventory came from another graph")
    for condition in conditions or protocol["conditions"]:
        if condition not in protocol["conditions"]:raise ValueError("Condition outside frozen design")
        for family in selected_families:
            source=frozen_source(output,protocol,family)
            apply_rules(dataset.with_graph(graphs[condition][0]),source["path"],output/condition/"frozen"/family,protocol["query_limit_facts"],indices)
    all_families=frozen_families(output,protocol)
    status_file="frozen-family-extension-execution.json" if (output/"frozen-family-extension.json").exists() else "frozen-execution.json"
    atomic_json(output/status_file,{"status":"complete" if all((output/c/"frozen"/f/"metrics.json").exists() for c in protocol["conditions"] for f in all_families) else "partial",
        "families":all_families,
        "scope":"inference-time evidence intervention, not fresh model training","primary_results_substituted":False})


def run(dataset,prepared,output,smoke=False,conditions=None,threads=1,seeds=(0,),rule_repetitions=1,
        *, graph_pair=None, lightweight_rules=False):
    output=Path(output)
    if (output/"resource-stop.json").exists():
        raise RuntimeError("This cohort was resource-stopped. Review resource-stop.json before explicitly planning further full-budget work; use a separate directory for a smaller smoke cohort.")
    output.mkdir(parents=True,exist_ok=True)
    graphs=prepared_graphs(dataset,prepared) if graph_pair is None else graph_pair
    indices=native_vocabulary(dataset.graph)
    atomic_json(output/"native-vocabulary.json",indices)
    protocol=design(dataset,graphs,smoke,threads,seeds,rule_repetitions)
    if graph_pair is not None:
        local_pair = {"targeted_local", "targeted_relation_matched_control"}
        evidence_pair = {"evidence_targeted", "evidence_matched"}
        if set(graph_pair) not in (local_pair, evidence_pair):
            raise ValueError("The replicated design requires exactly one targeted graph and its matched control")
        is_evidence = set(graph_pair) == evidence_pair
        intervention_metadata = graphs["evidence_targeted" if is_evidence else "targeted_local"][1]
        protocol.update(
            stage="SMOKE ONLY" if smoke else ("exploratory matched rule-body removal" if is_evidence
                                               else "exploratory replicated matched removal"),
            conditions=list(graph_pair),
            perturbation_seed=intervention_metadata["seed"],
            target_seed=intervention_metadata["target_seed"],
            secondary_frozen_families=[],
        )
        if is_evidence:
            protocol["hypotheses"] = {
                "evidence_loss": "training-selected rule-body edge removal reduces frozen general grounding availability",
                "ranking": "paired change in ComplEx minus AnyBURL Hits@1 relative to the matched graph",
            }
    if lightweight_rules:
        protocol["native_application_storage"] = "metadata-light; full masked-query cache"
    if (output/"protocol.json").exists() and read(output/"protocol.json")!=protocol:
        raise ValueError("Cannot change a started experiment's design")
    atomic_json(output/"protocol.json",protocol)
    chosen=conditions or protocol["conditions"]
    if not set(chosen)<=set(protocol["conditions"]):
        raise ValueError("Conditions outside the predeclared design")
    for name in chosen:
        graph,meta=graphs[name]
        modified=dataset.with_graph(graph)
        for seed in protocol["neural_seeds"]:
            cell=output/name/f"neural-{seed}"
            previous=cell/"manifest.json"
            if previous.exists() and read(previous)["status"] in ("interrupted","failed"):
                atomic_json(cell/"attempts"/f"manifest-{time.time_ns()}.json",read(previous))
            status={"status":"running","condition":name,"neural_seed":seed,"training_graph_sha256":triple_digest(graph.triples),
                    "original_positive_filters_fixed":True,"source":"fresh fitting on this graph; no pretrained model substitution"}
            atomic_json(cell/"manifest.json",status)
            try:
                model_path=cell/"embedding"
                if (model_path/"curve.json").exists() and read(model_path/"curve.json").get("status")=="complete":
                    completed=read(model_path/"curve.json")
                    if digest(model_path/"best.pt")!=completed["checkpoint_sha256"]:
                        raise ValueError("Completed neural checkpoint hash mismatch")
                    model,record=load_curve(graph,model_path)
                else:
                    model,record=fit(modified,{**protocol["embedding_recipe"],"seed":seed},model_path)
                evaluate_embedding(model,modified,cell/"validation-best",protocol["query_limit_facts"],
                    {"training_graph_sha256":triple_digest(graph.triples),"checkpoint_sha256":record["checkpoint_sha256"],"policy":"validation-best"})
                for policy,filename in (("fixed-updates","matched-updates.pt"),("last-epoch","last.pt")):
                    checkpoint=model_path/filename
                    if checkpoint.exists() and not (cell/policy/"metrics.json").exists():
                        info=record.get("policy_checkpoints",{}).get(filename)
                        if info and (info["sha256"]!=digest(checkpoint) or info["training_graph_sha256"]!=triple_digest(graph.triples)):
                            raise ValueError("Diagnostic checkpoint provenance mismatch")
                        model.model.load_state_dict(model.torch.load(checkpoint,map_location=model.model.device,weights_only=True))
                        model.model.eval()
                        evaluate_embedding(model,modified,cell/policy,protocol["query_limit_facts"],
                            {"training_graph_sha256":triple_digest(graph.triples),"checkpoint_sha256":digest(checkpoint),"policy":policy})
                status.update({"status":"complete","training":record})
                atomic_json(cell/"manifest.json",status)
                del model
                gc.collect()
            except BaseException as e:
                status.update({"status":"interrupted" if isinstance(e,KeyboardInterrupt) else "failed","error":repr(e)})
                atomic_json(cell/"manifest.json",status)
                raise
        for realization in protocol["mining_realizations"]:
            cell=output/name/f"rules-{realization}"
            previous=cell/"manifest.json"
            if previous.exists() and read(previous)["status"] in ("interrupted","failed"):
                atomic_json(cell/"attempts"/f"manifest-{time.time_ns()}.json",read(previous))
            status={"status":"running","condition":name,"realization_id":realization,"java_seed_controlled":False,
                    "training_graph_sha256":triple_digest(graph.triples),"source":"fresh Java mining on this graph; no pretrained inventory substitution"}
            atomic_json(cell/"manifest.json",status)
            try:
                mining=cell/"mining"
                if (mining/"training.json").exists():
                    trained=read(mining/"training.json")
                    if trained["training_graph_sha256"]!=triple_digest(graph.triples) or trained["config"]!=protocol["mining_config"]:
                        raise ValueError("Mining graph/config mismatch")
                else:
                    if mining.exists():
                        archive=cell/"interrupted"/f"mining-{time.time_ns()}"
                        archive.parent.mkdir(parents=True,exist_ok=True)
                        mining.rename(archive)
                    gate=CoolingBreaks();gate.thermal_rest()
                    before=resource.getrusage(resource.RUSAGE_CHILDREN)
                    source,trained=mine(graph,protocol["mining_config"],mining)
                    after=resource.getrusage(resource.RUSAGE_CHILDREN)
                    trained["child_cpu_seconds"]=(after.ru_utime+after.ru_stime)-(before.ru_utime+before.ru_stime)
                    trained["java_tool_options"]=os.environ.get("JAVA_TOOL_OPTIONS","")
                    atomic_json(mining/"training.json",trained)
                    gate.thermal_rest()
                catalog=inventory(trained["rules_file"],cell/"catalog")
                for family in protocol["rule_families"]:
                    options = {"retain_catalog_metadata": False, "cache_size": 2 * len(dataset.test)} if lightweight_rules else {}
                    apply_rules(modified,catalog["families"][family]["path"],cell/family,protocol["query_limit_facts"],indices,**options)
                status.update({"status":"complete","training":trained})
                atomic_json(cell/"manifest.json",status)
            except BaseException as e:
                status.update({"status":"interrupted" if isinstance(e,KeyboardInterrupt) else "failed","error":repr(e)})
                atomic_json(cell/"manifest.json",status)
                raise
        for family in protocol["secondary_frozen_families"]:
            old=read("runs/next-phase-frozen/subsets/subsets.json")["subsets"][family]
            if digest(old["path"])!=old["sha256"]:
                raise ValueError("Original frozen rule subset changed")
            apply_rules(modified,old["path"],output/name/"frozen"/family,protocol["query_limit_facts"],indices)
    manifests=list(output.glob("*/neural-*/manifest.json"))+list(output.glob("*/rules-*/manifest.json"))
    atomic_json(output/"execution.json",{"status":"complete" if len(manifests)==len(protocol["conditions"])*(len(protocol["neural_seeds"])+len(protocol["mining_realizations"])) and all(read(p)["status"]=="complete" for p in manifests) else "partial",
        "smoke":smoke,"completed_or_attempted_cells":[{"path":str(p.parent),"status":read(p)["status"]} for p in manifests],
        "protocol_sha256":digest(output/"protocol.json"),"environment":environment()})


def main():
    # Terminal/service termination must leave an interrupted manifest, rather
    # than stale "running" metadata or a partial completed baseline.
    def terminated(signum, frame):
        raise KeyboardInterrupt(f"Experiment received signal {signum}")
    signal.signal(signal.SIGTERM,terminated)
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("command",choices=("audit","smoke","run","frozen","report","cases","frozen-cases"))
    p.add_argument("--data",default="data/codex-s")
    p.add_argument("--prepared",default="runs/next-phase-sparsity-prepared")
    p.add_argument("--output",default="runs/phase5-90")
    p.add_argument("--conditions",nargs="+")
    p.add_argument("--threads",type=int,default=1)
    p.add_argument("--seeds",nargs="+",type=int,default=[0])
    p.add_argument("--rule-repetitions",type=int,default=1)
    p.add_argument("--families",nargs="+",choices=("general","constants"),help="Explicit separately recorded frozen-family extension")
    p.add_argument("--family",default="general",choices=("general","constants"),help="Frozen witness family")
    p.add_argument("--report-output",help="Separate report destination; preserves earlier cohort reports")
    args=p.parse_args()
    dataset=load_dataset(args.data)
    if args.command=="audit":
        audit(dataset,args.prepared,args.output)
    elif args.command in ("smoke","run"):
        run(dataset,args.prepared,args.output,args.command=="smoke",args.conditions,args.threads,args.seeds,args.rule_repetitions)
    elif args.command=="frozen":
        frozen_evidence(dataset,args.prepared,args.output,args.conditions,args.families)
    elif args.command=="report":
        from .structure_report import build
        build(dataset,args.prepared,args.output,output=args.report_output)
    elif args.command=="cases":
        from .structure_cases import build
        build(dataset,args.prepared,args.output,output=args.report_output)
    elif args.command=="frozen-cases":
        from .structure_frozen_cases import build
        build(dataset,args.prepared,args.output,output=args.report_output or "artifacts/phase5/report",family=args.family)


if __name__=="__main__":
    main()
