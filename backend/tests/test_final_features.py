import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.repositories.prediction_records import SEVERITY_MODEL_VERSION
from app.services import github_triage
from app.services.csv_evaluation import (
    CsvProblem,
    build_warnings,
    compute_metrics,
    parse_labeled_csv,
    predict_all,
)
from app.services.triage import run_triage

SECRET = "s" * 20


class StubPredictor:
    version = "stub-v1"

    def __init__(self, label="major", needs_review=False, margin=0.3):
        self.label, self.needs_review, self.margin = label, needs_review, margin
        self.calls = []

    def predict(self, texts, projects=None):
        self.calls.append(len(texts))
        return [
            {"label": self.label, "margin": self.margin, "needs_review": self.needs_review,
             "scores": {"major": 1.0, "normal": 0.5}}
            for _ in texts
        ]


class StubFinder:
    threshold = 0.8

    def find(self, text, top_k=None, threshold=None):
        return [
            {"bug_id": 11, "project": "Core", "text": "Crash on save @someone `x`", "similarity": 0.91},
            {"bug_id": 12, "project": "JDT", "text": "Another crash", "similarity": 0.62},
        ][: top_k or 5]


# ---------- triage ----------


def test_triage_marks_likely_duplicates_by_the_finder_threshold():
    result = run_triage(StubPredictor(), StubFinder(), "Crash on save")
    assert result["severity"]["label"] == "major"
    assert [hit["likely_duplicate"] for hit in result["similar"]] == [True, False]
    assert result["duplicate_threshold"] == 0.8
    assert result["model_version"] == "stub-v1"


def test_triage_works_without_a_finder_and_falls_back_to_the_default_model_name():
    class Plain:
        def predict(self, texts, projects=None):
            return [{"label": "normal", "margin": 0.9, "needs_review": False, "scores": {"normal": 1.0}}]

    result = run_triage(Plain(), None, "Some text")
    assert result["similar"] == [] and result["duplicate_threshold"] is None
    assert result["model_version"] == SEVERITY_MODEL_VERSION


# ---------- csv evaluation ----------


RAW_HEADER = "Project,Bug ID,Severity Label,Resolution Status,Short Description\n"


def test_parse_accepts_the_raw_dataset_header_and_skips_bad_rows():
    data = (
        RAW_HEADER
        + "Core,1,normal,FIXED,Crash on save\n"
        + "Core,2,urgent,FIXED,Unknown severity\n"
        + "Core,3,major,FIXED,\n"
        + "JDT,4,MAJOR,FIXED,Another one\n"
    ).encode()
    rows, skipped, examples = parse_labeled_csv(data)
    assert rows == [("Crash on save", "Core", "normal"), ("Another one", "JDT", "major")]
    assert skipped == 2
    assert any("unknown severity" in item for item in examples) and any("empty text" in item for item in examples)


def test_parse_reports_missing_columns_and_too_many_rows():
    with pytest.raises(CsvProblem):
        parse_labeled_csv(b"a,b\n1,2\n")
    with pytest.raises(CsvProblem):
        parse_labeled_csv(b"")
    many = "text,severity\n" + "x,normal\n" * 4
    with pytest.raises(CsvProblem):
        parse_labeled_csv(many.encode(), max_rows=3)


def test_parse_reads_latin1_files_too():
    rows, _, _ = parse_labeled_csv("text,severity\ncaf\u00e9 crash,major\n".encode("latin-1"))
    assert rows[0][0] == "caf\u00e9 crash"


