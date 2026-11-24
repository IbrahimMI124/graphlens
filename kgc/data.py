"""Official CoDEx splits, immutable train-only backend views, persistent IDs."""
from dataclasses import dataclass, field, replace
from pathlib import Path
import json
import time
import urllib.request
from .io import digest, triple_digest, write_json

SPLITS = ("train", "valid", "test", "valid_negatives", "test_negatives")
EXPECTED = {"s": (32888, 1827, 1828, 1827, 1828), "m": (185584, 10310, 10311, 10310, 10311)}
BASE = "https://raw.githubusercontent.com/tsafavi/codex"


def read_triples(path):
    rows = []
    for i, line in enumerate(Path(path).read_text().splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 3:
            raise ValueError(f"{path}:{i}: expected head relation tail")
        rows.append(tuple(parts))
    if len(set(rows)) != len(rows):
        raise ValueError(f"Duplicate triples in {path}")
    return tuple(rows)


def write_triples(path, triples):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join("\t".join(t) + "\n" for t in triples))


@dataclass(frozen=True)
class TrainGraph:
    """Only this object crosses the training/inference boundary. No held-out facts."""
    triples: tuple
    entities: tuple
    relations: tuple
    entity_to_id: dict = field(init=False, repr=False)
    relation_to_id: dict = field(init=False, repr=False)

    def __post_init__(self):
        object.__setattr__(self, "entity_to_id", {x: i for i, x in enumerate(self.entities)})
        object.__setattr__(self, "relation_to_id", {x: i for i, x in enumerate(self.relations)})
        if len(set(self.triples)) != len(self.triples):
            raise ValueError("Duplicate training edges")
        for h, r, t in self.triples:
            if h not in self.entity_to_id or t not in self.entity_to_id or r not in self.relation_to_id:
                raise ValueError("Training edge outside declared vocabulary")

    def mapped(self, triples=None):
        import numpy as np
        return np.array([(self.entity_to_id[h], self.relation_to_id[r], self.entity_to_id[t])
                         for h, r, t in (self.triples if triples is None else triples)], dtype=np.int64).reshape(-1, 3)

    def with_triples(self, triples):
        return replace(self, triples=tuple(triples))


@dataclass(frozen=True)
class Dataset:
    graph: TrainGraph
    valid: tuple
    test: tuple
    valid_negatives: tuple
    test_negatives: tuple
    provenance: dict
    labels: dict = field(default_factory=dict)
    filter_training_positives: tuple | None = field(default=None, repr=False)

    def positives_for_filter(self, split):
        # Graph interventions change model inputs, not the evaluator's knowledge
        # of original positives. Removed edges remain true; injected edges have
        # unknown truth and must not automatically become filtering facts.
        training = self.graph.triples if self.filter_training_positives is None else self.filter_training_positives
        if split == "valid":
            return training + self.valid  # Never test while selecting models
        if split == "test":
            return training + self.valid + self.test
        raise ValueError(split)

    def with_graph(self, graph):
        if graph.entities != self.graph.entities or graph.relations != self.graph.relations:
            raise ValueError("Perturbations must preserve the original candidate universe")
        original = self.graph.triples if self.filter_training_positives is None else self.filter_training_positives
        return replace(self, graph=graph, filter_training_positives=original)


def load_dataset(root, size="s", excerpt=False):
    root = Path(root)
    if size not in EXPECTED:
        raise ValueError("Supported CoDEx sizes: s, m")
    rows = {s: read_triples(root / f"{s}.txt") for s in SPLITS}
    if not excerpt and tuple(map(len, rows.values())) != EXPECTED[size]:
        raise ValueError(f"Not complete official CoDEx-{size.upper()} splits: { {k: len(v) for k, v in rows.items()} }. Use --excerpt only for smoke fixtures.")
    positives = set(rows["train"] + rows["valid"] + rows["test"])
    if sum(len(rows[s]) for s in ("train", "valid", "test")) != len(positives):
        raise ValueError("Positive splits overlap")
    if positives.intersection(rows["valid_negatives"] + rows["test_negatives"]):
        raise ValueError("Verified negatives overlap known positive facts")
    vocab_rows = rows["train"]
    if excerpt:
        vocab_rows = sum(rows.values(), ())
    entities = tuple(sorted({e for h, _, t in vocab_rows for e in (h, t)}))
    relations = tuple(sorted({r for _, r, _ in vocab_rows}))
    graph = TrainGraph(rows["train"], entities, relations)
    for triples in rows.values():
        graph.mapped(triples)  # Fail on unseen IDs rather than silently dropping rows
    source = root / "source.json"
    provenance = {"dataset": f"CoDEx-{size.upper()}", "excerpt": excerpt,
                  "counts": {k: len(v) for k, v in rows.items()},
                  "sha256": {s: digest(root / f"{s}.txt") for s in SPLITS},
                  "training_graph_sha256": triple_digest(graph.triples),
                  "source": json.loads(source.read_text()) if source.exists() else {"status": "local files, upstream revision unverified"}}
    labels_path = root / "labels.json"
    labels = json.loads(labels_path.read_text()) if labels_path.exists() else {}
    return Dataset(graph, *(rows[s] for s in SPLITS[1:]), provenance, labels)


