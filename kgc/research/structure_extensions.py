"""Prospective frozen-family extensions without changing an existing protocol."""
from pathlib import Path
from .runner import read
from .intervention_training import atomic_json
from ..io import digest

FROZEN_FAMILIES=("general","constants")


def declare_frozen_extension(root,families,source_catalogs=None):
    root=Path(root);protocol=read(root/"protocol.json")
    if not families or not set(families)<=set(FROZEN_FAMILIES):
        raise ValueError("Frozen extension supports general or constant-bearing conditional rules")
    additions=[f for f in FROZEN_FAMILIES if f in families and f not in protocol["secondary_frozen_families"]]
    if not additions:
        return None
    if source_catalogs is None:
        source_catalogs=read("runs/next-phase-frozen/subsets/subsets.json")["subsets"]
        mining=read("runs/next-phase-frozen/mining/training.json")
        if mining["training_graph_sha256"]!=protocol["source_graph_sha256"]["original"]:
            raise ValueError("Frozen catalog was not learned on the declared original training graph")
    sources={}
    for family in additions:
        item=source_catalogs[family]
        if digest(item["path"])!=item["sha256"]:
            raise ValueError("Frozen source checksum mismatch")
        sources[family]={k:item[k] for k in ("path","sha256","n_rules")}
    record={"schema_version":1,"base_protocol_sha256":digest(root/"protocol.json"),
        "families":additions,"conditions":protocol["conditions"],
        "source_graph_sha256":protocol["source_graph_sha256"],"query_limit_facts":protocol["query_limit_facts"],
        "native_vocabulary_sha256":digest(root/"native-vocabulary.json"),"source_catalogs":sources,
        "scope":"additional inference-time evidence intervention; no retraining or new independent catalog replicate",
        "semantics":"unchanged original expressions, confidences, support, smoothing, family weights, maxplus, frequency ties and candidate universe; constants exclude zero-body priors"}
    path=root/"frozen-family-extension.json"
    if path.exists():
        if read(path)!=record:
            raise ValueError("Cannot change a declared frozen-family extension")
    else:
        atomic_json(path,record)
    return record


def frozen_families(root,protocol):
    root=Path(root);families=list(protocol["secondary_frozen_families"])
    path=root/"frozen-family-extension.json"
    if not path.exists():return families
    record=read(path)
    if record["schema_version"]!=1 or record["base_protocol_sha256"]!=digest(root/"protocol.json"):
        raise ValueError("Frozen extension refers to another protocol")
    for key in ("conditions","source_graph_sha256","query_limit_facts"):
        if record[key]!=protocol[key]:raise ValueError("Frozen extension graph/query contract mismatch")
    if record["native_vocabulary_sha256"]!=digest(root/"native-vocabulary.json"):
        raise ValueError("Frozen extension vocabulary changed")
    if not record["families"] or not set(record["families"])<=set(FROZEN_FAMILIES):
        raise ValueError("Unsupported frozen extension family")
    if set(record["source_catalogs"])!=set(record["families"]):
        raise ValueError("Frozen extension source catalog mismatch")
    for family in record["families"]:
        source=record["source_catalogs"][family]
        if digest(source["path"])!=source["sha256"]:
            raise ValueError("Frozen extension source changed")
        if family not in families:families.append(family)
    return families


def frozen_source(root,protocol,family):
    root=Path(root)
    if family not in frozen_families(root,protocol):
        raise ValueError("Frozen family has not been declared")
    if family in protocol["secondary_frozen_families"]:
        source=read("runs/next-phase-frozen/subsets/subsets.json")["subsets"][family]
    else:
        source=read(root/"frozen-family-extension.json")["source_catalogs"][family]
    if digest(source["path"])!=source["sha256"]:
        raise ValueError("Frozen source changed")
    return source
