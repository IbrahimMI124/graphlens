"""Check saved benchmark evidence and index the inputs for the course report."""
from pathlib import Path
from xml.etree import ElementTree
from collections import Counter
import csv

from kgc.backends.anyburl import parse_rule
from kgc.data import load_dataset
from kgc.io import digest, triple_digest, write_csv, write_json
from kgc.research.evidence_intervention import strata
from kgc.research.last_proof import samples
from kgc.research.runner import read


BASE = Path("artifacts")


def csv_rows(path):
    with path.open() as stream:
        return list(csv.DictReader(stream))


def verify_last_proof():
    root = BASE / "closeout/last-proof"
    manifest = read(root / "status.json")
    protocol = read(root / "protocol.json")
    graph = load_dataset("data/codex-s").graph
    rules = (root / "two-hop.rules").read_text().splitlines()
    if (manifest["status"] != "complete" or manifest["protocol_sha256"] != digest(root / "protocol.json")
            or protocol["graph_sha256"] != triple_digest(graph.triples)
            or protocol["two_hop_sha256"] != digest(root / "two-hop.rules")
            or len(rules) != protocol["n_rules"] or any(parse_rule(rule).length != 2 for rule in rules)):
        raise ValueError("Last-proof feasibility manifest failed verification")
    membership = {i: key for key, indices in strata(graph).items() for i in indices}
    summary = []
    for entry, (fit, audit) in zip(manifest["draws"], samples(len(graph.triples)), strict=True):
        folder = root / f"draw-{entry['draw']}"
        plan = read(folder / "plan.json")
        rows = csv_rows(folder / "audit.csv")
        indices = [int(r["train_index"]) for r in rows]
        if (digest(folder / "plan.json") != entry["plan_sha256"]
                or digest(folder / "audit.csv") != entry["audit_sha256"]
                or plan["fit_ids"] != fit or plan["audit_ids"] != audit
                or len(indices) != len(set(indices)) or not set(indices) <= set(audit)
                or any(not 1 <= int(r["original_two_hop_proofs"]) <= protocol["max_proofs"] for r in rows)):
            raise ValueError("Last-proof probe provenance failed verification")
        quota = Counter({(r, h, t): count for r, h, t, count in plan["quota"]})
        counts, backups = {}, {}
        for arm in ("targeted", "matched"):
            removed = plan[f"removed_{arm}"]
            if (len(removed) != entry["n_removed"] or len(set(removed)) != len(removed)
                    or len(removed) > protocol["max_removals"]
                    or Counter(membership[i] for i in removed) != quota):
                raise ValueError("Last-proof masks are incompatible with the matched quotas")
            exhausted = []
            for row in rows:
                before, lost = int(row["original_two_hop_proofs"]), int(row[f"{arm}_proofs_lost"])
                if not 0 <= lost <= before or int(row[f"{arm}_all_lost"]) != (lost == before):
                    raise ValueError("Loss indicators disagree with proof counts")
                if lost == before:
                    exhausted.append(row)
            counts[arm] = len(exhausted)
            for family in ("general", "constants"):
                if any(row[f"{arm}_remaining_{family}"] not in ("0", "1") for row in exhausted):
                    raise ValueError("Missing alternative proof diagnostic")
                backups[f"{arm}_{family}_remaining"] = sum(int(row[f"{arm}_remaining_{family}"]) for row in exhausted)
        n = len(rows)
        difference = (counts["targeted"] - counts["matched"]) / n if n else None
        passed = n >= protocol["min_eligible_audit"] and difference >= protocol["min_difference"]
        if (n != entry["n_eligible_audit"] or difference != entry["difference"] or passed != entry["passed"]
                or any(entry[f"{arm}_all_lost"] != count for arm, count in counts.items())):
            raise ValueError("Last-proof audit totals differ from the saved gate calculation")
        summary.append(dict(draw=entry["draw"], n_eligible_audit=n, n_removed=entry["n_removed"],
                            targeted_all_lost=counts["targeted"], matched_all_lost=counts["matched"],
                            difference=difference, passed=passed, **backups))
    if manifest["gate_passed"] != all(row["passed"] for row in summary):
        raise ValueError("Last-proof gate decision differs from the three verified draws")
    write_csv(root / "verified-summary.csv", summary)
    return dict(status=str(root / "status.json"), gate_passed=manifest["gate_passed"],
                summary=str(root / "verified-summary.csv"))


