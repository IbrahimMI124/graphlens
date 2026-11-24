"""Validation-selected ComplEx curves. New recipes never change legacy checkpoints.

1vsAll is per training triple (not PyKEEN's grouped multi-label LCWA), using
PyKEEN ComplEx representations/interaction with explicitly indexed reciprocals.
"""
from copy import deepcopy
from pathlib import Path
import random
import time
import json
import numpy as np
from ..data import TrainGraph
from ..backends.embedding import EmbeddingBackend
from ..evaluation import Prediction, evaluate
from ..io import write_json, write_csv, environment, triple_digest
from .resources import CoolingBreaks


class CurveModel(EmbeddingBackend):
    def __init__(self, graph, config):
        if config["model"] != "ComplEx":
            raise ValueError("The research 1vsAll adapter supports ComplEx only; use EmbeddingBackend for the existing RotatE baseline")
        if config["objective"] not in ("slcwa", "1vsAll"):
            raise ValueError("Research objectives: slcwa or per-triple 1vsAll")
        self.original_graph = graph
        self.reciprocal = config.get("reciprocal", False)
        self.base_relations = len(graph.relations)
        train = graph
        if self.reciprocal:
            inverse = tuple("inverse::" + r for r in graph.relations)
            if set(inverse) & set(graph.relations):
                raise ValueError("Inverse relation name collision")
            train = TrainGraph(graph.triples + tuple((t, "inverse::" + r, h) for h, r, t in graph.triples),
                               graph.entities, graph.relations + inverse)
        super().__init__(train, config)
        self.training_graph = train
        self.graph = graph

    def predict(self, query):
        if not self.reciprocal or query.direction == "tail":
            return super().predict(query)
        g, torch = self.graph, self.torch
        batch = torch.tensor([[g.entity_to_id[query.known], g.relation_to_id[query.relation] + self.base_relations]],
                             device=self.model.device)
        self.model.eval()
        with torch.inference_mode():
            values = self.model.score_t(batch).cpu().reshape(-1).tolist()
        return Prediction(list(zip(g.entities, values)), full_ranking=True,
                          metadata={"head_policy": "inverse relation tail score", "score_type": "raw"})

    def score_triples(self, triples):
        torch = self.torch
        data = torch.as_tensor(self.graph.mapped(triples), device=self.model.device)
        scores = []
        self.model.eval()
        with torch.inference_mode():
            for batch in data.split(256):
                forward = self.model.score_hrt(batch).reshape(-1)
                if self.reciprocal:
                    inverse = batch[:, [2, 1, 0]].clone()
                    inverse[:, 1] += self.base_relations
                    forward = (forward + self.model.score_hrt(inverse).reshape(-1)) / 2
                scores.extend(forward.cpu().tolist())
        return np.asarray(scores), np.ones(len(scores), dtype=bool)

    def training_scores(self, hr):
        """Real/imaginary component dropout; candidates share one sampled matrix."""
        torch = self.torch
        def dropout(x, p):
            if p and self.model.training:
                real = torch.nn.functional.dropout(torch.view_as_real(x), p=p, training=True)
                return torch.view_as_complex(real.contiguous())
            return x
        heads = dropout(self.model.entity_representations[0](hr[:, 0]), self.config.get("entity_dropout", 0.))
        relations = dropout(self.model.relation_representations[0](hr[:, 1]), self.config.get("relation_dropout", 0.))
        tails = dropout(self.model.entity_representations[0](None), self.config.get("entity_dropout", 0.))
        product = heads * relations
        return product.real @ tails.real.T + product.imag @ tails.imag.T


