"""Hard-negative discrimination; calibration and threshold selection use VALID only."""
import time
import numpy as np


def calibrate_and_evaluate(backend, dataset):
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics import roc_auc_score, average_precision_score, accuracy_score, f1_score, balanced_accuracy_score, brier_score_loss
    except ImportError as e:
        raise RuntimeError("Install the analysis extra for classification") from e
    validation = dataset.valid + dataset.valid_negatives
    test = dataset.test + dataset.test_negatives
    yv = np.r_[np.ones(len(dataset.valid)), np.zeros(len(dataset.valid_negatives))]
    yt = np.r_[np.ones(len(dataset.test)), np.zeros(len(dataset.test_negatives))]
    start = time.perf_counter()
    sv, av = backend.score_triples(validation)
    validation_seconds = time.perf_counter() - start
    if not np.isfinite(sv).all():
        raise ValueError("Nonfinite validation classification score")
    scaler = StandardScaler().fit(sv.reshape(-1, 1))
    calibrator = LogisticRegression(C=1., random_state=0).fit(scaler.transform(sv.reshape(-1, 1)), yv)
    pv = calibrator.predict_proba(scaler.transform(sv.reshape(-1, 1)))[:, 1]
    # Select threshold by validation covered balanced accuracy. Unsupported rule cases abstain.
    candidates = np.unique(np.r_[0., pv[av], 1.])
    def objective(threshold):
        if not av.any() or len(set(yv[av])) < 2:
            return float("-inf")
        return balanced_accuracy_score(yv[av], pv[av] >= threshold)
    threshold = max(candidates, key=lambda t: (objective(t), -abs(float(t) - .5)))
    # Test is first scored AFTER fitting and selecting every calibration parameter.
    start = time.perf_counter()
    st, at = backend.score_triples(test)
    test_seconds = time.perf_counter() - start
    if not np.isfinite(st).all():
        raise ValueError("Nonfinite test classification score")
    pt = calibrator.predict_proba(scaler.transform(st.reshape(-1, 1)))[:, 1]
    decision = pt >= threshold
    n_covered = int(at.sum())
    record = {"n_test": len(test), "n_validation": len(validation), "n_covered": n_covered,
              "coverage": float(at.mean()), "threshold": float(threshold),
              "threshold_selection": "validation covered balanced accuracy; abstain when unsupported",
              "validation_selection_status": "available" if av.any() and len(set(yv[av])) == 2 else "insufficient covered validation classes; exploratory only",
              "auroc_raw": float(roc_auc_score(yt, st)), "average_precision_raw": float(average_precision_score(yt, st)),
              "brier_calibrated_all": float(brier_score_loss(yt, pt)),
              "accuracy_on_covered": float(accuracy_score(yt[at], decision[at])) if n_covered else None,
              "f1_on_covered": float(f1_score(yt[at], decision[at], zero_division=0)) if n_covered else None,
              "overall_accuracy_uncovered_miss": float(((decision == yt) & at).mean()),
              "unsupported_score_convention": "zero is abstention for rules, not a negative judgment; AUROC/AP include this fixed score",
              "calibration": {"method": "validation StandardScaler + logistic (C=1)",
                              "mean": scaler.mean_.tolist(), "scale": scaler.scale_.tolist(),
                              "coef": calibrator.coef_.tolist(), "intercept": calibrator.intercept_.tolist()},
              "validation_score_seconds": validation_seconds, "test_score_seconds": test_seconds}
    rows = [{"head": h, "relation": r, "tail": t, "label": int(y), "raw_score": float(s),
             "calibrated_probability": float(p), "supported": bool(a),
             "prediction": int(p >= threshold) if a else "abstain"}
            for (h, r, t), y, s, p, a in zip(test, yt, st, pt, at)]
    return record, rows
