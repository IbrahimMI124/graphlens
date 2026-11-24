"""The validated ComplEx recipe with atomic epoch snapshots for interventions.

Fresh model/optimizer per graph and seed. Resume restores optimizer, scheduler,
best state, shuffle/dropout RNG streams and the last committed full epoch.
"""
from copy import deepcopy
from pathlib import Path
import json
import os
import random
import time
import numpy as np
from ..io import write_json, digest, triple_digest, environment
from ..evaluation import evaluate
from .curves import CurveModel
from .resources import CoolingBreaks


def atomic_json(path, value):
    path = Path(path)
    temp = path.with_suffix(path.suffix + ".tmp")
    write_json(temp, value)
    os.replace(temp, path)


def fit(dataset, config, output, stop_after_epoch=None):
    """stop_after_epoch is a synthetic interruption hook, never a model selector."""
    if config["objective"] != "1vsAll":
        raise ValueError("Interventions require the selected per-triple 1vsAll recipe")
    if config.get("device", "cpu") != "cpu":
        raise ValueError("This interruption-safe intervention trainer currently supports CPU RNG restoration")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    graph_hash = triple_digest(dataset.graph.triples)
    backend = CurveModel(dataset.graph, config)
    torch = backend.torch
    optimizer = torch.optim.Adam(backend.model.get_grad_params(), lr=config["learning_rate"])
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", factor=.95, patience=config.get("scheduler_patience", 7), threshold=1e-4)
    cooling = CoolingBreaks()
    best, best_epoch, stale, epoch = -float("inf"), 0, 0, 0
    best_state = None
    history, losses = [], []
    seconds, updates, cpu_seconds, examples_seen = 0., 0, 0., 0
    state_path = output / "training-state.json"
    state = None
    if state_path.exists():
        state = json.loads(state_path.read_text())
        if state["config"] != config or state["training_graph_sha256"] != graph_hash:
            raise ValueError("Interrupted checkpoint graph/config mismatch")
        if state.get("resume_checkpoint"):
            path = output / state["resume_checkpoint"]
            if digest(path) != state["resume_checkpoint_sha256"]:
                raise ValueError("Checkpoint hash mismatch")
            # Only this application's own hash-checked local optimizer snapshot.
            saved = torch.load(path, map_location=backend.model.device, weights_only=False)
            if saved["graph_hash"] != graph_hash or saved["config"] != config:
                raise ValueError("Snapshot payload does not match current experiment")
            backend.model.load_state_dict(saved["model"])
            optimizer.load_state_dict(saved["optimizer"])
            scheduler.load_state_dict(saved["scheduler"])
            epoch, best, best_epoch, stale = (saved[k] for k in ("epoch", "best", "best_epoch", "stale"))
            best_state, history, losses = saved["best_state"], saved["history"], saved["losses"]
            seconds, updates, cpu_seconds = saved["seconds"], saved["updates"], saved["cpu_seconds"]
            examples_seen = saved["examples_seen"]
            random.setstate(saved["python_rng"])
            np.random.set_state(saved["numpy_rng"])
            torch.set_rng_state(saved["torch_rng"].cpu())
            print(f"Restored full epoch {epoch} with optimizer/RNG state: {output}", flush=True)
    record = {"status": "running", "config": config, "training_graph_sha256": graph_hash,
              "entities": list(dataset.graph.entities), "relations": list(dataset.graph.relations),
              "completed_epoch": epoch, "resume_checkpoint": state.get("resume_checkpoint") if state else None,
              "resume_checkpoint_sha256": state.get("resume_checkpoint_sha256") if state else None}
    atomic_json(state_path, record)
    data = torch.as_tensor(backend.training_graph.mapped(), device=backend.model.device)
    max_epoch = max(config["budgets"])
    try:
        for current in range(epoch + 1, max_epoch + 1):
            if stale >= config.get("early_stopping_checks", 3):
                break
            cooling.thermal_rest()
            start, cpu_start = time.perf_counter(), time.process_time()
            cooling_before = cooling.waited
            backend.model.train()
            permutation = torch.randperm(len(data), device=data.device)
            total = 0.
            for indices in permutation.split(config["batch_size"]):
                batch = data[indices]
                optimizer.zero_grad(set_to_none=True)
                value = torch.nn.functional.cross_entropy(backend.training_scores(batch[:, :2]), batch[:, 2])
                value = value + backend.model.collect_regularization_term()
                value.backward()
                optimizer.step()
                backend.model.post_parameter_update()
                backend.model.post_forward_pass()
                updates += 1
                examples_seen += len(batch)
                total += float(value.detach()) * len(batch)
                if updates == config.get("diagnostic_common_updates"):
                    torch.save(backend.model.state_dict(), output / "matched-updates.pt.tmp")
                    os.replace(output / "matched-updates.pt.tmp", output / "matched-updates.pt")
                    atomic_json(output / "matched-updates.json", {"updates": updates, "epoch": current, "examples_seen": examples_seen,
                        "training_graph_sha256":graph_hash,"seed":config["seed"],
                        "policy": "fixed before training, no validation or test selection; equal optimizer-update count across graph conditions"})
                cooling.thermal_rest()
                cooling.rest()
            seconds += time.perf_counter() - start - (cooling.waited-cooling_before)
            cpu_seconds += time.process_time() - cpu_start
            losses.append(total/len(data))
            if current in config["budgets"]:
                _, metrics = evaluate(backend, dataset.valid, dataset.graph.entities, dataset.positives_for_filter("valid"), "valid", cache_size=256)
                metric = metrics["mrr_exact"]
                scheduler.step(metric)
                history.append({"epoch": current, "validation": metrics, "training_loss": losses[-1], "learning_rate": optimizer.param_groups[0]["lr"]})
                if metric > best + config.get("min_improvement", 1e-4):
                    best, best_epoch, stale = metric, current, 0
                    best_state = deepcopy(backend.model.state_dict())
                else:
                    stale += 1
            payload = {"graph_hash": graph_hash, "config": config, "epoch": current,
                       "model": backend.model.state_dict(), "optimizer": optimizer.state_dict(), "scheduler": scheduler.state_dict(),
                       "best": best, "best_epoch": best_epoch, "stale": stale, "best_state": best_state,
                       "history": history, "losses": losses, "seconds": seconds, "updates": updates, "cpu_seconds": cpu_seconds, "examples_seen": examples_seen,
                       "python_rng": random.getstate(), "numpy_rng": np.random.get_state(), "torch_rng": torch.get_rng_state()}
            checkpoint = output / f"epoch-{current}.pt"
            temp = checkpoint.with_suffix(".tmp")
            torch.save(payload, temp)
            os.replace(temp, checkpoint)
            record.update({"completed_epoch": current, "resume_checkpoint": checkpoint.name, "resume_checkpoint_sha256": digest(checkpoint)})
            atomic_json(state_path, record)
            # Delete only superseded snapshots from this new run, after commit.
            for old in output.glob("epoch-*.pt"):
                if old != checkpoint:
                    old.unlink()
            print(f"{output.parent.name}/{output.name}: epoch {current}/{max_epoch}, loss={losses[-1]:.6f}, updates={updates}", flush=True)
            cooling.rest()
            if stop_after_epoch == current:
                raise KeyboardInterrupt("Synthetic interruption after committed full epoch")
        if best_state is None:
            raise RuntimeError("No validation-selected complete checkpoint")
        torch.save(backend.model.state_dict(), output / "last.pt.tmp")
        os.replace(output / "last.pt.tmp", output / "last.pt")
        backend.model.load_state_dict(best_state)
        backend.model.eval()
        torch.save(best_state, output / "best.pt.tmp")
        os.replace(output / "best.pt.tmp", output / "best.pt")
        complete = {"status": "complete", "config": config, "training_graph_sha256": graph_hash,
            "entities": list(dataset.graph.entities), "relations": list(dataset.graph.relations),
            "best_epoch": best_epoch, "best_validation_mrr": best, "history": history, "epoch_losses": losses,
            "training_seconds": seconds, "training_cpu_seconds": cpu_seconds, "optimizer_updates": updates,
            "completed_epochs": len(losses), "directional_examples_per_epoch": len(data),
            "examples_seen": examples_seen,
            "optimizer_updates_per_full_epoch": int(np.ceil(len(data)/config["batch_size"])),
            "effective_training_facts": len(dataset.graph.triples), "checkpoint": str(output / "best.pt"),
            "checkpoint_sha256": digest(output / "best.pt"), "test_access": "none",
            "environment": environment(), "resource_policy": cooling.record(), "learned_model": repr(backend.model),
            "num_parameters": backend.model.num_parameters, "resume_policy": "last committed full epoch, complete optimizer/scheduler/RNG/best state restored"}
        complete["policy_checkpoints"]={filename:{"sha256":digest(output/filename),"training_graph_sha256":graph_hash,"seed":config["seed"]}
            for filename in ("best.pt","last.pt","matched-updates.pt") if (output/filename).exists()}
        complete["resource_policy"]["scope"]="cooling observations for this invocation; committed training counters accumulate across resumes; discarded partial-epoch work excluded"
        atomic_json(output / "curve.json", complete)
        record["status"] = "complete"
        atomic_json(state_path, record)
        return backend, complete
    except BaseException as error:
        record.update({"status": "interrupted" if isinstance(error, KeyboardInterrupt) else "failed", "error": repr(error),
                       "partial_epoch_policy": "resume from last committed full epoch; no partial model is a completed baseline"})
        atomic_json(state_path, record)
        raise
