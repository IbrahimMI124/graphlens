"""Inference-only continuation; never starts neural fitting or Java mining.

This worker can be duty-cycled without altering a wall-clock learning budget.
Prefix smoke outputs are separate and cannot complete a primary experiment cell.
"""
import argparse
from pathlib import Path
import signal
import time
from ..data import load_dataset
from ..io import digest,triple_digest
from .runner import read
from .intervention_training import atomic_json
from .structure import apply_rules,inventory
from .structure_audit import CONDITIONS,prepared_graphs
from .structure_extensions import frozen_families,frozen_source


def resolve_file(recorded,local,expected_hash):
    """Relocated bytes must match recorded provenance; never rewrite the record."""
    for path in dict.fromkeys((Path(recorded),Path(local))):
        if path.exists() and digest(path)==expected_hash:return path
    raise ValueError("No content-verified inference artifact at the recorded or relocated path")


def run(root,kind,conditions,families,limit_facts=None,report_output=None):
    root=Path(root);protocol=read(root/"protocol.json")
    if kind not in ("fresh","frozen","frozen-cases") or not conditions or not families:
        raise ValueError("Explicit inference-only scope required")
    if len(set(conditions))!=len(conditions) or not set(conditions)<=set(protocol["conditions"]):
        raise ValueError("Inference conditions differ from the declared design")
    allowed=set(protocol["rule_families"]) if kind=="fresh" else set(frozen_families(root,protocol))
    if len(set(families))!=len(families) or not set(families)<=allowed:
        raise ValueError("Inference family was not declared")
    if limit_facts is not None and limit_facts<1:raise ValueError("Positive prefix limit required")
    if kind=="frozen-cases" and (limit_facts is not None or set(conditions)!=set(protocol["conditions"])):
        raise ValueError("Frozen witness cases require all declared conditions and no prefix limit")
    if report_output is not None and kind!="frozen-cases":
        raise ValueError("A report destination applies only to witness-case inference")
    data=load_dataset("data/codex-s");graphs=prepared_graphs(data,"runs/next-phase-sparsity-prepared")
    indices=read(root/"native-vocabulary.json")
    if indices["source_training_graph_sha256"]!=triple_digest(data.graph.triples):
        raise ValueError("Native vocabulary comes from another original training graph")
    tag="-".join((kind,*conditions,*families,"full" if limit_facts is None else f"prefix-{limit_facts}"))
    state_path=root/"inference-tasks"/(tag+".json")
    state={"status":"running","scope":"inference only; no training or mining","kind":kind,
        "conditions":conditions,"families":families,"limit_facts":limit_facts,
        "protocol_sha256":digest(root/"protocol.json"),"completed_applications":[]}
    atomic_json(state_path,state)
    try:
        if kind=="frozen-cases":
            from .structure_frozen_cases import build
            destination=Path(report_output or "artifacts/phase5/remaining-report")
            for family in families:
                build(data,"runs/next-phase-sparsity-prepared",root,output=destination,family=family)
                prefix="frozen" if family=="general" else "frozen-constants"
                state["completed_applications"].append(str(destination/(prefix+"-cases.md")));atomic_json(state_path,state)
            state["status"]="complete";atomic_json(state_path,state)
            return state
        for condition in conditions:
            graph=graphs[condition][0];modified=data.with_graph(graph)
            if kind=="fresh":
                for realization in protocol["mining_realizations"]:
                    cell=root/condition/f"rules-{realization}"
                    training=read(cell/"mining/training.json")
                    if training["training_graph_sha256"]!=triple_digest(graph.triples) or training["config"]!=protocol["mining_config"]:
                        raise ValueError("Cannot infer from another graph or mining configuration")
                    source=resolve_file(training["rules_file"],cell/"mining"/Path(training["rules_file"]).name,training["rule_file_sha256"])
                    catalog=inventory(source,cell/"catalog")
                    for family in families:
                        item=catalog["families"][family]
                        fallback=source if family=="all" else cell/"catalog"/(family+".rules")
                        path=resolve_file(item["path"],fallback,item["sha256"])
                        destination=cell/family if limit_facts is None else root/"inference-smoke"/kind/condition/f"rules-{realization}"/family
                        apply_rules(modified,path,destination,limit_facts,indices,retain_catalog_metadata=False,cache_size=2*len(data.test),progress_every=100)
                        state["completed_applications"].append(str(destination));atomic_json(state_path,state)
                    complete=limit_facts is None and set(protocol["rule_families"])<=set(families) and all((cell/f/"metrics.json").exists() and read(cell/f/"metrics.json")["n_queries"]==2*len(data.test) for f in protocol["rule_families"])
                    if complete:
                        previous=cell/"manifest.json"
                        if previous.exists():atomic_json(cell/"attempts"/f"before-inference-continuation-{time.time_ns()}.json",read(previous))
                        atomic_json(previous,{"status":"complete","condition":condition,"realization_id":realization,
                            "java_seed_controlled":False,"training_graph_sha256":triple_digest(graph.triples),"training":training,
                            "source":"fresh AnyBURL mining on this graph; completed application through inference-only continuation; no retraining or pretrained substitution"})
            else:
                for family in families:
                    source=frozen_source(root,protocol,family)
                    destination=root/condition/"frozen"/family if limit_facts is None else root/"inference-smoke"/kind/condition/family
                    apply_rules(modified,source["path"],destination,limit_facts,indices,retain_catalog_metadata=False,cache_size=2*len(data.test),progress_every=100)
                    state["completed_applications"].append(str(destination));atomic_json(state_path,state)
        state["status"]="complete";atomic_json(state_path,state)
        return state
    except BaseException as error:
        state.update(status="interrupted" if isinstance(error,KeyboardInterrupt) else "failed",error=repr(error))
        atomic_json(state_path,state);raise


def main():
    def terminated(signum,frame):raise KeyboardInterrupt(f"Inference worker received signal {signum}")
    signal.signal(signal.SIGTERM,terminated)
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",required=True)
    parser.add_argument("--kind",required=True,choices=("fresh","frozen","frozen-cases"))
    parser.add_argument("--conditions",required=True,nargs="+",choices=CONDITIONS)
    parser.add_argument("--families",required=True,nargs="+",choices=("all","general","constants"))
    parser.add_argument("--limit-facts",type=int)
    parser.add_argument("--report-output")
    args=parser.parse_args();run(args.root,args.kind,args.conditions,args.families,args.limit_facts,args.report_output)


if __name__=="__main__":main()
