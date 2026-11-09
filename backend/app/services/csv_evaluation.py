import csv
import io

LABELS = ["blocker", "critical", "major", "normal", "minor", "trivial"]
TEXT_NAMES = ("text", "short description", "title", "summary", "description")
SEVERITY_NAMES = ("severity", "severity label", "label")
PROJECT_NAMES = ("project", "product", "component")
MAX_ROWS = 1000
MAX_BYTES = 2 * 1024 * 1024
BATCH_SIZE = 64
MIN_RELIABLE_ROWS = 200


class CsvProblem(ValueError):
    """CSV mein aisi ghalti jo user ko batani hai."""


def _decode(data):
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("latin-1")


def _find(lookup, names):
    for name in names:
        if name in lookup:
            return lookup[name]
    return None


def parse_labeled_csv(data, max_rows=MAX_ROWS):
    """Wapas deta hai: (rows, skipped_count, skipped_examples). rows = [(text, project, label)]."""
    reader = csv.DictReader(io.StringIO(_decode(data)))
    if not reader.fieldnames:
        raise CsvProblem("The file is empty.")
    lookup = {str(name).strip().lower(): name for name in reader.fieldnames if name}
    text_column = _find(lookup, TEXT_NAMES)
    severity_column = _find(lookup, SEVERITY_NAMES)
    project_column = _find(lookup, PROJECT_NAMES)
    if text_column is None or severity_column is None:
        raise CsvProblem(
            "Columns not found. The file needs a text column (text, title, summary or short description) "
            "and a severity column (severity or label). Found: " + ", ".join(str(n) for n in reader.fieldnames)
        )

    rows, skipped, examples, total = [], 0, [], 0
    for number, record in enumerate(reader, start=2):
        total += 1
        if total > max_rows:
            raise CsvProblem(f"Too many rows (the limit is {max_rows}). Use a smaller file.")
        text = " ".join(str(record.get(text_column) or "").split())
        label = str(record.get(severity_column) or "").strip().lower()
        project = str(record.get(project_column) or "").strip() if project_column else ""
        reason = None
        if not text:
            reason = f"row {number}: empty text"
        elif label not in LABELS:
            reason = f"row {number}: unknown severity '{label[:20]}'"
        if reason:
            skipped += 1
            if len(examples) < 5:
                examples.append(reason)
            continue
        rows.append((text, project or None, label))
    return rows, skipped, examples


def predict_all(predictor, rows, batch_size=BATCH_SIZE):
    labels = []
    for start in range(0, len(rows), batch_size):
        chunk = rows[start:start + batch_size]
        results = predictor.predict([r[0] for r in chunk], [r[1] for r in chunk])
        labels.extend(item["label"] for item in results)
    return labels


def compute_metrics(true_labels, predicted_labels, labels=LABELS):
    index = {label: i for i, label in enumerate(labels)}
    size = len(labels)
    matrix = [[0] * size for _ in range(size)]
    for actual, predicted in zip(true_labels, predicted_labels):
        matrix[index[actual]][index[predicted]] += 1

    total = len(true_labels)
    per_class = []
    for i, label in enumerate(labels):
        true_positive = matrix[i][i]
        predicted_count = sum(matrix[r][i] for r in range(size))
        support = sum(matrix[i])
        precision = true_positive / predicted_count if predicted_count else 0.0
        recall = true_positive / support if support else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class.append({"label": label, "precision": precision, "recall": recall, "f1": f1, "support": support})

    present = [row for row in per_class if row["support"] > 0]
    macro_f1 = sum(row["f1"] for row in present) / len(present) if present else 0.0
    accuracy = sum(matrix[i][i] for i in range(size)) / total if total else 0.0
    majority = max(sum(row) for row in matrix) / total if total else 0.0
    return {
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "majority_baseline_accuracy": majority,
        "labels": list(labels),
        "per_class": per_class,
        "confusion_matrix": matrix,
    }


def build_warnings(rows_used, per_class):
    warnings = []
    if rows_used < MIN_RELIABLE_ROWS:
        warnings.append(f"Only {rows_used} usable rows. With fewer than {MIN_RELIABLE_ROWS} the numbers are rough.")
    missing = [row["label"] for row in per_class if row["support"] == 0]
    if missing:
        warnings.append("No rows for: " + ", ".join(missing) + ". Macro F1 only counts the classes that appear.")
    warnings.append(
        "If these reports were part of the model's training data, the scores look better than they really are."
    )
    return warnings
