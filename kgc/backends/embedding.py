"""PyKEEN 1.11.1 ComplEx / RotatE using a train-only SLCWA loop."""
import random
import time
from pathlib import Path
import numpy as np
from ..evaluation import Prediction
from ..io import environment, triple_digest, write_json


def require_backend():
    try:
        import torch
        from pykeen import models
        from pykeen.triples import TriplesFactory
        from pykeen.training import SLCWATrainingLoop
    except ImportError as e:
        raise RuntimeError("Neural backend unavailable. Install Python 3.11/3.12, torch and pykeen==1.11.1; see docs/INSTALL.md") from e
    return torch, models, TriplesFactory, SLCWATrainingLoop


class EmbeddingBackend:
    def __init__(self, graph, config):
        torch, models, factory, _ = require_backend()
        self.graph, self.config, self.torch = graph, dict(config), torch
        seed = config["seed"]
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        torch.set_num_threads(config.get("threads", 1))
        torch.use_deterministic_algorithms(True)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        if config["model"] not in ("ComplEx", "RotatE"):
            raise ValueError("Supported embedding models: ComplEx, RotatE")
        self.factory = factory(mapped_triples=torch.as_tensor(graph.mapped(), dtype=torch.long),
                               entity_to_id=graph.entity_to_id, relation_to_id=graph.relation_to_id,
                               create_inverse_triples=False)
        self.model = getattr(models, config["model"])(
            triples_factory=self.factory, embedding_dim=config["embedding_dim"],
            random_seed=seed, loss=config.get("loss", "SoftplusLoss"),
            **config.get("model_kwargs", {})).to(config.get("device", "cpu"))

    def fit(self, output):
        _, _, _, loop_class = require_backend()
        start = time.perf_counter()
        loop = loop_class(model=self.model, triples_factory=self.factory,
                          optimizer="Adam", optimizer_kwargs={"lr": self.config["learning_rate"]},
                          negative_sampler="basic", negative_sampler_kwargs={
                              "num_negs_per_pos": self.config.get("num_negs_per_pos", 10),
                              "filtered": True}, automatic_memory_optimization=False)
        callbacks = []
        if self.config.get("log_epochs", False):
            from pykeen.training.callbacks import TrainingCallback
            epochs = self.config["epochs"]
            class Progress(TrainingCallback):
                def post_epoch(self, epoch, epoch_loss, **kwargs):
                    print(f"Neural epoch {epoch}/{epochs}: loss={epoch_loss:.6f}", flush=True)
            callbacks.append(Progress())
        losses = loop.train(triples_factory=self.factory, num_epochs=self.config["epochs"],
                            batch_size=self.config["batch_size"], num_workers=0,
                            use_tqdm=False, use_tqdm_batch=False, pin_memory=False, callbacks=callbacks)
        if self.model.device.type == "cuda":
            self.torch.cuda.synchronize()
        seconds = time.perf_counter() - start
        self.model.eval()
        output = Path(output)
        output.mkdir(parents=True, exist_ok=True)
        self.torch.save(self.model.state_dict(), output / "model.pt")
        record = {"backend": "pykeen", "config": self.config, "losses": losses,
                  "training_seconds": seconds, "learned_model": repr(self.model),
                  "num_parameters": self.model.num_parameters,
                  "training_graph_sha256": triple_digest(self.graph.triples),
                  "entities": self.graph.entities, "relations": self.graph.relations,
                  "environment": environment(), "training_data": "positive training edges only",
                  "negative_sampling": "train-filtered unobserved corruptions, not verified false facts"}
        write_json(output / "training.json", record)
        return record

    def predict(self, query):
        g, torch = self.graph, self.torch
        r, known = g.relation_to_id[query.relation], g.entity_to_id[query.known]
        pair = [r, known] if query.direction == "head" else [known, r]
        batch = torch.tensor([pair], dtype=torch.long, device=self.model.device)
        self.model.eval()
        with torch.inference_mode():
            scores = (self.model.score_h(batch) if query.direction == "head" else self.model.score_t(batch))
            values = scores.detach().cpu().numpy().reshape(-1).tolist()
        return Prediction(list(zip(g.entities, values)), full_ranking=True,
                          metadata={"score_type": "raw model score", "probability": False})

    def score_triples(self, triples):
        torch = self.torch
        batch = torch.as_tensor(self.graph.mapped(triples), dtype=torch.long, device=self.model.device)
        self.model.eval()
        chunks = []
        with torch.inference_mode():
            for chunk in batch.split(self.config.get("score_batch_size", 256)):
                chunks.extend(self.model.score_hrt(chunk).detach().cpu().reshape(-1).tolist())
        return np.asarray(chunks), np.ones(len(chunks), dtype=bool)

    @classmethod
    def load(cls, graph, path):
        import json
        path = Path(path)
        record = json.loads((path / "training.json").read_text())
        if record["training_graph_sha256"] != triple_digest(graph.triples):
            raise ValueError("Checkpoint training graph mismatch")
        if record["entities"] != list(graph.entities) or record["relations"] != list(graph.relations):
            raise ValueError("Checkpoint ID map mismatch")
        backend = cls(graph, record["config"])
        backend.model.load_state_dict(backend.torch.load(path / "model.pt", map_location=backend.model.device, weights_only=True))
        backend.model.eval()
        return backend
