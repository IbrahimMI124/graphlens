"""Real AnyBURL mining via Java; answer-blind application via documented PyClause.

No replacement miner is supplied. Java Apply's benchmark filter path is deliberately
unused: PyClause QAHandler receives only (known entity, relation) pairs.
"""
from dataclasses import asdict, dataclass
from pathlib import Path
import re
import shutil
import subprocess
import time
import numpy as np
from ..data import write_triples
from ..evaluation import Prediction
from ..io import digest, environment, triple_digest, write_json

JAR_URL = "https://web.informatik.uni-mannheim.de/AnyBURL/AnyBURL-23-1x.jar"
# Inspected Learn bytecode: its normal snapshot-complete path calls System.exit(1).
KNOWN_EXIT_ONE_JAR = "d1977ee0ffae3f715e48e32e91e8d46d0c5c243941a5a430fd132086160d06b5"
ATOM = re.compile(r"([^\s(),]+)\(([^,()]+),([^,()]+)\)")


@dataclass(frozen=True)
class Rule:
    expression: str
    predictions: int
    support: int
    confidence: float
    length: int
    kind: str


def parse_rule(line):
    fields = line.strip().split(maxsplit=3)
    if len(fields) != 4 or "<=" not in fields[3]:
        raise ValueError(f"Invalid AnyBURL rule: {line[:120]}")
    predictions, support = int(fields[0]), int(fields[1])
    confidence = float(fields[2])
    if predictions < support or support < 0 or not 0 <= confidence <= 1:
        raise ValueError("Invalid rule statistics")
    expression = fields[3]
    head, body = expression.split("<=", 1)
    atoms = ATOM.findall(body)
    head_atoms = ATOM.findall(head)
    if len(head_atoms) != 1:
        raise ValueError("Invalid rule head")
    # AnyBURL uses single uppercase variable names; Wikidata IDs are constants.
    args = [v for atom in head_atoms + atoms for v in atom[1:]]
    kind = ("entity_prior" if not atoms else "constant" if any(not re.fullmatch(r"[A-Z]", x) for x in args)
            else "relational_path")
    return Rule(expression, predictions, support, confidence, len(atoms), kind)


def read_rules(path, progress_callback=None):
    rules = []
    for line in Path(path).read_text().splitlines():
        if line.strip():
            rules.append(parse_rule(line))
            if progress_callback and len(rules) % 10000 == 0:
                progress_callback()
    return rules


def mine(graph, config, output):
    """Wall-clock-budgeted mining is stochastic; a Python seed cannot seed the JAR."""
    jar = Path(config["jar"]).expanduser().resolve()
    if not jar.is_file() or shutil.which("java") is None:
        raise RuntimeError(f"Real AnyBURL JAR or Java missing. Obtain {JAR_URL}; see docs/INSTALL.md")
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    train = output / "train.txt"
    write_triples(train, graph.triples)
    seconds = int(config["seconds"])
    if seconds < 1 or config["max_length"] not in (1, 2, 3):
        raise ValueError("Positive mining time and maximum cyclic length 1, 2, or 3 required")
    props = {"PATH_TRAINING": train, "PATH_OUTPUT": output / "rules", "SNAPSHOTS_AT": seconds,
             "WORKER_THREADS": config.get("threads", 1), "MAX_LENGTH_CYCLIC": config["max_length"],
             "MAX_LENGTH_ACYCLIC": 1, "MAX_LENGTH_GROUNDED_CYCLIC": 1,
             "ZERO_RULES_ACTIVE": str(config.get("zero_rules", False)).lower(),
             "THRESHOLD_CORRECT_PREDICTIONS": config.get("min_support", 2)}
    properties = output / "learn.properties"
    properties.write_text("".join(f"{k} = {v}\n" for k, v in props.items()))
    command = ["java", f"-Xmx{config.get('heap', '2G')}", "-cp", str(jar),
               "de.unima.ki.anyburl.Learn", str(properties)]
    rules_file = output / f"rules-{seconds}"
    if rules_file.exists():
        raise FileExistsError(f"Refusing to overwrite an existing mining snapshot: {rules_file}")
    start = time.perf_counter()
    with (output / "learn.log").open("w") as log:
        process = subprocess.run(command, cwd=output, stdout=log, stderr=subprocess.STDOUT,
                                 check=False, timeout=seconds + config.get("startup_timeout", 180))
    elapsed = time.perf_counter() - start
    log_text = (output / "learn.log").read_text()
    known_normal_exit = (process.returncode == 1 and digest(jar) == KNOWN_EXIT_ONE_JAR
                         and ">>> Bye, bye." in log_text
                         and re.search(r">>> stored \d+ rules", log_text)
                         and not re.search(r"Exception|Error:|Could not read", log_text)
                         and rules_file.is_file())
    if process.returncode != 0 and not known_normal_exit:
        raise RuntimeError(f"AnyBURL exited {process.returncode}; inspect {output / 'learn.log'}")
    rules = read_rules(rules_file)
    write_json(output / "rules.json", [asdict(x) for x in rules])
    record = {"backend": "AnyBURL-23-1x", "training_seconds": elapsed,
              "training_graph_sha256": triple_digest(graph.triples), "jar_sha256": digest(jar),
              "rule_file_sha256": digest(rules_file), "rules_file": str(rules_file),
              "rule_count": len(rules), "config": config, "command": command,
              "java_exit_code": process.returncode,
              "known_normal_exit_one": bool(known_normal_exit),
              "environment": environment(), "jar_seed_control": "not verified; stochastic wall-clock snapshots",
              "rule_scope": "cyclic/path length varied; acyclic and grounded cyclic fixed at 1"}
    write_json(output / "training.json", record)
    return rules_file, record


