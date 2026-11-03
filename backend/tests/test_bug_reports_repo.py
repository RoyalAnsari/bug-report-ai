from app.repositories.bug_reports import build_report_documents, make_report_id, normalize_text


def test_normalize_text_collapses_spaces():
    assert normalize_text("  Crash   on\tsave ") == "Crash on save"


def test_report_id_is_stable_for_same_report():
    assert make_report_id("Core", "Crash  on SAVE") == make_report_id("core", " crash on save")


def test_report_id_differs_by_project():
    assert make_report_id("Core", "Crash on save") != make_report_id("JDT", "Crash on save")


def test_same_report_twice_gives_one_document():
    reports = [
        {"text": "Crash on save", "project": "Core"},
        {"text": "crash  on save", "project": "core"},
        {"text": "Typo in menu", "project": "Core"},
    ]
    assert len(build_report_documents(reports, "test")) == 2


def test_severity_only_included_when_present():
    without = build_report_documents([{"text": "abc def", "project": "Core", "severity": None}], "t")
    with_label = build_report_documents(
        [{"text": "abc def", "project": "Core", "severity": "major", "external_id": 7}], "t"
    )
    assert "severity" not in next(iter(without.values()))
    fields = next(iter(with_label.values()))
    assert fields["severity"] == "major"
    assert fields["external_id"] == "7"