def fit_curve(dataset, config, output):
    """Only training facts and validation queries/filters are accessed here."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    backend = CurveModel(dataset.graph, config)
    torch = backend.torch
    optimizer = torch.optim.Adam(backend.model.get_grad_params(), lr=config["learning_rate"])
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", factor=.95,
                                                        patience=config.get("scheduler_patience", 7), threshold=1e-4)
    budgets = config["budgets"]
    best, best_epoch, stale = -float("inf"), 0, 0
    history, epoch_losses = [], []
    training_seconds = 0.
    cooling = CoolingBreaks()
    checkpoint = output / "best.pt"
    loop = None
    if config["objective"] == "slcwa":
        from pykeen.training import SLCWATrainingLoop
        loop = SLCWATrainingLoop(model=backend.model, triples_factory=backend.factory, optimizer=optimizer,
            negative_sampler="basic", negative_sampler_kwargs={"num_negs_per_pos": config.get("num_negs_per_pos", 2), "filtered": True},
            automatic_memory_optimization=False)
    data = torch.as_tensor(backend.training_graph.mapped(), device=backend.model.device)
    for epoch in range(1, max(budgets) + 1):
        start = time.perf_counter()
        if loop is not None:
            # PyKEEN num_epochs is the absolute endpoint when continuing.
            losses = loop.train(triples_factory=backend.factory, num_epochs=epoch,
                                batch_size=config["batch_size"], continue_training=epoch > 1,
                                clear_optimizer=False, num_workers=0, use_tqdm=False, pin_memory=False)
            loss = float(losses[-1])
            optimizer = loop.optimizer
            scheduler.optimizer = optimizer
        else:
            backend.model.train()
            permutation = torch.randperm(len(data), device=data.device)
            loss, count = 0., 0
            for indices in permutation.split(config["batch_size"]):
                batch = data[indices]
                optimizer.zero_grad(set_to_none=True)
                scores = backend.training_scores(batch[:, :2])
                value = torch.nn.functional.cross_entropy(scores, batch[:, 2])
                value = value + backend.model.collect_regularization_term()
                value.backward()
                optimizer.step()
                backend.model.post_parameter_update()
                backend.model.post_forward_pass()
                loss += float(value.detach()) * len(batch)
                count += len(batch)
            loss /= count
        training_seconds += time.perf_counter() - start
        epoch_losses.append(loss)
        print(f"{output.name}: epoch {epoch}, loss {loss:.6f}", flush=True)
        cooling.rest()
        if epoch not in budgets:
            continue
        _, metrics = evaluate(backend, dataset.valid, dataset.graph.entities, dataset.positives_for_filter("valid"),
                              "valid", cache_size=256)
        metric = metrics["mrr_exact"]
        history.append({"epoch": epoch, "training_loss": loss, "training_seconds": training_seconds,
                        "learning_rate": optimizer.param_groups[0]["lr"], "validation": metrics})
        scheduler.step(metric)
        if metric > best + config.get("min_improvement", 1e-4):
            best, best_epoch, stale = metric, epoch, 0
            torch.save(backend.model.state_dict(), checkpoint)
        else:
            stale += 1
        write_json(output / "curve.json", {"config": config, "history": history, "epoch_losses": epoch_losses,
                   "best_epoch": best_epoch, "best_validation_mrr": best, "test_access": "none", "status": "running"})
        if stale >= config.get("early_stopping_checks", 3):
            break
    backend.model.load_state_dict(torch.load(checkpoint, map_location=backend.model.device, weights_only=True))
    backend.model.eval()
    record = {"config": config, "history": history, "epoch_losses": epoch_losses,
              "best_epoch": best_epoch, "best_validation_mrr": best, "training_seconds": training_seconds,
              "training_graph_sha256": triple_digest(dataset.graph.triples), "test_access": "none", "status": "complete",
              "entities": list(dataset.graph.entities), "relations": list(dataset.graph.relations),
              "environment": environment(), "checkpoint": str(checkpoint),
              "learned_model": repr(backend.model), "num_parameters": backend.model.num_parameters,
              "resource_policy": cooling.record(),
              "protocol": "explicit reciprocal IDs; per-triple CE 1vsAll or PyKEEN sLCWA; query/component dropout only in training; global validation stopping",
              "classification_policy": "mean forward/inverse raw score when reciprocal; validation calibration remains separate"}
    write_json(output / "curve.json", record)
    write_csv(output / "curve.csv", [{"epoch": x["epoch"], "loss": x["training_loss"], "seconds": x["training_seconds"],
              "validation_mrr": x["validation"]["mrr_exact"], "validation_hits1": x["validation"]["hits1"],
              "validation_hits10": x["validation"]["hits10"]} for x in history])
    return backend, record


def load_curve(graph, path):
    path = Path(path)
    record = json.loads((path / "curve.json").read_text())
    if record["training_graph_sha256"] != triple_digest(graph.triples):
        raise ValueError("Curve checkpoint graph mismatch")
    # Initial next-phase curves used the canonical loader's sorted train-only
    # vocabulary. Guard that convention for those records as well as explicit
    # recorded maps in newer checkpoints; never accept a permuted ID mapping.
    expected_entities = record.get("entities", sorted({e for h, _, t in graph.triples for e in (h, t)}))
    expected_relations = record.get("relations", sorted({r for _, r, _ in graph.triples}))
    if list(graph.entities) != expected_entities or list(graph.relations) != expected_relations:
        raise ValueError("Curve checkpoint ID map mismatch")
    b = CurveModel(graph, record["config"])
    b.model.load_state_dict(b.torch.load(path / "best.pt", map_location=b.model.device, weights_only=True))
    b.model.eval()
    return b, record