class AnyBURLBackend:
    def __init__(self, graph, rules_file, top_k=100, collect_evidence=True, evidence_mode="groundings",
                 loader_options=None, qa_options=None, metadata_callback=None, token_indices=None, retain_catalog_metadata=True):
        try:
            from c_clause import Loader, QAHandler, PredictionHandler
            from clause import Options
        except ImportError as e:
            raise RuntimeError("AnyBURL application needs real PyClause (c_clause), a C++14 compiler, and learned AnyBURL rules; see docs/INSTALL.md") from e
        self.graph = graph
        self.training_edges = set(graph.triples)
        self.rules_file = Path(rules_file)
        self.rules = read_rules(rules_file, metadata_callback)
        if not retain_catalog_metadata and evidence_mode!="none":
            raise ValueError("Metadata-light application requires evidence_mode='none'; retain metadata for explanations")
        self.retain_catalog_metadata=bool(retain_catalog_metadata)
        self.by_expression, self.rule_catalog, self.expression_to_id = {}, {}, {}
        if retain_catalog_metadata:
            for i, r in enumerate(self.rules):
                self.by_expression[r.expression] = asdict(r)
                self.rule_catalog[i] = asdict(r)
                self.expression_to_id[r.expression] = i
                if metadata_callback and i % 10000 == 0:
                    metadata_callback()
        if evidence_mode not in ("groundings", "references", "none"):
            raise ValueError(evidence_mode)
        self.evidence_mode = evidence_mode
        self.top_k = top_k
        opts = Options()
        # Preserve AnyBURL's maxplus ordering. The scalar score alone does not
        # encode its lexicographic rule sequence. Do not re-sort by that score.
        for key, value in {"qa_handler.aggregation_function": "maxplus",
                           "qa_handler.tie_handling": "frequency",
                           "qa_handler.collect_rules": collect_evidence and evidence_mode != "none",
                           "qa_handler.topk": top_k, "qa_handler.filter_w_data": False,
                           "qa_handler.num_threads": 1, "qa_handler.verbose": False,
                           "qa_handler.disc_at_least": -1, "qa_handler.hard_stop_at": -1,
                           "qa_handler.num_top_rules": -1,
                           "loader.b_max_branching_factor": -1,
                           "loader.d_max_branching_factor": -1,
                           "loader.verbose": False, "loader.num_threads": 1,
                           "prediction_handler.collect_explanations": True,
                           "prediction_handler.aggregation_function": "maxplus",
                           "prediction_handler.num_top_rules": -1,
                           "prediction_handler.num_threads": 1,
                           "prediction_handler.verbose": False}.items():
            opts.set(key, value)
        self.options = opts
        for key, value in (loader_options or {}).items():
            opts.set("loader." + key, value)
        for key, value in (qa_options or {}).items():
            opts.set("qa_handler." + key, value)
        self.effective_loader_options = opts.get("loader", as_string=False)
        self.effective_qa_options = opts.get("qa_handler", as_string=False)
        self.loader = Loader(options=opts.get("loader"))
        self.token_indices = token_indices
        if token_indices is not None:
            if set(token_indices["entities"]) != set(graph.entities) or set(token_indices["relations"]) != set(graph.relations):
                raise ValueError("Fixed native indices must match the declared candidate vocabulary")
            if len(token_indices["entities"]) != len(graph.entities) or len(token_indices["relations"]) != len(graph.relations):
                raise ValueError("Duplicate fixed vocabulary tokens")
            self.loader.set_entity_index(token_indices["entities"])
            self.loader.set_relation_index(token_indices["relations"])
        self.loader.load_data(list(graph.triples))  # No validation, test, or verified negatives
        if token_indices is not None:
            if self.loader.get_entity_index() != {e:i for i,e in enumerate(token_indices["entities"])} or self.loader.get_relation_index() != {r:i for i,r in enumerate(token_indices["relations"])}:
                raise ValueError("Native loader changed the supplied token index")
        self.loader.load_rules(str(self.rules_file))
        self.qa = QAHandler(options=opts.get("qa_handler"))
        self.scorer = PredictionHandler(options=opts.get("prediction_handler"))
        opts.set("prediction_handler.collect_explanations", False)
        self.classifier = PredictionHandler(options=opts.get("prediction_handler"))
        # Empty/perturbed relations or isolated entities can be unseen in PyClause.
        self.seen_entities = {x for h, _, t in graph.triples for x in (h, t)}
        self.seen_relations = {r for _, r, _ in graph.triples}
        if token_indices is not None:
            self.seen_entities = set(token_indices["entities"])
            self.seen_relations = set(token_indices["relations"])

    def explain(self, triples):
        if not self.retain_catalog_metadata:
            raise RuntimeError("Reload with retained catalog metadata before requesting rule explanations")
        if not triples:
            return {}, []
        self.scorer.calculate_scores(triples=list(triples), loader=self.loader)
        raw = self.scorer.get_explanations(as_string=True)
        targets, expressions, groundings = raw
        evidence = {}
        for triple, rules, grounds in zip(targets, expressions, groundings):
            items = []
            for expression, grounding in zip(rules, grounds):
                # PyClause may return full AnyBURL lines or expressions depending on version.
                expression = expression.split("\t")[-1].strip()
                item = dict(self.by_expression.get(expression, {"expression": expression}))
                item["groundings"] = grounding
                for instance in grounding:
                    if any(tuple(edge) not in self.training_edges for edge in instance):
                        raise ValueError("Backend explanation includes a non-training edge")
                items.append(item)
            evidence[tuple(triple)] = items
        return evidence, self.scorer.get_scores(as_string=True)

    def predict(self, query):
        if query.known not in self.seen_entities or query.relation not in self.seen_relations:
            return Prediction([], exhaustive_support=False, metadata={"query_representable": False,
                "reason": "unseen token in perturbed PyClause training graph; abstention, not proof that no constant/prior rule applies"})
        self.qa.calculate_answers(queries=[(query.known, query.relation)], loader=self.loader,
                                  direction=query.direction)
        answers = self.qa.get_answers(as_string=True)[0]
        candidates = [(str(e), float(score)) for e, score in answers]
        # Preserve native rule attribution even if normalized explanation API differs.
        by_candidate, raw_rules = {}, []
        if self.evidence_mode == "references" and candidates:
            raw_rules = self.qa.get_rules(as_string=True)
            if len(raw_rules) != 1 or len(raw_rules[0]) != len(candidates):
                raise ValueError("PyClause candidate/rule attribution alignment mismatch")
            by_candidate = {e: [self.expression_to_id[expression.strip()] for expression in expressions]
                            for (e, _), expressions in zip(candidates, raw_rules[0])}
            raw_rules = []  # Rules are recorded once in rule_catalog.json, not repeated per query
        elif self.evidence_mode == "groundings":
            raw_rules = self.qa.get_rules(as_string=True)
            triples = [query.triple(e) for e, _ in candidates]
            evidence, _ = self.explain(triples)
            by_candidate = {e: evidence.get(query.triple(e), []) for e, _ in candidates}
        return Prediction(candidates, evidence=by_candidate, order_is_ranking=True,
                          # Conservative: do not infer completeness just because len < K.
                          exhaustive_support=False,
                          metadata={"backend": "AnyBURL rules / PyClause maxplus", "top_k": self.top_k,
                                    "evidence_mode": self.evidence_mode,
                                    "raw_rule_attribution": raw_rules, "ranking": "potentially truncated",
                                    "tie_handling": "native maxplus rule sequence, then training frequency",
                                    "score_type": "raw top rule confidence; native ranking uses full rule sequence, not calibrated probability"})

    def score_triples(self, triples):
        scores = np.zeros(len(triples))
        supported = np.zeros(len(triples), dtype=bool)
        known = [(i, t) for i, t in enumerate(triples) if t[0] in self.seen_entities and t[2] in self.seen_entities
                 and t[1] in self.seen_relations]
        if known:
            self.classifier.calculate_scores(triples=[t for _, t in known], loader=self.loader)
            raw_scores = self.classifier.get_scores(as_string=True)
            score_map = {tuple(row[:3]): float(row[3]) for row in raw_scores}
            for i, triple in known:
                scores[i] = score_map[triple]
                # Fixed loader policy accepts only positive-confidence rules and
                # uses positive type weights. A positive max score certifies support.
                supported[i] = scores[i] > 0
        return scores, supported