def verify_length_replication():
    closeout = BASE / "closeout"
    jobs = read(closeout / "cloud-jobs.json")["length_catalogs"]
    results = []
    for job in jobs:
        root = closeout / f"length-{job['catalog']}"
        status_path = root / "status.json"
        metrics_path, effects_path = root / "metrics.csv", root / "paired-length-3-minus-1.csv"
        manifest = read(status_path)
        source_hash = manifest["source_sha256"]
        metrics, effects = csv_rows(metrics_path), csv_rows(effects_path)
        expected = {(mode, str(length)) for mode in ("general", "fixed_constants") for length in (1, 2, 3)}
        registered = {(r["mode"], r["max_general_length"]): r for r in metrics}
        if (manifest["status"] != "complete" or manifest["limit_facts"] is not None
                or manifest["metrics_sha256"] != digest(metrics_path) or manifest["effects_sha256"] != digest(effects_path)
                or len(metrics) != 6 or set(registered) != expected
                or any(row["n_queries"] != "3656" or row["source_sha256"] != source_hash for row in metrics)
                or len(effects) != 2 or {r["mode"] for r in effects} != {"general", "fixed_constants"}):
            raise ValueError("Rule-length replication is incomplete or failed provenance checks")
        counts = {int(registered["fixed_constants", str(k)]["n_rules"]) - int(registered["general", str(k)]["n_rules"])
                  for k in (1, 2, 3)}
        if len(counts) != 1:
            raise ValueError("Fixed constant inventory counts differ across length caps")
        for row in effects:
            mode = row["mode"]
            delta = float(registered[mode, "3"]["hits1"]) - float(registered[mode, "1"]["hits1"])
            if abs(delta - float(row["difference"])) > 1e-12 or row["source_sha256"] != source_hash:
                raise ValueError("Saved paired length contrast does not match its arm scores")
        results.append(dict(job_id=job["id"], catalog=job["catalog"], source_sha256=source_hash,
                            metrics=str(metrics_path), paired_effects=str(effects_path)))
    if len(results) != 2 or len({r["source_sha256"] for r in results}) != 2:
        raise ValueError("Expected two independently mined catalogs")
    return results