def download_dataset(root, size="s", revision="master", metadata=False, resume=False):
    """Resolve master ONCE to an immutable commit; save checksums and URLs."""
    if size not in EXPECTED:
        raise ValueError(size)
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    if not resume and any((root / f"{s}.txt").exists() for s in SPLITS):
        raise FileExistsError("Dataset directory already contains splits; choose a new directory")
    pending = root / "download-state.json"
    source = root / "source.json"
    saved = pending if pending.exists() else source
    state = json.loads(saved.read_text()) if resume and saved.exists() else {}
    if state.get("size", size) != size:
        raise ValueError("Cannot resume a different CoDEx size")
    commit = state.get("commit")
    if not commit:
        print("Resolving upstream CoDEx commit...", flush=True)
        req = urllib.request.Request(f"https://api.github.com/repos/tsafavi/codex/commits/{revision}",
                                     headers={"User-Agent": "aid851-kgc-study"})
        with urllib.request.urlopen(req, timeout=15) as f:
            commit = json.load(f)["sha"]
    urls = state.get("urls", {})
    checksums = state.get("sha256", {})
    state = {"commit": commit, "size": size, "urls": urls, "sha256": checksums}
    write_json(pending, state)

    def fetch(url, temp):
        start = time.monotonic()
        count = 0
        with urllib.request.urlopen(url, timeout=15) as response, temp.open("wb") as output:
            while True:
                # read1 surfaces partial transfers promptly; socket and total budgets
                # bound a stalled or indefinitely trickling host.
                chunk = getattr(response, "read1", response.read)(64 * 1024)
                if not chunk:
                    break
                output.write(chunk)
                count += len(chunk)
                print(f"  {temp.stem}: {count:,} bytes", flush=True)
                if time.monotonic() - start > 120:
                    raise TimeoutError(f"Download time budget exceeded: {url}; rerun with --resume")

    for split in SPLITS:
        destination = root / f"{split}.txt"
        url = f"{BASE}/{commit}/data/triples/codex-{size}/{split}.txt"
        if destination.exists() and checksums.get(split) == digest(destination):
            print(f"Reusing verified {split}.txt", flush=True)
            continue
        print(f"Downloading {split}.txt" + (" to verify existing file" if destination.exists() else ""), flush=True)
        temp = root / f"{split}.tmp"
        fetch(url, temp)
        read_triples(temp)
        if destination.exists():
            if digest(destination) != digest(temp):
                raise ValueError(f"Existing {destination} differs from pinned upstream; preserved it. Use a new data directory.")
            temp.unlink()
        else:
            temp.rename(destination)
        urls[split] = url
        checksums[split] = digest(destination)
        write_json(pending, state)
    if metadata:
        labels = {}
        for kind in ("entities", "relations"):
            url = f"{BASE}/{commit}/data/{kind}/en/{kind}.json"
            temp = root / f"{kind}-metadata.tmp"
            print(f"Downloading optional {kind} metadata", flush=True)
            fetch(url, temp)
            labels.update({k: v["label"] for k, v in json.loads(temp.read_text()).items()})
            temp.unlink()
        write_json(root / "labels.json", labels)
        temp = root / "types-metadata.tmp"
        fetch(f"{BASE}/{commit}/data/types/entity2types.json", temp)
        json.loads(temp.read_text())
        temp.rename(root / "entity2types.json")
    write_json(source, state)
    dataset = load_dataset(root, size)
    pending.unlink(missing_ok=True)
    return dataset