def test_metrics_are_computed_correctly_on_a_small_example():
    truth = ["normal", "normal", "major", "blocker"]
    predicted = ["normal", "major", "major", "normal"]
    metrics = compute_metrics(truth, predicted)
    by_label = {row["label"]: row for row in metrics["per_class"]}
    assert metrics["accuracy"] == 0.5
    assert metrics["majority_baseline_accuracy"] == 0.5
    assert by_label["normal"]["precision"] == 0.5 and by_label["normal"]["recall"] == 0.5
    assert by_label["major"]["recall"] == 1.0 and round(by_label["major"]["f1"], 4) == 0.6667
    assert by_label["blocker"]["f1"] == 0.0 and by_label["blocker"]["support"] == 1
    # macro F1 sirf un classes par jo maujood hain: normal, major, blocker
    assert round(metrics["macro_f1"], 4) == round((0.5 + 2 / 3 + 0.0) / 3, 4)
    assert metrics["confusion_matrix"][3][3] == 1  # normal -> normal


def test_predict_all_works_in_batches_and_keeps_the_order():
    predictor = StubPredictor()
    rows = [(f"text {i}", None, "normal") for i in range(5)]
    assert predict_all(predictor, rows, batch_size=2) == ["major"] * 5
    assert predictor.calls == [2, 2, 1]


def test_warnings_mention_few_rows_missing_classes_and_training_data():
    metrics = compute_metrics(["normal"] * 3, ["normal"] * 3)
    warnings = build_warnings(3, metrics["per_class"])
    assert any("Only 3 usable rows" in item for item in warnings)
    assert any("No rows for" in item for item in warnings)
    assert any("training data" in item for item in warnings)


# ---------- github helpers ----------


def sign(body, secret=SECRET):
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_signature_check():
    body = b'{"a": 1}'
    assert github_triage.verify_signature(SECRET, body, sign(body)) is True
    assert github_triage.verify_signature(SECRET, body, sign(body, "other-secret-value")) is False
    assert github_triage.verify_signature(SECRET, body, None) is False
    assert github_triage.verify_signature(SECRET, body, "sha1=abc") is False
    assert github_triage.verify_signature("", body, sign(body)) is False


def test_comment_has_the_suggestion_and_is_safe_for_mentions():
    result = run_triage(StubPredictor(needs_review=True), StubFinder(), "Crash on save")
    comment = github_triage.build_comment(result)
    assert "Suggested severity: **major**" in comment
    assert "not sure" in comment
    assert "(likely duplicate)" in comment
    assert "`Crash on save @someone 'x'`" in comment  # code ke andar, backtick badla hua
    assert "not a decision" in comment


def issue_payload(**changes):
    payload = {
        "action": "opened",
        "issue": {"number": 7, "title": "Crash when saving a file"},
        "repository": {"full_name": "owner/repo"},
    }
    payload.update(changes)
    return payload


def test_new_issue_gets_labels_and_one_comment():
    calls = []
    outcome = github_triage.handle_issue_opened(
        issue_payload(), StubPredictor(needs_review=True), StubFinder(), lambda url, data: calls.append((url, data))
    )
    assert outcome["labels"] == ["severity: major", "triage: needs review", "triage: possible duplicate"]
    assert calls[0][0] == "https://api.github.com/repos/owner/repo/issues/7/labels"
    assert calls[1][0] == "https://api.github.com/repos/owner/repo/issues/7/comments"
    assert "Suggested severity" in calls[1][1]["body"]


def test_issue_handling_ignores_bad_input():
    calls = []
    post = lambda url, data: calls.append(url)  # noqa: E731
    predictor = StubPredictor()
    assert github_triage.handle_issue_opened(issue_payload(repository={"full_name": "bad name/../x"}), predictor, None, post) is None
    assert github_triage.handle_issue_opened(issue_payload(issue={"number": 1, "title": "ab"}), predictor, None, post) is None
    assert github_triage.handle_issue_opened(
        issue_payload(issue={"number": 1, "title": "A pull request", "pull_request": {}}), predictor, None, post
    ) is None
    assert calls == []


def test_issue_handling_works_without_the_duplicate_finder():
    calls = []
    outcome = github_triage.handle_issue_opened(issue_payload(), StubPredictor(), None, lambda url, data: calls.append(url))
    assert outcome["labels"] == ["severity: major"]
    assert len(calls) == 2


# ---------- endpoints ----------