def verify():
    phase = BASE / "phase5/replicated-report"
    report_path = phase / "report-status.json"
    status = read(report_path)
    execution = read(phase / "provenance/work-execution.json")
    if (execution["status"] != "complete" or execution["final_report_check"]["sha256"] != digest(report_path)
            or status["smoke"] or not status["all_primary_cells_complete"]
            or not status["all_declared_frozen_cells_complete"]
            or len(status["cells"]) != 25 or len(status["frozen_family_cells"]) != 10):
        raise ValueError("Five-graph cohort failed verification")
    replication = BASE / "removal-replication"
    draws = []
    for entry in read(replication / "hf-submission.json")["draws"]:
        root = replication / f"draw-{entry['draw']}-{entry['id']}"
        path = root / "replication-status.json"
        manifest = read(path)
        metrics = csv_rows(root / "overall.csv")
        if (manifest["status"] != "complete" or not manifest["certified_hits"] or manifest["smoke"]
                or manifest["protocol_sha256"] != digest(root / "replication-protocol.json")
                or manifest["outcomes_sha256"] != digest(root / "outcomes.npz")
                or len(metrics) != 30 or {r["n_queries"] for r in metrics} != {"3656"}):
            raise ValueError(f"Independent graph draw failed verification: {root}")
        draws.append(dict(root=str(root), status_sha256=digest(path)))
    if len(draws) != 3:
        raise ValueError("Expected three independent graph draws")
    baseline = BASE / "next-phase"
    family_metrics = baseline / "rule-family-metrics.csv"
    families = [r for r in csv_rows(family_metrics) if r["condition"] in ("all", "constants", "general")]
    if len(families) != 3 or not all(
            row["n_queries"] == "3656" and row["hits_metric_status"].startswith("certified ") and not row["mrr_exact"]
            for row in families):
        raise ValueError("Frozen baseline ranking certification failed verification")
    for version in (1, 2):
        folder = BASE / f"evidence-intervention/v{version}-prepared"
        audit = read(folder / "preparation-status.json")
        if audit["status"] != "complete" or len(audit["draws"]) != 3:
            raise ValueError("Previous evidence audit is incomplete")
        for i, draw in enumerate(audit["draws"], 1):
            if draw["audit"]["passed"] or draw["plan_sha256"] != digest(folder / f"draw-{i}/plan.json"):
                raise ValueError("Saved audit result differs from its original plan")
    for size in ("s", "m"):
        folder = Path(f"data/codex-{size}")
        source = read(folder / "source.json")
        if any(digest(folder / f"{name}.txt") != expected for name, expected in source["sha256"].items()):
            raise ValueError(f"CoDEx-{size.upper()} checksum mismatch")
    tests = BASE / "closeout/tests.xml"
    counts = ElementTree.parse(tests).find("testsuite").attrib
    if any(int(counts[k]) for k in ("errors", "failures", "skipped")):
        raise ValueError("The saved full suite has failures or skips")
    noise_path = BASE / "closeout/noise-design-audit.csv"
    noise = csv_rows(noise_path)
    if len(noise) != 18 or any(r["training"] != "not launched" for r in noise):
        raise ValueError("Missing the configured noise proposal audit")
    n_rejected = sum(row["split_audit"] == "fail" for row in noise)
    return {
        "tests": {"artifact": str(tests), "sha256": digest(tests), "total_incl_subtests": int(counts["tests"])},
        "CoDEx-M": {"official_files_validated": True, "model_replication": False,
                     "validation": str(BASE / "closeout-codex-m-validation.json")},
        "CoDEx-S": {
            "baseline": {"reference": str(baseline / "report.md"), "test_facts": 1828, "directional_queries": 3656},
            "rule_family_and_length_ablation": {
                "reference": str(family_metrics), "certified_hits": True, "exact_rule_mrr": False
            },
            "independent_rule_length_replications": verify_length_replication(),
            "verified_negatives": {"reference": str(baseline / "classification-metrics.csv"), "task": "classification"},
            "complementarity": {"reference": str(baseline / "neural-rule-comparison.json")},
            "relation_diagnostics": {
                "reference": str(baseline / "training-relation-properties.csv"), "interpretation": "descriptive"
            },
            "primary_retraining": {"reference": str(report_path), "primary_cells": 25, "frozen_cells": 10,
                                   "sha256": digest(report_path)},
            "independent_graph_draws": draws,
            "direct_rule_body_pilots": {"reference": str(BASE / "evidence-intervention/report.md"),
                                        "completed_draws": 6, "passed_gate": 0},
            "last_proof_feasibility": verify_last_proof(),
        },
        "scope": {"larger_retention_sweeps": "outside the completed cohort",
                  "noise_proposals": {"audit": str(noise_path), "proposals": len(noise),
                                      "rejected_for_split_overlap": n_rejected, "retraining": "not executed"},
                  "medium_benchmark_replication": "outside the completed cohort",
                  "final_course_report": "awaiting writing request"},
    }


if __name__ == "__main__":
    write_json(BASE / "closeout/verified-evidence.json", verify())
    print("Verified the saved CoDEx-S benchmark cohorts, audits, full test suite and both dataset checksums.")
