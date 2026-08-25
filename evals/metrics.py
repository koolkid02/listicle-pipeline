"""Hand-rolled classification metrics for the guardrail (binary) and intent (multiclass)
eval suites. No sklearn dependency - the datasets are small and the formulas are simple."""

from collections import Counter


def binary_confusion(preds: list[bool], labels: list[bool]) -> dict:
    assert len(preds) == len(labels)
    tp = sum(p and l for p, l in zip(preds, labels))
    fp = sum(p and not l for p, l in zip(preds, labels))
    tn = sum(not p and not l for p, l in zip(preds, labels))
    fn = sum(not p and l for p, l in zip(preds, labels))

    accuracy = (tp + tn) / len(preds) if preds else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    return {
        "n": len(preds),
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def multiclass_report(preds: list[str], labels: list[str], classes: list[str]) -> dict:
    assert len(preds) == len(labels)
    n = len(preds)
    accuracy = sum(p == l for p, l in zip(preds, labels)) / n if n else 0.0

    confusion = {label: Counter() for label in classes}
    for p, l in zip(preds, labels):
        confusion[l][p] += 1

    per_class = {}
    for cls in classes:
        tp = confusion[cls][cls]
        fp = sum(confusion[other][cls] for other in classes if other != cls)
        fn = sum(v for k, v in confusion[cls].items() if k != cls)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        per_class[cls] = {"precision": precision, "recall": recall, "f1": f1, "support": tp + fn}

    macro_precision = sum(m["precision"] for m in per_class.values()) / len(classes)
    macro_recall = sum(m["recall"] for m in per_class.values()) / len(classes)
    macro_f1 = sum(m["f1"] for m in per_class.values()) / len(classes)

    return {
        "n": n,
        "accuracy": accuracy,
        "per_class": per_class,
        "macro_precision": macro_precision,
        "macro_recall": macro_recall,
        "macro_f1": macro_f1,
        "confusion": {label: dict(counts) for label, counts in confusion.items()},
    }