def make_client(predictor=None, finder=None, **options):
    app = create_app(Settings(load_models=False, **options))
    client = TestClient(app)
    client.__enter__()
    client.app.state.severity = predictor
    client.app.state.finder = finder
    return client


def test_triage_endpoint_returns_severity_and_similar_reports():
    client = make_client(StubPredictor(), StubFinder())
    response = client.post("/api/v1/triage", json={"text": "Crash on save", "project": "Core"})
    assert response.status_code == 200
    body = response.json()
    assert body["severity"]["label"] == "major"
    assert body["similar"][0]["likely_duplicate"] is True
    assert body["model_version"] == "stub-v1"


def test_triage_endpoint_rejects_short_text_and_needs_a_loaded_model():
    client = make_client(StubPredictor(), StubFinder())
    assert client.post("/api/v1/triage", json={"text": "ab"}).status_code == 422
    empty = make_client(None, None)
    assert empty.post("/api/v1/triage", json={"text": "Crash on save"}).status_code == 503


def test_evaluate_endpoint_returns_metrics_for_a_labelled_csv():
    client = make_client(StubPredictor(label="normal"), None)
    data = b"text,severity\nCrash,normal\nSlow,normal\nTypo,major\n"
    response = client.post("/api/v1/evaluate", files={"file": ("labelled.csv", data, "text/csv")})
    assert response.status_code == 200
    body = response.json()
    assert body["rows_used"] == 3 and body["rows_skipped"] == 0
    assert round(body["accuracy"], 3) == round(2 / 3, 3)
    assert body["labels"][0] == "blocker" and len(body["confusion_matrix"]) == 6
    assert body["model_version"] == "stub-v1"


def test_evaluate_endpoint_explains_bad_files():
    client = make_client(StubPredictor(), None)
    bad = client.post("/api/v1/evaluate", files={"file": ("x.csv", b"a,b\n1,2\n", "text/csv")})
    assert bad.status_code == 400 and "Columns not found" in bad.json()["error"]["message"]
    nothing = client.post("/api/v1/evaluate", files={"file": ("x.csv", b"text,severity\n,normal\n", "text/csv")})
    assert nothing.status_code == 400


def webhook(client, event, payload, secret=SECRET, signature=None):
    body = json.dumps(payload).encode()
    headers = {"X-GitHub-Event": event, "X-Hub-Signature-256": signature or sign(body, secret), "Content-Type": "application/json"}
    return client.post("/api/v1/integrations/github/webhook", content=body, headers=headers)


def test_webhook_is_off_without_a_secret_and_rejects_a_bad_signature():
    off = make_client(StubPredictor(), None)
    assert webhook(off, "issues", issue_payload()).status_code == 404
    on = make_client(StubPredictor(), None, github_webhook_secret=SECRET, github_token="t")
    assert webhook(on, "issues", issue_payload(), signature="sha256=wrong").status_code == 401


def test_webhook_ignores_other_events_and_actions():
    client = make_client(StubPredictor(), None, github_webhook_secret=SECRET, github_token="t")
    assert webhook(client, "ping", {"zen": "x"}).json()["ignored"] == "ping"
    assert webhook(client, "issues", issue_payload(action="closed")).json()["ignored"] == "issues:closed"


def test_webhook_labels_a_new_issue(monkeypatch):
    calls = []
    monkeypatch.setattr(github_triage, "make_poster", lambda token: (lambda url, data: calls.append((token, url, data))))
    client = make_client(StubPredictor(), StubFinder(), github_webhook_secret=SECRET, github_token="tok")
    response = webhook(client, "issues", issue_payload())
    assert response.status_code == 202 and response.json()["accepted"] is True
    assert [url.rsplit("/", 1)[1] for _, url, _ in calls] == ["labels", "comments"]
    assert calls[0][0] == "tok"


def test_config_checks_the_webhook_secret_length():
    Settings(github_webhook_secret=SECRET).validate_for_startup()
    with pytest.raises(ValueError):
        Settings(github_webhook_secret="short").validate_for_startup()
